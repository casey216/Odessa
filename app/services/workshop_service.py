from uuid import UUID

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.pagination import PaginatedResponse, paginate
from app.core.utils import is_unique_violation, parse_unique_violation
from app.crud.workshop import WorkshopCrud
from app.models import User
from app.models.workshop import Workshop
from app.schemas.base import QueryParams
from app.schemas.workshop import WorkshopCreate, WorkshopOut, WorkshopUpdate

from .base import BaseService


class WorkshopService(BaseService[WorkshopCrud, Workshop]):
    crud = WorkshopCrud()
    FILTER_FIELDS = {
        "is_active",
        "created_by",
    }
    DATE_FIELDS = [("created_from", "created_to", "created_at")]
    out_schema = WorkshopOut

    async def create(self, db: AsyncSession, data: WorkshopCreate, current_user: User) -> Workshop:
        existing = await self.crud.get_by_name(db, name=data.name)
        if existing:
            raise ConflictError(f"Workshop {data.name} already exists!")

        try:
            instance = await self.crud.create(
                db, {"created_by": current_user.id, **data.model_dump()}
            )
            await db.commit()
            await db.refresh(instance)
            return instance
        except IntegrityError as e:
            await db.rollback()
            if is_unique_violation(e):
                raise ConflictError(parse_unique_violation(e)) from e
            raise

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
        self, db: AsyncSession, id: UUID, data: WorkshopUpdate, current_user: User
    ) -> Workshop:
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

    async def set_active_status(self, db, id: UUID, is_active: bool) -> Workshop:
        instance = await self.crud.get_or_404(db, id)
        if instance.is_active != is_active:
            instance.is_active = is_active
            await db.commit()
            await db.refresh(instance)
        return instance


workshop_service = WorkshopService()
