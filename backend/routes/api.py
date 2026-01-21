"""
API routes for BGA Stats application.
Provides REST endpoints for data import and retrieval.
"""

from flask import Blueprint, request, jsonify
from backend.services.import_service import import_data
from backend.models import (
    Player, PlayerGameStat, Game,
    Tournament, TournamentMatch, TournamentMatchPlayer,
    Match, MatchMove
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


@api_bp.route('/sync/pull/move-stats', methods=['POST'])
def sync_pull_move_stats():
    """
    Pull move statistics from BGA using Playwright.
    
    Expects JSON:
        {"table_ids": "12345,67890"} - Manual table IDs
        OR
        {"auto_discover": true, "limit": 50} - Auto-discover recent matches
    
    Returns:
        JSON response with import results
    """
    from backend.services.bga_session_service import get_session_service
    from backend.services.bga_pull_move_stats import BGAMoveStatsPuller
    from backend.services.import_service import import_data
    
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
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
            puller = BGAMoveStatsPuller(context)
            
            # Determine mode: manual or auto-discover
            if data.get('auto_discover'):
                # Auto-discover mode
                limit = data.get('limit', 50)
                print(f"Auto-discovering recent matches (limit: {limit})")
                
                table_ids = puller.discover_recent_matches(limit=limit)
                
                if not table_ids:
                    context.close()
                    browser.close()
                    return jsonify({
                        'success': False,
                        'error': 'No recent matches found'
                    }), 404
                
                print(f"Found {len(table_ids)} matches to pull")
                tsv_data = puller.pull_multiple_matches(table_ids)
            else:
                # Manual mode
                table_ids_input = data.get('table_ids', '').strip()
                
                if not table_ids_input:
                    context.close()
                    browser.close()
                    return jsonify({
                        'success': False,
                        'error': 'Missing required field: table_ids'
                    }), 400
                
                # Parse comma-separated table IDs
                table_ids = [tid.strip() for tid in table_ids_input.split(',') if tid.strip()]
                
                if not table_ids:
                    context.close()
                    browser.close()
                    return jsonify({
                        'success': False,
                        'error': 'No valid table IDs provided'
                    }), 400
                
                print(f"Pulling {len(table_ids)} matches manually specified")
                tsv_data = puller.pull_multiple_matches(table_ids)
            
            # Close browser before import (can take time)
            context.close()
            browser.close()
            
            if not tsv_data:
                return jsonify({
                    'success': False,
                    'error': 'Failed to pull move stats'
                }), 500
            
            # Import the data - split by match and import each separately
            # The TSV data contains multiple matches, each with the same table_id
            # We need to split by table_id and import each match individually
            lines = tsv_data.strip().split('\n')
            
            # Group lines by table_id
            matches_by_table = {}
            for line in lines:
                if not line.strip():
                    continue
                table_id = line.split(';')[0].strip()
                if table_id not in matches_by_table:
                    matches_by_table[table_id] = []
                matches_by_table[table_id].append(line)
            
            # Import each match
            total_matches_created = 0
            total_matches_updated = 0
            total_moves_created = 0
            
            for table_id, match_lines in matches_by_table.items():
                match_tsv = '\n'.join(match_lines)
                import_result = import_data(match_tsv, import_type='move_stats')
                
                if import_result.get('success'):
                    results = import_result.get('results', {})
                    total_matches_created += results.get('matches_created', 0)
                    total_matches_updated += results.get('matches_updated', 0)
                    total_moves_created += results.get('moves_created', 0)
            
            return jsonify({
                'success': True,
                'message': 'Move stats imported successfully',
                'result': {
                    'matches_created': total_matches_created,
                    'matches_updated': total_matches_updated,
                    'moves_created': total_moves_created
                }
            })
        
        except Exception as e:
            context.close()
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


@api_bp.route('/matches', methods=['GET'])
def get_matches():
    """
    Get all matches with optional filtering.
    
    Query params:
        game_name (str): Filter by game name (partial match)
        player_name (str): Filter by player name (in any move)
        date_from (str): Filter imported_at >= date (ISO format)
        date_to (str): Filter imported_at <= date (ISO format)
        min_moves (int): Minimum move count
        max_moves (int): Maximum move count
    
    Returns:
        JSON with matches array containing match summaries and statistics
    """
    from sqlalchemy import func
    from datetime import datetime
    
    try:
        session = get_session()
        
        # Start with base query joining Match and MatchMove
        query = session.query(
            Match.id,
            Match.bga_table_id,
            Match.game_name,
            Match.imported_at,
            func.count(MatchMove.id).label('move_count')
        ).outerjoin(MatchMove, Match.id == MatchMove.match_id)\
         .group_by(Match.id, Match.bga_table_id, Match.game_name, Match.imported_at)
        
        # Apply game name filter
        game_name = request.args.get('game_name')
        if game_name:
            query = query.filter(Match.game_name.like(f'%{game_name}%'))
        
        # Apply player name filter (requires subquery)
        player_name = request.args.get('player_name')
        if player_name:
            player_subquery = session.query(MatchMove.match_id)\
                .filter(MatchMove.player_name.like(f'%{player_name}%'))\
                .distinct().subquery()
            query = query.filter(Match.id.in_(session.query(player_subquery.c.match_id)))
        
        # Apply date filters
        date_from = request.args.get('date_from')
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from)
                query = query.filter(Match.imported_at >= date_from_obj)
            except ValueError:
                pass  # Ignore invalid date format
        
        date_to = request.args.get('date_to')
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to)
                query = query.filter(Match.imported_at <= date_to_obj)
            except ValueError:
                pass  # Ignore invalid date format
        
        # Execute query
        results = query.order_by(Match.imported_at.desc()).all()
        
        # Build response with additional data
        matches_data = []
        for result in results:
            match_id, bga_table_id, game_name, imported_at, move_count = result
            
            # Apply move count filters
            min_moves = request.args.get('min_moves')
            if min_moves and move_count < int(min_moves):
                continue
            
            max_moves = request.args.get('max_moves')
            if max_moves and move_count > int(max_moves):
                continue
            
            # Get player names and time info
            moves = session.query(MatchMove)\
                .filter(MatchMove.match_id == match_id)\
                .order_by(MatchMove.id)\
                .all()
            
            player_names = list(set(move.player_name for move in moves))
            
            # Calculate duration from first and last move
            first_move_time = None
            last_move_time = None
            duration_minutes = None
            
            if moves:
                first_move_time = moves[0].datetime_local
                last_move_time = moves[-1].datetime_local
                
                # Try to parse and calculate duration
                try:
                    # Parse datetime strings (format varies by locale)
                    first_dt = datetime.strptime(first_move_time, '%m/%d/%Y, %I:%M:%S %p')
                    last_dt = datetime.strptime(last_move_time, '%m/%d/%Y, %I:%M:%S %p')
                    duration = last_dt - first_dt
                    duration_minutes = int(duration.total_seconds() / 60)
                except:
                    try:
                        # Try alternative format
                        first_dt = datetime.strptime(first_move_time, '%d/%m/%Y, %H:%M:%S')
                        last_dt = datetime.strptime(last_move_time, '%d/%m/%Y, %H:%M:%S')
                        duration = last_dt - first_dt
                        duration_minutes = int(duration.total_seconds() / 60)
                    except:
                        pass  # Leave as None if can't parse
            
            matches_data.append({
                'id': match_id,
                'bga_table_id': bga_table_id,
                'game_name': game_name,
                'imported_at': imported_at.isoformat() if imported_at else None,
                'move_count': move_count,
                'player_names': player_names,
                'first_move_time': first_move_time,
                'last_move_time': last_move_time,
                'duration_minutes': duration_minutes,
                'url': f'/matches/{bga_table_id}'
            })
        
        return jsonify({
            'success': True,
            'matches': matches_data,
            'count': len(matches_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@api_bp.route('/matches/<int:bga_table_id>', methods=['GET'])
def get_match_detail(bga_table_id):
    """
    Get detailed match information with full move timeline.
    
    Args:
        bga_table_id: BGA table ID
    
    Returns:
        JSON with match details, moves, and statistics
    """
    from datetime import datetime
    
    try:
        session = get_session()
        
        # Get match by bga_table_id
        match = session.query(Match).filter(Match.bga_table_id == bga_table_id).first()
        
        if not match:
            return jsonify({
                'success': False,
                'error': 'Match not found'
            }), 404
        
        # Get all moves ordered by id (insertion order)
        moves = session.query(MatchMove)\
            .filter(MatchMove.match_id == match.id)\
            .order_by(MatchMove.id)\
            .all()
        
        # Build moves array
        moves_data = []
        for move in moves:
            moves_data.append({
                'move_no': move.move_no,
                'player_name': move.player_name,
                'datetime_local': move.datetime_local,
                'datetime_excel': move.datetime_excel,
                'remaining_time': move.remaining_time
            })
        
        # Calculate statistics
        player_names = list(set(move.player_name for move in moves))
        total_moves = len(moves)
        player_count = len(player_names)
        
        # Calculate moves per player
        moves_per_player = {}
        for player in player_names:
            moves_per_player[player] = sum(1 for m in moves if m.player_name == player)
        
        # Calculate duration
        first_move_time = None
        last_move_time = None
        duration_minutes = None
        avg_time_per_move_seconds = None
        
        if moves:
            first_move_time = moves[0].datetime_local
            last_move_time = moves[-1].datetime_local
            
            # Try to parse and calculate duration
            try:
                # Try multiple datetime formats
                formats = [
                    '%m/%d/%Y, %I:%M:%S %p',
                    '%d/%m/%Y, %H:%M:%S',
                    '%Y-%m-%d %H:%M:%S',
                    '%m/%d/%Y %I:%M:%S %p'
                ]
                
                first_dt = None
                last_dt = None
                
                for fmt in formats:
                    try:
                        first_dt = datetime.strptime(first_move_time, fmt)
                        last_dt = datetime.strptime(last_move_time, fmt)
                        break
                    except:
                        continue
                
                if first_dt and last_dt:
                    duration = last_dt - first_dt
                    duration_minutes = int(duration.total_seconds() / 60)
                    if total_moves > 1:
                        avg_time_per_move_seconds = int(duration.total_seconds() / (total_moves - 1))
            except:
                pass  # Leave as None if can't parse
        
        statistics = {
            'total_moves': total_moves,
            'player_count': player_count,
            'player_names': player_names,
            'duration_minutes': duration_minutes,
            'first_move_time': first_move_time,
            'last_move_time': last_move_time,
            'moves_per_player': moves_per_player,
            'avg_time_per_move_seconds': avg_time_per_move_seconds
        }
        
        match_data = {
            'id': match.id,
            'bga_table_id': match.bga_table_id,
            'game_name': match.game_name,
            'imported_at': match.imported_at.isoformat() if match.imported_at else None
        }
        
        return jsonify({
            'success': True,
            'match': match_data,
            'moves': moves_data,
            'statistics': statistics
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
