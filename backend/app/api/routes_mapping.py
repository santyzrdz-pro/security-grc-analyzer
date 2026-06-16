"""Control mapping engine routes (stateless testing endpoint)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.deps import require_permission
from app.core.permissions import CONTROL_READ
from app.models.user import User
from app.services.mapping_engine import map_finding

router = APIRouter(prefix="/mapping", tags=["mapping"])


class MappingRequest(BaseModel):
    finding: str = Field(min_length=1)
    max_controls: int = Field(default=4, ge=1, le=9)


class MappingMatchOut(BaseModel):
    control_id: str
    confidence: int
    method: str
    rationale: str


class MappingResponse(BaseModel):
    finding: str
    controls: list[str]
    confidence: int
    matches: list[MappingMatchOut]


@router.post("", response_model=MappingResponse)
def run_mapping(
    payload: MappingRequest,
    _: User = Depends(require_permission(CONTROL_READ)),
) -> MappingResponse:
    result = map_finding(payload.finding, max_controls=payload.max_controls)
    return MappingResponse(
        finding=result.finding,
        controls=result.controls,
        confidence=result.confidence,
        matches=[
            MappingMatchOut(
                control_id=m.control_id,
                confidence=m.confidence,
                method=m.method,
                rationale=m.rationale,
            )
            for m in result.matches
        ],
    )
