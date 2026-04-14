"""Scope service — CRUD and Gmail query compilation."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scope import Scope
from app.schemas.scope import ScopeCreate, ScopeUpdate

logger = logging.getLogger(__name__)


class ScopeService:
    """Manage mailbox scope objects."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: str, data: ScopeCreate) -> Scope:
        """Create a new scope."""
        scope = Scope(
            user_id=UUID(user_id),
            name=data.name,
            include_system_labels=data.include_system_labels,
            exclude_system_labels=data.exclude_system_labels,
            include_user_labels=data.include_user_labels,
            exclude_user_labels=data.exclude_user_labels,
            default_date_window=data.default_date_window,
        )
        self.db.add(scope)
        await self.db.flush()
        return scope

    async def get(self, scope_id: str) -> Scope | None:
        """Fetch a scope by ID."""
        result = await self.db.execute(
            select(Scope).where(Scope.id == UUID(scope_id))
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: str) -> list[Scope]:
        """List all scopes for a user."""
        result = await self.db.execute(
            select(Scope)
            .where(Scope.user_id == UUID(user_id))
            .order_by(Scope.created_at.desc())
        )
        return list(result.scalars().all())

    async def update(self, scope_id: str, data: ScopeUpdate) -> Scope | None:
        """Update an existing scope."""
        scope = await self.get(scope_id)
        if scope is None:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(scope, field, value)

        await self.db.flush()
        return scope

    async def delete(self, scope_id: str) -> bool:
        """Delete a scope."""
        scope = await self.get(scope_id)
        if scope is None:
            return False
        await self.db.delete(scope)
        await self.db.flush()
        return True

    def compile_to_gmail_query(
        self,
        scope: Scope,
        additional_query: str | None = None,
        date_override_days: int | None = None,
    ) -> dict:
        """Compile a Scope into Gmail API query parameters.

        Returns:
            Dict with 'q' (query string) and 'labelIds' list.
        """
        query_parts: list[str] = []
        label_ids: list[str] = []

        # Include system labels become labelIds filter
        if scope.include_system_labels:
            label_ids.extend(scope.include_system_labels)

        # Exclude system labels as negative query
        if scope.exclude_system_labels:
            for lbl in scope.exclude_system_labels:
                # Convert system label to search syntax
                # e.g. CATEGORY_PROMOTIONS → -category:promotions
                if lbl.startswith("CATEGORY_"):
                    category = lbl.replace("CATEGORY_", "").lower()
                    query_parts.append(f"-category:{category}")
                else:
                    query_parts.append(f"-label:{lbl.lower()}")

        # Include user labels
        if scope.include_user_labels:
            label_ids.extend(scope.include_user_labels)

        # Exclude user labels
        if scope.exclude_user_labels:
            for lbl in scope.exclude_user_labels:
                query_parts.append(f"-label:{lbl}")

        # Date window — use epoch seconds for timezone precision
        days = date_override_days or scope.default_date_window
        if days:
            since = datetime.now(timezone.utc) - timedelta(days=days)
            epoch_seconds = int(since.timestamp())
            query_parts.append(f"after:{epoch_seconds}")

        # Additional query
        if additional_query:
            query_parts.append(additional_query)

        return {
            "q": " ".join(query_parts) if query_parts else None,
            "labelIds": label_ids if label_ids else None,
        }
