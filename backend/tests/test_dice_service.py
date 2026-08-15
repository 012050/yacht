"""Test dice rolling and keeping logic."""
import pytest
from app.services.dice_service import (
    roll_5_dice,
    resolve_final_dice,
    validate_keep_indices,
)


class TestRollDice:
    def test_roll_returns_five(self):
        dice = roll_5_dice()
        assert len(dice) == 5

    def test_roll_values_in_range(self):
        dice = roll_5_dice()
        for d in dice:
            assert 1 <= d <= 6

    def test_multiple_rolls_differ(self):
        rolls = [roll_5_dice() for _ in range(100)]
        # Statistically they should not all be identical
        assert len(set(map(tuple, rolls))) > 1


class TestResolveFinalDice:
    def test_no_values_rolls_all_five(self):
        dice = resolve_final_dice([], [])
        assert len(dice) == 5
        for d in dice:
            assert 1 <= d <= 6

    def test_kept_dice_preserved(self):
        values = [3, 1, 5, 2, 6]
        dice = resolve_final_dice(values, [0, 2])
        assert dice[0] == 3
        assert dice[2] == 5
        assert len(dice) == 5

    def test_unkept_dice_rerolled_in_range(self):
        values = [4, 4, 4, 1, 2]
        for _ in range(50):
            dice = resolve_final_dice(values, [0, 1, 2])
            for i in (0, 1, 2):
                assert dice[i] == 4
            for i in (3, 4):
                assert 1 <= dice[i] <= 6

    def test_all_kept_returns_same_values(self):
        values = [2, 5, 1, 6, 3]
        dice = resolve_final_dice(values, [0, 1, 2, 3, 4])
        assert dice == values


class TestValidateKeep:
    def test_valid_indices(self):
        assert validate_keep_indices([0, 2, 4], 5) is True
        assert validate_keep_indices([], 5) is True
        assert validate_keep_indices([0], 5) is True

    def test_invalid_index_out_of_range(self):
        assert validate_keep_indices([5], 5) is False
        assert validate_keep_indices([-1], 5) is False

    def test_invalid_duplicate_indices(self):
        assert validate_keep_indices([0, 0], 5) is False
