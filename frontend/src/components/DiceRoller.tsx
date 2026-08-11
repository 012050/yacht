import { useGameStore } from "../store/gameStore";

export default function DiceRoller() {
  const gameState = useGameStore((s) => s.gameState);
  const { rollDice, finishRolls } = useGameStore();

  if (!gameState || gameState.state !== "playing") return null;

  const dice = gameState.dice || [];
  const rollsLeft = gameState.rolls_left;

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold text-slate-800">주사위</h2>
        <span className="text-sm text-slate-500">남은 횟수: {rollsLeft}</span>
      </div>
      
      <div className="flex gap-3 justify-center mb-6">
        {dice.map((value, i) => (
          <div key={i} className={`dice ${i % 2 === 0 ? 'kept' : ''}`}>
            {value}
          </div>
        ))}
        {dice.length === 0 && (
          <div className="text-slate-400 text-sm py-4">주사위를 굴리세요</div>
        )}
      </div>

      <div className="flex gap-2 justify-center">
        <button onClick={rollDice} disabled={rollsLeft === 0} className="btn btn-primary">
          굴리기
        </button>
        <button onClick={finishRolls} disabled={dice.length === 0} className="btn btn-warning">
          카테고리 선택으로 이동
        </button>
      </div>
    </div>
  );
}
