import os
import joblib
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import StratifiedKFold, cross_val_score
from scipy.stats import ttest_rel
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_curve,
    auc,
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from xgboost import XGBClassifier
import seaborn as sns

# =========================
# PATH CONFIGURATION
# =========================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

DATA_PATH = os.path.join(BASE_DIR, "app", "data", "heart.csv")
MODEL_PATH = os.path.join(BASE_DIR, "models", "heart_xgb.pkl")
OUTPUT_DIR = os.path.join(BASE_DIR, "app", "evaluation", "outputs")

os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"📂 Dataset path: {DATA_PATH}")
print(f"📦 Model path: {MODEL_PATH}")

# =========================
# LOAD DATA (ROBUSTLY)
# =========================
data = pd.read_csv(DATA_PATH)

# Handle broken CSV headers permanently
if "target" not in data.columns:
    print("⚠️ Header mismatch detected — repairing dataset")

    COLUMNS = [
        "age", "sex", "cp", "trestbps", "chol", "fbs",
        "restecg", "thalach", "exang", "oldpeak",
        "slope", "ca", "thal", "target"
    ]

    data = pd.read_csv(DATA_PATH, header=None, names=COLUMNS)

print("✅ Dataset loaded successfully")
print("Columns:", data.columns.tolist())

# =========================
# TARGET CLEANUP
# =========================
data["target"] = data["target"].apply(lambda x: 1 if x > 0 else 0)

data = data.apply(pd.to_numeric, errors="coerce")
data.dropna(inplace=True)

# =========================
# SPLIT DATA
# =========================
X = data.drop("target", axis=1)
y = data["target"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

# =========================
# LOAD TRAINED XGBOOST MODEL
# =========================
xgb_model = joblib.load(MODEL_PATH)
print("✅ XGBoost model loaded")

# =========================
# BASELINE + TREE MODELS
# =========================
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

log_reg = Pipeline([
    ("scaler", StandardScaler()),
    ("lr", LogisticRegression(max_iter=3000))
])
rf_model = RandomForestClassifier(n_estimators=200, random_state=42)
et_model = ExtraTreesClassifier(n_estimators=200, random_state=42)

log_reg.fit(X_train, y_train)
rf_model.fit(X_train, y_train)
et_model.fit(X_train, y_train)

# =========================
# PREDICTIONS
# =========================
y_pred_xgb = xgb_model.predict(X_test)
y_prob_xgb = xgb_model.predict_proba(X_test)[:, 1]

y_pred_lr = log_reg.predict(X_test)
y_prob_lr = log_reg.predict_proba(X_test)[:, 1]

y_pred_rf = rf_model.predict(X_test)
y_prob_rf = rf_model.predict_proba(X_test)[:, 1]

y_pred_et = et_model.predict(X_test)
y_prob_et = et_model.predict_proba(X_test)[:, 1]

# =========================
# METRICS
# =========================
print("\n📊 MODEL PERFORMANCE\n")

print("🔹 XGBoost Classifier")
print("Accuracy:", accuracy_score(y_test, y_pred_xgb))
print(classification_report(y_test, y_pred_xgb))

print("🔹 Logistic Regression (Baseline)")
print("Accuracy:", accuracy_score(y_test, y_pred_lr))
print(classification_report(y_test, y_pred_lr))

print("🔹 Random Forest")
print("Accuracy:", accuracy_score(y_test, y_pred_rf))
print(classification_report(y_test, y_pred_rf))

print("🔹 Extra Trees")
print("Accuracy:", accuracy_score(y_test, y_pred_et))
print(classification_report(y_test, y_pred_et))

# =========================
# SUMMARY TABLE (CSV + LaTeX)
# =========================
results = []

def add_result(name, y_true, y_pred, y_prob):
    results.append({
        "Model": name,
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": classification_report(y_true, y_pred, output_dict=True)["weighted avg"]["precision"],
        "Recall": classification_report(y_true, y_pred, output_dict=True)["weighted avg"]["recall"],
        "F1-score": classification_report(y_true, y_pred, output_dict=True)["weighted avg"]["f1-score"],
        "AUC": auc(*roc_curve(y_true, y_prob)[:2])
    })

add_result("XGBoost", y_test, y_pred_xgb, y_prob_xgb)
add_result("Logistic Regression", y_test, y_pred_lr, y_prob_lr)
add_result("Random Forest", y_test, y_pred_rf, y_prob_rf)
add_result("Extra Trees", y_test, y_pred_et, y_prob_et)

results_df = pd.DataFrame(results)

results_df.to_csv(os.path.join(OUTPUT_DIR, "model_comparison.csv"), index=False)
results_df.to_latex(os.path.join(OUTPUT_DIR, "model_comparison.tex"), index=False)

print("📄 Model comparison table saved (CSV + LaTeX)")

# =========================
# CONFUSION MATRIX (XGBOOST)
# =========================
cm = confusion_matrix(y_test, y_pred_xgb)

plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
plt.title("Confusion Matrix — XGBoost")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "confusion_matrix_xgb.png"))
plt.close()

