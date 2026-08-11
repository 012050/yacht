"""
??? ???/?? ??
"""

import random


def roll_dice(count: int) -> list[int]:
    """5? ???? ?? 1~6? ?? ??? ??"""
    return [random.randint(1, 6) for _ in range(count)]


class DiceState:
    def __init__(self):
        self.dice: list[int] = []
        self.kept_indices: set[int] = set()
        self.rolls_left: int = 3

    def roll(self) -> list[int]:
        """?? ???? ??"""
        if self.rolls_left <= 0:
            raise ValueError("?? ??? ?? ?????.")

        unrolled_count = 5 - len(self.kept_indices)
        if self.dice:
            # ? ???? ?? ??: ???? ?? ???? ???
            new_rolls = roll_dice(unrolled_count)
            new_dice = []
            new_idx = 0
            for i in range(5):
                if i in self.kept_indices:
                    new_dice.append(self.dice[i])
                else:
                    new_dice.append(new_rolls[new_idx])
                    new_idx += 1
            self.dice = new_dice
        else:
            # ? ???
            self.dice = roll_dice(5)

        self.rolls_left -= 1
        return self.dice[:]

    def keep(self, indices: list[int]) -> None:
        """??? ??? ??? ?? (0~4)"""
        for idx in indices:
            if idx < 0 or idx > 4:
                raise ValueError(f"???? ?? ??? ???: {idx}")
        self.kept_indices = set(indices)

    def reset(self) -> None:
        """? ?? ?? ?? ???"""
        self.dice = []
        self.kept_indices = set()
        self.rolls_left = 3

    def finish_early(self) -> list[int]:
        """?? ??: ?? ??? ?? (?? ?? ?? ? ?)"""
        return self.dice[:]

    @property
    def is_exhausted(self) -> bool:
        return self.rolls_left <= 0 and len(self.dice) == 5
