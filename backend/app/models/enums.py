"""Shared enumerations used across models and schemas."""
from __future__ import annotations

from enum import Enum


class RoleName(str, Enum):
    ADMIN = "Admin"
    ANALYST = "Security Analyst"
    AUDITOR = "Auditor"
    EXECUTIVE = "Executive"


class AssetType(str, Enum):
    WORKSTATION = "Workstation"
    SERVER = "Server"
    CLOUD_RESOURCE = "Cloud Resource"
    NETWORK_DEVICE = "Network Device"
    APPLICATION = "Application"


class Criticality(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Environment(str, Enum):
    PRODUCTION = "Production"
    STAGING = "Staging"
    DEVELOPMENT = "Development"
    TEST = "Test"


class AssetStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    DECOMMISSIONED = "Decommissioned"


class Severity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class FindingStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    ACCEPTED_RISK = "Accepted Risk"


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class RemediationStatus(str, Enum):
    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    BLOCKED = "Blocked"
    COMPLETED = "Completed"


class ControlImplementationStatus(str, Enum):
    IMPLEMENTED = "Implemented"
    PARTIALLY_IMPLEMENTED = "Partially Implemented"
    PLANNED = "Planned"
    NOT_IMPLEMENTED = "Not Implemented"
    NOT_APPLICABLE = "Not Applicable"
