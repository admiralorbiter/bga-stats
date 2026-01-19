"""
SQLAlchemy ORM models for BGA Stats application.
Defines Player, Game, and PlayerGameStat models for Phase 1.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Game(Base):
    """
    Represents a game on BoardGameArena.
    """
    __tablename__ = 'games'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bga_game_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # alpha, beta, published
    premium = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    player_stats = relationship('PlayerGameStat', back_populates='game')

    def __repr__(self):
        return f"<Game(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"


class Player(Base):
    """
    Represents a player on BoardGameArena.
    Stores overall player statistics and profile information.
    """
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bga_player_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    xp = Column(Integer, default=0)
    karma = Column(Integer, default=0)  # Percentage 0-100
    matches_total = Column(Integer, default=0)
    wins_total = Column(Integer, default=0)
    abandoned = Column(Integer, default=0)
    timeout = Column(Integer, default=0)
    recent_matches = Column(Integer, default=0)
    last_seen_days = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    game_stats = relationship('PlayerGameStat', back_populates='player', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Player(id={self.id}, bga_player_id={self.bga_player_id}, name='{self.name}')>"


class PlayerGameStat(Base):
    """
    Represents a player's statistics for a specific game.
    Links players to games with their performance metrics (ELO, rank, matches played/won).
    """
    __tablename__ = 'player_game_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id', ondelete='CASCADE'), nullable=False)
    game_id = Column(Integer, ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    elo = Column(String(50))  # String to handle "N/A" values
    rank = Column(String(50))  # String to handle empty/unranked
    played = Column(Integer, default=0, nullable=False)
    won = Column(Integer, default=0, nullable=False)
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    player = relationship('Player', back_populates='game_stats')
    game = relationship('Game', back_populates='player_stats')
    
    # Unique constraint: one stat per player-game combination
    __table_args__ = (
        UniqueConstraint('player_id', 'game_id', name='uix_player_game'),
    )

    def __repr__(self):
        return f"<PlayerGameStat(id={self.id}, player_id={self.player_id}, game_id={self.game_id})>"
