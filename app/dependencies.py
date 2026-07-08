from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import decode_token, has_permission
from app.core.audit import register_audit_listener
from app.core.context import RequestContext
from app.core.pagination import PaginationParams
from app.database import AsyncSessionLocal
from app.models.user import User
from app.schemas.base import QueryParams
from app.schemas.user import UserRole


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active.is_(True))
    )
    return result.scalar_one_or_none()


def get_request_context(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> RequestContext:
    return RequestContext(
        current_user=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


def get_template(request: Request) -> Jinja2Templates:
    return request.app.state.templates


async def get_audited_db(ctx: RequestContext = Depends(get_request_context)):
    async with AsyncSessionLocal() as session:
        register_audit_listener(session, ctx)
        try:
            yield session
        finally:
            await session.close()


async def require_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    user = await get_current_user(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND, headers={"Location": "/auth/login"}
        )
    return user


def require_role(*roles: UserRole):
    async def checker(request: Request, db: AsyncSession = Depends(get_db)) -> User:
        user = await get_current_user(request, db)
        if not user:
            raise HTTPException(status_code=302, headers={"Location": "/auth/login"})
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return checker


def require_permission(resource: str, action: str):
    async def checker(
        request: Request, db: AsyncSession = Depends(get_audited_db)
    ) -> User:
        user = await get_current_user(request, db)
        if not user:
            raise HTTPException(status_code=302, headers={"Location": "/auth/login"})
        if not has_permission(user, resource, action):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return checker


def get_query_params(filter_cls: type[BaseModel]):
    def dependency(
        pagination: Annotated[PaginationParams, Depends()],
        filters=Depends(filter_cls),
    ) -> QueryParams:
        return QueryParams(pagination=pagination, filters=filters)

    return dependency
