"""In-memory per-game turn timer and dice tracking.

Tracks the dice state of the current turn (so a timeout can auto-play with
the real dice) and schedules an asyncio timeout task per game.

State is in-memory: a server restart drops pending timers, but every turn
advance re-schedules the timer, so the next turn is still enforced.
"""
import asyncio
import logging
from typing import Awaitable, Callable, Optional

logger = logging.getLogger(__name__)


class TurnTimer:
    """Schedules turn timeout callbacks keyed by game_id."""

    def __init__(self) -> None:
        self._tasks: dict[str, asyncio.Task] = {}
        self.turn_states: dict[str, dict] = {}

    # ── Turn dice state ────────────────────────────────────────────────

    def record_roll(
        self,
        game_id: str,
        user_id: str,
        values: list[int],
        kept_indices: list[int],
        rolls_remaining: int,
    ) -> None:
        """Store the latest dice state for the current turn."""
        self.turn_states[game_id] = {
            "user_id": user_id,
            "values": list(values),
            "kept_indices": list(kept_indices),
            "rolls_remaining": rolls_remaining,
        }

    def get_turn_state(self, game_id: str) -> Optional[dict]:
        return self.turn_states.get(game_id)

    def clear_turn(self, game_id: str) -> None:
        self.turn_states.pop(game_id, None)

    # ── Timeout scheduling ─────────────────────────────────────────────

    def cancel(self, game_id: str) -> None:
        task = self._tasks.pop(game_id, None)
        if task is not None and not task.done():
            task.cancel()

    def schedule_turn(
        self,
        game_id: str,
        delay_seconds: float,
        on_timeout: Callable[[], Awaitable[None]],
    ) -> None:
        """Cancel any pending timer and schedule a new one."""
        self.cancel(game_id)

        async def _runner() -> None:
            try:
                await asyncio.sleep(delay_seconds)
            except asyncio.CancelledError:
                return
            self._tasks.pop(game_id, None)
            try:
                await on_timeout()
            except Exception:
                logger.exception(
                    "Turn timeout handler failed for game %s", game_id
                )

        self._tasks[game_id] = asyncio.create_task(_runner())

    def cancel_all(self) -> None:
        for game_id in list(self._tasks):
            self.cancel(game_id)


# Module-level singleton shared by the WebSocket layer and HTTP routes.
turn_timer = TurnTimer()
