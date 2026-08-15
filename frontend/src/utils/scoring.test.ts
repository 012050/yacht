import { describe, test, expect } from 'vitest';
/**
 * Frontend scoring tests - must match backend scoring.py exactly.
 * Per design.md cross-validation test requirement.
 */
import {
  calculateScore,
  calculateOnes,
  calculateTwos,
  calculateThrees,
  calculateFours,
  calculateFives,
  calculateSixes,
  calculateYacht,
  calculateFourOfAKind,
  calculateFullHouse,
  calculateSmallStraight,
  calculateLargeStraight,
  calculateChance,
  calculateBonus,
} from './scoring';
import type { Category } from '../types/game';

describe('Upper Section Scoring', () => {
  test('Ones: [1,1,3,5,6] = 2', () => {
    expect(calculateScore('ones' as Category, [1, 1, 3, 5, 6])).toBe(2);
  });

  test('Twos: [2,2,2,4,6] = 6', () => {
    expect(calculateScore('twos' as Category, [2, 2, 2, 4, 6])).toBe(6);
  });

  test('Threes: [3,3,5,6,6] = 6', () => {
    expect(calculateScore('threes' as Category, [3, 3, 5, 6, 6])).toBe(6);
  });

  test('Fours: [4,4,4,4,5] = 16', () => {
    expect(calculateScore('fours' as Category, [4, 4, 4, 4, 5])).toBe(16);
  });

  test('Fives: [1,5,5,5,5] = 20', () => {
    expect(calculateScore('fives' as Category, [1, 5, 5, 5, 5])).toBe(20);
  });

  test('Sixes: [6,6,6,6,6] = 30', () => {
    expect(calculateScore('sixes' as Category, [6, 6, 6, 6, 6])).toBe(30);
  });

  test('Ones with no ones = 0', () => {
    expect(calculateScore('ones' as Category, [2, 3, 4, 5, 6])).toBe(0);
  });
});

describe('Yacht', () => {
  test('[3,3,3,3,3] = 50', () => {
    expect(calculateYacht([3, 3, 3, 3, 3])).toBe(50);
  });

  test('[6,6,6,6,2] = 0', () => {
    expect(calculateYacht([6, 6, 6, 6, 2])).toBe(0);
  });

  test('[1,2,3,4,5] = 0', () => {
    expect(calculateYacht([1, 2, 3, 4, 5])).toBe(0);
  });
});

describe('Four of a Kind', () => {
  test('[4,4,4,4,2] = 17', () => {
    expect(calculateFourOfAKind([4, 4, 4, 4, 2])).toBe(17);
  });

  test('[6,6,6,6,6] = 31', () => {
    expect(calculateFourOfAKind([6, 6, 6, 6, 6])).toBe(31);
  });

  test('[1,3,4,5,6] = 0', () => {
    expect(calculateFourOfAKind([1, 3, 4, 5, 6])).toBe(0);
  });
});

describe('Full House', () => {
  test('[2,2,3,3,3] = 25', () => {
    expect(calculateFullHouse([2, 2, 3, 3, 3])).toBe(25);
  });

  test('[5,5,1,1,1] = 25', () => {
    expect(calculateFullHouse([5, 5, 1, 1, 1])).toBe(25);
  });

  test('[1,2,3,4,5] = 0', () => {
    expect(calculateFullHouse([1, 2, 3, 4, 5])).toBe(0);
  });

  test('[1,1,1,1,1] = 0 (all same is not full house)', () => {
    expect(calculateFullHouse([1, 1, 1, 1, 1])).toBe(0);
  });
});

describe('Small Straight', () => {
  test('[1,2,3,4,6] = 30', () => {
    expect(calculateSmallStraight([1, 2, 3, 4, 6])).toBe(30);
  });

  test('[2,3,4,5,5] = 30', () => {
    expect(calculateSmallStraight([2, 3, 4, 5, 5])).toBe(30);
  });

  test('[1,3,4,5,6] = 0', () => {
    expect(calculateSmallStraight([1, 3, 4, 5, 6])).toBe(30);
  });
});

describe('Large Straight', () => {
  test('[1,2,3,4,5] = 40', () => {
    expect(calculateLargeStraight([1, 2, 3, 4, 5])).toBe(40);
  });

  test('[2,3,4,5,6] = 40', () => {
    expect(calculateLargeStraight([2, 3, 4, 5, 6])).toBe(40);
  });

  test('[1,2,3,4,6] = 0', () => {
    expect(calculateLargeStraight([1, 2, 3, 4, 6])).toBe(0);
  });
});

describe('Chance', () => {
  test('[3,4,2,5,6] = 20', () => {
    expect(calculateChance([3, 4, 2, 5, 6])).toBe(20);
  });

  test('[1,1,1,1,1] = 5', () => {
    expect(calculateChance([1, 1, 1, 1, 1])).toBe(5);
  });
});

describe('Bonus', () => {
  test('upper total 63 -> bonus 35', () => {
    expect(calculateBonus(63)).toBe(35);
  });

  test('upper total 100 -> bonus 35', () => {
    expect(calculateBonus(100)).toBe(35);
  });

  test('upper total 62 -> bonus 0', () => {
    expect(calculateBonus(62)).toBe(0);
  });

  test('upper total 0 -> bonus 0', () => {
    expect(calculateBonus(0)).toBe(0);
  });
});

describe('Cross-validation: game-rules.md examples', () => {
  const examples: [Category, number[], number][] = [
    ['ones', [1, 1, 3, 5, 6], 2],
    ['twos', [2, 2, 2, 4, 6], 6],
    ['threes', [3, 3, 5, 6, 6], 6],
    ['fours', [4, 4, 4, 4, 5], 16],
    ['fives', [1, 5, 5, 5, 5], 20],
    ['sixes', [6, 6, 6, 6, 6], 30],
    ['yacht', [3, 3, 3, 3, 3], 50],
    ['four_of_a_kind', [4, 4, 4, 4, 2], 17],
    ['four_of_a_kind', [6, 6, 6, 6, 6], 31],
    ['full_house', [2, 2, 3, 3, 3], 25],
    ['small_straight', [1, 2, 3, 4, 6], 30],
    ['large_straight', [1, 2, 3, 4, 5], 40],
    ['chance', [3, 4, 2, 5, 6], 20],
  ];

  test.each(examples)('category %s with dice %j = %d', (category, dice, expected) => {
    expect(calculateScore(category, dice)).toBe(expected);
  });
});
