"""HTTP routes for broadcast server."""

import os

from flask import Blueprint, render_template

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    """Main page - detects if user should be broadcaster or viewer."""
    # Get AdSense IDs from environment variables
    adsense_client = os.getenv("ADSENSE_CLIENT_ID", "ca-pub-5408741906258224")
    adsense_slot = os.getenv("ADSENSE_SLOT_ID", "1640890230")

    return render_template(
        "broadcast.html", adsense_client=adsense_client, adsense_slot=adsense_slot
    )
