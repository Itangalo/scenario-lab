#!/usr/bin/env python3
"""
Scenario Lab Web Server - FastAPI backend for human interaction

Provides:
- REST API for scenario control
- WebSocket for real-time updates
- Static file serving for markdown files
- Human actor decision submission
"""
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
import json

# Add src to path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

# Import scenario_executor from local web directory
try:
    from scenario_executor import ScenarioExecutor, HumanDecision
except ImportError as e:
    print(f"Warning: Could not import scenario_executor: {e}")
    ScenarioExecutor = None
    HumanDecision = None

# Import core modules from src
try:
    from scenario_parser import ScenarioParser
    from world_state import WorldState
except ImportError as e:
    print(f"Warning: Could not import core modules: {e}")
    ScenarioParser = None
    WorldState = None


# Pydantic models for API requests/responses
class ScenarioStartRequest(BaseModel):
    scenario_path: str
    max_turns: Optional[int] = None
    credit_limit: Optional[float] = None


class HumanDecisionRequest(BaseModel):
    long_term_goals: List[str]
    short_term_priorities: List[str]
    reasoning: str
    action: str


class ScenarioStatus(BaseModel):
    scenario_path: Optional[str]
    current_turn: int
    max_turns: Optional[int]
    status: str  # 'idle', 'running', 'waiting_for_human', 'paused', 'completed'
    waiting_for_actor: Optional[str]
    total_cost: float
    actors: List[Dict[str, Any]]


# FastAPI app
app = FastAPI(
    title="Scenario Lab",
    description="AI-powered scenario simulation with human interaction",
    version="0.6.0"
)

# CORS middleware for development (frontend on different port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React/Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (in production, use proper state management)
class ServerState:
    def __init__(self):
        self.executor: Optional['ScenarioExecutor'] = None
        self.scenario_task: Optional[asyncio.Task] = None

    def to_status(self) -> ScenarioStatus:
        if self.executor:
            return ScenarioStatus(
                scenario_path=self.executor.scenario_path,
                current_turn=self.executor.current_turn,
                max_turns=self.executor.max_turns,
                status='waiting_for_human' if self.executor.waiting_for_actor else
                       ('running' if self.executor.is_running else 'idle'),
                waiting_for_actor=self.executor.waiting_for_actor,
                total_cost=self.executor.cost_tracker.get_total_cost() if self.executor.cost_tracker else 0.0,
                actors=self.executor.get_actors_info()
            )
        else:
            return ScenarioStatus(
                scenario_path=None,
                current_turn=0,
                max_turns=None,
                status='idle',
                waiting_for_actor=None,
                total_cost=0.0,
                actors=[]
            )

state = ServerState()


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")

manager = ConnectionManager()


# API Endpoints

@app.get("/api")
async def root():
    """API info endpoint"""
    return {
        "name": "Scenario Lab API",
        "version": "0.6.0",
        "status": "running"
    }


@app.get("/api/status")
async def get_status() -> ScenarioStatus:
    """Get current scenario status"""
    return state.to_status()


@app.post("/api/scenario/start")
async def start_scenario(request: ScenarioStartRequest):
    """Start a new scenario"""
    if state.executor and state.executor.is_running:
        raise HTTPException(status_code=400, detail="Scenario already running")

    # Validate scenario path exists
    if not os.path.exists(request.scenario_path):
        raise HTTPException(status_code=404, detail=f"Scenario not found: {request.scenario_path}")

    if not ScenarioExecutor:
        raise HTTPException(status_code=500, detail="Scenario execution not available")

    try:
        # Create executor
        state.executor = ScenarioExecutor(
            scenario_path=request.scenario_path,
            max_turns=request.max_turns,
            credit_limit=request.credit_limit
        )

        # Set up callbacks for WebSocket updates
        async def broadcast_status(status_data: dict):
            await manager.broadcast(status_data)

        state.executor.set_status_callback(broadcast_status)

        # Setup the executor
        success = await state.executor.setup()
        if not success:
            state.executor = None
            raise HTTPException(status_code=500, detail="Failed to setup scenario")

        # Start execution in background
        state.scenario_task = asyncio.create_task(state.executor.run())

        # Broadcast initial status
        await manager.broadcast({
            'type': 'scenario_started',
            'status': state.to_status().dict()
        })

        return {
            "message": "Scenario started",
            "scenario_path": request.scenario_path,
            "actors": state.executor.get_actors_info()
        }

    except Exception as e:
        state.executor = None
        raise HTTPException(status_code=500, detail=f"Failed to start scenario: {e}")


