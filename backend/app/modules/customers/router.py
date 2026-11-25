from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.customers import service
from app.modules.customers.models import Customer
from app.modules.customers.schemas import CustomerCreate, CustomerRead, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])
BIGINT_MAX = 2**63 - 1
CustomerId = Annotated[int, Path(ge=1, le=BIGINT_MAX)]
Database = Annotated[Session, Depends(get_db)]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CustomerRead)
def create_customer(data: CustomerCreate, db: Database) -> Customer:
    return service.create_customer(db, data)


@router.get("", response_model=list[CustomerRead])
def list_customers(
    db: Database,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0, le=BIGINT_MAX)] = 0,
) -> Sequence[Customer]:
    return service.list_customers(db, limit, offset)


def require_customer(customer: Customer | None) -> Customer:
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


@router.get("/{id}", response_model=CustomerRead, responses={404: {}})
def get_customer(id: CustomerId, db: Database) -> Customer:
    return require_customer(service.get_customer(db, id))


@router.patch("/{id}", response_model=CustomerRead, responses={404: {}})
def update_customer(id: CustomerId, data: CustomerUpdate, db: Database) -> Customer:
    return require_customer(service.update_customer(db, id, data))
