"""
FastAPI Application for Scenario Lab V2

Provides REST API and WebSocket endpoints for programmatic scenario execution,
monitoring, and analytics.

Authentication and Rate Limiting:
    - API key authentication via X-API-Key header (configurable)
    - Rate limiting with configurable requests/window
    - Development mode for local testing (bypasses auth and rate limits)

CORS Configuration:
    - By default, only localhost origins are allowed for security
    - Configure allowed origins via SCENARIO_LAB_CORS_ORIGINS for production

Environment Variables:
    SCENARIO_LAB_API_KEY: API key(s) for authentication (comma-separated)
    SCENARIO_LAB_AUTH_ENABLED: Enable/disable authentication
    SCENARIO_LAB_RATE_LIMIT_ENABLED: Enable/disable rate limiting
    SCENARIO_LAB_RATE_LIMIT_REQUESTS: Max requests per window (default: 100)
    SCENARIO_LAB_RATE_LIMIT_WINDOW: Time window in seconds (default: 60)
    SCENARIO_LAB_DEV_MODE: Development mode (disables auth and rate limiting)
    SCENARIO_LAB_CORS_ORIGINS: Comma-separated list of allowed CORS origins
                               (default: localhost only for security)
"""
from __future__ import annotations
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from scenario_lab import __version__
from scenario_lab.runners import SyncRunner
from scenario_lab.database import Database
from scenario_lab.core.events import Event, EventType
from scenario_lab.api.settings import get_settings
from scenario_lab.api.auth import verify_api_key, optional_api_key
from scenario_lab.api.rate_limit import check_rate_limit, get_rate_limiter

logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Scenario Lab API",
    description="AI-powered multi-actor scenario simulation framework",
    version=__version__,
)


