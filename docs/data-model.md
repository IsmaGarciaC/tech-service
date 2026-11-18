# TechService — Modelo de datos

**Estado:** esquema lógico aprobado, no migrado ni implementado  
**Fecha:** 2026-11-18 · **Versión:** 0.1

## 1. Relaciones

```text
Customer (1) ─── (N) Device (1) ─── (N) WorkOrder
```

Cada dispositivo pertenece a un cliente; cada orden pertenece a un dispositivo. El historial de un cliente se deriva de las órdenes de sus dispositivos; **no** existe una tabla adicional de historial.

## 2. Tablas de negocio

### `customers`

| Columna | Tipo PostgreSQL | Regla |
|---|---|---|
| `id` | BIGINT | PK, identidad generada por BD |
| `name` | VARCHAR(120) | NOT NULL; no vacío tras normalizar espacios |
| `phone` | VARCHAR(30) | NOT NULL; texto, no entero; no vacío |
| `email` | VARCHAR(254) | NULL; formato validado si existe |

Ni `phone` ni `email` son únicos globalmente. El nombre no se usa como clave natural.

### `devices`

| Columna | Tipo PostgreSQL | Regla |
|---|---|---|
| `id` | BIGINT | PK, identidad generada por BD |
| `customer_id` | BIGINT | FK NOT NULL → `customers.id` |
| `device_type` | VARCHAR(50) | NOT NULL; no vacío |
| `brand` | VARCHAR(80) | NULL |
| `model` | VARCHAR(120) | NULL |
| `serial_number` | VARCHAR(120) | NULL; no UNIQUE |

**Política de propiedad:** no cambiar `customer_id` mediante el API. Si un dispositivo cambia de dueño, crear otro registro bajo el nuevo cliente. Pueden existir números de serie repetidos.

### `work_orders`

| Columna | Tipo PostgreSQL | Regla |
|---|---|---|
| `id` | BIGINT | PK, identidad generada por BD |
| `device_id` | BIGINT | FK NOT NULL → `devices.id` |
| `problem_description` | TEXT | NOT NULL; no vacío |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT `pending`, CHECK de valores |
| `technician_notes` | TEXT | NULL |
| `created_at` | TIMESTAMPTZ | NOT NULL, valor inicial automático UTC |
| `delivered_at` | TIMESTAMPTZ | NULL; se establece al entregar |

Valores de `status`: `pending`, `in_progress`, `ready`, `delivered`. `delivered` es terminal.

```text
pending ──→ in_progress ──→ ready ──→ delivered
```

El servicio solo acepta transiciones consecutivas. Al pasar a `delivered` asigna `delivered_at`; antes de ello permanece nulo. Un intento de salto de estado se rechaza (API: 409).

El servicio aplica además el vínculo lógico entre estado y `delivered_at`; la BD garantiza como mínimo los estados permitidos y las relaciones. Una restricción CHECK adicional para coherencia `delivered_at`/`status` puede establecerse al crear la migración, con su prueba correspondiente.

## 3. Restricciones transversales

- IDs generados por PostgreSQL; números positivos se validan en contratos de entrada cuando corresponda.
- Claves foráneas con integridad referencial y sin borrado en cascada.
- Sin endpoints de borrado de entidades de negocio en el MVP.
- Pydantic valida formatos, límites y strings con espacios; los servicios verifican asociaciones, existencia y transiciones; PostgreSQL protege los datos fundamentales. Los campos obligatorios de texto necesitan también protección contra valores vacíos en la BD (CHECK o equivalente en migraciones).
- Marcas y tipos de equipo siguen siendo texto, sin tablas catálogo iniciales.
- Fechas almacenadas como instantes con zona horaria (UTC); respuestas ISO 8601.
- Indexar las claves foráneas `devices.customer_id` y `work_orders.device_id`. Evaluar índices adicionales basándose en consultas reales.

## 4. Tablas técnicas (seguridad)

Además de las tres tablas de negocio, `users` y `sessions` brindarán acceso a una cuenta inicial.

- **`users`:** `id` (PK), `username` (único), `password_hash`, `is_active`.
- **`sessions`:** relación con usuario, verificador/hash de sesión, caducidad e información mínima necesaria para revocación.

La forma exacta del token, los nombres/longitudes de columnas auxiliares de sesión y las políticas de expiración se especificarán durante la implementación de autenticación con pruebas. No se almacenará una contraseña en claro ni un token de sesión reutilizable en claro en la base de datos.

## 5. Ejemplos de comportamiento que deberán probarse

1. Cliente con varios dispositivos y dispositivo con varias órdenes.
2. Serie duplicada en equipos de clientes diferentes permitida.
3. Rechazo de `device.customer_id` inexistente y `work_order.device_id` inexistente.
4. Rechazo de textos obligatorios vacíos o compuestos solo por espacios.
5. Orden nueva en `pending`, `delivered_at = NULL`.
6. Avance válido por los cuatro estados; salto de `pending` a `delivered` rechazado.
7. Entrega guarda `delivered_at`; órdenes entregadas visibles en historial.
8. Sin borrado en cascada y sin transferencia de equipo mediante API.

Este documento fija el modelo lógico; las migraciones Alembic se crearán durante el desarrollo, no ahora.
