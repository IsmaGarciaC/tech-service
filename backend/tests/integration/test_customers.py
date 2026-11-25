import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.customers import service
from app.modules.customers.schemas import CustomerCreate, CustomerUpdate

CUSTOMERS = "/api/v1/customers"
CUSTOMER = {"name": "Ana", "phone": "099 123", "email": "ana@example.com"}
MAX_ID = 2**63 - 1


def test_create_get_and_patch_persist(client: TestClient, engine: Engine) -> None:
    created = client.post(CUSTOMERS, json=CUSTOMER)
    assert created.status_code == 201
    customer_id = created.json()["id"]
    assert 0 < customer_id <= MAX_ID
    expected = CUSTOMER | {"id": customer_id}
    assert created.json() == expected
    path = f"{CUSTOMERS}/{customer_id}"

    fetched = client.get(path)
    assert fetched.status_code == 200
    assert fetched.json() == expected

    for changes, normalized in [
        ({"name": "  Ana María  "}, {"name": "Ana María"}),
        (
            {"phone": "321", "email": "ana2@example.com"},
            {"phone": "321", "email": "ana2@example.com"},
        ),
        ({"email": None}, {"email": None}),
        ({}, {}),
    ]:
        response = client.patch(path, json=changes)
        expected.update(normalized)
        assert response.status_code == 200
        assert response.json() == expected
        with engine.connect() as connection:
            record = (
                connection.execute(
                    text("SELECT id, name, phone, email FROM customers WHERE id = :id"),
                    {"id": customer_id},
                )
                .mappings()
                .one()
            )
            assert dict(record) == expected


def test_partial_update_preserves_another_sessions_change(engine: Engine) -> None:
    with Session(engine, expire_on_commit=False) as first, Session(engine) as second:
        customer = service.create_customer(first, CustomerCreate(**CUSTOMER))
        service.update_customer(second, customer.id, CustomerUpdate(email=None))
        updated = service.update_customer(
            first, customer.id, CustomerUpdate(phone="456")
        )
        assert updated is not None
        assert (updated.phone, updated.email) == ("456", None)


def test_list_customers(client: TestClient, engine: Engine) -> None:
    empty = client.get(CUSTOMERS)
    assert empty.status_code == 200
    assert empty.json() == []

    # Keep the physical insert order different from the required listing order.
    with engine.begin() as connection:
        connection.execute(
            text("""
            INSERT INTO customers (id, name, phone, email) OVERRIDING SYSTEM VALUE
            SELECT id, 'Ana', '123', 'shared@example.com'
            FROM generate_series(22, 1, -1) AS id
        """)
        )

    first = client.get(CUSTOMERS)
    assert first.status_code == 200
    assert [item["id"] for item in first.json()] == list(range(1, 21))
    page = client.get(CUSTOMERS, params={"limit": 2, "offset": 19})
    assert page.status_code == 200
    assert [item["id"] for item in page.json()] == [20, 21]
    last = client.get(CUSTOMERS, params={"limit": 100, "offset": MAX_ID})
    assert last.status_code == 200
    assert last.json() == []


def test_missing_and_invalid_ids(client: TestClient) -> None:
    for id, status in [
        (MAX_ID, 404),
        (0, 422),
        (-1, 422),
        (MAX_ID + 1, 422),
        ("abc", 422),
    ]:
        path = f"{CUSTOMERS}/{id}"
        assert client.get(path).status_code == status
        assert client.patch(path, json={"phone": "123"}).status_code == status


def test_invalid_pagination(client: TestClient) -> None:
    for params in [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"offset": MAX_ID + 1},
    ]:
        assert client.get(CUSTOMERS, params=params).status_code == 422


def test_invalid_bodies_leave_customer_unchanged(client: TestClient) -> None:
    assert client.post(CUSTOMERS, json={"phone": "123"}).status_code == 422
    assert client.post(CUSTOMERS, json=CUSTOMER | {"id": 1}).status_code == 422
    created = client.post(CUSTOMERS, json=CUSTOMER).json()
    path = f"{CUSTOMERS}/{created['id']}"
    for invalid in [{"id": 123}, {"name": None}, {"phone": None}, {"name": "A\0B"}]:
        assert client.patch(path, json=invalid).status_code == 422
    assert client.get(path).json() == created


def test_failed_writes_roll_back_and_hide_database_errors(
    client: TestClient, engine: Engine
) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE customers ADD CONSTRAINT test_write_failure "
                "CHECK (phone <> '0')"
            )
        )
    invalid = CustomerCreate(name="Ana", phone="0")
    with Session(engine) as session:
        with pytest.raises(IntegrityError):
            service.create_customer(session, invalid)
        saved = service.create_customer(session, CustomerCreate(name="Ana", phone="1"))
        with pytest.raises(IntegrityError):
            service.update_customer(session, saved.id, CustomerUpdate(phone="0"))
        assert saved.phone == "1"
        assert list(service.list_customers(session, 20, 0)) == [saved]

    failed = client.post(CUSTOMERS, json=invalid.model_dump())
    assert failed.status_code == 500
    assert failed.json() == {"detail": "Database operation failed"}
