"""Generated audit report metadata model."""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[str] = mapped_column(String(60), default="Audit", nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    compliance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generated_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
