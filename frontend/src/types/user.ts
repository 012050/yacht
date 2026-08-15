export interface User {
  id: string;
  username: string;
  nickname: string;
  total_games: number;
  total_wins: number;
  cumulative_score: number;
}

export interface LeaderboardEntry {
  user: User;
  rank: number;
}
