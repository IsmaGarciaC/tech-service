from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.customers.models import Customer
from app.modules.devices.models import Device
from app.modules.devices.schemas import DeviceCreate, DeviceUpdate


def create_device(db: Session, data: DeviceCreate) -> Device | None:
    try:
        # Keep the owner's key valid until the foreign key is written.
        owner = select(Customer.id).where(Customer.id == data.customer_id)
        if db.scalar(owner.with_for_update(read=True, key_share=True)) is None:
            db.rollback()
            return None
        device = Device(**data.model_dump())
        db.add(device)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return device


def list_devices(
    db: Session, limit: int, offset: int, customer_id: int | None = None
) -> Sequence[Device]:
    query = select(Device)
    if customer_id is not None:
        query = query.where(Device.customer_id == customer_id)
    return db.scalars(query.order_by(Device.id).limit(limit).offset(offset)).all()


def get_device(db: Session, device_id: int) -> Device | None:
    return db.get(Device, device_id)


def update_device(db: Session, device_id: int, data: DeviceUpdate) -> Device | None:
    try:
        device = db.get(Device, device_id, with_for_update=True, populate_existing=True)
        if device is not None:
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(device, field, value)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return device