def configure_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware with settings from environment.

    CORS origins are loaded from the SCENARIO_LAB_CORS_ORIGINS environment variable
    (comma-separated list). If not set, defaults to localhost only for security.

    For production, set SCENARIO_LAB_CORS_ORIGINS to your frontend domain(s):
        export SCENARIO_LAB_CORS_ORIGINS="https://app.example.com,https://admin.example.com"
    """
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Configure CORS middleware for web dashboard
configure_cors(app)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware to add rate limit headers to responses.

    Also handles rate limit checking for all routes.
    """
    settings = get_settings()

    # Skip rate limiting for health and root endpoints
    if request.url.path in ["/", "/api/health", "/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)

    # Check rate limit
    if settings.rate_limit_enabled and not settings.dev_mode:
        limiter = get_rate_limiter()
        # Extract API key from header for rate limit tracking
        api_key = request.headers.get("X-API-Key")
        allowed, remaining, reset_seconds = limiter.check_rate_limit(request, api_key)

        if not allowed:
            return Response(
                content=f"Rate limit exceeded. Try again in {reset_seconds} seconds.",
                status_code=429,
                headers={
                    "Retry-After": str(reset_seconds),
                    "X-RateLimit-Limit": str(settings.rate_limit_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_seconds),
                },
            )

        # Process request and add headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    return await call_next(request)

# Global state
running_scenarios: Dict[str, Dict[str, Any]] = {}
database: Optional[Database] = None


# Pydantic models for API
class ScenarioExecuteRequest(BaseModel):
    """Request to execute a scenario"""

    scenario_path: str = Field(..., description="Path to scenario directory")
    end_turn: Optional[int] = Field(None, description="Turn number to stop at")
    credit_limit: Optional[float] = Field(None, description="Maximum cost in USD")
    output_path: Optional[str] = Field(None, description="Output directory path")
    enable_database: bool = Field(
        True, description="Enable database persistence for analytics"
    )


class ScenarioStatus(BaseModel):
    """Status of a running or completed scenario"""

    scenario_id: str
    status: str  # running, completed, halted, failed
    current_turn: int
    total_cost: float
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    waiting_for_human: Optional[str] = None  # Actor name waiting for input


class HumanDecisionRequest(BaseModel):
    """Human actor decision submission"""

    actor: str
    long_term_goals: list[str]
    short_term_priorities: list[str]
    reasoning: str
    action: str


class RunSummary(BaseModel):
    """Summary of a completed run"""

    run_id: str
    scenario_name: str
    status: str
    turns: int
    total_cost: float
    created: datetime


@app.on_event("startup")
async def startup_event():
    """Initialize database and log configuration on startup"""
    global database
    try:
        database = Database("sqlite:///scenario-lab.db")
        logger.info("Scenario Lab API started with database")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.warning("API will run without database support")
        database = None

    # Log authentication and rate limiting configuration
    settings = get_settings()
    if settings.dev_mode:
        logger.warning("API running in DEVELOPMENT MODE - auth and rate limiting disabled")
    else:
        if settings.auth_enabled:
            logger.info(f"API authentication enabled with {len(settings.api_keys)} API key(s)")
        else:
            logger.warning("API authentication DISABLED - no API keys configured or auth explicitly disabled")

        if settings.rate_limit_enabled:
            logger.info(
                f"Rate limiting enabled: {settings.rate_limit_requests} requests per {settings.rate_limit_window}s"
            )
        else:
            logger.warning("Rate limiting DISABLED")

    # Log CORS configuration
    logger.info(f"CORS allowed origins: {settings.cors_allowed_origins}")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Scenario Lab API",
        "version": __version__,
        "status": "running",
        "endpoints": {
            "scenarios": "/api/scenarios",
            "runs": "/api/runs",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint (no authentication required)"""
    settings = get_settings()
    return {
        "status": "healthy",
        "version": __version__,
        "database": "connected" if database else "not configured",
        "running_scenarios": len(running_scenarios),
        "auth_enabled": settings.auth_enabled,
        "rate_limit_enabled": settings.rate_limit_enabled,
        "dev_mode": settings.dev_mode,
    }


@app.post("/api/scenarios/execute", response_model=ScenarioStatus)
async def execute_scenario(
    request: ScenarioExecuteRequest,
    background_tasks: BackgroundTasks,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """
    Execute a scenario in the background

    Returns immediately with a scenario_id that can be used to monitor progress.
    """
    # Validate scenario path
    scenario_path = Path(request.scenario_path)
    if not scenario_path.exists():
        raise HTTPException(status_code=404, detail=f"Scenario not found: {request.scenario_path}")

    # Generate scenario ID
    scenario_id = f"scenario-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Initialize status
    running_scenarios[scenario_id] = {
        "scenario_id": scenario_id,
        "status": "initializing",
        "current_turn": 0,
        "total_cost": 0.0,
        "started_at": datetime.now(),
        "completed_at": None,
        "error": None,
        "runner": None,
    }

    # Start scenario in background
    background_tasks.add_task(
        _run_scenario_background,
        scenario_id,
        request,
    )

    return ScenarioStatus(
        scenario_id=scenario_id,
        status="initializing",
        current_turn=0,
        total_cost=0.0,
        started_at=running_scenarios[scenario_id]["started_at"],
    )


async def _run_scenario_background(scenario_id: str, request: ScenarioExecuteRequest):
    """Run scenario in background task"""
    try:
        # Update status
        running_scenarios[scenario_id]["status"] = "running"

        # Create runner
        runner = SyncRunner(
            scenario_path=request.scenario_path,
            output_path=request.output_path,
            end_turn=request.end_turn,
            credit_limit=request.credit_limit,
            database=database if request.enable_database else None,
        )

        # Setup
        runner.setup()
        running_scenarios[scenario_id]["runner"] = runner

        # Setup event handlers to track progress
        @runner.event_bus.on(EventType.TURN_STARTED)
        async def on_turn_start(event: Event):
            turn = event.data.get("turn", 0)
            running_scenarios[scenario_id]["current_turn"] = turn

        @runner.event_bus.on(EventType.TURN_COMPLETED)
        async def on_turn_complete(event: Event):
            state = event.data.get("state")
            if state:
                running_scenarios[scenario_id]["total_cost"] = state.total_cost()

        @runner.event_bus.on(EventType.SCENARIO_HALTED)
        async def on_halted(event: Event):
            reason = event.data.get("reason", "unknown")
            running_scenarios[scenario_id]["status"] = "halted"
            running_scenarios[scenario_id]["error"] = reason

        # Execute scenario
        final_state = await runner.run()

        # Update status based on final state (if not already set by event handler)
        if running_scenarios[scenario_id]["status"] not in ["halted", "failed"]:
            running_scenarios[scenario_id]["status"] = final_state.status.value

        running_scenarios[scenario_id]["current_turn"] = final_state.turn
        running_scenarios[scenario_id]["total_cost"] = final_state.total_cost()
        running_scenarios[scenario_id]["completed_at"] = datetime.now()
        running_scenarios[scenario_id]["run_id"] = final_state.run_id

        logger.info(f"Scenario {scenario_id} completed with status: {final_state.status.value}")

    except Exception as e:
        logger.error(f"Scenario {scenario_id} failed: {e}")
        running_scenarios[scenario_id]["status"] = "failed"
        running_scenarios[scenario_id]["error"] = str(e)
        running_scenarios[scenario_id]["completed_at"] = datetime.now()


@app.get("/api/scenarios/{scenario_id}/status", response_model=ScenarioStatus)
async def get_scenario_status(
    scenario_id: str,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """Get the current status of a running or completed scenario"""
    if scenario_id not in running_scenarios:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")

    info = running_scenarios[scenario_id]
    return ScenarioStatus(
        scenario_id=scenario_id,
        status=info["status"],
        current_turn=info["current_turn"],
        total_cost=info["total_cost"],
        started_at=info["started_at"],
        completed_at=info["completed_at"],
        error=info["error"],
        waiting_for_human=info.get("waiting_for_human"),
    )


@app.get("/api/runs", response_model=list[RunSummary])
async def list_runs(
    scenario: Optional[str] = None,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """List all runs, optionally filtered by scenario"""
    if not database:
        raise HTTPException(status_code=503, detail="Database not configured")

    runs = database.list_runs(scenario_id=scenario)

    return [
        RunSummary(
            run_id=run.id,
            scenario_name=run.scenario_name,
            status=run.status,
            turns=run.total_turns,
            total_cost=run.total_cost,
            created=run.created,
        )
        for run in runs
    ]


@app.get("/api/runs/{run_id}")
async def get_run(
    run_id: str,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """Get detailed information about a specific run"""
    if not database:
        raise HTTPException(status_code=503, detail="Database not configured")

    run = database.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    # Get statistics
    stats = database.get_run_statistics(run_id)

    return stats


@app.get("/api/runs/{run_id}/statistics")
async def get_run_statistics(
    run_id: str,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """Get comprehensive statistics for a run"""
    if not database:
        raise HTTPException(status_code=503, detail="Database not configured")

    stats = database.get_run_statistics(run_id)
    if not stats:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    return stats


@app.post("/api/runs/compare")
async def compare_runs(
    run_ids: list[str],
    api_key: Optional[str] = Depends(verify_api_key),
):
    """Compare multiple runs side by side"""
    if not database:
        raise HTTPException(status_code=503, detail="Database not configured")

    comparison = database.compare_runs(run_ids)
    return comparison


@app.get("/api/metrics/{metric_name}/aggregate")
async def aggregate_metric(
    metric_name: str,
    scenario: Optional[str] = None,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """Aggregate a metric across runs"""
    if not database:
        raise HTTPException(status_code=503, detail="Database not configured")

    aggregation = database.aggregate_metrics(metric_name, scenario=scenario)
    return aggregation


@app.post("/api/scenarios/{scenario_id}/pause")
async def pause_scenario(
    scenario_id: str,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """Pause a running scenario"""
    if scenario_id not in running_scenarios:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")

    runner = running_scenarios[scenario_id].get("runner")
    if not runner:
        raise HTTPException(status_code=400, detail="Scenario not yet initialized")

    # Note: Pause functionality would need to be added to SyncRunner
    # For now, just update status
    running_scenarios[scenario_id]["paused"] = True

    return {"message": "Scenario paused", "scenario_id": scenario_id}


@app.post("/api/scenarios/{scenario_id}/resume")
async def resume_scenario(
    scenario_id: str,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """Resume a paused scenario"""
    if scenario_id not in running_scenarios:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")

    runner = running_scenarios[scenario_id].get("runner")
    if not runner:
        raise HTTPException(status_code=400, detail="Scenario not yet initialized")

    # Resume
    running_scenarios[scenario_id]["paused"] = False

    return {"message": "Scenario resumed", "scenario_id": scenario_id}


@app.post("/api/scenarios/{scenario_id}/human-decision")
async def submit_human_decision(
    scenario_id: str,
    decision: HumanDecisionRequest,
    api_key: Optional[str] = Depends(verify_api_key),
):
    """Submit a human actor's decision"""
    if scenario_id not in running_scenarios:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {scenario_id}")

    runner = running_scenarios[scenario_id].get("runner")
    if not runner:
        raise HTTPException(status_code=400, detail="Scenario not yet initialized")

    # Store the decision in the scenario's state
    # Note: This is a simplified implementation
    # Full implementation would need proper integration with the orchestrator
    if "human_decisions" not in running_scenarios[scenario_id]:
        running_scenarios[scenario_id]["human_decisions"] = {}

    running_scenarios[scenario_id]["human_decisions"][decision.actor] = {
        "long_term_goals": decision.long_term_goals,
        "short_term_priorities": decision.short_term_priorities,
        "reasoning": decision.reasoning,
        "action": decision.action,
    }

    # Clear waiting status
    running_scenarios[scenario_id]["waiting_for_human"] = None

    logger.info(f"Human decision received for {decision.actor} in scenario {scenario_id}")

    return {
        "message": "Decision received",
        "actor": decision.actor,
        "scenario_id": scenario_id,
    }


@app.websocket("/api/scenarios/{scenario_id}/stream")
async def websocket_stream(websocket: WebSocket, scenario_id: str):
    """
    WebSocket endpoint for real-time scenario updates

    Streams events as they happen during scenario execution.
    """
    await websocket.accept()

    try:
        # Wait for scenario to exist (with timeout)
        timeout = 30  # 30 seconds
        elapsed = 0
        while scenario_id not in running_scenarios:
            if elapsed >= timeout:
                await websocket.send_json({"error": "Scenario not found or timeout"})
                await websocket.close()
                return
            await asyncio.sleep(0.1)
            elapsed += 0.1

        # Wait for runner to be initialized (with timeout)
        runner = None
        elapsed = 0
        while not runner:
            runner = running_scenarios[scenario_id].get("runner")
            if elapsed >= timeout:
                await websocket.send_json({"error": "Runner initialization timeout"})
                await websocket.close()
                return
            if not runner:
                await asyncio.sleep(0.1)
                elapsed += 0.1

        # Setup event handlers to forward to WebSocket
        handlers = []

        async def forward_event(event: Event):
            try:
                # Convert float timestamp to ISO format datetime
                timestamp_dt = datetime.fromtimestamp(event.timestamp)

                await websocket.send_json(
                    {
                        "type": event.type,
                        "data": event.data,
                        "timestamp": timestamp_dt.isoformat(),
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")

        # Register handler and keep reference for cleanup
        runner.event_bus.on("*", forward_event)
        handlers.append(forward_event)

        # Keep connection alive
        while True:
            # Check if scenario is still running
            if running_scenarios[scenario_id]["status"] in ["completed", "failed", "halted"]:
                await websocket.send_json(
                    {
                        "type": "scenario_finished",
                        "data": {
                            "status": running_scenarios[scenario_id]["status"],
                            "final_turn": running_scenarios[scenario_id]["current_turn"],
                            "total_cost": running_scenarios[scenario_id]["total_cost"],
                        },
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                break

            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for scenario {scenario_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
