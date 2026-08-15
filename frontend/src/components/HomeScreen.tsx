import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useGameStore } from '../store/gameStore';
import api from '../utils/api';
import PlayerStats from './PlayerStats';
import { User } from '../types/user';

interface LeaderboardEntry {
  user: User;
  rank: number;
}

export default function HomeScreen() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const setError = useGameStore((s) => s.setError);

  useEffect(() => {
    if (!user) return;
    (async () => {
      try {
        const { data } = await api.get<LeaderboardEntry[]>('/leaderboard');
        setLeaderboard(data);
      } catch {
        // leaderboard not available
      } finally {
        setLoading(false);
      }
    })();
  }, [user]);

  const handleCreateGame = useCallback(async () => {
    setCreating(true);
    setError(null);
    try {
      const { data } = await api.post('/games', {});
      // Backend returns { id, join_code, status, host_user_id }
      const gameId = data.id;
      navigate(`/waiting/${gameId}`, { replace: true });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create game';
      setError(message);
      console.error('Create game error:', err);
    } finally {
      setCreating(false);
    }
  }, [navigate, setError]);

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Nav bar */}
      <nav className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <h1 className="text-2xl font-bold">Yacht</h1>
          <div className="flex items-center gap-4">
            <span className="text-slate-300 text-sm">{user?.nickname}</span>
            <button
              onClick={logout}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-medium transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      {/* Main content */}
      <div className="max-w-5xl mx-auto p-6">
        {/* Welcome */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-1">
            Welcome, {user?.nickname}!
          </h2>
          <p className="text-slate-400">Ready to play some Yacht?</p>
        </div>

        {/* Actions */}
        <div className="flex gap-4 mb-8">
          <button
            onClick={handleCreateGame}
            disabled={creating}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:opacity-50 text-white font-semibold py-4 rounded-xl text-lg transition-colors"
          >
            {creating ? 'Creating...' : 'Create Game'}
          </button>
          <button
            onClick={() => navigate('/join')}
            className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-4 rounded-xl text-lg transition-colors"
          >
            Join Game
          </button>
        </div>

        {/* Stats + Leaderboard */}
        <div className="grid md:grid-cols-2 gap-6">
          {user && <PlayerStats user={user} />}

          <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-3">Leaderboard</h3>
            {loading ? (
              <div className="text-slate-400 text-sm">Loading...</div>
            ) : leaderboard.length === 0 ? (
              <div className="text-slate-400 text-sm">No data yet</div>
            ) : (
              <div className="space-y-1">
                {leaderboard.slice(0, 10).map((entry) => (
                  <div
                    key={entry.user.id}
                    className="flex items-center gap-3 px-3 py-2 bg-slate-700/50 rounded-lg"
                  >
                    <span className="text-sm font-bold text-slate-500 w-6 text-center">
                      {entry.rank}
                    </span>
                    <span className="text-sm font-medium text-white flex-1">
                      {entry.user.nickname}
                    </span>
                    <span className="text-sm text-slate-400">
                      {entry.user.total_wins}W / {entry.user.total_games}G
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
