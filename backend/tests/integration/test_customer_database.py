import pytest
from alembic.config import Config
from sqlalchemy import BigInteger, Engine, inspect, text
from sqlalchemy.exc import IntegrityError

from alembic import command


def test_migration_round_trip(empty_engine: Engine, alembic_config: Config) -> None:
    assert not inspect(empty_engine).has_table("customers")
    command.upgrade(alembic_config, "head")
    command.check(alembic_config)

    schema = inspect(empty_engine)
    columns = {c["name"]: c for c in schema.get_columns("customers")}
    assert set(columns) == {"id", "name", "phone", "email"}
    assert isinstance(columns["id"]["type"], BigInteger)
    assert columns["id"]["identity"]["always"]
    assert schema.get_pk_constraint("customers")["constrained_columns"] == ["id"]
    for field, length in [("name", 120), ("phone", 30), ("email", 254)]:
        assert columns[field]["type"].length == length
    assert columns["email"]["nullable"]

    command.downgrade(alembic_config, "base")
    assert not inspect(empty_engine).has_table("customers")
    command.upgrade(alembic_config, "head")
    assert inspect(empty_engine).has_table("customers")


def test_required_text_constraints(engine: Engine) -> None:
    insert = text("INSERT INTO customers (name, phone) VALUES (:name, :phone)")
    for field in ["name", "phone"]:
        for value in [None, "", "   ", "\t\n"]:
            row = {"name": "Ana", "phone": "123", field: value}
            with pytest.raises(IntegrityError) as error, engine.begin() as conn:
                conn.execute(insert, row)
            assert error.value.orig.sqlstate == ("23502" if value is None else "23514")
            if value is not None:
                assert (
                    error.value.orig.diag.constraint_name
                    == f"ck_customers_{field}_not_blank"
                )
