from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    UUID as SAUUID,
)
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_extensions import uuid7

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.vehicle_model import VehicleModel


class Manufacturer(Base):
    __tablename__ = "manufacturers"
    __table_args__ = (
        Index(
            "ix_manufacturers_name_active",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(SAUUID, primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_by: Mapped[UUID | None] = mapped_column(SAUUID, ForeignKey("users.id"))
    updated_by: Mapped[UUID | None] = mapped_column(SAUUID, ForeignKey("users.id"))

    created_by_user: Mapped["User | None"] = relationship(foreign_keys=[created_by])
    updated_by_user: Mapped["User | None"] = relationship(foreign_keys=[updated_by])

    vehicle_models: Mapped[list["VehicleModel"]] = relationship(
        back_populates="manufacturer"
    )

    def __repr__(self) -> str:
        return f"<Manufacturer id={self.id} name={self.name!r}>"
