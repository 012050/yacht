import asyncio
import random
from datetime import datetime, timezone
import json

from app.services.scoring import (
    calculate_score, calculate_best_category, calculate_bonus,
    CATEGORIES, TOP_CATEGORIES, BOTTOM_CATEGORIES
)
from app.services.dice_service import DiceState

class GameState:
    def __init__(self, game_id, host_user_id, timeout_duration):
        self.game_id = game_id
        self.host_user_id = host_user_id
        self.timeout_duration = timeout_duration
        self.players = []
        self.player_order = []
        self.current_player_index = 0
        self.current_round = 0
        self.dice = DiceState()
        self.scoreboards = {}
        self.state = "created"
        self.started_at = None
        self.finished_at = None
        self.turn_start_time = None

    def join_player(self, user_id):
        if self.state != "created":
            raise ValueError("Already started")
        for p in self.players:
            if p["user_id"] == user_id:
                raise ValueError("Already joined")
        self.players.append({
            "user_id": user_id,
            "join_order": len(self.players) + 1,
            "is_host": user_id == self.host_user_id
        })
        if len(self.players) >= 2:
            self.state = "waiting"

    def start(self):
        if self.state != "waiting":
            raise ValueError("Can only start from waiting")
        self.player_order = [p["user_id"] for p in self.players]
        random.shuffle(self.player_order)
        self.current_player_index = 0
        self.current_round = 1
        self.state = "playing"
        self.started_at = datetime.now(timezone.utc)
        for uid in self.player_order:
            self.scoreboards[uid] = {}
        self.dice.reset()
        self.turn_start_time = datetime.now(timezone.utc)

    def get_current_user_id(self):
        if self.state != "playing":
            raise ValueError("Game not playing")
        return self.player_order[self.current_player_index]

    def roll_dice(self):
        if self.state != "playing":
            raise ValueError("Game not playing")
        return self.dice.roll()

    def keep_dice(self, indices):
        if self.state != "playing":
            raise ValueError("Game not playing")
        self.dice.keep(indices)

    def finish_rolls(self):
        if not self.dice.dice:
            self.dice.roll()

    def select_category(self, user_id, category):
        current = self.get_current_user_id()
        if user_id != current:
            raise ValueError("Not your turn")
        if category in self.scoreboards.get(user_id, {}):
            raise ValueError("Category already used")
        score = calculate_score(self.dice.dice, category)
        self.scoreboards[user_id][category] = score
        self._next_turn()
        return score

    def auto_select_category(self):
        current = self.get_current_user_id()
        used = set(self.scoreboards.get(current, {}).keys())
        result = calculate_best_category(self.dice.dice, used)
        if result:
            cat, score = result
            self.scoreboards[current][cat] = score
        self._next_turn()

    def pass_category(self, user_id):
        current = self.get_current_user_id()
        if user_id != current:
            raise ValueError("Not your turn")
        used = set(self.scoreboards.get(current, {}).keys())
        available = [c for c in CATEGORIES if c not in used]
        if available:
            self.scoreboards[current][available[0]] = 0
        self._next_turn()

    def player_leave(self, user_id):
        self.players = [p for p in self.players if p["user_id"] != user_id]
        if user_id in self.player_order:
            self.player_order.remove(user_id)
            if self.current_player_index >= len(self.player_order):
                self.current_player_index = 0
        if user_id in self.scoreboards:
            used = set(self.scoreboards[user_id].keys())
            for cat in CATEGORIES:
                if cat not in used:
                    self.scoreboards[user_id][cat] = 0
        if len(self.player_order) == 0:
            self.state = "finished"

    def _next_turn(self):
        current = self.get_current_user_id()
        if len(self.scoreboards.get(current, {})) >= 12:
            self.current_player_index += 1
            if self.current_player_index >= len(self.player_order):
                if self._all_categories_filled():
                    self.state = "finished"
                    return
                self.current_round += 1
                self.current_player_index = 0
        else:
            self.current_player_index += 1
            if self.current_player_index >= len(self.player_order):
                self.current_player_index = 0
        self.dice.reset()
        self.turn_start_time = datetime.now(timezone.utc)

    def _all_categories_filled(self):
        for uid in self.player_order:
            if len(self.scoreboards.get(uid, {})) < 12:
                return False
        return True

    def to_dict(self):
        return {
            "game_id": self.game_id, "state": self.state,
            "timeout_duration": self.timeout_duration,
            "players": [{"user_id": p["user_id"], "is_host": p["is_host"]} for p in self.players],
            "player_order": self.player_order,
            "current_player_index": self.current_player_index,
            "current_round": self.current_round,
            "dice": self.dice.dice, "rolls_left": self.dice.rolls_left,
            "scoreboards": self.scoreboards
        }

class GameService:
    def __init__(self):
        self._games = {}

    def _get_game(self, game_id):
        if game_id not in self._games:
            raise ValueError(f"Game {game_id} not found")
        return self._games[game_id]

    def create_game(self, game_id, host_user_id, timeout_duration):
        gs = GameState(game_id, host_user_id, timeout_duration)
        gs.join_player(host_user_id)
        self._games[game_id] = gs
        return gs

    def join_player(self, game_id, user_id):
        self._get_game(game_id).join_player(user_id)

    def start_game(self, game_id):
        self._get_game(game_id).start()

    def roll_dice(self, game_id):
        return self._get_game(game_id).roll_dice()

    def keep_dice(self, game_id, indices):
        self._get_game(game_id).keep_dice(indices)

    def finish_rolls(self, game_id):
        self._get_game(game_id).finish_rolls()

    def select_category(self, game_id, user_id, category, db):
        gs = self._get_game(game_id)
        score = gs.select_category(user_id, category)
        db.commit()

    def pass_category(self, game_id, user_id, db):
        gs = self._get_game(game_id)
        gs.pass_category(user_id)
        db.commit()

    def get_game_state(self, game_id):
        return self._get_game(game_id).to_dict()

    async def handle_session_recover(self, game_id, user_id, ws):
        gs = self._get_game(game_id)
        await ws.send_text(json.dumps({"type": "SESSION_RECOVERED", "payload": gs.to_dict()}))

    async def handle_roll(self, game_id, user_id):
        gs = self._get_game(game_id)
        dice = gs.roll_dice()
        return dice, gs.dice.rolls_left

    async def handle_keep(self, game_id, user_id, indices):
        gs = self._get_game(game_id)
        gs.keep_dice(indices)

    async def handle_finish_rolls(self, game_id, user_id):
        gs = self._get_game(game_id)
        gs.finish_rolls()

    async def handle_select_category(self, game_id, user_id, category):
        gs = self._get_game(game_id)
        score = gs.select_category(user_id, category)
        return score, gs.current_player_index

    async def handle_pass(self, game_id, user_id):
        gs = self._get_game(game_id)
        gs.pass_category(user_id)
        return gs.current_player_index

    async def handle_player_leave(self, game_id, user_id):
        gs = self._get_game(game_id)
        gs.player_leave(user_id)

    async def handle_auto_timeout(self, game_id):
        gs = self._get_game(game_id)
        gs.auto_select_category()

game_service = GameService()
