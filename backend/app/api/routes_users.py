"""User management routes (Admin only)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import USER_MANAGE
from app.core.security import hash_password
from app.models.enums import RoleName
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import UserCreate, UserOut, UserUpdate
from app.services.audit import record_audit

router = APIRouter(prefix="/users", tags=["users"])


def _get_role(db: Session, name: str) -> Role:
    role = db.scalar(select(Role).where(Role.name == name))
    if not role:
        raise HTTPException(status_code=422, detail=f"Unknown role '{name}'")
    return role


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(USER_MANAGE)),
) -> list[User]:
    return list(db.scalars(select(User).where(User.deleted_at.is_(None))).all())


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(USER_MANAGE)),
) -> User:
    if db.scalar(select(User).where(User.email == payload.email.lower())):
        raise HTTPException(status_code=409, detail="Email already registered")
    valid_roles = {r.value for r in RoleName}
    if payload.role not in valid_roles:
        raise HTTPException(status_code=422, detail="Invalid role")
    role = _get_role(db, payload.role)
    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    record_audit(db, user=current, action="create", entity_type="user", entity_id=user.id)
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(USER_MANAGE)),
) -> User:
    user = db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.password is not None:
        user.hashed_password = hash_password(payload.password)
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.role is not None:
        user.role_id = _get_role(db, payload.role).id
    db.commit()
    db.refresh(user)
    record_audit(db, user=current, action="update", entity_type="user", entity_id=user.id)
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(USER_MANAGE)),
):
    user = db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    from datetime import datetime, timezone

    user.deleted_at = datetime.now(timezone.utc)
    user.is_active = False
    db.commit()
    record_audit(db, user=current, action="delete", entity_type="user", entity_id=user_id)
