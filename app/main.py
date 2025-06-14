"""Initialize and configure the Flask application.

This module serves as the entry point for the YouTube Playlist Analyzer application.
It handles the basic Flask app configuration, logging setup, and blueprint registration.

Typical usage example:
    python main.py
"""

import logging
import os

from app_factory import create_app
from middleware.logging_middleware import setup_logging_middleware

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create Flask app using the Application Factory pattern
app = create_app()

# Set up middleware
setup_logging_middleware(app)

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8090))

    # Run the app
    app.run(
        host="0.0.0.0",  # Allow connections from any host
        port=port,
        use_reloader=True,
        debug=False,
    )
