from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import BaseCrud
from app.models import Permission


class PermissionCrud(BaseCrud[Permission]):
    MODEL = Permission
    ALLOWED_COLUMNS = {"code": Permission.code}
    SEARCH_COLUMNS = ("code__ilike",)

    async def get_by_code(
        self,
        db: AsyncSession,
        *,
        code: str,
    ) -> Permission | None:
        stmt = select(Permission).where(Permission.code == code)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
