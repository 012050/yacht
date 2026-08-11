from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(20), unique=True, nullable=False, index=True)
    nickname = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    games_created = relationship("Game", foreign_keys="Game.host_user_id", back_populates="host")
    game_players = relationship("GamePlayer", back_populates="user")
    game_results = relationship("GameResult", back_populates="user")


class Game(Base):
    __tablename__ = "games"

    id = Column(String(36), primary_key=True)
    join_code = Column(String(6), unique=True, nullable=False, index=True)
    host_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    state = Column(String(20), nullable=False, default="created")
    timeout_duration = Column(Integer, nullable=False, default=60)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    host = relationship("User", foreign_keys=[host_user_id], back_populates="games_created")
    players = relationship("GamePlayer", back_populates="game")
    scoreboards = relationship("Scoreboard", back_populates="game")


class GamePlayer(Base):
    __tablename__ = "game_players"

    game_id = Column(String(36), ForeignKey("games.id"), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    join_order = Column(Integer, nullable=False)
    is_host = Column(Boolean, default=False)

    game = relationship("Game", back_populates="players")
    user = relationship("User", back_populates="game_players")


class Scoreboard(Base):
    __tablename__ = "scoreboards"

    game_id = Column(String(36), ForeignKey("games.id"), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    category = Column(String(20), primary_key=True)
    score = Column(Integer, nullable=False, default=0)

    game = relationship("Game", back_populates="scoreboards")


class GameResult(Base):
    __tablename__ = "game_results"

    id = Column(String(36), primary_key=True)
    game_id = Column(String(36), ForeignKey("games.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    rank = Column(Integer, nullable=False)
    total_score = Column(Integer, nullable=False)
    top_section_sum = Column(Integer, nullable=False)
    bottom_section_sum = Column(Integer, nullable=False)
    bonus = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="game_results")
