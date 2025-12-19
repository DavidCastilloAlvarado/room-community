"""Flask application factory."""

import os

from cachetools import TTLCache
from flask import Flask
from flask_socketio import SocketIO

# Initialize Flask-SocketIO
socketio = SocketIO()

# Track channels/rooms with 1-hour TTL (auto-cleanup)
# TTLCache(maxsize=100, ttl=3600) - stores max 100 channels, each expires after 1 hour
channels = TTLCache(maxsize=100, ttl=3600)


def create_app():
    """Create and configure the Flask application."""
    # Get the parent directory (where templates/ folder is)
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))

    app = Flask(__name__, template_folder=template_dir)
    app.config["SECRET_KEY"] = "your-secret-key-here"

    # Initialize SocketIO with the app
    socketio.init_app(app, cors_allowed_origins="*", async_mode="threading")

    # Register routes
    from . import routes

    app.register_blueprint(routes.bp)

    # Register Socket.IO event handlers

    return app
