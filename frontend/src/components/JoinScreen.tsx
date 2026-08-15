import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';

export default function JoinScreen() {
  const [code, setCode] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleJoin = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setSubmitting(true);
      setError(null);
      try {
        const { data } = await api.post('/games/join', { join_code: code.trim().toUpperCase() });
        // Backend returns { id, join_code, status, host_user_id }
        navigate(`/waiting/${data.id}`, { replace: true });
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to join game';
        setError(message);
        console.error('Join game error:', err);
      } finally {
        setSubmitting(false);
      }
    },
    [code, navigate]
  );

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="bg-slate-800 rounded-2xl shadow-xl p-8 w-full max-w-md border border-slate-700">
        <h1 className="text-3xl font-bold text-center text-white mb-2">Join Game</h1>
        <p className="text-slate-400 text-center mb-6">
          Enter the join code to participate
        </p>

        {error && (
          <div className="bg-red-900/50 border border-red-700 text-red-200 rounded-lg p-3 mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleJoin} className="space-y-4">
          <div>
            <label htmlFor="joinCode" className="block text-sm font-medium text-slate-300 mb-1">
              Join Code
            </label>
            <input
              id="joinCode"
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              required
              maxLength={6}
              className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white text-center text-xl tracking-widest placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="ABC123"
            />
          </div>

          <button
            type="submit"
            disabled={submitting || code.length < 6}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg transition-colors"
          >
            {submitting ? 'Joining...' : 'Join Game'}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={() => navigate('/home')}
            className="text-sm text-slate-400 hover:text-slate-300 transition-colors"
          >
            Back to Home
          </button>
        </div>
      </div>
    </div>
  );
}
