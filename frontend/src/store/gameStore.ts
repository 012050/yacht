import { create } from 'zustand';
import {
  GameState,
  DiceState,
} from '../types/game';

interface GameStoreState {
  gameState: GameState | null;
  error: string | null;
  setGameState: (partial: Partial<GameState> | GameState) => void;
  updateDice: (dice: DiceState) => void;
  updateScoreboard: (playerId: string, category: string, score: number) => void;
  setError: (error: string | null) => void;
}

export const useGameStore = create<GameStoreState>((set) => ({
  gameState: null,
  error: null,

  setGameState: (partial) => {
    set((state) => {
      const prev = state.gameState;
      if (!prev) {
        // If no previous state, only set if we have a full GameState
        if (partial.game_id !== undefined && partial.status && partial.players && partial.scoreboards !== undefined) {
          return { ...state, gameState: partial as GameState };
        }
        return state;
      }
      // Merge partial into existing state
      // Handle dice separately: use "dice" in partial to detect when dice should be cleared
      // (handleMessage passes dice: undefined on turn change, which must be respected)
      const { dice: partialDice, ...partialWithoutDice } = partial as Record<string, unknown>;
      const hasDiceKey = "dice" in partial;
      const updated: GameState = {
        ...prev,
        ...partialWithoutDice,
        dice: hasDiceKey ? (partialDice as DiceState | undefined) : prev.dice,
        players: partial.players !== undefined ? partial.players : prev.players,
        scoreboards: partial.scoreboards !== undefined ? partial.scoreboards : prev.scoreboards,
      };
      return { gameState: updated };
    });
  },

  updateDice: (dice: DiceState) => {
    set((state) => ({
      gameState: state.gameState
        ? { ...state.gameState, dice }
        : null,
    }));
  },

  updateScoreboard: (playerId: string, category: string, score: number) => {
    set((state) => {
      if (!state.gameState) return state;
      const sb = state.gameState.scoreboards[playerId];
      if (!sb) return state;
      const updatedEntries = sb.entries.map((e) =>
        e.category === category ? { ...e, score } : e
      );
      const UPPER = ['ones', 'twos', 'threes', 'fours', 'fives', 'sixes'];
      const topSum = updatedEntries
        .filter((e) => UPPER.includes(e.category))
        .reduce((s, e) => s + e.score, 0);
      const bottomSum = updatedEntries
        .filter((e) => !UPPER.includes(e.category))
        .reduce((s, e) => s + e.score, 0);
      const bonus = topSum >= 63 ? 35 : 0;
      const totalScore = topSum + bottomSum + bonus;
      const updatedScoreboards = {
        ...state.gameState.scoreboards,
        [playerId]: {
          ...sb,
          entries: updatedEntries,
          top_section_sum: topSum,
          bottom_section_sum: bottomSum,
          bonus,
          total_score: totalScore,
        },
      };
      return {
        gameState: { ...state.gameState, scoreboards: updatedScoreboards },
      };
    });
  },

  setError: (error: string | null) => set({ error }),
}));
