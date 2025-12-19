"""HTTP routes for broadcast server."""
from flask import Blueprint, render_template

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Main page - detects if user should be broadcaster or viewer."""
    return render_template('broadcast.html')
