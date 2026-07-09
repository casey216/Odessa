from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import UUID as SAUUID
from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_extensions import uuid7

from app.core.database import Base


class PermissionEffect(StrEnum):
    allow = "allow"
    deny = "deny"


class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[UUID] = mapped_column(SAUUID, primary_key=True, default=uuid7)
    code: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(500))

    user_links = relationship("UserPermission", back_populates="permission")


class UserPermission(Base):
    __tablename__ = "user_permissions"
    user_id: Mapped[UUID] = mapped_column(
        SAUUID, ForeignKey("users.id"), primary_key=True, index=True
    )
    permission_id: Mapped[UUID] = mapped_column(
        SAUUID, ForeignKey("permissions.id"), primary_key=True, index=True
    )
    effect: Mapped[PermissionEffect] = mapped_column(
        Enum(PermissionEffect), default=PermissionEffect.allow
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user = relationship("User", back_populates="permission_links")
    permission = relationship("Permission", back_populates="user_links")
