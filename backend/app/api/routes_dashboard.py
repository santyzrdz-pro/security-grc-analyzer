"""Executive dashboard and compliance routes."""
from __future__ import annotations

from collections import Counter, OrderedDict
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import DASHBOARD_READ
from app.models.asset import Asset
from app.models.control import Control
from app.models.enums import (
    FindingStatus,
    RemediationStatus,
    RiskLevel,
    Severity,
)
from app.models.finding import Finding
from app.models.remediation import Remediation
from app.models.risk import Risk
from app.models.user import User
from app.schemas.dashboard import (
    ComplianceResponse,
    DashboardResponse,
    DashboardStats,
    NameValue,
    TrendPoint,
)
from app.services.compliance import compute_compliance

router = APIRouter(tags=["dashboard"])


def _count(db: Session, model, *conditions) -> int:
    stmt = select(func.count(model.id)).where(model.deleted_at.is_(None), *conditions)
    return db.scalar(stmt) or 0


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(DASHBOARD_READ)),
) -> DashboardResponse:
    compliance = compute_compliance(db)

    stats = DashboardStats(
        total_assets=_count(db, Asset),
        open_findings=_count(db, Finding, Finding.status == FindingStatus.OPEN),
        critical_findings=_count(db, Finding, Finding.severity == Severity.CRITICAL),
        total_risks=_count(db, Risk),
        high_risks=_count(
            db, Risk, Risk.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])
        ),
        compliance_score=compliance.compliance_percentage,
    )

    # Risk distribution by level
    risk_counter: Counter[str] = Counter()
    for level in db.scalars(select(Risk.risk_level).where(Risk.deleted_at.is_(None))).all():
        risk_counter[level.value] += 1
    risk_distribution = [
        NameValue(name=lvl.value, value=risk_counter.get(lvl.value, 0))
        for lvl in RiskLevel
    ]

    # Findings by severity
    sev_counter: Counter[str] = Counter()
    for sev in db.scalars(select(Finding.severity).where(Finding.deleted_at.is_(None))).all():
        sev_counter[sev.value] += 1
    findings_by_severity = [
        NameValue(name=s.value, value=sev_counter.get(s.value, 0)) for s in Severity
    ]

    # Controls by family
    fam_counter: Counter[str] = Counter()
    for fam in db.scalars(select(Control.family).where(Control.deleted_at.is_(None))).all():
        fam_counter[fam] += 1
    controls_by_family = [
        NameValue(name=fam, value=count) for fam, count in sorted(fam_counter.items())
    ]

    # Remediation progress by status
    rem_counter: Counter[str] = Counter()
    for st in db.scalars(
        select(Remediation.status).where(Remediation.deleted_at.is_(None))
    ).all():
        rem_counter[st.value] += 1
    remediation_progress = [
        NameValue(name=st.value, value=rem_counter.get(st.value, 0))
        for st in RemediationStatus
    ]

    # Monthly findings trend (last 6 months)
    months: "OrderedDict[str, int]" = OrderedDict()
    today = date.today()
    for i in range(5, -1, -1):
        m = (today.month - i - 1) % 12 + 1
        y = today.year + ((today.month - i - 1) // 12)
        key = f"{y:04d}-{m:02d}"
        months[key] = 0
    for d in db.scalars(
        select(Finding.detection_date).where(
            Finding.deleted_at.is_(None), Finding.detection_date.is_not(None)
        )
    ).all():
        key = f"{d.year:04d}-{d.month:02d}"
        if key in months:
            months[key] += 1
    monthly_trend = [TrendPoint(month=k, count=v) for k, v in months.items()]

    return DashboardResponse(
        stats=stats,
        risk_distribution=risk_distribution,
        findings_by_severity=findings_by_severity,
        controls_by_family=controls_by_family,
        remediation_progress=remediation_progress,
        monthly_findings_trend=monthly_trend,
    )


@router.get("/compliance", response_model=ComplianceResponse, tags=["compliance"])
def get_compliance(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(DASHBOARD_READ)),
) -> ComplianceResponse:
    return compute_compliance(db)
