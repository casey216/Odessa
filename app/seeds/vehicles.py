"""
Seed script for the vehicles table.

Depends on both the manufacturers and vehicle_models seeds having run
first — vehicles are linked to a vehicle model by (manufacturer, model
name, year) lookup, not a hardcoded id.

Usage:
    python -m app.seeds.manufacturers
    python -m app.seeds.vehicle_models
    python -m app.seeds.vehicles
"""

import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.database import AsyncSessionLocal
from app.models.manufacturer import Manufacturer
from app.models.tag import Tag, VehicleTagChoice, vehicle_tags
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.vehicle_model import VehicleModel

VEHICLES = [
    (
        "Toyota",
        "Corolla",
        2023,
        "LAG-101-AB",
        "White",
        VehicleStatus.AVAILABLE,
        12500,
        date(2023, 3, 14),
        Decimal("24500.00"),
        [VehicleTagChoice.OWNED, VehicleTagChoice.POOL_VEHICLE],
    ),
    (
        "Toyota",
        "Corolla",
        2024,
        "LAG-102-AB",
        "Silver",
        VehicleStatus.IN_USE,
        3200,
        date(2024, 1, 20),
        Decimal("26200.00"),
        [VehicleTagChoice.OWNED],
    ),
    (
        "Toyota",
        "Camry",
        2023,
        "LAG-103-AB",
        "Black",
        VehicleStatus.IN_USE,
        18400,
        date(2023, 5, 2),
        Decimal("32900.00"),
        [VehicleTagChoice.EXECUTIVE, VehicleTagChoice.GPS_TRACKED],
    ),
    (
        "Toyota",
        "RAV4",
        2022,
        "LAG-104-AB",
        "Blue",
        VehicleStatus.IN_MAINTENANCE,
        41200,
        date(2022, 6, 11),
        Decimal("29800.00"),
        [VehicleTagChoice.OWNED, VehicleTagChoice.UNDER_MAINTENANCE_CONTRACT],
    ),
    (
        "Toyota",
        "RAV4",
        2023,
        "LAG-105-AB",
        "White",
        VehicleStatus.AVAILABLE,
        5600,
        date(2023, 9, 8),
        Decimal("35400.00"),
        [VehicleTagChoice.EV_CHARGING_REQUIRED],
    ),
    (
        "Toyota",
        "Hilux",
        2021,
        "LAG-106-AB",
        "Gray",
        VehicleStatus.IN_USE,
        68900,
        date(2021, 4, 19),
        Decimal("27500.00"),
        [VehicleTagChoice.HIGH_MILEAGE, VehicleTagChoice.OWNED],
    ),
    (
        "Toyota",
        "Land Cruiser",
        2024,
        "LAG-107-AB",
        "Black",
        VehicleStatus.AVAILABLE,
        1100,
        date(2024, 2, 3),
        Decimal("68000.00"),
        [VehicleTagChoice.EXECUTIVE, VehicleTagChoice.OWNED],
    ),
    (
        "Toyota",
        "Prius",
        2023,
        "LAG-108-AB",
        "White",
        VehicleStatus.AVAILABLE,
        9800,
        date(2023, 7, 27),
        Decimal("28900.00"),
        [VehicleTagChoice.EV_CHARGING_REQUIRED, VehicleTagChoice.POOL_VEHICLE],
    ),
    (
        "Toyota",
        "Yaris",
        2020,
        None,
        "Red",
        VehicleStatus.RETIRED,
        112400,
        date(2020, 3, 1),
        Decimal("16500.00"),
        [VehicleTagChoice.HIGH_MILEAGE, VehicleTagChoice.DECOMMISSION_PENDING],
    ),
    (
        "Honda",
        "Civic",
        2023,
        "LAG-109-AB",
        "Silver",
        VehicleStatus.IN_USE,
        15200,
        date(2023, 4, 16),
        Decimal("24800.00"),
        [VehicleTagChoice.OWNED],
    ),
    (
        "Honda",
        "Civic",
        2024,
        "LAG-110-AB",
        "White",
        VehicleStatus.AVAILABLE,
        2100,
        date(2024, 3, 5),
        Decimal("26400.00"),
        [],
    ),
    (
        "Honda",
        "Accord",
        2022,
        "LAG-111-AB",
        "Black",
        VehicleStatus.IN_USE,
        33900,
        date(2022, 8, 22),
        Decimal("29500.00"),
        [VehicleTagChoice.EXECUTIVE],
    ),
    (
        "Honda",
        "CR-V",
        2023,
        "LAG-112-AB",
        "Blue",
        VehicleStatus.AVAILABLE,
        8700,
        date(2023, 10, 14),
        Decimal("31200.00"),
        [VehicleTagChoice.POOL_VEHICLE],
    ),
    (
        "Honda",
        "CR-V",
        2024,
        "LAG-113-AB",
        "Gray",
        VehicleStatus.IN_USE,
        4300,
        date(2024, 4, 9),
        Decimal("38900.00"),
        [VehicleTagChoice.EV_CHARGING_REQUIRED, VehicleTagChoice.GPS_TRACKED],
    ),
    (
        "Honda",
        "Pilot",
        2021,
        "LAG-114-AB",
        "White",
        VehicleStatus.IN_MAINTENANCE,
        54200,
        date(2021, 5, 30),
        Decimal("34700.00"),
        [VehicleTagChoice.UNDER_MAINTENANCE_CONTRACT],
    ),
    (
        "Honda",
        "Fit",
        2019,
        None,
        "Yellow",
        VehicleStatus.OUT_OF_SERVICE,
        98300,
        date(2019, 6, 4),
        Decimal("14200.00"),
        [VehicleTagChoice.HIGH_MILEAGE],
    ),
    (
        "Ford",
        "F-150",
        2023,
        "LAG-115-AB",
        "Black",
        VehicleStatus.IN_USE,
        21400,
        date(2023, 2, 27),
        Decimal("45200.00"),
        [VehicleTagChoice.OWNED, VehicleTagChoice.GPS_TRACKED],
    ),
    (
        "Ford",
        "F-150",
        2024,
        "LAG-116-AB",
        "White",
        VehicleStatus.AVAILABLE,
        900,
        date(2024, 5, 1),
        Decimal("52800.00"),
        [VehicleTagChoice.EV_CHARGING_REQUIRED],
    ),
    (
        "Ford",
        "Mustang",
        2022,
        "LAG-117-AB",
        "Red",
        VehicleStatus.AVAILABLE,
        12800,
        date(2022, 9, 17),
        Decimal("39900.00"),
        [VehicleTagChoice.EXECUTIVE],
    ),
    (
        "Ford",
        "Explorer",
        2023,
        "LAG-118-AB",
        "Blue",
        VehicleStatus.IN_USE,
        17600,
        date(2023, 6, 21),
        Decimal("36500.00"),
        [VehicleTagChoice.POOL_VEHICLE],
    ),
    (
        "Ford",
        "Ranger",
        2021,
        "LAG-119-AB",
        "Gray",
        VehicleStatus.IN_MAINTENANCE,
        61300,
        date(2021, 11, 8),
        Decimal("28100.00"),
        [VehicleTagChoice.UNDER_MAINTENANCE_CONTRACT, VehicleTagChoice.HIGH_MILEAGE],
    ),
    (
        "Ford",
        "Focus",
        2018,
        None,
        "Silver",
        VehicleStatus.RETIRED,
        134500,
        date(2018, 4, 12),
        Decimal("11800.00"),
        [VehicleTagChoice.HIGH_MILEAGE, VehicleTagChoice.DECOMMISSION_PENDING],
    ),
    (
        "Volkswagen",
        "Golf",
        2022,
        "LAG-120-AB",
        "White",
        VehicleStatus.AVAILABLE,
        22300,
        date(2022, 3, 9),
        Decimal("23400.00"),
        [VehicleTagChoice.OWNED],
    ),
    (
        "Volkswagen",
        "Golf",
        2023,
        "LAG-121-AB",
        "Black",
        VehicleStatus.IN_USE,
        9100,
        date(2023, 8, 3),
        Decimal("25100.00"),
        [],
    ),
    (
        "Volkswagen",
        "Tiguan",
        2023,
        "LAG-122-AB",
        "Blue",
        VehicleStatus.AVAILABLE,
        6400,
        date(2023, 12, 19),
        Decimal("32700.00"),
        [VehicleTagChoice.POOL_VEHICLE],
    ),
    (
        "Volkswagen",
        "ID.4",
        2024,
        "LAG-123-AB",
        "Gray",
        VehicleStatus.IN_USE,
        3800,
        date(2024, 6, 15),
        Decimal("41200.00"),
        [VehicleTagChoice.EV_CHARGING_REQUIRED, VehicleTagChoice.GPS_TRACKED],
    ),
    (
        "BMW",
        "3 Series",
        2023,
        "LAG-124-AB",
        "Black",
        VehicleStatus.IN_USE,
        14200,
        date(2023, 1, 25),
        Decimal("47800.00"),
        [VehicleTagChoice.EXECUTIVE, VehicleTagChoice.LEASED],
    ),
    (
        "BMW",
        "X5",
        2023,
        "LAG-125-AB",
        "White",
        VehicleStatus.AVAILABLE,
        7900,
        date(2023, 7, 4),
        Decimal("68500.00"),
        [VehicleTagChoice.EXECUTIVE, VehicleTagChoice.GPS_TRACKED],
    ),
    (
        "BMW",
        "i4",
        2024,
        "LAG-126-AB",
        "Blue",
        VehicleStatus.AVAILABLE,
        1600,
        date(2024, 3, 22),
        Decimal("59900.00"),
        [VehicleTagChoice.EV_CHARGING_REQUIRED, VehicleTagChoice.LEASED],
    ),
    (
        "Mercedes-Benz",
        "C-Class",
        2023,
        "LAG-127-AB",
        "Silver",
        VehicleStatus.IN_USE,
        11300,
        date(2023, 4, 30),
        Decimal("49500.00"),
        [VehicleTagChoice.EXECUTIVE, VehicleTagChoice.LEASED],
    ),
    (
        "Mercedes-Benz",
        "GLC",
        2023,
        "LAG-128-AB",
        "Black",
        VehicleStatus.AVAILABLE,
        4200,
        date(2023, 11, 11),
        Decimal("54200.00"),
        [VehicleTagChoice.EXECUTIVE],
    ),
    (
        "Mercedes-Benz",
        "EQS",
        2024,
        "LAG-129-AB",
        "White",
        VehicleStatus.AVAILABLE,
        800,
        date(2024, 5, 20),
        Decimal("104000.00"),
        [VehicleTagChoice.EV_CHARGING_REQUIRED, VehicleTagChoice.EXECUTIVE],
    ),
    (
        "Hyundai",
        "Elantra",
        2023,
        "LAG-130-AB",
        "Gray",
        VehicleStatus.IN_USE,
        16700,
        date(2023, 3, 28),
        Decimal("21900.00"),
        [VehicleTagChoice.RENTAL],
    ),
    (
        "Hyundai",
        "Tucson",
        2023,
        "LAG-131-AB",
        "Blue",
        VehicleStatus.AVAILABLE,
        8300,
        date(2023, 9, 15),
        Decimal("28600.00"),
        [VehicleTagChoice.POOL_VEHICLE],
    ),
    (
        "Hyundai",
        "Ioniq 5",
        2024,
        "LAG-132-AB",
        "White",
        VehicleStatus.IN_USE,
        2400,
        date(2024, 2, 18),
        Decimal("44100.00"),
        [VehicleTagChoice.EV_CHARGING_REQUIRED, VehicleTagChoice.GPS_TRACKED],
    ),
    (
        "Kia",
        "Sportage",
        2023,
        "LAG-133-AB",
        "Red",
        VehicleStatus.AVAILABLE,
        9600,
        date(2023, 6, 7),
        Decimal("27300.00"),
        [VehicleTagChoice.RENTAL],
    ),
    (
        "Kia",
        "EV6",
        2024,
        "LAG-134-AB",
        "Black",
        VehicleStatus.IN_MAINTENANCE,
        5100,
        date(2024, 1, 9),
        Decimal("46800.00"),
        [
            VehicleTagChoice.EV_CHARGING_REQUIRED,
            VehicleTagChoice.UNDER_MAINTENANCE_CONTRACT,
        ],
    ),
    (
        "Nissan",
        "Leaf",
        2023,
        "LAG-135-AB",
        "Silver",
        VehicleStatus.AVAILABLE,
        6800,
        date(2023, 5, 26),
        Decimal("29900.00"),
        [VehicleTagChoice.EV_CHARGING_REQUIRED],
    ),
    (
        "Mazda",
        "CX-5",
        2023,
        "LAG-136-AB",
        "White",
        VehicleStatus.IN_USE,
        13100,
        date(2023, 8, 19),
        Decimal("28800.00"),
        [VehicleTagChoice.OWNED],
    ),
    (
        "Subaru",
        "Outback",
        2023,
        "LAG-137-AB",
        "Gray",
        VehicleStatus.AVAILABLE,
        7400,
        date(2023, 10, 2),
        Decimal("30500.00"),
        [VehicleTagChoice.POOL_VEHICLE],
    ),
    (
        "Tesla",
        "Model 3",
        2024,
        "LAG-138-AB",
        "White",
        VehicleStatus.IN_USE,
        4900,
        date(2024, 4, 25),
        Decimal("41500.00"),
        [VehicleTagChoice.EV_CHARGING_REQUIRED, VehicleTagChoice.EXECUTIVE],
    ),
    (
        "Tesla",
        "Model Y",
        2024,
        "LAG-139-AB",
        "Black",
        VehicleStatus.AVAILABLE,
        2900,
        date(2024, 6, 3),
        Decimal("47200.00"),
        [VehicleTagChoice.EV_CHARGING_REQUIRED],
    ),
    (
        "Porsche",
        "911",
        2023,
        "LAG-140-AB",
        "Red",
        VehicleStatus.AVAILABLE,
        3100,
        date(2023, 7, 14),
        Decimal("118000.00"),
        [VehicleTagChoice.EXECUTIVE],
    ),
    (
        "Chevrolet",
        "Silverado",
        2023,
        "LAG-141-AB",
        "Black",
        VehicleStatus.IN_USE,
        19800,
        date(2023, 3, 30),
        Decimal("42300.00"),
        [VehicleTagChoice.OWNED],
    ),
    (
        "Chevrolet",
        "Bolt EV",
        2023,
        "LAG-142-AB",
        "Blue",
        VehicleStatus.AVAILABLE,
        5600,
        date(2023, 9, 27),
        Decimal("27900.00"),
        [VehicleTagChoice.EV_CHARGING_REQUIRED, VehicleTagChoice.POOL_VEHICLE],
    ),
    (
        "Audi",
        "Q5",
        2023,
        "LAG-143-AB",
        "Gray",
        VehicleStatus.AVAILABLE,
        8900,
        date(2023, 5, 8),
        Decimal("46700.00"),
        [VehicleTagChoice.EXECUTIVE, VehicleTagChoice.LEASED],
    ),
    (
        "Volvo",
        "XC60",
        2023,
        "LAG-144-AB",
        "White",
        VehicleStatus.IN_USE,
        11700,
        date(2023, 4, 3),
        Decimal("44500.00"),
        [VehicleTagChoice.EXECUTIVE],
    ),
    (
        "Volvo",
        "C40",
        2024,
        "LAG-145-AB",
        "Black",
        VehicleStatus.AVAILABLE,
        1900,
        date(2024, 3, 30),
        Decimal("48900.00"),
        [VehicleTagChoice.EV_CHARGING_REQUIRED, VehicleTagChoice.LEASED],
    ),
]


