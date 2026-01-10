from flask import Blueprint, render_template
from flask_login import current_user
bp = Blueprint("core", __name__)

@bp.get("/")
def index():
    return render_template("index.html")
