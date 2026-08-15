"""Pure scoring functions for Yacht. Follows game-rules.md exactly."""
from collections import Counter
from typing import Tuple

from sqlalchemy.orm import Session

from app.database.models import Scoreboard

CATEGORIES = [
    "ones", "twos", "threes", "fours", "fives", "sixes",
    "yacht", "four_of_a_kind", "full_house",
    "small_straight", "large_straight", "chance",
]

UPPER_CATEGORIES = ["ones", "twos", "threes", "fours", "fives", "sixes"]
LOWER_CATEGORIES = [
    "yacht", "four_of_a_kind", "full_house",
    "small_straight", "large_straight", "chance",
]


# ── Upper section ─────────────────────────────────────────────────────

def calculate_ones(dice: list[int]) -> int:
    return dice.count(1) * 1


def calculate_twos(dice: list[int]) -> int:
    return dice.count(2) * 2


def calculate_threes(dice: list[int]) -> int:
    return dice.count(3) * 3


def calculate_fours(dice: list[int]) -> int:
    return dice.count(4) * 4


def calculate_fives(dice: list[int]) -> int:
    return dice.count(5) * 5


def calculate_sixes(dice: list[int]) -> int:
    return dice.count(6) * 6


# ── Lower section ─────────────────────────────────────────────────────

def calculate_yacht(dice: list[int]) -> int:
    return 50 if len(set(dice)) == 1 else 0


def calculate_four_of_a_kind(dice: list[int]) -> int:
    """If any eye appears >= 4 times: sum of ALL matching dice + 1, else 0."""
    counts = Counter(dice)
    for eye, count in counts.items():
        if count >= 4:
            return eye * count + 1
    return 0


def calculate_full_house(dice: list[int]) -> int:
    """3 of one eye + 2 of another eye = 25, else 0."""
    counts = sorted(Counter(dice).values())
    return 25 if counts == [2, 3] else 0


def calculate_small_straight(dice: list[int]) -> int:
    """4 consecutive unique values = 30, else 0."""
    unique = sorted(set(dice))
    consecutive_run = 1
    max_run = 1
    for i in range(1, len(unique)):
        if unique[i] == unique[i - 1] + 1:
            consecutive_run += 1
            max_run = max(max_run, consecutive_run)
        else:
            consecutive_run = 1
    return 30 if max_run >= 4 else 0


def calculate_large_straight(dice: list[int]) -> int:
    """5 consecutive unique values (1-5 or 2-6) = 40, else 0."""
    unique = sorted(set(dice))
    if unique == [1, 2, 3, 4, 5] or unique == [2, 3, 4, 5, 6]:
        return 40
    return 0


def calculate_chance(dice: list[int]) -> int:
    return sum(dice)


# ── Dispatch map ──────────────────────────────────────────────────────

CATEGORY_MAP = {
    "ones": calculate_ones,
    "twos": calculate_twos,
    "threes": calculate_threes,
    "fours": calculate_fours,
    "fives": calculate_fives,
    "sixes": calculate_sixes,
    "yacht": calculate_yacht,
    "four_of_a_kind": calculate_four_of_a_kind,
    "full_house": calculate_full_house,
    "small_straight": calculate_small_straight,
    "large_straight": calculate_large_straight,
    "chance": calculate_chance,
}


def calculate_score(category: str, dice: list[int]) -> int:
    """Dispatch to the correct scoring function for a category."""
    func = CATEGORY_MAP.get(category)
    if func is None:
        raise ValueError(f"Unknown category: {category}")
    return func(dice)


# ── Bonus ─────────────────────────────────────────────────────────────

def calculate_bonus(upper_total: int) -> int:
    """35 bonus if upper section total >= 63, else 0."""
    return 35 if upper_total >= 63 else 0


# ── Auto-select ───────────────────────────────────────────────────────

def auto_select_category(
    dice: list[int],
    user_id: str,
    game_id: str,
    session: Session,
) -> Tuple[str, int]:
    """Find the best available category for the current dice.

    Returns (category, score). If all categories are taken returns ("chance", 0).
    """
    used = {
        row.category
        for row in session.query(Scoreboard)
        .filter_by(game_id=game_id, user_id=user_id)
        .all()
    }

    best_category: str | None = None
    best_score = -1

    for cat in CATEGORIES:
        if cat in used:
            continue
        score = calculate_score(cat, dice)
        if score > best_score:
            best_score = score
            best_category = cat

    # All categories used — record 0 in chance as a fallback.
    if best_category is None:
        return "chance", 0

    return best_category, best_score
