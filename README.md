# IIH Web Framework (Flask) — Web-only Integrated HIS

This is a minimal, working **web-based** implementation of the Intelligent Integrated Health (IIH) Framework:
- **Clinical DSS**: Heart disease prediction (expects your trained XGBoost model file).
- **Appointments**: Booking, listing, cancellation, attendance marking.
- **Admin dashboard**: Operational metrics (no-show rate, utilisation).
- **Sensitization**: Public pages + simple CMS for admin to post content.
- **Role-based access**: patient / clinician / admin / public_health.

## 1) Setup (local)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
python init_db.py
flask run
```

Open: http://127.0.0.1:5000

## 2) Default accounts created by init_db.py
- Admin: `admin@iih.local` / `Admin@123`
- Clinician: `clinician@iih.local` / `Clinician@123`
- Public health: `ph@iih.local` / `PublicHealth@123`
- Patient: `patient@iih.local` / `Patient@123`

**Change passwords** in production.

## 3) Heart disease model integration

The app expects:
- `models/heart_xgb.pkl` : a pickled sklearn-style classifier with `.predict_proba(X)` or `.predict(X)`.
- `models/heart_features.json` : a JSON array of feature names in the **exact order** your model expects.

Example `heart_features.json`:
```json
["age","sex","cp","trestbps","chol","fbs","restecg","thalach","exang","oldpeak","slope","ca","thal"]
```

Put these files under `models/` (already created). If model files are missing, the UI still works but prediction will show a helpful error message.

## 4) Deploy
- Use `gunicorn`:
  ```bash
  gunicorn -w 2 -b 0.0.0.0:8000 run:app
  ```

## 5) Notes for your paper
- The system logs appointment outcomes (completed/no-show/cancelled).
- Admin dashboard computes: utilisation and no-show rate from recorded outcomes.
