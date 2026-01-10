def classify_risk(proba: float):
    """
    Convert prediction probability into
    (risk_level, risk_color)
    """

    if proba < 0.30:
        return "Low", "success"
    elif proba < 0.70:
        return "Moderate", "warning"
    else:
        return "High", "danger"
