"""
??? ???/?? ?? ???
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.dice_service import DiceState


def test_first_roll():
    ds = DiceState()
    dice = ds.roll()
    assert len(dice) == 5
    assert all(1 <= d <= 6 for d in dice)
    assert ds.rolls_left == 2


def test_keep_and_reroll():
    ds = DiceState()
    ds.roll()  # first roll
    ds.keep([0, 2])  # keep index 0 and 2
    dice2 = ds.roll()
    assert len(dice2) == 5
    assert ds.rolls_left == 1


def test_three_rolls_exhausted():
    ds = DiceState()
    ds.roll()
    ds.keep([0])
    ds.roll()
    ds.keep([0, 1])
    ds.roll()
    assert ds.rolls_left == 0
    assert len(ds.dice) == 5


def test_cannot_roll_after_exhausted():
    ds = DiceState()
    ds.roll()
    ds.roll()
    ds.roll()
    import pytest
    with pytest.raises(ValueError):
        ds.roll()


def test_reset():
    ds = DiceState()
    ds.roll()
    ds.keep([0, 1])
    ds.roll()
    ds.reset()
    assert ds.dice == []
    assert ds.kept_indices == set()
    assert ds.rolls_left == 3


def test_invalid_keep_index():
    ds = DiceState()
    import pytest
    with pytest.raises(ValueError):
        ds.keep([5])
    with pytest.raises(ValueError):
        ds.keep([-1])


def test_finish_early():
    ds = DiceState()
    ds.roll()
    ds.keep([0, 1])
    result = ds.finish_early()
    assert len(result) == 5


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
