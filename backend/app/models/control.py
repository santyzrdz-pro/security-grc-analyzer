"""NIST 800-53 control library model."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ControlImplementationStatus

if TYPE_CHECKING:
    from app.models.finding_control import FindingControl


class Control(Base):
    __tablename__ = "controls"

    id: Mapped[int] = mapped_column(primary_key=True)
    control_id: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    family: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    family_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    implementation_status: Mapped[ControlImplementationStatus] = mapped_column(
        SAEnum(ControlImplementationStatus, native_enum=False, length=40),
        default=ControlImplementationStatus.NOT_IMPLEMENTED,
        nullable=False,
        index=True,
    )

    finding_links: Mapped[list["FindingControl"]] = relationship(
        back_populates="control"
    )
