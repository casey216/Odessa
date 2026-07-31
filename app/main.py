from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.core.exceptions.handlers import register_exception_handlers
from app.core.logging import logger
from app.core.templates import templates
from app.routers import (
    activity,
    auth,
    manufacturer,
    permission,
    users,
    vehicle,
    vehicle_assignment,
    vehicle_model,
    workshop,
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

app.mount("/static", StaticFiles(directory="app/static"), name="static")

register_exception_handlers(app)

app.state.templates = templates

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(manufacturer.router, prefix="/manufacturers", tags=["manufacturers"])
app.include_router(vehicle_model.router, prefix="/vehicle-models", tags=["vehicle models"])
app.include_router(vehicle.router, prefix="/vehicles", tags=["vehicles"])
app.include_router(
    vehicle_assignment.router,
    prefix="/vehicle-assignments",
    tags=["vehicle assignments"],
)
app.include_router(workshop.router, prefix="/workshops", tags=["workshops"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(permission.router)
app.include_router(activity.router, prefix="/activity", tags=["activity logs"])


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")
