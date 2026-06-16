"""Authentication routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.permissions import ROLE_PERMISSIONS
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import Token, UserWithPermissions
from app.services.audit import record_audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = db.scalar(select(User).where(User.email == form_data.username.lower()))
    if not user or not verify_password(form_data.password, user.hashed_password):
        record_audit(
            db,
            user=None,
            action="login_failed",
            entity_type="user",
            detail=f"Failed login for {form_data.username}",
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    token = create_access_token(subject=user.id, role=user.role.name)
    record_audit(
        db,
        user=user,
        action="login",
        entity_type="user",
        entity_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return Token(access_token=token)


def _permissions_for(role_name: str) -> list[str]:
    perms = ROLE_PERMISSIONS.get(role_name, set())
    return sorted(perms)


@router.get("/me", response_model=UserWithPermissions)
def read_me(current_user: User = Depends(get_current_active_user)) -> UserWithPermissions:
    return UserWithPermissions(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        role=current_user.role,
        permissions=_permissions_for(current_user.role.name),
    )
