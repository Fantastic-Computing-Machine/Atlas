"""Gmail API client wrapper.

Provides a clean interface over the Google Gmail API for:
- Listing messages with search queries and label filters
- Fetching individual messages (metadata or full)
- Fetching threads
- Listing labels
- Batch operations
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


@dataclass
class GmailMessage:
    """Parsed Gmail message data."""

    id: str
    thread_id: str
    internal_date: datetime | None
    from_header: str | None
    to_header: str | None
    subject: str | None
    snippet: str | None
    label_ids: list[str]
    body_text: str | None
    size_estimate: int | None
    is_read: bool
    has_attachments: bool


@dataclass
class GmailLabel:
    """Gmail label metadata."""

    id: str
    name: str
    type: str  # system | user
    message_count: int | None = None
    threads_count: int | None = None


class GmailService:
    """Wrapper around the Gmail API."""

    def __init__(self, credentials: Credentials) -> None:
        self._service = build("gmail", "v1", credentials=credentials)
        self._user_id = "me"

    # ── Labels ───────────────────────────────

    def list_labels(self) -> list[GmailLabel]:
        """Fetch all labels for the authenticated user."""
        result = self._service.users().labels().list(userId=self._user_id).execute()
        labels = []
        for lbl in result.get("labels", []):
            labels.append(
                GmailLabel(
                    id=lbl["id"],
                    name=lbl["name"],
                    type=lbl.get("type", "user"),
                    message_count=lbl.get("messagesTotal"),
                    threads_count=lbl.get("threadsTotal"),
                )
            )
        return labels

    # ── Messages ─────────────────────────────

    def list_message_ids(
        self,
        query: str | None = None,
        label_ids: list[str] | None = None,
        max_results: int = 500,
    ) -> list[dict[str, str]]:
        """List message IDs (and thread IDs) matching query/labels.

        Returns:
            List of dicts with 'id' and 'threadId'.
        """
        all_messages: list[dict[str, str]] = []
        page_token: str | None = None

        while len(all_messages) < max_results:
            batch_size = min(100, max_results - len(all_messages))
            kwargs: dict[str, Any] = {
                "userId": self._user_id,
                "maxResults": batch_size,
            }
            if query:
                kwargs["q"] = query
            if label_ids:
                kwargs["labelIds"] = label_ids
            if page_token:
                kwargs["pageToken"] = page_token

            result = self._service.users().messages().list(**kwargs).execute()
            messages = result.get("messages", [])
            all_messages.extend(messages)

            page_token = result.get("nextPageToken")
            if not page_token:
                break

        return all_messages[:max_results]

    def get_message(
        self,
        message_id: str,
        format: str = "metadata",
        metadata_headers: list[str] | None = None,
    ) -> GmailMessage:
        """Fetch a single message.

        Args:
            message_id: Gmail message ID.
            format: 'metadata', 'full', 'raw', or 'minimal'.
            metadata_headers: Headers to include when format='metadata'.
        """
        if metadata_headers is None:
            metadata_headers = ["From", "To", "Subject", "Date"]

        kwargs: dict[str, Any] = {
            "userId": self._user_id,
            "id": message_id,
            "format": format,
        }
        if format == "metadata":
            kwargs["metadataHeaders"] = metadata_headers

        msg = self._service.users().messages().get(**kwargs).execute()
        return self._parse_message(msg, include_body=(format == "full"))

    def batch_get_messages(
        self,
        message_ids: list[str],
        format: str = "metadata",
        metadata_headers: list[str] | None = None,
    ) -> list[GmailMessage]:
        """Batch fetch multiple messages.

        Uses the Gmail API's batch request capability.
        """
        if metadata_headers is None:
            metadata_headers = ["From", "To", "Subject", "Date"]

        results: list[GmailMessage] = []

        # Process in batches of 100 (Gmail API limit)
        for i in range(0, len(message_ids), 100):
            batch_ids = message_ids[i : i + 100]
            batch = self._service.new_batch_http_request()

            def _callback(request_id, response, exception):
                if exception:
                    logger.warning(f"Batch get failed for {request_id}: {exception}")
                    return
                results.append(
                    self._parse_message(response, include_body=(format == "full"))
                )

            for mid in batch_ids:
                kwargs: dict[str, Any] = {
                    "userId": self._user_id,
                    "id": mid,
                    "format": format,
                }
                if format == "metadata":
                    kwargs["metadataHeaders"] = metadata_headers
                batch.add(
                    self._service.users().messages().get(**kwargs),
                    callback=_callback,
                )

            batch.execute()

        return results

    # ── Threads ──────────────────────────────

    def get_thread(self, thread_id: str) -> dict[str, Any]:
        """Fetch a thread with all its messages."""
        return (
            self._service.users()
            .threads()
            .get(userId=self._user_id, id=thread_id, format="metadata")
            .execute()
        )

    # ── History (incremental sync) ───────────

    def list_history(
        self,
        start_history_id: str,
        history_types: list[str] | None = None,
    ) -> tuple[list[dict], str | None]:
        """Fetch history changes since a given historyId.

        Returns:
            Tuple of (history_records, new_history_id).
        """
        if history_types is None:
            history_types = ["messageAdded", "messageDeleted", "labelAdded", "labelRemoved"]

        all_history: list[dict] = []
        page_token: str | None = None
        new_history_id: str | None = None

        while True:
            kwargs: dict[str, Any] = {
                "userId": self._user_id,
                "startHistoryId": start_history_id,
                "historyTypes": history_types,
            }
            if page_token:
                kwargs["pageToken"] = page_token

            try:
                result = self._service.users().history().list(**kwargs).execute()
            except Exception as e:
                logger.warning(f"History list failed: {e}")
                break

            history = result.get("history", [])
            all_history.extend(history)
            new_history_id = result.get("historyId", new_history_id)

            page_token = result.get("nextPageToken")
            if not page_token:
                break

        return all_history, new_history_id

    # ── Profile ──────────────────────────────

    def get_profile(self) -> dict[str, Any]:
        """Get the user's Gmail profile."""
        return self._service.users().getProfile(userId=self._user_id).execute()

    # ── Internal Helpers ─────────────────────

    def _parse_message(self, raw: dict, include_body: bool = False) -> GmailMessage:
        """Parse a raw Gmail API message response into a GmailMessage."""
        headers = {}
        payload = raw.get("payload", {})
        for h in payload.get("headers", []):
            headers[h["name"].lower()] = h["value"]

        # Parse internal date (milliseconds since epoch)
        internal_date = None
        if "internalDate" in raw:
            ts_ms = int(raw["internalDate"])
            internal_date = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)

        # Extract body text if requested
        body_text = None
        if include_body:
            body_text = self._extract_body_text(payload)

        label_ids = raw.get("labelIds", [])

        return GmailMessage(
            id=raw["id"],
            thread_id=raw.get("threadId", ""),
            internal_date=internal_date,
            from_header=headers.get("from"),
            to_header=headers.get("to"),
            subject=headers.get("subject"),
            snippet=raw.get("snippet"),
            label_ids=label_ids,
            body_text=body_text,
            size_estimate=raw.get("sizeEstimate"),
            is_read="UNREAD" not in label_ids,
            has_attachments=any(
                p.get("filename") for p in payload.get("parts", [])
            ),
        )

    def _extract_body_text(self, payload: dict) -> str | None:
        """Extract plain text body from message payload."""
        # Direct body
        body = payload.get("body", {})
        if body.get("data"):
            return base64.urlsafe_b64decode(body["data"]).decode("utf-8", errors="replace")

        # Multipart — look for text/plain first
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        # Fallback: text/html
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/html":
                data = part.get("body", {}).get("data")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        return None
