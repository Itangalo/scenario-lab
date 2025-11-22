# Scenario Lab Web Interface

Web-based interface for human interaction with Scenario Lab scenarios.

## ⚠️ IMPORTANT: Use V2 API

The web backend in this directory (`web/app.py`) is **DEPRECATED**.

**Please use the V2 API instead:**

```bash
# Start the V2 API server
scenario-lab serve

# Or with options
scenario-lab serve --host 0.0.0.0 --port 8000 --reload
```

- **Location**: `scenario_lab/api/app.py`
- **Documentation**: http://localhost:8000/docs
- **Guide**: See `docs/API.md` and `docs/PHASE_5_WEB_INTEGRATION.md`

---

## Features

- **Human Actor Participation**: Control actors in real-time during scenario execution
- **Real-time Dashboard**: Monitor scenario progress with live updates
- **Scenario Viewer**: Browse and view completed scenario runs
- **WebSocket Updates**: Real-time status updates via WebSocket connection

## Architecture

### Backend: V2 REST API ✅

**Location**: `scenario_lab/api/app.py`

- **REST API**: Scenario execution, status queries, run analytics
- **WebSocket**: Real-time event streaming during scenario execution
- **Database**: Persistent storage for runs and analytics
- **Full V2 Integration**: Uses V2 SyncRunner, Database, Event system

### Frontend: React + TypeScript ✅

**Location**: `web/frontend/`

- Built with React, TypeScript, Vite
- Uses V2 API client (`src/api/client.ts`)
- Real-time WebSocket integration
- Human actor interface for decision submission

## Quick Start (V2 API)

### 1. Start V2 API Server

```bash
# From project root
scenario-lab serve
```

The server will be available at:

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/api/health

### 2. Start Frontend (Development)

```bash
# From web/frontend directory
cd web/frontend
npm install
npm run dev
```

Frontend dev server: http://localhost:5173

### 3. Production Build

```bash
# Build frontend
cd web/frontend
npm run build  # Outputs to web/static/

# Serve with V2 API (serves both API and static frontend)
scenario-lab serve
```

---

## Legacy V1 Backend (DEPRECATED)

The files `web/app.py` and `web/scenario_executor.py` are deprecated V1 components.

**DO NOT USE** - They will be removed in a future version.

If you need to run the legacy backend (not recommended):

```bash
# Install dependencies
pip install -r web/requirements.txt

# Run (DEPRECATED)
cd web
python app.py
```

## API Endpoints

### Scenario Control

- `GET /api/status` - Get current scenario status
- `POST /api/scenario/start` - Start a new scenario
- `POST /api/scenario/pause` - Pause running scenario
- `POST /api/scenario/resume` - Resume paused scenario
- `POST /api/scenario/stop` - Stop scenario execution
- `POST /api/human/decision` - Submit human actor decision

### Browse

- `GET /api/scenarios` - List available scenarios
- `GET /api/runs` - List completed runs

### Real-time Updates

- `WS /ws` - WebSocket connection for live updates

## Example API Usage

### Start a Scenario

```bash
curl -X POST "http://localhost:8000/api/scenario/start" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_path": "scenarios/ai-summit-4actors",
    "end_turn": 5
  }'
```

### Check Status

```bash
curl "http://localhost:8000/api/status"
```

### Submit Human Decision

```bash
curl -X POST "http://localhost:8000/api/human/decision" \
  -H "Content-Type: application/json" \
  -d '{
    "actor_name": "EU",
    "turn": 1,
    "long_term_goals": ["Establish AI safety standards", "Maintain competitiveness"],
    "short_term_priorities": ["Draft regulation proposal"],
    "reasoning": "Given the current situation...",
    "action": "Propose a comprehensive AI safety framework"
  }'
```

## WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};

// Send ping to keep connection alive
setInterval(() => ws.send('ping'), 30000);
```

## Development

The server uses FastAPI's automatic reload during development. Any changes to `app.py` will trigger a restart.

### Interactive API Documentation

Visit http://localhost:8000/docs to see Swagger UI with:

- All endpoints documented
- Try-it-out functionality
- Request/response schemas
- WebSocket testing

## Next Steps

1. **Frontend Development**: React + TypeScript dashboard (in progress)
2. **Scenario Execution Integration**: Connect API to actual scenario runner
3. **Human Actor Workflow**: Complete the decision submission and execution flow
4. **Authentication**: Add user authentication (Phase 5)

## Technology Stack

- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server
- **WebSockets**: Real-time communication
- **Pydantic**: Data validation
