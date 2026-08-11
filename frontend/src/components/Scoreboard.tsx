import { useGameStore } from "../store/gameStore";

const labels: Record<string, string> = {
  "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6",
  "yacht": "요트", "four_of_a_kind": "4개 이상", "full_house": "풀하우스",
  "small_straight": "스몰 스트레이트", "large_straight": "라지 스트레이트", "chance": "찬스"
};

export default function Scoreboard() {
  const gameState = useGameStore((s) => s.gameState);
  if (!gameState) return null;

  const cats = ["1","2","3","4","5","6","yacht","four_of_a_kind","full_house","small_straight","large_straight","chance"];
  let top = 0, bot = 0;
  cats.forEach((c, i) => {
    Object.values(gameState.scoreboards).forEach((s: any) => {
      if (s[c] !== undefined) (i < 6 ? top += s[c] : bot += s[c]);
    });
  });
  const bonus = top >= 63 ? 35 : 0;

  return (
    <div className="card col-span-2">
      <h2 className="text-lg font-bold text-slate-800 mb-3">점수판</h2>
      <div className="grid grid-cols-6 sm:grid-cols-12 gap-2 text-sm">
        {cats.map((c) => (
          <div key={c} className="bg-slate-50 rounded p-2 text-center border border-slate-100">
            <div className="font-medium text-slate-600">{labels[c]}</div>
          </div>
        ))}
      </div>
      <div className="mt-4 flex gap-6 text-sm border-t pt-3">
        <span>상단 합계: <b className="text-blue-600">{top}</b></span>
        <span>하단 합계: <b className="text-purple-600">{bot}</b></span>
        {bonus > 0 && <span>보너스: <b className="text-emerald-600">+{bonus}</b></span>}
        <span className="ml-auto">총점: <b className="text-lg text-slate-900">{top + bot + bonus}</b></span>
      </div>
    </div>
  );
}
