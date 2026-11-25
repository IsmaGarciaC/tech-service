from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=1, max_length=30)
    email: EmailStr | None = Field(default=None, max_length=254)
