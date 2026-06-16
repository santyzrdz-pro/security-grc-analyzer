"""Role-based permission matrix.

Permissions are coarse-grained capability strings. Each role maps to the set of
capabilities it is granted. ``*`` grants everything (Admin).
"""
from __future__ import annotations

from app.models.enums import RoleName

# Capability constants
ASSET_READ = "asset:read"
ASSET_WRITE = "asset:write"
FINDING_READ = "finding:read"
FINDING_WRITE = "finding:write"
CONTROL_READ = "control:read"
CONTROL_WRITE = "control:write"
RISK_READ = "risk:read"
RISK_WRITE = "risk:write"
REMEDIATION_READ = "remediation:read"
REMEDIATION_WRITE = "remediation:write"
DASHBOARD_READ = "dashboard:read"
REPORT_READ = "report:read"
REPORT_WRITE = "report:write"
USER_MANAGE = "user:manage"
AUDIT_READ = "audit:read"

ROLE_PERMISSIONS: dict[str, set[str]] = {
    RoleName.ADMIN.value: {"*"},
    RoleName.ANALYST.value: {
        ASSET_READ,
        ASSET_WRITE,
        FINDING_READ,
        FINDING_WRITE,
        CONTROL_READ,
        RISK_READ,
        RISK_WRITE,
        REMEDIATION_READ,
        REMEDIATION_WRITE,
        DASHBOARD_READ,
        REPORT_READ,
        REPORT_WRITE,
    },
    RoleName.AUDITOR.value: {
        ASSET_READ,
        FINDING_READ,
        CONTROL_READ,
        RISK_READ,
        REMEDIATION_READ,
        DASHBOARD_READ,
        REPORT_READ,
        AUDIT_READ,
    },
    RoleName.EXECUTIVE.value: {
        DASHBOARD_READ,
        REPORT_READ,
        REPORT_WRITE,
    },
}


def role_has_permission(role_name: str, permission: str) -> bool:
    granted = ROLE_PERMISSIONS.get(role_name, set())
    return "*" in granted or permission in granted
