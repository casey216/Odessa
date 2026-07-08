from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import BaseCrud
from app.models.manufacturer import Manufacturer


class ManufacturerCrud(BaseCrud[Manufacturer]):
    MODEL = Manufacturer
    ALLOWED_COLUMNS = {
        "name": Manufacturer.name,
        "created_at": Manufacturer.created_at,
        "updated_at": Manufacturer.updated_at,
        "is_active": Manufacturer.is_active,
        "created_by": Manufacturer.created_by,
    }
    SEARCH_COLUMNS = ("name__ilike",)

    async def get_by_name(
        self,
        db: AsyncSession,
        *,
        name: str,
        include_deleted: bool = False,
    ) -> Manufacturer | None:
        """Looks up a manufacturer by exact name.

        Used by the service layer to enforce the partial-unique-index
        constraint (unique among non-deleted rows) at the application level
        before hitting the DB, so we can raise a clean 409 instead of a raw
        IntegrityError.
        """
        stmt = select(Manufacturer).where(Manufacturer.name == name)
        if not include_deleted:
            stmt = stmt.where(Manufacturer.deleted_at.is_(None))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
