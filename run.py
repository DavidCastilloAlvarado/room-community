#!/usr/bin/env python3
"""Run the broadcast server."""

import logging
import sys

from broadcast.app import create_app, socketio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

app = create_app()

if __name__ == "__main__":
    logger.info("Server running on http://0.0.0.0:3000")
    socketio.run(app, host="0.0.0.0", port=3000, debug=False, allow_unsafe_werkzeug=True)
