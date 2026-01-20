"""
Import service for BGA Stats application.
Handles parsing and importing data into the database.
"""

from datetime import datetime
from backend.db import get_session
from backend.models import (
    Player, Game, PlayerGameStat,
    Match, MatchMove,
    Tournament, TournamentMatch, TournamentMatchPlayer
)
from backend.parsers.player_stats_parser import parse_player_stats
from backend.parsers.game_list_parser import parse_game_list
from backend.parsers.move_stats_parser import parse_move_stats
from backend.parsers.tournament_stats_parser import parse_tournament_stats
from backend.parsers.exceptions import ValidationError, ParseError


def detect_import_type(raw_text):
    """
    Auto-detect the import format type based on content signatures.
    
    Args:
        raw_text (str): Raw import data
        
    Returns:
        str: Import type ('player_stats', 'move_stats', 'game_list', 'tournament_stats', or 'unknown')
    """
    if not raw_text or not raw_text.strip():
        return 'unknown'
    
    # Check for Player Stats signatures
    if '\tXP\t' in raw_text and '\tRecent games\t' in raw_text:
        return 'player_stats'
    
    # Check for Move Stats (semicolon-delimited)
    if ';' in raw_text and '\t' not in raw_text:
        return 'move_stats'
    
    # Check for Tournament Stats (has double-tab and specific pattern)
    if '\t\t' in raw_text and any(line.split('\t')[2].strip() in ['0', '1'] for line in raw_text.split('\n') if line.count('\t') >= 10):
        return 'tournament_stats'
    
    # Check for Game List (5 tab-separated columns, numeric first column)
    lines = raw_text.strip().split('\n')
    if lines:
        first_line = lines[0].split('\t')
        if len(first_line) == 5 and first_line[0].strip().isdigit() and first_line[4].strip() in ['0', '1']:
            return 'game_list'
    
    return 'unknown'


def import_player_stats(session, parsed_data):
    """
    Import parsed player statistics data into the database.
    Uses upsert logic to update existing records or create new ones.
    
    Args:
        session: SQLAlchemy database session
        parsed_data (list): List of player dictionaries from parser
        
    Returns:
        dict: Import results with counts of created/updated records
    """
    players_created = 0
    players_updated = 0
    games_created = 0
    stats_created = 0
    stats_updated = 0
    
    # Get the minimum bga_game_id currently in database
    # Use negative numbers as placeholders to avoid conflicts
    min_game_id = session.query(Game.bga_game_id).filter(Game.bga_game_id < 0).order_by(Game.bga_game_id).first()
    next_placeholder_id = (min_game_id[0] - 1) if min_game_id else -1
    
    for player_data in parsed_data:
        # Upsert Player
        player_record = session.query(Player).filter_by(
            bga_player_id=player_data['bga_player_id']
        ).first()
        
        if player_record:
            # Update existing player
            player_record.name = player_data['name']
            player_record.xp = player_data['xp']
            player_record.karma = player_data['karma']
            player_record.matches_total = player_data['matches_total']
            player_record.wins_total = player_data['wins_total']
            player_record.abandoned = player_data['abandoned']
            player_record.timeout = player_data['timeout']
            player_record.recent_matches = player_data['recent_matches']
            player_record.last_seen_days = player_data['last_seen_days']
            player_record.updated_at = datetime.utcnow()
            players_updated += 1
        else:
            # Create new player
            player_record = Player(
                bga_player_id=player_data['bga_player_id'],
                name=player_data['name'],
                xp=player_data['xp'],
                karma=player_data['karma'],
                matches_total=player_data['matches_total'],
                wins_total=player_data['wins_total'],
                abandoned=player_data['abandoned'],
                timeout=player_data['timeout'],
                recent_matches=player_data['recent_matches'],
                last_seen_days=player_data['last_seen_days']
            )
            session.add(player_record)
            players_created += 1
        
        # Flush to get player ID for relationships
        session.flush()
        
        # Process game stats
        for game_stat in player_data['game_stats']:
            # Upsert Game (by name, since we don't have bga_game_id yet)
            game_record = session.query(Game).filter_by(
                name=game_stat['game_name']
            ).first()
            
            if not game_record:
                # Create placeholder game record
                # Use negative IDs as placeholders until GameList import provides real IDs
                game_record = Game(
                    bga_game_id=next_placeholder_id,
                    name=game_stat['game_name'],
                    display_name=game_stat['game_name'],
                    status='unknown',
                    premium=False
                )
                session.add(game_record)
                session.flush()  # Get game ID
                games_created += 1
                next_placeholder_id -= 1  # Decrement for next game
            
            # Upsert PlayerGameStat
            stat_record = session.query(PlayerGameStat).filter_by(
                player_id=player_record.id,
                game_id=game_record.id
            ).first()
            
            if stat_record:
                # Update existing stat
                stat_record.elo = game_stat['elo']
                stat_record.rank = game_stat['rank']
                stat_record.played = game_stat['played']
                stat_record.won = game_stat['won']
                stat_record.imported_at = datetime.utcnow()
                stat_record.updated_at = datetime.utcnow()
                stats_updated += 1
            else:
                # Create new stat
                stat_record = PlayerGameStat(
                    player_id=player_record.id,
                    game_id=game_record.id,
                    elo=game_stat['elo'],
                    rank=game_stat['rank'],
                    played=game_stat['played'],
                    won=game_stat['won']
                )
                session.add(stat_record)
                stats_created += 1
    
    return {
        'players_created': players_created,
        'players_updated': players_updated,
        'games_created': games_created,
        'game_stats_created': stats_created,
        'game_stats_updated': stats_updated
    }


