# Scenario Lab API Documentation

The Scenario Lab V2 API provides programmatic access to scenario execution, monitoring, and analytics. This document provides comprehensive documentation of all endpoints, authentication, rate limiting, and the WebSocket streaming protocol.

## Table of Contents

- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [API Endpoints](#api-endpoints)
  - [Health & Status](#health--status)
  - [Scenario Execution](#scenario-execution)
  - [Scenario Control](#scenario-control)
  - [Run Management](#run-management)
  - [Analytics](#analytics)
- [WebSocket Protocol](#websocket-protocol)
- [Error Handling](#error-handling)
- [Python Client](#python-client)
- [Configuration](#configuration)

---

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

- **Interactive API Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/api/health

### Make Your First Request

```bash
# Check API health (no authentication required)
curl http://localhost:8000/api/health

# Execute a scenario (requires API key if auth is enabled)
curl -X POST http://localhost:8000/api/scenarios/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"scenario_path": "scenarios/ai-summit", "end_turn": 5}'
```

---

## Authentication

The API uses API key authentication via the `X-API-Key` HTTP header. Authentication behavior is controlled by environment variables.

### Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `SCENARIO_LAB_API_KEY` | (none) | Comma-separated list of valid API keys |
| `SCENARIO_LAB_AUTH_ENABLED` | `true` (if keys exist) | Enable/disable authentication |
| `SCENARIO_LAB_DEV_MODE` | `false` | Development mode (bypasses auth and rate limiting) |

### Making Authenticated Requests

Include the `X-API-Key` header in all requests to protected endpoints:

```bash
curl -X GET http://localhost:8000/api/runs \
  -H "X-API-Key: your-secret-api-key"
```

### Authentication Responses

**Success (200 OK):**
Request proceeds normally.

**Missing API Key (401 Unauthorized):**

```json
{
  "detail": "Missing API key. Provide X-API-Key header."
}
```

**Invalid API Key (401 Unauthorized):**

```json
{
  "detail": "Invalid API key"
}
```

### Unauthenticated Endpoints

The following endpoints do not require authentication:

- `GET /` - Root endpoint with API information
- `GET /api/health` - Health check endpoint
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation
- `GET /openapi.json` - OpenAPI schema

### Development Mode

For local development, enable dev mode to bypass authentication:

```bash
export SCENARIO_LAB_DEV_MODE=true
scenario-lab serve
```

**Warning:** Never use dev mode in production environments.

---

## Rate Limiting

The API implements sliding window rate limiting to prevent abuse and ensure fair resource usage.

### Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `SCENARIO_LAB_RATE_LIMIT_ENABLED` | `true` | Enable/disable rate limiting |
| `SCENARIO_LAB_RATE_LIMIT_REQUESTS` | `100` | Maximum requests per time window |
| `SCENARIO_LAB_RATE_LIMIT_WINDOW` | `60` | Time window in seconds |

### Rate Limit Headers

All responses include rate limit information in headers:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed per window |
| `X-RateLimit-Remaining` | Requests remaining in current window |
| `X-RateLimit-Reset` | Seconds until the rate limit resets |

### Client Identification

Clients are identified by:

1. **API Key** (preferred): If `X-API-Key` header is provided, the key is used for rate limit tracking
2. **IP Address** (fallback): If no API key, the client IP is used (respects `X-Forwarded-For` for proxied requests)

### Rate Limit Exceeded Response

**HTTP 429 Too Many Requests:**

```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds."
}
```

**Additional Headers:**

```
Retry-After: 45
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 45
```

### Excluded Endpoints

The following endpoints are excluded from rate limiting:

- `GET /` - Root endpoint
- `GET /api/health` - Health check
- `GET /docs`, `/redoc`, `/openapi.json` - Documentation endpoints

---

## API Endpoints

### Health & Status

#### GET /

Returns basic API information and available endpoints.

**Authentication:** Not required

**Response (200 OK):**

```json
{
  "name": "Scenario Lab API",
  "version": "2.0.0",
  "status": "running",
  "endpoints": {
    "scenarios": "/api/scenarios",
    "runs": "/api/runs",
    "docs": "/docs",
    "openapi": "/openapi.json"
  }
}
```

---

#### GET /api/health

Health check endpoint for monitoring and load balancer health probes. Returns current server status including database connectivity and configuration.

**Authentication:** Not required

**Rate Limiting:** Excluded

**Response (200 OK):**

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "connected",
  "running_scenarios": 2,
  "auth_enabled": true,
  "rate_limit_enabled": true,
  "dev_mode": false
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always `"healthy"` if endpoint responds |
| `version` | string | Scenario Lab version |
| `database` | string | `"connected"` or `"not configured"` |
| `running_scenarios` | integer | Count of currently executing scenarios |
| `auth_enabled` | boolean | Whether API key authentication is enabled |
| `rate_limit_enabled` | boolean | Whether rate limiting is active |
| `dev_mode` | boolean | Whether development mode is enabled |

---

### Scenario Execution

#### POST /api/scenarios/execute

Execute a scenario in the background. Returns immediately with a scenario ID that can be used to monitor progress via polling or WebSocket streaming.

**Authentication:** Required

**Request Body:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `scenario_path` | string | Yes | - | Path to scenario directory (relative or absolute) |
| `end_turn` | integer | No | null | Turn number to stop at (null = run to completion) |
| `credit_limit` | number | No | null | Maximum cost in USD before halting |
| `output_path` | string | No | null | Custom output directory path |
| `enable_database` | boolean | No | true | Enable database persistence for analytics |

**Request Example:**

```json
{
  "scenario_path": "scenarios/ai-summit",
  "end_turn": 10,
  "credit_limit": 5.0,
  "output_path": "output/my-experiment",
  "enable_database": true
}
```

**Response (200 OK):**

```json
{
  "scenario_id": "scenario-20251122-143256",
  "status": "initializing",
  "current_turn": 0,
  "total_cost": 0.0,
  "started_at": "2025-11-22T14:32:56.123456",
  "completed_at": null,
  "error": null,
  "waiting_for_human": null
}
```

**Error Response (404 Not Found):**

```json
{
  "detail": "Scenario not found: scenarios/invalid-path"
}
```

**Usage Notes:**

- The scenario executes asynchronously in a background task
- Use `GET /api/scenarios/{scenario_id}/status` to poll for status updates
- Use `WS /api/scenarios/{scenario_id}/stream` for real-time event streaming
- The `scenario_id` format is `scenario-YYYYMMDD-HHMMSS`

---

#### GET /api/scenarios/{scenario_id}/status

Retrieve the current status of a running or completed scenario. Use this endpoint to poll for status updates after starting a scenario.

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `scenario_id` | string | The scenario ID returned from `/api/scenarios/execute` |

**Response (200 OK) - Running:**

```json
{
  "scenario_id": "scenario-20251122-143256",
  "status": "running",
  "current_turn": 5,
  "total_cost": 2.45,
  "started_at": "2025-11-22T14:32:56.123456",
  "completed_at": null,
  "error": null,
  "waiting_for_human": null
}
```

**Response (200 OK) - Completed:**

```json
{
  "scenario_id": "scenario-20251122-143256",
  "status": "completed",
  "current_turn": 10,
  "total_cost": 4.87,
  "started_at": "2025-11-22T14:32:56.123456",
  "completed_at": "2025-11-22T14:45:23.456789",
  "error": null,
  "waiting_for_human": null
}
```

**Response (200 OK) - Halted (cost limit):**

```json
{
  "scenario_id": "scenario-20251122-143256",
  "status": "halted",
  "current_turn": 7,
  "total_cost": 5.02,
  "started_at": "2025-11-22T14:32:56.123456",
  "completed_at": "2025-11-22T14:40:12.789012",
  "error": "Credit limit exceeded: $5.02 > $5.00",
  "waiting_for_human": null
}
```

**Response (200 OK) - Waiting for Human Input:**

```json
{
  "scenario_id": "scenario-20251122-143256",
  "status": "running",
  "current_turn": 3,
  "total_cost": 1.23,
  "started_at": "2025-11-22T14:32:56.123456",
  "completed_at": null,
  "error": null,
  "waiting_for_human": "Policy Advisor"
}
```

**Response (200 OK) - Failed:**

```json
{
  "scenario_id": "scenario-20251122-143256",
  "status": "failed",
  "current_turn": 2,
  "total_cost": 0.89,
  "started_at": "2025-11-22T14:32:56.123456",
  "completed_at": "2025-11-22T14:35:45.123456",
  "error": "LLM API error: Rate limit exceeded",
  "waiting_for_human": null
}
```

**Status Values:**

| Status | Description |
|--------|-------------|
| `initializing` | Scenario is being set up (loading config, initializing actors) |
| `running` | Scenario is actively executing turns |
| `completed` | Scenario finished all turns successfully |
| `halted` | Scenario stopped due to cost limit, turn limit, or user action |
| `failed` | Scenario encountered an unrecoverable error |

**Error Response (404 Not Found):**

```json
{
  "detail": "Scenario not found: scenario-invalid-id"
}
```

---

### Scenario Control

#### POST /api/scenarios/{scenario_id}/pause

Pause a running scenario. The scenario will complete its current operation before pausing.

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `scenario_id` | string | The scenario ID to pause |

**Response (200 OK):**

```json
{
  "message": "Scenario paused",
  "scenario_id": "scenario-20251122-143256"
}
```

**Error Response (404 Not Found):**

```json
{
  "detail": "Scenario not found: scenario-invalid-id"
}
```

**Error Response (400 Bad Request):**

```json
{
  "detail": "Scenario not yet initialized"
}
```

---

#### POST /api/scenarios/{scenario_id}/resume

Resume a paused scenario from where it left off.

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `scenario_id` | string | The scenario ID to resume |

**Response (200 OK):**

```json
{
  "message": "Scenario resumed",
  "scenario_id": "scenario-20251122-143256"
}
```

**Error Response (404 Not Found):**

```json
{
  "detail": "Scenario not found: scenario-invalid-id"
}
```

---

#### POST /api/scenarios/{scenario_id}/human-decision

Submit a decision for a human-controlled actor. Use this when the scenario status shows `waiting_for_human` is not null.

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `scenario_id` | string | The scenario ID |

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `actor` | string | Yes | Name of the human-controlled actor |
| `long_term_goals` | array[string] | Yes | Updated long-term goals |
| `short_term_priorities` | array[string] | Yes | Current short-term priorities |
| `reasoning` | string | Yes | Reasoning behind the decision |
| `action` | string | Yes | The action to take |

**Request Example:**

```json
{
  "actor": "Policy Advisor",
  "long_term_goals": [
    "Establish robust AI governance framework",
    "Maintain international cooperation"
  ],
  "short_term_priorities": [
    "Address immediate safety concerns",
    "Build consensus among stakeholders"
  ],
  "reasoning": "Given the recent developments in AI capabilities, we need to prioritize safety measures while maintaining open dialogue with international partners.",
  "action": "Propose a temporary moratorium on frontier AI development until safety standards are established, while initiating bilateral discussions with major AI-developing nations."
}
```

**Response (200 OK):**

```json
{
  "message": "Decision received",
  "actor": "Policy Advisor",
  "scenario_id": "scenario-20251122-143256"
}
```

**Error Response (404 Not Found):**

```json
{
  "detail": "Scenario not found: scenario-invalid-id"
}
```

---

### Run Management

#### GET /api/runs

List all completed runs stored in the database. Supports filtering by scenario name.

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scenario` | string | No | Filter runs by scenario name |

**Response (200 OK):**

```json
[
  {
    "run_id": "run-20251122-143256",
    "scenario_name": "AI Summit",
    "status": "completed",
    "turns": 10,
    "total_cost": 4.32,
    "created": "2025-11-22T14:32:56.123456"
  },
  {
    "run_id": "run-20251121-091534",
    "scenario_name": "AI Summit",
    "status": "halted",
    "turns": 7,
    "total_cost": 3.21,
    "created": "2025-11-21T09:15:34.567890"
  },
  {
    "run_id": "run-20251120-162045",
    "scenario_name": "Trade Negotiation",
    "status": "completed",
    "turns": 15,
    "total_cost": 6.78,
    "created": "2025-11-20T16:20:45.234567"
  }
]
```

**Response (200 OK) - Filtered by scenario:**

Request: `GET /api/runs?scenario=AI%20Summit`

```json
[
  {
    "run_id": "run-20251122-143256",
    "scenario_name": "AI Summit",
    "status": "completed",
    "turns": 10,
    "total_cost": 4.32,
    "created": "2025-11-22T14:32:56.123456"
  },
  {
    "run_id": "run-20251121-091534",
    "scenario_name": "AI Summit",
    "status": "halted",
    "turns": 7,
    "total_cost": 3.21,
    "created": "2025-11-21T09:15:34.567890"
  }
]
```

**Response (200 OK) - Empty list:**

```json
[]
```

**Error Response (503 Service Unavailable):**

```json
{
  "detail": "Database not configured"
}
```

---

#### GET /api/runs/{run_id}

Get detailed information about a specific run including statistics.

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | string | The run ID to retrieve |

**Response (200 OK):**

```json
{
  "run_id": "run-20251122-143256",
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
  "cost_by_actor": {
    "US Representative": 1.45,
    "China Representative": 1.38,
    "EU Representative": 1.49
  },
  "metrics_summary": {
    "cooperation_level": {
      "final": 0.72,
      "min": 0.45,
      "max": 0.78,
      "trend": "increasing"
    },
    "tension_index": {
      "final": 0.35,
      "min": 0.28,
      "max": 0.62,
      "trend": "decreasing"
    }
  },
  "created": "2025-11-22T14:32:56.123456",
  "completed": "2025-11-22T14:45:23.456789"
}
```

**Error Response (404 Not Found):**

```json
{
  "detail": "Run not found: run-invalid-id"
}
```

**Error Response (503 Service Unavailable):**

```json
{
  "detail": "Database not configured"
}
```

---

#### GET /api/runs/{run_id}/statistics

Get comprehensive statistics for a run. Returns the same data as `GET /api/runs/{run_id}`.

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | string | The run ID to retrieve statistics for |

**Response (200 OK):**

See `GET /api/runs/{run_id}` response format.

---

### Analytics

#### POST /api/runs/compare

Compare multiple runs side by side. Useful for analyzing outcomes across different scenario variations or parameter settings.

**Authentication:** Required

**Request Body:**

Array of run IDs to compare (2-10 runs recommended).

```json
["run-20251122-143256", "run-20251121-091534", "run-20251120-162045"]
```

**Response (200 OK):**

```json
{
  "runs": [
    {
      "run_id": "run-20251122-143256",
      "scenario": "AI Summit",
      "status": "completed",
      "turns": 10,
      "total_cost": 4.32,
      "final_metrics": {
        "cooperation_level": 0.72,
        "tension_index": 0.35
      }
    },
    {
      "run_id": "run-20251121-091534",
      "scenario": "AI Summit",
      "status": "halted",
      "turns": 7,
      "total_cost": 3.21,
      "final_metrics": {
        "cooperation_level": 0.58,
        "tension_index": 0.48
      }
    },
    {
      "run_id": "run-20251120-162045",
      "scenario": "AI Summit",
      "status": "completed",
      "turns": 10,
      "total_cost": 4.87,
      "final_metrics": {
        "cooperation_level": 0.81,
        "tension_index": 0.22
      }
    }
  ],
  "comparison": {
    "cooperation_level": {
      "min": 0.58,
      "max": 0.81,
      "avg": 0.70,
      "std_dev": 0.12
    },
    "tension_index": {
      "min": 0.22,
      "max": 0.48,
      "avg": 0.35,
      "std_dev": 0.13
    },
    "total_cost": {
      "min": 3.21,
      "max": 4.87,
      "avg": 4.13
    }
  }
}
```

**Error Response (503 Service Unavailable):**

```json
{
  "detail": "Database not configured"
}
```

---

#### GET /api/metrics/{metric_name}/aggregate

Aggregate a specific metric across all runs, optionally filtered by scenario.

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `metric_name` | string | Name of the metric to aggregate |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scenario` | string | No | Filter by scenario name |

**Response (200 OK):**

```json
{
  "metric": "cooperation_level",
  "min": 0.30,
  "max": 0.92,
  "avg": 0.65,
  "std_dev": 0.18,
  "count": 45,
  "scenario": null
}
```

**Response (200 OK) - Filtered by scenario:**

Request: `GET /api/metrics/cooperation_level/aggregate?scenario=AI%20Summit`

```json
{
  "metric": "cooperation_level",
  "min": 0.45,
  "max": 0.81,
  "avg": 0.68,
  "std_dev": 0.12,
  "count": 15,
  "scenario": "AI Summit"
}
```

**Error Response (503 Service Unavailable):**

```json
{
  "detail": "Database not configured"
}
```

---

## WebSocket Protocol

The WebSocket endpoint provides real-time streaming of scenario events during execution. This is more efficient than polling for long-running scenarios.

### Connection

**Endpoint:** `ws://localhost:8000/api/scenarios/{scenario_id}/stream`

**Authentication:** WebSocket connections do not currently require API key authentication.

### Connection Flow

1. **Start Scenario:** First, call `POST /api/scenarios/execute` to start a scenario
2. **Connect WebSocket:** Open a WebSocket connection to the stream endpoint
3. **Receive Events:** The server pushes events as they occur
4. **Handle Completion:** When scenario finishes, a `scenario_finished` event is sent and the connection closes

### Message Format

All messages are JSON objects with the following structure:

```json
{
  "type": "event_type",
  "data": { ... },
  "timestamp": "2025-11-22T14:32:56.789123"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Event type identifier |
| `data` | object | Event-specific payload |
| `timestamp` | string | ISO 8601 timestamp of when the event occurred |

### Event Types

#### turn_started

Emitted when a new turn begins.

```json
{
  "type": "turn_started",
  "data": {
    "turn": 5,
    "turn_duration": "3 months"
  },
  "timestamp": "2025-11-22T14:35:12.123456"
}
```

#### turn_completed

Emitted when a turn finishes, including cost information.

```json
{
  "type": "turn_completed",
  "data": {
    "turn": 5,
    "turn_cost": 0.47,
    "total_cost": 2.35,
    "world_state_summary": "Negotiations continue with moderate progress..."
  },
  "timestamp": "2025-11-22T14:36:45.234567"
}
```

#### phase_started

Emitted when a phase within a turn begins.

```json
{
  "type": "phase_started",
  "data": {
    "turn": 5,
    "phase": "decision",
    "actors": ["US Representative", "China Representative", "EU Representative"]
  },
  "timestamp": "2025-11-22T14:35:15.345678"
}
```

#### phase_completed

Emitted when a phase within a turn finishes.

```json
{
  "type": "phase_completed",
  "data": {
    "turn": 5,
    "phase": "decision",
    "phase_cost": 0.32,
    "decisions_made": 3
  },
  "timestamp": "2025-11-22T14:36:02.456789"
}
```

#### actor_decision

Emitted when an actor makes a decision.

```json
{
  "type": "actor_decision",
  "data": {
    "turn": 5,
    "actor": "US Representative",
    "action_summary": "Proposed bilateral safety framework agreement",
    "cost": 0.11
  },
  "timestamp": "2025-11-22T14:35:45.567890"
}
```

#### communication_sent

Emitted when an actor sends a communication.

```json
{
  "type": "communication_sent",
  "data": {
    "turn": 5,
    "from_actor": "EU Representative",
    "to_actor": "China Representative",
    "type": "bilateral",
    "summary": "Invitation to joint working group"
  },
  "timestamp": "2025-11-22T14:35:30.678901"
}
```

#### world_state_updated

Emitted when the world state is synthesized after all decisions.

```json
{
  "type": "world_state_updated",
  "data": {
    "turn": 5,
    "summary": "International tensions ease as bilateral talks show progress...",
    "key_changes": [
      "US-China safety framework proposed",
      "EU initiates joint working group",
      "Global AI governance momentum builds"
    ]
  },
  "timestamp": "2025-11-22T14:36:30.789012"
}
```

#### metrics_extracted

Emitted when metrics are extracted from the turn.

```json
{
  "type": "metrics_extracted",
  "data": {
    "turn": 5,
    "metrics": {
      "cooperation_level": 0.68,
      "tension_index": 0.42,
      "progress_score": 0.55
    }
  },
  "timestamp": "2025-11-22T14:36:40.890123"
}
```

#### validation_completed

Emitted when QA validation completes for a turn.

```json
{
  "type": "validation_completed",
  "data": {
    "turn": 5,
    "issues_found": 1,
    "severity": "low",
    "summary": "Minor consistency note: Actor referenced event before it occurred"
  },
  "timestamp": "2025-11-22T14:36:42.901234"
}
```

#### credit_limit_warning

Emitted when cost approaches the credit limit (80% threshold).

```json
{
  "type": "credit_limit_warning",
  "data": {
    "current_cost": 4.12,
    "credit_limit": 5.00,
    "percentage_used": 82.4
  },
  "timestamp": "2025-11-22T14:40:15.012345"
}
```

#### human_input_required

Emitted when the scenario is waiting for human actor input.

```json
{
  "type": "human_input_required",
  "data": {
    "turn": 6,
    "actor": "Policy Advisor",
    "context": "Review the proposed safety framework and decide on response",
    "deadline": null
  },
  "timestamp": "2025-11-22T14:41:00.123456"
}
```

#### scenario_halted

Emitted when the scenario is stopped before completion.

```json
{
  "type": "scenario_halted",
  "data": {
    "reason": "credit_limit_exceeded",
    "message": "Credit limit exceeded: $5.02 > $5.00",
    "final_turn": 7,
    "total_cost": 5.02,
    "can_resume": true
  },
  "timestamp": "2025-11-22T14:42:30.234567"
}
```

#### scenario_finished

Emitted when the scenario completes (success, halt, or failure). This is always the final event.

```json
{
  "type": "scenario_finished",
  "data": {
    "status": "completed",
    "final_turn": 10,
    "total_cost": 4.87,
    "run_id": "run-20251122-143256"
  },
  "timestamp": "2025-11-22T14:45:23.345678"
}
```

#### error

Emitted when an error occurs during execution.

```json
{
  "type": "error",
  "data": {
    "error": "LLM API error",
    "message": "Rate limit exceeded. Retrying in 30 seconds...",
    "recoverable": true
  },
  "timestamp": "2025-11-22T14:38:15.456789"
}
```

### Connection Errors

If the scenario doesn't exist or times out during initialization:

```json
{
  "error": "Scenario not found or timeout"
}
```

If the runner fails to initialize:

```json
{
  "error": "Runner initialization timeout"
}
```

### Client Implementation

#### JavaScript/TypeScript Example

```javascript
const scenarioId = "scenario-20251122-143256";
const ws = new WebSocket(`ws://localhost:8000/api/scenarios/${scenarioId}/stream`);

ws.onopen = () => {
  console.log("Connected to scenario stream");
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case "turn_started":
      console.log(`Turn ${message.data.turn} started`);
      break;
    case "turn_completed":
      console.log(`Turn ${message.data.turn} completed, cost: $${message.data.total_cost.toFixed(2)}`);
      break;
    case "actor_decision":
      console.log(`${message.data.actor}: ${message.data.action_summary}`);
      break;
    case "scenario_finished":
      console.log(`Scenario ${message.data.status}: ${message.data.final_turn} turns, $${message.data.total_cost.toFixed(2)}`);
      ws.close();
      break;
    case "error":
      if (!message.data.recoverable) {
        console.error(`Fatal error: ${message.data.message}`);
        ws.close();
      }
      break;
  }
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("Disconnected from scenario stream");
};
```

#### Python Example

```python
import asyncio
import websockets
import json

async def stream_scenario(scenario_id: str):
    uri = f"ws://localhost:8000/api/scenarios/{scenario_id}/stream"

    async with websockets.connect(uri) as websocket:
        print(f"Connected to scenario stream: {scenario_id}")

        async for message in websocket:
            event = json.loads(message)
            event_type = event["type"]
            data = event["data"]

            if event_type == "turn_started":
                print(f"Turn {data['turn']} started")
            elif event_type == "turn_completed":
                print(f"Turn {data['turn']} completed, cost: ${data['total_cost']:.2f}")
            elif event_type == "actor_decision":
                print(f"{data['actor']}: {data['action_summary']}")
            elif event_type == "scenario_finished":
                print(f"Scenario {data['status']}: {data['final_turn']} turns, ${data['total_cost']:.2f}")
                break
            elif event_type == "error" and not data.get("recoverable"):
                print(f"Fatal error: {data['message']}")
                break

# Usage
asyncio.run(stream_scenario("scenario-20251122-143256"))
```

### Best Practices

1. **Always handle `scenario_finished`**: This event signals the end of the stream
2. **Handle reconnection**: If disconnected unexpectedly, use status polling as fallback
3. **Process events asynchronously**: Don't block on event processing
4. **Implement error recovery**: Check `recoverable` flag on error events
5. **Set connection timeout**: The server waits 30 seconds for scenario initialization

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid request body or parameters |
| 401 | Unauthorized | Missing or invalid API key |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Database not configured or unavailable |

### Error Response Format

All error responses follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

### Common Errors

**Scenario not found:**

```json
{
  "detail": "Scenario not found: scenarios/invalid-path"
}
```

**Run not found:**

```json
{
  "detail": "Run not found: run-invalid-id"
}
```

**Database not configured:**

```json
{
  "detail": "Database not configured"
}
```

**Authentication failed:**

```json
{
  "detail": "Missing API key. Provide X-API-Key header."
}
```

**Rate limit exceeded:**

```json
{
  "detail": "Rate limit exceeded. Try again in 45 seconds."
}
```

---

## Python Client

A Python client library is available for easy API access:

```python
from examples.api_client import ScenarioLabClient

async def main():
    client = ScenarioLabClient(
        base_url="http://localhost:8000",
        api_key="your-api-key"  # Optional if auth disabled
    )

    # Execute scenario
    result = await client.execute_scenario(
        scenario_path="scenarios/ai-summit",
        end_turn=10,
        credit_limit=5.0
    )
    scenario_id = result["scenario_id"]
    print(f"Started scenario: {scenario_id}")

    # Poll for status
    while True:
        status = await client.get_status(scenario_id)
        print(f"Status: {status['status']}, Turn: {status['current_turn']}")

        if status["status"] in ["completed", "halted", "failed"]:
            break

        await asyncio.sleep(2)

    # Or stream events
    async for event in client.stream_scenario(scenario_id):
        print(f"Event: {event['type']} - {event['data']}")

    # Query analytics
    runs = await client.list_runs()
    if runs:
        stats = await client.get_run_statistics(runs[0]["run_id"])
        print(f"Run statistics: {stats}")

asyncio.run(main())
```

### Command-Line Examples

```bash
# Execute and poll for status
python examples/api_client.py poll

# Execute and stream events
python examples/api_client.py stream

# Query run analytics
python examples/api_client.py analytics
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SCENARIO_LAB_API_KEY` | (none) | Comma-separated API keys for authentication |
| `SCENARIO_LAB_AUTH_ENABLED` | auto | Enable authentication (auto-enabled if keys set) |
| `SCENARIO_LAB_DEV_MODE` | `false` | Development mode (bypasses auth/rate limits) |
| `SCENARIO_LAB_RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `SCENARIO_LAB_RATE_LIMIT_REQUESTS` | `100` | Max requests per window |
| `SCENARIO_LAB_RATE_LIMIT_WINDOW` | `60` | Rate limit window in seconds |
| `SCENARIO_LAB_CORS_ORIGINS` | localhost only | Comma-separated allowed CORS origins |
| `DATABASE_URL` | `sqlite:///scenario-lab.db` | Database connection URL |

### CORS Configuration

By default, only localhost origins are allowed for security. For production:

```bash
export SCENARIO_LAB_CORS_ORIGINS="https://app.example.com,https://admin.example.com"
```

### Production Checklist

1. **Set API keys:** `export SCENARIO_LAB_API_KEY="key1,key2,key3"`
2. **Disable dev mode:** Ensure `SCENARIO_LAB_DEV_MODE` is not set or is `false`
3. **Configure CORS:** Set appropriate origins for your frontend
4. **Use HTTPS:** Deploy behind a reverse proxy with TLS
5. **Configure database:** Use PostgreSQL for production workloads
6. **Set rate limits:** Adjust based on expected load

### Database Requirements

The API requires database support for run persistence and analytics:

```bash
# SQLite (default, good for development)
# Database created automatically at ./scenario-lab.db

# PostgreSQL (recommended for production)
export DATABASE_URL="postgresql://user:pass@localhost:5432/scenario_lab"
```

---

## Development

### Start with Auto-Reload

```bash
scenario-lab serve --reload
```

API changes will automatically restart the server.

### Testing the API

```bash
# Health check
curl http://localhost:8000/api/health

# Execute scenario (dev mode, no auth)
curl -X POST http://localhost:8000/api/scenarios/execute \
  -H "Content-Type: application/json" \
  -d '{"scenario_path": "scenarios/ai-summit", "end_turn": 3}'

# Check status
curl http://localhost:8000/api/scenarios/scenario-20251122-143256/status

# List runs
curl http://localhost:8000/api/runs
```

### Debugging

Enable debug logging:

```bash
export SCENARIO_LAB_LOG_LEVEL=DEBUG
scenario-lab serve
```
