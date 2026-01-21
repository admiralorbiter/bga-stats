"""
API routes for BGA Stats application.
Provides REST endpoints for data import and retrieval.
"""

from flask import Blueprint, request, jsonify
from backend.services.import_service import import_data
from backend.models import (
    Player, PlayerGameStat, Game,
    Tournament, TournamentMatch, TournamentMatchPlayer
)
from backend.db import get_session

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/import', methods=['POST'])
def import_endpoint():
    """
    Import player statistics data.
    
    Accepts JSON with either:
    - {"data": "raw_tsv_text"} - auto-detects type
    - {"type": "player_stats", "data": "raw_tsv_text"} - explicit type
    
    Returns:
        JSON response with import results or error details
        
    Example success response:
        {
            "success": true,
            "import_type": "player_stats",
            "results": {
                "players_created": 2,
                "players_updated": 1,
                "games_created": 5,
                "game_stats_created": 8,
                "game_stats_updated": 2
            }
        }
        
    Example error response:
        {
            "success": false,
            "error": "Line 3: Expected at least 7 columns, got 6",
            "error_type": "ParseError"
        }
    """
    try:
        # Parse request body
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        if 'data' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: data'
            }), 400
        
        raw_text = data['data']
        import_type = data.get('type', None)  # Optional, will auto-detect
        
        # Call import service
        result = import_data(raw_text, import_type)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'error_type': 'ServerError'
        }), 500


@api_bp.route('/sync/session-info', methods=['GET'])
def sync_session_info():
    """
    Get information about the current BGA session.
    
    Returns:
        JSON response with session status
    """
    try:
        from backend.services.bga_session_service import get_session_service
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Playwright not installed. Use manual import at /import instead, or install Playwright: pip install playwright && playwright install chromium'
        }), 503
    
    try:
        service = get_session_service()
        info = service.get_session_info()
        
        if info:
            return jsonify({
                'success': True,
                'has_session': True,
                'info': info
            })
        else:
            return jsonify({
                'success': True,
                'has_session': False,
                'info': None
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/sync/login', methods=['POST'])
def sync_login():
    """
    Initiate BGA login flow.
    Opens a browser window for user to log in.
    
    Returns:
        JSON response with login status
    """
    try:
        from backend.services.bga_session_service import get_session_service
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Playwright not installed. Please install it: pip install playwright && playwright install chromium, or use manual import at /import'
        }), 503
    
    try:
        service = get_session_service()
        
        # Run login in a separate thread to avoid blocking
        result = {'success': False, 'message': 'Login initiated'}
        
        def do_login():
            nonlocal result
            result = service.initiate_login()
        
        # For now, run synchronously (blocking)
        # In production, you'd want to use async or background tasks
        do_login()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Login failed: {str(e)}'
        }), 500


@api_bp.route('/sync/logout', methods=['POST'])
def sync_logout():
    """
    Clear saved BGA session.
    
    Returns:
        JSON response with logout status
    """
    from backend.services.bga_session_service import get_session_service
    
    try:
        service = get_session_service()
        cleared = service.clear_session()
        
        return jsonify({
            'success': True,
            'cleared': cleared,
            'message': 'Session cleared successfully' if cleared else 'No session to clear'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/sync/validate', methods=['POST'])
def sync_validate():
    """
    Validate that the current session is still active.
    
    Returns:
        JSON response with validation status
    """
    from backend.services.bga_session_service import get_session_service
    
    try:
        service = get_session_service()
        is_valid = service.validate_session()
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'message': 'Session is valid' if is_valid else 'Session is invalid or expired'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/sync/pull/player-stats', methods=['POST'])
def sync_pull_player_stats():
    """
    Pull player statistics from BGA using Playwright.
    
    Expects JSON:
        {"ids": "12345,67890" or "group:123"}
    
    Returns:
        JSON response with import results
    """
    from backend.services.bga_session_service import get_session_service
    from backend.services.bga_pull_player_stats import BGAPlayerStatsPuller, parse_player_ids_input
    from backend.services.import_service import import_data
    
    try:
        # Parse request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        ids_input = data.get('ids', '').strip()
        
        if not ids_input:
            return jsonify({
                'success': False,
                'error': 'Missing required field: ids'
            }), 400
        
        # Get session
        session_service = get_session_service()
        
        if not session_service.has_saved_session():
            return jsonify({
                'success': False,
                'error': 'No saved session. Please log in first.'
            }), 401
        
        # Create browser context from saved session
        browser = session_service.create_browser(headless=True)
        context = session_service.create_context_from_saved_session()
        
        if not context:
            browser.close()
            return jsonify({
                'success': False,
                'error': 'Failed to load session. Please log in again.'
            }), 401
        
        try:
            # Parse player IDs input
            group_id, player_ids = parse_player_ids_input(ids_input)
            
            # Create puller
            puller = BGAPlayerStatsPuller(context)
            
            # If group ID, get members first
            if group_id:
                members = puller.pull_group_members(group_id)
                if not members:
                    return jsonify({
                        'success': False,
                        'error': f'No members found for group {group_id}'
                    }), 404
                player_ids = [m['id'] for m in members]
            
            if not player_ids:
                return jsonify({
                    'success': False,
                    'error': 'No valid player IDs provided'
                }), 400
            
            # Pull stats for all players
            tsv_data = puller.pull_multiple_players(player_ids)
            
            if not tsv_data:
                return jsonify({
                    'success': False,
                    'error': 'Failed to pull player stats'
                }), 500
            
            # Import the data using existing import pipeline
            import_result = import_data(tsv_data, import_type='player_stats')
            
            # Return the import result
            return jsonify(import_result), 200 if import_result['success'] else 400
            
        finally:
            context.close()
            browser.close()
            session_service.cleanup()
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Pull failed: {str(e)}'
        }), 500


