from datetime import date, datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    UUID as SAUUID,
)
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_extensions import uuid7

from app.core.database import Base
from app.models.tag import vehicle_tags

if TYPE_CHECKING:
    from app.models.tag import Tag
    from app.models.user import User
    from app.models.vehicle_model import VehicleModel


class VehicleStatus(str, PyEnum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    IN_MAINTENANCE = "in_maintenance"
    OUT_OF_SERVICE = "out_of_service"
    RETIRED = "retired"


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        Index(
            "ix_vehicles_vin_active",
            "vin",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "ix_vehicles_license_plate_active",
            "license_plate",
            unique=True,
            postgresql_where=text("deleted_at IS NULL AND license_plate IS NOT NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(SAUUID, primary_key=True, default=uuid7)

    vin: Mapped[str] = mapped_column(String(17), nullable=False)
    license_plate: Mapped[str | None] = mapped_column(String(20))
    color: Mapped[str | None] = mapped_column(String(50))

    status: Mapped[VehicleStatus] = mapped_column(
        SAEnum(VehicleStatus, name="vehicle_status"),
        nullable=False,
        default=VehicleStatus.AVAILABLE,
    )

    odometer_km: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    purchase_date: Mapped[date | None] = mapped_column(Date)
    purchase_price: Mapped[float | None] = mapped_column(Numeric(12, 2))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    vehicle_model_id: Mapped[UUID] = mapped_column(
        SAUUID, ForeignKey("vehicle_models.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_by: Mapped[UUID | None] = mapped_column(SAUUID, ForeignKey("users.id"))
    updated_by: Mapped[UUID | None] = mapped_column(SAUUID, ForeignKey("users.id"))

    # Relationships
    vehicle_model: Mapped["VehicleModel"] = relationship(
        foreign_keys=[vehicle_model_id], back_populates="vehicles"
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary=vehicle_tags, back_populates="vehicles"
    )
    assignments = relationship(
        "VehicleAssignment",
        back_populates="vehicle",
        foreign_keys="VehicleAssignment.vehicle_id",
    )

    created_by_user: Mapped["User | None"] = relationship(foreign_keys=[created_by])
    updated_by_user: Mapped["User | None"] = relationship(foreign_keys=[updated_by])

    def __repr__(self) -> str:
        return f"<Vehicle id={self.id} vin={self.vin!r} status={self.status}>"
