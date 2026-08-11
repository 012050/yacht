import { useGameStore } from "../store/gameStore";
import type { Category } from "../types/game";

const labels: Record<string, string> = {
  "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6",
  "yacht": "요트", "four_of_a_kind": "4개 이상", "full_house": "풀하우스",
  "small_straight": "스몰 스트레이트", "large_straight": "라지 스트레이트", "chance": "찬스"
};

export default function CategorySelector() {
  const gameState = useGameStore((s) => s.gameState);
  const { selectCategory, passCategory } = useGameStore();

  if (!gameState || gameState.state !== "playing") return null;

  const categories: Category[] = [
    "1", "2", "3", "4", "5", "6",
    "yacht", "four_of_a_kind", "full_house",
    "small_straight", "large_straight", "chance"
  ];

  return (
    <div className="card">
      <h2 className="text-lg font-bold text-slate-800 mb-3">카테고리 선택</h2>
      <div className="grid grid-cols-3 gap-2">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => selectCategory(cat)}
            className="bg-blue-100 hover:bg-blue-200 p-2 rounded text-sm"
          >
            {labels[cat]}
          </button>
        ))}
      </div>
      <button
        onClick={passCategory}
        className="mt-3 w-full bg-red-500 text-white p-2 rounded hover:bg-red-600"
      >
        PASS (0점)
      </button>
    </div>
  );
}
