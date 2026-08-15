import { Category, CATEGORIES } from '../types/game';
import { calculateScore } from '../utils/scoring';

interface CategorySelectorProps {
  dice: number[];
  takenCategories: Set<string>;
  onSelect: (category: string) => void;
  onPass: () => void;
  isMyTurn: boolean;
}

const categoryLabels: Record<string, string> = {
  ones: 'Ones (1s)',
  twos: 'Twos (2s)',
  threes: 'Threes (3s)',
  fours: 'Fours (4s)',
  fives: 'Fives (5s)',
  sixes: 'Sixes (6s)',
  yacht: 'Yacht',
  four_of_a_kind: 'Four of a Kind',
  full_house: 'Full House',
  small_straight: 'Small Straight',
  large_straight: 'Large Straight',
  chance: 'Chance',
};

const UPPER = ['ones', 'twos', 'threes', 'fours', 'fives', 'sixes'];

// Simple die face renderer for the category selector
function DieFaceSmall({ value }: { value: number }) {
  // 3x3 grid cell indices (must match dieFaces in DiceRoller.tsx):
  //   1 2 3
  //   4 5 6
  //   7 8 9
  const dotValues: Record<number, number[]> = {
    1: [5],
    2: [3, 7],
    3: [3, 5, 7],
    4: [1, 3, 7, 9],
    5: [1, 3, 5, 7, 9],
    6: [1, 3, 4, 6, 7, 9],
  };
  const dots = dotValues[value] || [];
  return (
    <div className="w-9 h-9 rounded-lg bg-slate-100 border border-slate-300 flex items-center justify-center grid grid-cols-3 grid-rows-3 gap-0 p-1">
      {Array.from({ length: 9 }).map((_, i) => (
        <div key={i} className={dots.includes(i + 1) ? 'w-1.5 h-1.5 rounded-full bg-slate-800' : 'w-1.5 h-1.5'} />
      ))}
    </div>
  );
}

export default function CategorySelector({
  dice,
  takenCategories,
  onSelect,
  onPass,
  isMyTurn,
}: CategorySelectorProps) {
  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
      <h3 className="text-lg font-semibold text-white mb-1">Select Category</h3>
      <p className="text-sm text-slate-400 mb-3">
        Choose where to record your score, or pass for 0 points.
      </p>

      {/* Show current dice */}
      <div className="flex items-center gap-2 mb-4 p-3 bg-slate-700/50 rounded-lg">
        <span className="text-sm text-slate-400">Dice:</span>
        <div className="flex gap-1.5">
          {dice.map((v, i) => (
            <DieFaceSmall key={i} value={v} />
          ))}
        </div>
        <span className="ml-auto text-sm text-slate-400">[{dice.join(', ')}]</span>
      </div>

      {/* Upper section */}
      <div className="mb-4">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
          Upper Section
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {UPPER.map((cat) => {
            if (takenCategories.has(cat)) return null;
            const score = calculateScore(cat as Category, dice);
            return (
              <button
                key={cat}
                onClick={() => onSelect(cat)}
                disabled={!isMyTurn}
                className={`p-3 rounded-lg text-left transition-colors ${
                  score > 0
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <div className="text-sm font-medium">{categoryLabels[cat]}</div>
                <div className="text-lg font-bold">{score}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Lower section */}
      <div className="mb-4">
        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
          Lower Section
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {CATEGORIES.filter((c) => !UPPER.includes(c)).map((cat) => {
            if (takenCategories.has(cat)) return null;
            const score = calculateScore(cat as Category, dice);
            return (
              <button
                key={cat}
                onClick={() => onSelect(cat)}
                disabled={!isMyTurn}
                className={`p-3 rounded-lg text-left transition-colors ${
                  score > 0
                    ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                    : 'bg-slate-700 hover:bg-slate-600 text-slate-300'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <div className="text-sm font-medium">{categoryLabels[cat]}</div>
                <div className="text-lg font-bold">{score}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Pass button */}
      <button
        onClick={onPass}
        disabled={!isMyTurn}
        className="w-full py-3 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:cursor-not-allowed text-slate-300 font-medium rounded-lg transition-colors"
      >
        Pass (0 points)
      </button>
    </div>
  );
}
