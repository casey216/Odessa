from datetime import date, datetime
from enum import StrEnum
from typing import Literal, Self
from uuid import UUID

from pydantic import model_validator

from app.core.exceptions import DateFilterError

from .base import FormBaseModel


class SortField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class WorkshopCreate(FormBaseModel):
    name: str
    address: str | None
    phone: str | None


class WorkshopUpdate(FormBaseModel):
    name: str | None
    address: str | None
    phone: str | None


class WorkshopOut(FormBaseModel):
    id: UUID
    name: str
    address: str
    phone: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: datetime
    updated_by: datetime

    model_config = {"from_attributes": True}


class WorkshopFilter(FormBaseModel):
    search: str | None = None

    is_active: bool = True
    created_by: UUID | None = None
    created_from: date | None = None
    created_to: date | None = None
    include_deleted: bool | None = None

    sort_by: SortField = SortField.CREATED_AT
    sort_order: Literal["asc", "desc"] = "desc"

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if self.created_from and self.created_to and self.created_from > self.created_to:
            raise DateFilterError("created_at")
        return self
