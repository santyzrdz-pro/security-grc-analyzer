"""Report schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    report_type: str
    summary: str | None = None
    compliance_score: int | None = None
    created_at: datetime


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_email: str | None = None
    action: str
    entity_type: str | None = None
    entity_id: int | None = None
    detail: str | None = None
    ip_address: str | None = None
    created_at: datetime
