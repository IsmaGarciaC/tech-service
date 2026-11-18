# TechService — Contrato inicial de API REST

**Estado:** diseño aprobado, endpoints aún no implementados  
**Fecha:** 2026-11-18 · **Versión:** 0.1

## 1. Convenciones

- Prefijo `/api/v1`; recursos plurales en inglés y segmentos compuestos en `kebab-case`.
- JSON con campos `snake_case`; fechas en ISO 8601 con desplazamiento/zona UTC.
- Sesión por cookie HTTP-only gestionada en servidor; peticiones que cambian estado protegidas contra CSRF (mecanismo definitivo en etapa auth).
- Endpoints privados requieren autenticación; `/auth/login` es público. `/health` es un endpoint técnico mínimo y no contiene datos del negocio.
- Se utiliza `GET`, `POST` y `PATCH`; sin `DELETE` en el MVP.
- Listados con `limit` (por defecto 20; máximo 100), `offset` (por defecto 0), con orden estable. Las órdenes se presentan desde las más recientes: `created_at DESC, id DESC`.
- Los esquemas finales de entrada/salida se concretarán con Pydantic al implementar cada módulo, manteniendo los campos de `docs/data-model.md`.

## 2. Recursos

| Método | Ruta (tras `/api/v1`) | Operación |
|---|---|---|
| POST | `/customers` | Crear cliente |
| GET | `/customers` | Listar clientes |
| GET | `/customers/{id}` | Obtener cliente |
| PATCH | `/customers/{id}` | Corregir datos |
| POST | `/devices` | Crear equipo para cliente existente |
| GET | `/devices` | Listar / filtrar por `customer_id` |
| GET | `/devices/{id}` | Obtener equipo |
| PATCH | `/devices/{id}` | Corregir datos descriptivos; no transferir propietario |
| POST | `/work-orders` | Crear orden de un equipo existente |
| GET | `/work-orders` | Listar / filtrar por `status`, `customer_id`, `device_id` |
| GET | `/work-orders/{id}` | Consultar orden |
| PATCH | `/work-orders/{id}` | Modificar notas técnicas |
| PATCH | `/work-orders/{id}/status` | Avanzar el estado bajo reglas de negocio |
| POST | `/auth/login` | Iniciar sesión |
| POST | `/auth/logout` | Invalidar sesión |
| GET | `/auth/me` | Consultar cuenta autenticada |

Fuera del prefijo funcional, `GET /health` verifica que la aplicación HTTP responde; inicialmente no requiere base de datos y no revela detalles internos.

## 3. Campos y reglas esenciales

### Customer
- Crear: `name`, `phone` requeridos; `email` opcional.
- Actualizar: subconjunto de campos editables; rechazar vacíos en campos obligatorios.
- Responder con `id` y campos pertinentes, sin exponer datos de otras entidades automáticamente.

### Device
- Crear: `customer_id`, `device_type` requeridos; `brand`, `model`, `serial_number` opcionales.
- Actualizar: solo datos descriptivos (`device_type`, `brand`, `model`, `serial_number`); **no** `customer_id`.
- Filtrar por `customer_id`.

### WorkOrder
- Crear: `device_id`, `problem_description` requeridos. `status` se asigna en servidor (`pending`).
- Actualizar notas: `technician_notes` opcional; no permitir modificar `device_id`, `created_at` o `delivered_at` arbitrariamente.
- Cambiar estado: `PATCH /work-orders/{id}/status` con cuerpo `{"status":"in_progress"}` (valores válidos según estado actual). Solo avance consecutivo `pending → in_progress → ready → delivered`.
- Al entregar: guardar `delivered_at`. No permitir transiciones adicionales desde `delivered`.
- Historia de cliente mediante `GET /work-orders?customer_id=5`, sin endpoint duplicado.

### Ejemplo de transición exitosa

```http
PATCH /api/v1/work-orders/15/status
Content-Type: application/json

{"status":"ready"}
```

Respuesta `200 OK` (representación mínima ilustrativa, no contrato completo):

```json
{"id":15,"status":"ready","delivered_at":null}
```

### Ejemplo de transición inválida

`pending → delivered` devuelve `409 Conflict`:

```json
{"detail":"Cannot transition from pending to delivered"}
```

## 4. Estados HTTP

| Estado | Uso |
|---|---|
| 200 | Lectura o modificación exitosa |
| 201 | Recurso creado |
| 401 | Sin sesión válida |
| 404 | Recurso inexistente |
| 409 | Conflicto de negocio (por ejemplo, transición inválida) |
| 422 | Datos no válidos conforme al esquema |

Se utilizará el formato estándar de errores de FastAPI (`detail`) inicialmente. No se expondrán errores internos de PostgreSQL ni trazas.

## 5. Seguridad, documentación y pruebas

- FastAPI es fuente de la especificación OpenAPI generada una vez implementadas las rutas; este documento registra intención y convenciones.
- Documentación interactiva disponible en desarrollo; evaluar restricción en despliegue real según riesgo.
- Autenticación y autorización deben estar completas antes de usar datos privados reales; la protección de rutas en React no sustituye autorización API.
- El cliente Fetch compartido incluirá cookies y las defensas CSRF requeridas. El despliegue se diseñará preferentemente con un solo origen.
- Probar respuestas `201`, `200`, `401`, `404`, `409`, `422` pertinentes; probar que una petición maliciosa no modifique campos no editables.

## 6. Asuntos intencionadamente diferidos

No existe aún un estándar cerrado para la estructura de metadatos de las listas paginadas (por ejemplo, lista simple frente a `items` + `total`), el payload exacto de login ni los detalles del token CSRF. Se definirán al implementar las primeras funciones que los requieran y se registrarán antes de consumirlos desde React. **No son decisiones de stack pendientes ni bloquean `/health`.**
