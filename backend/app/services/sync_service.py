"""Sync service — orchestrates initial and incremental Gmail sync.

Coordinates between GmailService (API calls) and the database
to keep local message/thread data up to date.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.mailbox import MailboxConnection
from app.models.message import Message, Thread
from app.services.auth_service import AuthService
from app.services.gmail_service import GmailMessage, GmailService

logger = logging.getLogger(__name__)
settings = get_settings()


class SyncService:
    """Manages mailbox synchronization."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def initial_sync(
        self,
        user_id: str,
        days: int | None = None,
    ) -> dict:
        """Run the initial mailbox sync for a user.

        Fetches message metadata for the last N days and stores it.

        Returns:
            Summary dict with counts and status.
        """
        if days is None:
            days = settings.initial_sync_days

        # Get Gmail credentials
        auth = AuthService(self.db)
        creds = await auth.get_credentials(user_id)
        if creds is None:
            raise RuntimeError("No valid credentials for user")

        gmail = GmailService(creds)

        # Update connection status
        conn = await self._get_connection(user_id)
        if conn:
            conn.status = "syncing"
            await self.db.flush()

        try:
            # Build date query
            since = datetime.now(timezone.utc) - timedelta(days=days)
            epoch_seconds = int(since.timestamp())
            query = f"after:{epoch_seconds}"

            # List all message IDs in the window
            logger.info(f"[Sync] Listing messages for user={user_id} query={query}")
            message_refs = gmail.list_message_ids(query=query, max_results=5000)
            logger.info(f"[Sync] Found {len(message_refs)} messages")

            # Batch fetch metadata
            message_ids = [m["id"] for m in message_refs]
            synced_count = 0

            for batch_start in range(0, len(message_ids), settings.sync_batch_size):
                batch = message_ids[batch_start : batch_start + settings.sync_batch_size]
                gmail_messages = gmail.batch_get_messages(batch, format="metadata")

                for gm in gmail_messages:
                    await self._upsert_message(user_id, gm)
                    synced_count += 1

                await self.db.flush()
                logger.info(f"[Sync] Processed {synced_count}/{len(message_ids)} messages")

            # Get profile for history cursor
            profile = gmail.get_profile()
            history_id = profile.get("historyId")

            # Update connection
            if conn:
                conn.status = "connected"
                conn.sync_cursor = history_id
                conn.last_sync_at = datetime.now(timezone.utc)
                conn.error_message = None
                await self.db.flush()

            return {
                "status": "completed",
                "messages_synced": synced_count,
                "history_id": history_id,
            }

        except Exception as e:
            logger.error(f"[Sync] Failed: {e}", exc_info=True)
            if conn:
                conn.status = "error"
                conn.error_message = str(e)
                await self.db.flush()
            raise

    async def incremental_sync(self, user_id: str) -> dict:
        """Run an incremental sync using Gmail history API.

        Returns:
            Summary of changes processed.
        """
        auth = AuthService(self.db)
        creds = await auth.get_credentials(user_id)
        if creds is None:
            raise RuntimeError("No valid credentials for user")

        conn = await self._get_connection(user_id)
        if conn is None or conn.sync_cursor is None:
            raise RuntimeError("No sync cursor — run initial sync first")

        gmail = GmailService(creds)

        history_records, new_history_id = gmail.list_history(conn.sync_cursor)

        added_ids: list[str] = []
        for record in history_records:
            for msg_added in record.get("messagesAdded", []):
                msg_id = msg_added.get("message", {}).get("id")
                if msg_id:
                    added_ids.append(msg_id)

        # Fetch and store new messages
        if added_ids:
            # Deduplicate
            added_ids = list(set(added_ids))
            gmail_messages = gmail.batch_get_messages(added_ids, format="metadata")
            for gm in gmail_messages:
                await self._upsert_message(user_id, gm)

        # Update cursor
        if new_history_id:
            conn.sync_cursor = new_history_id
        conn.last_sync_at = datetime.now(timezone.utc)
        await self.db.flush()

        return {
            "status": "completed",
            "new_messages": len(added_ids),
            "history_records": len(history_records),
        }

    async def get_sync_status(self, user_id: str) -> dict:
        """Get current sync status and message counts."""
        conn = await self._get_connection(user_id)

        # Count messages
        result = await self.db.execute(
            select(func.count()).where(Message.user_id == UUID(user_id))
        )
        message_count = result.scalar() or 0

        return {
            "status": conn.status if conn else "not_connected",
            "last_sync_at": conn.last_sync_at.isoformat() if conn and conn.last_sync_at else None,
            "sync_cursor": conn.sync_cursor if conn else None,
            "message_count": message_count,
        }

    # ── Helpers ──────────────────────────────

    async def _upsert_message(self, user_id: str, gm: GmailMessage) -> None:
        """Insert or update a message in the database."""
        result = await self.db.execute(
            select(Message).where(Message.gmail_message_id == gm.id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update label IDs and other mutable fields
            existing.label_ids = gm.label_ids
            existing.snippet = gm.snippet
            existing.is_read = gm.is_read
        else:
            msg = Message(
                user_id=UUID(user_id),
                gmail_message_id=gm.id,
                thread_id=gm.thread_id,
                internal_date=gm.internal_date,
                from_header=gm.from_header,
                to_header=gm.to_header,
                subject=gm.subject,
                snippet=gm.snippet,
                label_ids=gm.label_ids,
                raw_size=gm.size_estimate,
                is_read=gm.is_read,
                has_attachments=gm.has_attachments,
            )
            self.db.add(msg)

    async def _get_connection(self, user_id: str) -> MailboxConnection | None:
        """Fetch the mailbox connection for a user."""
        result = await self.db.execute(
            select(MailboxConnection).where(MailboxConnection.user_id == UUID(user_id))
        )
        return result.scalar_one_or_none()
