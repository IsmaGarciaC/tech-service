import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core import database
from app.core.config import Settings


def test_database_url_preserves_password_characters() -> None:
    password = "fake@:/%?#[]"
    settings = Settings(
        _env_file=None,
        postgres_db="test_db",
        postgres_user="test_user",
        postgres_password=password,
        postgres_host="localhost",
        postgres_port=5433,
    )

    url = database.database_url(settings)

    assert url.drivername == "postgresql+psycopg"
    assert (url.username, url.password) == ("test_user", password)
    assert (url.host, url.port, url.database) == ("localhost", 5433, "test_db")


@pytest.mark.parametrize("service_fails", [False, True])
def test_get_db_closes_session_without_committing(
    monkeypatch: pytest.MonkeyPatch, service_fails: bool
) -> None:
    engine = create_engine("sqlite://")
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(database, "get_session_factory", lambda: factory)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE sample (id INTEGER)"))

    dependency = database.get_db()
    session = next(dependency)
    connection = session.connection()
    session.execute(text("INSERT INTO sample VALUES (1)"))

    if service_fails:
        with pytest.raises(RuntimeError, match="service failed"):
            dependency.throw(RuntimeError("service failed"))
    else:
        with pytest.raises(StopIteration):
            next(dependency)

    assert connection.closed
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM sample")) == 0