def import_game_list(session, parsed_data):
    """
    Import parsed game list data into the database.
    
    Args:
        session: SQLAlchemy database session
        parsed_data (list): List of game dictionaries from parser
        
    Returns:
        dict: Import results with counts
    """
    games_created = 0
    games_updated = 0
    
    for game_data in parsed_data:
        # Upsert Game
        game_record = session.query(Game).filter_by(
            bga_game_id=game_data['bga_game_id']
        ).first()
        
        if game_record:
            # Update existing game
            game_record.name = game_data['name']
            game_record.display_name = game_data['display_name']
            game_record.status = game_data['status']
            game_record.premium = game_data['premium']
            game_record.updated_at = datetime.utcnow()
            games_updated += 1
        else:
            # Create new game
            game_record = Game(
                bga_game_id=game_data['bga_game_id'],
                name=game_data['name'],
                display_name=game_data['display_name'],
                status=game_data['status'],
                premium=game_data['premium']
            )
            session.add(game_record)
            games_created += 1
    
    return {
        'games_created': games_created,
        'games_updated': games_updated
    }


def import_move_stats(session, parsed_data):
    """
    Import parsed move stats data into the database.
    
    Args:
        session: SQLAlchemy database session
        parsed_data (dict): Match dictionary with moves from parser
        
    Returns:
        dict: Import results with counts
    """
    # Upsert Match
    match_record = session.query(Match).filter_by(
        bga_table_id=parsed_data['table_id']
    ).first()
    
    if match_record:
        # Update existing match
        match_record.game_name = parsed_data['game_name']
        match_record.imported_at = datetime.utcnow()
        match_record.updated_at = datetime.utcnow()
        matches_updated = 1
        matches_created = 0
        
        # Delete old moves
        session.query(MatchMove).filter_by(match_id=match_record.id).delete()
    else:
        # Create new match
        match_record = Match(
            bga_table_id=parsed_data['table_id'],
            game_name=parsed_data['game_name']
        )
        session.add(match_record)
        session.flush()  # Get match ID
        matches_created = 1
        matches_updated = 0
    
    # Add moves
    moves_created = 0
    for move_data in parsed_data['moves']:
        move_record = MatchMove(
            match_id=match_record.id,
            move_no=move_data['move_no'],
            player_name=move_data['player_name'],
            datetime_local=move_data['datetime_local'],
            datetime_excel=move_data['datetime_excel'],
            remaining_time=move_data['remaining_time']
        )
        session.add(move_record)
        moves_created += 1
    
    return {
        'matches_created': matches_created,
        'matches_updated': matches_updated,
        'moves_created': moves_created
    }


