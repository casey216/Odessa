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
from app.models.user import User
from app.models.vehicle_model import FuelType, TransmissionType
from app.schemas.base import QueryParams
from app.schemas.vehicle_model import (
    VehicleModelCreate,
    VehicleModelFilter,
    VehicleModelUpdate,
)
from app.services.manufacturer_service import manufacturer_service
from app.services.vehicle_model_service import vehicle_model_service

TempDpnds = Annotated[Jinja2Templates, Depends(get_template)]
router = APIRouter(dependencies=[Depends(require_user)])


async def _active_manufacturers(db: AsyncSession) -> list:
    """Small helper for populating the manufacturer <select> on list/form pages."""
    query = manufacturer_service.crud.build_query(
        filters={"is_active": True}, sort_by="name", order_by="asc"
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/", response_class=HTMLResponse)
async def list_vehicle_models(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[QueryParams, Depends(get_query_params(VehicleModelFilter))],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_model_read))
    ],
):
    if params.filters.include_deleted and not current_user.is_super_user:
        raise HTTPException(
            status_code=403,
            detail="Only system admins can view deleted vehicle models",
        )

    result = await vehicle_model_service.list(request, db, params)
    manufacturers = await _active_manufacturers(db)

    context = {
        "request": request,
        "page": "vehicles",
        "subpage": "vehicle-models",
        "vehicle_models": result.items,
        "manufacturers": manufacturers,
        "search": params.filters.search,
        "status_filter": params.filters.is_active,
        "manufacturer_filter": params.filters.manufacturer_id,
        "fuel_types": list(FuelType),
        "transmissions": list(TransmissionType),
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
        return templates.TemplateResponse(
            "vehicle_models/vehicle_model_rows.html", context
        )

    return templates.TemplateResponse("vehicle_models/vehicle_models.html", context)


@router.get("/new", response_class=HTMLResponse)
async def new_vehicle_model_form(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_model_create))
    ],
):
    manufacturers = await _active_manufacturers(db)
    return templates.TemplateResponse(
        "vehicle_models/vehicle_model_form.html",
        {
            "request": request,
            "vehicle_model": None,
            "manufacturers": manufacturers,
            "fuel_types": list(FuelType),
            "transmissions": list(TransmissionType),
            "user": current_user,
            "page": "vehicles",
            "subpage": "vehicle-models",
        },
    )


@router.get("/{vehicle_model_id}/edit", response_class=HTMLResponse)
async def edit_vehicle_model_form(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    vehicle_model_id: UUID,
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_model_update))
    ],
):
    vehicle_model = await vehicle_model_service.get_or_404(db, vehicle_model_id)
    manufacturers = await _active_manufacturers(db)
    return templates.TemplateResponse(
        "vehicle_models/vehicle_model_form.html",
        {
            "request": request,
            "vehicle_model": vehicle_model,
            "manufacturers": manufacturers,
            "fuel_types": list(FuelType),
            "transmissions": list(TransmissionType),
            "user": current_user,
            "page": "vehicles",
            "subpage": "vehicle-models",
        },
    )


@router.get("/{vehicle_model_id}", response_class=HTMLResponse)
async def read_vehicle_model(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    vehicle_model_id: UUID,
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_model_read))
    ],
):
    vehicle_model = await vehicle_model_service.get_or_404(db, vehicle_model_id)
    return templates.TemplateResponse(
        "vehicle_models/vehicle_model_detail.html",
        {
            "request": request,
            "vehicle_model": vehicle_model,
            "user": current_user,
            "page": "vehicles",
            "subpage": "vehicle-models",
        },
    )


@router.post("/", response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle_model(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    vehicle_model_in: Annotated[VehicleModelCreate, Form()],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_model_create))
    ],
):
    await vehicle_model_service.create(db, vehicle_model_in, current_user)
    response = HTMLResponse(content="", status_code=status.HTTP_201_CREATED)
    response.headers["HX-Redirect"] = "/vehicle-models"
    return response


@router.put("/{vehicle_model_id}", response_class=HTMLResponse)
async def update_vehicle_model(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    vehicle_model_id: UUID,
    vehicle_model_in: Annotated[VehicleModelUpdate, Form()],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_model_update))
    ],
):
    vehicle_model = await vehicle_model_service.update(
        db, vehicle_model_id, vehicle_model_in, current_user
    )
    response = HTMLResponse(content="")
    response.headers["HX-Redirect"] = f"/vehicle-models/{vehicle_model.id}"
    return response


@router.delete("/{vehicle_model_id}", status_code=status.HTTP_200_OK)
async def delete_vehicle_model(
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    vehicle_model_id: UUID,
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_model_delete))
    ],
):
    return await vehicle_model_service.delete(db, vehicle_model_id)


@router.post("/{vehicle_model_id}/activate", response_class=HTMLResponse)
async def activate_vehicle_model(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    vehicle_model_id: UUID,
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_model_update))
    ],
):
    vehicle_model = await vehicle_model_service.set_active_status(
        db, vehicle_model_id, is_active=True
    )
    return templates.TemplateResponse(
        "vehicle_models/vehicle_model_rows.html",
        {"request": request, "vehicle_models": [vehicle_model]},
    )


@router.post("/{vehicle_model_id}/deactivate", response_class=HTMLResponse)
async def deactivate_vehicle_model(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    vehicle_model_id: UUID,
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_model_update))
    ],
):
    vehicle_model = await vehicle_model_service.set_active_status(
        db, vehicle_model_id, is_active=False
    )
    return templates.TemplateResponse(
        "vehicle_models/vehicle_model_rows.html",
        {"request": request, "vehicle_models": [vehicle_model]},
    )
