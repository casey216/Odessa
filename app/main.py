from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.core.exceptions.handlers import register_exception_handlers
from app.core.logging import logger
from app.routers import (
    activity,
    auth,
    manufacturer,
    permission,
    users,
    vehicle,
    vehicle_model,
)
from app.scripts.sync_permissions import sync_permissions


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        logger.info("Database connection successful")

        async with AsyncSessionLocal() as db:
            await sync_permissions(db)

    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        raise

    yield

    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

register_exception_handlers(app)


# Custom template filters
def format_currency(value):
    if value is None:
        return "—"
    return f"₦{float(value):,.2f}"


def format_km(value):
    if value is None:
        return "—"
    return f"{int(value):,} km"


def format_date(value):
    if value is None:
        return "—"
    if hasattr(value, "strftime"):
        return value.strftime("%b %d, %Y")
    return str(value)


def days_until(value):
    if value is None:
        return None
    from datetime import date

    if hasattr(value, "date"):
        d = value.date()
    else:
        d = value
    delta = (d - date.today()).days
    return delta


def truncate_uuid(value):
    if value is None:
        return None
    return str(value)[:8]


templates.env.filters["currency"] = format_currency
templates.env.filters["km"] = format_km
templates.env.filters["fmt_date"] = format_date
templates.env.filters["days_until"] = days_until
templates.env.filters["truncate_uuid"] = truncate_uuid

# Inject templates into routers that need it
app.state.templates = templates

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(manufacturer.router, prefix="/manufacturers", tags=["manufacturers"])
app.include_router(
    vehicle_model.router, prefix="/vehicle-models", tags=["vehicle models"]
)
app.include_router(vehicle.router, prefix="/vehicles", tags=["vehicles"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(permission.router)
app.include_router(activity.router, prefix="/activity", tags=["activity logs"])


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")
