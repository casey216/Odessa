from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.core.logging import logger
from app.database import Base, engine
from app.routers import (
    activity,
    auth,
    manufacturer,
    users,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
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
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(activity.router, prefix="/activity", tags=["activity logs"])


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")
