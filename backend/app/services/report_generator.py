"""Audit-ready PDF report generator using ReportLab."""
from __future__ import annotations

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.control import Control
from app.models.enums import FindingStatus, RiskLevel, Severity
from app.models.finding import Finding
from app.models.risk import Risk
from app.services.compliance import compute_compliance

BRAND = colors.HexColor("#2563eb")
BRAND_DARK = colors.HexColor("#0f172a")
LIGHT = colors.HexColor("#f1f5f9")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="CMTitle",
            parent=styles["Title"],
            textColor=BRAND_DARK,
            fontSize=26,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CMSection",
            parent=styles["Heading2"],
            textColor=BRAND,
            fontSize=15,
            spaceBefore=14,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CMSub",
            parent=styles["Normal"],
            textColor=colors.HexColor("#475569"),
            fontSize=10,
            alignment=TA_CENTER,
        )
    )
    return styles


def _table(data: list[list[str]], col_widths: list[float] | None = None) -> Table:
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def generate_audit_report(
    db: Session, generated_by: str = "Security Compliance & Risk Management Analyzer"
) -> bytes:
    styles = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        title="Security Compliance & Risk Audit Report",
    )
    story: list = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ---- Cover ----
    story.append(Spacer(1, 60))
    story.append(
        Paragraph("Security Compliance &amp; Risk Management Analyzer", styles["CMTitle"])
    )
    story.append(Paragraph("Audit Report", styles["CMSection"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Generated: {now}", styles["CMSub"]))
    story.append(Paragraph(f"Prepared by: {generated_by}", styles["CMSub"]))
    story.append(Spacer(1, 30))

    # ---- Compliance snapshot for the cover ----
    compliance = compute_compliance(db)
    cover_metrics = [
        ["Compliance Score", f"{compliance.compliance_percentage}%  (Grade {compliance.grade})"],
        ["Controls Assessed", str(compliance.total_controls)],
        ["Controls Implemented", str(compliance.implemented_controls)],
    ]
    story.append(_table([["Metric", "Value"], *cover_metrics], [80 * mm, 80 * mm]))
    story.append(PageBreak())

    # ---- 1. Executive Summary ----
    total_assets = db.scalar(select(func.count(Asset.id)).where(Asset.deleted_at.is_(None))) or 0
    open_findings = (
        db.scalar(
            select(func.count(Finding.id)).where(
                Finding.deleted_at.is_(None), Finding.status == FindingStatus.OPEN
            )
        )
        or 0
    )
    critical_findings = (
        db.scalar(
            select(func.count(Finding.id)).where(
                Finding.deleted_at.is_(None), Finding.severity == Severity.CRITICAL
            )
        )
        or 0
    )
    total_risks = db.scalar(select(func.count(Risk.id)).where(Risk.deleted_at.is_(None))) or 0

    story.append(Paragraph("1. Executive Summary", styles["CMSection"]))
    story.append(
        Paragraph(
            f"This report summarizes the current security and compliance posture. "
            f"The organization manages <b>{total_assets}</b> assets, with "
            f"<b>{open_findings}</b> open findings ("
            f"<b>{critical_findings}</b> critical) and <b>{total_risks}</b> tracked risks. "
            f"The overall compliance score is <b>{compliance.compliance_percentage}%</b> "
            f"(Grade {compliance.grade}), based on NIST SP 800-53 control implementation.",
            styles["Normal"],
        )
    )

    # ---- 2. Asset Inventory ----
    story.append(Paragraph("2. Asset Inventory", styles["CMSection"]))
    assets = list(
        db.scalars(
            select(Asset).where(Asset.deleted_at.is_(None)).order_by(Asset.criticality)
        ).all()
    )[:25]
    asset_rows = [["Name", "Type", "Criticality", "Environment", "Status"]]
    for a in assets:
        asset_rows.append(
            [a.name, a.asset_type.value, a.criticality.value, a.environment.value, a.status.value]
        )
    story.append(_table(asset_rows, [45 * mm, 32 * mm, 28 * mm, 30 * mm, 28 * mm]))

    # ---- 3. Findings ----
    story.append(Paragraph("3. Findings", styles["CMSection"]))
    findings = list(
        db.scalars(
            select(Finding).where(Finding.deleted_at.is_(None)).order_by(Finding.severity)
        ).all()
    )[:25]
    finding_rows = [["Title", "Severity", "Status", "CVE"]]
    for f in findings:
        finding_rows.append([f.title, f.severity.value, f.status.value, f.cve or "-"])
    story.append(_table(finding_rows, [80 * mm, 28 * mm, 32 * mm, 28 * mm]))

    # ---- 4. Risk Register ----
    story.append(Paragraph("4. Risk Register", styles["CMSection"]))
    risks = list(
        db.scalars(
            select(Risk).where(Risk.deleted_at.is_(None)).order_by(Risk.risk_score.desc())
        ).all()
    )[:25]
    risk_rows = [["Risk", "Likelihood", "Impact", "Score", "Level"]]
    for r in risks:
        risk_rows.append(
            [r.title, str(r.likelihood), str(r.impact), str(r.risk_score), r.risk_level.value]
        )
    story.append(_table(risk_rows, [70 * mm, 24 * mm, 22 * mm, 20 * mm, 28 * mm]))

    # ---- 5. Control Mapping ----
    story.append(PageBreak())
    story.append(Paragraph("5. Control Mapping (NIST 800-53)", styles["CMSection"]))
    controls = list(db.scalars(select(Control).where(Control.deleted_at.is_(None))).all())
    control_rows = [["Control", "Family", "Title", "Status"]]
    for c in controls:
        control_rows.append(
            [c.control_id, c.family, c.title, c.implementation_status.value]
        )
    story.append(_table(control_rows, [22 * mm, 18 * mm, 80 * mm, 40 * mm]))

    # ---- 6. Compliance Status ----
    story.append(Paragraph("6. Compliance Status", styles["CMSection"]))
    comp_rows = [["Metric", "Value"]]
    comp_rows.append(["Compliance Percentage", f"{compliance.compliance_percentage}%"])
    comp_rows.append(["Grade", compliance.grade])
    comp_rows.append(["Implemented", str(compliance.implemented_controls)])
    comp_rows.append(["Partially Implemented", str(compliance.partially_implemented)])
    comp_rows.append(["Not Implemented", str(compliance.not_implemented)])
    story.append(_table(comp_rows, [80 * mm, 80 * mm]))

    # ---- 7. Recommendations ----
    story.append(Paragraph("7. Recommendations", styles["CMSection"]))
    crit_risks = sum(1 for r in risks if r.risk_level == RiskLevel.CRITICAL)
    recs = [
        f"Remediate the {critical_findings} critical finding(s) as the highest priority.",
        f"Address the {crit_risks} critical risk(s) in the register with documented mitigation plans.",
        "Improve implementation of NIST control families scoring below 70%.",
        "Enable continuous monitoring and centralized log review (AU-6, SI-4).",
        "Schedule recurring access reviews to enforce least privilege (AC-6).",
    ]
    for i, rec in enumerate(recs, start=1):
        story.append(Paragraph(f"{i}. {rec}", styles["Normal"]))
        story.append(Spacer(1, 2))

    doc.build(story)
    buf.seek(0)
    return buf.read()
