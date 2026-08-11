"""
12? ???? + ??? ?? ???
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.scoring import (
    score_numbers,
    score_yacht,
    score_four_of_a_kind,
    score_full_house,
    score_small_straight,
    score_large_straight,
    score_chance,
    calculate_score,
    calculate_best_category,
    calculate_bonus,
    calculate_total,
    CATEGORIES,
    TOP_CATEGORIES,
    BOTTOM_CATEGORIES,
)


# --- ??? ???? ---

def test_score_numbers_ones():
    assert score_numbers([1, 1, 3, 5, 6], 1) == 2
    assert score_numbers([1, 1, 1, 1, 1], 1) == 5
    assert score_numbers([2, 3, 4, 5, 6], 1) == 0


def test_score_numbers_twos():
    assert score_numbers([2, 2, 2, 4, 6], 2) == 6
    assert score_numbers([1, 3, 4, 5, 6], 2) == 0


def test_score_numbers_fours():
    assert score_numbers([4, 4, 4, 4, 5], 4) == 16


def test_score_numbers_fives():
    assert score_numbers([1, 5, 5, 5, 5], 5) == 20


def test_score_numbers_sixes():
    assert score_numbers([6, 6, 6, 6, 6], 6) == 30


# --- ?? ---

def test_score_yacht_valid():
    assert score_yacht([3, 3, 3, 3, 3]) == 50
    assert score_yacht([1, 1, 1, 1, 1]) == 50
    assert score_yacht([6, 6, 6, 6, 6]) == 50


def test_score_yacht_invalid():
    assert score_yacht([6, 6, 6, 6, 2]) == 0
    assert score_yacht([1, 2, 3, 4, 5]) == 0


# --- ? ? ?? ? ---

def test_score_four_of_a_kind_valid():
    assert score_four_of_a_kind([4, 4, 4, 4, 2]) == 17
    assert score_four_of_a_kind([6, 6, 6, 6, 6]) == 31  # ??? ??


def test_score_four_of_a_kind_invalid():
    assert score_four_of_a_kind([1, 3, 4, 5, 6]) == 0
    assert score_four_of_a_kind([1, 1, 1, 2, 2]) == 0


# --- ???? ---

def test_score_full_house_valid():
    assert score_full_house([2, 2, 3, 3, 3]) == 25
    assert score_full_house([5, 5, 1, 1, 1]) == 25


def test_score_full_house_invalid():
    assert score_full_house([1, 2, 3, 4, 5]) == 0
    assert score_full_house([1, 1, 1, 1, 2]) == 0  # ? ? ?? ?? ??


# --- ?? ????? ---

def test_score_small_straight_valid():
    assert score_small_straight([1, 2, 3, 4, 6]) == 30
    assert score_small_straight([2, 3, 4, 5, 5]) == 30
    assert score_small_straight([1, 2, 3, 4, 5]) == 30  # ?? ?????? ??


def test_score_small_straight_invalid():
    # [1,3,4,5,6] is actually valid: contains 3,4,5,6 consecutive -> 30
    assert score_small_straight([1, 1, 2, 2, 3]) == 0
    assert score_small_straight([1, 1, 1, 1, 1]) == 0
    assert score_small_straight([1, 1, 1, 1, 1]) == 0


# --- ?? ????? ---

def test_score_large_straight_valid():
    assert score_large_straight([1, 2, 3, 4, 5]) == 40
    assert score_large_straight([2, 3, 4, 5, 6]) == 40


def test_score_large_straight_invalid():
    assert score_large_straight([1, 2, 3, 4, 6]) == 0
    assert score_large_straight([1, 1, 1, 1, 1]) == 0


# --- ?? ---

def test_score_chance():
    assert score_chance([3, 4, 2, 5, 6]) == 20
    assert score_chance([1, 1, 1, 1, 1]) == 5
    assert score_chance([6, 6, 6, 6, 6]) == 30


# --- calculate_score ?? ---

def test_calculate_score_all_categories():
    dice = [3, 3, 3, 3, 5]
    assert calculate_score(dice, "3") == 12
    assert calculate_score(dice, "5") == 5
    assert calculate_score(dice, "yacht") == 0
    assert calculate_score(dice, "four_of_a_kind") == 13  # 3*4+1
    assert calculate_score(dice, "full_house") == 0
    assert calculate_score(dice, "chance") == 17


def test_calculate_score_invalid_category():
    import pytest
    with pytest.raises(ValueError):
        calculate_score([1, 2, 3, 4, 5], "invalid")


# --- ??? ---

def test_calculate_bonus():
    scores = {"1": 5, "2": 6, "3": 9, "4": 8, "5": 10, "6": 25}
    # ?? = 63 -> ???
    assert calculate_bonus(scores) == 35

    scores2 = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0}
    assert calculate_bonus(scores2) == 0

    scores3 = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 62}
    # ?? = 77 >= 63
    assert calculate_bonus(scores3) == 35


# --- ?? ---

def test_calculate_total():
    scores = {"1": 5, "2": 6, "3": 9, "4": 8, "5": 10, "6": 25,
              "yacht": 50, "four_of_a_kind": 0, "full_house": 0,
              "small_straight": 0, "large_straight": 0, "chance": 15}
    top = 5 + 6 + 9 + 8 + 10 + 25  # 63
    bottom = 50 + 0 + 0 + 0 + 0 + 15  # 65
    bonus = 35
    assert calculate_total(scores) == top + bottom + bonus


# --- calculate_best_category ---

def test_calculate_best_category():
    dice = [6, 6, 6, 6, 6]
    used = set()
    cat, score = calculate_best_category(dice, used)
    assert cat == "yacht"
    assert score == 50


def test_calculate_best_category_with_used():
    dice = [6, 6, 6, 6, 6]
    used = {"yacht", "six", "6"}
    cat, score = calculate_best_category(dice, used)
    assert score > 0  # ???


def test_calculate_best_category_all_used():
    dice = [1, 2, 3, 4, 5]
    used = set(CATEGORIES)
    result = calculate_best_category(dice, used)
    assert result is None


# --- ?? ??? ---

def test_boundary_all_ones():
    dice = [1, 1, 1, 1, 1]
    assert calculate_score(dice, "yacht") == 50
    assert calculate_score(dice, "four_of_a_kind") == 6  # 1*5+1
    assert calculate_score(dice, "full_house") == 0
    assert calculate_score(dice, "large_straight") == 0
    assert calculate_score(dice, "chance") == 5


def test_boundary_all_sixes():
    dice = [6, 6, 6, 6, 6]
    assert calculate_score(dice, "yacht") == 50
    assert calculate_score(dice, "four_of_a_kind") == 31
    assert calculate_score(dice, "6") == 30
    assert calculate_score(dice, "chance") == 30


def test_boundary_straight_edge():
    dice = [1, 2, 3, 4, 6]
    assert calculate_score(dice, "small_straight") == 30
    assert calculate_score(dice, "large_straight") == 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
