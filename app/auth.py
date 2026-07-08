from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.config import settings
from app.models.user import User
from app.schemas.user import UserRole

pwd_context = PasswordHash.recommended()

ROLE_PERMISSIONS = {
    UserRole.admin: {
        "users": ["read", "write", "delete"],
        "vehicles": ["read", "write", "delete"],
        "contracts": ["read", "write", "delete"],
        "insurance": ["read", "write", "delete"],
        "fuel": ["read", "write", "delete"],
        "maintenance": ["read", "write", "delete"],
        "reports": ["read"],
        "settings": ["read", "write"],
        "alerts": ["read", "write", "delete"],
        "inventory": ["read", "write", "delete"],
        "manufacturers": ["read", "write", "delete"],
    },
    UserRole.fleet_manager: {
        "users": ["read"],
        "vehicles": ["read", "write"],
        "contracts": ["read", "write"],
        "insurance": ["read", "write"],
        "fuel": ["read", "write"],
        "maintenance": ["read", "write"],
        "reports": ["read"],
        "settings": ["read"],
        "alerts": ["read", "write"],
        "inventory": ["read"],
        "manufacturers": ["read", "write"],
    },
    UserRole.maintenance_manager: {
        "users": [],
        "vehicles": ["read"],
        "contracts": ["read"],
        "insurance": ["read"],
        "fuel": ["read"],
        "maintenance": ["read", "write"],
        "reports": ["read"],
        "settings": [],
        "alerts": ["read", "write"],
        "inventory": ["read", "write", "delete"],
        "manufacturers": ["read"],
    },
    UserRole.driver: {
        "vehicles": ["read"],
        "contracts": ["read"],
        "insurance": ["read"],
        "fuel": ["read", "write"],
        "maintenance": ["read"],
        "reports": [],
        "settings": [],
        "alerts": ["read"],
        "inventory": ["read"],
    },
    UserRole.viewer: {
        "vehicles": ["read"],
        "contracts": ["read"],
        "insurance": ["read"],
        "fuel": ["read"],
        "maintenance": ["read"],
        "reports": ["read"],
        "settings": [],
        "alerts": ["read"],
        "inventory": ["read"],
        "manufacturers": ["read"],
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def has_permission(user: User, resource: str, action: str) -> bool:
    perms = ROLE_PERMISSIONS.get(UserRole(user.role), {})
    return action in perms.get(resource, [])
