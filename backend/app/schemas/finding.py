"""Finding schemas."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FindingStatus, Severity
from app.schemas.control import ControlOut


class FindingBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    severity: Severity
    status: FindingStatus = FindingStatus.OPEN
    detection_date: date | None = None
    source: str | None = None
    evidence: str | None = None
    cve: str | None = None
    asset_id: int | None = None


class FindingCreate(FindingBase):
    pass


class FindingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: Severity | None = None
    status: FindingStatus | None = None
    detection_date: date | None = None
    source: str | None = None
    evidence: str | None = None
    cve: str | None = None
    asset_id: int | None = None


class MappedControl(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    control: ControlOut
    confidence: int
    method: str | None = None
    rationale: str | None = None


class AIAnalysis(BaseModel):
    executive_summary: str | None = None
    business_impact: str | None = None
    technical_explanation: str | None = None
    recommended_remediation: str | None = None


class FindingOut(FindingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_name: str | None = None
    mapped_controls: list[MappedControl] = []
    ai_analysis: AIAnalysis | None = None


class CSVImportResult(BaseModel):
    imported: int
    failed: int
    errors: list[str] = []
