from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientPermissionError, PermissionNotFoundError
from app.core.permissions import PermissionCode
from app.crud.permission import PermissionCrud
from app.crud.user_permission import UserPermissionCrud
from app.models import User, UserPermission
from app.models.permission import PermissionEffect
from app.models.user import UserRole

DEFAULT_ROLE_PERMISSIONS: dict[UserRole, set[PermissionCode]] = {
    UserRole.admin: set(PermissionCode),
    UserRole.transport_manager: {
        PermissionCode.user_read,
        PermissionCode.manufacturer_create,
        PermissionCode.manufacturer_read,
        PermissionCode.manufacturer_update,
        PermissionCode.manufacturer_delete,
        PermissionCode.vehicle_model_create,
        PermissionCode.vehicle_model_read,
        PermissionCode.vehicle_model_update,
        PermissionCode.vehicle_model_delete,
        PermissionCode.vehicle_create,
        PermissionCode.vehicle_read,
        PermissionCode.vehicle_update,
        PermissionCode.vehicle_delete,
        PermissionCode.vehicle_assignment_create,
        PermissionCode.vehicle_assignment_read,
        PermissionCode.vehicle_assignment_update,
        PermissionCode.vehicle_assignment_delete,
        PermissionCode.activity_read,
    },
    UserRole.fleet_manager: {
        PermissionCode.user_read,
        PermissionCode.manufacturer_create,
        PermissionCode.manufacturer_read,
        PermissionCode.manufacturer_update,
        PermissionCode.manufacturer_delete,
        PermissionCode.vehicle_model_create,
        PermissionCode.vehicle_model_read,
        PermissionCode.vehicle_model_update,
        PermissionCode.vehicle_model_delete,
        PermissionCode.vehicle_create,
        PermissionCode.vehicle_read,
        PermissionCode.vehicle_update,
        PermissionCode.vehicle_delete,
        PermissionCode.vehicle_assignment_read,
    },
    UserRole.maintenance_manager: {
        PermissionCode.user_read,
        PermissionCode.vehicle_read,
        PermissionCode.vehicle_assignment_read,
    },
    UserRole.driver: {
        PermissionCode.vehicle_read,
        PermissionCode.vehicle_assignment_read,
    },
    UserRole.conductor: set(),
    UserRole.viewer: {
        PermissionCode.user_read,
        PermissionCode.manufacturer_read,
        PermissionCode.vehicle_model_read,
        PermissionCode.vehicle_read,
        PermissionCode.vehicle_assignment_read,
        PermissionCode.activity_read,
    },
}


class PermissionService:
    permission_crud = PermissionCrud()
    user_permission_crud = UserPermissionCrud()

    @staticmethod
    def _matches(code: PermissionCode, granted: set[str]) -> bool:
        if code.value in granted:
            return True
        return False

    @staticmethod
    def user_has_permission(user: User, permission_code: PermissionCode) -> bool:
        """
        Resolution order (deny always wins):
        1. Explicit per-user DENY overrides    -> False immediately
        2. Explicit per-user ALLOW overrides    -> True immediately
        3. Role default permissions             -> True/False
        """
        denies = {
            link.permission.code
            for link in user.permission_links
            if link.effect == PermissionEffect.deny
        }
        allows = {
            link.permission.code
            for link in user.permission_links
            if link.effect == PermissionEffect.allow
        }
        role_defaults = DEFAULT_ROLE_PERMISSIONS.get(user.role, set())
        default_permissions = {perm.value for perm in role_defaults}

        if PermissionService._matches(permission_code, denies):
            return False

        if PermissionService._matches(permission_code, allows):
            return True

        return PermissionService._matches(permission_code, default_permissions)

    @staticmethod
    def require_permission_or_raise(user: User, permission_code: PermissionCode) -> None:
        if not PermissionService.user_has_permission(user, permission_code):
            raise InsufficientPermissionError(permission_code)

    async def set_permission_override(
        self,
        db: AsyncSession,
        user_id: UUID,
        permission_code: PermissionCode,
        effect: PermissionEffect,
    ) -> None:
        permission = await self.permission_crud.get_by_code(db, code=permission_code.value)
        if permission is None:
            raise PermissionNotFoundError("Permision", permission_code.value)

        existing = await self.user_permission_crud.get_by_user_permission(
            db, user_id, permission.id
        )
        if existing:
            existing.effect = effect
        else:
            db.add(UserPermission(user_id=user_id, permission_id=permission.id, effect=effect))

        await db.commit()

    async def revoke_permission_override(
        self, db: AsyncSession, user_id: UUID, permission_code: PermissionCode
    ) -> None:
        """Removes the per-user override entirely, falling back to role default."""
        permission = await self.permission_crud.get_by_code(db, code=permission_code.value)
        if permission is None:
            raise PermissionNotFoundError("Permission", permission_code)

        link = await self.user_permission_crud.get_by_user_permission(db, user_id, permission.id)
        if link:
            await db.delete(link)
            await db.commit()


permission_service = PermissionService()
