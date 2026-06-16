"""Risk scoring engine.

Risk Score = Likelihood x Impact (each on a 1-5 scale), producing a 1-25 score
that maps to a qualitative risk level.
"""
from __future__ import annotations

from app.models.enums import Criticality, RiskLevel, Severity


def compute_risk_score(likelihood: int, impact: int) -> int:
    likelihood = max(1, min(5, likelihood))
    impact = max(1, min(5, impact))
    return likelihood * impact


def risk_level_for_score(score: int) -> RiskLevel:
    if score >= 17:
        return RiskLevel.CRITICAL
    if score >= 10:
        return RiskLevel.HIGH
    if score >= 5:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


# Derive default likelihood/impact when auto-generating risks from findings.
_SEVERITY_IMPACT: dict[Severity, int] = {
    Severity.LOW: 2,
    Severity.MEDIUM: 3,
    Severity.HIGH: 4,
    Severity.CRITICAL: 5,
}

_SEVERITY_LIKELIHOOD: dict[Severity, int] = {
    Severity.LOW: 2,
    Severity.MEDIUM: 3,
    Severity.HIGH: 4,
    Severity.CRITICAL: 4,
}

_CRITICALITY_BUMP: dict[Criticality, int] = {
    Criticality.LOW: 0,
    Criticality.MEDIUM: 0,
    Criticality.HIGH: 1,
    Criticality.CRITICAL: 1,
}


def derive_likelihood_impact(
    severity: Severity, asset_criticality: Criticality | None
) -> tuple[int, int]:
    impact = _SEVERITY_IMPACT.get(severity, 3)
    likelihood = _SEVERITY_LIKELIHOOD.get(severity, 3)
    if asset_criticality is not None:
        impact = min(5, impact + _CRITICALITY_BUMP.get(asset_criticality, 0))
    return likelihood, impact
