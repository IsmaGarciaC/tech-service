import os
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, make_url, pool, text
from sqlalchemy.orm import Session

from alembic import command
from app.core.database import get_db
from app.main import app


@pytest.fixture
def empty_engine() -> Iterator[Engine]:
    admin_url = os.environ.get("TEST_POSTGRES_ADMIN_URL")
    if not admin_url:
        pytest.fail("Set TEST_POSTGRES_ADMIN_URL to the isolated PostgreSQL instance")
    url = make_url(admin_url)
    if url.drivername != "postgresql+psycopg" or url.database != "postgres":
        pytest.fail("Use postgresql+psycopg and the postgres maintenance database")

    name = f"techservice_test_{uuid4().hex}"
    admin = create_engine(url, isolation_level="AUTOCOMMIT", poolclass=pool.NullPool)
    with admin.connect() as connection:
        connection.exec_driver_sql(f'CREATE DATABASE "{name}" TEMPLATE template0')
        engine = create_engine(url.set(database=name))
        try:
            with engine.connect() as target:
                if target.scalar(text("SELECT current_database()")) != name:
                    pytest.fail("The test connection did not select the new database")
            yield engine
        finally:
            engine.dispose()
            connection.exec_driver_sql(f'DROP DATABASE "{name}"')


@pytest.fixture
def alembic_config(empty_engine: Engine) -> Iterator[Config]:
    config = Config(Path(__file__).resolve().parents[2] / "alembic.ini")
    with empty_engine.connect() as connection:
        config.attributes["connection"] = connection
        yield config


@pytest.fixture
def engine(empty_engine: Engine, alembic_config: Config) -> Engine:
    command.upgrade(alembic_config, "head")
    return empty_engine


@pytest.fixture
def client(engine: Engine, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    def test_db() -> Iterator[Session]:
        with Session(engine, expire_on_commit=False) as session:
            yield session

    monkeypatch.setitem(app.dependency_overrides, get_db, test_db)
    with TestClient(app) as client:
        yield client
