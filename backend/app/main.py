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
from app.graph.builder import build_graph, compute_network_risk_signal

# ---------------------------------------------------------------------------
# In-Memory Stores
# ---------------------------------------------------------------------------
CACHE = {}
ACTIONS = {}
GRAPH = None

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
    
    global GRAPH
    print("Building synthetic transaction graph...")
    GRAPH = build_graph(CACHE)
    compute_network_risk_signal(GRAPH, CACHE)
    
    high_risk_ids = [acc_id for acc_id, data in CACHE.items() if data['risk_band'] == 'High']
    hr_with_edges = sum(1 for acc_id in high_risk_ids if GRAPH.degree(acc_id) > 0)
    
    print(f"Successfully generated graph with {GRAPH.number_of_nodes()} nodes and {GRAPH.number_of_edges()} edges.")
    print(f"Graph clusters: {hr_with_edges}/{len(high_risk_ids)} High-risk accounts have established network edges.")
    
    if hr_with_edges < len(high_risk_ids):
        missing = [acc_id for acc_id in high_risk_ids if GRAPH.degree(acc_id) == 0]
        print(f"Warning: The following High-risk accounts have no edges: {missing}")
    
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

@app.get("/accounts/{account_id}/network")
async def get_account_network(account_id: int):
    """Returns 1-hop graph neighborhood for the account."""
    if account_id not in CACHE:
        raise HTTPException(status_code=404, detail=f"Account ID {account_id} not found.")
        
    # If the node has no edges, return empty lists but include the node itself
    if GRAPH is None or account_id not in GRAPH or len(list(GRAPH.neighbors(account_id))) == 0:
        return {
            "nodes": [{"account_id": account_id, "risk_band": CACHE[account_id]["risk_band"], "mcs_score": CACHE[account_id]["mcs_score"]}],
            "edges": []
        }
        
    # Get 1-hop neighbors
    neighborhood_nodes = {account_id}
    for neighbor in GRAPH.neighbors(account_id):
        neighborhood_nodes.add(neighbor)
        
    # Build response
    nodes_res = []
    for n in neighborhood_nodes:
        nodes_res.append({
            "account_id": n,
            "risk_band": CACHE[n]["risk_band"],
            "mcs_score": CACHE[n]["mcs_score"]
        })
        
    edges_res = []
    subgraph = GRAPH.subgraph(neighborhood_nodes)
    for u, v, d in subgraph.edges(data=True):
        edges_res.append({
            "source": u,
            "target": v,
            "weight": d.get("weight", 1.0)
        })
        
    return {
        "nodes": nodes_res,
        "edges": edges_res
    }
