from sqlalchemy import BigInteger, CheckConstraint, Identity, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint("name ~ '[^[:space:]]'", name="ck_customers_name_not_blank"),
        CheckConstraint("phone ~ '[^[:space:]]'", name="ck_customers_phone_not_blank"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(254))
