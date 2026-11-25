# TechService

TechService es una aplicación web en desarrollo para pequeños talleres de reparación de computadoras. El backend FastAPI expone `GET /health`, valida los datos de entrada de clientes con Pydantic y dispone de sesiones SQLAlchemy y de Alembic para PostgreSQL. Los modelos ORM, las migraciones de negocio, las rutas de clientes y el frontend están pendientes.

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

Cuando PostgreSQL esté listo, comprueba la conexión y la revisión actual desde `backend/` con el entorno virtual activo.

```sh
python - <<'PY'
from sqlalchemy import text
from app.core.database import get_session_factory

session_factory = get_session_factory()
with session_factory() as session:
    print(session.scalar(text("SELECT 1")))
PY
python -m alembic current
```

La consulta debe imprimir `1`. En una base nueva, `alembic current` indica que usa PostgreSQL y termina sin listar una revisión.

## Modelos, sesiones y migraciones

Define los futuros modelos con `app.core.database.Base` e importa sus módulos en `alembic/env.py` para que Alembic pueda comparar `Base.metadata` con la base. Cuando haya un cambio de esquema, genera y revisa la migración desde `backend/` antes de aplicarla.

```sh
python -m alembic revision --autogenerate -m "descripcion del cambio"
# Revisa las operaciones upgrade y downgrade del archivo generado.
python -m alembic upgrade head
```

Las rutas que necesiten persistencia pueden usar `Depends(get_db)`. Cada petición recibe una sesión síncrona que se cierra al terminar. El servicio que coordina la operación decide cuándo hacer `commit` o `rollback`.

## Comprobar el backend

Ejecuta los controles desde `backend/` con el entorno virtual activo.

```sh
python -m ruff check .
python -m ruff format --check .
python -m pip check
python -m pytest -q
```

La suite se ejecuta sin PostgreSQL y sin un archivo `.env`. La comprobación de conexión real se ejecuta por separado con los comandos de la sección de PostgreSQL.

## Documentación de diseño

[Requisitos del MVP](docs/requirements.md) · [Arquitectura](docs/architecture.md) · [Modelo de datos](docs/data-model.md) · [Contrato inicial de API](docs/api.md)
