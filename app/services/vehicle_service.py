from uuid import UUID

from fastapi import Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions.base import ConflictError
from app.core.pagination import PaginatedResponse, paginate
from app.core.utils import is_unique_violation, parse_unique_violation
from app.crud.tag import tag_crud
from app.crud.vehicle import VehicleCrud
from app.models import Tag, User, Vehicle, VehicleAssignment
from app.policies.vehicle_policy import VehiclePolicy
from app.schemas.base import QueryParams
from app.schemas.vehicle import VehicleCreate, VehicleOut, VehicleUpdate
from app.services.base import BaseService
from app.services.vehicle_model_service import vehicle_model_service


class VehicleService(BaseService[VehicleCrud, Vehicle]):
    crud = VehicleCrud()
    out_schema = VehicleOut
    FILTER_FIELDS = {
        "is_active",
        "status",
        "vehicle_model_id",
        "manufacturer_id",
        "created_by",
    }
    DATE_FIELDS = [
        ("created_from", "created_to", "created_at"),
    ]

    async def create(self, db: AsyncSession, data: VehicleCreate, current_user: User) -> Vehicle:
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

    async def list(
        self, request: Request, db: AsyncSession, params: QueryParams, current_user: User
    ) -> PaginatedResponse[out_schema]:
        filters = self._build_post_filters(params.filters)
        query = self.crud.build_query(
            filters=filters,
            sort_by=params.filters.sort_by,
            order_by=params.filters.sort_order,
        )

        if params.filters.tag:
            query = query.join(Vehicle.tags).where(Tag.name == params.filters.tag.value)
        query = VehiclePolicy.scope(query, current_user)

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

            instance.tags = await tag_crud.get_or_create_many(db, [t.value for t in data.tags])

            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            if is_unique_violation(e):
                raise ConflictError(parse_unique_violation(e)) from e
            raise

        return await self.crud.get_or_404(db, id)

    async def delete(self, db: AsyncSession, id: UUID, soft: bool = True) -> None:
        if await self.crud.has_children(
            db,
            fk_column=VehicleAssignment.vehicle_id,
            parent_id=id,
        ):
            raise ConflictError(
                "Cannot delete vehicle because it has vehicle assignments. Set inactive instead."
            )
        if soft:
            await self.crud.soft_delete(db, id)
        else:
            await self.crud.delete(db, id)
        await db.commit()

    async def set_active_status(self, db: AsyncSession, id: UUID, is_active: bool) -> Vehicle:
        instance = await self.crud.get_or_404(db, id)
        if instance.is_active != is_active:
            instance.is_active = is_active
            await db.commit()
        return await self.crud.get_or_404(db, id)


vehicle_service = VehicleService()
