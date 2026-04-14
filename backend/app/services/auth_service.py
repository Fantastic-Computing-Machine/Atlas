"""Google OAuth 2.0 authentication service.

Handles:
- OAuth flow initiation (authorization URL generation)
- Token exchange (authorization code → credentials)
- Token encryption/decryption at rest (Fernet)
- Token refresh
- User creation/update in the database
"""

from __future__ import annotations

import json
import logging
from typing import Any

from cryptography.fernet import Fernet
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.mailbox import MailboxConnection
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthService:
    """Manage Google OAuth 2.0 authentication lifecycle."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._fernet = Fernet(settings.encryption_key.encode()) if settings.encryption_key else None

    # ── OAuth Flow ───────────────────────────

    def build_flow(self) -> Flow:
        """Create a google_auth_oauthlib Flow from config."""
        client_config = {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri],
            }
        }
        flow = Flow.from_client_config(
            client_config,
            scopes=settings.gmail_scopes_list,
            redirect_uri=settings.google_redirect_uri,
        )
        return flow

    def get_authorization_url(self) -> str:
        """Generate the Google OAuth consent URL."""
        flow = self.build_flow()
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return auth_url

    async def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for credentials and persist user.

        Returns:
            Dict with user info and connection status.
        """
        flow = self.build_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Get user email from Google userinfo
        import httplib2
        from googleapiclient.discovery import build

        service = build("oauth2", "v2", credentials=credentials)
        user_info = service.userinfo().get().execute()
        email = user_info.get("email", "")

        # Encrypt and store tokens
        token_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": list(credentials.scopes) if credentials.scopes else [],
        }
        encrypted = self._encrypt_tokens(token_data)

        # Upsert user
        user = await self._get_user_by_email(email)
        if user is None:
            user = User(email=email, auth_provider="google", encrypted_token_ref=encrypted)
            self.db.add(user)
            await self.db.flush()
        else:
            user.encrypted_token_ref = encrypted

        # Upsert mailbox connection
        result = await self.db.execute(
            select(MailboxConnection).where(MailboxConnection.user_id == user.id)
        )
        connection = result.scalar_one_or_none()
        if connection is None:
            connection = MailboxConnection(
                user_id=user.id,
                provider="gmail",
                granted_scopes=list(credentials.scopes) if credentials.scopes else [],
                status="connected",
            )
            self.db.add(connection)
        else:
            connection.granted_scopes = list(credentials.scopes) if credentials.scopes else []
            connection.status = "connected"
            connection.error_message = None

        await self.db.flush()

        return {
            "user_id": str(user.id),
            "email": email,
            "status": "connected",
        }

    # ── Token Management ─────────────────────

    def _encrypt_tokens(self, token_data: dict) -> str:
        """Encrypt token data with Fernet."""
        if self._fernet is None:
            raise RuntimeError("ENCRYPTION_KEY is not configured")
        payload = json.dumps(token_data).encode()
        return self._fernet.encrypt(payload).decode()

    def _decrypt_tokens(self, encrypted: str) -> dict:
        """Decrypt token data."""
        if self._fernet is None:
            raise RuntimeError("ENCRYPTION_KEY is not configured")
        payload = self._fernet.decrypt(encrypted.encode())
        return json.loads(payload.decode())

    async def get_credentials(self, user_id: str) -> Credentials | None:
        """Load and optionally refresh Google credentials for a user."""
        from uuid import UUID

        result = await self.db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if user is None or user.encrypted_token_ref is None:
            return None

        token_data = self._decrypt_tokens(user.encrypted_token_ref)
        creds = Credentials(
            token=token_data["token"],
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id", settings.google_client_id),
            client_secret=token_data.get("client_secret", settings.google_client_secret),
            scopes=token_data.get("scopes"),
        )

        # Refresh if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            # Re-encrypt the refreshed token
            token_data["token"] = creds.token
            user.encrypted_token_ref = self._encrypt_tokens(token_data)
            await self.db.flush()

        return creds

    async def get_connection_status(self, user_id: str) -> dict[str, Any]:
        """Get the connection status for a user."""
        from uuid import UUID

        result = await self.db.execute(
            select(MailboxConnection).where(MailboxConnection.user_id == UUID(user_id))
        )
        conn = result.scalar_one_or_none()
        if conn is None:
            return {"connected": False}

        return {
            "connected": conn.status == "connected",
            "status": conn.status,
            "last_sync_at": conn.last_sync_at.isoformat() if conn.last_sync_at else None,
            "granted_scopes": conn.granted_scopes,
        }

    async def disconnect(self, user_id: str) -> bool:
        """Mark a user as disconnected and clear tokens."""
        from uuid import UUID

        result = await self.db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if user is None:
            return False

        user.encrypted_token_ref = None

        conn_result = await self.db.execute(
            select(MailboxConnection).where(MailboxConnection.user_id == user.id)
        )
        conn = conn_result.scalar_one_or_none()
        if conn:
            conn.status = "disconnected"

        await self.db.flush()
        return True

    # ── Helpers ───────────────────────────────

    async def _get_user_by_email(self, email: str) -> User | None:
        """Fetch a user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_or_create_default_user(self) -> User | None:
        """For local-first mode: get the first (and likely only) user."""
        result = await self.db.execute(select(User).limit(1))
        return result.scalar_one_or_none()
