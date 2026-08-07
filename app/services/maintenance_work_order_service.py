from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ImmutableStateError,
    InvalidStatusTransitionError,
    NotFoundError,
)
from app.core.pagination import PaginatedResponse, paginate
from app.core.utils import is_unique_violation, parse_unique_violation
from app.crud.maintenance_work_order import MaintenanceWorkOrderCrud
from app.crud.workshop import WorkshopCrud
from app.models import User
from app.models.maintenance_work_order import (
    MaintenanceWorkOrder,
    MaintenanceWorkOrderStatus,
)
from app.schemas.base import QueryParams
from app.schemas.maintenance_work_order import (
    MaintenanceWorkOrderCreate,
    MaintenanceWorkOrderOut,
    MaintenanceWorkOrderUpdate,
)

from .base import BaseService

_ALLOWED_TRANSITIONS: dict[MaintenanceWorkOrderStatus, set[MaintenanceWorkOrderStatus]] = {
    MaintenanceWorkOrderStatus.draft: {
        MaintenanceWorkOrderStatus.scheduled,
        MaintenanceWorkOrderStatus.cancelled,
    },
    MaintenanceWorkOrderStatus.scheduled: {
        MaintenanceWorkOrderStatus.in_progress,
        MaintenanceWorkOrderStatus.cancelled,
    },
    MaintenanceWorkOrderStatus.in_progress: {
        MaintenanceWorkOrderStatus.completed,
        MaintenanceWorkOrderStatus.cancelled,
    },
    MaintenanceWorkOrderStatus.completed: {
        MaintenanceWorkOrderStatus.closed,
    },
    MaintenanceWorkOrderStatus.closed: set(),
    MaintenanceWorkOrderStatus.cancelled: set(),
}

_NON_EDITABLE_STATUSES = {
    MaintenanceWorkOrderStatus.completed,
    MaintenanceWorkOrderStatus.closed,
    MaintenanceWorkOrderStatus.cancelled,
}


