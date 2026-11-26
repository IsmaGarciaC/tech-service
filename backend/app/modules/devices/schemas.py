from typing import Annotated

from pydantic import MISSING, BaseModel, ConfigDict, Field

from app.core.api import Limit, Offset, PositiveId

DeviceText = Annotated[str, Field(pattern=r"^[^\x00]*$")]
DeviceType = Annotated[DeviceText, Field(min_length=1, max_length=50)]


class _DeviceFields(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    device_type: DeviceType
    brand: Annotated[DeviceText, Field(max_length=80)] | None = None
    model: Annotated[DeviceText, Field(max_length=120)] | None = None
    serial_number: Annotated[DeviceText, Field(max_length=120)] | None = None


class DeviceCreate(_DeviceFields):
    customer_id: Annotated[PositiveId, Field(strict=True)]


class DeviceUpdate(_DeviceFields):
    device_type: DeviceType | MISSING = MISSING


class DeviceRead(DeviceCreate):
    model_config = ConfigDict(
        from_attributes=True, json_schema_serialization_defaults_required=True
    )

    id: PositiveId


class DeviceListParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: PositiveId | None = None
    limit: Limit = 20
    offset: Offset = 0
