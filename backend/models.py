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


# Phase 2 Models: Matches and Move Stats

class Match(Base):
    """
    Represents a match/game table on BGA.
    Stores match metadata and links to move history.
    """
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bga_table_id = Column(Integer, unique=True, nullable=False, index=True)
    game_name = Column(String(255), nullable=False)
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    moves = relationship('MatchMove', back_populates='match', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Match(id={self.id}, bga_table_id={self.bga_table_id}, game_name='{self.game_name}')>"


class MatchMove(Base):
    """
    Represents a single move in a match.
    Stores move number, timestamp, player, and remaining time.
    """
    __tablename__ = 'match_moves'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey('matches.id', ondelete='CASCADE'), nullable=False)
    move_no = Column(String(50))  # Can be "null" for some moves
    player_name = Column(String(255), nullable=False)
    datetime_local = Column(String(255))  # Localized datetime string
    datetime_excel = Column(String(50))   # Excel datetime serial value
    remaining_time = Column(String(50))   # Remaining time string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    match = relationship('Match', back_populates='moves')
    
    def __repr__(self):
        return f"<MatchMove(id={self.id}, match_id={self.match_id}, move_no={self.move_no})>"


# Phase 2 Models: Tournaments

class Tournament(Base):
    """
    Represents a tournament on BGA.
    Stores tournament metadata and summary information.
    """
    __tablename__ = 'tournaments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    bga_tournament_id = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    game_name = Column(String(255), nullable=False)
    start_time = Column(String(255))  # Localized datetime string
    end_time = Column(String(255))    # Localized datetime string
    rounds = Column(Integer, default=0)
    round_limit = Column(Integer, default=0)  # Hours
    total_matches = Column(Integer, default=0)
    timeout_matches = Column(Integer, default=0)
    player_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    matches = relationship('TournamentMatch', back_populates='tournament', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Tournament(id={self.id}, bga_tournament_id={self.bga_tournament_id}, name='{self.name}')>"


class TournamentMatch(Base):
    """
    Represents a match within a tournament.
    Links to the tournament and stores match-specific data.
    """
    __tablename__ = 'tournament_matches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id', ondelete='CASCADE'), nullable=False)
    bga_table_id = Column(Integer, nullable=False, index=True)
    is_timeout = Column(Boolean, default=False, nullable=False)
    progress = Column(Integer, default=0)  # 0-100
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    tournament = relationship('Tournament', back_populates='matches')
    players = relationship('TournamentMatchPlayer', back_populates='match', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<TournamentMatch(id={self.id}, tournament_id={self.tournament_id}, bga_table_id={self.bga_table_id})>"


class TournamentMatchPlayer(Base):
    """
    Represents a player's participation in a tournament match.
    Stores player name, remaining time, and points earned.
    """
    __tablename__ = 'tournament_match_players'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_match_id = Column(Integer, ForeignKey('tournament_matches.id', ondelete='CASCADE'), nullable=False)
    player_name = Column(String(255), nullable=False)
    remaining_time_seconds = Column(Integer)  # Can be negative for timeouts
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    match = relationship('TournamentMatch', back_populates='players')
    
    def __repr__(self):
        return f"<TournamentMatchPlayer(id={self.id}, player_name='{self.player_name}', points={self.points})>"
