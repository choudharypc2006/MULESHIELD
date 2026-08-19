# 🛡️ MULESHIELD

**Mule-Account Risk-Intelligence Platform** — Hackathon MVP

MULESHIELD detects mule accounts in banking transaction networks by combining a **rule engine**, an **ML classifier**, and **graph analytics** into a single composite risk score.

---

## Tech Stack

| Layer    | Technologies                                      |
| -------- | ------------------------------------------------- |
| Backend  | Python 3.11, FastAPI, scikit-learn, pandas, NetworkX, XGBoost, SHAP |
| Frontend | React 19, TypeScript, Tailwind CSS v4, Recharts, Vite |

---

## Project Structure

```text
muleshield/
├── backend/
│   ├── app/
│   │   ├── data/
│   │   │   ├── generate_dataset.py  # Generates 8K row synthetic dataset with realistic distribution
│   │   │   └── features.md          # Domain relevance & feature data dictionary
│   │   ├── rules/
│   │   │   ├── engine.py            # 5 deterministic rule functions (pure functions)
│   │   │   ├── default_config.json  # Tunable thresholds for rule triggering
│   │   │   └── test_engine.py       # Pytest unit tests for all rule logic
│   │   ├── model/
│   │   │   ├── train_model.py       # 5-fold CV (RF/XGBoost/LR), saves best model & plot metrics
│   │   │   └── explain.py           # Uses SHAP to generate summary & force plots, outputs text explanations
│   │   ├── scoring/                 # Composite mule-confidence scoring (Coming soon)
│   │   └── main.py                  # FastAPI entrypoint
│   ├── requirements.txt
│   ├── setup.sh                     # Unix script to build dataset and run model pipeline
│   └── setup.bat                    # Windows script to build dataset and run model pipeline
├── frontend/                        # React + Vite application
├── README.md
└── .gitignore
```

---

## What's implemented so far

- **Synthetic Dataset Generator:** Outputs 8,000 realistic bank accounts mapped to 30 behavioural features, mimicking near-misses and false-positive account anomalies typical of genuine data.
- **Rule Engine:** Contains 5 hard-coded rules (e.g. New Account Surge, Smurfing Pattern, Rapid In-Out) separated from their thresholds allowing for non-technical configurability.
- **ML Classifier & Evaluator:** Supports Random Forest, XGBoost (with scale_pos_weight mapping), and Logistic Regression algorithms evaluated across 5-fold stratified cross-validation (tracking F1, PR-AUC, ROC-AUC).
- **SHAP Explainability Layer:** Interprets the model logic natively using SHAP values. The `get_explanation()` function surfaces both hard-coded rule triggers and top 3 ML feature contributions mapped into plain-language sentences.

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** and **npm**

### 1. Backend

```bash
# Create & activate a virtual environment
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Generate data & train the model
Note: The generated dataset (`synthetic_accounts.csv`), ML binary model (`best_model.joblib`), extracted `feature_importances.json`, and visual reports (in `reports/`) are all strictly gitignored. You **must** generate these files locally before the API will have real data to serve.

Run the setup script from the `/backend` directory:
```bash
# On Mac/Linux:
chmod +x setup.sh
./setup.sh

# On Windows:
setup.bat
```

*Alternatively, run the three-command sequence manually:*
```bash
python -m app.data.generate_dataset
python -m app.model.train_model
python -m app.model.explain
```

#### Start the API server

```bash
# Start the API server (port 8000)
uvicorn app.main:app --reload --port 8000
```

Verify: [http://localhost:8000/health](http://localhost:8000/health) → `{"status": "ok", "service": "muleshield-api"}`

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server (port 5173)
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) — the dashboard should show **✅ API connected** when the backend is running.

---

## API Endpoints

| Method | Path      | Description       |
| ------ | --------- | ----------------- |
| GET    | `/health` | Liveness probe    |

_More endpoints coming soon._

---

## License

MIT