class MaintenanceWorkOrderService(BaseService[MaintenanceWorkOrderCrud, MaintenanceWorkOrder]):
    crud = MaintenanceWorkOrderCrud()
    FILTER_FIELDS = {
        "vehicle_id",
        "workshop_id",
        "maintenance_type",
        "priority",
        "status",
        "created_by",
    }
    DATE_FIELDS = [
        ("created_from", "created_to", "created_at"),
        ("scheduled_from", "scheduled_to", "scheduled_date"),
    ]
    out_schema = MaintenanceWorkOrderOut

    async def create(
        self, db: AsyncSession, data: MaintenanceWorkOrderCreate, current_user: User
    ) -> MaintenanceWorkOrder:
        try:
            instance = await self.crud.create(
                db,
                {
                    "reference_no": await self._generate_reference_no(db),
                    "created_by": current_user.id,
                    **data.model_dump(),
                },
            )
            await db.commit()
            await db.refresh(instance)
            return instance
        except IntegrityError as e:
            await db.rollback()
            if is_unique_violation(e):
                raise ConflictError(parse_unique_violation(e)) from e
            raise

    async def get_by_reference_number(
        self, db: AsyncSession, reference_number: str
    ) -> MaintenanceWorkOrder:
        instance = await self.crud.get_by_reference_no(db, reference_no=reference_number)
        if not instance:
            raise NotFoundError("Maintenance Work Order", reference_number)
        return instance

    async def get_with_details(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        include_deleted: bool = False,
    ) -> MaintenanceWorkOrder:
        instance = await self.crud.get_with_details(db, id=id, include_deleted=include_deleted)
        if not instance:
            raise NotFoundError("Maintenance Work Order", id)
        return instance

    async def get_by_vehicle(
        self, db: AsyncSession, vehicle_id: UUID
    ) -> list[MaintenanceWorkOrder]:
        return await self.crud.get_by_vehicle(db, vehicle_id=vehicle_id)

    async def get_active_by_vehicle(
        self, db: AsyncSession, vehicle_id: UUID
    ) -> list[MaintenanceWorkOrder]:
        return await self.crud.get_active_by_vehicle(db, vehicle_id=vehicle_id)

    async def get_due(self, db: AsyncSession) -> list[MaintenanceWorkOrder]:
        return await self.crud.get_due(db)

    async def get_overdue(self, db: AsyncSession) -> list[MaintenanceWorkOrder]:
        return await self.crud.get_overdue(db)

    async def list(
        self, request: Request, db: AsyncSession, params: QueryParams
    ) -> PaginatedResponse[out_schema]:
        filters = self._build_post_filters(params.filters)
        query = self.crud.build_query(
            filters=filters,
            sort_by=params.filters.sort_by,
            order_by=params.filters.sort_order,
        )
        return await paginate(request, db, query, params.pagination, self.out_schema)

    async def update(
        self,
        db: AsyncSession,
        id: UUID,
        data: MaintenanceWorkOrderUpdate,
        current_user: User,
    ) -> MaintenanceWorkOrder:
        order = await self.crud.get_or_404(db, id)
        if order.status in _NON_EDITABLE_STATUSES:
            raise ImmutableStateError(order.status.value, "update", "maintenance work order")

        if data.workshop_id is not None and data.workshop_id != order.workshop_id:
            await WorkshopCrud().get_or_404(db, data.workshop_id)

        try:
            instance = await self.crud.update(
                db,
                id,
                {"updated_by": current_user.id, **data.model_dump(exclude_unset=True)},
            )
            await db.commit()
            await db.refresh(instance)
            return instance
        except IntegrityError as e:
            if is_unique_violation(e):
                raise ConflictError(parse_unique_violation(e)) from e
            raise

    async def delete(self, db: AsyncSession, id: UUID, soft: bool = True) -> None:
        if soft:
            await self.crud.soft_delete(db, id)
        else:
            await self.crud.delete(db, id)
        await db.commit()

    async def schedule(self, db: AsyncSession, id: UUID) -> MaintenanceWorkOrder:
        return await self._transition(db, id, MaintenanceWorkOrderStatus.scheduled)

    async def start(self, db: AsyncSession, id: UUID) -> MaintenanceWorkOrder:
        return await self._transition(
            db, id, MaintenanceWorkOrderStatus.in_progress, started_at=datetime.now(UTC)
        )

    async def complete(self, db: AsyncSession, id: UUID) -> MaintenanceWorkOrder:
        return await self._transition(
            db, id, MaintenanceWorkOrderStatus.completed, completed_at=datetime.now(UTC)
        )

    async def close(self, db: AsyncSession, id: UUID) -> MaintenanceWorkOrder:
        return await self._transition(
            db, id, MaintenanceWorkOrderStatus.closed, closed_at=datetime.now(UTC)
        )

    async def cancel(self, db: AsyncSession, id: UUID) -> MaintenanceWorkOrder:
        return await self._transition(db, id, MaintenanceWorkOrderStatus.cancelled)

    async def _transition(
        self,
        db: AsyncSession,
        id: UUID,
        target_status: MaintenanceWorkOrderStatus,
        **extra_fields,
    ) -> MaintenanceWorkOrder:
        instance = await self.crud.get_or_404(db, id)
        allowed = _ALLOWED_TRANSITIONS.get(instance.status, set())
        if target_status not in allowed:
            raise InvalidStatusTransitionError(instance.status.value, target_status.value)

        instance.status = target_status
        for field, value in extra_fields.items():
            setattr(instance, field, value)

        await db.commit()
        await db.refresh(instance)
        return instance

    async def _generate_reference_no(self, db: AsyncSession) -> str:
        """Builds a unique, human-readable reference number scoped to the
        current month, e.g. MWO-202608-0001, MWO-202608-0002, etc.
        """
        today = date.today()
        prefix = f"MWO-{today:%Y%m}"
        count = await self.crud.count_by_reference_prefix(db, prefix=prefix)
        return f"{prefix}-{count + 1:04d}"


maintenance_work_order_service = MaintenanceWorkOrderService()
