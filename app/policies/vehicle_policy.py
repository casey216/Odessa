from dataclasses import dataclass
from typing import Any

from sqlalchemy import Select, false, select

from app.core.permissions import PermissionCode
from app.models import User, Vehicle, VehicleAssignment
from app.models.user import UserRole
from app.schemas.vehicle_assignment import AssignmentStatus
from app.services.permission_service import permission_service

from .base import Policy


@dataclass
class VehicleReadContext:
    vehicle: Vehicle
    has_active_assignment: bool


class VehiclePolicy(Policy):
    @staticmethod
    def scope(query: Select[Any], current_user: User) -> Select[Any]:
        if not permission_service.user_has_permission(
            current_user, PermissionCode.vehicle_assignment_read
        ):
            return query.where(false())
        if (current_user.role == UserRole.driver) or (current_user.role == UserRole.fleet_manager):
            own_ids = select(VehicleAssignment.vehicle_id).where(
                VehicleAssignment.user_id == current_user.id,
                VehicleAssignment.status == AssignmentStatus.ACTIVE,
                VehicleAssignment.deleted_at.is_(None),
            )
            query = query.where(Vehicle.id.in_(own_ids))
        return query

    @staticmethod
    def can_read(current_user: User, resource: VehicleReadContext) -> bool:
        if not permission_service.user_has_permission(current_user, PermissionCode.vehicle_read):
            return False

        if (current_user.role == UserRole.driver) or (current_user.role == UserRole.fleet_manager):
            return resource.has_active_assignment

        return True