@api_bp.route('/sync/pull/game-list', methods=['POST'])
def sync_pull_game_list():
    """
    Pull complete game catalog from BGA using Playwright.
    
    No request body needed.
    
    Returns:
        JSON response with import results
    """
    from backend.services.bga_session_service import get_session_service
    from backend.services.bga_pull_game_list import BGAGameListPuller
    from backend.services.import_service import import_data
    
    try:
        # Get session
        session_service = get_session_service()
        
        if not session_service.has_saved_session():
            return jsonify({
                'success': False,
                'error': 'No saved session. Please log in first.'
            }), 401
        
        # Create browser context from saved session
        browser = session_service.create_browser(headless=True)
        context = session_service.create_context_from_saved_session()
        
        if not context:
            browser.close()
            return jsonify({
                'success': False,
                'error': 'Failed to load session. Please log in again.'
            }), 401
        
        try:
            # Create puller
            puller = BGAGameListPuller(context)
            
            # Pull game list
            tsv_data = puller.pull_game_list()
            
            if not tsv_data:
                return jsonify({
                    'success': False,
                    'error': 'Failed to pull game list from BGA'
                }), 500
            
            # Import the data using existing import pipeline
            import_result = import_data(tsv_data, import_type='game_list')
            
            # Return the import result
            return jsonify(import_result), 200 if import_result['success'] else 400
            
        finally:
            context.close()
            browser.close()
            session_service.cleanup()
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Pull failed: {str(e)}'
        }), 500


