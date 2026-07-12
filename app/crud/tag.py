from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag


class TagCrud:
    async def get_or_create_many(self, db: AsyncSession, names: list[str]) -> list[Tag]:
        if not names:
            return []

        unique_names = list(dict.fromkeys(n.strip() for n in names if n.strip()))
        if not unique_names:
            return []

        stmt = pg_insert(Tag).values([{"name": name} for name in unique_names])
        stmt = stmt.on_conflict_do_nothing(index_elements=["name"])
        await db.execute(stmt)

        result = await db.execute(select(Tag).where(Tag.name.in_(unique_names)))
        return list(result.scalars().all())


tag_crud = TagCrud()
