"""Security finding model."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import FindingStatus, Severity

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.finding_control import FindingControl
    from app.models.risk import Risk


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[Severity] = mapped_column(
        SAEnum(Severity, native_enum=False, length=20), nullable=False, index=True
    )
    status: Mapped[FindingStatus] = mapped_column(
        SAEnum(FindingStatus, native_enum=False, length=20),
        default=FindingStatus.OPEN,
        nullable=False,
        index=True,
    )
    detection_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str | None] = mapped_column(String(120), nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    cve: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)

    asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("assets.id"), nullable=True, index=True
    )
    asset: Mapped["Asset | None"] = relationship(back_populates="findings")

    # AI analyst output (cached)
    ai_executive_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_business_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_technical_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_recommended_remediation: Mapped[str | None] = mapped_column(Text, nullable=True)

    control_links: Mapped[list["FindingControl"]] = relationship(
        back_populates="finding", cascade="all, delete-orphan"
    )
    risks: Mapped[list["Risk"]] = relationship(back_populates="finding")
