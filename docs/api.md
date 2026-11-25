# TechService — Contrato inicial de API REST

**Estado:** clientes y `/health` implementados. Los demás recursos siguen en diseño.

**Fecha:** 2026-11-25 · **Versión:** 0.2

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

Las cuatro rutas de clientes están temporalmente abiertas sin autenticación. Utiliza solo datos ficticios en desarrollo mientras se implementa la sesión.

| Petición | Respuesta |
|---|---|
| `POST /api/v1/customers` | `201` con el cliente creado |
| `GET /api/v1/customers` | `200` con una lista JSON de clientes, incluso si está vacía (`[]`) |
| `GET /api/v1/customers/{id}` | `200` con el cliente o `404` si no existe |
| `PATCH /api/v1/customers/{id}` | `200` con el cliente actualizado o `404` si no existe |

Cada cliente se representa con `id`, `name`, `phone` y `email`. PostgreSQL genera el ID. El parámetro de ruta acepta enteros de 1 a 9223372036854775807.

- Para crear un cliente, envía `name` (1–120 caracteres) y `phone` (1–30, como texto). Se recortan los espacios exteriores y se rechaza el texto vacío. El correo es opcional, admite `null` y, si se proporciona, debe ser válido y tener como máximo 254 caracteres. Se admiten teléfonos y correos compartidos.
- En un `PATCH`, cada campo omitido conserva su valor. Por ejemplo, `{"email":null}` borra el correo y conserva nombre y teléfono. Un objeto vacío (`{}`) devuelve el cliente sin cambios. Proporcionar `null` en `name` o `phone` devuelve `422`.
- Ambos cuerpos de escritura rechazan con `422` el campo `id`, los campos desconocidos y los valores inválidos. Los parámetros de ruta o paginación fuera de rango también devuelven `422`.
- El listado se ordena por `id` ascendente. `limit` admite de 1 a 100 y por defecto vale 20. `offset` admite de 0 a 9223372036854775807 y por defecto vale 0. La respuesta es un array sin total.

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

El listado de clientes usa una lista simple. El cuerpo de login y los detalles del token CSRF se definirán al implementar autenticación.
