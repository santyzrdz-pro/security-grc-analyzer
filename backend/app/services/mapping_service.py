"""Persist mapping engine results as finding<->control links."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.control import Control
from app.models.finding import Finding
from app.models.finding_control import FindingControl
from app.services.mapping_engine import map_finding


def apply_mapping_to_finding(db: Session, finding: Finding, replace: bool = True) -> int:
    """Run the mapping engine on a finding and persist control links.

    Returns the number of control links created.
    """
    text = f"{finding.title} {finding.description or ''}"
    result = map_finding(text)

    if replace:
        for link in list(finding.control_links):
            db.delete(link)
        db.flush()

    created = 0
    for match in result.matches:
        control = db.scalar(
            select(Control).where(Control.control_id == match.control_id)
        )
        if control is None:
            continue
        link = FindingControl(
            finding_id=finding.id,
            control_id=control.id,
            confidence=match.confidence,
            method=match.method,
            rationale=match.rationale,
        )
        db.add(link)
        created += 1
    db.flush()
    return created
