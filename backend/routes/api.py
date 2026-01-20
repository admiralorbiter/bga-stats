"""
API routes for BGA Stats application.
Provides REST endpoints for data import and retrieval.
"""

from flask import Blueprint, request, jsonify
from backend.services.import_service import import_data

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
