"""NIST control library routes."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.pagination import paginate
from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import CONTROL_READ, CONTROL_WRITE
from app.models.control import Control
from app.models.enums import ControlImplementationStatus
from app.models.user import User
from app.schemas.common import Page
from app.schemas.control import ControlCreate, ControlOut, ControlUpdate
from app.services.audit import record_audit

router = APIRouter(prefix="/controls", tags=["controls"])


@router.get("", response_model=Page[ControlOut])
def list_controls(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(CONTROL_READ)),
    search: str | None = None,
    family: str | None = None,
    implementation_status: ControlImplementationStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> Page:
    stmt = select(Control).where(Control.deleted_at.is_(None))
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            or_(
                Control.control_id.ilike(like),
                Control.title.ilike(like),
                Control.description.ilike(like),
                Control.family.ilike(like),
            )
        )
    if family:
        stmt = stmt.where(Control.family == family.upper())
    if implementation_status:
        stmt = stmt.where(Control.implementation_status == implementation_status)
    stmt = stmt.order_by(Control.control_id)
    return paginate(db, stmt, page, page_size, ControlOut.model_validate)


@router.get("/{control_pk}", response_model=ControlOut)
def get_control(
    control_pk: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(CONTROL_READ)),
) -> Control:
    control = db.get(Control, control_pk)
    if not control or control.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Control not found")
    return control


@router.post("", response_model=ControlOut, status_code=201)
def create_control(
    payload: ControlCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(CONTROL_WRITE)),
) -> Control:
    if db.scalar(select(Control).where(Control.control_id == payload.control_id)):
        raise HTTPException(status_code=409, detail="Control ID already exists")
    control = Control(**payload.model_dump())
    db.add(control)
    db.commit()
    db.refresh(control)
    record_audit(db, user=current, action="create", entity_type="control", entity_id=control.id)
    return control


@router.patch("/{control_pk}", response_model=ControlOut)
def update_control(
    control_pk: int,
    payload: ControlUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(CONTROL_WRITE)),
) -> Control:
    control = db.get(Control, control_pk)
    if not control or control.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Control not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(control, key, value)
    db.commit()
    db.refresh(control)
    record_audit(db, user=current, action="update", entity_type="control", entity_id=control.id)
    return control


@router.delete("/{control_pk}", status_code=204)
def delete_control(
    control_pk: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(CONTROL_WRITE)),
):
    control = db.get(Control, control_pk)
    if not control or control.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Control not found")
    control.deleted_at = datetime.now(timezone.utc)
    db.commit()
    record_audit(db, user=current, action="delete", entity_type="control", entity_id=control_pk)
