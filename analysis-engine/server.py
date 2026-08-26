"""UnitForge Analysis Engine — HTTP Server.

Wraps the analysis engine as a FastAPI service so the dashboard
(or any HTTP client) can trigger code analysis without a local CLI.

Deploy on Render as a separate service.

Usage::

    python server.py                        # starts on PORT (default 8001)
    POST http://localhost:8001/analyze       # analyse a GitHub repo
    GET  http://localhost:8001/health        # liveness probe
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from github_cloner import cleanup_clone, clone_repository, is_github_url
from models.module_map import ModuleMap
from parsers.openapi_parser import parse_openapi_spec
from parsers.python_parser import parse_python_directory, parse_python_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="UnitForge Analysis Engine",
    description="Analyzes Python/Java codebases and OpenAPI specs",
    version="0.7.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """Body for the ``POST /analyze`` endpoint."""

    url: str
    input_type: str = "python"


class AnalyzeResponse(BaseModel):
    """Structured response returned by ``POST /analyze``."""

    success: bool
    module_count: int
    module_map: dict
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
@app.head("/health")
def health() -> dict:
    """Health check — supports both GET and HEAD for monitors."""
    return {"status": "UP", "service": "UnitForge Analysis Engine"}


@app.get("/")
@app.head("/")
def root() -> dict:
    return {"service": "UnitForge Analysis Engine", "health": "/health"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze a GitHub URL or OpenAPI spec URL.

    Accepts:
      - GitHub URL: ``https://github.com/user/repo``
      - Local path (for CLI/Docker usage)

    Returns the full module_map JSON ready to POST
    to the orchestrator ``/api/jobs`` endpoint.
    """
    logger.info(
        "Analyze request: url=%s, type=%s", request.url, request.input_type,
    )

    clone_result = None
    try:
        # --- Resolve input path (GitHub URL or local) ---------------
        if is_github_url(request.url):
            clone_result = clone_repository(request.url)
            if not clone_result.success:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Failed to clone repository: "
                        f"{clone_result.error_message}"
                    ),
                )
            actual_path = clone_result.local_path
            logger.info("Cloned to %s", actual_path)
        else:
            actual_path = request.url

        # --- Run the appropriate parser -----------------------------
        if request.input_type == "python":
            modules = parse_python_directory(actual_path)
            module_map = ModuleMap(modules=modules)
        elif request.input_type == "openapi":
            module = parse_openapi_spec(actual_path)
            module_map = ModuleMap(modules=[module])
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported type: {request.input_type}. "
                    f"Use python or openapi"
                ),
            )

        module_map_dict = module_map.to_dict()
        module_count = len(module_map_dict.get("modules", []))

        logger.info("Analysis complete — %d modules found", module_count)

        return AnalyzeResponse(
            success=True,
            module_count=module_count,
            module_map=module_map_dict,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Analysis failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {exc}",
        )
    finally:
        if clone_result:
            cleanup_clone(clone_result)


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8001"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
