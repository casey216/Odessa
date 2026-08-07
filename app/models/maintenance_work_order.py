from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import UUID as SAUUID
from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_extensions import uuid7

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.vehicle import Vehicle
    from app.models.workshop import Workshop


class MaintenanceType(StrEnum):
    preventive = "preventive"
    corrective = "corrective"
    inspection = "inspection"
    emergency = "emergency"


class MaintenancePriority(StrEnum):
    low = "low"
    normal = "normal"
    high = "high"
    critical = "critical"


class MaintenanceWorkOrderStatus(StrEnum):
    draft = "draft"
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    closed = "closed"
    cancelled = "cancelled"


class MaintenanceWorkOrder(Base):
    __tablename__ = "maintenance_work_orders"
    __table_args__ = (
        Index(
            "ix_maintenance_work_orders_vehicle_status",
            "vehicle_id",
            "status",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        SAUUID,
        primary_key=True,
        default=uuid7,
    )
    reference_no: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
    )
    vehicle_id: Mapped[UUID] = mapped_column(
        SAUUID,
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    workshop_id: Mapped[UUID] = mapped_column(
        SAUUID,
        ForeignKey("workshops.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[UUID] = mapped_column(
        SAUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        SAUUID,
        ForeignKey("users.id", ondelete="RESTRICT"),
    )
    maintenance_type: Mapped[MaintenanceType] = mapped_column(
        Enum(MaintenanceType),
        nullable=False,
    )
    priority: Mapped[MaintenancePriority] = mapped_column(
        Enum(MaintenancePriority),
        nullable=False,
        default=MaintenancePriority.normal,
    )
    status: Mapped[MaintenanceWorkOrderStatus] = mapped_column(
        Enum(MaintenanceWorkOrderStatus),
        nullable=False,
        index=True,
        default=MaintenanceWorkOrderStatus.draft,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
    )
    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    odometer_at_service_km: Mapped[int | None] = mapped_column()
    total_labor_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
    )
    total_parts_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        index=True,
    )

    @hybrid_property
    def total_cost(self) -> Decimal:
        return self.total_labor_cost + self.total_parts_cost

    @total_cost.expression  # type: ignore
    def total_cost_expression(cls):
        return cls.total_labor_cost + cls.total_parts_cost

    # Relationships
    vehicle: Mapped["Vehicle"] = relationship(back_populates="maintenance_work_orders")
    workshop: Mapped["Workshop"] = relationship(back_populates="maintenance_work_orders")
    creator: Mapped["User"] = relationship(
        foreign_keys=[created_by],
    )
    updater: Mapped["User | None"] = relationship(
        foreign_keys=[updated_by],
    )
