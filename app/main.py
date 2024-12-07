"""Initialize and configure the Flask application.

This module serves as the entry point for the YouTube Playlist Analyzer application.
It handles the basic Flask app configuration, logging setup, and blueprint registration.

Typical usage example:
    python main.py
"""

import logging

from flask import Flask
from routes import home_routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Register Blueprints
app.register_blueprint(home_routes.bp)

if __name__ == "__main__":
    app.run(use_reloader=True, debug=False)
