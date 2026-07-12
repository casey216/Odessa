from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager
from sqlalchemy.sql import Select

from app.crud.base import BaseCrud
from app.models.manufacturer import Manufacturer
from app.models.vehicle_model import VehicleModel


class VehicleModelCrud(BaseCrud[VehicleModel]):
    MODEL = VehicleModel
    ALLOWED_COLUMNS = {
        "name": VehicleModel.name,
        "year": VehicleModel.year,
        "fuel_type": VehicleModel.fuel_type,
        "transmission": VehicleModel.transmission,
        "seating_capacity": VehicleModel.seating_capacity,
        "engine_displacement_cc": VehicleModel.engine_displacement_cc,
        "horsepower": VehicleModel.horsepower,
        "is_active": VehicleModel.is_active,
        "manufacturer_id": VehicleModel.manufacturer_id,
        "manufacturer_name": Manufacturer.name,
        "created_at": VehicleModel.created_at,
        "updated_at": VehicleModel.updated_at,
        "created_by": VehicleModel.created_by,
    }
    SEARCH_COLUMNS = ("name__ilike", "manufacturer_name__ilike")

    def _base_query(self) -> Select:
        return (
            select(self.MODEL)
            .join(self.MODEL.manufacturer)
            .options(contains_eager(self.MODEL.manufacturer))
        )

    async def get_by_natural_key(
        self,
        db: AsyncSession,
        *,
        manufacturer_id: UUID,
        name: str,
        year: int,
        include_deleted: bool = False,
    ) -> VehicleModel | None:
        """Looks up a vehicle model by (manufacturer, name, year).

        Used by the service layer to enforce the partial-unique-index
        constraint (unique among non-deleted rows) at the application level
        before hitting the DB, so we can raise a clean 409 instead of a raw
        IntegrityError.
        """
        stmt = select(VehicleModel).where(
            VehicleModel.manufacturer_id == manufacturer_id,
            VehicleModel.name == name,
            VehicleModel.year == year,
        )
        if not include_deleted:
            stmt = stmt.where(VehicleModel.deleted_at.is_(None))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
