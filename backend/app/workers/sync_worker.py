"""Sync worker — background tasks for Gmail synchronization."""

from __future__ import annotations

import asyncio
import logging

from app.workers import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine in a synchronous Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="atlas.sync.initial", max_retries=3)
def run_initial_sync(self, user_id: str, days: int | None = None):
    """Background task for initial mailbox sync."""
    from app.database import async_session_factory
    from app.services.sync_service import SyncService

    async def _sync():
        async with async_session_factory() as session:
            svc = SyncService(session)
            result = await svc.initial_sync(user_id, days=days)
            await session.commit()
            return result

    try:
        result = _run_async(_sync())
        logger.info(f"[SyncWorker] Initial sync completed for user={user_id}: {result}")
        return result
    except Exception as exc:
        logger.error(f"[SyncWorker] Initial sync failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, name="atlas.sync.incremental", max_retries=3)
def run_incremental_sync(self, user_id: str):
    """Background task for incremental sync."""
    from app.database import async_session_factory
    from app.services.sync_service import SyncService

    async def _sync():
        async with async_session_factory() as session:
            svc = SyncService(session)
            result = await svc.incremental_sync(user_id)
            await session.commit()
            return result

    try:
        result = _run_async(_sync())
        logger.info(f"[SyncWorker] Incremental sync completed: {result}")
        return result
    except Exception as exc:
        logger.error(f"[SyncWorker] Incremental sync failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))
