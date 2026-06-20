"""FastAPI dependencies for auth and RBAC."""
from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.permissions import role_has_permission
from app.core.security import decode_token
from app.models.enums import RoleName
from app.models.role import Role
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=settings.AUTH_ENABLED,
)

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def _system_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.email == settings.ADMIN_EMAIL.lower()))
    if user is None:
        user = db.scalar(
            select(User)
            .join(Role)
            .where(Role.name == RoleName.ADMIN.value, User.deleted_at.is_(None))
            .limit(1)
        )
    if user is None or not user.is_active or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System user not initialized. Restart the backend to run seed.",
        )
    return user


def get_current_user(
    db: Session = Depends(get_db),
    token: str | None = Depends(oauth2_scheme),
) -> User:
    if not settings.AUTH_ENABLED:
        return _system_user(db)

    if token is None:
        raise credentials_exception

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exception
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user = db.get(User, int(user_id))
    if user is None or not user.is_active or user.deleted_at is not None:
        raise credentials_exception
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_permission(permission: str) -> Callable[[User], User]:
    """Dependency factory enforcing a capability based on the user's role."""

    def checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not settings.AUTH_ENABLED:
            return current_user

        role_name = current_user.role.name if current_user.role else ""
        if not role_has_permission(role_name, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_name}' lacks permission '{permission}'",
            )
        return current_user

    return checker
