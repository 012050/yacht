import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { ResultPlayer, CATEGORIES } from '../types/game';
import { calculateBonus } from '../utils/scoring';

interface GameResultData {
  game_id: string;
  players: ResultPlayer[];
  finished_at: string;
}

const CATEGORY_LABELS: Record<string, string> = {
  ones: 'Ones',
  twos: 'Twos',
  threes: 'Threes',
  fours: 'Fours',
  fives: 'Fives',
  sixes: 'Sixes',
  yacht: 'Yacht',
  four_of_a_kind: 'Four of a Kind',
  full_house: 'Full House',
  small_straight: 'Small Straight',
  large_straight: 'Large Straight',
  chance: 'Chance',
};

const UPPER_CATEGORIES = ['ones', 'twos', 'threes', 'fours', 'fives', 'sixes'];

export default function ResultScreen() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [result, setResult] = useState<GameResultData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    api
      .get<GameResultData>(`/games/${id}/results`)
      .then(({ data }) => {
        setResult(data);
      })
      .catch(() => {
        // fallback: show empty
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900 text-white">
        Loading results...
      </div>
    );
  }

  if (!result || result.players.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900 text-white">
        <div className="text-center">
          <p className="text-xl mb-4">No results available</p>
          <button
            onClick={() => navigate('/home')}
            className="px-6 py-2 bg-blue-600 rounded hover:bg-blue-700"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  const winner = result.players[0];

  return (
    <div className="min-h-screen bg-slate-900 text-white p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <h1 className="text-3xl font-bold text-center mb-2">Game Results</h1>

        {/* Winner */}
        {winner && (
          <div className="bg-gradient-to-r from-yellow-600 to-amber-600 rounded-lg p-6 text-center mb-6">
            <p className="text-lg opacity-90">Winner</p>
            <p className="text-3xl font-bold">{winner.display_name}</p>
            <p className="text-xl mt-2">{winner.total_score} points</p>
          </div>
        )}

        {/* Rankings */}
        <div className="bg-slate-800 rounded-lg p-4 mb-6">
          <h2 className="text-xl font-bold mb-4">Rankings</h2>
          <div className="space-y-2">
            {result.players.map((player, index) => (
              <div
                key={player.user_id}
                className={`flex items-center justify-between p-3 rounded ${
                  index === 0 ? 'bg-yellow-900/30 border border-yellow-600' : 'bg-slate-700'
                }`}
              >
                <div className="flex items-center gap-4">
                  <span className="text-2xl font-bold w-8 text-center">
                    {index === 0 ? '1' : index === 1 ? '2' : `${index + 1}`}
                  </span>
                  <span className="font-semibold">{player.display_name}</span>
                </div>
                <div className="text-right">
                  <span className="text-lg font-bold">{player.total_score}</span>
                  <span className="text-sm text-slate-400 ml-2">pts</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Detailed Scoreboard */}
        {result.players.map((player) => (
          <div key={player.user_id} className="bg-slate-800 rounded-lg p-4 mb-4">
            <h3 className="text-lg font-bold mb-3">{player.display_name} - {player.total_score} pts</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {CATEGORIES.map((cat) => {
                const score = player.scores?.[cat] ?? 0;
                const isUpper = UPPER_CATEGORIES.includes(cat);
                return (
                  <div key={cat} className="flex justify-between py-1 px-2 bg-slate-700 rounded">
                    <span>{CATEGORY_LABELS[cat]}</span>
                    <span className={isUpper ? 'text-blue-300' : 'text-green-300'}>{score}</span>
                  </div>
                );
              })}
              {/* Subtotals */}
              <div className="col-span-2 mt-2 pt-2 border-t border-slate-600">
                <div className="flex justify-between py-1">
                  <span className="font-semibold">Upper Total</span>
                  <span className="font-semibold">{player.top_section_sum}</span>
                </div>
                {player.bonus > 0 && (
                  <div className="flex justify-between py-1 text-yellow-400">
                    <span>Bonus</span>
                    <span>+{player.bonus}</span>
                  </div>
                )}
                <div className="flex justify-between py-1">
                  <span className="font-semibold">Lower Total</span>
                  <span className="font-semibold">{player.bottom_section_sum}</span>
                </div>
                <div className="flex justify-between py-2 font-bold text-lg border-t border-slate-500 mt-1">
                  <span>Total</span>
                  <span>{player.total_score}</span>
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Actions */}
        <div className="flex gap-4 justify-center mt-6">
          <button
            onClick={() => navigate('/home')}
            className="px-8 py-3 bg-blue-600 rounded-lg hover:bg-blue-700 font-semibold text-lg"
          >
            Back to Home
          </button>
        </div>
      </div>
    </div>
  );
}
