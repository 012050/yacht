import { create } from "zustand";
import type { GameState, Category } from "../types/game";

interface GameStore {
  gameState: GameState | null;
  setGameState: (state: GameState) => void;
  clearGameState: () => void;
  rollDice: () => void;
  keepDice: (indices: number[]) => void;
  finishRolls: () => void;
  selectCategory: (category: Category) => void;
  passCategory: () => void;
}

export const useGameStore = create<GameStore>((set) => ({
  gameState: null,
  setGameState: (state) => set({ gameState: state }),
  clearGameState: () => set({ gameState: null }),
  rollDice: () => {
    // WebSocket ??? ?? ??
    const ws = (window as any).__ws;
    if (ws) {
      ws.send(JSON.stringify({ type: "ROLL", payload: {} }));
    }
  },
  keepDice: (indices: number[]) => {
    const ws = (window as any).__ws;
    if (ws) {
      ws.send(JSON.stringify({ type: "KEEP", payload: { indices } }));
    }
  },
  finishRolls: () => {
    const ws = (window as any).__ws;
    if (ws) {
      ws.send(JSON.stringify({ type: "FINISH_ROLLS", payload: {} }));
    }
  },
  selectCategory: (category: Category) => {
    const ws = (window as any).__ws;
    if (ws) {
      ws.send(JSON.stringify({ type: "SELECT_CATEGORY", payload: { category } }));
    }
  },
  passCategory: () => {
    const ws = (window as any).__ws;
    if (ws) {
      ws.send(JSON.stringify({ type: "PASS", payload: {} }));
    }
  },
}));
