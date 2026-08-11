import asyncio
from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded

from app.database.db import init_db
from app.api.routes import auth, users, games, websocket
from app.services.security_service import limiter, handle_rate_limit_exceeded
from app.services.game_service import game_service

app = FastAPI(title="Yacht Dice Game API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, handle_rate_limit_exceeded)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(games.router)
app.include_router(websocket.router)

async def check_timers():
    while True:
        await asyncio.sleep(1)
        for game_id, gs in list(game_service._games.items()):
            if gs.state == "playing" and gs.turn_start_time:
                from datetime import datetime, timezone
                elapsed = (datetime.now(timezone.utc) - gs.turn_start_time).total_seconds()
                if elapsed >= gs.timeout_duration:
                    await game_service.handle_auto_timeout(game_id)

@app.on_event("startup")
def startup():
    init_db()
    asyncio.create_task(check_timers())

@app.get("/health")
def health():
    return {"status": "ok"}
