"""
VICTOR-SSI API Gateway
Minimal FastAPI entrypoint providing health and component discovery endpoints.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI(
    title="VICTOR-SSI API Gateway",
    description="Orchestration gateway for the MASSIVEMAGNETICS Aether Hub platform.",
    version="0.1.0",
)

RAGFLOW_URL = os.getenv("RAGFLOW_URL", "http://ragflow:5100")
CONSCIOUS_RIVER_URL = os.getenv("CONSCIOUS_RIVER_URL", "http://conscious-river:5200")
RESEARCH_AGENT_URL = os.getenv("RESEARCH_AGENT_URL", "http://research-agent:5300")


@app.get("/health")
async def health():
    """Liveness probe."""
    return {"status": "ok", "service": "gateway"}


@app.get("/components")
async def components():
    """Return configured component service URLs."""
    return {
        "ragflow": RAGFLOW_URL,
        "conscious_river": CONSCIOUS_RIVER_URL,
        "research_agent": RESEARCH_AGENT_URL,
    }
