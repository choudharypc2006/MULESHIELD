"""
MULESHIELD — Mule-Account Risk-Intelligence Platform
FastAPI entrypoint
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="MULESHIELD API",
    description="Mule-account risk-intelligence platform API",
    version="0.1.0",
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
# Health-check endpoint
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """Simple liveness probe the frontend can call to verify connectivity."""
    return {"status": "ok", "service": "muleshield-api"}
