from datetime import datetime, time, timedelta
from uuid import UUID

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.base import ConflictError
from app.core.pagination import PaginatedResponse, paginate
from app.core.utils import is_unique_violation, parse_unique_violation
from app.crud.tag import tag_crud
from app.crud.vehicle import VehicleCrud
from app.models.tag import Tag
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.base import QueryParams
from app.schemas.vehicle import VehicleCreate, VehicleFilter, VehicleOut, VehicleUpdate
from app.services.vehicle_model_service import vehicle_model_service


class VehicleService:
    crud = VehicleCrud()
    out_schema = VehicleOut

    async def create(
        self, db: AsyncSession, data: VehicleCreate, current_user: User
    ) -> Vehicle:
        await vehicle_model_service.get_or_404(db, data.vehicle_model_id)

        existing = await self.crud.get_by_vin(db, vin=data.vin)
        if existing is not None:
            raise ConflictError(f"Vehicle with VIN '{data.vin}' already exists.")

        tags = await tag_crud.get_or_create_many(db, [t.value for t in data.tags])
        payload = data.model_dump(exclude={"tags"})

        try:
            instance = await self.crud.create(
                db, {"created_by": current_user.id, **payload, "tags": tags}
            )
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            if is_unique_violation(e):
                raise ConflictError(parse_unique_violation(e)) from e
            raise
        return await self.crud.get_or_404(db, instance.id)

    async def get(self, db: AsyncSession, id: UUID) -> Vehicle | None:
        return await self.crud.get(db, id)

    async def get_or_404(self, db: AsyncSession, id: UUID) -> Vehicle:
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

        if params.filters.tag:
            query = query.join(Vehicle.tags).where(Tag.name == params.filters.tag.value)

        return await paginate(request, db, query, params.pagination, self.out_schema)

    async def update(
        self, db: AsyncSession, id: UUID, data: VehicleUpdate, current_user: User
    ) -> Vehicle:
        if data.vehicle_model_id is not None:
            await vehicle_model_service.get_or_404(db, data.vehicle_model_id)

        instance = await self.crud.get_or_404(db, id)
        update_data = data.model_dump(exclude_unset=True, exclude={"tags"})

        try:
            for key, value in update_data.items():
                if getattr(instance, key, None) != value:
                    setattr(instance, key, value)
            instance.updated_by = current_user.id

            instance.tags = await tag_crud.get_or_create_many(
                db, [t.value for t in data.tags]
            )

            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            if is_unique_violation(e):
                raise ConflictError(parse_unique_violation(e)) from e
            raise

        return await self.crud.get_or_404(db, id)

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
    ) -> Vehicle:
        instance = await self.crud.get_or_404(db, id)
        if instance.is_active != is_active:
            instance.is_active = is_active
            await db.commit()
        return await self.crud.get_or_404(db, id)

    @classmethod
    def _build_post_filters(cls, params: VehicleFilter) -> dict:
        filters = {"and": []}

        if search := params.search:
            if len(search) >= 2:
                filters["and"].append((cls.crud._build_q_filters(search)))

        if params.is_active is not None:
            filters["and"].append({"is_active": params.is_active})

        if params.status is not None:
            filters["and"].append({"status": params.status})

        if params.vehicle_model_id is not None:
            filters["and"].append({"vehicle_model_id": params.vehicle_model_id})

        if params.manufacturer_id is not None:
            filters["and"].append({"manufacturer_id": params.manufacturer_id})

        if params.created_by is not None:
            filters["and"].append({"created_by": params.created_by})

        if params.created_from is not None:
            filters["and"].append(
                {"created_at__gte": datetime.combine(params.created_from, time.min)}
            )

        if params.created_to is not None:
            filters["and"].append(
                {
                    "created_at__lt": datetime.combine(
                        params.created_to + timedelta(days=1), time.min
                    )
                }
            )

        if params.include_deleted:
            filters["and"].append({"include_deleted": True})

        return filters


vehicle_service = VehicleService()
