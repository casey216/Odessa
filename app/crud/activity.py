from typing import Sequence
from uuid import UUID

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models.activity import ActivityLog
from app.schemas.activity import ActivityLogFilter


class ActivityLogCrud:
    model = ActivityLog
    equality_filters: list[str] = ["user_id", "action", "entity_type", "entity_id"]

    async def create(self, db: AsyncSession, data: dict) -> model:
        instance = self.model(**data)
        db.add(instance)
        await db.flush()
        return instance

    async def get_by_id(self, db: AsyncSession, id: UUID) -> model | None:
        return await db.get(self.model, id)

    def apply_filters(self, query: Select, filters: ActivityLogFilter) -> Select:
        for field in self.equality_filters:
            value = getattr(filters, field, None)

            if value is not None:
                query = query.filter(getattr(self.model, field) == value)
        if filters.min_date:
            query.filter(ActivityLog.created_at >= filters.min_date)

        if filters.max_date:
            query.filter(ActivityLog.created_at <= filters.max_date)

        return query

    def fetch_all(
        self,
        filters=None,
        sort_by: str = "created_at",
        order_by: str = "desc",
    ) -> Select:
        query = select(self.model)

        if filters:
            query = self.apply_filters(query, filters)

        order_fn = desc if order_by == "desc" else asc
        return query.order_by(order_fn(getattr(self.model, sort_by)))

    async def count(self, db: AsyncSession) -> int:
        return await db.scalar(select(func.count()).select_from(self.model)) or 0

    async def get_by_entity(self, db: AsyncSession, entity_id: UUID) -> Sequence[model]:
        result = await db.execute(
            select(self.model)
            .filter(self.model.entity_id == entity_id)
            .order_by(self.model.created_at.desc())
        )
        return result.scalars().all()
