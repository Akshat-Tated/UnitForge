"""
Tiny HTTP health server for Render Web Service deployment.
Runs in a background thread alongside the Redis agent loop.
Render requires an HTTP port to treat this as a web service (free tier).
"""

import os
import threading
import uvicorn
from fastapi import FastAPI

app = FastAPI()

# Shared state — agent.py updates these
agent_status = {
    "status": "starting",
    "provider": "unknown",
    "tasks_processed": 0,
    "redis_connected": False,
}


@app.get("/health")
def health():
    """
    Always returns 200 OK.
    Render must see 200 to keep the service alive.
    503 causes Render to restart, making downtime worse.
    """
    return {
        "status": "UP",
        "service": "UnitForge Test Agent",
        "agent": agent_status,
    }


@app.head("/health")
def health_head():
    """Support HEAD requests from UptimeRobot monitors."""
    return {}

@app.get("/debug/fingerprint")
def get_fingerprint():
    import hashlib
    agent_token = os.getenv("AGENT_TOKEN", "").strip()
    if not agent_token:
        return {"fingerprint": "MISSING"}
    sha = hashlib.sha256(agent_token.encode('utf-8')).hexdigest()
    return {"fingerprint": sha[:8]}


@app.get("/")
def root():
    return {"service": "UnitForge Test Agent", "health": "/health"}


@app.head("/")
def root_head():
    return {}


def start_health_server():
    """Start the HTTP health server in a daemon thread."""
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="warning",  # quiet — agent logs are enough
    )


def start_in_background():
    """Launch health server without blocking the agent loop."""
    thread = threading.Thread(target=start_health_server, daemon=True)
    thread.start()
