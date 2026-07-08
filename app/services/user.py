from datetime import datetime, time, timedelta
from uuid import UUID

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_password_hash
from app.core.exceptions import ConflictError
from app.core.pagination import PaginatedResponse, paginate
from app.crud.user import UserCrud
from app.models.user import User
from app.schemas.base import QueryParams
from app.schemas.user import UserCreate, UserFilter, UserOut, UserUpdate
from app.utils import is_unique_violation, parse_unique_violation


class UserService:
    crud = UserCrud()
    out_schema = UserOut

    async def create(
        self, db: AsyncSession, data: UserCreate, current_user: User
    ) -> User:
        existing = await self.crud.get_by_email(db, email=data.email)
        if existing is not None:
            raise ConflictError(f"Email '{data.email}' already exists.")
        hashed_password = get_password_hash(data.password)
        try:
            instance = await self.crud.create(
                db,
                {
                    "created_by": current_user.id,
                    "hashed_password": hashed_password,
                    **data.model_dump(exclude={"password", "confirm_password"}),
                },
            )
            await db.commit()
            await db.refresh(instance)
            return instance
        except IntegrityError as e:
            await db.rollback()
            if is_unique_violation(e):
                raise ConflictError(f"Email '{data.email}' already exists.") from e
            raise

    async def get(self, db: AsyncSession, id: UUID) -> User | None:
        return await self.crud.get(db, id)

    async def get_or_404(self, db: AsyncSession, id: UUID) -> User:
        return await self.crud.get_or_404(db, id)

    async def list(
        self, request: Request, db: AsyncSession, params: QueryParams
    ) -> PaginatedResponse[out_schema]:
        filters = self._build_post_filters(params.filters)
        query = self.crud.build_query(
            filters=filters,
            sort_by=params.filters.sort_by,
            order_by=params.filters.sort_order,
        )
        return await paginate(request, db, query, params.pagination, self.out_schema)

    async def update(
        self, db: AsyncSession, id: UUID, data: UserUpdate, current_user: User
    ) -> User:
        try:
            instance = await self.crud.update(
                db,
                id,
                {"updated_by": current_user.id, **data.model_dump(exclude_unset=True)},
            )
            await db.commit()
            await db.refresh(instance)
            return instance
        except IntegrityError as e:
            if is_unique_violation(e):
                raise ConflictError(parse_unique_violation(e)) from e
            raise

    async def delete(self, db: AsyncSession, id: UUID, soft: bool = True) -> None:
        if soft:
            await self.crud.soft_delete(db, id)
        else:
            await self.crud.delete(db, id)
        await db.commit()

    async def exists(self, db: AsyncSession, id: UUID) -> bool:
        return await self.crud.exists(db, id)

    async def count(self, db: AsyncSession, id: UUID) -> int:
        return await self.crud.count(db)

    async def set_active_status(
        self, db: AsyncSession, id: UUID, is_active: bool
    ) -> User:
        instance = await self.crud.get_or_404(db, id)
        if instance.is_active != is_active:
            instance.is_active = is_active
            await db.commit()
            await db.refresh(instance)
        return instance

    @classmethod
    def _build_post_filters(cls, params: UserFilter) -> dict:
        filters = {}

        if search := params.search:
            if len(search) >= 2:
                filters.update(cls.crud._build_q_filters(search))

        if params.role is not None:
            filters["role"] = params.role

        if params.is_active is not None:
            filters["is_active"] = params.is_active

        if params.is_super_user is not None:
            filters["is_super_user"] = params.is_super_user

        if params.department is not None:
            filters["department"] = params.department

        if params.created_from is not None:
            filters["created_at__gte"] = datetime.combine(
                params.created_from,
                time.min,
            )

        if params.created_to is not None:
            filters["created_at__lt"] = datetime.combine(
                params.created_to + timedelta(days=1),
                time.min,
            )

        if params.last_login_from is not None:
            filters["last_login__gte"] = datetime.combine(
                params.last_login_from,
                time.min,
            )

        if params.last_login_to is not None:
            filters["last_login__lt"] = datetime.combine(
                params.last_login_to + timedelta(days=1),
                time.min,
            )

        if params.never_logged_in is not None:
            filters["last_login__is_null"] = True

        return filters


user_service = UserService()
