from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token, verify_password
from app.core.config import settings
from app.core.dependencies import get_current_user, get_db, get_template
from app.models.activity import ActivityLog
from app.models.user import User

router = APIRouter()

TempDpnds = Annotated[Jinja2Templates, Depends(get_template)]


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    templates: TempDpnds,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "app_name": settings.APP_NAME,
        },
    )


@router.post("/login")
async def login(
    request: Request,
    templates: TempDpnds,
    email: str = Form(...),
    password: str = Form(...),
    remember: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.email == email, User.is_active.is_not(False))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": "Invalid email or password",
                "email": email,
                "app_name": settings.APP_NAME,
            },
            status_code=401,
        )

    user.last_login = datetime.utcnow()
    db.add(
        ActivityLog(
            user_id=user.id,
            action="login",
            entity_type="user",
            entity_id=user.id,
            ip_address=request.client.host if request.client else None,
        )
    )
    await db.commit()

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30 if remember else None,
    )
    return response


@router.post("/logout")
def logout():
    resp = Response(status_code=200)
    resp.delete_cookie("access_token", path="/")
    resp.headers["HX-Redirect"] = "/auth/login"
    return resp
