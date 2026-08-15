import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ResultScreen from './ResultScreen';
import api from '../utils/api';

vi.mock('../utils/api', () => ({
  default: { get: vi.fn() },
}));

const getMock = vi.mocked(api.get);

function mockResults() {
  return {
    game_id: 'game-1',
    players: [
      {
        user_id: 'u1',
        display_name: 'Alice',
        rank: 1,
        total_score: 154,
        scores: {
          ones: 6, twos: 4, threes: 0, fours: 8, fives: 10, sixes: 6,
          yacht: 50, four_of_a_kind: 25, full_house: 0,
          small_straight: 30, large_straight: 0, chance: 15,
        },
        top_section_sum: 34,
        bottom_section_sum: 120,
        bonus: 0,
      },
      {
        user_id: 'u2',
        display_name: 'Bob',
        rank: 2,
        total_score: 77,
        scores: {
          ones: 5, twos: 4, threes: 3, fours: 2, fives: 1, sixes: 5,
          yacht: 0, four_of_a_kind: 22, full_house: 25,
          small_straight: 0, large_straight: 0, chance: 10,
        },
        top_section_sum: 20,
        bottom_section_sum: 57,
        bonus: 0,
      },
    ],
    finished_at: '2026-08-16T00:00:00Z',
  };
}

function renderResultScreen() {
  return render(
    <MemoryRouter initialEntries={['/result/game-1']}>
      <Routes>
        <Route path="/result/:id" element={<ResultScreen />} />
      </Routes>
    </MemoryRouter>
  );
}

describe('ResultScreen', () => {
  beforeEach(() => {
    getMock.mockReset();
  });

  it('fetches the results endpoint and shows per-category scores', async () => {
    getMock.mockResolvedValue({ data: mockResults() } as never);
    renderResultScreen();

    const aliceNodes = await screen.findAllByText('Alice');
    expect(aliceNodes.length).toBeGreaterThan(0);
    expect(screen.getByText('154 points')).toBeInTheDocument();
    // Regression: before the /results endpoint existed, every category
    // rendered 0 because the game-info payload had no scores field.
    expect(screen.getByText('50')).toBeInTheDocument();
    expect(screen.getByText('22')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(getMock).toHaveBeenCalledWith('/games/game-1/results');
  });

  it('shows a fallback when results are unavailable', async () => {
    getMock.mockRejectedValue(new Error('Game has not finished'));
    renderResultScreen();

    expect(await screen.findByText('No results available')).toBeInTheDocument();
  });
});
