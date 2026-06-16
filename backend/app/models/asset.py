"""Asset inventory model."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AssetStatus, AssetType, Criticality, Environment

if TYPE_CHECKING:
    from app.models.finding import Finding
    from app.models.risk import Risk


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    business_unit: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    asset_type: Mapped[AssetType] = mapped_column(
        SAEnum(AssetType, native_enum=False, length=50), nullable=False, index=True
    )
    criticality: Mapped[Criticality] = mapped_column(
        SAEnum(Criticality, native_enum=False, length=20), nullable=False, index=True
    )
    operating_system: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    environment: Mapped[Environment] = mapped_column(
        SAEnum(Environment, native_enum=False, length=20),
        default=Environment.PRODUCTION,
        nullable=False,
        index=True,
    )
    status: Mapped[AssetStatus] = mapped_column(
        SAEnum(AssetStatus, native_enum=False, length=20),
        default=AssetStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    findings: Mapped[list["Finding"]] = relationship(back_populates="asset")
    risks: Mapped[list["Risk"]] = relationship(back_populates="asset")
