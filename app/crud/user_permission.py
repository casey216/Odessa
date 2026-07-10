from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import BaseCrud
from app.models.permission import UserPermission


class UserPermissionCrud(BaseCrud[UserPermission]):
    MODEL = UserPermission

    async def get_by_user_permission(
        self, db: AsyncSession, user_id: UUID, permission_id: UUID
    ) -> UserPermission | None:
        query = self._base_query()
        query = query.where(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission_id,
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
