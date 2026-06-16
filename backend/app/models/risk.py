"""Risk register model."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer
from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import RiskLevel

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.finding import Finding


class Risk(Base):
    __tablename__ = "risks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    likelihood: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    impact: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 1-25
    risk_level: Mapped[RiskLevel] = mapped_column(
        SAEnum(RiskLevel, native_enum=False, length=20), nullable=False, index=True
    )
    mitigation_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("assets.id"), nullable=True, index=True
    )
    asset: Mapped["Asset | None"] = relationship(back_populates="risks")

    finding_id: Mapped[int | None] = mapped_column(
        ForeignKey("findings.id"), nullable=True, index=True
    )
    finding: Mapped["Finding | None"] = relationship(back_populates="risks")
