from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_query_params, get_template, require_user
from app.models.user import User
from app.schemas.activity import ActivityLogFilter
from app.schemas.base import QueryParams
from app.services.activity import activity_service
from app.services.user import user_service

router = APIRouter()

TempDpnds = Annotated[Jinja2Templates, Depends(get_template)]


@router.get("/", response_class=HTMLResponse)
async def get_activity_list(
    request: Request,
    templates: TempDpnds,
    db: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[QueryParams, Depends(get_query_params(ActivityLogFilter))],
    current_user: User = Depends(require_user),
):
    context = await activity_service.get_activity_list(request, db, params)
    entity_types = {activity.entity_type for activity in context.items}
    results = await user_service.list_for_view(db)
    users = {user.id: user for user in results}

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "activity/activity_rows.html",
            {"request": request, "paginated_result": context, "users": users},
        )

    return templates.TemplateResponse(
        "activity/activity.html",
        {
            "request": request,
            "page": "activity",
            "user": current_user,
            "paginated_result": context,
            "users": users,
            "action_filter": params.filters.action,
            "entity_types": entity_types,
        },
    )
