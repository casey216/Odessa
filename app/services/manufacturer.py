from datetime import datetime, time, timedelta
from uuid import UUID

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError
from app.core.pagination import PaginatedResponse, paginate
from app.core.utils import is_unique_violation
from app.crud.manufacturer import ManufacturerCrud
from app.models.manufacturer import Manufacturer
from app.models.user import User
from app.schemas.base import QueryParams
from app.schemas.manufacturer import (
    ManufacturerCreate,
    ManufacturerFilter,
    ManufacturerOut,
    ManufacturerUpdate,
)


class ManufacturerService:
    crud = ManufacturerCrud()
    out_schema = ManufacturerOut

    async def create(
        self, db: AsyncSession, data: ManufacturerCreate, current_user: User
    ) -> Manufacturer:
        existing = await self.crud.get_by_name(db, name=data.name)
        if existing is not None:
            raise ConflictError(f"Manufacturer '{data.name}' already exists.")
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
                raise ConflictError(
                    f"Manufacturer '{data.name}' already exists."
                ) from e
            raise

    async def get(self, db: AsyncSession, id: UUID) -> Manufacturer | None:
        return await self.crud.get(db, id)

    async def get_or_404(self, db: AsyncSession, id: UUID) -> Manufacturer:
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
        self, db: AsyncSession, id: UUID, data: ManufacturerUpdate, current_user: User
    ) -> Manufacturer:
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
                raise ConflictError(
                    f"Manufacturer '{data.name}' already exists."
                ) from e
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

    async def set_active_status(self, db, id: UUID, is_active: bool) -> Manufacturer:
        instance = await self.crud.get_or_404(db, id)
        if instance.is_active != is_active:
            instance.is_active = is_active
            await db.commit()
            await db.refresh(instance)
        return instance

    @classmethod
    def _build_post_filters(cls, params: ManufacturerFilter) -> dict:
        filters = {}

        if search := params.search:
            if len(search) >= 2:
                filters.update(cls.crud._build_q_filters(search))

        if params.is_active is not None:
            filters["is_active"] = params.is_active

        if params.created_by is not None:
            filters["created_by"] = params.created_by

        if params.min_date is not None:
            filters["created_at__gte"] = datetime.combine(
                params.min_date,
                time.min,
            )

        if params.max_date is not None:
            filters["created_at__lt"] = datetime.combine(
                params.max_date + timedelta(days=1),
                time.min,
            )

        if params.include_deleted:
            filters["include_deleted"] = True

        return filters


manufacturer_service = ManufacturerService()
