from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload
from sqlalchemy.sql import Select

from app.crud.base import BaseCrud
from app.models.vehicle import Vehicle
from app.models.vehicle_assignment import (
    AssignmentStatus,
    AssignmentType,
    VehicleAssignment,
)


class VehicleAssignmentCrud(BaseCrud[VehicleAssignment]):
    MODEL = VehicleAssignment
    ALLOWED_COLUMNS = {
        "vehicle_id": VehicleAssignment.vehicle_id,
        "user_id": VehicleAssignment.user_id,
        "assignment_type": VehicleAssignment.assignment_type,
        "status": VehicleAssignment.status,
        "vehicle_vin": Vehicle.vin,
        "assigned_at": VehicleAssignment.assigned_at,
        "unassigned_at": VehicleAssignment.unassigned_at,
        "assigned_by": VehicleAssignment.assigned_by,
        "unassigned_by": VehicleAssignment.unassigned_by,
        "created_at": VehicleAssignment.created_at,
        "updated_at": VehicleAssignment.updated_at,
        "created_by": VehicleAssignment.created_by,
    }
    SEARCH_COLUMNS = (
        "vehicle_vin__ilike",
        "notes__ilike",
    )

    def _base_query(self) -> Select:
        return (
            select(self.MODEL)
            .join(self.MODEL.vehicle)
            .options(
                contains_eager(self.MODEL.vehicle),
                joinedload(self.MODEL.assigned_to_user),
            )
        )

    async def get_active_for_vehicle(
        self,
        db: AsyncSession,
        *,
        vehicle_id: UUID,
        assignment_type: AssignmentType,
    ) -> VehicleAssignment | None:
        """Looks up the current active assignment of a given type for a vehicle."""
        stmt = select(self.MODEL).where(
            self.MODEL.vehicle_id == vehicle_id,
            self.MODEL.assignment_type == assignment_type,
            self.MODEL.status == AssignmentStatus.ACTIVE,
            self.MODEL.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_driver_assignment_for_user(
        self, db: AsyncSession, *, user_id: UUID
    ) -> VehicleAssignment | None:
        """Looks up a driver's current active assignment, if any."""
        stmt = select(self.MODEL).where(
            self.MODEL.user_id == user_id,
            self.MODEL.assignment_type == AssignmentType.DRIVER,
            self.MODEL.status == AssignmentStatus.ACTIVE,
            self.MODEL.deleted_at.is_(None),
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_active_assignment(
        self,
        db: AsyncSession,
        *,
        vehicle_id: UUID,
        user_id: UUID,
    ) -> bool:
        stmt = select(
            exists().where(
                self.MODEL.vehicle_id == vehicle_id,
                self.MODEL.user_id == user_id,
                self.MODEL.status == AssignmentStatus.ACTIVE,
                self.MODEL.deleted_at.is_(None),
            )
        )

        return bool(await db.scalar(stmt))
