import { useState } from "react";
import api from "../utils/api";
import type { ResultPlayer } from "../types/game";

const labels: Record<string, string> = {
  "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6",
  "yacht": "요트", "four_of_a_kind": "4개 이상", "full_house": "풀하우스",
  "small_straight": "스몰 스트레이트", "large_straight": "라지 스트레이트", "chance": "찬스"
};

interface Props {
  gameId: string;
  onReplay: () => void;
}

export default function ResultScreen({ gameId, onReplay }: Props) {
  const [players, setPlayers] = useState<ResultPlayer[]>([]);
  const [loading, setLoading] = useState(true);

  useState(() => {
    api.get(`/games/${gameId}/result`)
      .then(({ data }) => {
        setPlayers(data.players);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  });

  if (loading) return <div className="min-h-screen flex items-center justify-center">로딩 중...</div>;

  return (
    <div className="min-h-screen bg-slate-100 p-8">
      <h1 className="text-3xl font-bold text-center mb-6">게임 결과</h1>
      <div className="max-w-2xl mx-auto space-y-4">
        {players.map((p, i) => (
          <div key={p.user_id} className="bg-white p-4 rounded shadow">
            <div className="flex justify-between items-center mb-2">
              <span className="text-lg font-bold">{i + 1}위 {p.nickname}</span>
              <span className="text-xl font-bold text-blue-600">{p.total_score}점</span>
            </div>
            <div className="grid grid-cols-3 gap-1 text-sm">
              {Object.entries(p.scores).map(([cat, score]) => (
                <div key={cat} className="p-1 bg-slate-50 rounded">
                  {labels[cat] || cat}: {score}
                </div>
              ))}
            </div>
            <div className="mt-2 text-xs text-slate-600">
              상단: {p.top_section_sum} | 하단: {p.bottom_section_sum} | 보너스: +{p.bonus}
            </div>
          </div>
        ))}
      </div>
      <div className="text-center mt-6">
        <button onClick={onReplay} className="bg-emerald-600 text-white px-6 py-3 rounded text-lg hover:bg-emerald-700">
          다시 플레이
        </button>
      </div>
    </div>
  );
}
