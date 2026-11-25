from collections.abc import Iterator
from functools import cache

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings


class Base(DeclarativeBase):
    pass


def database_url(settings: Settings) -> URL:
    return URL.create(
        "postgresql+psycopg",
        username=settings.postgres_user,
        password=settings.postgres_password.get_secret_value(),
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
    )


@cache
def get_session_factory() -> sessionmaker[Session]:
    engine = create_engine(database_url(Settings()))
    return sessionmaker(bind=engine)


def get_db() -> Iterator[Session]:
    session_factory = get_session_factory()
    with session_factory() as session:
        yield session
