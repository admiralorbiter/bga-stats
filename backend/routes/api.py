"""
API routes for BGA Stats application.
Will be populated in Sprint 4 with import and data endpoints.
"""

from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

# API routes will be added in Sprint 4:
# - POST /api/import
# - GET /api/players
# - GET /api/players/<id>
# - GET /api/games
