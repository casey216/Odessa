from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
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