def _make_vin(index: int) -> str:
    """Synthetic 17-char placeholder VIN — not a real checksummed VIN."""
    return f"SEED{index:013d}"


async def seed_vehicles() -> None:
    async with AsyncSessionLocal() as session:
        # --- Resolve vehicle_model_id by (manufacturer, model, year) ---
        result = await session.execute(
            select(
                VehicleModel.id, VehicleModel.name, VehicleModel.year, Manufacturer.name
            ).join(Manufacturer, VehicleModel.manufacturer_id == Manufacturer.id)
        )
        model_ids = {
            (mfr_name, vm_name, vm_year): vm_id
            for vm_id, vm_name, vm_year, mfr_name in result.all()
        }

        rows = []
        skipped = []
        for index, (
            manufacturer_name,
            model_name,
            model_year,
            license_plate,
            color,
            status,
            odometer_km,
            purchase_date,
            purchase_price,
            tags,
        ) in enumerate(VEHICLES, start=1):
            vehicle_model_id = model_ids.get(
                (manufacturer_name, model_name, model_year)
            )
            if vehicle_model_id is None:
                skipped.append(f"{manufacturer_name} {model_name} ({model_year})")
                continue

            rows.append(
                {
                    "vin": _make_vin(index),
                    "license_plate": license_plate,
                    "color": color,
                    "status": status,
                    "odometer_km": odometer_km,
                    "purchase_date": purchase_date,
                    "purchase_price": purchase_price,
                    "vehicle_model_id": vehicle_model_id,
                    "is_active": True,
                    "tags": tags,
                }
            )

        if not rows:
            print(
                "No vehicles to seed — have manufacturers and vehicle_models "
                "been seeded yet? Run those seeds first."
            )
            return

        # --- Insert vehicles (tags handled separately below, association
        # table doesn't accept plain values() inserts) ---
        vehicle_payload = [
            {k: v for k, v in row.items() if k != "tags"} for row in rows
        ]
        stmt = pg_insert(Vehicle).values(vehicle_payload)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["vin"],
            index_where=text("deleted_at IS NULL"),
        )
        await session.execute(stmt)

        # --- Ensure every VehicleTagChoice has a backing Tag row ---
        tag_stmt = pg_insert(Tag).values([{"name": t.value} for t in VehicleTagChoice])
        tag_stmt = tag_stmt.on_conflict_do_nothing(index_elements=["name"])
        await session.execute(tag_stmt)

        tag_result = await session.execute(select(Tag.id, Tag.name))
        tag_ids = {name: tag_id for tag_id, name in tag_result.all()}

        # --- Re-fetch vehicle ids by VIN (whether just inserted or already
        # present from a prior run) so tag associations stay correct even
        # on a re-run ---
        vins = [row["vin"] for row in rows]
        vehicle_result = await session.execute(
            select(Vehicle.id, Vehicle.vin).where(Vehicle.vin.in_(vins))
        )
        vehicle_ids = {vin: vehicle_id for vehicle_id, vin in vehicle_result.all()}

        association_rows = []
        for row in rows:
            vehicle_id = vehicle_ids.get(row["vin"])
            if vehicle_id is None:
                continue
            for tag in row["tags"]:
                association_rows.append(
                    {"vehicle_id": vehicle_id, "tag_id": tag_ids[tag.value]}
                )

        if association_rows:
            assoc_stmt = pg_insert(vehicle_tags).values(association_rows)
            assoc_stmt = assoc_stmt.on_conflict_do_nothing(
                index_elements=["vehicle_id", "tag_id"]
            )
            await session.execute(assoc_stmt)

        await session.commit()

    print(f"Seeded {len(rows)} vehicles with tag associations (duplicates skipped).")
    if skipped:
        print(
            f"Skipped {len(skipped)} vehicle(s) whose model wasn't found: "
            f"{', '.join(skipped)}"
        )


if __name__ == "__main__":
    asyncio.run(seed_vehicles())
