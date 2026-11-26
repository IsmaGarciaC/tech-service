# TechService

TechService es una aplicación web en desarrollo para pequeños talleres de reparación de computadoras. El backend FastAPI permite registrar, listar, consultar y actualizar clientes y equipos en PostgreSQL bajo `/api/v1/customers` y `/api/v1/devices`. Estas rutas son temporalmente accesibles sin autenticación. En desarrollo, utiliza solo datos ficticios. Consulta los campos y ejemplos en el [contrato REST](docs/api.md#device).

## Instalar y ejecutar el backend

Desde la raíz del repositorio, crea el entorno con Python 3.14, instala las dependencias y arranca Uvicorn.

```sh
cd backend
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m uvicorn app.main:app
```

En otra terminal, ejecuta `curl -fsS http://127.0.0.1:8000/health`. La respuesta esperada es HTTP 200 con `{"status":"ok"}`. Puedes arrancar la API y consultar esta ruta sin configurar PostgreSQL.

## Configurar PostgreSQL

Compose define el servicio `db` con PostgreSQL 18, un volumen persistente y el puerto local `127.0.0.1:5432`. El backend se ejecuta en el equipo anfitrión. Para preparar una instalación nueva, copia la configuración de ejemplo desde la raíz.

```sh
cp -n .env.example .env
```

Edita `.env` y elige `POSTGRES_DB`, `POSTGRES_USER` y una contraseña propia en `POSTGRES_PASSWORD`. Para el Compose incluido, usa `POSTGRES_HOST=127.0.0.1` y `POSTGRES_PORT=5432`. Si el volumen ya está inicializado, usa las credenciales vigentes de esa instancia. Git ignora el archivo `.env`.

Con Docker en ejecución y acceso a su socket, valida la configuración y arranca el servicio desde la raíz.

```sh
docker compose config --quiet
docker compose up -d --no-recreate db
```

Para habilitar las rutas de clientes y equipos, aplica las migraciones desde `backend/` con el entorno virtual activo y PostgreSQL listo.

```sh
python -m alembic upgrade head
python -m alembic current
```

La revisión `f511a0394d3e` crea `customers` y la siguiente, `2c997572e58f`, añade `devices`. Con la API en ejecución, `curl -fsS 'http://127.0.0.1:8000/api/v1/devices?customer_id=1'` lista los equipos de ese cliente. Una lista sin coincidencias devuelve `[]`.

## Modelos, sesiones y migraciones

Define los futuros modelos con `app.core.database.Base` e importa sus módulos en `alembic/env.py` para que Alembic pueda comparar `Base.metadata` con la base. Cuando haya un cambio de esquema, genera y revisa la migración desde `backend/` antes de aplicarla.

```sh
python -m alembic revision --autogenerate -m "descripcion del cambio"
# Revisa las operaciones upgrade y downgrade del archivo generado.
python -m alembic upgrade head
```

Las rutas que necesiten persistencia pueden usar `Depends(get_db)`. Cada petición recibe una sesión síncrona que se cierra al terminar. El servicio que coordina la operación decide cuándo hacer `commit` o `rollback`.

## Comprobar el backend

Para las pruebas de integración, arranca una instancia desechable en el puerto local 55432. El contenedor usa memoria temporal, admite conexiones locales sin contraseña y es independiente del servicio de desarrollo. Espera a que `pg_isready` indique que acepta conexiones.

```sh
docker run -d --rm --name techservice-pg-test --tmpfs /var/lib/postgresql \
  -p 127.0.0.1:55432:5432 -e POSTGRES_HOST_AUTH_METHOD=trust postgres:18
docker exec techservice-pg-test pg_isready -U postgres -h 127.0.0.1
export TEST_POSTGRES_ADMIN_URL=postgresql+psycopg://postgres@127.0.0.1:55432/postgres
```

Ejecuta los controles desde `backend/` con el entorno virtual activo. Cada prueba de integración crea una base con nombre aleatorio en esa instancia, aplica Alembic y elimina solo su propia base al terminar. El rol de pruebas necesita permiso `CREATEDB`.

```sh
python -m ruff check .
python -m ruff format --check .
python -m pip check
python -m pytest -q
```

La suite comprueba también `upgrade head`, `alembic check`, `downgrade base` y la reaplicación. Al terminar, detén el contenedor con `docker stop techservice-pg-test`. Para ejecutar únicamente las pruebas unitarias sin PostgreSQL, usa `python -m pytest -q --ignore=tests/integration`.

## Documentación de diseño

[Requisitos del MVP](docs/requirements.md) · [Arquitectura](docs/architecture.md) · [Modelo de datos](docs/data-model.md) · [Contrato inicial de API](docs/api.md)