@api_bp.route('/sync/pull/tournament-stats', methods=['POST'])
def sync_pull_tournament_stats():
    """
    Pull all tournament statistics from BGA using Playwright.
    
    Returns:
        JSON response with import results
    """
    from backend.services.bga_session_service import get_session_service
    from backend.services.bga_pull_tournament_stats import BGATournamentStatsPuller
    from backend.services.import_service import import_data
    
    try:
        # Get session
        session_service = get_session_service()
        
        if not session_service.has_saved_session():
            return jsonify({
                'success': False,
                'error': 'No saved session. Please log in first.'
            }), 401
        
        # Create browser context from saved session
        browser = session_service.create_browser(headless=True)
        context = session_service.create_context_from_saved_session()
        
        if not context:
            browser.close()
            return jsonify({
                'success': False,
                'error': 'Failed to load session. Please log in again.'
            }), 401
        
        try:
            # Create puller and pull all tournaments
            puller = BGATournamentStatsPuller(context)
            tsv_data = puller.pull_all_tournaments()
            
            if tsv_data is None:
                browser.close()
                return jsonify({
                    'success': False,
                    'error': 'Failed to pull tournament data from BGA'
                }), 500
            
            if not tsv_data.strip():
                # No tournaments found - this is valid
                browser.close()
                return jsonify({
                    'success': True,
                    'message': 'No tournaments found',
                    'results': {
                        'tournaments_processed': 0
                    }
                })
            
            # Import the data
            import_result = import_data(tsv_data, import_type='tournament_stats')
            
            if not import_result['success']:
                browser.close()
                return jsonify({
                    'success': False,
                    'error': import_result.get('error', 'Import failed')
                }), 500
            
            browser.close()
            
            return jsonify({
                'success': True,
                'results': import_result.get('results', {})
            })
            
        except Exception as e:
            browser.close()
            raise e
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/players', methods=['GET'])
def get_players():
    """
    Get all players from the database.
    
    Returns:
        JSON array of players with their stats
    """
    try:
        session = get_session()
        players = session.query(Player).all()
        
        players_data = []
        for player in players:
            players_data.append({
                'id': player.id,
                'bga_player_id': player.bga_player_id,
                'name': player.name,
                'xp': player.xp,
                'karma': player.karma,
                'matches_total': player.matches_total,
                'wins_total': player.wins_total,
                'url': f'/players/{player.id}'
            })
        
        return jsonify({
            'success': True,
            'players': players_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@api_bp.route('/players/<int:player_id>', methods=['GET'])
def get_player_detail(player_id):
    """
    Get detailed information about a specific player.
    
    Args:
        player_id: Player ID
    
    Returns:
        JSON with player details and game stats
    """
    try:
        session = get_session()
        player = session.query(Player).filter(Player.id == player_id).first()
        
        if not player:
            return jsonify({
                'success': False,
                'error': 'Player not found'
            }), 404
        
        # Get game stats with game details
        game_stats = session.query(PlayerGameStat, Game)\
            .join(Game, PlayerGameStat.game_id == Game.id)\
            .filter(PlayerGameStat.player_id == player_id)\
            .all()
        
        game_stats_data = []
        for stat, game in game_stats:
            game_stats_data.append({
                'game_name': game.name,
                'elo': stat.elo,
                'rank': stat.rank,
                'played': stat.played,
                'won': stat.won
            })
        
        player_data = {
            'id': player.id,
            'bga_player_id': player.bga_player_id,
            'name': player.name,
            'xp': player.xp,
            'karma': player.karma,
            'matches_total': player.matches_total,
            'wins_total': player.wins_total,
            'abandoned': player.abandoned,
            'timeout': player.timeout,
            'recent_matches': player.recent_matches,
            'last_seen_days': player.last_seen_days,
            'game_stats': game_stats_data
        }
        
        return jsonify({
            'success': True,
            'player': player_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@api_bp.route('/games', methods=['GET'])
def get_games():
    """
    Get all games with optional filtering.
    
    Query params:
        status (str, optional): Filter by status (alpha, beta, published)
        premium (str, optional): Filter by premium (0 or 1)
        search (str, optional): Search by name or display_name
        has_stats (str, optional): Filter to games with player stats (any player)
    
    Returns:
        JSON array of games
    """
    try:
        session = get_session()
        query = session.query(Game)
        
        # Filter by games that have player stats (any player)
        has_stats = request.args.get('has_stats')
        if has_stats and has_stats.lower() == 'true':
            print("Filtering to games with player stats")
            # Join with PlayerGameStat to only show games that have stats
            query = query.join(PlayerGameStat, PlayerGameStat.game_id == Game.id)
            print(f"Query after has_stats filter: {query}")
        
        # Apply filters from query params
        status = request.args.get('status')
        if status:
            query = query.filter(Game.status == status)
        
        premium = request.args.get('premium')
        if premium is not None:
            query = query.filter(Game.premium == (premium == '1'))
        
        search = request.args.get('search')
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                (Game.name.like(search_pattern)) | 
                (Game.display_name.like(search_pattern))
            )
        
        # Order by display name and ensure distinct results
        games = query.order_by(Game.display_name).distinct().all()
        
        games_data = []
        for game in games:
            games_data.append({
                'id': game.id,
                'bga_game_id': game.bga_game_id,
                'name': game.name,
                'display_name': game.display_name,
                'status': game.status,
                'premium': game.premium,
                'url': f'/games/{game.id}'
            })
        
        return jsonify({
            'success': True,
            'games': games_data,
            'count': len(games_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@api_bp.route('/games/<int:game_id>', methods=['GET'])
def get_game_detail(game_id):
    """
    Get detailed information about a game including player stats.
    
    Returns:
        JSON with game details and list of players who have played it
    """
    try:
        session = get_session()
        game = session.query(Game).filter(Game.id == game_id).first()
        
        if not game:
            return jsonify({
                'success': False,
                'error': 'Game not found'
            }), 404
        
        # Get all player stats for this game
        player_stats = session.query(PlayerGameStat, Player)\
            .join(Player, PlayerGameStat.player_id == Player.id)\
            .filter(PlayerGameStat.game_id == game_id)\
            .order_by(Player.name)\
            .all()
        
        players_data = []
        for stat, player in player_stats:
            win_rate = (stat.won / stat.played * 100) if stat.played > 0 else 0
            players_data.append({
                'player_id': player.id,
                'player_name': player.name,
                'bga_player_id': player.bga_player_id,
                'elo': stat.elo,
                'rank': stat.rank,
                'played': stat.played,
                'won': stat.won,
                'win_rate': round(win_rate, 1)
            })
        
        game_data = {
            'id': game.id,
            'bga_game_id': game.bga_game_id,
            'name': game.name,
            'display_name': game.display_name,
            'status': game.status,
            'premium': game.premium,
            'player_count': len(players_data),
            'players': players_data
        }
        
        return jsonify({
            'success': True,
            'game': game_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@api_bp.route('/tournaments', methods=['GET'])
def get_tournaments():
    """
    Get all tournaments with optional filtering.
    
    Query params:
        game_name (str, optional): Filter by game name
        search (str, optional): Search by tournament name
    
    Returns:
        JSON array of tournaments with match summaries
    """
    try:
        session = get_session()
        query = session.query(Tournament)
        
        # Apply filters
        game_name = request.args.get('game_name')
        if game_name:
            query = query.filter(Tournament.game_name == game_name)
        
        search = request.args.get('search')
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(Tournament.name.like(search_pattern))
        
        # Order by most recent first
        tournaments = query.order_by(Tournament.start_time.desc()).all()
        
        tournaments_data = []
        for tournament in tournaments:
            tournaments_data.append({
                'id': tournament.id,
                'bga_tournament_id': tournament.bga_tournament_id,
                'name': tournament.name,
                'game_name': tournament.game_name,
                'start_time': tournament.start_time,
                'end_time': tournament.end_time,
                'rounds': tournament.rounds,
                'round_limit': tournament.round_limit,
                'total_matches': tournament.total_matches,
                'timeout_matches': tournament.timeout_matches,
                'player_count': tournament.player_count,
                'timeout_percentage': round((tournament.timeout_matches / tournament.total_matches * 100) if tournament.total_matches > 0 else 0, 1),
                'url': f'/tournaments/{tournament.id}'
            })
        
        return jsonify({
            'success': True,
            'tournaments': tournaments_data,
            'count': len(tournaments_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@api_bp.route('/tournaments/<int:tournament_id>', methods=['GET'])
def get_tournament_detail(tournament_id):
    """
    Get detailed tournament information including matches and players.
    
    Returns:
        JSON with tournament details, matches, and player stats
    """
    try:
        session = get_session()
        tournament = session.query(Tournament).filter(Tournament.id == tournament_id).first()
        
        if not tournament:
            return jsonify({
                'success': False,
                'error': 'Tournament not found'
            }), 404
        
        # Get all matches with their players
        matches = session.query(TournamentMatch)\
            .filter(TournamentMatch.tournament_id == tournament_id)\
            .order_by(TournamentMatch.id)\
            .all()
        
        matches_data = []
        for match in matches:
            # Get players for this match
            players = session.query(TournamentMatchPlayer)\
                .filter(TournamentMatchPlayer.tournament_match_id == match.id)\
                .all()
            
            players_data = []
            for player in players:
                players_data.append({
                    'name': player.player_name,
                    'remaining_time_seconds': player.remaining_time_seconds,
                    'remaining_time_hours': round(player.remaining_time_seconds / 3600, 1) if player.remaining_time_seconds else None,
                    'points': player.points,
                    'timed_out': player.remaining_time_seconds < 0 if player.remaining_time_seconds is not None else False
                })
            
            matches_data.append({
                'id': match.id,
                'bga_table_id': match.bga_table_id,
                'is_timeout': match.is_timeout,
                'progress': match.progress,
                'players': players_data
            })
        
        tournament_data = {
            'id': tournament.id,
            'bga_tournament_id': tournament.bga_tournament_id,
            'name': tournament.name,
            'game_name': tournament.game_name,
            'start_time': tournament.start_time,
            'end_time': tournament.end_time,
            'rounds': tournament.rounds,
            'round_limit': tournament.round_limit,
            'total_matches': tournament.total_matches,
            'timeout_matches': tournament.timeout_matches,
            'player_count': tournament.player_count,
            'timeout_percentage': round((tournament.timeout_matches / tournament.total_matches * 100) if tournament.total_matches > 0 else 0, 1),
            'matches': matches_data
        }
        
        return jsonify({
            'success': True,
            'tournament': tournament_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@api_bp.route('/health', methods=['GET'])
def api_health():
    """
    API health check endpoint.
    
    Returns:
        JSON response with API status
    """
    return jsonify({
        'status': 'ok',
        'service': 'bga-stats-api',
        'version': '1.0.0'
    })
