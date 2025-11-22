# Scenario Lab API Documentation

The Scenario Lab V2 API provides programmatic access to scenario execution, monitoring, and analytics.

## Quick Start

### Start the API Server

```bash
# Start server (default: http://0.0.0.0:8000)
scenario-lab serve

# Custom host and port
scenario-lab serve --host localhost --port 8080

# Development mode with auto-reload
scenario-lab serve --reload
```

### Access API Documentation

Once the server is running:

- **Interactive API Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/api/health

## API Endpoints

### Scenario Execution

#### POST /api/scenarios/execute

Execute a scenario in the background.

**Request:**
```json
{
  "scenario_path": "scenarios/ai-summit",
  "end_turn": 10,
  "credit_limit": 5.0,
  "output_path": "output/custom-path",
  "enable_database": true
}
```

**Response:**
```json
{
  "scenario_id": "scenario-20250119-123456",
  "status": "initializing",
  "current_turn": 0,
  "total_cost": 0.0,
  "started_at": "2025-01-19T12:34:56"
}
```

#### GET /api/scenarios/{scenario_id}/status

Get the current status of a running or completed scenario.

**Response:**
```json
{
  "scenario_id": "scenario-20250119-123456",
  "status": "running",
  "current_turn": 5,
  "total_cost": 2.45,
  "started_at": "2025-01-19T12:34:56",
  "completed_at": null,
  "error": null
}
```

**Status values:**
- `initializing` - Setting up scenario
- `running` - Executing turns
- `completed` - Finished successfully
- `halted` - Stopped due to limits
- `failed` - Error occurred

### Run Management

#### GET /api/runs

List all runs, optionally filtered by scenario.

**Query Parameters:**
- `scenario` (optional): Filter by scenario ID

**Response:**
```json
[
  {
    "run_id": "run-20250119-123456",
    "scenario_name": "AI Summit",
    "status": "completed",
    "turns": 10,
    "total_cost": 4.32,
    "created": "2025-01-19T12:34:56"
  }
]
```

#### GET /api/runs/{run_id}

Get detailed information about a specific run.

**Response:**
```json
{
  "run_id": "run-20250119-123456",
  "scenario": "AI Summit",
  "status": "completed",
  "turns": 10,
  "decisions": 30,
  "communications": 12,
  "metrics": 45,
  "total_cost": 4.32,
  "cost_by_phase": {
    "communication": 0.85,
    "decision": 2.10,
    "world_update": 1.37
  },
  "created": "2025-01-19T12:34:56"
}
```

#### GET /api/runs/{run_id}/statistics

Get comprehensive statistics for a run (same as above).

### Analytics

#### POST /api/runs/compare

Compare multiple runs side by side.

**Request:**
```json
["run-001", "run-002", "run-003"]
```

**Response:**
```json
{
  "runs": [
    {
      "run_id": "run-001",
      "scenario": "AI Summit",
      "turns": 10,
      "total_cost": 4.32,
      ...
    },
    ...
  ]
}
```

#### GET /api/metrics/{metric_name}/aggregate

Aggregate a metric across runs.

**Query Parameters:**
- `scenario` (optional): Filter by scenario ID

**Response:**
```json
{
  "metric": "cooperation_level",
  "min": 0.3,
  "max": 0.9,
  "avg": 0.65,
  "count": 45,
  "scenario": null
}
```

### WebSocket Streaming

#### WS /api/scenarios/{scenario_id}/stream

Stream real-time events during scenario execution.

**Event Format:**
```json
{
  "type": "turn_started",
  "data": {
    "turn": 5
  },
  "timestamp": "2025-01-19T12:34:56.789Z"
}
```

**Event Types:**
- `turn_started` - New turn begins
- `turn_completed` - Turn finishes
- `phase_completed` - Phase completes
- `credit_limit_warning` - Approaching cost limit
- `scenario_halted` - Scenario stopped
- `scenario_finished` - Scenario completed

## Python Client

Use the provided client for easy API access:

```python
from examples.api_client import ScenarioLabClient

client = ScenarioLabClient("http://localhost:8000")

# Execute scenario
result = await client.execute_scenario(
    scenario_path="scenarios/ai-summit",
    end_turn=10,
    credit_limit=5.0
)

# Monitor progress
status = await client.get_status(result["scenario_id"])
print(f"Status: {status['status']}, Turn: {status['current_turn']}")

# Stream events
async for event in client.stream_scenario(result["scenario_id"]):
    print(f"Event: {event['type']}")

# Query analytics
runs = await client.list_runs()
stats = await client.get_run_statistics(runs[0]["run_id"])
```

## Examples

See `examples/api_client.py` for complete examples:

```bash
# Execute and poll for status
python examples/api_client.py poll

# Execute and stream events
python examples/api_client.py stream

# Query run analytics
python examples/api_client.py analytics
```

## Authentication

Currently, the API does not require authentication. For production deployments:

1. Use API keys or OAuth2
2. Enable CORS appropriately
3. Use HTTPS/WSS
4. Rate limiting recommended

## Rate Limiting

No rate limiting is currently enforced. Consider adding:

- Per-user request limits
- Concurrent scenario execution limits
- Cost-based throttling

## Error Handling

All endpoints return standard HTTP status codes:

- `200` - Success
- `400` - Bad request
- `404` - Not found
- `500` - Server error
- `503` - Service unavailable

Error responses include details:
```json
{
  "detail": "Scenario not found: invalid-id"
}
```

## Database Requirements

The API requires database support for run persistence and analytics:

```python
# Database is initialized automatically on startup
# Default: sqlite:///scenario-lab.db

# Custom database URL via environment:
# export DATABASE_URL="postgresql://user:pass@localhost/scenario_lab"
```

## Performance Considerations

- Scenarios execute in background tasks
- Multiple scenarios can run concurrently
- WebSocket connections maintained per scenario
- Database queries use connection pooling

## Monitoring

Check server health:

```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "healthy",
  "version": "2.0.0-alpha.3",
  "database": "connected",
  "running_scenarios": 2
}
```

## Development

Start with auto-reload for development:

```bash
scenario-lab serve --reload
```

API changes will automatically restart the server.
