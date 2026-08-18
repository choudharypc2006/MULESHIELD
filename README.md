# 🛡️ MULESHIELD

**Mule-Account Risk-Intelligence Platform** — Hackathon MVP

MULESHIELD detects mule accounts in banking transaction networks by combining a **rule engine**, an **ML classifier**, and **graph analytics** into a single composite risk score.

---

## Tech Stack

| Layer    | Technologies                                      |
| -------- | ------------------------------------------------- |
| Backend  | Python 3.11, FastAPI, scikit-learn, pandas, NetworkX |
| Frontend | React 19, TypeScript, Tailwind CSS v4, Recharts, Vite |

---

## Project Structure

```
muleshield/
├── backend/
│   ├── app/
│   │   ├── data/       # Synthetic dataset generator & loader
│   │   ├── rules/      # Deterministic rule engine
│   │   ├── model/      # ML classifier (scikit-learn)
│   │   ├── scoring/    # Composite mule-confidence scoring
│   │   └── main.py     # FastAPI entrypoint
│   └── requirements.txt
├── frontend/           # React + Vite application
├── README.md
└── .gitignore
```

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
