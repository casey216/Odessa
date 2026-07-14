from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    UUID as SAUUID,
)
from sqlalchemy import (
    CheckConstraint,
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
    from app.models.user import User
    from app.models.vehicle import Vehicle


class AssignmentType(str, PyEnum):
    DRIVER = "driver"
    FLEET_MANAGER = "fleet_manager"


class AssignmentStatus(str, PyEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VehicleAssignment(Base):
    __tablename__ = "vehicle_assignments"
    __table_args__ = (
        Index(
            "ix_vehicle_assignments_vehicle_type_active",
            "vehicle_id",
            "assignment_type",
            unique=True,
            postgresql_where=text("status = 'ACTIVE' AND deleted_at IS NULL"),
        ),
        Index(
            "ix_vehicle_assignments_driver_one_vehicle",
            "user_id",
            unique=True,
            postgresql_where=text(
                "assignment_type = 'DRIVER' AND status = 'ACTIVE'"
                " AND deleted_at IS NULL"
            ),
        ),
        CheckConstraint(
            "odometer_in_km IS NULL OR odometer_out_km IS NULL "
            "OR odometer_in_km >= odometer_out_km",
            name="ck_vehicle_assignments_odometer_in_gte_out",
        ),
    )

    id: Mapped[UUID] = mapped_column(SAUUID, primary_key=True, default=uuid7)

    vehicle_id: Mapped[UUID] = mapped_column(
        SAUUID, ForeignKey("vehicles.id"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        SAUUID, ForeignKey("users.id"), nullable=False, index=True
    )

    assignment_type: Mapped[AssignmentType] = mapped_column(
        SAEnum(AssignmentType, name="assignment_type"),
        nullable=False,
        index=True,
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        SAEnum(AssignmentStatus, name="assignment_status"),
        nullable=False,
        default=AssignmentStatus.ACTIVE,
        index=True,
    )

    odometer_out_km: Mapped[int | None] = mapped_column(Integer)
    odometer_in_km: Mapped[int | None] = mapped_column(Integer)

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    unassigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    assigned_by: Mapped[UUID | None] = mapped_column(SAUUID, ForeignKey("users.id"))
    unassigned_by: Mapped[UUID | None] = mapped_column(SAUUID, ForeignKey("users.id"))

    notes: Mapped[str | None] = mapped_column(String(500))

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
    vehicle: Mapped["Vehicle"] = relationship(
        foreign_keys=[vehicle_id], back_populates="assignments"
    )

    assigned_to_user: Mapped["User | None"] = relationship(foreign_keys=[user_id])
    assigned_by_user: Mapped["User | None"] = relationship(foreign_keys=[assigned_by])
    unassigned_by_user: Mapped["User | None"] = relationship(
        foreign_keys=[unassigned_by]
    )
    created_by_user: Mapped["User | None"] = relationship(foreign_keys=[created_by])
    updated_by_user: Mapped["User | None"] = relationship(foreign_keys=[updated_by])

    def __repr__(self) -> str:
        return (
            f"<VehicleAssignment id={self.id} vehicle_id={self.vehicle_id} "
            f"user_id={self.user_id} type={self.assignment_type} status={self.status}>"
        )
