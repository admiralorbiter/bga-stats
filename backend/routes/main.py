"""
Main routes for serving HTML pages.
"""

from flask import Blueprint, render_template, redirect, url_for, jsonify

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Homepage route - redirect to import page for now.
    Later: redirect based on whether data exists.
    """
    # For now, render a simple welcome page
    return render_template('home.html')


@main_bp.route('/import')
def import_page():
    """
    Import page - allows users to paste export data from bookmarklets.
    """
    return render_template('import.html')


@main_bp.route('/tools')
def tools_page():
    """
    Tools page - displays bookmarklets for data collection from BGA.
    """
    return render_template('tools.html')


@main_bp.route('/sync')
def sync_page():
    """
    Sync page - allows users to pull data directly from BGA using Playwright.
    """
    return render_template('sync.html')


@main_bp.route('/players')
def players():
    """Players list page."""
    return render_template('players.html')


@main_bp.route('/players/<int:player_id>')
def player_detail(player_id):
    """Player detail page."""
    return render_template('player_detail.html', player_id=player_id)


@main_bp.route('/games')
def games():
    """Games list page."""
    return render_template('games.html')


@main_bp.route('/games/<int:game_id>')
def game_detail(game_id):
    """Game detail page."""
    return render_template('game_detail.html', game_id=game_id)


@main_bp.route('/tournaments')
def tournaments():
    """Tournaments list page."""
    return render_template('tournaments.html')


@main_bp.route('/tournaments/<int:tournament_id>')
def tournament_detail(tournament_id):
    """Tournament detail page."""
    return render_template('tournament_detail.html', tournament_id=tournament_id)


@main_bp.route('/matches')
def matches():
    """Matches list page."""
    return render_template('matches.html')


@main_bp.route('/matches/<int:bga_table_id>')
def match_detail(bga_table_id):
    """Match detail page with move timeline."""
    return render_template('match_detail.html', bga_table_id=bga_table_id)


@main_bp.route('/health')
def health():
    """
    Health check endpoint for monitoring.
    Returns JSON with application status.
    """
    return jsonify({
        'status': 'ok',
        'service': 'bga-stats',
        'version': '1.0.0'
    })
