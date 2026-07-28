from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_permission
from app.core.permissions import PermissionCode
from app.models import User
from app.models.permission import PermissionEffect
from app.services.permission_service import permission_service

router = APIRouter(prefix="/users/{user_id}/permissions", tags=["permissions"])


class PermissionCodeRequest(BaseModel):
    permission_code: PermissionCode


@router.post("/grant", status_code=status.HTTP_200_OK)
async def grant_permission(
    user_id: UUID,
    body: Annotated[PermissionCodeRequest, Form()],
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_permission(PermissionCode.permission_grant)),
) -> None:
    await permission_service.set_permission_override(
        db, user_id, body.permission_code, PermissionEffect.allow
    )


@router.post("/deny", status_code=status.HTTP_200_OK)
async def deny_permission(
    user_id: UUID,
    body: Annotated[PermissionCodeRequest, Form()],
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_permission(PermissionCode.permission_grant)),
) -> None:
    await permission_service.set_permission_override(
        db, user_id, body.permission_code, PermissionEffect.deny
    )


@router.post("/revoke/", status_code=status.HTTP_200_OK)
async def revoke_permission(
    user_id: UUID,
    body: Annotated[PermissionCodeRequest, Form()],
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_permission(PermissionCode.permission_revoke)),
) -> None:
    await permission_service.revoke_permission_override(db, user_id, body.permission_code)
