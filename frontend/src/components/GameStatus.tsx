import { useState, useEffect } from 'react';
import { GameState } from '../types/game';

interface GameStatusProps {
  gameState: GameState;
}

export default function GameStatus({ gameState }: GameStatusProps) {
  const [timeLeft, setTimeLeft] = useState(gameState.turn_time_remaining);
  const currentPlayerIndex = gameState.current_player_index;
  const currentRound = gameState.current_round;

  useEffect(() => {
    setTimeLeft(gameState.turn_time_remaining);
  }, [currentPlayerIndex, currentRound, gameState.turn_time_remaining]);

  useEffect(() => {
    if (gameState.status !== 'PLAYING') return;
    if (timeLeft <= 0) return;
    const timer = setInterval(() => {
      setTimeLeft((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [gameState.status, timeLeft <= 0]);

  const currentPlayer = gameState.players[gameState.current_player_index];
  const pct = gameState.turn_time_limit > 0 ? (timeLeft / gameState.turn_time_limit) * 100 : 0;
  const timeColor = pct > 50 ? 'bg-emerald-500' : pct > 25 ? 'bg-amber-500' : 'bg-red-500';

  if (gameState.status === 'WAITING') {
    return (
      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 text-center">
        <div className="text-slate-400">Waiting for game to start...</div>
      </div>
    );
  }

  if (gameState.status === 'FINISHED') {
    return (
      <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 text-center">
        <div className="text-amber-400 font-semibold">Game Over!</div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-xs text-slate-400">Round</div>
          <div className="text-2xl font-bold text-white">{gameState.current_round} / 12</div>
        </div>
        <div className="text-right">
          <div className="text-xs text-slate-400">Current Player</div>
          <div className="text-lg font-semibold text-blue-400">
            {currentPlayer?.display_name ?? '---'}
          </div>
        </div>
      </div>
      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-slate-400">Time Remaining</span>
          <span className={`text-sm font-bold ${timeLeft <= 10 ? 'text-red-400 animate-pulse' : 'text-slate-300'}`}>
            {timeLeft}s
          </span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-1000 ${timeColor}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  );
}
