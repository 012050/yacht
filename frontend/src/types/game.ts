export type Category =
  | "1" | "2" | "3" | "4" | "5" | "6"
  | "yacht" | "four_of_a_kind" | "full_house"
  | "small_straight" | "large_straight" | "chance";

export interface ScoreEntry {
  category: Category;
  score: number;
}

export interface PlayerInGame {
  user_id: string;
  nickname: string;
  is_host: boolean;
  total_score: number;
}

export interface GameState {
  game_id: string;
  state: "created" | "waiting" | "playing" | "finished";
  timeout_duration: number;
  players: PlayerInGame[];
  current_player_index: number;
  current_round: number;
  dice: number[];
  rolls_left: number;
  scoreboards: Record<string, Record<string, number>>;
  turn_start_time?: string;
}

export interface GameResult {
  game_id: string;
  players: ResultPlayer[];
  finished_at?: string;
}

export interface ResultPlayer {
  user_id: string;
  nickname: string;
  rank: number;
  total_score: number;
  top_section_sum: number;
  bottom_section_sum: number;
  bonus: number;
  scores: Record<string, number>;
}
