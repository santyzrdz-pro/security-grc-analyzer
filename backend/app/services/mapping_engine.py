"""Rule-based control mapping engine.

Maps free-text security findings to NIST 800-53 controls using a combination of
keyword and regular-expression pattern matching. Each rule contributes a
confidence weight; the engine aggregates weights per control, supports multiple
control outputs per finding, and normalizes confidence to a 0-100 score.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MappingRule:
    control_id: str
    keywords: tuple[str, ...] = ()
    patterns: tuple[str, ...] = ()
    weight: int = 60
    rationale: str = ""


# Ordered library of mapping rules. Multiple rules can target the same control.
MAPPING_RULES: list[MappingRule] = [
    MappingRule(
        control_id="SC-7",
        keywords=("firewall", "boundary", "network segmentation", "perimeter", "dmz", "egress"),
        patterns=(r"firewall\s+(disabled|off|down|misconfig)", r"open\s+port"),
        weight=70,
        rationale="Boundary protection / firewall controls (SC-7).",
    ),
    MappingRule(
        control_id="IA-5",
        keywords=("password policy", "weak password", "password complexity", "credential", "default password", "password rotation"),
        patterns=(r"weak\s+password", r"password\s+(policy|complexity)"),
        weight=70,
        rationale="Authenticator management / password policy (IA-5).",
    ),
    MappingRule(
        control_id="IA-2",
        keywords=("mfa", "multi-factor", "multifactor", "two-factor", "2fa", "single factor", "authentication bypass"),
        patterns=(r"(no|missing|disabled)\s+mfa", r"multi-?factor"),
        weight=70,
        rationale="Identification and authentication / MFA (IA-2).",
    ),
    MappingRule(
        control_id="AC-6",
        keywords=("excessive privilege", "administrator privilege", "admin rights", "least privilege", "over-privileged", "privilege escalation", "sudo"),
        patterns=(r"excessive\s+(admin|administrator|privilege)", r"least\s+privilege"),
        weight=72,
        rationale="Least privilege (AC-6).",
    ),
    MappingRule(
        control_id="AC-2",
        keywords=("account management", "stale account", "orphaned account", "inactive account", "disabled account", "shared account", "service account"),
        patterns=(r"(stale|orphaned|inactive|dormant)\s+account",),
        weight=66,
        rationale="Account management (AC-2).",
    ),
    MappingRule(
        control_id="AC-3",
        keywords=("access control", "unauthorized access", "acl", "permission", "rbac", "authorization"),
        patterns=(r"unauthorized\s+access", r"access\s+control"),
        weight=62,
        rationale="Access enforcement (AC-3).",
    ),
    MappingRule(
        control_id="AU-2",
        keywords=("logging disabled", "no logging", "audit logging", "log generation", "event logging"),
        patterns=(r"(missing|no|disabled)\s+(security\s+)?logging", r"audit\s+log"),
        weight=64,
        rationale="Event logging (AU-2).",
    ),
    MappingRule(
        control_id="AU-6",
        keywords=("log review", "log monitoring", "siem", "log analysis", "missing security logging", "no log review"),
        patterns=(r"log\s+(review|monitoring|analysis)", r"missing\s+security\s+logging"),
        weight=68,
        rationale="Audit record review, analysis, and reporting (AU-6).",
    ),
    MappingRule(
        control_id="SI-4",
        keywords=("intrusion detection", "ids", "ips", "endpoint detection", "edr", "antivirus", "malware", "monitoring", "no monitoring"),
        patterns=(r"(intrusion|malware|endpoint)\s+(detection)?", r"(missing|no)\s+monitoring"),
        weight=66,
        rationale="System monitoring (SI-4).",
    ),
]


@dataclass
class ControlMatch:
    control_id: str
    confidence: int
    method: str
    rationale: str


@dataclass
class MappingResult:
    finding: str
    controls: list[str] = field(default_factory=list)
    confidence: int = 0
    matches: list[ControlMatch] = field(default_factory=list)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def map_finding(text: str, max_controls: int = 4) -> MappingResult:
    """Map a finding's text (title + description) to NIST controls."""
    haystack = _normalize(text)
    if not haystack:
        return MappingResult(finding=text)

    scores: dict[str, dict] = {}

    for rule in MAPPING_RULES:
        hit_weight = 0
        method = ""
        for keyword in rule.keywords:
            if keyword in haystack:
                hit_weight = max(hit_weight, rule.weight)
                method = "keyword"
        for pattern in rule.patterns:
            if re.search(pattern, haystack):
                # Pattern matches are stronger signals.
                hit_weight = max(hit_weight, rule.weight + 18)
                method = "pattern" if method != "keyword" else "keyword+pattern"
        if hit_weight == 0:
            continue
        existing = scores.get(rule.control_id)
        if existing is None or hit_weight > existing["confidence"]:
            scores[rule.control_id] = {
                "confidence": min(hit_weight, 99),
                "method": method,
                "rationale": rule.rationale,
            }

    matches = [
        ControlMatch(
            control_id=cid,
            confidence=data["confidence"],
            method=data["method"],
            rationale=data["rationale"],
        )
        for cid, data in scores.items()
    ]
    matches.sort(key=lambda m: m.confidence, reverse=True)
    matches = matches[:max_controls]

    overall = matches[0].confidence if matches else 0
    return MappingResult(
        finding=text,
        controls=[m.control_id for m in matches],
        confidence=overall,
        matches=matches,
    )
