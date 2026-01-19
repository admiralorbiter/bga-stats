"""
Configuration module for BGA Stats application.
Handles database paths and Flask settings.
"""

import os
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', BASE_DIR / 'bga_stats.db')
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'

# Flask configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.getenv('FLASK_ENV', 'production') == 'development'
