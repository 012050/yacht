import { Category, UPPER_CATEGORIES, LOWER_CATEGORIES, CATEGORIES } from '../types/game';

export function calculateOnes(dice: number[]): number {
  return dice.filter((v) => v === 1).length * 1;
}

export function calculateTwos(dice: number[]): number {
  return dice.filter((v) => v === 2).length * 2;
}

export function calculateThrees(dice: number[]): number {
  return dice.filter((v) => v === 3).length * 3;
}

export function calculateFours(dice: number[]): number {
  return dice.filter((v) => v === 4).length * 4;
}

export function calculateFives(dice: number[]): number {
  return dice.filter((v) => v === 5).length * 5;
}

export function calculateSixes(dice: number[]): number {
  return dice.filter((v) => v === 6).length * 6;
}

export function calculateYacht(dice: number[]): number {
  if (dice.length === 0) return 0;
  return dice.every((v) => v === dice[0]) ? 50 : 0;
}

export function calculateFourOfAKind(dice: number[]): number {
  const counts: Record<number, number> = {};
  for (const v of dice) counts[v] = (counts[v] || 0) + 1;
  for (const [valStr, count] of Object.entries(counts)) {
    if (count >= 4) {
      const val = parseInt(valStr, 10);
      return val * count + 1;
    }
  }
  return 0;
}

export function calculateFullHouse(dice: number[]): number {
  const counts: Record<number, number> = {};
  for (const v of dice) counts[v] = (counts[v] || 0) + 1;
  const uniqueCounts = Object.values(counts).sort((a, b) => b - a);
  return uniqueCounts.length === 2 && uniqueCounts[0] === 3 && uniqueCounts[1] === 2 ? 25 : 0;
}

export function calculateSmallStraight(dice: number[]): number {
  const unique = [...new Set(dice)].sort((a, b) => a - b);
  let consecutive = 1;
  let maxConsecutive = 1;
  for (let i = 1; i < unique.length; i++) {
    if (unique[i] === unique[i - 1] + 1) {
      consecutive++;
      if (consecutive > maxConsecutive) maxConsecutive = consecutive;
    } else {
      consecutive = 1;
    }
  }
  return maxConsecutive >= 4 ? 30 : 0;
}

export function calculateLargeStraight(dice: number[]): number {
  const unique = [...new Set(dice)].sort((a, b) => a - b);
  if (unique.length !== 5) return 0;
  for (let i = 1; i < unique.length; i++) {
    if (unique[i] !== unique[i - 1] + 1) return 0;
  }
  return 40;
}

export function calculateChance(dice: number[]): number {
  return dice.reduce((sum, v) => sum + v, 0);
}

export function calculateScore(category: Category, dice: number[]): number {
  switch (category) {
    case 'ones': return calculateOnes(dice);
    case 'twos': return calculateTwos(dice);
    case 'threes': return calculateThrees(dice);
    case 'fours': return calculateFours(dice);
    case 'fives': return calculateFives(dice);
    case 'sixes': return calculateSixes(dice);
    case 'yacht': return calculateYacht(dice);
    case 'four_of_a_kind': return calculateFourOfAKind(dice);
    case 'full_house': return calculateFullHouse(dice);
    case 'small_straight': return calculateSmallStraight(dice);
    case 'large_straight': return calculateLargeStraight(dice);
    case 'chance': return calculateChance(dice);
  }
}

export function calculateBonus(upperTotal: number): number {
  return upperTotal >= 63 ? 35 : 0;
}

export function getPotentialScores(
  dice: number[],
  takenCategories: Set<string>
): Record<string, number> {
  const scores: Record<string, number> = {};
  for (const cat of CATEGORIES) {
    if (!takenCategories.has(cat)) {
      scores[cat] = calculateScore(cat, dice);
    }
  }
  return scores;
}

export function getUpperTotal(scoreboard: { entries: { category: string; score: number }[] }): number {
  return UPPER_CATEGORIES.reduce((sum, cat) => {
    const entry = scoreboard.entries.find((e) => e.category === cat);
    return sum + (entry ? entry.score : 0);
  }, 0);
}

export function getLowerTotal(scoreboard: { entries: { category: string; score: number }[] }): number {
  return LOWER_CATEGORIES.reduce((sum, cat) => {
    const entry = scoreboard.entries.find((e) => e.category === cat);
    return sum + (entry ? entry.score : 0);
  }, 0);
}
