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
    DriverAssignmentClose,
    DriverAssignmentCreate,
    FleetManagerAssignmentClose,
    FleetManagerAssignmentCreate,
    VehicleAssignmentFilter,
    VehicleAssignmentUpdate,
)
from app.services.vehicle_assignment_service import vehicle_assignment_service

TempDpnds = Annotated[Jinja2Templates, Depends(get_template)]
router = APIRouter(dependencies=[Depends(require_user)])


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

    result = await vehicle_assignment_service.list(request, db, params)

    context = {
        "request": request,
        "page": "vehicle_assignments",
        "subpage": "vehicle_assignments",
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

    return templates.TemplateResponse(
        "vehicle_assignments/vehicle_assignments.html", context
    )


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
    assignment = await vehicle_assignment_service.get_or_404(db, assignment_id)
    return templates.TemplateResponse(
        "vehicle_assignments/vehicle_assignment_detail.html",
        {
            "request": request,
            "assignment": assignment,
            "user": current_user,
            "page": "vehicle_assignments",
            "subpage": "vehicle_assignments",
        },
    )


@router.post(
    "/drivers", response_class=HTMLResponse, status_code=status.HTTP_201_CREATED
)
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
    return await vehicle_assignment_service.delete(db, assignment_id)


@router.post("/{assignment_id}/drivers/close", response_class=HTMLResponse)
async def close_driver_assignment(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    assignment_id: UUID,
    close_in: Annotated[DriverAssignmentClose, Form()],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_assignment_update))
    ],
):
    if close_in.status == AssignmentStatus.COMPLETED:
        assignment = await vehicle_assignment_service.complete(
            db, assignment_id, current_user, close_in
        )
    else:
        assignment = await vehicle_assignment_service.cancel(
            db, assignment_id, current_user, close_in
        )
    return templates.TemplateResponse(
        "vehicle_assignments/vehicle_assignment_rows.html",
        {"request": request, "assignments": [assignment]},
    )


@router.post("/{assignment_id}/fleet-managers/close", response_class=HTMLResponse)
async def close_fleet_manager_assignment(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    assignment_id: UUID,
    close_in: Annotated[FleetManagerAssignmentClose, Form()],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.vehicle_assignment_update))
    ],
):
    if close_in.status == AssignmentStatus.COMPLETED:
        assignment = await vehicle_assignment_service.complete(
            db, assignment_id, current_user, close_in
        )
    else:
        assignment = await vehicle_assignment_service.cancel(
            db, assignment_id, current_user, close_in
        )
    return templates.TemplateResponse(
        "vehicle_assignments/vehicle_assignment_rows.html",
        {"request": request, "assignments": [assignment]},
    )
