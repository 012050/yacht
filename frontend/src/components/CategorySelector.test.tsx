import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import CategorySelector from './CategorySelector';

const EXPECTED_PIPS: Record<number, number> = {
  1: 1,
  2: 2,
  3: 3,
  4: 4,
  5: 5,
  6: 6,
};

function countDiePips(container: HTMLElement): number {
  // The dice row contains exactly 5 die faces of 9 cells each. Pips are the
  // cells carrying both the rounded-full and bg-slate-800 classes.
  const cells = Array.from(
    container.querySelectorAll('div.w-1\\.5.h-1\\.5.rounded-full.bg-slate-800')
  );
  return cells.length;
}

function renderWithDice(dice: number[]) {
  return render(
    <CategorySelector
      dice={dice}
      takenCategories={new Set()}
      onSelect={() => {}}
      onPass={() => {}}
      isMyTurn
    />
  );
}

describe('CategorySelector die faces', () => {
  it('renders the correct number of pips for each die value', () => {
    for (const value of [1, 2, 3, 4, 5, 6]) {
      const { container, unmount } = renderWithDice([value, 1, 1, 1, 1]);
      const pips = countDiePips(container);
      expect(pips, `value ${value} should render ${EXPECTED_PIPS[value] + 4} pips`).toBe(
        EXPECTED_PIPS[value] + 4
      );
      unmount();
    }
  });

  it('renders a 6 differently from a 4 (regression: both showed 4 pips)', () => {
    const four = renderWithDice([4, 1, 1, 1, 1]);
    const six = renderWithDice([6, 1, 1, 1, 1]);

    const fourPips = countDiePips(four.container);
    const sixPips = countDiePips(six.container);

    expect(fourPips).toBe(8);
    expect(sixPips).toBe(10);
    expect(sixPips).not.toBe(fourPips);
  });
});
