"""Remediation tracking routes (Kanban board)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import REMEDIATION_READ, REMEDIATION_WRITE
from app.models.remediation import Remediation
from app.models.user import User
from app.schemas.remediation import (
    RemediationCreate,
    RemediationOut,
    RemediationUpdate,
)
from app.services.audit import record_audit

router = APIRouter(prefix="/remediations", tags=["remediations"])


@router.get("", response_model=list[RemediationOut])
def list_remediations(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(REMEDIATION_READ)),
) -> list[Remediation]:
    return list(
        db.scalars(
            select(Remediation)
            .where(Remediation.deleted_at.is_(None))
            .order_by(Remediation.due_date.asc().nullslast())
        ).all()
    )


@router.post("", response_model=RemediationOut, status_code=201)
def create_remediation(
    payload: RemediationCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(REMEDIATION_WRITE)),
) -> Remediation:
    rem = Remediation(**payload.model_dump())
    db.add(rem)
    db.commit()
    db.refresh(rem)
    record_audit(db, user=current, action="create", entity_type="remediation", entity_id=rem.id)
    return rem


@router.patch("/{rem_id}", response_model=RemediationOut)
def update_remediation(
    rem_id: int,
    payload: RemediationUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(REMEDIATION_WRITE)),
) -> Remediation:
    rem = db.get(Remediation, rem_id)
    if not rem or rem.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Remediation not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rem, key, value)
    db.commit()
    db.refresh(rem)
    record_audit(db, user=current, action="update", entity_type="remediation", entity_id=rem.id)
    return rem


@router.delete("/{rem_id}", status_code=204)
def delete_remediation(
    rem_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(REMEDIATION_WRITE)),
):
    rem = db.get(Remediation, rem_id)
    if not rem or rem.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Remediation not found")
    rem.deleted_at = datetime.now(timezone.utc)
    db.commit()
    record_audit(db, user=current, action="delete", entity_type="remediation", entity_id=rem_id)
