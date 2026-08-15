import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


# ── User ──────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(20), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nickname = Column(String(20), unique=True, nullable=False)
    total_games = Column(Integer, default=0, nullable=False)
    total_wins = Column(Integer, default=0, nullable=False)
    cumulative_score = Column(Integer, default=0, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    games_hosted = relationship("Game", back_populates="host")
    game_results = relationship("GameResult", back_populates="user")
    scoreboards = relationship("Scoreboard", back_populates="user")
    game_players = relationship("GamePlayer", back_populates="user")


# ── Game ──────────────────────────────────────────────────────────────

class Game(Base):
    __tablename__ = "games"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    host_user_id = Column(
        String, ForeignKey("users.id"), nullable=False
    )
    join_code = Column(String(6), unique=True, nullable=False)
    status = Column(String, default="waiting", nullable=False)
    current_player_index = Column(Integer, default=0, nullable=False)
    current_round = Column(Integer, default=1, nullable=False)
    turn_time_limit = Column(Integer, default=60, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    finished_at = Column(DateTime, nullable=True)

    host = relationship("User", back_populates="games_hosted", foreign_keys=[host_user_id])
    players = relationship("GamePlayer", back_populates="game")
    scoreboards = relationship("Scoreboard", back_populates="game")
    results = relationship("GameResult", back_populates="game")


# ── GamePlayer (association table with extra columns) ────────────────

class GamePlayer(Base):
    __tablename__ = "game_players"

    game_id = Column(String, ForeignKey("games.id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    join_order = Column(Integer, nullable=False)

    game = relationship("Game", back_populates="players")
    user = relationship("User", back_populates="game_players")


# ── Scoreboard ────────────────────────────────────────────────────────

class Scoreboard(Base):
    __tablename__ = "scoreboards"

    game_id = Column(String, ForeignKey("games.id"), primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    category = Column(String, primary_key=True, nullable=False)
    score = Column(Integer, nullable=False, default=0)

    game = relationship("Game", back_populates="scoreboards")
    user = relationship("User", back_populates="scoreboards")


# ── GameResult ────────────────────────────────────────────────────────

class GameResult(Base):
    __tablename__ = "game_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    rank = Column(Integer, nullable=False)
    total_score = Column(Integer, nullable=False)
    top_section_sum = Column(Integer, nullable=False, default=0)
    bottom_section_sum = Column(Integer, nullable=False, default=0)
    bonus = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    game = relationship("Game", back_populates="results")
    user = relationship("User", back_populates="game_results")
