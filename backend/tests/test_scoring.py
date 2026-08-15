"""Test all 12 scoring categories + bonus per game-rules.md."""
import pytest
from app.services.scoring import (
    calculate_ones,
    calculate_twos,
    calculate_threes,
    calculate_fours,
    calculate_fives,
    calculate_sixes,
    calculate_yacht,
    calculate_four_of_a_kind,
    calculate_full_house,
    calculate_small_straight,
    calculate_large_straight,
    calculate_chance,
    calculate_bonus,
    calculate_score,
    CATEGORIES,
)


# ── Upper section ─────────────────────────────────────────────────────

class TestUpperSection:
    def test_ones(self):
        assert calculate_ones([1, 1, 3, 5, 6]) == 2
        assert calculate_ones([1, 1, 1, 1, 1]) == 5
        assert calculate_ones([2, 3, 4, 5, 6]) == 0

    def test_twos(self):
        assert calculate_twos([2, 2, 2, 4, 6]) == 6
        assert calculate_twos([1, 3, 5, 6]) == 0

    def test_threes(self):
        assert calculate_threes([3, 3, 5, 6, 6]) == 6

    def test_fours(self):
        assert calculate_fours([4, 4, 4, 4, 5]) == 16

    def test_fives(self):
        assert calculate_fives([1, 5, 5, 5, 5]) == 20

    def test_sixes(self):
        assert calculate_sixes([6, 6, 6, 6, 6]) == 30

    def test_upper_dispatch(self):
        assert calculate_score("ones", [1, 1, 3]) == 2
        assert calculate_score("sixes", [6, 6, 6, 6, 6]) == 30


# ── Lower section ─────────────────────────────────────────────────────

class TestYacht:
    def test_yacht_match(self):
        assert calculate_yacht([3, 3, 3, 3, 3]) == 50
        assert calculate_yacht([6, 6, 6, 6, 6]) == 50
        assert calculate_yacht([1, 1, 1, 1, 1]) == 50

    def test_yacht_no_match(self):
        assert calculate_yacht([6, 6, 6, 6, 2]) == 0
        assert calculate_yacht([1, 2, 3, 4, 5]) == 0


class TestFourOfAKind:
    def test_four_match(self):
        assert calculate_four_of_a_kind([4, 4, 4, 4, 2]) == 17
        assert calculate_four_of_a_kind([1, 1, 1, 1, 6]) == 5

    def test_five_match_is_also_four(self):
        assert calculate_four_of_a_kind([6, 6, 6, 6, 6]) == 31

    def test_no_match(self):
        assert calculate_four_of_a_kind([1, 3, 4, 5, 6]) == 0
        assert calculate_four_of_a_kind([1, 1, 2, 2, 3]) == 0


class TestFullHouse:
    def test_full_house_match(self):
        assert calculate_full_house([2, 2, 3, 3, 3]) == 25
        assert calculate_full_house([5, 5, 1, 1, 1]) == 25
        assert calculate_full_house([6, 6, 6, 4, 4]) == 25

    def test_full_house_no_match(self):
        assert calculate_full_house([1, 2, 3, 4, 5]) == 0
        assert calculate_full_house([1, 1, 1, 1, 1]) == 0
        assert calculate_full_house([1, 1, 2, 3, 4]) == 0


class TestSmallStraight:
    def test_match(self):
        assert calculate_small_straight([1, 2, 3, 4, 6]) == 30
        assert calculate_small_straight([2, 3, 4, 5, 5]) == 30
        assert calculate_small_straight([2, 3, 4, 5, 6]) == 30
        # [1,3,4,5,6] has 3,4,5,6 = 4 consecutive
        assert calculate_small_straight([1, 3, 4, 5, 6]) == 30

    def test_no_match(self):
        assert calculate_small_straight([1, 1, 2, 4, 6]) == 0
        assert calculate_small_straight([1, 2, 4, 5, 6]) == 0
        assert calculate_small_straight([1, 1, 1, 1, 1]) == 0


class TestLargeStraight:
    def test_match(self):
        assert calculate_large_straight([1, 2, 3, 4, 5]) == 40
        assert calculate_large_straight([2, 3, 4, 5, 6]) == 40

    def test_no_match(self):
        assert calculate_large_straight([1, 2, 3, 4, 6]) == 0
        assert calculate_large_straight([1, 1, 3, 4, 5]) == 0


class TestChance:
    def test_chance(self):
        assert calculate_chance([3, 4, 2, 5, 6]) == 20
        assert calculate_chance([1, 1, 1, 1, 1]) == 5
        assert calculate_chance([6, 6, 6, 6, 6]) == 30


# ── Bonus ─────────────────────────────────────────────────────────────

class TestBonus:
    def test_bonus_applied(self):
        assert calculate_bonus(63) == 35
        assert calculate_bonus(100) == 35

    def test_bonus_not_applied(self):
        assert calculate_bonus(62) == 0
        assert calculate_bonus(30) == 0
        assert calculate_bonus(0) == 0


# ── Categories list ───────────────────────────────────────────────────

class TestCategories:
    def test_all_categories_present(self):
        expected = [
            "ones", "twos", "threes", "fours", "fives", "sixes",
            "yacht", "four_of_a_kind", "full_house",
            "small_straight", "large_straight", "chance",
        ]
        assert CATEGORIES == expected

    def test_unknown_category_raises(self):
        with pytest.raises(ValueError):
            calculate_score("unknown_cat", [1, 2, 3, 4, 5])


# ── Cross-validation cases ────────────────────────────────────────────

class TestCrossValidation:
    """Test cases from game-rules.md examples."""
    def test_game_rules_examples(self):
        assert calculate_score("ones", [1, 1, 3, 5, 6]) == 2
        assert calculate_score("twos", [2, 2, 2, 4, 6]) == 6
        assert calculate_score("threes", [3, 3, 5, 6, 6]) == 6
        assert calculate_score("fours", [4, 4, 4, 4, 5]) == 16
        assert calculate_score("fives", [1, 5, 5, 5, 5]) == 20
        assert calculate_score("sixes", [6, 6, 6, 6, 6]) == 30
        assert calculate_score("yacht", [3, 3, 3, 3, 3]) == 50
        assert calculate_score("four_of_a_kind", [4, 4, 4, 4, 2]) == 17
        assert calculate_score("four_of_a_kind", [6, 6, 6, 6, 6]) == 31
        assert calculate_score("full_house", [2, 2, 3, 3, 3]) == 25
        assert calculate_score("small_straight", [1, 2, 3, 4, 6]) == 30
        assert calculate_score("large_straight", [1, 2, 3, 4, 5]) == 40
        assert calculate_score("chance", [3, 4, 2, 5, 6]) == 20
