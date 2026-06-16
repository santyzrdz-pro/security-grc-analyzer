"""Audit logging helper."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User


def record_audit(
    db: Session,
    *,
    user: User | None,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
    commit: bool = True,
) -> AuditLog:
    log = AuditLog(
        user_id=user.id if user else None,
        actor_email=user.email if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(log)
    if commit:
        db.commit()
    return log
