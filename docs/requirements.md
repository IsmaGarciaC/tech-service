# TechService — Requisitos del MVP

**Estado:** borrador inicial para implementación y validación con usuarios reales  
**Fecha:** 2026-11-18  
**Versión del documento:** 0.1

## 1. Contexto y propósito

TechService es una aplicación web para pequeños talleres de reparación de computadoras. Su objetivo es centralizar el registro de clientes, equipos y órdenes de trabajo, permitir el seguimiento del estado de las reparaciones y consultar el historial de servicios.

El proyecto tiene dos metas de importancia similar: servir como proyecto profesional de portafolio y validar la posibilidad de ofrecer una solución a negocios reales. **La demanda comercial todavía no está validada.**

## 2. Usuario objetivo y problema a validar

**Usuario objetivo inicial:** propietario o técnico de un taller pequeño de reparación de computadoras, operado inicialmente por una sola persona.

**Hipótesis de problema:** el taller podría tener dificultades para registrar, localizar y dar seguimiento a las órdenes cuando utiliza papel, mensajes o registros dispersos. Esta hipótesis debe comprobarse mediante conversaciones y observación del proceso real del taller.

**Objetivo del usuario:** saber qué trabajos recibió, en qué estado se encuentran, a qué cliente pertenecen y qué reparaciones anteriores se registraron.

## 3. Alcance funcional del MVP

### RF-01 — Clientes
- Registrar un cliente con nombre y teléfono obligatorios; correo opcional.
- Listar y consultar clientes.
- Corregir sus datos mediante actualización parcial.

### RF-02 — Equipos
- Registrar un equipo vinculado a un cliente existente.
- Registrar tipo de equipo obligatorio; marca, modelo y número de serie opcionales.
- Listar y consultar equipos, incluyendo filtrado por cliente.
- Corregir información descriptiva del equipo sin transferir su propiedad entre clientes.
- Si cambia de propietario, crear un registro de equipo nuevo vinculado al nuevo cliente. El número de serie no será único globalmente.

### RF-03 — Órdenes de trabajo
- Crear una orden vinculada a un equipo existente con descripción obligatoria del problema reportado.
- Asignar automáticamente `pending` al crear la orden.
- Consultar y listar órdenes con filtros por estado, cliente y equipo.
- Agregar o modificar notas técnicas.
- Cambiar estados exclusivamente en este orden: `pending` → `in_progress` → `ready` → `delivered`.
- Registrar `delivered_at` cuando se produzca la transición a `delivered`.
- Consultar el historial de servicios de un cliente a partir de las órdenes de sus equipos; no se necesita una tabla de historial adicional.

### RF-04 — Vista principal
- Mostrar una lista de órdenes con filtros por estado y acceso a sus detalles.
- Facilitar la creación de nuevas órdenes.
- No se requiere un panel analítico avanzado.

### RF-05 — Acceso
- Permitir que una cuenta inicial del taller inicie y cierre sesión.
- Proteger las operaciones de consulta y modificación de información del taller.
- No habrá registro público ni roles múltiples en el MVP.
- Las funciones de autenticación deben estar completas antes de usar datos reales en un entorno accesible por usuarios.

## 4. Modelo de datos de negocio

### Customer
`id` (PK, BIGINT), `name` (VARCHAR 120, requerido), `phone` (VARCHAR 30, requerido), `email` (VARCHAR 254, opcional).

### Device
`id` (PK, BIGINT), `customer_id` (FK, requerido), `device_type` (VARCHAR 50, requerido), `brand` (VARCHAR 80, opcional), `model` (VARCHAR 120, opcional), `serial_number` (VARCHAR 120, opcional).

### WorkOrder
`id` (PK, BIGINT), `device_id` (FK, requerido), `problem_description` (TEXT, requerido), `status` (VARCHAR 20, requerido, por defecto `pending`), `technician_notes` (TEXT, opcional), `created_at` (TIMESTAMPTZ, automático), `delivered_at` (TIMESTAMPTZ, opcional).

