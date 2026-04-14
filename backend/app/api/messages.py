"""Messages and sync API routes.

Endpoints:
- GET  /api/messages           → list synced messages
- GET  /api/messages/{id}      → get message details
- POST /api/messages/sync      → trigger sync
- GET  /api/messages/sync/status → get sync status
- GET  /api/messages/labels    → list Gmail labels
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.message import Message

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Response Schemas ─────────────────────────

class MessageResponse(BaseModel):
    id: str
    gmail_message_id: str
    thread_id: str | None
    internal_date: str | None
    from_header: str | None
    to_header: str | None
    subject: str | None
    snippet: str | None
    label_ids: list[str] | None
    is_read: bool | None
    has_attachments: bool | None

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    total: int
    page: int
    page_size: int


class SyncStatusResponse(BaseModel):
    status: str
    last_sync_at: str | None
    sync_cursor: str | None
    message_count: int


class SyncTriggerResponse(BaseModel):
    status: str
    message: str


class GmailLabelResponse(BaseModel):
    id: str
    name: str
    type: str
    message_count: int | None = None


# ── Endpoints ────────────────────────────────

@router.get("", response_model=MessageListResponse)
async def list_messages(
    user_id: str = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = Query(None, description="Search in subject/from/snippet"),
    label: str | None = Query(None, description="Filter by Gmail label"),
    db: AsyncSession = Depends(get_db),
):
    """List synced messages with pagination and optional filtering."""
    query = select(Message).where(Message.user_id == UUID(user_id))

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Message.subject.ilike(search_filter))
            | (Message.from_header.ilike(search_filter))
            | (Message.snippet.ilike(search_filter))
        )

    if label:
        query = query.where(Message.label_ids.any(label))

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = (
        query.order_by(Message.internal_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    messages = result.scalars().all()

    return MessageListResponse(
        messages=[
            MessageResponse(
                id=str(m.id),
                gmail_message_id=m.gmail_message_id,
                thread_id=m.thread_id,
                internal_date=m.internal_date.isoformat() if m.internal_date else None,
                from_header=m.from_header,
                to_header=m.to_header,
                subject=m.subject,
                snippet=m.snippet,
                label_ids=m.label_ids,
                is_read=m.is_read,
                has_attachments=m.has_attachments,
            )
            for m in messages
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/sync/status", response_model=SyncStatusResponse)
async def sync_status(
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Get the current sync status."""
    from app.services.sync_service import SyncService

    svc = SyncService(db)
    status = await svc.get_sync_status(user_id)
    return SyncStatusResponse(**status)


@router.post("/sync", response_model=SyncTriggerResponse)
async def trigger_sync(
    user_id: str = Query(...),
    days: int = Query(None, ge=1, le=3650),
    incremental: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a mailbox sync (initial or incremental)."""
    from app.services.sync_service import SyncService

    svc = SyncService(db)

    try:
        if incremental:
            result = await svc.incremental_sync(user_id)
        else:
            result = await svc.initial_sync(user_id, days=days)

        return SyncTriggerResponse(
            status=result["status"],
            message=f"Sync completed. {result.get('messages_synced', result.get('new_messages', 0))} messages processed.",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/labels", response_model=list[GmailLabelResponse])
async def list_gmail_labels(
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """List all Gmail labels (system + user) for the connected account."""
    from app.services.auth_service import AuthService
    from app.services.gmail_service import GmailService

    auth = AuthService(db)
    creds = await auth.get_credentials(user_id)
    if creds is None:
        raise HTTPException(status_code=401, detail="Gmail not connected")

    gmail = GmailService(creds)
    labels = gmail.list_labels()

    return [
        GmailLabelResponse(
            id=lbl.id,
            name=lbl.name,
            type=lbl.type,
            message_count=lbl.message_count,
        )
        for lbl in labels
    ]
