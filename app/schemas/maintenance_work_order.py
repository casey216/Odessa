from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal, Self
from uuid import UUID

from pydantic import model_validator

from app.core.exceptions import DateFilterError
from app.models.maintenance_work_order import (
    MaintenancePriority,
    MaintenanceType,
    MaintenanceWorkOrderStatus,
)

from .base import FormBaseModel


class SortField(StrEnum):
    REFERENCE_NO = "reference_no"
    SCHEDULED_DATE = "scheduled_date"
    STATUS = "status"
    PRIORITY = "priority"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class MaintenanceWorkOrderCreate(FormBaseModel):
    vehicle_id: UUID
    workshop_id: UUID
    maintenance_type: MaintenanceType
    priority: MaintenancePriority = MaintenancePriority.normal
    title: str
    description: str | None = None
    scheduled_date: date
    odometer_at_service_km: int | None = None
    notes: str | None = None


class MaintenanceWorkOrderUpdate(FormBaseModel):
    workshop_id: UUID | None = None
    maintenance_type: MaintenanceType | None = None
    priority: MaintenancePriority | None = None
    title: str | None = None
    description: str | None = None
    scheduled_date: date | None = None
    odometer_at_service_km: int | None = None
    total_labor_cost: Decimal | None = None
    total_parts_cost: Decimal | None = None
    notes: str | None = None


class MaintenanceWorkOrderOut(FormBaseModel):
    id: UUID
    reference_no: str
    vehicle_id: UUID
    workshop_id: UUID
    maintenance_type: MaintenanceType
    priority: MaintenancePriority
    status: MaintenanceWorkOrderStatus
    title: str
    description: str | None
    scheduled_date: date
    started_at: datetime | None
    completed_at: datetime | None
    closed_at: datetime | None
    odometer_at_service_km: int | None
    total_labor_cost: Decimal
    total_parts_cost: Decimal
    total_cost: Decimal
    notes: str | None
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID | None

    model_config = {"from_attributes": True}


class MaintenanceWorkOrderFilter(FormBaseModel):
    search: str | None = None

    vehicle_id: UUID | None = None
    workshop_id: UUID | None = None
    maintenance_type: MaintenanceType | None = None
    priority: MaintenancePriority | None = None
    status: MaintenanceWorkOrderStatus | None = None
    created_by: UUID | None = None

    scheduled_from: date | None = None
    scheduled_to: date | None = None
    created_from: date | None = None
    created_to: date | None = None
    include_deleted: bool | None = None

    sort_by: SortField = SortField.SCHEDULED_DATE
    sort_order: Literal["asc", "desc"] = "desc"

    @model_validator(mode="after")
    def validate_date_ranges(self) -> Self:
        if self.scheduled_from and self.scheduled_to and self.scheduled_from > self.scheduled_to:
            raise DateFilterError("scheduled")
        if self.created_from and self.created_to and self.created_from > self.created_to:
            raise DateFilterError("created_at")
        return self
