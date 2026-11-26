# TechService — Arquitectura técnica

**Estado:** diseño aprobado. El backend implementa clientes y equipos con PostgreSQL y migraciones Alembic.

**Fecha:** 2026-11-25 · **Versión:** 0.2

## 1. Objetivo y límites

TechService es una aplicación web para gestionar clientes, equipos y órdenes de un taller pequeño de reparación de computadoras. El primer despliegue corresponde a **un taller por instancia** y una cuenta operativa inicial. No se presupone validación comercial ni una plataforma SaaS multiempresa.

**Objetivos técnicos:** mantener responsabilidades claras, aprender construyendo en incrementos pequeños, permitir ejecución local de desarrollo y preparar una futura distribución local autohospedada. La distribución final no está implementada.

## 2. Stack aprobado

| Área | Decisión | Introducción |
|---|---|---|
| Backend | Python, FastAPI, Pydantic v2 | Primera etapa |
| Persistencia | PostgreSQL, SQLAlchemy 2.x síncrono, Alembic | Primera funcionalidad persistente |
| Frontend | React, TypeScript, Vite | Después del backend funcional |
| Navegación | React Router (modo declarativo) | Al construir pantallas |
| HTTP | Fetch API con cliente compartido | Primera integración frontend |
| Estado UI | `useState`, `useContext` cuando aporte valor | Frontend |
| Estado remoto | TanStack Query si la sincronización lo justifica | Posterior, no requisito inicial |
| Formularios | React nativo, React Hook Form solo si aporta valor | Frontend |
| Estilos | CSS Modules | Frontend |
| Pruebas | pytest y TestClient; PostgreSQL de test; Vitest y Testing Library | Según funcionalidades |
| Calidad | Ruff, ESLint, TypeScript (`tsc`) | Desde cada subproyecto |
| Automatización | GitHub Actions + PRs y protección de `main` | Primera etapa |
| Desarrollo local | Python/React ejecutados localmente; PostgreSQL en Docker Compose | Al incorporar persistencia |
| Distribución local futura | Servicios empaquetados con Docker Compose | Después del MVP funcional |

No se introducirán microservicios, Redis, colas, Redux, inventario ni un framework full-stack adicional para el MVP.

## 3. Diseño general

```text
Navegador
   │ HTTPS o HTTP local
   ▼
React SPA (TypeScript)
   │ REST / JSON, cookies de sesión y protección CSRF
   ▼
FastAPI (monolito modular)
   ├── routers: HTTP, dependencias y respuestas
   ├── schemas Pydantic: contratos y validación
   ├── services: reglas de negocio y transacciones
   └── models SQLAlchemy: persistencia
           │
           ▼
       PostgreSQL
```

En producción se prefiere **un mismo origen** para frontend y API: `/` sirve la SPA y `/api/v1/*` se dirige a FastAPI mediante un proxy inverso. En desarrollo Vite podrá reenviar llamadas `/api` a FastAPI. Esto reduce complejidad de cookies y CORS, pero no sustituye protección CSRF ni controles de autorización.

## 4. Backend por funcionalidades

Estructura objetivo, creada progresivamente — **no** se deben generar módulos vacíos:

```text
backend/
  app/
    main.py
    core/                 # configuración y seguridad compartida
    db/                   # sesión y migraciones/configuración
    modules/
      auth/
      customers/
      devices/
      work_orders/
  tests/
```

Dentro de una funcionalidad pueden aparecer `router.py`, `schemas.py`, `models.py` y `service.py` según se necesiten.

### Responsabilidades

- **Router:** traducir peticiones/respuestas HTTP, invocar servicios y depender de la sesión/autenticación.
- **Pydantic:** validar entrada y definir salida; no sustituye reglas de negocio ni integridad relacional.
- **Service:** verificar transiciones, asociaciones y casos de uso; delimitar la transacción de una operación de negocio.
- **SQLAlchemy:** ORM 2.x síncrono, utilizado directamente desde servicios en el MVP, sin repositorios abstractos obligatorios.
- **PostgreSQL:** claves primarias/foráneas, `NOT NULL`, `CHECK` y persistencia.
- **Alembic:** versionar los cambios de esquema; no usar `create_all()` como mecanismo de migración de producción.

Las sesiones de base de datos se obtendrán por dependencia por petición y se cerrarán al finalizar. Definiremos claramente el propietario del `commit`/`rollback` de cada operación; no se confirmarán cambios parciales de un caso de uso.

## 5. Frontend por funcionalidades

```text
frontend/
  src/
    app/                 # entrada y rutas
    features/
      auth/
      customers/
      devices/
      work-orders/
    shared/
      api/               # cliente Fetch único
      components/        # componentes realmente compartidos
      styles/
    main.tsx
```

