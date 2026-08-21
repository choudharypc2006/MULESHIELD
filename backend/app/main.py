"""
MULESHIELD — Mule-Account Risk-Intelligence Platform
FastAPI entrypoint
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List

from app.scoring.mcs import (
    load_data, 
    compute_all_scores, 
    compute_mcs, 
    get_config, 
    update_config
)
from app.model.explain import get_explanation

# ---------------------------------------------------------------------------
# In-Memory Stores
# ---------------------------------------------------------------------------
CACHE = {}
ACTIONS = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    try:
        load_data()
    except SystemExit as e:
        print(e)
        import sys
        sys.exit(1)
        
    print("Computing Mule Confidence Scores for all accounts on startup...")
    all_scores = compute_all_scores()
    
    for s in all_scores:
        CACHE[s["account_id"]] = {
            "account_id": s["account_id"],
            "mcs_score": s["mcs_score"],
            "risk_band": s["risk_band"]
        }
        
    print(f"Successfully loaded and scored {len(all_scores)} accounts.")
    yield
    # --- Shutdown ---
    pass


app = FastAPI(
    title="MULESHIELD API",
    description="Mule-account risk-intelligence platform API",
    version="0.1.0",
    lifespan=lifespan
)

# ---------------------------------------------------------------------------
# CORS — allow the Vite dev server during local development
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ActionRequest(BaseModel):
    action: str

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Simple liveness probe the frontend can call to verify connectivity."""
    return {"status": "ok", "service": "muleshield-api"}

@app.get("/accounts")
async def list_accounts():
    """Returns a summarized list of all accounts (cached)."""
    return list(CACHE.values())

@app.get("/accounts/{account_id}")
async def get_account(account_id: int):
    """Returns full scoring details and SHAP explanations for a single account."""
    if account_id not in CACHE:
        raise HTTPException(status_code=404, detail=f"Account ID {account_id} not found.")
        
    # Recompute live full details
    mcs_data = compute_mcs(account_id)
    
    # Get plain-language SHAP explanations
    explain_data = get_explanation(account_id)
    mcs_data["top_shap_contributions"] = explain_data.get("top_shap_contributions", [])
    
    # Inject active status if any
    if account_id in ACTIONS:
        mcs_data["action"] = ACTIONS[account_id]
        
    return mcs_data

@app.post("/accounts/{account_id}/action")
async def take_action(account_id: int, req: ActionRequest):
    """Stores an analyst action (mule, clear, escalate) on an account."""
    if account_id not in CACHE:
        raise HTTPException(status_code=404, detail=f"Account ID {account_id} not found.")
        
    valid_actions = ["mule", "clear", "escalate"]
    if req.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Action must be one of: {', '.join(valid_actions)}")
        
    ACTIONS[account_id] = req.action
    
    # Return the updated record
    return await get_account(account_id)

@app.get("/rules/config")
async def read_config():
    """Returns the current deterministic rule thresholds."""
    return get_config()

@app.put("/rules/config")
async def write_config(updates: Dict[str, Any]):
    """Applies partial updates to rule configurations."""
    update_config(updates)
    return {"recompute_needed": True}
