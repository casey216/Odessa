from app.core.permissions import PermissionCode
from app.models.user import User
from app.models.vehicle_assignment import VehicleAssignment
from app.services.permission_service import permission_service

from .base import Policy


class VehicleAssignmentPolicy(Policy):
    @staticmethod
    def can_read(current_user: User, resource: VehicleAssignment) -> bool:
        if permission_service.user_has_permission(
            current_user, PermissionCode.vehicle_assignment_read
        ):
            return True
        return resource.user_id == current_user.id
