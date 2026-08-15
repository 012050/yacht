"""Test game flow: create, join, start, turn handling, finish."""
import pytest
from app.database.models import User, Game, GamePlayer, Scoreboard
from app.services.game_service import GameService
from app.services.auth_service import hash_password
from app.services.scoring import CATEGORIES, UPPER_CATEGORIES, LOWER_CATEGORIES


@pytest.fixture
def game_svc():
    return GameService()


@pytest.fixture
def sample_user(db_session):
    user = User(
        id="test-user-1",
        username="testuser",
        password_hash=hash_password("password"),
        nickname="TestPlayer",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_user2(db_session):
    user = User(
        id="test-user-2",
        username="testuser2",
        password_hash=hash_password("password"),
        nickname="TestPlayer2",
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestCreateGame:
    def test_create_game(self, db_session, sample_user, game_svc):
        game = game_svc.create_game(db_session, sample_user.id)
        assert game is not None
        assert game.status == "waiting"
        assert len(game.join_code) == 6
        assert game.host_user_id == sample_user.id

    def test_create_game_has_host_player(self, db_session, sample_user, game_svc):
        game = game_svc.create_game(db_session, sample_user.id)
        players = db_session.query(GamePlayer).filter_by(game_id=game.id).all()
        assert len(players) == 1
        assert players[0].user_id == sample_user.id

    def test_create_game_unique_join_code(self, db_session, sample_user, game_svc):
        game1 = game_svc.create_game(db_session, sample_user.id)
        # Need a second user for second game
        user2 = User(
            id="test-user-3",
            username="testuser3",
            password_hash=hash_password("password"),
            nickname="TestPlayer3",
        )
        db_session.add(user2)
        db_session.commit()
        game2 = game_svc.create_game(db_session, user2.id)
        assert game1.join_code != game2.join_code


class TestJoinGame:
    def test_join_game(self, db_session, sample_user, sample_user2, game_svc):
        game = game_svc.create_game(db_session, sample_user.id)
        result = game_svc.join_game(db_session, game.join_code, sample_user2.id)
        assert result.id == game.id
        players = db_session.query(GamePlayer).filter_by(game_id=game.id).all()
        assert len(players) == 2

    def test_join_nonexistent_game(self, db_session, sample_user, game_svc):
        with pytest.raises(ValueError, match="Game not found"):
            game_svc.join_game(db_session, "ZZZZZZ", sample_user.id)

    def test_join_twice(self, db_session, sample_user, sample_user2, game_svc):
        game = game_svc.create_game(db_session, sample_user.id)
        game_svc.join_game(db_session, game.join_code, sample_user2.id)
        with pytest.raises(ValueError, match="Already a player"):
            game_svc.join_game(db_session, game.join_code, sample_user2.id)


class TestStartGame:
    def test_start_game_as_host(self, db_session, sample_user, sample_user2, game_svc):
        game = game_svc.create_game(db_session, sample_user.id)
        game_svc.join_game(db_session, game.join_code, sample_user2.id)
        result = game_svc.start_game(db_session, game.id, sample_user.id)
        assert result.status == "playing"

    def test_start_game_not_host(self, db_session, sample_user, sample_user2, game_svc):
        game = game_svc.create_game(db_session, sample_user.id)
        game_svc.join_game(db_session, game.join_code, sample_user2.id)
        with pytest.raises(ValueError, match="Only the host"):
            game_svc.start_game(db_session, game.id, sample_user2.id)

    def test_start_game_one_player(self, db_session, sample_user, game_svc):
        game = game_svc.create_game(db_session, sample_user.id)
        with pytest.raises(ValueError, match="at least 2 players"):
            game_svc.start_game(db_session, game.id, sample_user.id)


class TestPlayerLeave:
    def test_leave_fills_remaining_categories(self, db_session, sample_user, sample_user2, game_svc):
        game = game_svc.create_game(db_session, sample_user.id)
        game_svc.join_game(db_session, game.join_code, sample_user2.id)
        game_svc.start_game(db_session, game.id, sample_user.id)
        game_svc.handle_player_leave(db_session, game.id, sample_user2.id)
        # Check remaining categories are filled with 0
        entries = db_session.query(Scoreboard).filter_by(
            game_id=game.id, user_id=sample_user2.id
        ).all()
        assert len(entries) == len(CATEGORIES)
        for entry in entries:
            assert entry.score == 0


class TestFinishGame:
    def test_finish_game_calculates_scores(self, db_session, sample_user, sample_user2, game_svc):
        game = game_svc.create_game(db_session, sample_user.id)
        game_svc.join_game(db_session, game.join_code, sample_user2.id)
        game_svc.start_game(db_session, game.id, sample_user.id)

        # Manually fill scoreboards
        for cat in CATEGORIES:
            db_session.add(Scoreboard(
                game_id=game.id, user_id=sample_user.id, category=cat, score=10
            ))
            db_session.add(Scoreboard(
                game_id=game.id, user_id=sample_user2.id, category=cat, score=5
            ))
        db_session.commit()

        results = game_svc.finish_game(db_session, game.id)
        assert game.status == "finished"
        assert len(results) == 2
        # First player has higher score
        assert results[0]["user_id"] == sample_user.id


class TestTimeout:
    def test_timeout_records_best_category(self, db_session, sample_user, sample_user2, game_svc):
        game = game_svc.create_game(db_session, sample_user.id)
        game_svc.join_game(db_session, game.join_code, sample_user2.id)
        game_svc.start_game(db_session, game.id, sample_user.id)

        # It is sample_user's turn (index 0). Five 1s: yacht (50) is best.
        result = game_svc.handle_timeout(
            db_session, game.id, sample_user.id, [1, 1, 1, 1, 1]
        )
        assert result["category"] == "yacht"
        assert result["score"] == 50
        assert result["game_finished"] is False

        entry = db_session.query(Scoreboard).filter_by(
            game_id=game.id, user_id=sample_user.id, category="yacht"
        ).first()
        assert entry.score == 50

        # Turn advanced to the next player.
        assert game.current_player_index == 1

    def test_timeout_skips_used_categories(self, db_session, sample_user, sample_user2, game_svc):
        game = game_svc.create_game(db_session, sample_user.id)
        game_svc.join_game(db_session, game.join_code, sample_user2.id)
        game_svc.start_game(db_session, game.id, sample_user.id)

        # Pre-use yacht and ones; for [1,1,1,1,1] the best available is
        # four_of_a_kind (1*5+1 = 6), beating chance (5).
        db_session.add(Scoreboard(game_id=game.id, user_id=sample_user.id, category="yacht", score=50))
        db_session.add(Scoreboard(game_id=game.id, user_id=sample_user.id, category="ones", score=5))
        db_session.commit()

        result = game_svc.handle_timeout(
            db_session, game.id, sample_user.id, [1, 1, 1, 1, 1]
        )
        assert result["category"] == "four_of_a_kind"
        assert result["score"] == 6

    def test_timeout_wrong_player_rejected(self, db_session, sample_user, sample_user2, game_svc):
        game = game_svc.create_game(db_session, sample_user.id)
        game_svc.join_game(db_session, game.join_code, sample_user2.id)
        game_svc.start_game(db_session, game.id, sample_user.id)
        with pytest.raises(ValueError, match="Not your turn"):
            game_svc.handle_timeout(
                db_session, game.id, sample_user2.id, [2, 2, 2, 2, 2]
            )


class TestGameEnd:
    def test_last_score_finishes_game_without_autoflush(
        self, no_autoflush_session, game_svc
    ):
        """Regression: production session has autoflush=False, so the final
        record_score must see its own entry and end the game."""
        db = no_autoflush_session
        u1 = User(
            id="u1", username="u1", password_hash=hash_password("pw"), nickname="U1"
        )
        u2 = User(
            id="u2", username="u2", password_hash=hash_password("pw"), nickname="U2"
        )
        db.add_all([u1, u2])
        db.commit()

        game = game_svc.create_game(db, u1.id)
        game_svc.join_game(db, game.join_code, u2.id)
        game_svc.start_game(db, game.id, u1.id)

        finished = False
        for cat in CATEGORIES:
            # Turns alternate: u1 (join order 1) then u2 (join order 2).
            result = game_svc.record_score(db, game.id, u1.id, cat, 1)
            finished = finished or result["game_finished"]
            result = game_svc.record_score(db, game.id, u2.id, cat, 2)
            finished = finished or result["game_finished"]

        assert finished is True
        db.refresh(game)
        assert game.status == "finished"


class TestGameResults:
    def _play_full_game(self, db, game_svc):
        u1 = User(
            id="u1", username="u1", password_hash=hash_password("pw"), nickname="Alice"
        )
        u2 = User(
            id="u2", username="u2", password_hash=hash_password("pw"), nickname="Bob"
        )
        db.add_all([u1, u2])
        db.commit()

        game = game_svc.create_game(db, u1.id)
        game_svc.join_game(db, game.join_code, u2.id)
        game_svc.start_game(db, game.id, u1.id)
        return game, u1, u2

    def test_results_include_recorded_scores(self, no_autoflush_session, game_svc):
        db = no_autoflush_session
        game, u1, u2 = self._play_full_game(db, game_svc)

        for cat in CATEGORIES:
            game_svc.record_score(db, game.id, u1.id, cat, 7)
            game_svc.record_score(db, game.id, u2.id, cat, 3)

        data = game_svc.get_game_results(db, game.id)
        assert data["game_id"] == game.id
        assert len(data["players"]) == 2

        first = data["players"][0]
        assert first["user_id"] == u1.id
        assert first["display_name"] == "Alice"
        assert first["rank"] == 1
        assert first["total_score"] == 7 * len(CATEGORIES)
        assert first["scores"] == {cat: 7 for cat in CATEGORIES}
        assert first["top_section_sum"] == 7 * len(UPPER_CATEGORIES)
        assert first["bottom_section_sum"] == 7 * len(LOWER_CATEGORIES)
        assert first["bonus"] == 0

        second = data["players"][1]
        assert second["user_id"] == u2.id
        assert second["rank"] == 2
        assert second["total_score"] == 3 * len(CATEGORIES)

    def test_results_before_finish_rejected(self, no_autoflush_session, game_svc):
        db = no_autoflush_session
        game, u1, _ = self._play_full_game(db, game_svc)
        game_svc.record_score(db, game.id, u1.id, "chance", 5)

        with pytest.raises(ValueError, match="has not finished"):
            game_svc.get_game_results(db, game.id)

    def test_results_unknown_game(self, no_autoflush_session, game_svc):
        with pytest.raises(ValueError, match="Game not found"):
            game_svc.get_game_results(no_autoflush_session, "no-such-game")


class TestRollDice:
    def _playing_game(self, db, game_svc):
        u1 = User(
            id="u1", username="u1", password_hash=hash_password("pw"), nickname="Alice"
        )
        u2 = User(
            id="u2", username="u2", password_hash=hash_password("pw"), nickname="Bob"
        )
        db.add_all([u1, u2])
        db.commit()

        game = game_svc.create_game(db, u1.id)
        game_svc.join_game(db, game.join_code, u2.id)
        game_svc.start_game(db, game.id, u1.id)
        return game, u1

    def test_first_roll_starts_with_two_rerolls(self, db_session, game_svc):
        game, u1 = self._playing_game(db_session, game_svc)
        result = game_svc.roll_dice(db_session, game.id, u1.id)
        assert len(result["values"]) == 5
        assert result["rollsRemaining"] == 2
        assert result["keptIndices"] == []

    def test_reroll_without_keeps_still_decrements(self, db_session, game_svc):
        """Regression: a reroll with no dice kept must not reset the counter."""
        game, u1 = self._playing_game(db_session, game_svc)
        first = game_svc.roll_dice(db_session, game.id, u1.id)

        second = game_svc.roll_dice(
            db_session, game.id, u1.id, [], first["values"], first["rollsRemaining"]
        )
        assert second["rollsRemaining"] == 1

        third = game_svc.roll_dice(
            db_session, game.id, u1.id, [], second["values"], second["rollsRemaining"]
        )
        assert third["rollsRemaining"] == 0

    def test_reroll_with_none_kept_indices_still_decrements(self, db_session, game_svc):
        """Regression: kept_indices=None with values present is a reroll,
        not a first roll (the websocket layer used to normalize [] to None)."""
        game, u1 = self._playing_game(db_session, game_svc)
        first = game_svc.roll_dice(db_session, game.id, u1.id)

        result = game_svc.roll_dice(
            db_session, game.id, u1.id, None, first["values"], first["rollsRemaining"]
        )
        assert result["rollsRemaining"] == 1

    def test_reroll_keeps_selected_dice(self, db_session, game_svc):
        game, u1 = self._playing_game(db_session, game_svc)
        first = game_svc.roll_dice(db_session, game.id, u1.id)

        result = game_svc.roll_dice(
            db_session, game.id, u1.id, [0, 2], first["values"], first["rollsRemaining"]
        )
        assert result["values"][0] == first["values"][0]
        assert result["values"][2] == first["values"][2]
        assert result["rollsRemaining"] == 1
        assert result["keptIndices"] == [0, 2]
