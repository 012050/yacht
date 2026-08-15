import { User } from '../types/user';

interface PlayerStatsProps {
  user: User;
}

export default function PlayerStats({ user }: PlayerStatsProps) {
  const winRate = user.total_games > 0 ? ((user.total_wins / user.total_games) * 100).toFixed(1) : '0.0';

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <h3 className="text-lg font-semibold text-white mb-3">Your Stats</h3>
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-slate-700 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-blue-400">{user.total_games}</div>
          <div className="text-xs text-slate-400">Games Played</div>
        </div>
        <div className="bg-slate-700 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-emerald-400">{user.total_wins}</div>
          <div className="text-xs text-slate-400">Wins</div>
        </div>
        <div className="bg-slate-700 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-amber-400">{winRate}%</div>
          <div className="text-xs text-slate-400">Win Rate</div>
        </div>
        <div className="bg-slate-700 rounded-lg p-3 text-center">
          <div className="text-2xl font-bold text-violet-400">{user.cumulative_score}</div>
          <div className="text-xs text-slate-400">Total Score</div>
        </div>
      </div>
    </div>
  );
}
