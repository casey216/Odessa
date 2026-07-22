from datetime import datetime, time, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base
from app.crud.base import BaseCrud


class BaseService[CrudT: BaseCrud, ModelT: Base]:
    FILTER_FIELDS: set
    DATE_FIELDS: list[tuple[str, str, str]]
    crud: CrudT

    async def get(self, db: AsyncSession, id: UUID) -> ModelT | None:
        return await self.crud.get(db, id)

    async def get_or_404(self, db: AsyncSession, id: UUID) -> ModelT:
        return await self.crud.get_or_404(db, id)

    async def exists(self, db: AsyncSession, id: UUID) -> bool:
        return await self.crud.exists(db, id)

    async def count(self, db: AsyncSession, id: UUID) -> int:
        return await self.crud.count(db)

    @classmethod
    def _build_post_filters(cls, params):
        filters = {"and": []}

        if search := getattr(params, "search", None):
            if len(search) >= 2:
                filters["and"].append(cls.crud._build_q_filters(search))

        for field in cls.FILTER_FIELDS:
            value = getattr(params, field, None)
            if value is not None:
                filters["and"].append({field: value})

        for from_field, to_field, column in cls.DATE_FIELDS:
            if value := getattr(params, from_field, None):
                filters["and"].append(
                    {
                        f"{column}__gte": datetime.combine(
                            value,
                            time.min,
                        )
                    }
                )

            if value := getattr(params, to_field, None):
                filters["and"].append(
                    {
                        f"{column}__lt": datetime.combine(
                            value + timedelta(days=1),
                            time.min,
                        )
                    }
                )

        if getattr(params, "include_deleted", False):
            filters["and"].append({"include_deleted": True})

        return filters
