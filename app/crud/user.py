from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import BaseCrud
from app.models.user import User


class UserCrud(BaseCrud[User]):
    MODEL = User
    ALLOWED_COLUMNS = {
        "full_name": User.full_name,
        "email": User.email,
        "phone": User.phone,
        "department": User.department,
        "role": User.role,
        "is_active": User.is_active,
        "is_super_user": User.is_super_user,
        "created_at": User.created_at,
        "last_login": User.last_login,
        "updated_at": User.updated_at,
    }
    SEARCH_COLUMNS = (
        "full_name__ilike",
        "email__ilike",
        "phone__ilike",
        "department__ilike",
    )

    async def get_by_email(
        self,
        db: AsyncSession,
        *,
        email: str,
        include_deleted: bool = False,
    ) -> User | None:
        stmt = select(User).where(User.email == email)
        if not include_deleted:
            stmt = stmt.where(User.deleted_at.is_(None))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
