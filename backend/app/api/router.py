"""Aggregate API router."""
from __future__ import annotations

from fastapi import APIRouter

from app.api import (
    routes_assets,
    routes_auth,
    routes_controls,
    routes_dashboard,
    routes_findings,
    routes_mapping,
    routes_remediations,
    routes_reports,
    routes_risks,
    routes_users,
)

api_router = APIRouter()
api_router.include_router(routes_auth.router)
api_router.include_router(routes_users.router)
api_router.include_router(routes_assets.router)
api_router.include_router(routes_findings.router)
api_router.include_router(routes_controls.router)
api_router.include_router(routes_mapping.router)
api_router.include_router(routes_risks.router)
api_router.include_router(routes_remediations.router)
api_router.include_router(routes_dashboard.router)
api_router.include_router(routes_reports.router)
