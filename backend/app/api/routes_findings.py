"""Findings management routes (incl. CSV/JSON import, mapping, AI analysis)."""
from __future__ import annotations

import csv
import io
import json
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.pagination import paginate
from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import FINDING_READ, FINDING_WRITE
from app.models.asset import Asset
from app.models.enums import FindingStatus, Severity
from app.models.finding import Finding
from app.models.finding_control import FindingControl
from app.models.user import User
from app.schemas.common import Page
from app.schemas.finding import (
    AIAnalysis,
    CSVImportResult,
    FindingCreate,
    FindingOut,
    FindingUpdate,
    MappedControl,
)
from app.services.ai_analyst import analyze_finding
from app.services.audit import record_audit
from app.services.mapping_service import apply_mapping_to_finding

router = APIRouter(prefix="/findings", tags=["findings"])


def _serialize(finding: Finding) -> FindingOut:
    mapped = [
        MappedControl(
            control=link.control,
            confidence=link.confidence,
            method=link.method,
            rationale=link.rationale,
        )
        for link in sorted(
            finding.control_links, key=lambda link: link.confidence, reverse=True
        )
    ]
    ai = None
    if any(
        [
            finding.ai_executive_summary,
            finding.ai_business_impact,
            finding.ai_technical_explanation,
            finding.ai_recommended_remediation,
        ]
    ):
        ai = AIAnalysis(
            executive_summary=finding.ai_executive_summary,
            business_impact=finding.ai_business_impact,
            technical_explanation=finding.ai_technical_explanation,
            recommended_remediation=finding.ai_recommended_remediation,
        )
    return FindingOut(
        id=finding.id,
        title=finding.title,
        description=finding.description,
        severity=finding.severity,
        status=finding.status,
        detection_date=finding.detection_date,
        source=finding.source,
        evidence=finding.evidence,
        cve=finding.cve,
        asset_id=finding.asset_id,
        asset_name=finding.asset.name if finding.asset else None,
        mapped_controls=mapped,
        ai_analysis=ai,
    )


def _load_finding(db: Session, finding_id: int) -> Finding:
    finding = db.scalar(
        select(Finding)
        .where(Finding.id == finding_id, Finding.deleted_at.is_(None))
        .options(
            selectinload(Finding.control_links).selectinload(FindingControl.control),
            selectinload(Finding.asset),
        )
    )
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding


@router.get("", response_model=Page[FindingOut])
def list_findings(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(FINDING_READ)),
    search: str | None = None,
    severity: Severity | None = None,
    status: FindingStatus | None = None,
    asset_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Page:
    stmt = (
        select(Finding)
        .where(Finding.deleted_at.is_(None))
        .options(
            selectinload(Finding.control_links).selectinload(FindingControl.control),
            selectinload(Finding.asset),
        )
    )
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            or_(
                Finding.title.ilike(like),
                Finding.description.ilike(like),
                Finding.cve.ilike(like),
                Finding.source.ilike(like),
            )
        )
    if severity:
        stmt = stmt.where(Finding.severity == severity)
    if status:
        stmt = stmt.where(Finding.status == status)
    if asset_id:
        stmt = stmt.where(Finding.asset_id == asset_id)
    stmt = stmt.order_by(Finding.detection_date.desc().nullslast(), Finding.id.desc())
    return paginate(db, stmt, page, page_size, _serialize)


@router.get("/{finding_id}", response_model=FindingOut)
def get_finding(
    finding_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(FINDING_READ)),
) -> FindingOut:
    return _serialize(_load_finding(db, finding_id))


def _create_finding(db: Session, payload: FindingCreate, run_ai: bool = True) -> Finding:
    finding = Finding(**payload.model_dump())
    db.add(finding)
    db.flush()
    apply_mapping_to_finding(db, finding)
    if run_ai:
        ai = analyze_finding(finding.title, finding.description, finding.severity)
        finding.ai_executive_summary = ai.get("executive_summary")
        finding.ai_business_impact = ai.get("business_impact")
        finding.ai_technical_explanation = ai.get("technical_explanation")
        finding.ai_recommended_remediation = ai.get("recommended_remediation")
    db.commit()
    return _load_finding(db, finding.id)


@router.post("", response_model=FindingOut, status_code=201)
def create_finding(
    payload: FindingCreate,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(FINDING_WRITE)),
) -> FindingOut:
    finding = _create_finding(db, payload)
    record_audit(
        db,
        user=current,
        action="create",
        entity_type="finding",
        entity_id=finding.id,
        detail=finding.title,
        ip_address=request.client.host if request.client else None,
    )
    return _serialize(finding)


