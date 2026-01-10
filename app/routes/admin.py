from datetime import datetime, timedelta, date

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from .. import db
from ..models import Appointment, AppointmentStatus, AppointmentEvent, Role, User

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _require_roles(*roles):
    if not current_user.is_authenticated or current_user.role not in roles:
        flash("Admin access required.", "danger")
        return False
    return True


@bp.get("/schedule")
@login_required
def schedule():
    if not _require_roles(Role.ADMIN.value, Role.CLINICIAN.value):
        return redirect(url_for("core.index"))

    day_str = request.args.get("day", "").strip()
    if day_str:
        try:
            day = datetime.strptime(day_str, "%Y-%m-%d").date()
        except Exception:
            day = date.today()
    else:
        day = date.today()

    appts = (
        Appointment.query
        .filter_by(appointment_date=day)
        .order_by(Appointment.appointment_time.asc())
        .all()
    )
    return render_template("admin/schedule.html", appts=appts, day=day)


@bp.post("/appointments/<int:appt_id>/status")
@login_required
def update_status(appt_id):
    if not _require_roles(Role.ADMIN.value, Role.CLINICIAN.value):
        return redirect(url_for("core.index"))

    appt = Appointment.query.get_or_404(appt_id)
    new_status = request.form.get("status", "").strip()

    if new_status not in [s.value for s in AppointmentStatus]:
        flash("Invalid status.", "danger")
        return redirect(url_for("admin.schedule"))

    appt.status = new_status
    db.session.add(
        AppointmentEvent(
            appointment_id=appt.id,
            event_type=f"status:{new_status}",
            notes="Updated by staff",
        )
    )
    db.session.commit()

    flash("Status updated.", "success")
    return redirect(url_for("admin.schedule", day=appt.appointment_date.isoformat()))


@bp.get("/dashboard")
@login_required
def dashboard():
    if not _require_roles(Role.ADMIN.value, Role.CLINICIAN.value, Role.PUBLIC_HEALTH.value):
        return redirect(url_for("core.index"))

    # Optional: allow dashboard date filtering: ?date=YYYY-MM-DD
    date_str = request.args.get("date", "").strip()
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = date.today()
            flash("Invalid date format. Showing today's dashboard.", "warning")
    else:
        selected_date = date.today()

    # 30-day window ending at selected_date
    date_to = selected_date
    date_from = date_to - timedelta(days=30)

    q = Appointment.query.filter(
        Appointment.appointment_date >= date_from,
        Appointment.appointment_date <= date_to,
    )

    total = q.count()
    completed = q.filter(Appointment.status == AppointmentStatus.COMPLETED.value).count()
    no_show = q.filter(Appointment.status == AppointmentStatus.NO_SHOW.value).count()
    cancelled = q.filter(Appointment.status == AppointmentStatus.CANCELLED.value).count()
    booked = q.filter(Appointment.status == AppointmentStatus.BOOKED.value).count()

    denom = max(total - cancelled, 1)
    no_show_rate = no_show / denom
    utilisation = completed / max(total, 1)

    # Optional: risk breakdown
    high_risk = q.filter(Appointment.risk_score.isnot(None), Appointment.risk_score >= 0.5).count()
    low_risk = q.filter(Appointment.risk_score.isnot(None), Appointment.risk_score < 0.5).count()

    return render_template(
        "admin/dashboard.html",
        total=total,
        completed=completed,
        no_show=no_show,
        cancelled=cancelled,
        booked=booked,
        no_show_rate=no_show_rate,
        utilisation=utilisation,
        high_risk=high_risk,
        low_risk=low_risk,
        date_from=date_from.strftime("%b %d, %Y"),
        date_to=date_to.strftime("%b %d, %Y"),
        selected_date=selected_date.strftime("%Y-%m-%d"),
    )
