import { useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGameStore } from '../store/gameStore';
import { useAuth } from '../hooks/useAuth';
import { useWebSocket } from '../hooks/useWebSocket';
import { GameState, DiceState, WSMessage } from '../types/game';
import DiceRoller from './DiceRoller';
import Scoreboard from './Scoreboard';
import GameStatus from './GameStatus';
import CategorySelector from './CategorySelector';
import PlayerList from './PlayerList';
import api from '../utils/api';

export default function GameScreen() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const gameState = useGameStore((s) => s.gameState);
  const setGameState = useGameStore((s) => s.setGameState);
  const updateDice = useGameStore((s) => s.updateDice);
  const updateScoreboard = useGameStore((s) => s.updateScoreboard);
  const { sendMessage, onMessage, isConnected } = useWebSocket(id ?? null);

  // Refs for latest values to avoid stale closures in WebSocket handler.
  const gameStateRef = useRef<GameState | null>(null);
  useEffect(() => { gameStateRef.current = gameState; }, [gameState]);

  const prevPlayerIndexRef = useRef<number>(-1);

  // Fetch game state on mount.
  useEffect(() => {
    if (!id) return;
    prevPlayerIndexRef.current = -1;
    api
      .get<GameState>(`/games/${id}`)
      .then(({ data }) => {
        setGameState(data);
        prevPlayerIndexRef.current = data.current_player_index;
        if (data.status === 'FINISHED') {
          navigate(`/result/${id}`);
        }
      })
      .catch(() => {});
  }, [id, navigate, setGameState]);

  // Handle WebSocket messages.
  const handleMessage = useCallback(
    (msg: WSMessage) => {
      const gs = gameStateRef.current;
      switch (msg.type) {
        case 'STATE_UPDATE': {
          const state = msg.payload as Partial<GameState>;
          // When turn changed, clear dice so the new player needs to roll.
          if (gs && state.current_player_index !== undefined &&
              state.current_player_index !== gs.current_player_index) {
            prevPlayerIndexRef.current = state.current_player_index;
            setGameState({ ...state, dice: undefined });
          } else {
            setGameState(state);
          }
          break;
        }
        case 'DICE_ROLL': {
          const p = msg.payload as DiceState & { user_id?: string };
          updateDice(p as DiceState);
          break;
        }
        case 'DICE_KEEP': {
          const p = msg.payload as DiceState & { user_id?: string };
          updateDice(p as DiceState);
          break;
        }
        case 'SELECT_CATEGORY': {
          const p = msg.payload as { user_id: string; category: string; score: number };
          updateScoreboard(p.user_id, p.category, p.score);
          break;
        }
        case 'GAME_FINISHED':
          navigate(`/result/${id}`);
          break;
        case 'TIMER_UPDATE':
          setGameState({ turn_time_remaining: msg.payload as number } as Partial<GameState>);
          break;
      }
    },
    [setGameState, updateDice, updateScoreboard, navigate, id],
  );

  useEffect(() => {
    const unsub = onMessage(handleMessage);
    return unsub;
  }, [handleMessage, onMessage]);

  if (!gameState) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900 text-white">
        Loading game...
      </div>
    );
  }

  if (gameState.status === 'FINISHED') {
    navigate(`/result/${id}`);
    return null;
  }

  const currentUserId = user?.id;
  const currentPlayer = gameState.players[gameState.current_player_index];
  const isMyTurn = currentUserId !== null && currentPlayer && currentPlayer.user_id === currentUserId;
  const dice = gameState.dice;
  const shouldShowSelector = isMyTurn && dice && dice.rollsRemaining <= 0;

  const takenCategories = new Set<string>();
  if (currentUserId && gameState.scoreboards[currentUserId]) {
    gameState.scoreboards[currentUserId].entries.forEach((e) => takenCategories.add(e.category));
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold">Yacht Dice Game</h1>
          <PlayerList players={gameState.players} currentPlayerIndex={gameState.current_player_index} />
        </div>

        {/* Game Status */}
        {gameState.status === 'PLAYING' && <GameStatus gameState={gameState} />}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-4">
          {/* Left: Dice / Roll Button / Category Selector */}
          <div className="lg:col-span-1">
            {/* Already have dice - show DiceRoller */}
            {dice && !shouldShowSelector && (
              <DiceRoller
                dice={dice}
                onRoll={() => {
                  if (!isMyTurn) return;
                  sendMessage('DICE_ROLL', {
                    keptIndices: dice.keptIndices,
                    values: dice.values,
                    rollsRemaining: dice.rollsRemaining,
                  });
                }}
                onFinish={() => {
                  if (!isMyTurn) return;
                  updateDice({ ...dice, rollsRemaining: 0 });
                }}
                onToggleKeep={(index: number) => {
                  if (!isMyTurn) return;
                  const newSet = new Set(dice.keptIndices);
                  if (newSet.has(index)) {
                    newSet.delete(index);
                  } else {
                    newSet.add(index);
                  }
                  updateDice({ ...dice, keptIndices: [...newSet] });
                }}
                isMyTurn={isMyTurn}
              />
            )}

            {/* Category Selector (rollsRemaining <= 0 and it's my turn) */}
            {shouldShowSelector && dice && (
              <CategorySelector
                dice={dice.values}
                takenCategories={takenCategories}
                onSelect={(category: string) => {
                  sendMessage('SELECT_CATEGORY', {
                    category,
                    dice: dice.values,
                  });
                }}
                onPass={() => {
                  sendMessage('SELECT_CATEGORY', {
                    category: 'chance',
                    dice: dice.values,
                    isPass: true,
                  });
                }}
                isMyTurn={true}
              />
            )}

            {/* No dice yet - show initial roll button or waiting message */}
            {!dice && isMyTurn && (
              <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 text-center">
                <p className="text-lg text-white mb-4">Your turn!</p>
                <button
                  onClick={() => {
                    sendMessage('DICE_ROLL', { keptIndices: [] });
                  }}
                  disabled={!isConnected}
                  className="px-8 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors"
                >
                  Roll Dice
                </button>
              </div>
            )}

            {!dice && !isMyTurn && gameState.status === 'PLAYING' && (
              <div className="bg-slate-800 rounded-lg p-6 text-center">
                <p className="text-lg">
                  Waiting for <span className="font-bold text-yellow-400">{currentPlayer?.display_name}</span>...
                </p>
              </div>
            )}
          </div>

          {/* Right: Scoreboard */}
          <div className="lg:col-span-2">
            <Scoreboard
              scoreboards={gameState.scoreboards}
              players={gameState.players}
              currentPlayerId={currentPlayer?.user_id ?? ''}
              currentDice={dice?.values}
            />
          </div>
        </div>

        {/* Connection Status */}
        <div className="mt-4 text-sm text-slate-500">
          {isConnected ? 'Connected' : 'Connecting...'}
        </div>
      </div>
    </div>
  );
}
