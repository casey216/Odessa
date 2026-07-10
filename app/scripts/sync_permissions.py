from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import PermissionCode
from app.models import Permission


async def sync_permissions(db: AsyncSession) -> None:
    existing_codes = {
        p.code for p in (await db.execute(select(Permission))).scalars().all()
    }

    for member in PermissionCode:
        if member.value not in existing_codes:
            db.add(Permission(code=member.value, description=None))

    await db.commit()
