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
from app.models.vehicle_assignment import AssignmentStatus, AssignmentType
from app.schemas.base import QueryParams
from app.schemas.vehicle_assignment import (
    DriverAssignmentComplete,
    DriverAssignmentCreate,
    FleetManagerAssignmentComplete,
    FleetManagerAssignmentCreate,
    VehicleAssignmentFilter,
    VehicleAssignmentUpdate,
)
from app.services.user_service import user_service
from app.services.vehicle_assignment_service import vehicle_assignment_service
from app.services.vehicle_service import vehicle_service

TempDpnds = Annotated[Jinja2Templates, Depends(get_template)]
router = APIRouter(dependencies=[Depends(require_user)])


async def _available_vehicles(db: AsyncSession) -> list:
    """get list of vehicles with status: available"""
    query = vehicle_service.crud.build_query(filters={"status": "available"})
    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def _user_list_by_role(db: AsyncSession, role: str) -> list:
    """get list of drivers"""
    query = user_service.crud.build_query(
        filters={"role": role}, sort_by="full_name", order_by="asc"
    )
    result = await db.execute(query)
    return list(result.scalars().unique().all())


@router.get("/", response_class=HTMLResponse)
async def list_vehicle_assignments(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[QueryParams, Depends(get_query_params(VehicleAssignmentFilter))],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_assignment_read))
    ],
):
    if params.filters.include_deleted and not current_user.is_super_user:
        raise HTTPException(
            status_code=403,
            detail="Only system admins can view deleted assignments",
        )

    result = await vehicle_assignment_service.list(request, db, params, current_user)

    context = {
        "request": request,
        "page": "vehicles",
        "subpage": "assignments",
        "assignments": result.items,
        "search": params.filters.search,
        "assignment_type_filter": params.filters.assignment_type,
        "status_filter": params.filters.status,
        "assignment_types": list(AssignmentType),
        "statuses": list(AssignmentStatus),
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
            "vehicle_assignments/vehicle_assignment_list_content.html", context
        )

    return templates.TemplateResponse("vehicle_assignments/vehicle_assignments.html", context)


@router.get("/{assignment_id}", response_class=HTMLResponse)
async def read_vehicle_assignment(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    assignment_id: UUID,
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_assignment_read))
    ],
):
    assignment = await vehicle_assignment_service.get_or_404(db, assignment_id, current_user)
    return templates.TemplateResponse(
        "vehicle_assignments/vehicle_assignment_detail.html",
        {
            "request": request,
            "assignment": assignment,
            "user": current_user,
            "page": "vehicles",
            "subpage": "assignments",
        },
    )


@router.get("/drivers/new", response_class=HTMLResponse)
async def new_driver_assignment_form(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_assignment_create))
    ],
):
    vehicles = await _available_vehicles(db)
    drivers = await _user_list_by_role(db, role="driver")
    return templates.TemplateResponse(
        "vehicle_assignments/vehicle_assignment_form_driver.html",
        {
            "request": request,
            "vehicles": vehicles,
            "drivers": drivers,
            "user": current_user,
            "page": "vehicles",
            "subpage": "assignments",
        },
    )


@router.get("/fleet-managers/new", response_class=HTMLResponse)
async def new_fleet_manager_assignment_form(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_assignment_create))
    ],
):
    vehicles = await _available_vehicles(db)
    fleet_managers = await _user_list_by_role(db, role="fleet_manager")
    return templates.TemplateResponse(
        "vehicle_assignments/vehicle_assignment_form_fleet_manager.html",
        {
            "request": request,
            "vehicles": vehicles,
            "fleet_managers": fleet_managers,
            "user": current_user,
            "page": "vehicles",
            "subpage": "assignments",
        },
    )


@router.get("/{assignment_id}/edit", response_class=HTMLResponse)
async def edit_vehicle_assignment_form(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    assignment_id: UUID,
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_assignment_update))
    ],
):
    assignment = await vehicle_assignment_service.get_or_404(db, assignment_id, current_user)
    return templates.TemplateResponse(
        "vehicle_assignments/vehicle_assignment_edit_form.html",
        {
            "request": request,
            "assignment": assignment,
            "user": current_user,
            "page": "vehicles",
            "subpage": "assignments",
        },
    )


@router.post("/drivers", response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
async def create_driver_assignment(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    assignment_in: Annotated[DriverAssignmentCreate, Form()],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_assignment_create))
    ],
):
    await vehicle_assignment_service.create(db, assignment_in, current_user)
    response = HTMLResponse(content="", status_code=status.HTTP_201_CREATED)
    response.headers["HX-Redirect"] = "/vehicle-assignments"
    return response


@router.post(
    "/fleet-managers",
    response_class=HTMLResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_fleet_manager_assignment(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    assignment_in: Annotated[FleetManagerAssignmentCreate, Form()],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_assignment_create))
    ],
):
    await vehicle_assignment_service.create(db, assignment_in, current_user)
    response = HTMLResponse(content="", status_code=status.HTTP_201_CREATED)
    response.headers["HX-Redirect"] = "/vehicle-assignments"
    return response


@router.put("/{assignment_id}", response_class=HTMLResponse)
async def update_vehicle_assignment(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    assignment_id: UUID,
    assignment_in: Annotated[VehicleAssignmentUpdate, Form()],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_assignment_update))
    ],
):
    assignment = await vehicle_assignment_service.update(
        db, assignment_id, assignment_in, current_user
    )
    response = HTMLResponse(content="")
    response.headers["HX-Redirect"] = f"/vehicle-assignments/{assignment.id}"
    return response


@router.delete("/{assignment_id}", status_code=status.HTTP_200_OK)
async def delete_vehicle_assignment(
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    assignment_id: UUID,
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_assignment_delete))
    ],
):
    return await vehicle_assignment_service.delete(db, assignment_id, current_user)


@router.post("/{assignment_id}/drivers/complete", response_class=HTMLResponse)
async def complete_driver_assignment(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    assignment_id: UUID,
    complete_in: Annotated[DriverAssignmentComplete, Form()],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_assignment_update))
    ],
):
    assignment = await vehicle_assignment_service.complete(
        db, assignment_id, current_user, complete_in
    )
    response = HTMLResponse(content="")
    response.headers["HX-Redirect"] = f"/vehicle-assignments/{assignment.id}"
    return response


@router.post("/{assignment_id}/fleet-managers/complete", response_class=HTMLResponse)
async def complete_fleet_manager_assignment(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    assignment_id: UUID,
    complete_in: Annotated[FleetManagerAssignmentComplete, Form()],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_assignment_update))
    ],
):
    assignment = await vehicle_assignment_service.complete(
        db, assignment_id, current_user, complete_in
    )
    response = HTMLResponse(content="")
    response.headers["HX-Redirect"] = f"/vehicle-assignments/{assignment.id}"
    return response


@router.post("/{assignment_id}/cancel", response_class=HTMLResponse)
async def cancel_vehicle_assignment(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    assignment_id: UUID,
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_assignment_update))
    ],
):
    assignment = await vehicle_assignment_service.cancel(db, assignment_id, current_user)
    response = HTMLResponse(content="")
    response.headers["HX-Redirect"] = f"/vehicle-assignments/{assignment.id}"
    return response
