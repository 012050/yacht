export type GameStatus = 'WAITING' | 'PLAYING' | 'FINISHED';

export type Category =
  | 'ones'
  | 'twos'
  | 'threes'
  | 'fours'
  | 'fives'
  | 'sixes'
  | 'yacht'
  | 'four_of_a_kind'
  | 'full_house'
  | 'small_straight'
  | 'large_straight'
  | 'chance';

export const CATEGORIES: Category[] = [
  'ones', 'twos', 'threes', 'fours', 'fives', 'sixes',
  'yacht', 'four_of_a_kind', 'full_house',
  'small_straight', 'large_straight', 'chance',
];

export const UPPER_CATEGORIES: Category[] = ['ones', 'twos', 'threes', 'fours', 'fives', 'sixes'];
export const LOWER_CATEGORIES: Category[] = ['yacht', 'four_of_a_kind', 'full_house', 'small_straight', 'large_straight', 'chance'];

export interface PlayerInfo {
  user_id: string;
  display_name: string;
  join_order: number;
  is_host: boolean;
}

export interface DiceState {
  values: number[];
  keptIndices: number[];
  rollsRemaining: number;
}

export interface ScoreboardEntry {
  category: string;
  score: number;
}

export interface PlayerScoreboard {
  user_id: string;
  entries: ScoreboardEntry[];
  top_section_sum: number;
  bottom_section_sum: number;
  bonus: number;
  total_score: number;
}

export interface GameState {
  game_id: string;
  status: GameStatus;
  current_round: number;
  current_player_index: number;
  players: PlayerInfo[];
  scoreboards: Record<string, PlayerScoreboard>;
  dice?: DiceState;
  turn_time_remaining: number;
  turn_time_limit: number;
}

export interface GameResult {
  game_id: string;
  players: ResultPlayer[];
  finished_at: string;
}

export interface ResultPlayer {
  user_id: string;
  display_name: string;
  rank: number;
  total_score: number;
  scores: Record<string, number>;
  top_section_sum: number;
  bottom_section_sum: number;
  bonus: number;
}

export interface WSMessage {
  type: string;
  payload: unknown;
}
