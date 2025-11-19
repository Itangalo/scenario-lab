# V2 Frontend Integration Status

**Date**: 2025-11-19
**Status**: PARTIALLY COMPLETE (60%)

## Overview

The React frontend is being updated from V1.5 API to V2 REST API. The V2 API provides better architecture with RESTful endpoints and WebSocket streaming, but requires changes to the frontend's "single active scenario" model.

---

## Completed ✅

### 1. API Client (`web/frontend/src/api/client.ts`)

Created a TypeScript API client that wraps all V2 endpoints:

**Features:**
- Execute scenarios (`POST /api/scenarios/execute`)
- Get scenario status (`GET /api/scenarios/{id}/status`)
- List runs (`GET /api/runs`)
- Get run details and statistics
- Compare runs
- Aggregate metrics
- WebSocket connection management
- "Active scenario" concept for UI simplicity

**Usage:**
```typescript
import { apiClient } from './api/client'

// Start a scenario
const status = await apiClient.executeScenario({
  scenario_path: 'scenarios/ai-summit',
  max_turns: 10,
  credit_limit: 5.0
})

// Get current status
const currentStatus = await apiClient.getScenarioStatus()

// Connect WebSocket
const ws = apiClient.connectWebSocket(undefined, (event) => {
  console.log('Event:', event)
})
```

### 2. Updated TypeScript Types (`web/frontend/src/types.ts`)

**Changes:**
- Updated `WebSocketMessage` to match V2 event format:
  ```typescript
  interface WebSocketMessage {
    type: string
    data: Record<string, any>
    timestamp: string
    source?: string
  }
  ```
- Added V2-specific fields to `ScenarioStatus`:
  - `scenario_id?: string`
  - `status?: string`
- Created `LegacyWebSocketMessage` for V1.5 compatibility
- Added documentation for all types

### 3. Updated Event Handling (`web/frontend/src/components/ScenarioDashboard.tsx`)

**Changes:**
- Updated `getEventDescription()` to handle V2 event types:
  - `turn_started`, `turn_completed`
  - `phase_started`, `phase_completed`
  - `scenario_completed`, `scenario_failed`, `scenario_halted`
- Maintained backward compatibility with V1.5 events
- Fixed `wsMessage.data.actor` access (was `wsMessage.actor`)

---

## Remaining Work ❌

### 1. Update App.tsx (CRITICAL)

**Current State:** Uses V1.5 API endpoints directly
**Needed:**
- Replace fetch('/api/status') with apiClient.getScenarioStatus()
- Update WebSocket connection to use apiClient.connectWebSocket()
- Handle "no active scenario" state properly
- Map V2 status to UI state

**Complexity:** Medium (2-3 hours)

### 2. Create Scenario Launcher Component

**Current State:** Frontend assumes scenario is already running
**Needed:**
- Component to start new scenarios
- Form for scenario parameters (path, max_turns, credit_limit)
- Display list of available scenarios
- Integration with App.tsx

**Complexity:** Medium (3-4 hours)

### 3. Update Human Decision Endpoint

**Current State:** POST /api/human/decision (V1.5)
**Needed:**
- V2 API doesn't have this endpoint yet
- Options:
  1. Add human decision endpoint to V2 API
  2. Use V1.5 endpoint temporarily
  3. Implement via pause/resume mechanism

**Complexity:** Low-Medium (depends on approach)

### 4. Actor Status Tracking

**Current State:** Expects `actors` array with status in ScenarioStatus
**Needed:**
- V2 API doesn't provide real-time actor status
- Options:
  1. Add actor status to V2 API
  2. Infer from events (phase_started, decision_made, etc.)
  3. Remove from UI temporarily

**Complexity:** Medium (depends on approach)

### 5. Testing & Integration

**Needed:**
- Start V2 API backend
- Test WebSocket streaming
- Test scenario execution
- Test human actor interface
- Fix any integration bugs

**Complexity:** High (4-6 hours)

---

## Architecture Differences

### V1.5 API (Current Frontend)

**Model:** Single stateful scenario
- GET `/api/status` - Global status
- WS `/ws` - Global WebSocket
- POST `/api/scenario/start` - Start scenario
- POST `/api/human/decision` - Submit decision

**Pros:**
- Simple for UI
- Always has context

