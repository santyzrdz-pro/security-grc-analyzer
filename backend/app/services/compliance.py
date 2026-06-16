"""Compliance scoring engine."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.control import Control
from app.models.enums import ControlImplementationStatus
from app.schemas.dashboard import ComplianceResponse, NameValue

# Partial credit weights for the compliance percentage.
_STATUS_WEIGHT = {
    ControlImplementationStatus.IMPLEMENTED: 1.0,
    ControlImplementationStatus.PARTIALLY_IMPLEMENTED: 0.5,
    ControlImplementationStatus.PLANNED: 0.25,
    ControlImplementationStatus.NOT_IMPLEMENTED: 0.0,
}


def grade_for_percentage(pct: int) -> str:
    if pct >= 90:
        return "A"
    if pct >= 80:
        return "B"
    if pct >= 70:
        return "C"
    if pct >= 60:
        return "D"
    return "F"


def compute_compliance(db: Session) -> ComplianceResponse:
    controls = list(
        db.scalars(select(Control).where(Control.deleted_at.is_(None))).all()
    )

    # Controls marked Not Applicable are excluded from scoring.
    applicable = [
        c
        for c in controls
        if c.implementation_status != ControlImplementationStatus.NOT_APPLICABLE
    ]

    total = len(applicable)
    implemented = sum(
        1
        for c in applicable
        if c.implementation_status == ControlImplementationStatus.IMPLEMENTED
    )
    partial = sum(
        1
        for c in applicable
        if c.implementation_status
        == ControlImplementationStatus.PARTIALLY_IMPLEMENTED
    )
    not_impl = sum(
        1
        for c in applicable
        if c.implementation_status == ControlImplementationStatus.NOT_IMPLEMENTED
    )
    not_applicable = sum(
        1
        for c in controls
        if c.implementation_status == ControlImplementationStatus.NOT_APPLICABLE
    )

    if total > 0:
        weighted = sum(_STATUS_WEIGHT.get(c.implementation_status, 0.0) for c in applicable)
        pct = round((weighted / total) * 100)
    else:
        pct = 0

    family_totals: dict[str, list[int]] = {}
    for c in applicable:
        bucket = family_totals.setdefault(c.family, [0, 0])
        bucket[1] += 1
        if c.implementation_status == ControlImplementationStatus.IMPLEMENTED:
            bucket[0] += 1
    by_family = [
        NameValue(name=fam, value=round((vals[0] / vals[1]) * 100) if vals[1] else 0)
        for fam, vals in sorted(family_totals.items())
    ]

    return ComplianceResponse(
        total_controls=total,
        implemented_controls=implemented,
        partially_implemented=partial,
        not_implemented=not_impl,
        not_applicable=not_applicable,
        compliance_percentage=pct,
        grade=grade_for_percentage(pct),
        by_family=by_family,
    )
