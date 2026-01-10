import os
import json
import joblib
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from xgboost import XGBClassifier


def main():
    # -------------------------------------------------
    # 1) Load UCI Heart Disease dataset (no pandas)
    # -------------------------------------------------
    # Columns based on UCI documentation
    feature_names = [
        "age", "sex", "cp", "trestbps", "chol",
        "fbs", "restecg", "thalach", "exang",
        "oldpeak", "slope", "ca", "thal"
    ]

    data_path = os.path.join("data", "heart.csv")

    raw = np.genfromtxt(
        data_path,
        delimiter=",",
        dtype=float,
        missing_values="?",
        filling_values=np.nan,
    )

    # Split features and target
    X = raw[:, :-1]
    y_raw = raw[:, -1]

    # Convert target to binary: 0 = no disease, 1 = disease
    y = (y_raw > 0).astype(int)

    # Remove rows with missing values
    mask = ~np.isnan(X).any(axis=1)
    X = X[mask]
    y = y[mask]

    # -------------------------------------------------
    # 2) Train/test split
    # -------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # -------------------------------------------------
    # 3) Train XGBoost model
    # -------------------------------------------------
    model = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
        n_jobs=4,
    )

    model.fit(X_train, y_train)

    # -------------------------------------------------
    # 4) Evaluation
    # -------------------------------------------------
    y_pred = model.predict(X_test)

    print("\n=== TEST METRICS ===")
    print(f"Accuracy : {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred):.4f}")
    print(f"Recall   : {recall_score(y_test, y_pred):.4f}")
    print(f"F1-score : {f1_score(y_test, y_pred):.4f}")
    print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))

    # -------------------------------------------------
    # 5) Save model + feature list
    # -------------------------------------------------
    os.makedirs("models", exist_ok=True)

    joblib.dump(model, "models/heart_xgb.pkl")

    with open("models/heart_features.json", "w") as f:
        json.dump(feature_names, f, indent=2)

    print("\nSaved:")
    print(" - models/heart_xgb.pkl")
    print(" - models/heart_features.json")


if __name__ == "__main__":
    main()