@router.patch("/{finding_id}", response_model=FindingOut)
def update_finding(
    finding_id: int,
    payload: FindingUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(FINDING_WRITE)),
) -> FindingOut:
    finding = _load_finding(db, finding_id)
    data = payload.model_dump(exclude_unset=True)
    remap = "title" in data or "description" in data
    for key, value in data.items():
        setattr(finding, key, value)
    if remap:
        apply_mapping_to_finding(db, finding)
    db.commit()
    record_audit(db, user=current, action="update", entity_type="finding", entity_id=finding.id)
    return _serialize(_load_finding(db, finding_id))


@router.delete("/{finding_id}", status_code=204)
def delete_finding(
    finding_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(FINDING_WRITE)),
):
    finding = _load_finding(db, finding_id)
    finding.deleted_at = datetime.now(timezone.utc)
    db.commit()
    record_audit(db, user=current, action="delete", entity_type="finding", entity_id=finding_id)


@router.post("/{finding_id}/remap", response_model=FindingOut)
def remap_finding(
    finding_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(FINDING_WRITE)),
) -> FindingOut:
    finding = _load_finding(db, finding_id)
    apply_mapping_to_finding(db, finding)
    db.commit()
    record_audit(db, user=current, action="remap", entity_type="finding", entity_id=finding_id)
    return _serialize(_load_finding(db, finding_id))


@router.post("/{finding_id}/analyze", response_model=FindingOut)
def analyze(
    finding_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(FINDING_WRITE)),
) -> FindingOut:
    finding = _load_finding(db, finding_id)
    ai = analyze_finding(finding.title, finding.description, finding.severity)
    finding.ai_executive_summary = ai.get("executive_summary")
    finding.ai_business_impact = ai.get("business_impact")
    finding.ai_technical_explanation = ai.get("technical_explanation")
    finding.ai_recommended_remediation = ai.get("recommended_remediation")
    db.commit()
    record_audit(db, user=current, action="ai_analyze", entity_type="finding", entity_id=finding_id)
    return _serialize(_load_finding(db, finding_id))


# ---- Imports ----

def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _coerce_enum(enum_cls, value, default):
    if value is None:
        return default
    value = str(value).strip()
    for member in enum_cls:
        if member.value.lower() == value.lower() or member.name.lower() == value.lower():
            return member
    return default


def _import_rows(db: Session, rows: list[dict], current: User) -> CSVImportResult:
    imported, failed = 0, 0
    errors: list[str] = []
    for idx, row in enumerate(rows, start=1):
        try:
            title = (row.get("title") or row.get("Title") or "").strip()
            if not title:
                failed += 1
                errors.append(f"Row {idx}: missing title")
                continue
            severity = _coerce_enum(
                Severity, row.get("severity") or row.get("Severity"), Severity.MEDIUM
            )
            status = _coerce_enum(
                FindingStatus, row.get("status") or row.get("Status"), FindingStatus.OPEN
            )
            asset_id = None
            asset_name = row.get("asset") or row.get("Asset") or row.get("asset_name")
            if asset_name:
                asset = db.scalar(
                    select(Asset).where(Asset.name.ilike(str(asset_name).strip()))
                )
                asset_id = asset.id if asset else None
            payload = FindingCreate(
                title=title,
                description=row.get("description") or row.get("Description"),
                severity=severity,
                status=status,
                detection_date=_parse_date(row.get("detection_date") or row.get("Detection Date")),
                source=row.get("source") or row.get("Source"),
                evidence=row.get("evidence") or row.get("Evidence"),
                cve=row.get("cve") or row.get("CVE"),
                asset_id=asset_id,
            )
            _create_finding(db, payload, run_ai=False)
            imported += 1
        except Exception as exc:  # noqa: BLE001
            failed += 1
            errors.append(f"Row {idx}: {exc}")
    record_audit(
        db, user=current, action="import", entity_type="finding", detail=f"imported={imported}"
    )
    return CSVImportResult(imported=imported, failed=failed, errors=errors[:25])


@router.post("/import/csv", response_model=CSVImportResult)
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(FINDING_WRITE)),
) -> CSVImportResult:
    content = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    return _import_rows(db, rows, current)


@router.post("/import/json", response_model=CSVImportResult)
async def import_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(FINDING_WRITE)),
) -> CSVImportResult:
    content = (await file.read()).decode("utf-8-sig")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid JSON: {exc}") from exc
    if isinstance(data, dict):
        data = data.get("findings", [])
    if not isinstance(data, list):
        raise HTTPException(status_code=422, detail="JSON must be a list of findings")
    return _import_rows(db, data, current)
