from datetime import UTC, datetime
from typing import List
from uuid import UUID

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.base import ConflictError, ValidationError
from app.core.pagination import PaginatedResponse, paginate
from app.core.utils import is_unique_violation, parse_unique_violation
from app.crud.vehicle_assignment import VehicleAssignmentCrud
from app.models.user import User
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.vehicle_assignment import (
    AssignmentStatus,
    AssignmentType,
    VehicleAssignment,
)
from app.policies.vehicle_assignment_policy import VehicleAssignmentPolicy
from app.schemas.base import QueryParams
from app.schemas.vehicle_assignment import (
    DriverAssignmentComplete,
    DriverAssignmentCreate,
    FleetManagerAssignmentComplete,
    FleetManagerAssignmentCreate,
    VehicleAssignmentOut,
    VehicleAssignmentUpdate,
)
from app.services.base import BaseService
from app.services.user_service import user_service
from app.services.vehicle_service import vehicle_service


class VehicleAssignmentService(BaseService[VehicleAssignmentCrud, VehicleAssignment]):
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
        vehicle = await vehicle_service.get_or_404(db, data.vehicle_id)
        await user_service.get_or_404(db, data.user_id)

        if not vehicle.is_active:
            raise ConflictError("Cannot assign inactive vehicle.")

        existing_for_vehicle = await self.crud.get_active_for_vehicle(
            db, vehicle_id=data.vehicle_id, assignment_type=data.assignment_type
        )
        if existing_for_vehicle is not None:
            raise ConflictError(
                f"Vehicle already has an active "
                f"{data.assignment_type.value.replace("_", " ")} assignment."
            )

        if isinstance(data, DriverAssignmentCreate):
            existing_for_driver = await self.crud.get_active_driver_assignment_for_user(
                db, user_id=data.user_id
            )
            if existing_for_driver is not None:
                raise ConflictError(
                    "User already has an active driver assignment on another vehicle."
                )
            if vehicle.status != VehicleStatus.AVAILABLE:
                raise ConflictError(
                    f"Vehicle is {vehicle.status.value}, not available for a driver assignment."
                )
            if data.odometer_out_km < vehicle.odometer_km:
                raise ValidationError(
                    f"Odometer out ({data.odometer_out_km} km) is less than "
                    f"the vehicle's current odometer ({vehicle.odometer_km} km). "
                    "If the vehicle's odometer is incorrect, correct it on "
                    "the vehicle's record first."
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
            if isinstance(data, DriverAssignmentCreate):
                vehicle.status = VehicleStatus.IN_USE
                vehicle.odometer_km = data.odometer_out_km
                vehicle.updated_by = current_user.id
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            if is_unique_violation(e):
                raise ConflictError(parse_unique_violation(e)) from e
            raise
        return await self.crud.get_or_404(db, instance.id)

    async def get_or_403(self, db: AsyncSession, id: UUID, current_user: User) -> VehicleAssignment:
        assignment = await self.crud.get_or_404(db, id)
        VehicleAssignmentPolicy.authorize(
            VehicleAssignmentPolicy.can_read, current_user, assignment
        )
        return assignment

    async def list(
        self, request: Request, db: AsyncSession, params: QueryParams, current_user: User
    ) -> PaginatedResponse[out_schema]:
        filters = self._build_post_filters(params.filters)
        query = self.crud.build_query(
            filters=filters,
            sort_by=params.filters.sort_by,
            order_by=params.filters.sort_order,
        )
        query = VehicleAssignmentPolicy.scope(query, current_user)
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

    async def delete(
        self, db: AsyncSession, id: UUID, current_user: User, soft: bool = True
    ) -> None:
        instance = await self.crud.get_or_404(db, id)
        if (
            instance.assignment_type == AssignmentType.DRIVER
            and instance.status == AssignmentStatus.ACTIVE
        ):
            vehicle = await vehicle_service.get_or_404(db, instance.vehicle_id)
            if vehicle.status == VehicleStatus.IN_USE:
                vehicle.status = VehicleStatus.AVAILABLE
                vehicle.updated_by = current_user.id

        if soft:
            await self.crud.soft_delete(db, id)
        else:
            await self.crud.delete(db, id)
        await db.commit()

    async def complete(
        self,
        db: AsyncSession,
        id: UUID,
        current_user: User,
        data: DriverAssignmentComplete | FleetManagerAssignmentComplete,
    ) -> VehicleAssignment:
        update_data = data.model_dump(exclude_unset=True)
        return await self._end_assignment(
            db, id, current_user, AssignmentStatus.COMPLETED, update_data
        )

    async def cancel(
        self,
        db: AsyncSession,
        id: UUID,
        current_user: User,
        notes: str | None = None,
    ) -> VehicleAssignment:
        update_data = {"notes": notes} if notes is not None else {}
        return await self._end_assignment(
            db, id, current_user, AssignmentStatus.CANCELLED, update_data
        )

    async def get_user_vehicles(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> List[Vehicle]:
        stmt = (
            select(Vehicle)
            .join(VehicleAssignment, VehicleAssignment.vehicle_id == Vehicle.id)
            .where(
                VehicleAssignment.user_id == user_id,
                VehicleAssignment.status == AssignmentStatus.ACTIVE,
                VehicleAssignment.deleted_at.is_(None),
            )
        )

        return list((await db.scalars(stmt)).all())

    async def get_vehicle_current_user(self, db: AsyncSession, vehicle_id: UUID) -> User | None:
        stmt = (
            select(User)
            .join(VehicleAssignment, VehicleAssignment.user_id == User.id)
            .where(
                VehicleAssignment.vehicle_id == vehicle_id,
                VehicleAssignment.status == AssignmentStatus.ACTIVE,
                VehicleAssignment.deleted_at.is_(None),
            )
        )

        return await db.scalar(stmt)

    async def _end_assignment(
        self,
        db: AsyncSession,
        id: UUID,
        current_user: User,
        end_status: AssignmentStatus,
        update_data: dict,
    ) -> VehicleAssignment:
        instance = await self.crud.get_or_404(db, id)
        if instance.status != AssignmentStatus.ACTIVE:
            raise ValidationError(f"Only active assignments can be {end_status.value}.")

        if (
            instance.assignment_type == AssignmentType.DRIVER
            and "odometer_in_km" in update_data
            and update_data["odometer_in_km"] < instance.odometer_out_km
        ):
            raise ValidationError(
                f"Odometer in ({update_data['odometer_in_km']} km) can't be "
                f"less than odometer out ({instance.odometer_out_km} km)."
            )

        for key, value in update_data.items():
            if getattr(instance, key, None) != value:
                setattr(instance, key, value)

        instance.status = end_status
        instance.unassigned_at = datetime.now(UTC)
        instance.unassigned_by = current_user.id
        instance.updated_by = current_user.id

        if instance.assignment_type == AssignmentType.DRIVER:
            vehicle = await vehicle_service.get_or_404(db, instance.vehicle_id)
            vehicle_changed = False
            if vehicle.status == VehicleStatus.IN_USE:
                vehicle.status = VehicleStatus.AVAILABLE
                vehicle_changed = True
            if (
                instance.odometer_in_km is not None
                and instance.odometer_in_km != vehicle.odometer_km
            ):
                vehicle.odometer_km = instance.odometer_in_km
                vehicle_changed = True
            if vehicle_changed:
                vehicle.updated_by = current_user.id

        await db.commit()

        return await self.crud.get_or_404(db, id)


vehicle_assignment_service = VehicleAssignmentService()
