"""User-related Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    """Public user representation."""

    id: uuid.UUID
    email: str
    auth_provider: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConnectionStatus(BaseModel):
    """Gmail connection status."""

    connected: bool
    email: str | None = None
    status: str | None = None
    last_sync_at: datetime | None = None
    granted_scopes: list[str] | None = None
    message_count: int | None = None


class AuthConnectResponse(BaseModel):
    """Response from the connect endpoint."""

    authorization_url: str


class AuthCallbackResponse(BaseModel):
    """Response from the callback endpoint."""

    success: bool
    user: UserResponse | None = None
    message: str = ""
