"""Game flow management: create, join, start, turn handling, finish."""
import random
import string
from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.database.models import Game, GamePlayer, Scoreboard, GameResult, User
from app.services.dice_service import validate_keep_indices
from app.services.scoring import (
    LOWER_CATEGORIES,
    CATEGORIES,
    UPPER_CATEGORIES,
    auto_select_category,
    calculate_bonus,
    calculate_score,
)
from app.services.stats_service import update_stats


class GameService:
    """Stateless service that operates on a DB session per call."""

    # ── Game creation & joining ────────────────────────────────────────

    @staticmethod
    def _generate_join_code() -> str:
        chars = string.ascii_uppercase + string.digits
        return "".join(random.choices(chars, k=6))

    def create_game(
        self,
        db: Session,
        host_user_id: str,
        turn_time_limit: int = 60,
    ) -> Game:
        """Create a new game in WAITING state and add the host as the first player."""
        # Generate a unique join code.
        while True:
            code = self._generate_join_code()
            existing = db.query(Game).filter(Game.join_code == code).first()
            if not existing:
                break

        game = Game(
            host_user_id=host_user_id,
            join_code=code,
            status="waiting",
            turn_time_limit=turn_time_limit,
            current_player_index=0,
            current_round=1,
        )
        db.add(game)
        db.flush()

        game_player = GamePlayer(game_id=game.id, user_id=host_user_id, join_order=1)
        db.add(game_player)
        db.commit()
        return game

    def join_game(self, db: Session, join_code: str, user_id: str) -> Game:
        """Join an existing game by join_code. Raises ValueError on bad input."""
        game = db.query(Game).filter(Game.join_code == join_code).first()
        if not game:
            raise ValueError("Game not found")
        if game.status != "waiting":
            raise ValueError("Game has already started")

        # Check not already joined.
        existing = (
            db.query(GamePlayer)
            .filter_by(game_id=game.id, user_id=user_id)
            .first()
        )
        if existing:
            raise ValueError("Already a player in this game")

        max_order = (
            db.query(GamePlayer)
            .filter_by(game_id=game.id)
            .order_by(GamePlayer.join_order.desc())
            .first()
        )
        join_order = (max_order.join_order + 1) if max_order else 1

        game_player = GamePlayer(game_id=game.id, user_id=user_id, join_order=join_order)
        db.add(game_player)
        db.commit()
        return game

    # ── Start game ─────────────────────────────────────────────────────

    def start_game(self, db: Session, game_id: str, user_id: str) -> Game:
        """Host starts the game. Turns proceed in join order; sets PLAYING."""
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise ValueError("Game not found")
        if game.host_user_id != user_id:
            raise ValueError("Only the host can start the game")
        if game.status != "waiting":
            raise ValueError("Game is not in waiting state")

        player_count = db.query(GamePlayer).filter_by(game_id=game_id).count()
        if player_count < 2:
            raise ValueError("Need at least 2 players to start")

        game.status = "playing"
        db.commit()
        return game

    # ── Turn info ──────────────────────────────────────────────────────

    def get_turn_state(
        self,
        db: Session,
        game_id: str,
        user_id: str,
    ) -> dict:
        """Return turn information for the current game."""
        from app.database.models import User

        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise ValueError("Game not found")

        players = (
            db.query(GamePlayer)
            .filter_by(game_id=game_id)
            .order_by(GamePlayer.join_order)
            .all()
        )

        if not players:
            raise ValueError("No players in this game")

        current_player_gp = players[game.current_player_index % len(players)]
        current_user = db.query(User).filter(User.id == current_player_gp.user_id).first()

        used_categories = {
            row.category
            for row in db.query(Scoreboard)
            .filter_by(game_id=game_id, user_id=current_player_gp.user_id)
            .all()
        }

        available = [cat for cat in CATEGORIES if cat not in used_categories]

        return {
            "game_id": game_id,
            "current_player_user_id": current_player_gp.user_id,
            "current_player_display_name": current_user.nickname if current_user else "Unknown",
            "current_round": game.current_round,
            "status": game.status,
            "turn_time_limit": game.turn_time_limit,
            "available_categories": available,
        }

    # ── Dice rolling ───────────────────────────────────────────────────

    def roll_dice(
        self,
        db: Session,
        game_id: str,
        user_id: str,
        kept_indices: Optional[list[int]] = None,
        current_values: Optional[list[int]] = None,
        rolls_remaining: Optional[int] = None,
    ) -> dict:
        """Roll dice for the current player's turn.

        On first roll (current_values is None): roll all 5 dice.
        On reroll (current_values provided): keep the indexed dice from
        current_values and roll the rest. kept_indices may be empty, meaning
        no dice are kept; the roll counter still decreases.

        Returns a dict matching frontend DiceState:
        {values: number[], keptIndices: number[], rollsRemaining: number}
        """
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise ValueError("Game not found")

        players = (
            db.query(GamePlayer)
            .filter_by(game_id=game_id)
            .order_by(GamePlayer.join_order)
            .all()
        )
        current_gp = players[game.current_player_index % len(players)]
        if current_gp.user_id != user_id:
            raise ValueError("Not your turn")

        from app.services.dice_service import roll_5_dice

        if current_values is None:
            # First roll — roll all 5 dice.
            values = roll_5_dice()
            rolls_remaining = 2
            kept = []
        else:
            # Reroll — merge kept dice with new rolls.
            if len(current_values) != 5:
                raise ValueError("current_values must contain 5 dice")
            if kept_indices is None:
                kept_indices = []
            if not validate_keep_indices(kept_indices, 5):
                raise ValueError("Invalid keep indices")
            kept_set = set(kept_indices)
            values = []
            for i in range(5):
                if i in kept_set:
                    values.append(current_values[i])
                else:
                    values.append(random.randint(1, 6))
            rolls_remaining = max(0, rolls_remaining - 1) if rolls_remaining else 0
            kept = kept_indices

        return {
            "values": values,
            "keptIndices": kept,
            "rollsRemaining": rolls_remaining,
        }

    # ── Keep dice ──────────────────────────────────────────────────────

    def keep_dice(
        self,
        db: Session,
        game_id: str,
        user_id: str,
        indices: list[int],
    ) -> dict:
        """Validate and return the kept dice info."""
        if not validate_keep_indices(indices, 5):
            raise ValueError("Invalid keep indices")
        return {"kept_indices": sorted(indices)}

    # ── Record score ───────────────────────────────────────────────────

    def record_score(
        self,
        db: Session,
        game_id: str,
        user_id: str,
        category: str,
        score: int,
    ) -> dict:
        """Record a score entry, check bonus, advance turn, check game end."""
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise ValueError("Game not found")

        players = (
            db.query(GamePlayer)
            .filter_by(game_id=game_id)
            .order_by(GamePlayer.join_order)
            .all()
        )
        if not players:
            raise ValueError("No players")

        current_gp = players[game.current_player_index % len(players)]
        if current_gp.user_id != user_id:
            raise ValueError("Not your turn")

        # Check category already used.
        existing = (
            db.query(Scoreboard)
            .filter_by(game_id=game_id, user_id=user_id, category=category)
            .first()
        )
        if existing:
            raise ValueError(f"Category '{category}' already used")

        # Add scoreboard entry. Flush explicitly: the production session has
        # autoflush=False, so the bonus sum, game-end count, and finish_game
        # must see this entry before committing.
        entry = Scoreboard(game_id=game_id, user_id=user_id, category=category, score=score)
        db.add(entry)
        db.flush()

        # Calculate upper total for bonus.
        upper_entries = (
            db.query(Scoreboard)
            .filter_by(game_id=game_id, user_id=user_id)
            .filter(Scoreboard.category.in_(UPPER_CATEGORIES))
            .all()
        )
        upper_total = sum(e.score for e in upper_entries)
        bonus = calculate_bonus(upper_total)

        # Advance to next player.
        game.current_player_index = (game.current_player_index + 1) % len(players)
        if game.current_player_index == 0:
            game.current_round += 1

        # Check if game is finished: all players have filled all categories.
        player_count = len(players)
        total_needed = player_count * len(CATEGORIES)
        total_filled = db.query(Scoreboard).filter_by(game_id=game_id).count()

        game_finished = total_filled >= total_needed
        if game_finished and game.status == "playing":
            self.finish_game(db, game_id)
            db.commit()
            return {
                "score": score,
                "category": category,
                "bonus": bonus,
                "game_finished": True,
            }

        db.commit()

        return {
            "score": score,
            "category": category,
            "bonus": bonus,
            "game_finished": False,
        }

    # ── Timeout handling ───────────────────────────────────────────────

    def handle_timeout(
        self,
        db: Session,
        game_id: str,
        user_id: str,
        dice: list[int],
    ) -> dict:
        """Auto-select best available category for the timed-out player's dice.

        Records the score and advances the turn. Returns the record_score
        result dict (score, category, bonus, game_finished).
        """
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise ValueError("Game not found")

        category, score = auto_select_category(dice, user_id, game_id, db)
        return self.record_score(db, game_id, user_id, category, score)

    # ── Player leave ───────────────────────────────────────────────────

    def handle_player_leave(self, db: Session, game_id: str, user_id: str) -> dict:
        """Handle a player leaving mid-game: fill remaining categories with 0."""
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise ValueError("Game not found")

        # Auto-fill remaining categories with 0.
        used = {
            row.category
            for row in db.query(Scoreboard)
            .filter_by(game_id=game_id, user_id=user_id)
            .all()
        }
        for cat in CATEGORIES:
            if cat not in used:
                entry = Scoreboard(game_id=game_id, user_id=user_id, category=cat, score=0)
                db.add(entry)
        db.flush()

        # If it was the current player's turn, advance.
        players = (
            db.query(GamePlayer)
            .filter_by(game_id=game_id)
            .order_by(GamePlayer.join_order)
            .all()
        )
        if players:
            current_gp = players[game.current_player_index % len(players)]
            if current_gp.user_id == user_id:
                game.current_player_index = (game.current_player_index + 1) % len(players)

        # Check if game should end (all categories filled for all players).
        player_count = len(players)
        total_needed = player_count * len(CATEGORIES)
        total_filled = db.query(Scoreboard).filter_by(game_id=game_id).count()

        game_finished = total_filled >= total_needed
        if game_finished and game.status == "playing":
            self.finish_game(db, game_id)

        db.commit()

        return {"game_finished": game_finished}

    # ── Finish game ────────────────────────────────────────────────────

    def finish_game(self, db: Session, game_id: str) -> list[dict]:
        """Calculate final scores, save results, update user stats, set FINISHED."""
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise ValueError("Game not found")

        players = (
            db.query(GamePlayer)
            .filter_by(game_id=game_id)
            .order_by(GamePlayer.join_order)
            .all()
        )

        results_data: list[dict] = []

        for gp in players:
            entries = (
                db.query(Scoreboard)
                .filter_by(game_id=game_id, user_id=gp.user_id)
                .all()
            )
            score_map = {e.category: e.score for e in entries}

            top_sum = sum(score_map.get(cat, 0) for cat in UPPER_CATEGORIES)
            bottom_sum = sum(score_map.get(cat, 0) for cat in LOWER_CATEGORIES)
            bonus = calculate_bonus(top_sum)
            total = top_sum + bottom_sum + bonus

            results_data.append({
                "user_id": gp.user_id,
                "total_score": total,
                "top_section_sum": top_sum,
                "bottom_section_sum": bottom_sum,
                "bonus": bonus,
            })

        # Sort by total_score descending to assign ranks.
        results_data.sort(key=lambda x: x["total_score"], reverse=True)

        for rank, rd in enumerate(results_data, start=1):
            result = GameResult(
                game_id=game_id,
                user_id=rd["user_id"],
                rank=rank,
                total_score=rd["total_score"],
                top_section_sum=rd["top_section_sum"],
                bottom_section_sum=rd["bottom_section_sum"],
                bonus=rd["bonus"],
            )
            db.add(result)

            # Update user stats (rank 1 counts as a win).
            update_stats(db, rd["user_id"], rd["total_score"], is_win=(rank == 1))

        game.status = "finished"
        game.finished_at = datetime.now(timezone.utc)
        db.commit()

        return results_data

    # ── Results ────────────────────────────────────────────────────────

    def get_game_results(self, db: Session, game_id: str) -> dict:
        """Build the final results payload for a finished game.

        Returns {"game_id", "players", "finished_at"} with players sorted by
        rank and per-category scores pulled from the scoreboards.
        """
        game = db.query(Game).filter(Game.id == game_id).first()
        if not game:
            raise ValueError("Game not found")
        if game.status != "finished":
            raise ValueError("Game has not finished")

        results = (
            db.query(GameResult)
            .filter_by(game_id=game_id)
            .order_by(GameResult.rank)
            .all()
        )

        players = []
        for r in results:
            user = db.query(User).filter(User.id == r.user_id).first()
            entries = (
                db.query(Scoreboard)
                .filter_by(game_id=game_id, user_id=r.user_id)
                .all()
            )
            players.append({
                "user_id": r.user_id,
                "display_name": user.nickname if user else "Unknown",
                "rank": r.rank,
                "total_score": r.total_score,
                "scores": {e.category: e.score for e in entries},
                "top_section_sum": r.top_section_sum,
                "bottom_section_sum": r.bottom_section_sum,
                "bonus": r.bonus,
            })

        return {
            "game_id": game_id,
            "players": players,
            "finished_at": game.finished_at.isoformat() if game.finished_at else "",
        }
