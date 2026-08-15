import { PlayerInfo } from '../types/game';

interface PlayerListProps {
  players: PlayerInfo[];
  currentPlayerIndex?: number;
}

export default function PlayerList({ players, currentPlayerIndex }: PlayerListProps) {
  return (
    <div className="space-y-2">
      {players.map((player, index) => {
        const isCurrent = currentPlayerIndex !== undefined && index === currentPlayerIndex;
        return (
          <div
            key={player.user_id}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg ${
              isCurrent
                ? 'bg-blue-900/50 border border-blue-600'
                : 'bg-slate-700/50 border border-transparent'
            }`}
          >
            <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center text-sm font-bold text-white">
              {player.display_name.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium text-white">
                {player.display_name}
              </div>
              <div className="text-xs text-slate-400">
                {player.is_host ? 'Host' : `Player #${player.join_order}`}
              </div>
            </div>
            {player.is_host && (
              <span className="px-2 py-0.5 bg-amber-600 text-white text-xs rounded-full font-medium">
                Host
              </span>
            )}
            {isCurrent && (
              <span className="px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full font-medium animate-pulse">
                Current
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
