"""Asset schemas."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AssetStatus, AssetType, Criticality, Environment


class AssetBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    owner: str | None = None
    business_unit: str | None = None
    asset_type: AssetType
    criticality: Criticality
    operating_system: str | None = None
    ip_address: str | None = None
    environment: Environment = Environment.PRODUCTION
    status: AssetStatus = AssetStatus.ACTIVE


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: str | None = None
    owner: str | None = None
    business_unit: str | None = None
    asset_type: AssetType | None = None
    criticality: Criticality | None = None
    operating_system: str | None = None
    ip_address: str | None = None
    environment: Environment | None = None
    status: AssetStatus | None = None


class AssetOut(AssetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