La SPA será responsive y estará en español. El código y los contratos HTTP estarán en inglés. Se separan estado de interfaz y datos procedentes del servidor. La protección visual de rutas **no** autoriza acceso: FastAPI verificará la sesión para cada operación privada.

## 6. Autenticación y seguridad

- Tablas técnicas `users` y `sessions`, separadas de las tres entidades de negocio.
- Una cuenta inicial creada por un procedimiento controlado, sin contraseñas por defecto publicadas ni registro público.
- Contraseñas con hash resistente (Argon2); no almacenar contraseñas en claro.
- Sesiones **gestionadas por servidor**, con identificadores impredecibles, expiración, invalidación en logout y almacenamiento de un valor/verificador seguro en servidor.
- Cookie `HttpOnly`, `SameSite` apropiado, `Secure` bajo HTTPS; nunca almacenar credenciales o identificadores de sesión en localStorage.
- Protección CSRF para operaciones que cambian estado; evaluar estrategia concreta al implementar auth (token CSRF u otra defensa equivalente) y pruebas de seguridad.
- Una cuenta y sin roles múltiples en el primer piloto. Se requerirá sesión válida para datos de clientes/equipos/órdenes.
- Credenciales y configuración sensible vía entorno, sin subir secretos a Git; usar `.env.example` solo con claves y valores ficticios.

**Limitación:** autenticación, configuración de cookies, procedimiento de inicialización y defensa CSRF aún no están implementados. No usar datos reales antes de verificarlos.

## 7. API y consistencia

- Prefijo `/api/v1`, recursos plurales en inglés, URL en `kebab-case`, cuerpo JSON en `snake_case`.
- `GET`, `POST`, `PATCH`; sin `DELETE` expuesto al comienzo.
- `PATCH /work-orders/{id}/status` como operación explícita, con las transiciones `pending → in_progress → ready → delivered`.
- Listados `limit` (20 por defecto, máximo 100), `offset` y filtros; órdenes de más recientes a más antiguas por `(created_at, id)`.
- Respuestas HTTP convencionales: `200`, `201`, `401`, `404`, `409`, `422` y otros según proceda.
- Errores estándar FastAPI (`detail`); sin exponer excepciones internas.
- Fechas como ISO 8601 con zona horaria; almacenamiento UTC.
- OpenAPI generado por FastAPI. Ver `docs/api.md` para el contrato provisional.

## 8. Calidad, ramas y automatización

- Desarrollo incremental por Issue → rama → implementación → pruebas → PR → revisión → merge.
- `main` protegida mediante checks y revisión antes de fusionar cuando las capacidades del repositorio lo permitan.
- Backend: pytest para lógica de negocio, TestClient para API y PostgreSQL aislado para pruebas de integración.
- Frontend: Vitest + Testing Library al implementar componentes; posteriormente pocas pruebas E2E de los flujos más importantes (herramienta a elegir cuando haga falta).
- CI: Ruff + pytest; al añadir persistencia, servicio PostgreSQL para pruebas; al añadir frontend, ESLint + TypeScript + Vitest + build.
- Al menos una revisión crítica semanal de código generado por IA. Aprobar una PR exige revisar requisitos, arquitectura, errores y seguridad, no solo tests verdes.
- El primer despliegue será manual y verificable; **no** se activan despliegues automáticos con cada merge por defecto.

## 9. Entornos y operación

### Desarrollo
Python en `venv`, frontend en Node.js LTS/npm, base de datos PostgreSQL con Docker Compose cuando sea necesaria. Contenedores y volúmenes de datos de desarrollo separados de los de pruebas.

### Piloto y distribución
No se ha elegido proveedor de hosting. Para despliegue público: HTTPS, secretos, restricciones de red, backups automáticos, restauración probada, migraciones controladas y logs sin datos sensibles. Para instalación local futura: Compose con frontend, backend y PostgreSQL, puertos limitados por defecto a localhost, volumen persistente e instrucciones de backup/actualización. **Un volumen no es un backup.**

No hay instalador, empaquetado final ni licencia open source decidida. Son actividades futuras que no bloquean el primer endpoint.

## 10. Secuencia de implementación

1. FastAPI mínimo: `/health`, test, Ruff, CI y primera PR.
2. PostgreSQL + Alembic + módulo Customers.
3. Device y WorkOrder con relaciones y transiciones, tests de integración.
4. React SPA, formularios, filtros e integración.
5. Autenticación/cookies/CSRF y prueba del recorrido completo con datos ficticios.
6. Piloto seguro (alojado o local), backups/restauración y validación real con talleres.

## 11. Trazabilidad y estado

Este documento **registra decisiones acordadas**; no certifica implementación. Detalles de modelos en `docs/data-model.md`, operaciones HTTP en `docs/api.md` y alcance en `docs/requirements.md`. Si la realidad del negocio exige cambios, abrir una Issue y justificar el ajuste antes de modificar contratos.
