from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from .. import db
from ..models import User, Role

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("core.index"))
    next_url = request.args.get("next", "")
    return render_template("auth/login.html", next=next_url)

@bp.post("/login")
def login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    next_url = request.form.get("next", "").strip()

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        flash("Invalid email or password.", "danger")
        # keep next in the URL so it isn't lost
        if next_url:
            return redirect(url_for("auth.login", next=next_url))
        return redirect(url_for("auth.login"))

    login_user(user)

    # redirect to original destination if provided
    if next_url:
        return redirect(next_url)

    return redirect(url_for("core.index"))

@bp.get("/register")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("core.index"))
    next_url = request.args.get("next", "")
    return render_template("auth/register.html", next=next_url)

@bp.post("/register")
def register_post():
    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    next_url = request.form.get("next", "").strip()

    if not full_name or not email or not password:
        flash("All fields are required.", "danger")
        if next_url:
            return redirect(url_for("auth.register", next=next_url))
        return redirect(url_for("auth.register"))

    if User.query.filter_by(email=email).first():
        flash("Email already registered.", "warning")
        if next_url:
            return redirect(url_for("auth.register", next=next_url))
        return redirect(url_for("auth.register"))

    u = User(
        full_name=full_name,
        email=email,
        password_hash=generate_password_hash(password),
        role=Role.PATIENT.value,
    )
    db.session.add(u)
    db.session.commit()

    flash("Account created. Please log in.", "success")

    # send user to login and preserve next
    if next_url:
        return redirect(url_for("auth.login", next=next_url))
    return redirect(url_for("auth.login"))

@bp.get("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("core.index"))
