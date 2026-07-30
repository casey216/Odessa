from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workshop import Workshop

from .base import BaseCrud


class WorkshopCrud(BaseCrud[Workshop]):
    MODEL = Workshop
    ALLOWED_COLUMNS = {
        "name": Workshop.name,
        "created_at": Workshop.created_at,
        "updated_at": Workshop.updated_at,
        "is_active": Workshop.is_active,
        "created_by": Workshop.created_by,
    }
    SEARCH_COLUMNS = ("name__ilike",)

    async def get_by_name(
        self,
        db: AsyncSession,
        *,
        name: str,
        include_deleted: bool = False,
    ) -> Workshop | None:
        """Looks up a workshop by exact name."""
        stmt = select(Workshop).where(Workshop.name == name)
        if not include_deleted:
            stmt = stmt.where(Workshop.deleted_at.is_(None))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
