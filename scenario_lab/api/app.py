"""
FastAPI Application for Scenario Lab V2

Provides REST API and WebSocket endpoints for programmatic scenario execution,
monitoring, and analytics.
"""
from __future__ import annotations
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from scenario_lab import __version__
from scenario_lab.runners import SyncRunner
from scenario_lab.database import Database
from scenario_lab.core.events import Event, EventType

logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Scenario Lab API",
    description="AI-powered multi-actor scenario simulation framework",
    version=__version__,
)

# CORS middleware for web dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
running_scenarios: Dict[str, Dict[str, Any]] = {}
database: Optional[Database] = None


# Pydantic models for API
class ScenarioExecuteRequest(BaseModel):
    """Request to execute a scenario"""

    scenario_path: str = Field(..., description="Path to scenario directory")
    max_turns: Optional[int] = Field(None, description="Maximum number of turns")
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
    """Initialize database on startup"""
    global database
    database = Database("sqlite:///scenario-lab.db")
    logger.info("Scenario Lab API started")


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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": __version__,
        "database": "connected" if database else "not configured",
        "running_scenarios": len(running_scenarios),
    }


@app.post("/api/scenarios/execute", response_model=ScenarioStatus)
async def execute_scenario(
    request: ScenarioExecuteRequest, background_tasks: BackgroundTasks
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
            max_turns=request.max_turns,
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

        # Update status
        running_scenarios[scenario_id]["status"] = "completed"
        running_scenarios[scenario_id]["current_turn"] = final_state.turn
        running_scenarios[scenario_id]["total_cost"] = final_state.total_cost()
        running_scenarios[scenario_id]["completed_at"] = datetime.now()
        running_scenarios[scenario_id]["run_id"] = final_state.run_id

        logger.info(f"Scenario {scenario_id} completed successfully")

    except Exception as e:
        logger.error(f"Scenario {scenario_id} failed: {e}")
        running_scenarios[scenario_id]["status"] = "failed"
        running_scenarios[scenario_id]["error"] = str(e)
        running_scenarios[scenario_id]["completed_at"] = datetime.now()


@app.get("/api/scenarios/{scenario_id}/status", response_model=ScenarioStatus)
async def get_scenario_status(scenario_id: str):
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
    )


@app.get("/api/runs", response_model=list[RunSummary])
async def list_runs(scenario: Optional[str] = None):
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
async def get_run(run_id: str):
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
async def get_run_statistics(run_id: str):
    """Get comprehensive statistics for a run"""
    if not database:
        raise HTTPException(status_code=503, detail="Database not configured")

    stats = database.get_run_statistics(run_id)
    if not stats:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    return stats


@app.post("/api/runs/compare")
async def compare_runs(run_ids: list[str]):
    """Compare multiple runs side by side"""
    if not database:
        raise HTTPException(status_code=503, detail="Database not configured")

    comparison = database.compare_runs(run_ids)
    return comparison


@app.get("/api/metrics/{metric_name}/aggregate")
async def aggregate_metric(metric_name: str, scenario: Optional[str] = None):
    """Aggregate a metric across runs"""
    if not database:
        raise HTTPException(status_code=503, detail="Database not configured")

    aggregation = database.aggregate_metrics(metric_name, scenario=scenario)
    return aggregation


@app.websocket("/api/scenarios/{scenario_id}/stream")
async def websocket_stream(websocket: WebSocket, scenario_id: str):
    """
    WebSocket endpoint for real-time scenario updates

    Streams events as they happen during scenario execution.
    """
    await websocket.accept()

    try:
        # Wait for scenario to exist
        while scenario_id not in running_scenarios:
            await asyncio.sleep(0.1)

        runner = running_scenarios[scenario_id].get("runner")
        if not runner:
            await websocket.send_json({"error": "Runner not initialized"})
            await websocket.close()
            return

        # Setup event handlers to forward to WebSocket
        @runner.event_bus.on("*")
        async def forward_event(event: Event):
            try:
                await websocket.send_json(
                    {
                        "type": event.type,
                        "data": event.data,
                        "timestamp": event.timestamp.isoformat(),
                    }
                )
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")

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
