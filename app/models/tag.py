from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    UUID as SAUUID,
)
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_extensions import uuid7

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.vehicle import Vehicle


class VehicleTagChoice(str, PyEnum):
    """Closed vocabulary for vehicle tags."""

    LEASED = "leased"
    OWNED = "owned"
    POOL_VEHICLE = "pool_vehicle"
    EXECUTIVE = "executive"
    LOANER = "loaner"
    RENTAL = "rental"
    GPS_TRACKED = "gps_tracked"
    EV_CHARGING_REQUIRED = "ev_charging_required"
    UNDER_MAINTENANCE_CONTRACT = "under_maintenance_contract"
    HIGH_MILEAGE = "high_mileage"
    NEEDS_INSPECTION = "needs_inspection"
    DECOMMISSION_PENDING = "decommission_pending"


vehicle_tags = Table(
    "vehicle_tags",
    Base.metadata,
    Column(
        "vehicle_id",
        SAUUID,
        ForeignKey("vehicles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id", SAUUID, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(SAUUID, primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    vehicles: Mapped[list["Vehicle"]] = relationship(
        secondary=vehicle_tags, back_populates="tags"
    )

    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name!r}>"
