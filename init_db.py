import os
from app import create_app, db
from app.models import User, Role
from werkzeug.security import generate_password_hash

DEFAULT_USERS = [
    ("admin@iih.local", "Admin", "Admin@123", Role.ADMIN),
    ("clinician@iih.local", "Clinician", "Clinician@123", Role.CLINICIAN),
    ("ph@iih.local", "Public Health", "PublicHealth@123", Role.PUBLIC_HEALTH),
    ("patient@iih.local", "Patient", "Patient@123", Role.PATIENT),
]

def main():
    app = create_app()
    with app.app_context():
        db.create_all()

        # Create default users if they don't exist
        for email, name, pw, role in DEFAULT_USERS:
            if not User.query.filter_by(email=email).first():
                u = User(
                    email=email,
                    full_name=name,
                    role=role.value,
                    password_hash=generate_password_hash(pw),
                )
                db.session.add(u)
        db.session.commit()
        print("Database initialised. Default users created (if missing).")

if __name__ == "__main__":
    main()
