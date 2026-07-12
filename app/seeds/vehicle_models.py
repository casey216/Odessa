"""
Seed script for the vehicle_models table.

Depends on the manufacturers seed having run first (models are linked to
manufacturers by name lookup, not hardcoded ids).

Usage:
    python -m app.seeds.manufacturers
    python -m app.seeds.vehicle_models
"""

import asyncio

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.database import AsyncSessionLocal
from app.models.manufacturer import Manufacturer
from app.models.vehicle_model import FuelType, TransmissionType, VehicleModel

# (manufacturer_name, name, year, fuel_type, transmission,
#  seating_capacity, engine_displacement_cc, horsepower)
VEHICLE_MODELS = [
    # Toyota
    ("Toyota", "Corolla", 2023, FuelType.PETROL, TransmissionType.CVT, 5, 1800, 139),
    ("Toyota", "Corolla", 2024, FuelType.CNG, TransmissionType.MANUAL, 5, 1500, 108),
    (
        "Toyota",
        "Camry",
        2023,
        FuelType.PETROL,
        TransmissionType.AUTOMATIC,
        5,
        2500,
        203,
    ),
    ("Toyota", "RAV4", 2022, FuelType.PETROL, TransmissionType.AUTOMATIC, 5, 2500, 203),
    (
        "Toyota",
        "RAV4",
        2023,
        FuelType.ELECTRIC,
        TransmissionType.AUTOMATIC,
        5,
        None,
        302,
    ),
    ("Toyota", "Hilux", 2021, FuelType.DIESEL, TransmissionType.MANUAL, 5, 2800, 201),
    (
        "Toyota",
        "Land Cruiser",
        2024,
        FuelType.DIESEL,
        TransmissionType.AUTOMATIC,
        7,
        3300,
        305,
    ),
    ("Toyota", "Prius", 2023, FuelType.ELECTRIC, TransmissionType.CVT, 5, None, 194),
    ("Toyota", "Yaris", 2020, FuelType.PETROL, TransmissionType.MANUAL, 5, 1500, 106),
    # Honda
    ("Honda", "Civic", 2023, FuelType.PETROL, TransmissionType.CVT, 5, 2000, 158),
    (
        "Honda",
        "Civic",
        2024,
        FuelType.PETROL,
        TransmissionType.DUAL_CLUTCH,
        5,
        1500,
        180,
    ),
    ("Honda", "Accord", 2022, FuelType.PETROL, TransmissionType.CVT, 5, 1500, 192),
    ("Honda", "CR-V", 2023, FuelType.PETROL, TransmissionType.CVT, 5, 1500, 190),
    (
        "Honda",
        "CR-V",
        2024,
        FuelType.ELECTRIC,
        TransmissionType.AUTOMATIC,
        5,
        None,
        212,
    ),
    ("Honda", "Pilot", 2021, FuelType.PETROL, TransmissionType.AUTOMATIC, 8, 3500, 280),
    ("Honda", "Fit", 2019, FuelType.PETROL, TransmissionType.CVT, 5, 1500, 128),
    # Ford
    ("Ford", "F-150", 2023, FuelType.PETROL, TransmissionType.AUTOMATIC, 5, 3500, 400),
    (
        "Ford",
        "F-150",
        2024,
        FuelType.ELECTRIC,
        TransmissionType.AUTOMATIC,
        5,
        None,
        452,
    ),
    ("Ford", "Mustang", 2022, FuelType.PETROL, TransmissionType.MANUAL, 4, 5000, 450),
    (
        "Ford",
        "Explorer",
        2023,
        FuelType.PETROL,
        TransmissionType.AUTOMATIC,
        7,
        2300,
        300,
    ),
    ("Ford", "Ranger", 2021, FuelType.DIESEL, TransmissionType.MANUAL, 5, 2000, 213),
    ("Ford", "Focus", 2018, FuelType.PETROL, TransmissionType.MANUAL, 5, 1500, 123),
    # Volkswagen
    (
        "Volkswagen",
        "Golf",
        2022,
        FuelType.PETROL,
        TransmissionType.MANUAL,
        5,
        1400,
        148,
    ),
    (
        "Volkswagen",
        "Golf",
        2023,
        FuelType.DIESEL,
        TransmissionType.DUAL_CLUTCH,
        5,
        2000,
        148,
    ),
    (
        "Volkswagen",
        "Tiguan",
        2023,
        FuelType.PETROL,
        TransmissionType.AUTOMATIC,
        5,
        2000,
        184,
    ),
    (
        "Volkswagen",
        "Passat",
        2020,
        FuelType.DIESEL,
        TransmissionType.AUTOMATIC,
        5,
        2000,
        187,
    ),
    (
        "Volkswagen",
        "ID.4",
        2024,
        FuelType.ELECTRIC,
        TransmissionType.AUTOMATIC,
        5,
        None,
        201,
    ),
    ("Volkswagen", "Polo", 2019, FuelType.PETROL, TransmissionType.MANUAL, 5, 1000, 94),
    # BMW
    (
        "BMW",
        "3 Series",
        2023,
        FuelType.PETROL,
        TransmissionType.AUTOMATIC,
        5,
        2000,
        255,
    ),
    (
        "BMW",
        "5 Series",
        2022,
        FuelType.DIESEL,
        TransmissionType.AUTOMATIC,
        5,
        3000,
        282,
    ),
    ("BMW", "X5", 2023, FuelType.PETROL, TransmissionType.AUTOMATIC, 5, 3000, 375),
    ("BMW", "i4", 2024, FuelType.ELECTRIC, TransmissionType.AUTOMATIC, 5, None, 335),
    ("BMW", "1 Series", 2021, FuelType.PETROL, TransmissionType.MANUAL, 5, 1500, 136),
    # Mercedes-Benz
    (
        "Mercedes-Benz",
        "C-Class",
        2023,
        FuelType.PETROL,
        TransmissionType.AUTOMATIC,
        5,
        2000,
        255,
    ),
    (
        "Mercedes-Benz",
        "E-Class",
        2022,
        FuelType.DIESEL,
        TransmissionType.AUTOMATIC,
        5,
        2000,
        197,
    ),
    (
        "Mercedes-Benz",
        "GLC",
        2023,
        FuelType.PETROL,
        TransmissionType.AUTOMATIC,
        5,
        2000,
        255,
    ),
    (
        "Mercedes-Benz",
        "EQS",
        2024,
        FuelType.ELECTRIC,
        TransmissionType.AUTOMATIC,
        5,
        None,
        516,
    ),
    (
        "Mercedes-Benz",
        "A-Class",
        2020,
        FuelType.PETROL,
        TransmissionType.DUAL_CLUTCH,
        5,
        1300,
        161,
    ),
    # Hyundai
    (
        "Hyundai",
        "Elantra",
        2023,
        FuelType.PETROL,
        TransmissionType.AUTOMATIC,
        5,
        2000,
        147,
    ),
    (
        "Hyundai",
        "Tucson",
        2023,
        FuelType.PETROL,
        TransmissionType.AUTOMATIC,
        5,
        2500,
        187,
    ),
    (
        "Hyundai",
        "Santa Fe",
        2022,
        FuelType.DIESEL,
        TransmissionType.AUTOMATIC,
        7,
        2200,
        200,
    ),
    (
        "Hyundai",
        "Ioniq 5",
        2024,
        FuelType.ELECTRIC,
        TransmissionType.AUTOMATIC,
        5,
        None,
        320,
    ),
    ("Hyundai", "i10", 2019, FuelType.PETROL, TransmissionType.MANUAL, 5, 1200, 87),
    # Kia
    (
        "Kia",
        "Sportage",
        2023,
        FuelType.PETROL,
        TransmissionType.AUTOMATIC,
        5,
        2500,
        187,
    ),
    ("Kia", "Sorento", 2022, FuelType.DIESEL, TransmissionType.AUTOMATIC, 7, 2200, 202),
    ("Kia", "EV6", 2024, FuelType.ELECTRIC, TransmissionType.AUTOMATIC, 5, None, 320),
    ("Kia", "Rio", 2020, FuelType.PETROL, TransmissionType.MANUAL, 5, 1400, 100),
    # Nissan
    ("Nissan", "Altima", 2022, FuelType.PETROL, TransmissionType.CVT, 5, 2500, 188),
    ("Nissan", "Qashqai", 2023, FuelType.PETROL, TransmissionType.CVT, 5, 1300, 156),
    ("Nissan", "Navara", 2021, FuelType.DIESEL, TransmissionType.MANUAL, 5, 2300, 190),
    (
        "Nissan",
        "Leaf",
        2023,
        FuelType.ELECTRIC,
        TransmissionType.AUTOMATIC,
        5,
        None,
        147,
    ),
    # Mazda
    ("Mazda", "CX-5", 2023, FuelType.PETROL, TransmissionType.AUTOMATIC, 5, 2500, 187),
    ("Mazda", "Mazda3", 2022, FuelType.PETROL, TransmissionType.MANUAL, 5, 2000, 155),
    ("Mazda", "CX-30", 2021, FuelType.PETROL, TransmissionType.AUTOMATIC, 5, 2000, 186),
    # Subaru
    ("Subaru", "Outback", 2023, FuelType.PETROL, TransmissionType.CVT, 5, 2500, 182),
    ("Subaru", "Forester", 2022, FuelType.PETROL, TransmissionType.CVT, 5, 2500, 182),
    ("Subaru", "Impreza", 2020, FuelType.PETROL, TransmissionType.MANUAL, 5, 2000, 152),
    # Tesla
    (
        "Tesla",
        "Model 3",
        2024,
        FuelType.ELECTRIC,
        TransmissionType.AUTOMATIC,
        5,
        None,
        283,
    ),
    (
        "Tesla",
        "Model Y",
        2024,
        FuelType.ELECTRIC,
        TransmissionType.AUTOMATIC,
        5,
        None,
        384,
    ),
    (
        "Tesla",
        "Model S",
        2023,
        FuelType.ELECTRIC,
        TransmissionType.AUTOMATIC,
        5,
        None,
        670,
    ),
    (
        "Tesla",
        "Model X",
        2023,
        FuelType.ELECTRIC,
        TransmissionType.AUTOMATIC,
        7,
        None,
        670,
    ),
    # Porsche
    (
        "Porsche",
        "911",
        2023,
        FuelType.PETROL,
        TransmissionType.DUAL_CLUTCH,
        4,
        3000,
        379,
    ),
    (
        "Porsche",
        "Cayenne",
        2022,
        FuelType.PETROL,
        TransmissionType.AUTOMATIC,
        5,
        3000,
        335,
    ),
    (
        "Porsche",
        "Taycan",
        2024,
        FuelType.ELECTRIC,
        TransmissionType.AUTOMATIC,
        5,
        None,
        469,
    ),
    # Chevrolet
    (
        "Chevrolet",
        "Silverado",
        2023,
        FuelType.PETROL,
        TransmissionType.AUTOMATIC,
        5,
        5300,
        355,
    ),
    ("Chevrolet", "Malibu", 2021, FuelType.PETROL, TransmissionType.CVT, 5, 1500, 160),
    (
        "Chevrolet",
        "Equinox",
        2022,
        FuelType.PETROL,
        TransmissionType.AUTOMATIC,
        5,
        1500,
        175,
    ),
    (
        "Chevrolet",
        "Bolt EV",
        2023,
        FuelType.ELECTRIC,
        TransmissionType.AUTOMATIC,
        5,
        None,
        200,
    ),
    # Audi
    ("Audi", "A4", 2022, FuelType.PETROL, TransmissionType.DUAL_CLUTCH, 5, 2000, 201),
    ("Audi", "Q5", 2023, FuelType.DIESEL, TransmissionType.AUTOMATIC, 5, 2000, 201),
    (
        "Audi",
        "e-tron",
        2023,
        FuelType.ELECTRIC,
        TransmissionType.AUTOMATIC,
        5,
        None,
        355,
    ),
    # Volvo
    ("Volvo", "XC60", 2023, FuelType.PETROL, TransmissionType.AUTOMATIC, 5, 2000, 250),
    ("Volvo", "XC90", 2022, FuelType.DIESEL, TransmissionType.AUTOMATIC, 7, 2000, 235),
    ("Volvo", "C40", 2024, FuelType.ELECTRIC, TransmissionType.AUTOMATIC, 5, None, 402),
]


