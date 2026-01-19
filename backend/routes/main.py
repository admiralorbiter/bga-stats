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
