"""Asset inventory routes."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.pagination import paginate
from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import ASSET_READ, ASSET_WRITE
from app.models.asset import Asset
from app.models.enums import AssetStatus, AssetType, Criticality, Environment
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetOut, AssetUpdate
from app.schemas.common import Page
from app.services.audit import record_audit

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=Page[AssetOut])
def list_assets(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(ASSET_READ)),
    search: str | None = None,
    asset_type: AssetType | None = None,
    criticality: Criticality | None = None,
    environment: Environment | None = None,
    status: AssetStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
) -> Page:
    stmt = select(Asset).where(Asset.deleted_at.is_(None))
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            or_(
                Asset.name.ilike(like),
                Asset.owner.ilike(like),
                Asset.business_unit.ilike(like),
                Asset.ip_address.ilike(like),
            )
        )
    if asset_type:
        stmt = stmt.where(Asset.asset_type == asset_type)
    if criticality:
        stmt = stmt.where(Asset.criticality == criticality)
    if environment:
        stmt = stmt.where(Asset.environment == environment)
    if status:
        stmt = stmt.where(Asset.status == status)
    stmt = stmt.order_by(Asset.name)
    return paginate(db, stmt, page, page_size, AssetOut.model_validate)


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(ASSET_READ)),
) -> Asset:
    asset = db.get(Asset, asset_id)
    if not asset or asset.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.post("", response_model=AssetOut, status_code=201)
def create_asset(
    payload: AssetCreate,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(ASSET_WRITE)),
) -> Asset:
    asset = Asset(**payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    record_audit(
        db,
        user=current,
        action="create",
        entity_type="asset",
        entity_id=asset.id,
        detail=asset.name,
        ip_address=request.client.host if request.client else None,
    )
    return asset


@router.patch("/{asset_id}", response_model=AssetOut)
def update_asset(
    asset_id: int,
    payload: AssetUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(ASSET_WRITE)),
) -> Asset:
    asset = db.get(Asset, asset_id)
    if not asset or asset.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Asset not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, key, value)
    db.commit()
    db.refresh(asset)
    record_audit(db, user=current, action="update", entity_type="asset", entity_id=asset.id)
    return asset


@router.delete("/{asset_id}", status_code=204)
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(ASSET_WRITE)),
):
    asset = db.get(Asset, asset_id)
    if not asset or asset.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Asset not found")
    asset.deleted_at = datetime.now(timezone.utc)
    db.commit()
    record_audit(db, user=current, action="delete", entity_type="asset", entity_id=asset_id)
