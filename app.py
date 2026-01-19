"""
BGA Stats Application Launcher
Run this file to start the Flask application.

Usage:
    python app.py
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app

if __name__ == '__main__':
    app = create_app()
    print("=" * 60)
    print("BGA Stats Application Starting")
    print("=" * 60)
    print(f"Server running at: http://127.0.0.1:5000")
    print(f"Health check: http://127.0.0.1:5000/health")
    print("Press CTRL+C to quit")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
