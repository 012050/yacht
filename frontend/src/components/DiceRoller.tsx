import { DiceState } from '../types/game';

interface DiceRollerProps {
  dice: DiceState;
  onRoll: () => void;
  onFinish: () => void;
  onToggleKeep: (index: number) => void;
  isMyTurn: boolean;
}

const dieFaces: Record<number, string[]> = {
  1: ['center'],
  2: ['top-right', 'bottom-left'],
  3: ['top-right', 'center', 'bottom-left'],
  4: ['top-left', 'top-right', 'bottom-left', 'bottom-right'],
  5: ['top-left', 'top-right', 'center', 'bottom-left', 'bottom-right'],
  6: ['top-left', 'top-right', 'middle-left', 'middle-right', 'bottom-left', 'bottom-right'],
};

function DieFace({ value, kept }: { value: number; kept: boolean }) {
  const dots = dieFaces[value] || [];
  return (
    <div
      className={`w-16 h-16 sm:w-20 sm:h-20 rounded-xl flex items-center justify-center grid grid-cols-3 grid-rows-3 gap-0.5 p-2 transition-all duration-300 ${
        kept
          ? 'bg-blue-600 border-2 border-blue-400 shadow-lg shadow-blue-500/30 scale-105'
          : 'bg-slate-100 border-2 border-slate-300'
      }`}
    >
      {Array.from({ length: 9 }).map((_, i) => {
        const position = ['top-left', 'top-center', 'top-right', 'middle-left', 'center', 'middle-right', 'bottom-left', 'bottom-center', 'bottom-right'][i];
        const hasDot = dots.includes(position);
        return (
          <div
            key={i}
            className={`rounded-full ${hasDot ? 'bg-slate-800 w-2.5 h-2.5 sm:w-3 sm:h-3' : 'w-2.5 h-2.5 sm:w-3 sm:h-3'}`}
          />
        );
      })}
    </div>
  );
}

export default function DiceRoller({
  dice,
  onRoll,
  onFinish,
  onToggleKeep,
  isMyTurn,
}: DiceRollerProps) {
  const values = dice.values || [];
  const keptIndices = dice.keptIndices || [];
  const rollsRemaining = dice.rollsRemaining ?? 3;

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">
          {isMyTurn ? 'Roll Dice' : 'Dice'}
        </h3>
        <div className="text-sm text-slate-400">
          Rolls remaining: <span className="text-blue-400 font-bold">{rollsRemaining}</span>
        </div>
      </div>

      {/* Dice */}
      <div className="flex justify-center gap-3 mb-6">
        {Array.from({ length: 5 }).map((_, i) => {
          const value = values[i] || 1;
          const kept = keptIndices.includes(i);
          return (
            <button
              key={i}
              onClick={() => {
                if (isMyTurn && rollsRemaining > 0) {
                  onToggleKeep(i);
                }
              }}
              disabled={!isMyTurn || rollsRemaining === 0}
              className={`transition-transform ${
                isMyTurn && rollsRemaining > 0 ? 'cursor-pointer hover:scale-110' : 'cursor-default'
              }`}
              title={kept ? 'Kept' : isMyTurn && rollsRemaining > 0 ? 'Click to keep' : ''}
            >
              <DieFace value={value} kept={kept} />
            </button>
          );
        })}
      </div>

      {/* Buttons - only show for current player */}
      {isMyTurn && (
        <div className="flex justify-center gap-3">
          {rollsRemaining > 0 && (
            <button
              onClick={onRoll}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
            >
              Roll
            </button>
          )}
          <button
            onClick={onFinish}
            className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg transition-colors"
          >
            Finish & Select
          </button>
        </div>
      )}
    </div>
  );
}
