"""Risk register routes."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.pagination import paginate
from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import RISK_READ, RISK_WRITE
from app.models.enums import FindingStatus, RiskLevel
from app.models.finding import Finding
from app.models.risk import Risk
from app.models.user import User
from app.schemas.common import Page
from app.schemas.risk import (
    GenerateRisksResult,
    RiskCreate,
    RiskOut,
    RiskUpdate,
)
from app.services.audit import record_audit
from app.services.risk_engine import (
    compute_risk_score,
    derive_likelihood_impact,
    risk_level_for_score,
)

router = APIRouter(prefix="/risks", tags=["risks"])


def _serialize(risk: Risk) -> RiskOut:
    return RiskOut(
        id=risk.id,
        title=risk.title,
        description=risk.description,
        likelihood=risk.likelihood,
        impact=risk.impact,
        risk_score=risk.risk_score,
        risk_level=risk.risk_level,
        mitigation_plan=risk.mitigation_plan,
        owner=risk.owner,
        due_date=risk.due_date,
        asset_id=risk.asset_id,
        finding_id=risk.finding_id,
        asset_name=risk.asset.name if risk.asset else None,
    )


@router.get("", response_model=Page[RiskOut])
def list_risks(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(RISK_READ)),
    search: str | None = None,
    risk_level: RiskLevel | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Page:
    stmt = (
        select(Risk).where(Risk.deleted_at.is_(None)).options(selectinload(Risk.asset))
    )
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(Risk.title.ilike(like), Risk.description.ilike(like)))
    if risk_level:
        stmt = stmt.where(Risk.risk_level == risk_level)
    stmt = stmt.order_by(Risk.risk_score.desc(), Risk.id.desc())
    return paginate(db, stmt, page, page_size, _serialize)


@router.post("", response_model=RiskOut, status_code=201)
def create_risk(
    payload: RiskCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(RISK_WRITE)),
) -> RiskOut:
    score = compute_risk_score(payload.likelihood, payload.impact)
    risk = Risk(
        **payload.model_dump(),
        risk_score=score,
        risk_level=risk_level_for_score(score),
    )
    db.add(risk)
    db.commit()
    db.refresh(risk)
    record_audit(db, user=current, action="create", entity_type="risk", entity_id=risk.id)
    return _serialize(risk)


@router.patch("/{risk_id}", response_model=RiskOut)
def update_risk(
    risk_id: int,
    payload: RiskUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(RISK_WRITE)),
) -> RiskOut:
    risk = db.get(Risk, risk_id)
    if not risk or risk.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Risk not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(risk, key, value)
    risk.risk_score = compute_risk_score(risk.likelihood, risk.impact)
    risk.risk_level = risk_level_for_score(risk.risk_score)
    db.commit()
    db.refresh(risk)
    record_audit(db, user=current, action="update", entity_type="risk", entity_id=risk.id)
    return _serialize(risk)


@router.delete("/{risk_id}", status_code=204)
def delete_risk(
    risk_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(RISK_WRITE)),
):
    risk = db.get(Risk, risk_id)
    if not risk or risk.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Risk not found")
    risk.deleted_at = datetime.now(timezone.utc)
    db.commit()
    record_audit(db, user=current, action="delete", entity_type="risk", entity_id=risk_id)


@router.post("/generate-from-findings", response_model=GenerateRisksResult)
def generate_from_findings(
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(RISK_WRITE)),
) -> GenerateRisksResult:
    """Auto-create risk register entries for open/in-progress findings."""
    findings = list(
        db.scalars(
            select(Finding)
            .where(
                Finding.deleted_at.is_(None),
                Finding.status.in_([FindingStatus.OPEN, FindingStatus.IN_PROGRESS]),
            )
            .options(selectinload(Finding.asset))
        ).all()
    )
    existing = {
        r.finding_id
        for r in db.scalars(
            select(Risk).where(Risk.deleted_at.is_(None), Risk.finding_id.is_not(None))
        ).all()
    }
    created, skipped = 0, 0
    for finding in findings:
        if finding.id in existing:
            skipped += 1
            continue
        criticality = finding.asset.criticality if finding.asset else None
        likelihood, impact = derive_likelihood_impact(finding.severity, criticality)
        score = compute_risk_score(likelihood, impact)
        risk = Risk(
            title=f"Risk: {finding.title}",
            description=finding.description
            or f"Auto-generated from finding '{finding.title}'.",
            likelihood=likelihood,
            impact=impact,
            risk_score=score,
            risk_level=risk_level_for_score(score),
            mitigation_plan=finding.ai_recommended_remediation,
            owner=finding.asset.owner if finding.asset else None,
            asset_id=finding.asset_id,
            finding_id=finding.id,
        )
        db.add(risk)
        created += 1
    db.commit()
    record_audit(
        db, user=current, action="generate", entity_type="risk", detail=f"created={created}"
    )
    return GenerateRisksResult(created=created, skipped=skipped)
