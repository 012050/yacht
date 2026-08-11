"""
12? ???? ?? ?? ??. ?? ??? ???? ???? ?????.
?? ??: game-rules.md ??
"""

from collections import Counter


def score_numbers(dice: list[int], number: int) -> int:
    """??? ????: ?? ?? ?? x ?? ??"""
    return dice.count(number) * number


def score_yacht(dice: list[int]) -> int:
    """??: 5?? ?? ??? 50?, ??? 0?"""
    return 50 if len(set(dice)) == 1 else 0


def score_four_of_a_kind(dice: list[int]) -> int:
    """? ? ?? ?: ?? ?? 4? ???? ?? ?? ??? ? + 1"""
    counts = Counter(dice)
    for face, count in counts.items():
        if count >= 4:
            return face * count + 1
    return 0


def score_full_house(dice: list[int]) -> int:
    """????: 3? + 2? ???? 25?"""
    counts = list(Counter(dice).values())
    if sorted(counts) == [2, 3]:
        return 25
    return 0


def score_small_straight(dice: list[int]) -> int:
    """?? ?????: 4? ?? ???? 30?"""
    unique = sorted(set(dice))
    for i in range(len(unique) - 3):
        if unique[i + 3] - unique[i] == 3 and all(
            unique[i + k] == unique[i] + k for k in range(4)
        ):
            return 30
    return 0


def score_large_straight(dice: list[int]) -> int:
    """?? ?????: 5? ???? 40?"""
    unique = sorted(set(dice))
    if len(unique) == 5 and unique[-1] - unique[0] == 4:
        return 40
    return 0


def score_chance(dice: list[int]) -> int:
    """??: ??? ?? ?"""
    return sum(dice)


CATEGORIES = [
    "1", "2", "3", "4", "5", "6",
    "yacht", "four_of_a_kind", "full_house",
    "small_straight", "large_straight", "chance",
]

SCORING_FUNCTIONS = {
    "1": lambda d: score_numbers(d, 1),
    "2": lambda d: score_numbers(d, 2),
    "3": lambda d: score_numbers(d, 3),
    "4": lambda d: score_numbers(d, 4),
    "5": lambda d: score_numbers(d, 5),
    "6": lambda d: score_numbers(d, 6),
    "yacht": score_yacht,
    "four_of_a_kind": score_four_of_a_kind,
    "full_house": score_full_house,
    "small_straight": score_small_straight,
    "large_straight": score_large_straight,
    "chance": score_chance,
}

TOP_CATEGORIES = {"1", "2", "3", "4", "5", "6"}
BOTTOM_CATEGORIES = {"yacht", "four_of_a_kind", "full_house", "small_straight", "large_straight", "chance"}


def calculate_score(dice: list[int], category: str) -> int:
    """??? ???? ????? ?? ??? ?????."""
    if category not in SCORING_FUNCTIONS:
        raise ValueError(f"???? ?? ????: {category}")
    return SCORING_FUNCTIONS[category](dice)


def calculate_best_category(dice: list[int], used_categories: set[str]) -> tuple[str, int] | None:
    """
    ?? ??? ???? ? ?? ?? ??? ?????.
    (???? ?? ???)
    """
    available = [c for c in CATEGORIES if c not in used_categories]
    if not available:
        return None

    best = None
    best_score = -1
    for cat in available:
        s = SCORING_FUNCTIONS[cat](dice)
        if s > best_score:
            best_score = s
            best = cat
        elif s == best_score and s > 0 and CATEGORIES.index(cat) < CATEGORIES.index(best):
            best = cat

    return (best, best_score) if best else (available[0], 0)


def calculate_bonus(scores: dict[str, int]) -> int:
    """?? ??? 63? ???? 35? ??? ??"""
    top_sum = sum(scores.get(c, 0) for c in TOP_CATEGORIES)
    return 35 if top_sum >= 63 else 0


def calculate_total(scores: dict[str, int]) -> int:
    """?? = ?? ?? + ?? ?? + ???"""
    top_sum = sum(scores.get(c, 0) for c in TOP_CATEGORIES)
    bottom_sum = sum(scores.get(c, 0) for c in BOTTOM_CATEGORIES)
    bonus = calculate_bonus(scores)
    return top_sum + bottom_sum + bonus
