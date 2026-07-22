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
)
from app.core.permissions import PermissionCode
from app.models.user import User
from app.schemas.base import QueryParams
from app.schemas.user import UserCreate, UserFilter, UserRole, UserUpdate
from app.services.user_service import user_service

router = APIRouter()


TempDpnds = Annotated[Jinja2Templates, Depends(get_template)]


@router.get("/", response_class=HTMLResponse)
async def list_users(
    request: Request,
    templates: TempDpnds,
    current_user: Annotated[User, Depends(require_permission(PermissionCode.user_read))],
    params: Annotated[QueryParams, Depends(get_query_params(UserFilter))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if params.filters.include_deleted and not current_user.is_super_user:
        raise HTTPException(status_code=403, detail="Only system admins can view deleted users")

    result = await user_service.list(request, db, params)

    context = {
        "request": request,
        "page": "users",
        "users": result.items,
        "search": params.filters.search,
        "user": current_user,
        "roles": [r.value for r in UserRole],
        "pagination": {
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "pages": result.pages,
            "links": result.links,
        },
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("users/user_list_content.html", context)

    return templates.TemplateResponse("users/users.html", context)


@router.get("/new", response_class=HTMLResponse)
async def new_user_form(
    request: Request,
    templates: TempDpnds,
    current_user: User = Depends(require_permission(PermissionCode.user_create)),
):
    return templates.TemplateResponse(
        "users/user_form.html",
        {
            "request": request,
            "user": current_user,
            "roles": [r.value for r in UserRole],
            "edit_user": None,
            "page": "users",
        },
    )


@router.post("/", response_class=HTMLResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    user_in: Annotated[UserCreate, Form()],
    current_user: Annotated[User, Depends(require_permission(PermissionCode.user_create))],
    db: Annotated[AsyncSession, Depends(get_audited_db)],
):
    await user_service.create(db, user_in, current_user)
    response = HTMLResponse(content="", status_code=status.HTTP_201_CREATED)
    response.headers["HX-Redirect"] = "/users"
    return response


@router.get("/{user_id}", response_class=HTMLResponse)
async def read_user(
    user_id: UUID,
    request: Request,
    templates: TempDpnds,
    current_user: User = Depends(require_permission(PermissionCode.user_read)),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.get_or_403(db, user_id, current_user)
    return templates.TemplateResponse(
        "users/user_detail.html",
        {
            "request": request,
            "user": current_user,
            "page": "users",
            "target_user": user,
        },
    )


@router.get("/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_form(
    user_id: UUID,
    request: Request,
    templates: TempDpnds,
    current_user: User = Depends(require_permission(PermissionCode.user_update)),
    db: AsyncSession = Depends(get_db),
):
    target_user = await user_service.get_or_403(db, user_id, current_user)
    return templates.TemplateResponse(
        "users/user_form.html",
        {
            "request": request,
            "user": current_user,
            "edit_user": target_user,
            "roles": [r.value for r in UserRole],
            "page": "users",
            "is_own_profile": current_user.id == user_id,
        },
    )


@router.put("/{user_id}", response_class=HTMLResponse)
async def update_user(
    user_id: UUID,
    update_data: Annotated[UserUpdate, Form()],
    current_user: User = Depends(require_permission(PermissionCode.user_update)),
    db: AsyncSession = Depends(get_audited_db),
):
    user = await user_service.update(db, user_id, update_data, current_user)
    response = HTMLResponse(content="")
    response.headers["HX-Redirect"] = f"/users/{user.id}"
    return response


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: UUID,
    current_user: User = Depends(require_permission(PermissionCode.user_activate)),
    db: AsyncSession = Depends(get_audited_db),
):
    await user_service.set_active_status(db, user_id, is_active=True)
    response = HTMLResponse("")
    response.headers["HX-Refresh"] = "true"
    return response


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(require_permission(PermissionCode.user_deactivate)),
    db: AsyncSession = Depends(get_audited_db),
):
    await user_service.set_active_status(db, user_id, is_active=False)
    response = HTMLResponse("")
    response.headers["HX-Refresh"] = "true"
    return response


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_audited_db)],
    current_user: Annotated[User, Depends(require_permission(PermissionCode.user_delete))],
):
    return await user_service.delete(db, user_id)
