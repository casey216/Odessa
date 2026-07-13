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
from app.schemas.manufacturer import (
    ManufacturerCreate,
    ManufacturerFilter,
    ManufacturerUpdate,
)
from app.services.manufacturer_service import manufacturer_service

TempDpnds = Annotated[Jinja2Templates, Depends(get_template)]
router = APIRouter(dependencies=[Depends(require_user)])


@router.get("/", response_class=HTMLResponse)
async def list_manufacturers(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[QueryParams, Depends(get_query_params(ManufacturerFilter))],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.manufacturer_read))
    ],
):
    if params.filters.include_deleted and not current_user.is_super_user:
        raise HTTPException(
            status_code=403, detail="Only system admins can view deleted manufacturers"
        )

    result = await manufacturer_service.list(request, db, params)

    context = {
        "request": request,
        "page": "vehicles",
        "subpage": "manufacturers",
        "manufacturers": result.items,
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
        return templates.TemplateResponse(
            "manufacturers/manufacturer_list_content.html", context
        )

    return templates.TemplateResponse("manufacturers/manufacturers.html", context)


@router.get("/new", response_class=HTMLResponse)
async def new_manufacturer_form(
    request: Request,
    templates: TempDpnds,
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.manufacturer_create))
    ],
):
    return templates.TemplateResponse(
        "manufacturers/manufacturer_form.html",
        {
            "request": request,
            "manufacturer": None,
            "user": current_user,
            "page": "vehicles",
            "subpage": "manufacturers",
        },
    )


@router.get("/{manufacturer_id}/edit", response_class=HTMLResponse)
async def edit_manufacturer_form(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    manufacturer_id: UUID,
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.manufacturer_update))
    ],
):
    manufacturer = await manufacturer_service.get_or_404(db, manufacturer_id)
    return templates.TemplateResponse(
        "manufacturers/manufacturer_form.html",
        {
            "request": request,
            "manufacturer": manufacturer,
            "user": current_user,
            "page": "vehicles",
            "subpage": "manufacturers",
        },
    )


@router.get("/{manufacturer_id}", response_class=HTMLResponse)
async def read_manufacturer(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    manufacturer_id: UUID,
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.manufacturer_read))
    ],
):
    manufacturer = await manufacturer_service.get_or_404(db, manufacturer_id)
    return templates.TemplateResponse(
        "manufacturers/manufacturer_detail.html",
        {
            "request": request,
            "manufacturer": manufacturer,
            "user": current_user,
            "page": "vehicles",
            "subpage": "manufacturers",
        },
    )


@router.post("/", response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
async def create_manufacturer(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    manufacturer_in: Annotated[ManufacturerCreate, Form()],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.manufacturer_create))
    ],
):
    await manufacturer_service.create(db, manufacturer_in, current_user)
    response = HTMLResponse(content="", status_code=status.HTTP_201_CREATED)
    response.headers["HX-Redirect"] = "/manufacturers"
    return response


@router.put("/{manufacturer_id}", response_class=HTMLResponse)
async def update_manufacturer(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    manufacturer_id: UUID,
    manufacturer_in: Annotated[ManufacturerUpdate, Form()],
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.manufacturer_update))
    ],
):
    manufacturer = await manufacturer_service.update(
        db, manufacturer_id, manufacturer_in, current_user
    )
    response = HTMLResponse(content="")
    response.headers["HX-Redirect"] = f"/manufacturers/{manufacturer.id}"
    return response


@router.delete("/{manufacturer_id}", status_code=status.HTTP_200_OK)
async def delete_manufacturer(
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    manufacturer_id: UUID,
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.manufacturer_delete))
    ],
):
    return await manufacturer_service.delete(db, manufacturer_id)


@router.post("/{manufacturer_id}/activate", response_class=HTMLResponse)
async def activate_manufacturer(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    manufacturer_id: UUID,
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.manufacturer_update))
    ],
):
    manufacturer = await manufacturer_service.set_active_status(
        db, manufacturer_id, is_active=True
    )
    return templates.TemplateResponse(
        "manufacturers/manufacturer_rows.html",
        {"request": request, "manufacturers": [manufacturer]},
    )


@router.post("/{manufacturer_id}/deactivate", response_class=HTMLResponse)
async def deactivate_manufacturer(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    manufacturer_id: UUID,
    current_user: Annotated[
        User, Depends(require_permission(PermissionCode.manufacturer_update))
    ],
):
    manufacturer = await manufacturer_service.set_active_status(
        db, manufacturer_id, is_active=False
    )
    return templates.TemplateResponse(
        "manufacturers/manufacturer_rows.html",
        {"request": request, "manufacturers": [manufacturer]},
    )
