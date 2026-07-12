from datetime import datetime
from enum import Enum as PyEnum
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
    Integer,
    String,
    func,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_extensions import uuid7

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.manufacturer import Manufacturer
    from app.models.user import User
    from app.models.vehicle import Vehicle


class FuelType(str, PyEnum):
    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    CNG = "cng"


class TransmissionType(str, PyEnum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    CVT = "cvt"
    DUAL_CLUTCH = "dual_clutch"


class VehicleModel(Base):
    __tablename__ = "vehicle_models"
    __table_args__ = (
        Index(
            "ix_vehicle_models_manufacturer_name_year_active",
            "manufacturer_id",
            "name",
            "year",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[UUID] = mapped_column(SAUUID, primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    fuel_type: Mapped[FuelType] = mapped_column(
        SAEnum(FuelType, name="fuel_type"), nullable=False
    )
    transmission: Mapped[TransmissionType] = mapped_column(
        SAEnum(TransmissionType, name="transmission_type"), nullable=False
    )

    seating_capacity: Mapped[int | None] = mapped_column(Integer)
    engine_displacement_cc: Mapped[int | None] = mapped_column(Integer)
    horsepower: Mapped[int | None] = mapped_column(Integer)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    manufacturer_id: Mapped[UUID] = mapped_column(
        SAUUID, ForeignKey("manufacturers.id"), nullable=False
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

    manufacturer: Mapped["Manufacturer"] = relationship(
        foreign_keys=[manufacturer_id], back_populates="vehicle_models"
    )
    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="vehicle_model")
    created_by_user: Mapped["User | None"] = relationship(foreign_keys=[created_by])
    updated_by_user: Mapped["User | None"] = relationship(foreign_keys=[updated_by])

    def __repr__(self) -> str:
        return f"<VehicleModel id={self.id} name={self.name!r} year={self.year}>"
