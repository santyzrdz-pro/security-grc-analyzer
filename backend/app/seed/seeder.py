"""Idempotent database seeder."""
from __future__ import annotations

import logging
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.asset import Asset
from app.models.control import Control
from app.models.enums import RoleName
from app.models.finding import Finding
from app.models.remediation import Remediation
from app.models.role import Role
from app.models.user import User
from app.seed.data import (
    ASSETS,
    CONTROLS,
    FAMILY_NAMES,
    FINDINGS,
    REMEDIATIONS,
)
from app.services.ai_analyst import analyze_finding
from app.services.mapping_service import apply_mapping_to_finding
from app.services.risk_engine import (
    compute_risk_score,
    derive_likelihood_impact,
    risk_level_for_score,
)
from app.models.risk import Risk

logger = logging.getLogger(__name__)

ROLE_DESCRIPTIONS = {
    RoleName.ADMIN: "Full access to all modules and administration.",
    RoleName.ANALYST: "Manage findings, risks, assets, and remediation.",
    RoleName.AUDITOR: "Read-only access for audit and assurance.",
    RoleName.EXECUTIVE: "Dashboards and reports only.",
}

DEMO_USERS: list[tuple[str, str, RoleName, str]] = []


def seed_roles(db: Session) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for role_name in RoleName:
        role = db.scalar(select(Role).where(Role.name == role_name.value))
        if not role:
            role = Role(
                name=role_name.value, description=ROLE_DESCRIPTIONS.get(role_name)
            )
            db.add(role)
            db.flush()
        roles[role_name.value] = role
    db.commit()
    return roles


def seed_system_user(db: Session, roles: dict[str, Role]) -> None:
    admin_email = settings.ADMIN_EMAIL.lower()
    if not db.scalar(select(User).where(User.email == admin_email)):
        db.add(
            User(
                email=admin_email,
                full_name="System",
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role_id=roles[RoleName.ADMIN.value].id,
            )
        )
        db.commit()
    for email, name, role_name, password in DEMO_USERS:
        if not db.scalar(select(User).where(User.email == email)):
            db.add(
                User(
                    email=email,
                    full_name=name,
                    hashed_password=hash_password(password),
                    role_id=roles[role_name.value].id,
                )
            )
    db.commit()


def seed_controls(db: Session) -> None:
    for item in CONTROLS:
        if db.scalar(select(Control).where(Control.control_id == item["control_id"])):
            continue
        db.add(
            Control(
                control_id=item["control_id"],
                family=item["family"],
                family_name=FAMILY_NAMES.get(item["family"]),
                title=item["title"],
                description=item["description"],
                implementation_status=item["implementation_status"],
            )
        )
    db.commit()


def seed_assets(db: Session) -> dict[str, Asset]:
    assets: dict[str, Asset] = {}
    for item in ASSETS:
        existing = db.scalar(select(Asset).where(Asset.name == item["name"]))
        if existing:
            assets[item["name"]] = existing
            continue
        asset = Asset(**item)
        db.add(asset)
        db.flush()
        assets[item["name"]] = asset
    db.commit()
    return assets


def seed_findings(db: Session, assets: dict[str, Asset]) -> dict[str, Finding]:
    findings: dict[str, Finding] = {}
    today = date.today()
    for item in FINDINGS:
        existing = db.scalar(select(Finding).where(Finding.title == item["title"]))
        if existing:
            findings[item["title"]] = existing
            continue
        asset = assets.get(item["asset"]) if item.get("asset") else None
        finding = Finding(
            title=item["title"],
            description=item["description"],
            severity=item["severity"],
            status=item["status"],
            source=item.get("source"),
            cve=item.get("cve"),
            evidence=item.get("evidence"),
            detection_date=today - timedelta(days=item.get("detection_offset_days", 0)),
            asset_id=asset.id if asset else None,
        )
        db.add(finding)
        db.flush()
        apply_mapping_to_finding(db, finding)
        ai = analyze_finding(finding.title, finding.description, finding.severity)
        finding.ai_executive_summary = ai.get("executive_summary")
        finding.ai_business_impact = ai.get("business_impact")
        finding.ai_technical_explanation = ai.get("technical_explanation")
        finding.ai_recommended_remediation = ai.get("recommended_remediation")
        findings[item["title"]] = finding
    db.commit()
    return findings


def seed_risks(db: Session, findings: dict[str, Finding]) -> None:
    if db.scalar(select(func.count(Risk.id))):
        return
    for finding in findings.values():
        asset = finding.asset
        criticality = asset.criticality if asset else None
        likelihood, impact = derive_likelihood_impact(finding.severity, criticality)
        score = compute_risk_score(likelihood, impact)
        db.add(
            Risk(
                title=f"Risk: {finding.title}",
                description=finding.description,
                likelihood=likelihood,
                impact=impact,
                risk_score=score,
                risk_level=risk_level_for_score(score),
                mitigation_plan=finding.ai_recommended_remediation,
                owner=asset.owner if asset else None,
                asset_id=finding.asset_id,
                finding_id=finding.id,
            )
        )
    db.commit()


def seed_remediations(db: Session, findings: dict[str, Finding]) -> None:
    today = date.today()
    for item in REMEDIATIONS:
        if db.scalar(select(Remediation).where(Remediation.task == item["task"])):
            continue
        finding = findings.get(item.get("finding_title", ""))
        db.add(
            Remediation(
                task=item["task"],
                description=item.get("description"),
                owner=item.get("owner"),
                status=item["status"],
                priority=item["priority"],
                due_date=today + timedelta(days=item.get("due_offset_days", 0)),
                finding_id=finding.id if finding else None,
            )
        )
    db.commit()


def run_seed(db: Session, with_demo: bool = False) -> None:
    logger.info("Seeding roles and system user...")
    roles = seed_roles(db)
    seed_system_user(db, roles)
    logger.info("Seeding NIST controls...")
    seed_controls(db)
    if not with_demo:
        logger.info("Seed complete (no demo data).")
        return
    logger.info("Seeding demo assets, findings, risks, remediations...")
    assets = seed_assets(db)
    findings = seed_findings(db, assets)
    seed_risks(db, findings)
    seed_remediations(db, findings)
    logger.info("Seed complete.")
