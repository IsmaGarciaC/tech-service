from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.core.api import Database, PositiveId
from app.modules.devices import service
from app.modules.devices.models import Device
from app.modules.devices.schemas import (
    DeviceCreate,
    DeviceListParams,
    DeviceRead,
    DeviceUpdate,
)

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=DeviceRead,
    responses={404: {"description": "Customer not found"}},
)
def create_device(data: DeviceCreate, db: Database) -> Device:
    device = service.create_device(db, data)
    if device is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return device


@router.get("", response_model=list[DeviceRead])
def list_devices(
    db: Database, params: Annotated[DeviceListParams, Query()]
) -> Sequence[Device]:
    return service.list_devices(db, params.limit, params.offset, params.customer_id)


def require_device(device: Device | None) -> Device:
    if device is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


@router.get("/{id}", response_model=DeviceRead, responses={404: {}})
def get_device(id: PositiveId, db: Database) -> Device:
    return require_device(service.get_device(db, id))


@router.patch("/{id}", response_model=DeviceRead, responses={404: {}})
def update_device(id: PositiveId, data: DeviceUpdate, db: Database) -> Device:
    return require_device(service.update_device(db, id, data))
