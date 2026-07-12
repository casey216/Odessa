from datetime import date, datetime
from enum import StrEnum
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.core.exceptions.validation import DateFilterError
from app.models.vehicle_model import FuelType, TransmissionType
from app.schemas.base import FormBaseModel

MIN_YEAR = 1900
MAX_YEAR = 2100


class VehicleModelCreate(FormBaseModel):
    name: str
    year: int = Field(ge=MIN_YEAR, le=MAX_YEAR)
    manufacturer_id: UUID
    fuel_type: FuelType
    transmission: TransmissionType
    seating_capacity: int | None = Field(default=None, ge=1)
    engine_displacement_cc: int | None = Field(default=None, ge=0)
    horsepower: int | None = Field(default=None, ge=0)


class VehicleModelUpdate(FormBaseModel):
    name: str | None = None
    year: int | None = Field(default=None, ge=MIN_YEAR, le=MAX_YEAR)
    manufacturer_id: UUID | None = None
    fuel_type: FuelType | None = None
    transmission: TransmissionType | None = None
    seating_capacity: int | None = Field(default=None, ge=1)
    engine_displacement_cc: int | None = Field(default=None, ge=0)
    horsepower: int | None = Field(default=None, ge=0)


class ManufacturerRef(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class VehicleModelOut(BaseModel):
    id: UUID
    name: str
    year: int
    fuel_type: FuelType
    transmission: TransmissionType
    seating_capacity: int | None
    engine_displacement_cc: int | None
    horsepower: int | None
    is_active: bool
    manufacturer_id: UUID
    manufacturer: ManufacturerRef
    created_at: datetime
    updated_at: datetime | None
    created_by: UUID | None
    updated_by: UUID | None

    model_config = {"from_attributes": True}


class SortField(StrEnum):
    NAME = "name"
    YEAR = "year"
    MANUFACTURER_NAME = "manufacturer_name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class VehicleModelFilter(FormBaseModel):
    search: str | None = None

    is_active: bool | None = None
    manufacturer_id: UUID | None = None
    fuel_type: FuelType | None = None
    transmission: TransmissionType | None = None
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
