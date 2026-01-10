import os
import json
import pickle

class HeartPredictor:
    def __init__(self, model_path: str, features_path: str):
        self.model_path = model_path
        self.features_path = features_path
        self.model = None
        self.features = None
        self._load()

    def _load(self):
        if os.path.exists(self.features_path):
            with open(self.features_path, "r", encoding="utf-8") as f:
                self.features = json.load(f)

        if os.path.exists(self.model_path):
            with open(self.model_path, "rb") as f:
                self.model = pickle.load(f)

    def ready(self) -> bool:
        return self.model is not None and isinstance(self.features, list) and len(self.features) > 0

    def predict(self, payload: dict):
        if not self.ready():
            raise RuntimeError(
                "Heart disease model not configured. Provide models/heart_xgb.pkl and models/heart_features.json."
            )

        # Build 2D list in the exact feature order expected by the model
        row = []
        for feat in self.features:
            if feat not in payload:
                raise ValueError(f"Missing feature: {feat}")
            row.append(payload[feat])

        X = [row]  # shape (1, n_features)

        # Predict
        if hasattr(self.model, "predict_proba"):
            proba = float(self.model.predict_proba(X)[0][1])
            yhat = int(proba >= 0.5)
            return yhat, proba

        yhat = int(self.model.predict(X)[0])
        return yhat, None
