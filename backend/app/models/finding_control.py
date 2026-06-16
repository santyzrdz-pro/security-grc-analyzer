"""Association between findings and NIST controls (mapping results)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.control import Control
    from app.models.finding import Finding


class FindingControl(Base):
    __tablename__ = "finding_controls"
    __table_args__ = (
        UniqueConstraint("finding_id", "control_id", name="uq_finding_control"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    finding_id: Mapped[int] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    control_id: Mapped[int] = mapped_column(
        ForeignKey("controls.id"), nullable=False, index=True
    )
    confidence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    method: Mapped[str | None] = mapped_column(String(40), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)

    finding: Mapped["Finding"] = relationship(back_populates="control_links")
    control: Mapped["Control"] = relationship(back_populates="finding_links")
