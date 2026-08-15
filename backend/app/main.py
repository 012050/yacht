"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.database.db import Base, engine
from app.services.security_service import limiter

# ── Lifespan: create tables on startup ────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Create all tables on startup.
    Base.metadata.create_all(bind=engine)
    yield


# ── App creation ──────────────────────────────────────────────────────

app = FastAPI(
    title="Yacht Dice Game API",
    description="Backend API for the Yacht (Yahtzee) dice game",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS middleware ───────────────────────────────────────────────────
# Same-origin deployments (Vite proxy / Docker) need no CORS; the list
# covers local development frontends by default.

def _cors_origins() -> list[str]:
    configured = [
        origin.strip()
        for origin in settings.CORS_ORIGINS.split(",")
        if origin.strip()
    ]
    return configured or [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ──────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# ── Register routers ─────────────────────────────────────────────────

from app.api.routes import auth, games, users, websocket  # noqa: E402

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(games.router)
app.include_router(websocket.router)
