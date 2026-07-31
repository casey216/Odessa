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
from app.schemas.base import QueryParams
from app.schemas.workshop import (
    WorkshopCreate,
    WorkshopFilter,
)
from app.services.workshop_service import workshop_service

TempDpnds = Annotated[Jinja2Templates, Depends(get_template)]
router = APIRouter(dependencies=[Depends(require_user)])


@router.get("/", response_class=HTMLResponse)
async def list_workshops(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[QueryParams, Depends(get_query_params(WorkshopFilter))],
    current_user: Annotated[User, Depends(require_permission(PermissionCode.workshop_read))],
):
    if params.filters.include_deleted and not current_user.is_super_user:
        raise HTTPException(status_code=403, detail="Only system admins can view deleted workshops")

    result = await workshop_service.list(request, db, params)

    context = {
        "request": request,
        "page": "locations",
        "subpage": "workshops",
        "workshops": result.items,
        "search": params.filters.search,
        "status_filter": params.filters.is_active,
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
        return templates.TemplateResponse("workshops/workshop_list_content.html", context)

    return templates.TemplateResponse("workshops/workshops.html", context)


@router.get("/new", response_class=HTMLResponse)
async def new_workshop_form(
    request: Request,
    templates: TempDpnds,
    current_user: Annotated[User, Depends(require_permission(PermissionCode.workshop_create))],
):
    return templates.TemplateResponse(
        "workshops/workshop_form.html",
        {
            "request": request,
            "workshop": None,
            "user": current_user,
            "page": "locations",
            "subpage": "workshops",
        },
    )


@router.post("/", response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
async def create_workshop(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    workshop_in: Annotated[WorkshopCreate, Form()],
    current_user: Annotated[User, Depends(require_permission(PermissionCode.workshop_create))],
):
    await workshop_service.create(db, workshop_in, current_user)
    response = HTMLResponse(content="", status_code=status.HTTP_201_CREATED)
    response.headers["HX-Redirect"] = "/workshops"
    return response


@router.get("/{workshop_id}", response_class=HTMLResponse)
async def read_workshop(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    workshop_id: UUID,
    current_user: Annotated[User, Depends(require_permission(PermissionCode.workshop_read))],
):
    workshop = await workshop_service.get_or_404(db, workshop_id)
    return templates.TemplateResponse(
        "workshops/workshop_detail.html",
        {
            "request": request,
            "workshop": workshop,
            "user": current_user,
            "page": "locations",
            "subpage": "workshops",
        },
    )
