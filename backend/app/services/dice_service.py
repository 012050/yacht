"""Dice rolling and state management."""
import random


def roll_5_dice() -> list[int]:
    """Return a list of 5 random integers in [1, 6]."""
    return [random.randint(1, 6) for _ in range(5)]


def resolve_final_dice(
    current_values: list[int], kept_indices: list[int]
) -> list[int]:
    """Resolve the dice used for a timed-out turn.

    Kept dice stay as-is; the remaining dice are rolled once.
    If no values were rolled yet, all 5 dice are rolled fresh.
    """
    if not current_values:
        return roll_5_dice()
    kept_set = set(kept_indices)
    return [
        current_values[i] if i in kept_set else random.randint(1, 6)
        for i in range(5)
    ]


def validate_keep_indices(indices: list[int], num_dice: int) -> bool:
    """Validate that keep indices are valid for the current dice count."""
    if not indices:
        return True
    if len(indices) > num_dice:
        return False
    for idx in indices:
        if idx < 0 or idx >= num_dice:
            return False
    if len(indices) != len(set(indices)):
        return False
    return True
