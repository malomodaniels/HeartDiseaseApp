import os
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user
from ..services.predictor import HeartPredictor

bp = Blueprint("prediction", __name__, url_prefix="/predict")

# Risk thresholds (probability-based)
LOW_RISK_MAX = 0.30        # < 30%
MODERATE_RISK_MAX = 0.70   # 30–70%

def _predictor():
    model_path = os.getenv("HEART_MODEL_PATH", "models/heart_xgb.pkl")
    feats_path = os.getenv("HEART_FEATURES_PATH", "models/heart_features.json")
    return HeartPredictor(model_path=model_path, features_path=feats_path)
from flask import redirect, url_for

def interpret_risk(proba: float):
    """
    Convert model probability into clinically meaningful risk bands.
    """
    if proba < LOW_RISK_MAX:
        return {
            "label": "Low risk",
            "color": "success",
            "message": "Low likelihood of heart disease. Routine monitoring is advised."
        }
    elif proba < MODERATE_RISK_MAX:
        return {
            "label": "Moderate risk",
            "color": "warning",
            "message": "Moderate cardiovascular risk detected. Clinical consultation is recommended."
        }
    else:
        return {
            "label": "High risk",
            "color": "danger",
            "message": "High likelihood of heart disease. Prompt clinical evaluation is strongly advised."
        }

@bp.get("/")
def landing():
    return redirect(url_for("prediction.form"))

@bp.get("/form")
def form():
    p = _predictor()
    feats = p.features or []
        
    tpl = "prediction/form_modal.html" if request.headers.get("X-Modal") else "prediction/form.html"
    return render_template(tpl, features=feats, model_ready=p.ready())

from ..utils.risk import classify_risk

@bp.post("/run")
def run():
    p = _predictor()
    try:
        payload = {}
        if p.features:
            for feat in p.features:
                val = request.form.get(feat, "").strip()
                if val == "":
                    raise ValueError(f"Missing input: {feat}")
                try:
                    payload[feat] = float(val) if "." in val else int(val)
                except:
                    payload[feat] = val

        yhat, proba = p.predict(payload)

        # classify risk using your utility
        risk_level, risk_color = classify_risk(proba)

        return render_template(
            "prediction/result.html",
            yhat=yhat,
            proba=proba,
            risk_level=risk_level,
            risk_color=risk_color
        )

    except Exception as e:
        flash(str(e), "danger")
        return redirect(url_for("prediction.form"))
