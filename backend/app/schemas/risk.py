"""Risk register schemas."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import RiskLevel


class RiskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    mitigation_plan: str | None = None
    owner: str | None = None
    due_date: date | None = None
    asset_id: int | None = None
    finding_id: int | None = None


class RiskCreate(RiskBase):
    pass


class RiskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    likelihood: int | None = Field(default=None, ge=1, le=5)
    impact: int | None = Field(default=None, ge=1, le=5)
    mitigation_plan: str | None = None
    owner: str | None = None
    due_date: date | None = None
    asset_id: int | None = None


class RiskOut(RiskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    risk_score: int
    risk_level: RiskLevel
    asset_name: str | None = None


class GenerateRisksResult(BaseModel):
    created: int
    skipped: int
