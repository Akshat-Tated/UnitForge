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
    return {
        "status": "UP",
        "service": "UnitForge Test Agent",
        "agent": agent_status,
    }


@app.get("/")
def root():
    return {"service": "UnitForge Test Agent", "health": "/health"}


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
