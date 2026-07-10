from app.core.permissions import PermissionCode
from app.models import User, UserRole
from app.services.permission_service import permission_service

from .base import Policy


class UserPolicy(Policy):
    @staticmethod
    def can_read(user: User, current_user: User) -> bool:
        if permission_service.user_has_permission(
            current_user, PermissionCode.user_read
        ):
            if current_user.role == UserRole.admin:
                return True
            if not current_user.is_super_user:
                return user.id == current_user.id
            return True
        return False

    @staticmethod
    def can_update(user: User, current_user: User) -> bool:
        if permission_service.user_has_permission(
            current_user, PermissionCode.user_update
        ):
            if current_user.role == UserRole.admin:
                return True
            if not current_user.is_super_user:
                return user.id == current_user.id
            return True
        return False
