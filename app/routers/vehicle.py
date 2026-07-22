from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    get_audited_db,
    get_db,
    get_query_params,
    get_template,
    require_permission,
    require_user,
)
from app.core.permissions import PermissionCode
from app.models.tag import VehicleTagChoice
from app.models.user import User
from app.models.vehicle import VehicleStatus
from app.schemas.base import QueryParams
from app.schemas.vehicle import VehicleCreate, VehicleFilter, VehicleUpdate
from app.services.vehicle_model_service import vehicle_model_service
from app.services.vehicle_service import vehicle_service

TempDpnds = Annotated[Jinja2Templates, Depends(get_template)]
router = APIRouter(dependencies=[Depends(require_user)])


async def _active_vehicle_models(db: AsyncSession) -> list:
    """Populates the vehicle-model <select> on list/form pages."""
    query = vehicle_model_service.crud.build_query(
        filters={"is_active": True}, sort_by="name", order_by="asc"
    )
    result = await db.execute(query)
    return list(result.scalars().unique().all())


@router.get("/", response_class=HTMLResponse)
async def list_vehicles(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[QueryParams, Depends(get_query_params(VehicleFilter))],
    current_user: Annotated[User, Depends(require_permission(PermissionCode.vehicle_read))],
):
    if params.filters.include_deleted and not current_user.is_super_user:
        raise HTTPException(status_code=403, detail="Only system admins can view deleted vehicles")

    result = await vehicle_service.list(request, db, params, current_user)
    vehicle_models = await _active_vehicle_models(db)

    context = {
        "request": request,
        "page": "vehicles",
        "subpage": "vehicles",
        "vehicles": result.items,
        "vehicle_models": vehicle_models,
        "tag_choices": list(VehicleTagChoice),
        "search": params.filters.search,
        "status_filter": params.filters.status,
        "active_filter": params.filters.is_active,
        "vehicle_model_filter": params.filters.vehicle_model_id,
        "tag_filter": params.filters.tag,
        "statuses": list(VehicleStatus),
        "user": current_user,
        "pagination": {
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "pages": result.pages,
            "links": result.links,
        },
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("vehicles/vehicle_list_content.html", context)

    return templates.TemplateResponse("vehicles/vehicles.html", context)


@router.get("/new", response_class=HTMLResponse)
async def new_vehicle_form(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permission(PermissionCode.vehicle_create))],
):
    vehicle_models = await _active_vehicle_models(db)
    return templates.TemplateResponse(
        "vehicles/vehicle_form.html",
        {
            "request": request,
            "vehicle": None,
            "vehicle_models": vehicle_models,
            "statuses": list(VehicleStatus),
            "tag_choices": list(VehicleTagChoice),
            "user": current_user,
            "page": "vehicles",
            "subpage": "vehicles",
        },
    )


@router.get("/{vehicle_id}/edit", response_class=HTMLResponse)
async def edit_vehicle_form(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    vehicle_id: UUID,
    current_user: Annotated[User, Depends(require_permission(PermissionCode.vehicle_update))],
):
    vehicle = await vehicle_service.get_or_404(db, vehicle_id)
    vehicle_models = await _active_vehicle_models(db)
    return templates.TemplateResponse(
        "vehicles/vehicle_form.html",
        {
            "request": request,
            "vehicle": vehicle,
            "vehicle_models": vehicle_models,
            "statuses": list(VehicleStatus),
            "tag_choices": list(VehicleTagChoice),
            "user": current_user,
            "page": "vehicles",
            "subpage": "vehicles",
        },
    )


@router.get("/{vehicle_id}", response_class=HTMLResponse)
async def read_vehicle(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    vehicle_id: UUID,
    current_user: Annotated[User, Depends(require_permission(PermissionCode.vehicle_read))],
):
    vehicle = await vehicle_service.get_or_404(db, vehicle_id)
    return templates.TemplateResponse(
        "vehicles/vehicle_detail.html",
        {
            "request": request,
            "vehicle": vehicle,
            "user": current_user,
            "page": "vehicles",
            "subpage": "vehicles",
        },
    )


@router.post("/", response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    vehicle_in: Annotated[VehicleCreate, Form()],
    current_user: Annotated[User, Depends(require_permission(PermissionCode.vehicle_create))],
):
    await vehicle_service.create(db, vehicle_in, current_user)
    response = HTMLResponse(content="", status_code=status.HTTP_201_CREATED)
    response.headers["HX-Redirect"] = "/vehicles"
    return response


@router.put("/{vehicle_id}", response_class=HTMLResponse)
async def update_vehicle(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    vehicle_id: UUID,
    vehicle_in: Annotated[VehicleUpdate, Form()],
    current_user: Annotated[User, Depends(require_permission(PermissionCode.vehicle_update))],
):
    vehicle = await vehicle_service.update(db, vehicle_id, vehicle_in, current_user)
    response = HTMLResponse(content="")
    response.headers["HX-Redirect"] = f"/vehicles/{vehicle.id}"
    return response


@router.delete("/{vehicle_id}", status_code=status.HTTP_200_OK)
async def delete_vehicle(
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    vehicle_id: UUID,
    current_user: Annotated[User, Depends(require_permission(PermissionCode.vehicle_delete))],
):
    return await vehicle_service.delete(db, vehicle_id)


@router.post("/{vehicle_id}/activate", response_class=HTMLResponse)
async def activate_vehicle(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    vehicle_id: UUID,
    current_user: Annotated[User, Depends(require_permission(PermissionCode.vehicle_update))],
):
    vehicle = await vehicle_service.set_active_status(db, vehicle_id, is_active=True)
    return templates.TemplateResponse(
        "vehicles/vehicle_rows.html",
        {"request": request, "vehicles": [vehicle]},
    )


@router.post("/{vehicle_id}/deactivate", response_class=HTMLResponse)
async def deactivate_vehicle(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    vehicle_id: UUID,
    current_user: Annotated[User, Depends(require_permission(PermissionCode.vehicle_update))],
):
    vehicle = await vehicle_service.set_active_status(db, vehicle_id, is_active=False)
    return templates.TemplateResponse(
        "vehicles/vehicle_rows.html",
        {"request": request, "vehicles": [vehicle]},
    )
