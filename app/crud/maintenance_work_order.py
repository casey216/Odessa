from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.maintenance_work_order import MaintenanceWorkOrder, MaintenanceWorkOrderStatus

from .base import BaseCrud

_OPEN_STATUSES = (
    MaintenanceWorkOrderStatus.draft,
    MaintenanceWorkOrderStatus.scheduled,
    MaintenanceWorkOrderStatus.in_progress,
)


class MaintenanceWorkOrderCrud(BaseCrud[MaintenanceWorkOrder]):
    MODEL = MaintenanceWorkOrder
    ALLOWED_COLUMNS = {
        "reference_no": MaintenanceWorkOrder.reference_no,
        "vehicle_id": MaintenanceWorkOrder.vehicle_id,
        "workshop_id": MaintenanceWorkOrder.workshop_id,
        "maintenance_type": MaintenanceWorkOrder.maintenance_type,
        "priority": MaintenanceWorkOrder.priority,
        "status": MaintenanceWorkOrder.status,
        "scheduled_date": MaintenanceWorkOrder.scheduled_date,
        "created_at": MaintenanceWorkOrder.created_at,
        "updated_at": MaintenanceWorkOrder.updated_at,
        "created_by": MaintenanceWorkOrder.created_by,
    }
    SEARCH_COLUMNS = ("reference_no__ilike", "title__ilike")

    async def get_by_reference_no(
        self,
        db: AsyncSession,
        *,
        reference_no: str,
        include_deleted: bool = False,
    ) -> MaintenanceWorkOrder | None:
        """Looks up a work order by its exact reference number."""
        stmt = select(MaintenanceWorkOrder).where(MaintenanceWorkOrder.reference_no == reference_no)
        if not include_deleted:
            stmt = stmt.where(MaintenanceWorkOrder.deleted_at.is_(None))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_reference_prefix(self, db: AsyncSession, *, prefix: str) -> int:
        """Counts (including soft-deleted) work orders whose reference_no starts
        with `prefix`. Used to derive the next sequence number for a new
        reference.
        """
        stmt = (
            select(func.count())
            .select_from(MaintenanceWorkOrder)
            .where(MaintenanceWorkOrder.reference_no.like(f"{prefix}%"))
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    async def get_with_details(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        include_deleted: bool = False,
    ) -> MaintenanceWorkOrder | None:
        """Fetches a work order by ID, including related vehicle and workshop."""
        stmt = (
            select(MaintenanceWorkOrder)
            .where(MaintenanceWorkOrder.id == id)
            .options(
                selectinload(MaintenanceWorkOrder.vehicle),
                selectinload(MaintenanceWorkOrder.workshop),
                selectinload(MaintenanceWorkOrder.creator),
                selectinload(MaintenanceWorkOrder.updater),
            )
        )
        if not include_deleted:
            stmt = stmt.where(MaintenanceWorkOrder.deleted_at.is_(None))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_vehicle(
        self,
        db: AsyncSession,
        *,
        vehicle_id: UUID,
        include_deleted: bool = False,
    ) -> list[MaintenanceWorkOrder]:
        """Fetches all work orders for a given vehicle ID."""
        stmt = select(MaintenanceWorkOrder).where(MaintenanceWorkOrder.vehicle_id == vehicle_id)
        if not include_deleted:
            stmt = stmt.where(MaintenanceWorkOrder.deleted_at.is_(None))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_active_by_vehicle(
        self,
        db: AsyncSession,
        *,
        vehicle_id: UUID,
    ) -> list[MaintenanceWorkOrder]:
        """Fetches all active (not completed or closed) work orders for a given vehicle ID."""
        stmt = (
            select(MaintenanceWorkOrder)
            .where(
                MaintenanceWorkOrder.vehicle_id == vehicle_id,
                MaintenanceWorkOrder.status.in_(_OPEN_STATUSES),
                MaintenanceWorkOrder.deleted_at.is_(None),
            )
            .order_by(
                MaintenanceWorkOrder.scheduled_date.asc(),
                MaintenanceWorkOrder.created_at.asc(),
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_overdue(
        self,
        db: AsyncSession,
    ) -> list[MaintenanceWorkOrder]:
        """Fetches all work orders that are overdue (scheduled date in the past and
        not completed or closed)."""
        stmt = (
            select(MaintenanceWorkOrder)
            .where(
                MaintenanceWorkOrder.status.in_(_OPEN_STATUSES),
                MaintenanceWorkOrder.scheduled_date < func.current_date(),
                MaintenanceWorkOrder.deleted_at.is_(None),
            )
            .order_by(
                MaintenanceWorkOrder.scheduled_date.asc(),
                MaintenanceWorkOrder.created_at.asc(),
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_due(self, db: AsyncSession) -> list[MaintenanceWorkOrder]:
        """Fetches all work orders that are due (scheduled date today and not
        completed or closed)."""
        stmt = (
            select(MaintenanceWorkOrder)
            .where(
                MaintenanceWorkOrder.status.in_(_OPEN_STATUSES),
                MaintenanceWorkOrder.scheduled_date == func.current_date(),
                MaintenanceWorkOrder.deleted_at.is_(None),
            )
            .order_by(
                MaintenanceWorkOrder.scheduled_date.asc(),
                MaintenanceWorkOrder.created_at.asc(),
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
