from typing import Annotated

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import register_audit_listener
from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.core.exceptions import (
    AuthenticationError,
    InsufficientPermissionError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from app.core.pagination import PaginationParams
from app.core.permissions import PermissionCode
from app.core.security import decode_token
from app.models import User, UserPermission
from app.schemas.base import QueryParams
from app.services.permission_service import permission_service


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    user_id = decode_token(token)
    return await db.scalar(select(User).where(User.id == user_id, User.is_active.is_(True)))


async def get_current_user_with_permissions(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    token = request.cookies.get(
        "access_token",
    )
    if not token:
        raise InvalidTokenError
    user_id = decode_token(token)
    result = await db.execute(
        select(User)
        .options(selectinload(User.permission_links).selectinload(UserPermission.permission))
        .where(User.id == user_id, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise InvalidCredentialsError()
    return user


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
        raise AuthenticationError
    return user


def require_permission(permission_code: PermissionCode):
    async def checker(
        current_user: Annotated[User, Depends(get_current_user_with_permissions)],
    ) -> User:
        if not permission_service.user_has_permission(current_user, permission_code):
            raise InsufficientPermissionError()
        return current_user

    return checker


def get_query_params(filter_cls: type[BaseModel]):
    def dependency(
        pagination: Annotated[PaginationParams, Depends()],
        filters=Depends(filter_cls),
    ) -> QueryParams:
        return QueryParams(pagination=pagination, filters=filters)

    return dependency
