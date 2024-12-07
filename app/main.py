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
