# Scenario Lab Web Interface

Web-based interface for human interaction with Scenario Lab scenarios.

## Features

- **Human Actor Participation**: Control actors in real-time during scenario execution
- **Real-time Dashboard**: Monitor scenario progress with live updates
- **Scenario Viewer**: Browse and view completed scenario runs
- **WebSocket Updates**: Real-time status updates via WebSocket connection

## Architecture

### Backend (FastAPI)

- **REST API**: Scenario control, status queries, decision submission
- **WebSocket**: Real-time updates during scenario execution
- **Static Files**: Serves markdown files from completed runs

### Frontend (React + TypeScript)

Coming soon - currently the backend API is complete and can be accessed directly.

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt
```

## Running the Server

```bash
# From the web/ directory
python app.py

# Or using uvicorn directly
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at:

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)

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
    "max_turns": 5
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
