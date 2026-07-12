from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload
from sqlalchemy.sql import Select

from app.crud.base import BaseCrud
from app.models.manufacturer import Manufacturer
from app.models.vehicle import Vehicle
from app.models.vehicle_model import VehicleModel


class VehicleCrud(BaseCrud[Vehicle]):
    MODEL = Vehicle
    ALLOWED_COLUMNS = {
        "vin": Vehicle.vin,
        "license_plate": Vehicle.license_plate,
        "status": Vehicle.status,
        "odometer_km": Vehicle.odometer_km,
        "purchase_date": Vehicle.purchase_date,
        "is_active": Vehicle.is_active,
        "vehicle_model_id": Vehicle.vehicle_model_id,
        "vehicle_model_name": VehicleModel.name,
        "manufacturer_id": VehicleModel.manufacturer_id,
        "manufacturer_name": Manufacturer.name,
        "created_at": Vehicle.created_at,
        "updated_at": Vehicle.updated_at,
        "created_by": Vehicle.created_by,
    }
    SEARCH_COLUMNS = (
        "vin__ilike",
        "license_plate__ilike",
        "vehicle_model_name__ilike",
        "manufacturer_name__ilike",
    )

    def _base_query(self) -> Select:
        return (
            select(self.MODEL)
            .join(self.MODEL.vehicle_model)
            .join(VehicleModel.manufacturer)
            .options(
                contains_eager(self.MODEL.vehicle_model).contains_eager(
                    VehicleModel.manufacturer
                ),
                selectinload(self.MODEL.tags),
            )
        )

    async def get_by_vin(
        self, db: AsyncSession, *, vin: str, include_deleted: bool = False
    ) -> Vehicle | None:
        """Looks up a vehicle by VIN.

        Used by the service layer to enforce the partial-unique-index
        constraint (unique among non-deleted rows) at the application level
        before hitting the DB, so we can raise a clean 409 instead of a raw
        IntegrityError.
        """
        stmt = self._base_query().where(Vehicle.vin == vin)
        if not include_deleted:
            stmt = stmt.where(Vehicle.deleted_at.is_(None))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
