from datetime import datetime, date, time
from enum import Enum
from flask_login import UserMixin
from . import db, login_manager

class Role(Enum):
    PATIENT = "patient"
    CLINICIAN = "clinician"
    ADMIN = "admin"
    PUBLIC_HEALTH = "public_health"

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default=Role.PATIENT.value)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship("Appointment", backref="patient", lazy=True)

    def has_role(self, *roles: str) -> bool:
        return self.role in roles

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class AppointmentStatus(Enum):
    BOOKED = "booked"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class Appointment(db.Model):
    __tablename__ = "appointments"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    clinic_unit = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(30), nullable=False, default=AppointmentStatus.BOOKED.value)
    notes = db.Column(db.Text, nullable=True)
    
    risk_score = db.Column(db.Float, nullable=True)
    risk_label = db.Column(db.String(30), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = db.relationship("AppointmentEvent", backref="appointment", lazy=True, cascade="all, delete-orphan")

    @property
    def slot_key(self):
        return f"{self.appointment_date.isoformat()} {self.appointment_time.strftime('%H:%M')}"

class AppointmentEvent(db.Model):
    __tablename__ = "appointment_events"
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id"), nullable=False)
    event_type = db.Column(db.String(60), nullable=False)
    event_time = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

class SensitizationPost(db.Model):
    __tablename__ = "sens_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    body = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(120), nullable=True)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PageView(db.Model):
    __tablename__ = "page_views"
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    session_id = db.Column(db.String(64), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
