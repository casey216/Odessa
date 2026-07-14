from datetime import date, datetime
from enum import StrEnum
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.core.exceptions.validation import DateFilterError
from app.models.vehicle_assignment import AssignmentStatus, AssignmentType
from app.schemas.base import FormBaseModel

NOTES_MAX_LENGTH = 500


class VehicleRef(BaseModel):
    id: UUID
    vin: str
    license_plate: str | None

    model_config = {"from_attributes": True}


class UserRef(BaseModel):
    id: UUID
    full_name: str

    model_config = {"from_attributes": True}


class DriverAssignmentCreate(FormBaseModel):
    vehicle_id: UUID
    user_id: UUID
    assignment_type: AssignmentType = AssignmentType.DRIVER
    odometer_out_km: int = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=NOTES_MAX_LENGTH)


class FleetManagerAssignmentCreate(FormBaseModel):
    vehicle_id: UUID
    user_id: UUID
    assignment_type: AssignmentType = AssignmentType.FLEET_MANAGER
    notes: str | None = Field(default=None, max_length=NOTES_MAX_LENGTH)


class VehicleAssignmentUpdate(FormBaseModel):
    odometer_out_km: int | None = Field(default=None, ge=0)
    odometer_in_km: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=NOTES_MAX_LENGTH)


class DriverAssignmentClose(BaseModel):
    status: Literal[AssignmentStatus.COMPLETED, AssignmentStatus.CANCELLED]
    odometer_in_km: int = Field(ge=0)
    notes: str | None = None


class FleetManagerAssignmentClose(BaseModel):
    status: Literal[AssignmentStatus.COMPLETED, AssignmentStatus.CANCELLED]
    notes: str | None = None


class VehicleAssignmentOut(BaseModel):
    id: UUID
    vehicle_id: UUID
    user_id: UUID
    assignment_type: AssignmentType
    odometer_out_km: int | None
    odometer_in_km: int | None
    status: AssignmentStatus
    assigned_at: datetime
    unassigned_at: datetime | None
    assigned_by: UUID | None
    unassigned_by: UUID | None
    notes: str | None
    vehicle: VehicleRef
    assigned_to_user: UserRef | None
    created_at: datetime
    updated_at: datetime | None
    created_by: UUID | None
    updated_by: UUID | None

    model_config = {"from_attributes": True}


class SortField(StrEnum):
    ASSIGNED_AT = "assigned_at"
    UNASSIGNED_AT = "unassigned_at"
    STATUS = "status"
    ASSIGNMENT_TYPE = "assignment_type"
    VEHICLE_VIN = "vehicle_vin"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class VehicleAssignmentFilter(FormBaseModel):
    search: str | None = None

    vehicle_id: UUID | None = None
    user_id: UUID | None = None
    assignment_type: AssignmentType | None = None
    status: AssignmentStatus | None = None
    created_by: UUID | None = None
    assigned_from: date | None = None
    assigned_to: date | None = None
    include_deleted: bool | None = None

    sort_by: SortField = SortField.ASSIGNED_AT
    sort_order: Literal["asc", "desc"] = "desc"

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if (
            self.assigned_from
            and self.assigned_to
            and self.assigned_from > self.assigned_to
        ):
            raise DateFilterError("assigned_at")
        return self