async def seed_vehicle_models() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Manufacturer.id, Manufacturer.name))
        manufacturer_ids = {name: id_ for id_, name in result.all()}

        rows = []
        skipped_manufacturers = set()
        for (
            manufacturer_name,
            name,
            year,
            fuel_type,
            transmission,
            seating_capacity,
            engine_displacement_cc,
            horsepower,
        ) in VEHICLE_MODELS:
            manufacturer_id = manufacturer_ids.get(manufacturer_name)
            if manufacturer_id is None:
                skipped_manufacturers.add(manufacturer_name)
                continue

            rows.append(
                {
                    "manufacturer_id": manufacturer_id,
                    "name": name,
                    "year": year,
                    "fuel_type": fuel_type,
                    "transmission": transmission,
                    "seating_capacity": seating_capacity,
                    "engine_displacement_cc": engine_displacement_cc,
                    "horsepower": horsepower,
                    "is_active": True,
                }
            )

        if not rows:
            print(
                "No vehicle models to seed — have manufacturers been seeded yet? "
                "Run `python -m app.seeds.manufacturers` first."
            )
            return

        stmt = pg_insert(VehicleModel).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["manufacturer_id", "name", "year"],
            index_where=text("deleted_at IS NULL"),
        )
        await session.execute(stmt)
        await session.commit()

    print(f"Seeded {len(rows)} vehicle models (duplicates skipped).")
    if skipped_manufacturers:
        print(
            f"Skipped {len(skipped_manufacturers)} manufacturer(s) not found in DB: "
            f"{', '.join(sorted(skipped_manufacturers))}"
        )


if __name__ == "__main__":
    asyncio.run(seed_vehicle_models())
