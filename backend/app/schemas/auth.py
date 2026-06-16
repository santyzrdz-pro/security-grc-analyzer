"""Auth and user schemas."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role: str = "Security Analyst"


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: str | None = None
    is_active: bool | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    role: RoleOut


class UserWithPermissions(UserOut):
    permissions: list[str]