@app.post("/api/scenario/pause")
async def pause_scenario():
    """Pause running scenario"""
    if not state.executor or not state.executor.is_running:
        raise HTTPException(status_code=400, detail="No scenario running")

    state.executor.pause()

    await manager.broadcast({
        'type': 'scenario_paused',
        'status': state.to_status().dict()
    })

    return {"message": "Scenario paused"}


@app.post("/api/scenario/resume")
async def resume_scenario():
    """Resume paused scenario"""
    if not state.executor or not state.executor.is_paused:
        raise HTTPException(status_code=400, detail="Scenario not paused")

    state.executor.resume()

    await manager.broadcast({
        'type': 'scenario_resumed',
        'status': state.to_status().dict()
    })

    return {"message": "Scenario resumed"}


@app.post("/api/scenario/stop")
async def stop_scenario():
    """Stop scenario execution"""
    if state.executor:
        state.executor.stop()

    if state.scenario_task:
        state.scenario_task.cancel()

    state.executor = None

    await manager.broadcast({
        'type': 'scenario_stopped',
        'status': state.to_status().dict()
    })

    return {"message": "Scenario stopped"}


@app.post("/api/human/decision")
async def submit_human_decision(decision: HumanDecisionRequest):
    """Submit a human actor's decision"""
    if not state.executor or not state.executor.waiting_for_actor:
        raise HTTPException(status_code=400, detail="Not waiting for human decision")

    if not HumanDecision:
        raise HTTPException(status_code=500, detail="Human decision processing not available")

    # Submit decision to executor
    human_decision = HumanDecision(
        long_term_goals=decision.long_term_goals,
        short_term_priorities=decision.short_term_priorities,
        reasoning=decision.reasoning,
        action=decision.action
    )

    state.executor.submit_human_decision(human_decision)

    await manager.broadcast({
        'type': 'human_decision_received',
        'actor': state.executor.waiting_for_actor,
        'turn': state.executor.current_turn
    })

    return {"message": "Decision received and submitted", "actor": state.executor.waiting_for_actor}


@app.get("/api/scenarios")
async def list_scenarios():
    """List available scenarios"""
    scenarios_dir = Path(__file__).parent.parent / 'scenarios'
    if not scenarios_dir.exists():
        return {"scenarios": []}

    scenarios = []
    for item in scenarios_dir.iterdir():
        if item.is_dir() and (item / 'scenario.yaml').exists():
            scenarios.append({
                'name': item.name,
                'path': str(item)
            })

    return {"scenarios": scenarios}


@app.get("/api/runs")
async def list_runs():
    """List completed scenario runs"""
    output_dir = Path(__file__).parent.parent / 'output'
    if not output_dir.exists():
        return {"runs": []}

    runs = []
    for scenario_dir in output_dir.iterdir():
        if scenario_dir.is_dir():
            for run_dir in scenario_dir.iterdir():
                if run_dir.is_dir() and run_dir.name.startswith('run-'):
                    runs.append({
                        'scenario': scenario_dir.name,
                        'run': run_dir.name,
                        'path': str(run_dir)
                    })

    return {"runs": runs}


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time scenario updates"""
    await manager.connect(websocket)

    try:
        # Send initial status
        await websocket.send_json({
            'type': 'status_update',
            'status': state.to_status().dict()
        })

        # Keep connection alive
        while True:
            # Wait for messages from client (ping/pong, etc.)
            data = await websocket.receive_text()

            # Echo back for now (can handle client messages if needed)
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Serve static files (for markdown viewing)
output_dir = Path(__file__).parent.parent / 'output'
if output_dir.exists():
    app.mount("/output", StaticFiles(directory=str(output_dir)), name="output")

# Serve frontend static files (built React app)
static_dir = Path(__file__).parent / 'static'
if static_dir.exists():
    # Mount assets directory for JS/CSS
    assets_dir = static_dir / 'assets'
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # Catch-all route to serve index.html for React Router
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve frontend application (catch-all for React Router)"""
        # Don't intercept API routes
        if full_path.startswith('api/') or full_path.startswith('ws') or full_path.startswith('output/'):
            raise HTTPException(status_code=404)

        # Serve index.html for all other routes
        index_path = static_dir / 'index.html'
        if index_path.exists():
            return FileResponse(str(index_path))
        else:
            raise HTTPException(status_code=404, detail="Frontend not built")


# Development server
if __name__ == "__main__":
    print("Starting Scenario Lab Web Server...")
    print("API: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
