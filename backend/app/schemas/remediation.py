"""Remediation schemas."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RemediationStatus, Severity


class RemediationBase(BaseModel):
    task: str = Field(min_length=1, max_length=255)
    description: str | None = None
    owner: str | None = None
    status: RemediationStatus = RemediationStatus.NOT_STARTED
    priority: Severity = Severity.MEDIUM
    due_date: date | None = None
    finding_id: int | None = None
    risk_id: int | None = None


class RemediationCreate(RemediationBase):
    pass


class RemediationUpdate(BaseModel):
    task: str | None = None
    description: str | None = None
    owner: str | None = None
    status: RemediationStatus | None = None
    priority: Severity | None = None
    due_date: date | None = None


class RemediationOut(RemediationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
