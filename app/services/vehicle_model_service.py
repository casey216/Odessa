from uuid import UUID

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.base import ConflictError
from app.core.pagination import PaginatedResponse, paginate
from app.core.utils import is_unique_violation, parse_unique_violation
from app.crud.vehicle_model import VehicleModelCrud
from app.models import User, Vehicle, VehicleModel
from app.schemas.base import QueryParams
from app.schemas.vehicle_model import (
    VehicleModelCreate,
    VehicleModelOut,
    VehicleModelUpdate,
)
from app.services.base import BaseService
from app.services.manufacturer_service import manufacturer_service


class VehicleModelService(BaseService[VehicleModelCrud]):
    crud = VehicleModelCrud()
    out_schema = VehicleModelOut
    FILTER_FIELDS = {
        "is_active",
        "manufacturer_id",
        "fuel_type",
        "transmission",
        "created_by",
    }
    DATE_FIELDS = [
        ("created_from", "created_to", "created_at"),
    ]

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
                raise ConflictError(parse_unique_violation(e)) from e
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
                raise ConflictError(parse_unique_violation(e)) from e
            raise

    async def delete(self, db: AsyncSession, id: UUID, soft: bool = True) -> None:
        if await self.crud.has_children(
            db,
            fk_column=Vehicle.vehicle_model_id,
            parent_id=id,
        ):
            raise ConflictError(
                "Cannot delete vehicle model because it has vehicles. Set inactive instead."
            )
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


vehicle_model_service = VehicleModelService()
