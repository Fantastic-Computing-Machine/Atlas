"""Authentication API routes.

Endpoints:
- GET  /api/auth/connect     → redirect to Google OAuth consent
- GET  /api/auth/callback    → handle OAuth callback
- GET  /api/auth/status      → check connection status
- POST /api/auth/disconnect  → revoke and clear tokens
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import AuthCallbackResponse, AuthConnectResponse, ConnectionStatus
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/connect", response_model=AuthConnectResponse)
async def connect_gmail(db: AsyncSession = Depends(get_db)):
    """Generate the Google OAuth consent URL.

    The frontend should redirect the user to this URL.
    """
    auth = AuthService(db)
    url = auth.get_authorization_url()
    return AuthConnectResponse(authorization_url=url)


@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle the OAuth callback from Google.

    Exchanges the authorization code for tokens, creates/updates
    the user, and redirects to the frontend.
    """
    auth = AuthService(db)
    try:
        result = await auth.exchange_code(code, state=state)
        # Redirect to frontend with success
        from app.config import get_settings

        settings = get_settings()
        return RedirectResponse(
            url=f"{settings.frontend_url}/connect?status=success&user_id={result['user_id']}"
        )
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}", exc_info=True)
        from app.config import get_settings

        settings = get_settings()
        return RedirectResponse(
            url=f"{settings.frontend_url}/connect?status=error&message={str(e)}"
        )


@router.get("/status", response_model=ConnectionStatus)
async def connection_status(
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Check the Gmail connection status for a user."""
    auth = AuthService(db)
    status = await auth.get_connection_status(user_id)

    user = await auth.get_or_create_default_user()
    email = user.email if user else None

    # Get message count
    from app.services.sync_service import SyncService

    sync = SyncService(db)
    sync_status = await sync.get_sync_status(user_id)

    return ConnectionStatus(
        connected=status.get("connected", False),
        email=email,
        status=status.get("status"),
        last_sync_at=status.get("last_sync_at"),
        granted_scopes=status.get("granted_scopes"),
        message_count=sync_status.get("message_count"),
    )


@router.post("/disconnect")
async def disconnect_gmail(
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect Gmail and clear stored tokens."""
    auth = AuthService(db)
    success = await auth.disconnect(user_id)
    return {"success": success}
