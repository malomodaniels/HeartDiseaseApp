from datetime import date, datetime, time, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .. import db
from ..models import Appointment, AppointmentStatus, AppointmentEvent, Role, User

bp = Blueprint("appointments", __name__, url_prefix="/appointments")

def _recommended_slots_for_date(appt_date, max_items=5):
    """
    Returns a list of time objects representing earliest available slots on appt_date.
    Assumes clinic working hours 09:00 to 16:00, 30-min step.
    """
    start_t = time(9, 0)
    end_t = time(16, 0)
    step_minutes = 30

    # Pull already-booked times for that day (exclude cancelled)
    existing = Appointment.query.filter(
        Appointment.appointment_date == appt_date,
        Appointment.status != AppointmentStatus.CANCELLED.value,
    ).all()

    booked = set(a.appointment_time for a in existing)

    slots = []
    dt_cursor = datetime.combine(appt_date, start_t)
    dt_end = datetime.combine(appt_date, end_t)

    while dt_cursor <= dt_end and len(slots) < max_items:
        t = dt_cursor.time()
        if t not in booked:
            slots.append(t)
        dt_cursor += timedelta(minutes=step_minutes)

    return slots

WORK_START = time(9, 0)
WORK_END = time(16, 0)

def _parse_time(hhmm: str):
    return datetime.strptime(hhmm, "%H:%M").time()

@bp.get("/")
@login_required
def list_my():
    if current_user.has_role(Role.ADMIN.value, Role.CLINICIAN.value, Role.PUBLIC_HEALTH.value):
        flash("Use the admin schedule to view all appointments.", "info")
        return redirect(url_for("admin.schedule"))
    appts = Appointment.query.filter_by(patient_id=current_user.id).order_by(
        Appointment.appointment_date.desc(), Appointment.appointment_time.desc()
    ).all()
    return render_template("appointments/list.html", appts=appts)

@bp.get("/new")
@login_required
def new():
    risk_score = request.args.get("risk_score")
    risk_level = request.args.get("risk_level")
    return render_template("appointments/new.html", risk_score=risk_score, risk_level=risk_level)

    risk_score_str = request.args.get("risk_score", "").strip()
    risk_score = None
    is_high_risk = False

    if risk_score_str:
        try:
            risk_score = float(risk_score_str)
            is_high_risk = (risk_score >= 0.5)
        except Exception:
            risk_score = None
            is_high_risk = False

    # Pick a default date for recommendations (today). Patient can still choose any date.
    today = date.today()
    recommended_slots = _recommended_slots_for_date(today, max_items=5) if is_high_risk else []

    return render_template(
        "appointments/new.html",
        risk_score=risk_score_str,
        is_high_risk=is_high_risk,
        recommended_slots=recommended_slots,
        recommended_date=today
    )

@bp.post("/new")
@login_required
def create():
    if not current_user.has_role(Role.PATIENT.value):
        flash("Only patients can create bookings.", "warning")
        return redirect(url_for("admin.schedule"))

    date_str = request.form.get("appointment_date", "").strip()
    time_str = request.form.get("appointment_time", "").strip()
    clinic_unit = request.form.get("clinic_unit", "").strip() or None
    notes = request.form.get("notes", "").strip() or None
    
    
    risk_score_str = request.form.get("risk_score", "").strip()
    risk_score = None
    risk_label = None

    if risk_score_str:
        try:
            risk_score = float(risk_score_str)
            risk_label = "high" if risk_score >= 0.5 else "low"
        except Exception:
            risk_score = None
            risk_label = None

    try:
        appt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        appt_time = _parse_time(time_str)
    except Exception:
        flash("Invalid date/time.", "danger")
        return redirect(url_for("appointments.new"))

    # working hours rule
    if not (WORK_START <= appt_time <= WORK_END):
        flash("Appointment time must be within clinic hours (09:00–16:00).", "danger")
        return redirect(url_for("appointments.new"))

    # prevent slot conflicts across ALL patients
    conflict = Appointment.query.filter_by(
        appointment_date=appt_date,
        appointment_time=appt_time,
    ).filter(Appointment.status.in_([AppointmentStatus.BOOKED.value, AppointmentStatus.COMPLETED.value])).first()

    if conflict:
        flash("That slot is already booked. Please choose another time.", "warning")
        return redirect(url_for("appointments.new"))

    appt = Appointment(
        patient_id=current_user.id,
        appointment_date=appt_date,
        appointment_time=appt_time,
        clinic_unit=clinic_unit,
        notes=notes,
        status=AppointmentStatus.BOOKED.value,
        risk_score=risk_score,
        risk_label=risk_label,
    )
    
    db.session.add(appt)
    db.session.flush()

    db.session.add(AppointmentEvent(appointment_id=appt.id, event_type="booked", notes="Booked via web portal"))

    if risk_score is not None:
        db.session.add(AppointmentEvent(
            appointment_id=appt.id,
            event_type="risk_attached",
            notes=f"Risk score attached: {risk_score:.4f} ({risk_label})"
        ))

    db.session.commit()

    flash("Appointment booked.", "success")
    return redirect(url_for("appointments.list_my"))

@bp.post("/<int:appt_id>/cancel")
@login_required
def cancel(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    if not current_user.has_role(Role.ADMIN.value) and appt.patient_id != current_user.id:
        flash("Not authorised.", "danger")
        return redirect(url_for("core.index"))

    if appt.status != AppointmentStatus.BOOKED.value:
        flash("Only booked appointments can be cancelled.", "warning")
        return redirect(url_for("appointments.list_my" if current_user.has_role(Role.PATIENT.value) else "admin.schedule"))

    appt.status = AppointmentStatus.CANCELLED.value
    db.session.add(AppointmentEvent(appointment_id=appt.id, event_type="cancelled", notes="Cancelled"))
    db.session.commit()
    flash("Appointment cancelled.", "success")
    return redirect(url_for("appointments.list_my" if current_user.has_role(Role.PATIENT.value) else "admin.schedule"))
