import { render, screen, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import GameStatus from './GameStatus';
import { GameState } from '../types/game';

function makeState(overrides: Partial<GameState> = {}): GameState {
  return {
    game_id: 'game-1',
    status: 'PLAYING',
    current_round: 1,
    current_player_index: 0,
    turn_time_limit: 60,
    turn_time_remaining: 60,
    players: [
      { user_id: 'u1', display_name: 'Alice', join_order: 1, is_host: true },
      { user_id: 'u2', display_name: 'Bob', join_order: 2, is_host: false },
    ],
    scoreboards: {
      u1: {
        user_id: 'u1',
        entries: [],
        top_section_sum: 0,
        bottom_section_sum: 0,
        bonus: 0,
        total_score: 0,
      },
      u2: {
        user_id: 'u2',
        entries: [],
        top_section_sum: 0,
        bottom_section_sum: 0,
        bonus: 0,
        total_score: 0,
      },
    },
    ...overrides,
  };
}

describe('GameStatus', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('counts down the turn time while the turn is active', () => {
    render(<GameStatus gameState={makeState()} />);
    expect(screen.getByText('60s')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(10_000);
    });

    expect(screen.getByText('50s')).toBeInTheDocument();
  });

  it('resets the countdown to the full limit when the turn changes', () => {
    const { rerender } = render(<GameStatus gameState={makeState()} />);

    act(() => {
      vi.advanceTimersByTime(10_000);
    });
    expect(screen.getByText('50s')).toBeInTheDocument();

    rerender(<GameStatus gameState={makeState({ current_player_index: 1 })} />);

    expect(screen.getByText('60s')).toBeInTheDocument();
  });

  it('resets the countdown when a new round starts', () => {
    const { rerender } = render(<GameStatus gameState={makeState()} />);

    act(() => {
      vi.advanceTimersByTime(10_000);
    });
    expect(screen.getByText('50s')).toBeInTheDocument();

    rerender(<GameStatus gameState={makeState({ current_round: 2 })} />);

    expect(screen.getByText('60s')).toBeInTheDocument();
  });
});