def import_tournament_stats(session, parsed_data):
    """
    Import parsed tournament stats data into the database.
    
    Args:
        session: SQLAlchemy database session
        parsed_data (list): List of tournament dictionaries from parser
        
    Returns:
        dict: Import results with counts
    """
    tournaments_created = 0
    tournaments_updated = 0
    tournament_matches_created = 0
    
    for tournament_data in parsed_data:
        # Upsert Tournament
        tournament_record = session.query(Tournament).filter_by(
            bga_tournament_id=tournament_data['tournament_id']
        ).first()
        
        if tournament_record:
            # Update existing tournament
            tournament_record.name = tournament_data['name']
            tournament_record.game_name = tournament_data['game_name']
            tournament_record.start_time = tournament_data['start_time']
            tournament_record.end_time = tournament_data['end_time']
            tournament_record.rounds = tournament_data['rounds']
            tournament_record.round_limit = tournament_data['round_limit']
            tournament_record.total_matches = tournament_data['total_matches']
            tournament_record.timeout_matches = tournament_data['timeout_matches']
            tournament_record.player_count = tournament_data['player_count']
            tournament_record.updated_at = datetime.utcnow()
            tournaments_updated += 1
            
            # Delete old matches
            session.query(TournamentMatch).filter_by(tournament_id=tournament_record.id).delete()
        else:
            # Create new tournament
            tournament_record = Tournament(
                bga_tournament_id=tournament_data['tournament_id'],
                name=tournament_data['name'],
                game_name=tournament_data['game_name'],
                start_time=tournament_data['start_time'],
                end_time=tournament_data['end_time'],
                rounds=tournament_data['rounds'],
                round_limit=tournament_data['round_limit'],
                total_matches=tournament_data['total_matches'],
                timeout_matches=tournament_data['timeout_matches'],
                player_count=tournament_data['player_count']
            )
            session.add(tournament_record)
            tournaments_created += 1
        
        session.flush()  # Get tournament ID
        
        # Add matches
        for match_data in tournament_data['matches']:
            match_record = TournamentMatch(
                tournament_id=tournament_record.id,
                bga_table_id=match_data['table_id'],
                is_timeout=match_data['is_timeout'],
                progress=match_data['progress']
            )
            session.add(match_record)
            session.flush()  # Get match ID
            tournament_matches_created += 1
            
            # Add players
            for player_data in match_data['players']:
                player_record = TournamentMatchPlayer(
                    tournament_match_id=match_record.id,
                    player_name=player_data['name'],
                    remaining_time_seconds=player_data['remaining_time_seconds'],
                    points=player_data['points']
                )
                session.add(player_record)
    
    return {
        'tournaments_created': tournaments_created,
        'tournaments_updated': tournaments_updated,
        'tournament_matches_created': tournament_matches_created
    }


def import_data(raw_text, import_type=None):
    """
    Main import function. Orchestrates parsing, importing, and transaction management.
    
    Args:
        raw_text (str): Raw import data
        import_type (str, optional): Import type. If None, will auto-detect.
        
    Returns:
        dict: Result dictionary with success status, import type, and results/error
    """
    session = get_session()
    
    try:
        # Auto-detect if not specified
        if not import_type:
            import_type = detect_import_type(raw_text)
        
        if import_type == 'player_stats':
            parsed_data = parse_player_stats(raw_text)
            results = import_player_stats(session, parsed_data)
        elif import_type == 'game_list':
            parsed_data = parse_game_list(raw_text)
            results = import_game_list(session, parsed_data)
        elif import_type == 'move_stats':
            parsed_data = parse_move_stats(raw_text)
            results = import_move_stats(session, parsed_data)
        elif import_type == 'tournament_stats':
            parsed_data = parse_tournament_stats(raw_text)
            results = import_tournament_stats(session, parsed_data)
        else:
            return {
                'success': False,
                'error': f"Unsupported import type: {import_type}",
                'error_type': 'UnsupportedTypeError'
            }
        
        # Commit transaction
        session.commit()
        
        return {
            'success': True,
            'import_type': import_type,
            'results': results
        }
            
    except ValidationError as e:
        session.rollback()
        return {
            'success': False,
            'error': str(e),
            'error_type': 'ValidationError'
        }
    except ParseError as e:
        session.rollback()
        return {
            'success': False,
            'error': str(e),
            'error_type': 'ParseError'
        }
    except Exception as e:
        session.rollback()
        return {
            'success': False,
            'error': f"Import failed: {str(e)}",
            'error_type': 'ImportError'
        }
    finally:
        session.close()
