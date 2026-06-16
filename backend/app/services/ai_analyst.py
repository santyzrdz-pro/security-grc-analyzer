"""AI Security Analyst.

Provides an OpenAI-backed abstraction that turns a technical finding into
business-friendly narrative (executive summary, business impact, technical
explanation, recommended remediation). If no API key is configured, a
deterministic local fallback is used so the platform is fully demoable offline.
"""
from __future__ import annotations

import json
import logging

import httpx

from app.core.config import settings
from app.models.enums import Severity

logger = logging.getLogger(__name__)


class AIAnalysisResult(dict):
    """Plain dict with the four narrative sections."""


_SYSTEM_PROMPT = (
    "You are a senior cybersecurity GRC analyst. Given a security finding, "
    "produce concise, business-oriented analysis. Always return strict JSON with "
    "keys: executive_summary, business_impact, technical_explanation, "
    "recommended_remediation. Keep each value to 1-3 sentences."
)


def _fallback(title: str, description: str | None, severity: Severity) -> AIAnalysisResult:
    desc = description or title
    sev = severity.value if isinstance(severity, Severity) else str(severity)
    return AIAnalysisResult(
        executive_summary=(
            f"A {sev.lower()}-severity issue, '{title}', was identified and "
            "increases the organization's exposure to security incidents until remediated."
        ),
        business_impact=(
            "If left unaddressed, this weakness could enable unauthorized access to "
            "sensitive systems or data, leading to operational disruption, "
            "regulatory exposure, and reputational harm."
        ),
        technical_explanation=(
            f"Technical detail: {desc}. This condition deviates from the expected "
            "secure configuration baseline and weakens the affected control."
        ),
        recommended_remediation=(
            "Prioritize remediation according to severity, apply the appropriate "
            "secure configuration or patch, validate the fix, and document the change "
            "for audit evidence."
        ),
    )


def analyze_finding(
    title: str, description: str | None, severity: Severity
) -> AIAnalysisResult:
    """Return AI analysis, using OpenAI when available, else local fallback."""
    if not settings.OPENAI_API_KEY:
        return _fallback(title, description, severity)

    sev = severity.value if isinstance(severity, Severity) else str(severity)
    user_prompt = (
        f"Finding title: {title}\n"
        f"Severity: {sev}\n"
        f"Description: {description or 'N/A'}\n"
        "Return the JSON now."
    )
    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
            timeout=30.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        return AIAnalysisResult(
            executive_summary=data.get("executive_summary"),
            business_impact=data.get("business_impact"),
            technical_explanation=data.get("technical_explanation"),
            recommended_remediation=data.get("recommended_remediation"),
        )
    except Exception as exc:  # noqa: BLE001 - degrade gracefully
        logger.warning("OpenAI analysis failed, using fallback: %s", exc)
        return _fallback(title, description, severity)
