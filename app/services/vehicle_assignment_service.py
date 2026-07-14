from datetime import UTC, datetime
from uuid import UUID

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.base import ConflictError, ValidationError
from app.core.pagination import PaginatedResponse, paginate
from app.core.utils import is_unique_violation, parse_unique_violation
from app.crud.vehicle_assignment import VehicleAssignmentCrud
from app.models.user import User
from app.models.vehicle_assignment import (
    AssignmentStatus,
    AssignmentType,
    VehicleAssignment,
)
from app.schemas.base import QueryParams
from app.schemas.vehicle_assignment import (
    DriverAssignmentClose,
    DriverAssignmentCreate,
    FleetManagerAssignmentClose,
    FleetManagerAssignmentCreate,
    VehicleAssignmentOut,
    VehicleAssignmentUpdate,
)
from app.services.base import BaseService
from app.services.user_service import user_service
from app.services.vehicle_service import vehicle_service


class VehicleAssignmentService(BaseService[VehicleAssignmentCrud]):
    crud = VehicleAssignmentCrud()
    out_schema = VehicleAssignmentOut
    FILTER_FIELDS = {
        "vehicle_id",
        "user_id",
        "assignment_type",
        "status",
        "created_by",
    }
    DATE_FIELDS = [
        ("assigned_from", "assigned_to", "assigned_at"),
    ]

    async def create(
        self,
        db: AsyncSession,
        data: DriverAssignmentCreate | FleetManagerAssignmentCreate,
        current_user: User,
    ) -> VehicleAssignment:
        await vehicle_service.get_or_404(db, data.vehicle_id)
        await user_service.get_or_404(db, data.user_id, current_user)

        existing_for_vehicle = await self.crud.get_active_for_vehicle(
            db, vehicle_id=data.vehicle_id, assignment_type=data.assignment_type
        )
        if existing_for_vehicle is not None:
            raise ConflictError(
                f"Vehicle already has an active "
                f"{data.assignment_type.value} assignment."
            )

        if data.assignment_type == AssignmentType.DRIVER:
            existing_for_driver = await self.crud.get_active_driver_assignment_for_user(
                db, user_id=data.user_id
            )
            if existing_for_driver is not None:
                raise ConflictError(
                    "User already has an active driver assignment "
                    "on another vehicle."
                )

        payload = data.model_dump()

        try:
            instance = await self.crud.create(
                db,
                {
                    "created_by": current_user.id,
                    "assigned_by": current_user.id,
                    **payload,
                },
            )
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            if is_unique_violation(e):
                raise ConflictError(parse_unique_violation(e)) from e
            raise
        return await self.crud.get_or_404(db, instance.id)

    async def get(self, db: AsyncSession, id: UUID) -> VehicleAssignment | None:
        return await self.crud.get(db, id)

    async def get_or_404(self, db: AsyncSession, id: UUID) -> VehicleAssignment:
        return await self.crud.get_or_404(db, id)

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
        data: VehicleAssignmentUpdate,
        current_user: User,
    ) -> VehicleAssignment:
        instance = await self.crud.get_or_404(db, id)
        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if getattr(instance, key, None) != value:
                setattr(instance, key, value)
        instance.updated_by = current_user.id
        await db.commit()

        return await self.crud.get_or_404(db, id)

    async def delete(self, db: AsyncSession, id: UUID, soft: bool = True) -> None:
        if soft:
            await self.crud.soft_delete(db, id)
        else:
            await self.crud.delete(db, id)
        await db.commit()

    async def exists(self, db: AsyncSession, id: UUID) -> bool:
        return await self.crud.exists(db, id)

    async def count(self, db: AsyncSession, id: UUID) -> int:
        return await self.crud.count(db)

    async def complete(
        self, db: AsyncSession, id: UUID, current_user: User, data
    ) -> VehicleAssignment:
        return await self._end_assignment(db, id, current_user, data)

    async def cancel(
        self, db: AsyncSession, id: UUID, current_user: User, data
    ) -> VehicleAssignment:
        return await self._end_assignment(db, id, current_user, data)

    async def _end_assignment(
        self,
        db: AsyncSession,
        id: UUID,
        current_user: User,
        data: DriverAssignmentClose | FleetManagerAssignmentClose,
    ) -> VehicleAssignment:
        instance = await self.crud.get_or_404(db, id)
        if instance.status != AssignmentStatus.ACTIVE:
            raise ValidationError(f"Only active assignments can be {data.status}.")
        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if getattr(instance, key, None) != value:
                setattr(instance, key, value)

        instance.unassigned_at = datetime.now(UTC)
        instance.unassigned_by = current_user.id
        instance.updated_by = current_user.id
        await db.commit()

        return await self.crud.get_or_404(db, id)


vehicle_assignment_service = VehicleAssignmentService()
