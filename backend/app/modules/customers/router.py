from collections.abc import Sequence

from fastapi import APIRouter, HTTPException, status

from app.core.api import Database, Limit, Offset, PositiveId
from app.modules.customers import service
from app.modules.customers.models import Customer
from app.modules.customers.schemas import CustomerCreate, CustomerRead, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CustomerRead)
def create_customer(data: CustomerCreate, db: Database) -> Customer:
    return service.create_customer(db, data)


@router.get("", response_model=list[CustomerRead])
def list_customers(
    db: Database,
    limit: Limit = 20,
    offset: Offset = 0,
) -> Sequence[Customer]:
    return service.list_customers(db, limit, offset)


def require_customer(customer: Customer | None) -> Customer:
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.get("/{id}", response_model=CustomerRead, responses={404: {}})
def get_customer(id: PositiveId, db: Database) -> Customer:
    return require_customer(service.get_customer(db, id))


@router.patch("/{id}", response_model=CustomerRead, responses={404: {}})
def update_customer(id: PositiveId, data: CustomerUpdate, db: Database) -> Customer:
    return require_customer(service.update_customer(db, id, data))
