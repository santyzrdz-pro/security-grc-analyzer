"""Report generation and audit log routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import AUDIT_READ, REPORT_READ, REPORT_WRITE
from app.models.audit_log import AuditLog
from app.models.report import Report
from app.models.user import User
from app.schemas.report import AuditLogOut, ReportOut
from app.services.audit import record_audit
from app.services.compliance import compute_compliance
from app.services.report_generator import generate_audit_report

router = APIRouter(tags=["reports"])


@router.get("/reports", response_model=list[ReportOut])
def list_reports(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(REPORT_READ)),
) -> list[Report]:
    return list(
        db.scalars(
            select(Report)
            .where(Report.deleted_at.is_(None))
            .order_by(Report.created_at.desc())
        ).all()
    )


@router.post("/reports", response_class=Response)
def generate_report(
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(REPORT_WRITE)),
) -> Response:
    """Generate an audit-ready PDF and record report metadata."""
    compliance = compute_compliance(db)
    pdf_bytes = generate_audit_report(db, generated_by=current.full_name)

    report = Report(
        title="Security Compliance & Risk Audit Report",
        report_type="Audit",
        summary=f"Compliance {compliance.compliance_percentage}% (Grade {compliance.grade})",
        compliance_score=compliance.compliance_percentage,
        generated_by_id=current.id,
    )
    db.add(report)
    db.commit()
    record_audit(db, user=current, action="generate", entity_type="report", entity_id=report.id)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="security-grc-audit-report.pdf"'
        },
    )


@router.get("/audit-logs", response_model=list[AuditLogOut])
def list_audit_logs(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(AUDIT_READ)),
    limit: int = Query(100, ge=1, le=500),
) -> list[AuditLog]:
    return list(
        db.scalars(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        ).all()
    )
