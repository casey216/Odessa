from app.core.permissions import PermissionCode
from app.models.user import User
from app.models.vehicle_assignment import VehicleAssignment
from app.services.permission_service import permission_service

from .base import Policy


class VehicleAssignmentPolicy(Policy):
    @staticmethod
    def can_create(current_user: User) -> bool:
        return permission_service.user_has_permission(
            current_user, PermissionCode.vehicle_assignment_create
        )

    @staticmethod
    def can_read(assignment: VehicleAssignment, current_user: User) -> bool:
        if permission_service.user_has_permission(
            current_user, PermissionCode.vehicle_assignment_read
        ):
            return True
        return assignment.user_id == current_user.id

    @staticmethod
    def can_update(current_user: User) -> bool:
        return permission_service.user_has_permission(
            current_user, PermissionCode.vehicle_assignment_update
        )

    @staticmethod
    def can_delete(current_user: User) -> bool:
        return permission_service.user_has_permission(
            current_user, PermissionCode.vehicle_assignment_delete
        )