**Relaciones:** Customer 1:N Device; Device 1:N WorkOrder. No se aplicarán eliminaciones en cascada desde la aplicación.

Las tablas técnicas `users` y `sessions`, necesarias para el acceso, no cuentan como entidades de negocio.

## 5. Reglas e integridad

- Los identificadores son generados por PostgreSQL.
- No permitir nombres, teléfonos o descripciones obligatorias vacíos o compuestos solo por espacios.
- Validar formato de correo electrónico si se proporciona.
- No imponer unicidad global de teléfono, correo o número de serie.
- Un equipo debe tener un cliente existente; una orden debe tener un equipo existente.
- Los cambios de estado inválidos deben rechazarse, incluso si el cliente HTTP envía un estado contemplado por el esquema.
- El estado `delivered` es terminal en el MVP.
- No se expondrán endpoints de borrado de clientes, equipos ni órdenes en el MVP.
- Las reglas de negocio se aplican en servicios; Pydantic valida entradas y PostgreSQL garantiza restricciones fundamentales.

## 6. Requisitos no funcionales mínimos

- **Interfaz:** web responsive en español, utilizable desde computadora y teléfono.
- **API:** REST/JSON, rutas con prefijo `/api/v1`, convenciones en inglés y campos `snake_case`.
- **Seguridad:** contraseñas almacenadas con hash seguro, sesiones administradas por servidor con cookies seguras, expiración de sesiones y protección CSRF para cambios de datos.
- **Persistencia:** PostgreSQL; cambios de esquema gestionados por migraciones Alembic.
- **Fechas:** almacenamiento con zona horaria en UTC; presentación adaptada a la zona del taller.
- **Listados:** paginación con `limit` y `offset`, y filtros pertinentes.
- **Calidad:** pruebas unitarias y de integración relevantes, revisión de PR y CI antes de fusionar a `main`.
- **Operación:** antes de utilizar datos reales se requieren HTTPS en despliegues de red, gestión de secretos, copias de seguridad y capacidad comprobada de restauración.

## 7. Fuera del alcance inicial

Facturación electrónica, pagos, inventario, gestión de repuestos, garantías, fotos de equipos, WhatsApp, agentes de IA, roles múltiples, registro público, cambios de propietario entre registros, historiales detallados de transición, paneles analíticos, suscripciones y multiempresa compartida.

## 8. Distribución y comercialización

La arquitectura permite tanto una aplicación alojada como una instalación local futura mediante Docker Compose. **Empaquetar una distribución local para usuarios finales no forma parte del primer recorrido funcional.** El proyecto podría publicarse como código abierto, pero todavía no se ha elegido licencia.

No se asumirá que los talleres desean comprar, instalar o mantener el producto sin investigar sus necesidades.

## 9. Validación con talleres

Antes de ampliar el MVP, conversar con al menos dos talleres del segmento elegido. Investigar cómo registran ingresos, cómo conocen el estado de cada reparación, cómo recuperan el historial y qué problemas realmente les generan trabajo o pérdidas. Registrar observaciones sin inducir respuestas y separar necesidades comprobadas de ideas propuestas por el equipo.

## 10. Criterio de recorrido funcional mínimo

Con datos ficticios, una persona puede iniciar sesión, registrar un cliente, registrar un equipo para ese cliente, abrir una orden, avanzar por los cuatro estados, consultar su detalle y recuperar su historial desde el cliente. Las operaciones deben persistir al reiniciar la aplicación y sus reglas importantes deben tener pruebas automatizadas.

## 11. Secuencia de construcción

1. Primer endpoint FastAPI, entorno y pruebas.
2. PostgreSQL, migraciones y módulo de clientes.
3. Equipos y órdenes con reglas de estado.
4. Frontend React e integración HTTP.
5. Autenticación, protección y recorrido completo.
6. Preparación de piloto y validación de uso.

> Este documento describe requisitos iniciales acordados en el diseño. No confirma que exista una implementación ni que el mercado haya sido validado. Los detalles de infraestructura y arquitectura se registrarán separadamente en `docs/architecture.md`.
