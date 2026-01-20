"""
Import service for BGA Stats application.
Handles parsing and importing data into the database.
"""

from datetime import datetime
from backend.db import get_session
from backend.models import Player, Game, PlayerGameStat
from backend.parsers.player_stats_parser import parse_player_stats
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
    
    # Future: Check for other import types
    # elif ';' in raw_text:
    #     # Could be Move Stats (semicolon-delimited)
    #     return 'move_stats'
    
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
            # Parse the data
            parsed_data = parse_player_stats(raw_text)
            
            # Import to database
            results = import_player_stats(session, parsed_data)
            
            # Commit transaction
            session.commit()
            
            return {
                'success': True,
                'import_type': import_type,
                'results': results
            }
        else:
            return {
                'success': False,
                'error': f"Unsupported import type: {import_type}",
                'error_type': 'UnsupportedTypeError'
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