# =========================
# ROC CURVE + AUC
# =========================
fpr_xgb, tpr_xgb, _ = roc_curve(y_test, y_prob_xgb)
roc_auc_xgb = auc(fpr_xgb, tpr_xgb)

fpr_lr, tpr_lr, _ = roc_curve(y_test, y_prob_lr)
roc_auc_lr = auc(fpr_lr, tpr_lr)

fpr_rf, tpr_rf, _ = roc_curve(y_test, y_prob_rf)
roc_auc_rf = auc(fpr_rf, tpr_rf)

fpr_et, tpr_et, _ = roc_curve(y_test, y_prob_et)
roc_auc_et = auc(fpr_et, tpr_et)

# =========================
# CROSS-VALIDATION
# =========================
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

cv_scores = {
    "XGBoost": cross_val_score(xgb_model, X, y, cv=cv, scoring="accuracy"),
    "Logistic Regression": cross_val_score(log_reg, X, y, cv=cv, scoring="accuracy"),
    "Random Forest": cross_val_score(rf_model, X, y, cv=cv, scoring="accuracy"),
    "Extra Trees": cross_val_score(et_model, X, y, cv=cv, scoring="accuracy"),
}

for model, scores in cv_scores.items():
    print(f"{model} CV Accuracy: {scores.mean():.4f} ± {scores.std():.4f}")

# =========================
# STATISTICAL SIGNIFICANCE TESTS
# =========================
baseline = cv_scores["Logistic Regression"]

for model in ["XGBoost", "Random Forest", "Extra Trees"]:
    t_stat, p_val = ttest_rel(cv_scores[model], baseline)
    print(f"{model} vs Logistic Regression — p-value: {p_val:.5f}")

plt.figure(figsize=(8, 6))
plt.plot(fpr_xgb, tpr_xgb, label=f"XGBoost (AUC = {roc_auc_xgb:.3f})")
plt.plot(fpr_lr, tpr_lr, label=f"Logistic Regression (AUC = {roc_auc_lr:.3f})")
plt.plot(fpr_rf, tpr_rf, label=f"Random Forest (AUC = {roc_auc_rf:.3f})")
plt.plot(fpr_et, tpr_et, label=f"Extra Trees (AUC = {roc_auc_et:.3f})")
plt.plot([0, 1], [0, 1], linestyle="--", color="gray")

plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve Comparison")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "roc_curve_comparison.png"))
plt.close()

print("📈 ROC curves saved")
print("🖼 Confusion matrix saved")
print("\n✅ Evaluation complete")

# =========================
# FEATURE IMPORTANCE COMPARISON
# =========================
feature_importance = pd.DataFrame({
    "Feature": X.columns,
    "XGBoost": xgb_model.feature_importances_,
    "Random Forest": rf_model.feature_importances_,
    "Extra Trees": et_model.feature_importances_
})

feature_importance.set_index("Feature", inplace=True)

feature_importance.to_csv(
    os.path.join(OUTPUT_DIR, "feature_importance_comparison.csv")
)

plt.figure(figsize=(10, 6))
feature_importance.mean(axis=1).sort_values(ascending=False).plot(kind="bar")
plt.title("Average Feature Importance (Tree Models)")
plt.ylabel("Importance")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "feature_importance_comparison.png"))
plt.close()

print("🌳 Feature importance comparison saved")
