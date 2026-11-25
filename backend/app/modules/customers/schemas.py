from typing import Annotated

from pydantic import MISSING, BaseModel, ConfigDict, EmailStr, Field

CustomerName = Annotated[
    str, Field(min_length=1, max_length=120, pattern=r"^[^\x00]*$")
]
CustomerPhone = Annotated[
    str, Field(min_length=1, max_length=30, pattern=r"^[^\x00]*$")
]


class CustomerCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: CustomerName
    phone: CustomerPhone
    email: EmailStr | None = Field(default=None, max_length=254)


class CustomerUpdate(CustomerCreate):
    name: CustomerName | MISSING = MISSING
    phone: CustomerPhone | MISSING = MISSING


class CustomerRead(CustomerCreate):
    model_config = ConfigDict(
        from_attributes=True, json_schema_serialization_defaults_required=True
    )

    id: int
