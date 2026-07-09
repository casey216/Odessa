from datetime import date, datetime
from enum import StrEnum
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, model_validator

from app.core.exceptions.validation import DateFilterError
from app.schemas.base import FormBaseModel


class ManufacturerCreate(FormBaseModel):
    name: str


class ManufacturerUpdate(FormBaseModel):
    name: str | None = None


class ManufacturerOut(BaseModel):
    id: UUID
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None
    created_by: UUID | None
    updated_by: UUID | None

    model_config = {"from_attributes": True}


class SortField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class ManufacturerFilter(FormBaseModel):
    search: str | None = None

    is_active: bool | None = None
    created_by: UUID | None = None
    min_date: date | None = None
    max_date: date | None = None
    include_deleted: bool | None = None

    sort_by: SortField = SortField.CREATED_AT
    sort_order: Literal["asc", "desc"] = "desc"

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if self.min_date and self.max_date and self.min_date > self.max_date:
            raise DateFilterError("created_at")
        return self
