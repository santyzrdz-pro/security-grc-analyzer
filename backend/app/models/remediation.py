"""Remediation task tracking model."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RemediationStatus, Severity

if TYPE_CHECKING:
    from app.models.finding import Finding
    from app.models.risk import Risk


class Remediation(Base):
    __tablename__ = "remediations"

    id: Mapped[int] = mapped_column(primary_key=True)
    task: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[RemediationStatus] = mapped_column(
        SAEnum(RemediationStatus, native_enum=False, length=20),
        default=RemediationStatus.NOT_STARTED,
        nullable=False,
        index=True,
    )
    priority: Mapped[Severity] = mapped_column(
        SAEnum(Severity, native_enum=False, length=20),
        default=Severity.MEDIUM,
        nullable=False,
        index=True,
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    finding_id: Mapped[int | None] = mapped_column(
        ForeignKey("findings.id"), nullable=True, index=True
    )
    finding: Mapped["Finding | None"] = relationship()

    risk_id: Mapped[int | None] = mapped_column(
        ForeignKey("risks.id"), nullable=True, index=True
    )
    risk: Mapped["Risk | None"] = relationship()
