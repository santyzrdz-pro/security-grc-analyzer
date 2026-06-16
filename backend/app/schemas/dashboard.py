"""Dashboard and compliance schemas."""
from __future__ import annotations

from pydantic import BaseModel


class NameValue(BaseModel):
    name: str
    value: int


class TrendPoint(BaseModel):
    month: str
    count: int


class DashboardStats(BaseModel):
    total_assets: int
    open_findings: int
    critical_findings: int
    total_risks: int
    high_risks: int
    compliance_score: int


class DashboardResponse(BaseModel):
    stats: DashboardStats
    risk_distribution: list[NameValue]
    findings_by_severity: list[NameValue]
    controls_by_family: list[NameValue]
    remediation_progress: list[NameValue]
    monthly_findings_trend: list[TrendPoint]


class ComplianceResponse(BaseModel):
    total_controls: int
    implemented_controls: int
    partially_implemented: int
    not_implemented: int
    not_applicable: int
    compliance_percentage: int
    grade: str
    by_family: list[NameValue]
