"""
Flask application factory for BGA Stats.
Creates and configures the Flask application instance.
"""

from flask import Flask, render_template, jsonify
from backend import config
from backend.db import init_db, close_session
from backend.routes import main_bp, api_bp


def create_app():
    """
    Application factory for creating Flask app instances.
    
    Returns:
        Flask: Configured Flask application
    """
    app = Flask(__name__, 
                template_folder='../frontend/templates',
                static_folder='../frontend/static')
    
    # Load configuration
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['DEBUG'] = config.DEBUG
    app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
    
    # Initialize database
    with app.app_context():
        init_db()
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register teardown handler for database cleanup
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        close_session()
    
    return app


def register_error_handlers(app):
    """
    Register custom error handlers for the application.
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        return render_template('errors/500.html'), 500


# For development: allow running with `python backend/app.py`
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
