import pytest
from alembic.config import Config
from sqlalchemy import BigInteger, Engine, inspect, text
from sqlalchemy.exc import IntegrityError

from alembic import command


def test_device_migration_keeps_existing_customers(
    empty_engine: Engine, alembic_config: Config
) -> None:
    customers_revision = "f511a0394d3e"
    devices_revision = "2c997572e58f"
    command.upgrade(alembic_config, customers_revision)
    with empty_engine.begin() as db:
        customer = db.execute(
            text("""
            INSERT INTO customers (name, phone, email) VALUES ('Demo', '000', NULL)
            RETURNING id, name, phone, email
        """)
        ).one()

    command.upgrade(alembic_config, devices_revision)
    schema = inspect(empty_engine)
    columns = {c["name"]: c for c in schema.get_columns("devices")}
    assert isinstance(columns["id"]["type"], BigInteger)
    assert columns["id"]["identity"]["always"]
    assert schema.get_pk_constraint("devices")["constrained_columns"] == ["id"]
    assert any(
        index["column_names"] == ["customer_id"] and not index["unique"]
        for index in schema.get_indexes("devices")
    )
    with empty_engine.begin() as db:
        db.execute(
            text("INSERT INTO devices (customer_id, device_type) VALUES (:id, 'PC')"),
            {"id": customer.id},
        )

    command.downgrade(alembic_config, customers_revision)
    assert not inspect(empty_engine).has_table("devices")
    with empty_engine.connect() as db:
        assert db.execute(
            text("SELECT id, name, phone, email FROM customers")
        ).all() == [customer]


def test_database_rejects_orphans_blank_types_and_cascade_delete(
    engine: Engine,
) -> None:
    with engine.begin() as db:
        owner = db.scalar(
            text(
                "INSERT INTO customers (name, phone) VALUES ('Demo', '000') "
                "RETURNING id"
            )
        )
    insert = text(
        "INSERT INTO devices (customer_id, device_type) VALUES (:owner, :kind)"
    )
    for customer_id, device_type, sqlstate in [
        (owner + 1, "PC", "23503"),
        (None, "PC", "23502"),
        (owner, None, "23502"),
        (owner, "", "23514"),
        (owner, " \t ", "23514"),
    ]:
        with pytest.raises(IntegrityError) as error, engine.begin() as db:
            db.execute(insert, {"owner": customer_id, "kind": device_type})
        assert error.value.orig.sqlstate == sqlstate
    with engine.begin() as db:
        db.execute(insert, {"owner": owner, "kind": "PC"})
    with pytest.raises(IntegrityError) as error, engine.begin() as db:
        db.execute(text("DELETE FROM customers WHERE id = :id"), {"id": owner})
    assert error.value.orig.sqlstate == "23503"
