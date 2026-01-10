import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate 
from dotenv import load_dotenv

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    db_url = os.getenv("DATABASE_URL", "sqlite:///iih.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .routes.auth import bp as auth_bp
    from .routes.core import bp as core_bp
    from .routes.prediction import bp as pred_bp
    from .routes.appointments import bp as appt_bp
    from .routes.admin import bp as admin_bp
    from .routes.sensitization import bp as sens_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(pred_bp)
    app.register_blueprint(appt_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(sens_bp)

    @app.template_filter("pct")
    def pct(x):
        try:
            return f"{100.0*float(x):.2f}%"
        except Exception:
            return "—"

    return app
