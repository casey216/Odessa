from datetime import date, datetime
from enum import StrEnum
from typing import Literal, Self
from uuid import UUID

from pydantic import ConfigDict, EmailStr, model_validator

from app.core.exceptions.base import ValidationError
from app.core.exceptions.validation import DateFilterError, PasswordError
from app.schemas.base import FormBaseModel


class UserBase(FormBaseModel):
    full_name: str
    phone: str | None = None
    department: str | None = None


class UserRole(StrEnum):
    admin = "admin"
    fleet_manager = "fleet_manager"
    maintenance_manager = "maintenance_manager"
    driver = "driver"
    viewer = "viewer"


class UserCreate(UserBase):
    email: EmailStr
    password: str
    confirm_password: str
    role: UserRole = UserRole.viewer

    @model_validator(mode="after")
    def validate_password(self) -> Self:
        if self.password != self.confirm_password:
            raise PasswordError("Passwords do not match.")
        return self


class UserUpdate(FormBaseModel):
    full_name: str | None = None
    phone: str | None = None
    department: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    avatar_url: str | None = None


class UserOut(UserBase):
    id: UUID
    email: EmailStr
    role: UserRole
    is_active: bool
    avatar_url: str | None = None
    preferences: dict | None = None
    created_at: datetime
    updated_at: datetime | None = None
    last_login: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProfileUpdate(FormBaseModel):
    full_name: str | None = None
    phone: str | None = None
    department: str | None = None


class SortField(StrEnum):
    FULL_NAME = "full_name"
    EMAIL = "email"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    LAST_LOGIN = "last_login"
    ROLE = "role"


class UserFilter(FormBaseModel):
    search: str | None = None

    role: UserRole | None = None
    is_active: bool | None = None
    is_super_user: bool | None = None
    department: str | None = None
    include_deleted: bool | None = False

    created_from: date | None = None
    created_to: date | None = None

    last_login_from: date | None = None
    last_login_to: date | None = None
    never_logged_in: bool | None = None

    sort_by: SortField = SortField.FULL_NAME
    sort_order: Literal["asc", "desc"] = "asc"

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if (
            self.created_from
            and self.created_to
            and self.created_from > self.created_to
        ):
            raise DateFilterError("created_at")

        if (
            self.last_login_from
            and self.last_login_to
            and self.last_login_from > self.last_login_to
        ):
            raise DateFilterError("last_login")

        return self

    @model_validator(mode="after")
    def validate_last_login_exclusivity(self) -> Self:
        if self.never_logged_in is not None and (
            self.last_login_to or self.last_login_from
        ):
            raise ValidationError(
                "Cannot set never_logged and logged_in date range simultaneously."
            )
        return self
