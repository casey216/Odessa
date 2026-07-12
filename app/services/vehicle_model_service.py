from datetime import datetime, time, timedelta
from uuid import UUID

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.base import ConflictError
from app.core.pagination import PaginatedResponse, paginate
from app.core.utils import is_unique_violation
from app.crud.vehicle_model import VehicleModelCrud
from app.models.user import User
from app.models.vehicle_model import VehicleModel
from app.schemas.base import QueryParams
from app.schemas.vehicle_model import (
    VehicleModelCreate,
    VehicleModelFilter,
    VehicleModelOut,
    VehicleModelUpdate,
)
from app.services.manufacturer_service import manufacturer_service


class VehicleModelService:
    crud = VehicleModelCrud()
    out_schema = VehicleModelOut

    async def create(
        self, db: AsyncSession, data: VehicleModelCreate, current_user: User
    ) -> VehicleModel:
        await manufacturer_service.get_or_404(db, data.manufacturer_id)

        existing = await self.crud.get_by_natural_key(
            db,
            manufacturer_id=data.manufacturer_id,
            name=data.name,
            year=data.year,
        )
        if existing is not None:
            raise ConflictError(
                f"Vehicle model '{data.name}' ({data.year}) already exists "
                "for this manufacturer."
            )
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
                    f"Vehicle model '{data.name}' ({data.year}) already exists "
                    "for this manufacturer."
                ) from e
            raise

    async def get(self, db: AsyncSession, id: UUID) -> VehicleModel | None:
        return await self.crud.get(db, id)

    async def get_or_404(self, db: AsyncSession, id: UUID) -> VehicleModel:
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
        self,
        db: AsyncSession,
        id: UUID,
        data: VehicleModelUpdate,
        current_user: User,
    ) -> VehicleModel:
        if data.manufacturer_id is not None:
            await manufacturer_service.get_or_404(db, data.manufacturer_id)

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
            await db.rollback()
            if is_unique_violation(e):
                raise ConflictError(
                    f"Vehicle model '{data.name}' already exists "
                    "for this manufacturer."
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

    async def set_active_status(self, db, id: UUID, is_active: bool) -> VehicleModel:
        instance = await self.crud.get_or_404(db, id)
        if instance.is_active != is_active:
            instance.is_active = is_active
            await db.commit()
        return instance

    @classmethod
    def _build_post_filters(cls, params: VehicleModelFilter) -> dict:
        filters = {}

        if search := params.search:
            if len(search) >= 2:
                filters.update(cls.crud._build_q_filters(search))

        if params.is_active is not None:
            filters["is_active"] = params.is_active

        if params.manufacturer_id is not None:
            filters["manufacturer_id"] = params.manufacturer_id

        if params.fuel_type is not None:
            filters["fuel_type"] = params.fuel_type

        if params.transmission is not None:
            filters["transmission"] = params.transmission

        if params.created_by is not None:
            filters["created_by"] = params.created_by

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

        if params.include_deleted:
            filters["include_deleted"] = True

        return filters


vehicle_model_service = VehicleModelService()
