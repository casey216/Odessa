from app.core.permissions import PermissionCode
from app.models import User
from app.models.user import UserRole
from app.services.permission_service import permission_service

from .base import Policy


class UserPolicy(Policy):
    @staticmethod
    def can_read(current_user: User, resource: User) -> bool:
        if permission_service.user_has_permission(current_user, PermissionCode.user_read):
            if current_user.role == UserRole.admin:
                return True
            if not current_user.is_super_user:
                return resource.id == current_user.id
            return True
        return False

    @staticmethod
    def can_update(current_user: User, resource: User) -> bool:
        if permission_service.user_has_permission(current_user, PermissionCode.user_update):
            if current_user.role == UserRole.admin:
                return True
            if not current_user.is_super_user:
                return resource.id == current_user.id
            return True
        return False
