import {
  CATEGORIES,
  UPPER_CATEGORIES,
  LOWER_CATEGORIES,
  PlayerInfo,
  PlayerScoreboard,
  Category,
} from '../types/game';
import { calculateScore } from '../utils/scoring';

interface ScoreboardProps {
  scoreboards: Record<string, PlayerScoreboard>;
  players: PlayerInfo[];
  currentPlayerId: string;
  currentDice?: number[];
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

export default function Scoreboard({
  scoreboards,
  players,
  currentPlayerId,
  currentDice,
}: ScoreboardProps) {
  const getScore = (playerId: string, category: string) => {
    const sb = scoreboards[playerId];
    if (!sb) return null;
    const entry = sb.entries.find((e) => e.category === category);
    return entry ? entry.score : null;
  };

  const getPotentialScore = (category: Category) => {
    if (!currentDice || currentDice.length !== 5) return null;
    const sb = scoreboards[currentPlayerId];
    if (sb && sb.entries.find((e) => e.category === category)) return null;
    return calculateScore(category, currentDice);
  };

  const upperTotal = (playerId: string) =>
    UPPER_CATEGORIES.reduce((sum, cat) => sum + (getScore(playerId, cat) ?? 0), 0);

  const lowerTotal = (playerId: string) =>
    LOWER_CATEGORIES.reduce((sum, cat) => sum + (getScore(playerId, cat) ?? 0), 0);

  return (
    <div className="bg-slate-800 rounded-lg p-4 overflow-x-auto">
      <h2 className="text-lg font-bold mb-3">Scoreboard</h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-600">
            <th className="text-left py-2 px-2">Category</th>
            {players.map((p) => (
              <th
                key={p.user_id}
                className={`text-center py-2 px-2 ${
                  p.user_id === currentPlayerId ? 'text-yellow-400 font-bold' : ''
                }`}
              >
                {p.display_name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {/* Upper section */}
          {UPPER_CATEGORIES.map((cat) => (
            <tr key={cat} className="border-b border-slate-700">
              <td className="py-1 px-2 text-blue-300">{CATEGORY_LABELS[cat]}</td>
              {players.map((p) => {
                const score = getScore(p.user_id, cat);
                const potential = p.user_id === currentPlayerId ? getPotentialScore(cat as Category) : null;
                return (
                  <td key={p.user_id} className="text-center py-1 px-2">
                    {score !== null ? (
                      score
                    ) : potential !== null ? (
                      <span className="text-green-400 text-xs">{potential}</span>
                    ) : (
                      '-'
                    )}
                  </td>
                );
              })}
            </tr>
          ))}

          {/* Upper subtotal */}
          <tr className="bg-slate-700 font-bold">
            <td className="py-2 px-2 text-blue-300">Upper Total</td>
            {players.map((p) => (
              <td key={p.user_id} className="text-center py-2 px-2 text-blue-300">
                {upperTotal(p.user_id)}
              </td>
            ))}
          </tr>

          {/* Bonus */}
          <tr className="bg-slate-700">
            <td className="py-1 px-2 text-yellow-400">Bonus (+35)</td>
            {players.map((p) => {
              const total = upperTotal(p.user_id);
              return (
                <td key={p.user_id} className="text-center py-1 px-2 text-yellow-400">
                  {total >= 63 ? '+35' : '0'}
                </td>
              );
            })}
          </tr>

          {/* Lower section */}
          {LOWER_CATEGORIES.map((cat) => (
            <tr key={cat} className="border-b border-slate-700">
              <td className="py-1 px-2 text-green-300">{CATEGORY_LABELS[cat]}</td>
              {players.map((p) => {
                const score = getScore(p.user_id, cat);
                const potential = p.user_id === currentPlayerId ? getPotentialScore(cat as Category) : null;
                return (
                  <td key={p.user_id} className="text-center py-1 px-2">
                    {score !== null ? (
                      score
                    ) : potential !== null ? (
                      <span className="text-green-400 text-xs">{potential}</span>
                    ) : (
                      '-'
                    )}
                  </td>
                );
              })}
            </tr>
          ))}

          {/* Lower subtotal */}
          <tr className="bg-slate-700 font-bold">
            <td className="py-2 px-2 text-green-300">Lower Total</td>
            {players.map((p) => (
              <td key={p.user_id} className="text-center py-2 px-2 text-green-300">
                {lowerTotal(p.user_id)}
              </td>
            ))}
          </tr>

          {/* Grand total */}
          <tr className="bg-slate-600 font-bold text-lg">
            <td className="py-3 px-2">Total</td>
            {players.map((p) => {
              const upper = upperTotal(p.user_id);
              const lower = lowerTotal(p.user_id);
              const bonus = upper >= 63 ? 35 : 0;
              return (
                <td key={p.user_id} className="text-center py-3 px-2">
                  {upper + lower + bonus}
                </td>
              );
            })}
          </tr>
        </tbody>
      </table>
    </div>
  );
}
