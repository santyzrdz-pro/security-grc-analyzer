"""Control schemas."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ControlImplementationStatus


class ControlBase(BaseModel):
    control_id: str = Field(min_length=1, max_length=20)
    family: str = Field(min_length=1, max_length=10)
    family_name: str | None = None
    title: str
    description: str
    implementation_status: ControlImplementationStatus = (
        ControlImplementationStatus.NOT_IMPLEMENTED
    )


class ControlCreate(ControlBase):
    pass


class ControlUpdate(BaseModel):
    family: str | None = None
    family_name: str | None = None
    title: str | None = None
    description: str | None = None
    implementation_status: ControlImplementationStatus | None = None


class ControlOut(ControlBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
