import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .. import db
from ..models import SensitizationPost, PageView, Role

bp = Blueprint("sensitization", __name__, url_prefix="/sensitization")

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s[:240] or "post"

def log_view(page: str):
    try:
        db.session.add(PageView(page=page, user_id=getattr(current_user, "id", None), session_id=request.cookies.get("session", None)))
        db.session.commit()
    except Exception:
        db.session.rollback()

def seed_posts_if_empty():
    # Only seed once
    if SensitizationPost.query.first():
        return

    seed = [
        SensitizationPost(
            title="Know Your Blood Pressure",
            slug="know-your-blood-pressure",
            body=(
                "High blood pressure is often silent but it damages the heart and blood vessels over time.\n\n"
                "What to do:\n"
                "• Check your BP regularly\n"
                "• Reduce salt intake\n"
                "• Exercise at least 150 minutes weekly\n"
                "• Take prescribed meds consistently\n\n"
                "If your BP is consistently ≥140/90, consult a clinician."
            ),
            is_published=True,
        ),
        SensitizationPost(
            title="Heart Attack Warning Signs",
            slug="heart-attack-warning-signs",
            body=(
                "Common symptoms include chest pressure, pain radiating to arm/jaw, shortness of breath, cold sweat, nausea.\n\n"
                "If symptoms last more than a few minutes, seek emergency care immediately.\n\n"
                "Early response saves heart muscle."
            ),
            is_published=True,
        ),
        SensitizationPost(
            title="Stroke FAST Test",
            slug="stroke-fast-test",
            body=(
                "Use FAST:\n"
                "• Face drooping\n"
                "• Arm weakness\n"
                "• Speech difficulty\n"
                "• Time to call emergency services\n\n"
                "Stroke is time-critical — act immediately."
            ),
            is_published=True,
        ),
        SensitizationPost(
            title="Cholesterol: What It Means",
            slug="cholesterol-what-it-means",
            body=(
                "High LDL (“bad” cholesterol) increases plaque build-up in arteries.\n\n"
                "Improve cholesterol with:\n"
                "• Less fried/processed foods\n"
                "• More fiber (beans, oats, veggies)\n"
                "• Exercise and weight control\n"
                "• Medication if prescribed"
            ),
            is_published=True,
        ),
    ]

    db.session.add_all(seed)
    db.session.commit()

def seed_posts_if_empty():
    if SensitizationPost.query.filter_by(is_published=True).first():
        return

    data = [
        ("Know Your Blood Pressure", "know-your-blood-pressure",
         "High blood pressure often has no symptoms, but it damages the heart over time.\n\n"
         "What to do:\n• Check BP regularly\n• Reduce salt\n• Exercise weekly\n• Take prescribed meds\n"),
        ("Stroke FAST Test", "stroke-fast-test",
         "FAST:\n• Face drooping\n• Arm weakness\n• Speech difficulty\n• Time to seek emergency help\n"),
        ("Heart Attack Warning Signs", "heart-attack-warning-signs",
         "Chest pressure, shortness of breath, sweating, nausea, pain to arm/jaw.\n\n"
         "Seek urgent care immediately if symptoms persist.\n"),
    ]

    for title, slug, body in data:
        db.session.add(SensitizationPost(title=title, slug=slug, body=body, is_published=True))
    db.session.commit()

@bp.get("/")
def index():
    log_view("/sensitization")
    posts = (
        SensitizationPost.query
        .filter_by(is_published=True)
        .order_by(SensitizationPost.created_at.desc())
        .all()
    )
    return render_template("sensitization/index.html", posts=posts)

@bp.get("/post/<slug>")
def post(slug):
    log_view(f"/sensitization/post/{slug}")
    p = SensitizationPost.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template("sensitization/post.html", post=p)

@bp.get("/admin")
@login_required
def admin_list():
    if current_user.role not in [Role.ADMIN.value, Role.PUBLIC_HEALTH.value]:
        flash("Not authorised.", "danger")
        return redirect(url_for("sensitization.index"))
    posts = SensitizationPost.query.order_by(SensitizationPost.created_at.desc()).all()
    return render_template("sensitization/admin_list.html", posts=posts)

@bp.get("/admin/new")
@login_required
def admin_new():
    if current_user.role not in [Role.ADMIN.value, Role.PUBLIC_HEALTH.value]:
        flash("Not authorised.", "danger")
        return redirect(url_for("sensitization.index"))
    return render_template("sensitization/admin_edit.html", post=None)

@bp.post("/admin/new")
@login_required
def admin_create():
    if current_user.role not in [Role.ADMIN.value, Role.PUBLIC_HEALTH.value]:
        flash("Not authorised.", "danger")
        return redirect(url_for("sensitization.index"))
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    is_published = request.form.get("is_published") == "on"
    if not title or not body:
        flash("Title and body are required.", "danger")
        return redirect(url_for("sensitization.admin_new"))
    slug = slugify(title)
    image = request.form.get("image", "").strip() or None
    # ensure unique slug
    i = 2
    base = slug
    while SensitizationPost.query.filter_by(slug=slug).first():
        slug = f"{base}-{i}"
        i += 1
    p = SensitizationPost(title=title, slug=slug, body=body, image=image, is_published=is_published)
    db.session.add(p)
    db.session.commit()
    flash("Post created.", "success")
    return redirect(url_for("sensitization.admin_list"))

@bp.get("/admin/edit/<int:post_id>")
@login_required
def admin_edit(post_id):
    if current_user.role not in [Role.ADMIN.value, Role.PUBLIC_HEALTH.value]:
        flash("Not authorised.", "danger")
        return redirect(url_for("sensitization.index"))
    p = SensitizationPost.query.get_or_404(post_id)
    return render_template("sensitization/admin_edit.html", post=p)

@bp.post("/admin/edit/<int:post_id>")
@login_required
def admin_update(post_id):
    if current_user.role not in [Role.ADMIN.value, Role.PUBLIC_HEALTH.value]:
        flash("Not authorised.", "danger")
        return redirect(url_for("sensitization.index"))
    p = SensitizationPost.query.get_or_404(post_id)
    p.title = request.form.get("title", "").strip()
    p.body = request.form.get("body", "").strip()
    p.image = request.form.get("image", "").strip() or None
    p.is_published = request.form.get("is_published") == "on"
    db.session.commit()
    flash("Post updated.", "success")
    return redirect(url_for("sensitization.admin_list"))

@bp.post("/admin/delete/<int:post_id>")
@login_required
def admin_delete(post_id):
    if current_user.role not in [Role.ADMIN.value, Role.PUBLIC_HEALTH.value]:
        flash("Not authorised.", "danger")
        return redirect(url_for("sensitization.index"))

    p = SensitizationPost.query.get_or_404(post_id)
    db.session.delete(p)
    db.session.commit()

    flash("Post deleted.", "success")
    return redirect(url_for("sensitization.admin_list"))

