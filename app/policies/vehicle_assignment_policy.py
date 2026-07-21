from app.core.permissions import PermissionCode
from app.models.user import User, UserRole
from app.models.vehicle_assignment import VehicleAssignment
from app.services.permission_service import permission_service

from .base import Policy


class VehicleAssignmentPolicy(Policy):
    @staticmethod
    def can_read(current_user: User, resource: VehicleAssignment) -> bool:
        if not permission_service.user_has_permission(
            current_user, PermissionCode.vehicle_assignment_read
        ):
            return False

        if (current_user.role == UserRole.driver) or (current_user.role == UserRole.fleet_manager):
            return current_user.id == resource.user_id

        return True
