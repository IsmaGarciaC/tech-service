from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.customers.models import Customer
from app.modules.customers.schemas import CustomerCreate, CustomerUpdate


def create_customer(db: Session, data: CustomerCreate) -> Customer:
    customer = Customer(**data.model_dump())
    try:
        db.add(customer)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return customer


def list_customers(db: Session, limit: int, offset: int) -> Sequence[Customer]:
    query = select(Customer).order_by(Customer.id).limit(limit).offset(offset)
    return db.scalars(query).all()


def get_customer(db: Session, customer_id: int) -> Customer | None:
    return db.get(Customer, customer_id)


def update_customer(
    db: Session, customer_id: int, data: CustomerUpdate
) -> Customer | None:
    try:
        customer = db.get(
            Customer, customer_id, with_for_update=True, populate_existing=True
        )
        if customer is not None:
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(customer, field, value)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return customer
