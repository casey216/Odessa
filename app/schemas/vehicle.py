from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.exceptions.validation import DateFilterError
from app.models.tag import VehicleTagChoice
from app.models.vehicle import VehicleStatus
from app.schemas.base import FormBaseModel

VIN_MIN_LENGTH = 11
VIN_MAX_LENGTH = 17


class ManufacturerRef(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class VehicleModelRef(BaseModel):
    id: UUID
    name: str
    year: int
    manufacturer: ManufacturerRef

    model_config = {"from_attributes": True}


class TagOut(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class VehicleCreate(FormBaseModel):
    vin: str = Field(min_length=VIN_MIN_LENGTH, max_length=VIN_MAX_LENGTH)
    license_plate: str | None = None
    color: str | None = None
    status: VehicleStatus = VehicleStatus.AVAILABLE
    odometer_km: int = Field(default=0, ge=0)
    purchase_date: date | None = None
    purchase_price: Decimal | None = Field(default=None, ge=0)
    vehicle_model_id: UUID
    tags: list[VehicleTagChoice] = Field(default_factory=list)

    @field_validator("vin")
    @classmethod
    def normalize_vin(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("purchase_price", "odometer_km", mode="before")
    @classmethod
    def strip_thousands_separators(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.replace(",", "").strip()
            if value == "":
                return None
        return value


class VehicleUpdate(FormBaseModel):
    vin: str | None = Field(
        default=None, min_length=VIN_MIN_LENGTH, max_length=VIN_MAX_LENGTH
    )
    license_plate: str | None = None
    color: str | None = None
    status: VehicleStatus | None = None
    odometer_km: int | None = Field(default=None, ge=0)
    purchase_date: date | None = None
    purchase_price: Decimal | None = Field(default=None, ge=0)
    vehicle_model_id: UUID | None = None
    tags: list[VehicleTagChoice] = Field(default_factory=list)

    @field_validator("vin")
    @classmethod
    def normalize_vin(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value

    @field_validator("purchase_price", mode="before")
    @classmethod
    def strip_thousands_separators(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.replace(",", "").strip()
            if value == "":
                return None
        return value


class VehicleOut(BaseModel):
    id: UUID
    vin: str
    license_plate: str | None
    color: str | None
    status: VehicleStatus
    odometer_km: int
    purchase_date: date | None
    purchase_price: Decimal | None
    is_active: bool
    vehicle_model_id: UUID
    vehicle_model: VehicleModelRef
    tags: list[TagOut]
    created_at: datetime
    updated_at: datetime | None
    created_by: UUID | None
    updated_by: UUID | None

    model_config = {"from_attributes": True}


class SortField(StrEnum):
    VIN = "vin"
    STATUS = "status"
    ODOMETER_KM = "odometer_km"
    VEHICLE_MODEL_NAME = "vehicle_model_name"
    MANUFACTURER_NAME = "manufacturer_name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class VehicleFilter(FormBaseModel):
    search: str | None = None

    is_active: bool | None = None
    status: VehicleStatus | None = None
    vehicle_model_id: UUID | None = None
    manufacturer_id: UUID | None = None
    tag: VehicleTagChoice | None = None
    created_by: UUID | None = None
    created_from: date | None = None
    created_to: date | None = None
    include_deleted: bool | None = None

    sort_by: SortField = SortField.CREATED_AT
    sort_order: Literal["asc", "desc"] = "desc"

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if (
            self.created_from
            and self.created_to
            and self.created_from > self.created_to
        ):
            raise DateFilterError("created_at")
        return self
