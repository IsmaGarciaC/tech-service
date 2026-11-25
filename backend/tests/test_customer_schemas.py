import pytest
from pydantic import ValidationError

from app.modules.customers.schemas import CustomerCreate

VALID_CUSTOMER = {
    "name": "Ana Pérez",
    "phone": "+593 99 123 4567",
    "email": "ana@example.com",
}

# Each domain label stays within 63 characters as the total address length varies.
EMAIL_AT_LIMIT = "a" * 64 + "@" + ".".join(["b" * 63, "c" * 63, "d" * 57, "com"])


def test_create_customer_with_all_fields() -> None:
    customer = CustomerCreate(**VALID_CUSTOMER)

    assert customer.model_dump() == VALID_CUSTOMER


@pytest.mark.parametrize("email_fields", [{}, {"email": None}], ids=["omitted", "none"])
def test_customer_email_is_optional(email_fields: dict[str, None]) -> None:
    customer = CustomerCreate(name="Ana", phone="123", **email_fields)

    assert customer.email is None


@pytest.mark.parametrize("field", ["name", "phone"])
def test_customer_requires_field(field: str) -> None:
    data = VALID_CUSTOMER.copy()
    del data[field]

    with pytest.raises(ValidationError) as exc_info:
        CustomerCreate(**data)

    assert [error["loc"] for error in exc_info.value.errors()] == [(field,)]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "A"),
        ("phone", "1"),
        ("name", "A" * 120),
        ("phone", "1" * 30),
        ("email", EMAIL_AT_LIMIT),
    ],
)
def test_customer_accepts_values_at_length_limits(field: str, value: str) -> None:
    customer = CustomerCreate(**(VALID_CUSTOMER | {field: value}))

    assert getattr(customer, field) == value


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", ""),
        ("name", "   "),
        ("phone", ""),
        ("phone", "   "),
        ("email", ""),
        ("email", "   "),
        ("name", "A" * 121),
        ("phone", "1" * 31),
        ("email", EMAIL_AT_LIMIT + "x"),
        ("email", "ana.example.com"),
        ("email", "ana@"),
        ("email", "ana@@example.com"),
    ],
)
def test_customer_rejects_invalid_field_value(field: str, value: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        CustomerCreate(**(VALID_CUSTOMER | {field: value}))

    assert [error["loc"] for error in exc_info.value.errors()] == [(field,)]


def test_customer_strips_outer_whitespace_from_name_and_phone() -> None:
    customer = CustomerCreate(name="  Ana Pérez  ", phone="  099 123 4567  ")

    assert customer.name == "Ana Pérez"
    assert customer.phone == "099 123 4567"