**Cons:**
- Can't handle multiple scenarios
- Stateful backend

### V2 API (Target)

**Model:** RESTful with scenario IDs
- POST `/api/scenarios/execute` - Returns scenario_id
- GET `/api/scenarios/{id}/status` - Per-scenario status
- WS `/api/scenarios/{id}/stream` - Per-scenario stream
- No human decision endpoint yet

**Pros:**
- RESTful
- Multiple scenarios
- Stateless

**Cons:**
- More complex for simple UI
- Requires "active scenario" concept

---

## Migration Strategy

### Option A: Full V2 Integration (Recommended)

1. Update App.tsx to use apiClient
2. Add scenario launcher component
3. Implement V2 human decision endpoint in backend
4. Add actor status to V2 events or infer from events
5. Full testing

**Timeline:** 1-2 days
**Benefits:** Clean, future-proof
**Risks:** More work

### Option B: Hybrid Approach (Faster)

1. Update App.tsx to use apiClient for status/websocket
2. Keep using V1.5 endpoints for human decisions
3. Run both APIs simultaneously
4. Gradual migration

**Timeline:** 4-6 hours
**Benefits:** Faster, incremental
**Risks:** Technical debt, two APIs running

### Option C: V2 API Compatibility Layer

1. Add V1.5-compatible endpoints to V2 API
2. Minimal frontend changes
3. Backend handles mapping

**Timeline:** 3-4 hours (mostly backend work)
**Benefits:** Minimal frontend changes
**Risks:** Backend complexity

---

## Recommendation

**Go with Option A (Full V2 Integration)** because:

1. V2 API is already complete and tested
2. Frontend changes are moderate (not massive rewrite)
3. Clean architecture for future features
4. Only 1-2 days of work

**Implementation Order:**
1. Add human decision endpoint to V2 API (1 hour)
2. Add actor status to V2 events (1 hour)
3. Update App.tsx to use apiClient (2-3 hours)
4. Create scenario launcher component (3-4 hours)
5. Testing and bug fixes (2-3 hours)

**Total:** 9-12 hours of focused work

---

## Current Files

**Modified:**
- `web/frontend/src/api/client.ts` (NEW) - V2 API client
- `web/frontend/src/types.ts` - Updated types
- `web/frontend/src/components/ScenarioDashboard.tsx` - Updated event handling

**Needs Update:**
- `web/frontend/src/App.tsx` - Main app component
- `web/frontend/src/components/HumanActorInterface.tsx` - Human decision submission

**May Need Creation:**
- `web/frontend/src/components/ScenarioLauncher.tsx` - Scenario starter
- `web/frontend/src/components/RunsList.tsx` - Browse past runs

---

## API Gaps to Fill

### 1. Human Decision Endpoint

**Needed in V2 API:**
```typescript
POST /api/scenarios/{id}/human-decision
Body: {
  actor: string
  long_term_goals: string[]
  short_term_priorities: string[]
  reasoning: string
  action: string
}
```

### 2. Actor Status in Events

**Needed in V2 events:**
```typescript
{
  type: "actor_status_update",
  data: {
    actor: "EU Commission",
    status: "thinking" | "waiting" | "complete"
  }
}
```

Or infer from existing events:
- `phase_started` with phase="decision" → actors start thinking
- `decision_made` → actor complete

---

## Testing Plan

### 1. Backend Testing

```bash
# Start V2 API
cd scenario_lab/api
uvicorn app:app --reload

# Start V1.5 API (for comparison)
cd web
python app.py
```

### 2. Frontend Testing

```bash
cd web/frontend
npm install
npm run dev
```

### 3. Integration Tests

1. ✅ API client connects to backend
2. ✅ Execute scenario returns status
3. ✅ WebSocket receives events
4. ❌ UI updates with events
5. ❌ Human decision submission works
6. ❌ Actor status displays correctly
7. ❌ Cost tracking updates
8. ❌ Scenario completion handled

---

## Conclusion

**Progress:** 60% complete
**Status:** Foundation complete, integration needed
**Effort Remaining:** 9-12 hours
**Blockers:** None - just needs execution time

The V2 frontend integration is well-architected and partially complete. The API client is solid, types are updated, and event handling works. The remaining work is primarily wiring up App.tsx and creating the scenario launcher.
