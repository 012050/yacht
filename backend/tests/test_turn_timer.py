"""Test the in-memory turn timer."""
import asyncio

import pytest

from app.services.turn_timer import TurnTimer


async def _mark(bucket: list) -> None:
    bucket.append(1)


@pytest.fixture
def timer():
    t = TurnTimer()
    yield t
    t.cancel_all()


class TestTurnState:
    def test_record_and_get(self, timer):
        timer.record_roll("g1", "u1", [1, 2, 3, 4, 5], [0, 1], 1)
        state = timer.get_turn_state("g1")
        assert state["user_id"] == "u1"
        assert state["values"] == [1, 2, 3, 4, 5]
        assert state["kept_indices"] == [0, 1]
        assert state["rolls_remaining"] == 1

    def test_clear_turn(self, timer):
        timer.record_roll("g1", "u1", [1, 2, 3, 4, 5], [], 2)
        timer.clear_turn("g1")
        assert timer.get_turn_state("g1") is None

    def test_missing_state(self, timer):
        assert timer.get_turn_state("nope") is None


class TestScheduling:
    def test_callback_fires_after_delay(self, timer):
        async def scenario():
            fired = []
            timer.schedule_turn("g1", 0.05, lambda: _mark(fired))
            await asyncio.sleep(0.2)
            assert len(fired) == 1

        asyncio.run(scenario())

    def test_cancel_prevents_fire(self, timer):
        async def scenario():
            fired = []
            timer.schedule_turn("g1", 0.05, lambda: _mark(fired))
            timer.cancel("g1")
            await asyncio.sleep(0.15)
            assert fired == []

        asyncio.run(scenario())

    def test_reschedule_replaces_pending(self, timer):
        async def scenario():
            fired = []
            timer.schedule_turn("g1", 0.1, lambda: _mark(fired))
            timer.schedule_turn("g1", 0.05, lambda: _mark(fired))
            await asyncio.sleep(0.25)
            assert len(fired) == 1

        asyncio.run(scenario())

    def test_handler_exception_does_not_propagate(self, timer):
        async def scenario():
            async def boom():
                raise RuntimeError("boom")

            timer.schedule_turn("g1", 0.02, lambda: boom())
            await asyncio.sleep(0.1)  # must not raise

        asyncio.run(scenario())

    def test_cancel_all(self, timer):
        async def scenario():
            fired = []
            timer.schedule_turn("g1", 0.05, lambda: _mark(fired))
            timer.schedule_turn("g2", 0.05, lambda: _mark(fired))
            timer.cancel_all()
            await asyncio.sleep(0.15)
            assert fired == []

        asyncio.run(scenario())
