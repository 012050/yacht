import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { useAuthStore } from '../store/authStore';
import PlayerList from './PlayerList';
import { PlayerInfo } from '../types/game';

interface GameInfo {
  id: string;
  join_code: string;
  status: string;
  host_user_id: string;
  current_round: number;
  turn_time_limit: number;
  players: PlayerInfo[];
  scoreboards: unknown[];
}

export default function WaitingRoom() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const [game, setGame] = useState<GameInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeLimit, setTimeLimit] = useState(60);

  useEffect(() => {
    if (!id) return;
    const fetchGame = async () => {
      try {
        const { data } = await api.get<GameInfo>(`/games/${id}`);
        setGame(data);
        setTimeLimit(data.turn_time_limit ?? 60);

        // If game has started, redirect ALL players to game screen
        if (data.status === 'PLAYING') {
          navigate(`/game/${id}`, { replace: true });
        }
        // If game is finished, redirect to result screen
        if (data.status === 'FINISHED') {
          navigate(`/result/${id}`, { replace: true });
        }
      } catch {
        setError('Game not found');
      } finally {
        setLoading(false);
      }
    };
    fetchGame();

    // Poll for updates every 2 seconds
    const interval = setInterval(fetchGame, 2000);
    return () => clearInterval(interval);
  }, [id, navigate]);

  const isHost = user ? game?.host_user_id === user.id : false;

  const handleStart = useCallback(async () => {
    if (!id) return;
    setStarting(true);
    try {
      await api.post(`/games/${id}/start`);
      // Don't navigate here - let the useEffect poll detect the status change
      // This ensures all players get redirected simultaneously
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to start';
      setError(message);
    } finally {
      setStarting(false);
    }
  }, [id]);

  const handleCopyCode = useCallback(() => {
    if (game) {
      navigator.clipboard.writeText(game.join_code).catch(() => {});
    }
  }, [game]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading game...</div>
      </div>
    );
  }

  if (error || !game) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-xl mb-4">{error || 'Game not found'}</p>
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

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Nav */}
      <nav className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold">Waiting Room</h1>
          <button
            onClick={() => navigate('/home')}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-medium transition-colors"
          >
            Leave
          </button>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-4xl mx-auto p-6">
        {/* Join code */}
        <div className="bg-slate-800 rounded-xl p-6 mb-6 border border-slate-700 text-center">
          <div className="text-sm text-slate-400 mb-2">Share this code with friends</div>
          <div className="flex items-center justify-center gap-3">
            <span className="text-4xl font-mono font-bold tracking-widest text-blue-400">
              {game.join_code}
            </span>
            <button
              onClick={handleCopyCode}
              className="px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm transition-colors"
            >
              Copy
            </button>
          </div>
        </div>

        {/* Players */}
        <div className="bg-slate-800 rounded-xl p-6 mb-6 border border-slate-700">
          <h2 className="text-lg font-semibold mb-4">
            Players ({game.players.length})
          </h2>
          <PlayerList players={game.players} currentPlayerIndex={-1} />
        </div>

        {/* Host controls */}
        {isHost && (
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <h2 className="text-lg font-semibold mb-4">Host Controls</h2>
            <div className="flex flex-col sm:flex-row gap-4 items-end">
              <div className="flex-1">
                <label htmlFor="timeLimit" className="block text-sm text-slate-400 mb-1">
                  Turn Time Limit (seconds)
                </label>
                <input
                  id="timeLimit"
                  type="range"
                  min={30}
                  max={120}
                  step={10}
                  value={timeLimit}
                  onChange={(e) => setTimeLimit(Number(e.target.value))}
                  className="w-full"
                />
                <div className="text-center text-sm text-slate-300 mt-1">
                  {timeLimit}s
                </div>
              </div>
              <button
                onClick={handleStart}
                disabled={starting || game.players.length < 2}
                className="px-8 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors"
              >
                {starting ? 'Starting...' : 'Start Game'}
              </button>
            </div>
            {game.players.length < 2 && (
              <div className="text-xs text-slate-500 mt-2">
                Need at least 2 players to start
              </div>
            )}
          </div>
        )}

        {!isHost && (
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 text-center">
            <div className="text-slate-400">
              Waiting for host to start the game...
            </div>
            <div className="text-sm text-slate-500 mt-2">
              Auto-refreshing every 2 seconds
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
