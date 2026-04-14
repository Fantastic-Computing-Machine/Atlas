"""FastAPI application entry-point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup — nothing heavy yet; DB tables created via Alembic.
    yield
    # Shutdown — dispose the engine pool.
    from app.database import engine

    await engine.dispose()


app = FastAPI(
    title="Atlas",
    description="AI-powered Gmail control layer — organize & research your inbox.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────
from app.api.auth import router as auth_router  # noqa: E402
from app.api.messages import router as messages_router  # noqa: E402
from app.api.scopes import router as scopes_router  # noqa: E402

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(scopes_router, prefix="/api/scopes", tags=["Scopes"])
app.include_router(messages_router, prefix="/api/messages", tags=["Messages"])


@app.get("/api/health", tags=["System"])
async def health_check():
    """Basic health check."""
    return {"status": "ok", "service": "atlas"}
