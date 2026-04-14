"""Scopes API routes.

Endpoints:
- POST   /api/scopes            → create a scope
- GET    /api/scopes            → list scopes
- GET    /api/scopes/{id}       → get a scope
- PUT    /api/scopes/{id}       → update a scope
- DELETE /api/scopes/{id}       → delete a scope
- POST   /api/scopes/{id}/preview → preview messages in scope
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.scope import ScopeCreate, ScopePreview, ScopeResponse, ScopeUpdate
from app.services.scope_service import ScopeService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ScopeResponse, status_code=201)
async def create_scope(
    data: ScopeCreate,
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Create a new mailbox scope."""
    svc = ScopeService(db)
    scope = await svc.create(user_id, data)
    return scope


@router.get("", response_model=list[ScopeResponse])
async def list_scopes(
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """List all scopes for a user."""
    svc = ScopeService(db)
    return await svc.list_for_user(user_id)


@router.get("/{scope_id}", response_model=ScopeResponse)
async def get_scope(
    scope_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific scope."""
    svc = ScopeService(db)
    scope = await svc.get(scope_id)
    if scope is None:
        raise HTTPException(status_code=404, detail="Scope not found")
    return scope


@router.put("/{scope_id}", response_model=ScopeResponse)
async def update_scope(
    scope_id: str,
    data: ScopeUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a scope."""
    svc = ScopeService(db)
    scope = await svc.update(scope_id, data)
    if scope is None:
        raise HTTPException(status_code=404, detail="Scope not found")
    return scope


@router.delete("/{scope_id}", status_code=204)
async def delete_scope(
    scope_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a scope."""
    svc = ScopeService(db)
    deleted = await svc.delete(scope_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scope not found")


@router.post("/{scope_id}/preview", response_model=ScopePreview)
async def preview_scope(
    scope_id: str,
    user_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Preview messages matching a scope (queries Gmail live)."""
    svc = ScopeService(db)
    scope = await svc.get(scope_id)
    if scope is None:
        raise HTTPException(status_code=404, detail="Scope not found")

    # Compile scope to Gmail query
    gmail_params = svc.compile_to_gmail_query(scope)

    # Get credentials and query Gmail
    from app.services.auth_service import AuthService
    from app.services.gmail_service import GmailService

    auth = AuthService(db)
    creds = await auth.get_credentials(user_id)
    if creds is None:
        raise HTTPException(status_code=401, detail="Gmail not connected")

    gmail = GmailService(creds)
    message_refs = gmail.list_message_ids(
        query=gmail_params.get("q"),
        label_ids=gmail_params.get("labelIds"),
        max_results=50,
    )

    # Fetch subjects for sample
    sample_subjects = []
    if message_refs:
        sample_ids = [m["id"] for m in message_refs[:10]]
        messages = gmail.batch_get_messages(sample_ids, format="metadata")
        sample_subjects = [m.subject or "(no subject)" for m in messages]

    return ScopePreview(
        scope_id=scope.id,
        scope_name=scope.name,
        gmail_query=gmail_params.get("q") or "",
        estimated_count=len(message_refs),
        sample_subjects=sample_subjects,
    )
