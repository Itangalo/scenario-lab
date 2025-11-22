# Global State Patterns in Scenario Lab

> **Purpose**: This document describes all global state patterns used in the codebase, their thread-safety characteristics, and implications for parallel batch execution.

---

## Overview

Scenario Lab uses several global state patterns for performance optimization and resource sharing. Understanding these patterns is critical when running parallel batch executions or developing new features.

### Thread-Safety Summary

| Component | Global Variable | Thread-Safe | Process-Safe | Notes |
|-----------|----------------|-------------|--------------|-------|
| Response Cache | `_global_cache` | No | No | Use run-scoped caching |
| HTTP Session | `_http_session` | Yes* | No | requests.Session is thread-safe |
| Event Bus | `_global_bus` | No | No | Create per-run instances |
| Memory Monitor | `_global_memory_monitor` | Yes | Yes | Read-only after init |
| API Settings | `_settings` | Yes | Yes | Read-only after init |
| Rate Limiter | `_rate_limiter` | No | No | Use per-request locking |
| Model Pricing Cache | `_dynamic_pricing_cache` | No | No | Read-after-write race |
| API Running Scenarios | `running_scenarios` | No | No | Single API instance only |

\* Thread-safe for making requests, but not for initialization race conditions.

---

## Detailed Analysis

### 1. Response Cache (`scenario_lab/utils/response_cache.py`)

**Global Variable**: `_global_cache: Optional[ResponseCache]`

**Purpose**: Caches LLM responses to reduce costs and improve performance.

**Thread-Safety**: **NOT THREAD-SAFE**

The `ResponseCache` class uses a regular Python dictionary for in-memory storage, which is not thread-safe for concurrent writes.

```python
# Location: scenario_lab/utils/response_cache.py:339-373
_global_cache: Optional[ResponseCache] = None

def get_global_cache() -> ResponseCache:
    global _global_cache
    if _global_cache is None:
        # Race condition: multiple threads may create instances
        _global_cache = ResponseCache(...)
    return _global_cache
```

**Risks**:

- Race condition during initialization
- Concurrent cache updates may cause data corruption
- Memory cache dictionary is not thread-safe

**Mitigation for Parallel Execution**:

1. **Use run-scoped caching**: Set `SCENARIO_RUN_ID` environment variable to isolate cache per run
2. **Disable caching**: Set `SCENARIO_CACHE_ENABLED=false` for parallel batch runs
3. **Use disk-only caching**: File-based caching with proper locking (future enhancement)

**Recommendation**: For parallel batch execution, disable caching or use separate processes (multiprocessing) instead of threads.

---

### 2. HTTP Session (`scenario_lab/utils/api_client.py`)

**Global Variable**: `_http_session: Optional[requests.Session]`

**Purpose**: Connection pooling for HTTP requests to improve performance.

**Thread-Safety**: **PARTIALLY THREAD-SAFE**

The `requests.Session` object is thread-safe for making concurrent requests, but initialization has a race condition.

```python
# Location: scenario_lab/utils/api_client.py:28-65
_http_session: Optional[requests.Session] = None

def get_http_session() -> requests.Session:
    global _http_session
    if _http_session is None:
        # Race condition: multiple threads may create sessions
        _http_session = requests.Session()
        # Configure adapters...
    return _http_session
```

**Risks**:

- Initialization race condition (minor - worst case creates extra session)
- Session state (cookies, headers) is shared across threads

**Mitigation**:

1. Initialize the session before starting parallel execution
2. For batch runs, each process should have its own session

**Recommendation**: Safe to use with threads for API calls, but ensure initialization happens before parallel execution starts.

---

### 3. Event Bus (`scenario_lab/core/events.py`)

**Global Variable**: `_global_bus: Optional[EventBus]`

**Purpose**: Publish-subscribe pattern for component communication and observability.

**Thread-Safety**: **NOT THREAD-SAFE**

The `EventBus` uses regular Python dictionaries for handler registration and lists for event history.

```python
# Location: scenario_lab/core/events.py:274-304
_global_bus: Optional[EventBus] = None

def get_event_bus(create_if_missing: bool = True) -> EventBus:
    global _global_bus
    if _global_bus is None and create_if_missing:
        _global_bus = EventBus(keep_history=False)
    return _global_bus
```

**Risks**:

- Concurrent handler registration/removal may cause issues
- Event emission to multiple handlers is async but handler list modification is not safe
- Event history (if enabled) is not thread-safe

**Mitigation**:

1. Create separate `EventBus` instances per run for parallel batch execution
2. Use `set_event_bus()` to install a run-specific bus before execution
3. Avoid modifying handlers during execution

**Recommendation**: For parallel execution, use `set_event_bus(EventBus())` to create isolated buses per run.

---

### 4. Memory Monitor (`scenario_lab/utils/memory_optimizer.py`)

**Global Variable**: `_global_memory_monitor: Optional[MemoryMonitor]`

**Purpose**: Monitor memory usage and warn about potential OOM conditions.

**Thread-Safety**: **THREAD-SAFE** (effectively read-only)

The `MemoryMonitor` only reads system memory statistics via `psutil` and doesn't maintain significant mutable state.

```python
# Location: scenario_lab/utils/memory_optimizer.py:363-373
_global_memory_monitor = None

def get_memory_monitor() -> MemoryMonitor:
    global _global_memory_monitor
    if _global_memory_monitor is None:
        _global_memory_monitor = MemoryMonitor()
    return _global_memory_monitor
```

**Risks**:

- Minor: `warnings_shown` set may have race conditions, but consequences are minimal (duplicate warnings)

**Recommendation**: Safe to use in parallel execution. Duplicate warnings are acceptable.

---

### 5. API Settings (`scenario_lab/api/settings.py`)

**Global Variable**: `_settings: Optional[APISettings]`

**Purpose**: Load and cache API configuration from environment variables.

**Thread-Safety**: **THREAD-SAFE** (read-only after initialization)

Settings are loaded once from environment variables and never modified.

```python
# Location: scenario_lab/api/settings.py:135-157
_settings: Optional[APISettings] = None

def get_settings() -> APISettings:
    global _settings
    if _settings is None:
        _settings = APISettings.from_env()
    return _settings
```

**Risks**:

- Initialization race condition (minor - both threads would create identical settings)

**Recommendation**: Safe to use in parallel execution. Consider calling `get_settings()` during startup to avoid race.

---

### 6. Rate Limiter (`scenario_lab/api/rate_limit.py`)

**Global Variable**: `_rate_limiter: Optional[RateLimiter]`

**Purpose**: Track and enforce API rate limits per client.

**Thread-Safety**: **NOT THREAD-SAFE**

The `RateLimiter` uses `defaultdict` and modifies timestamp lists during rate checking.

```python
# Location: scenario_lab/api/rate_limit.py:131-153
_rate_limiter: Optional[RateLimiter] = None

def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
```

**Risks**:

- Concurrent rate limit checks may miss requests (under-counting)
- Timestamp list modifications are not atomic

**Context**: This is only used by the API server, which typically runs in a single process with async handlers (not true parallelism).

**Recommendation**: For multi-worker API deployments, use external rate limiting (Redis, etc.) instead of in-memory tracking.

---

### 7. Model Pricing Cache (`scenario_lab/utils/model_pricing.py`)

**Global Variables**: `_dynamic_pricing_cache: Dict`, `_cache_loaded: bool`

**Purpose**: Cache dynamically fetched pricing data from OpenRouter API.

**Thread-Safety**: **NOT THREAD-SAFE**

```python
# Location: scenario_lab/utils/model_pricing.py:48-49, 62
_dynamic_pricing_cache: Dict[str, Tuple[float, float]] = {}
_cache_loaded: bool = False

def fetch_openrouter_models(...):
    global _dynamic_pricing_cache, _cache_loaded
    if _cache_loaded:
        return _dynamic_pricing_cache
    # Fetch and populate cache...
```

**Risks**:

- Race condition: multiple threads may fetch pricing simultaneously
- Read-after-write race on `_cache_loaded` flag

**Mitigation**:

1. Call `fetch_openrouter_models()` during startup before parallel execution
2. Accept potential duplicate API calls (wasteful but not harmful)

**Recommendation**: Pre-warm the cache before parallel execution to avoid duplicate API calls.

---

### 8. API Application State (`scenario_lab/api/app.py`)

**Global Variables**: `running_scenarios: Dict`, `database: Optional[Database]`

**Purpose**: Track running scenario instances and database connection.

**Thread-Safety**: **NOT THREAD-SAFE**

```python
# Location: scenario_lab/api/app.py:50-51
running_scenarios: Dict[str, Dict[str, Any]] = {}
database: Optional[Database] = None
```

**Risks**:

- Concurrent scenario status updates may cause race conditions
- Not designed for multi-process API deployment

**Context**: The API server uses FastAPI with async handlers, which run in a single thread per process. This is safe for single-process deployments.

**Recommendation**: For production deployments with multiple workers, use external state storage (Redis, database) for scenario tracking.

---

## Recommendations for Parallel Batch Execution

### Using Multiprocessing (Recommended)

For parallel batch runs, use **multiprocessing** instead of threading:

```python
from multiprocessing import Pool

def run_scenario(scenario_config):
    # Each process gets its own globals
    runner = SyncRunner(scenario_config)
    return runner.run()

with Pool(processes=4) as pool:
    results = pool.map(run_scenario, scenario_configs)
```

Benefits:

- Each process has isolated global state
- No thread-safety concerns
- Better CPU utilization for compute-bound tasks

### Using Threading (Caution Required)

If using threading, take these precautions:

1. **Disable response caching** or use run-scoped caches
2. **Create per-run EventBus instances** using `set_event_bus()`
3. **Pre-initialize globals** before starting threads
4. **Use asyncio** for concurrent LLM calls within a single run

```python
import asyncio

async def run_parallel():
    # Reset globals for clean state
    reset_global_cache()

    # Pre-initialize shared resources
    get_http_session()
    fetch_openrouter_models()

    # Run scenarios concurrently with asyncio (single thread, event loop)
    tasks = [run_scenario_async(config) for config in configs]
    results = await asyncio.gather(*tasks)
```

### Current Batch Runner Implementation

The current `BatchParallelExecutor` (`scenario_lab/batch/batch_parallel_executor.py`) uses asyncio for concurrency, which runs in a single thread and avoids most thread-safety issues. This is the recommended approach for parallel batch execution.

---

## Future Improvements

1. **Thread-Safe Response Cache**: Implement locking or use `threading.local()` for per-thread caches
2. **Proper Singleton Pattern**: Use `threading.Lock` for initialization guards
3. **External State Storage**: Support Redis/database for distributed deployments
4. **Process-Isolated Caching**: Implement shared-nothing architecture for multiprocessing

---

## Testing Concurrent Access

See `tests/test_concurrent_access.py` for tests that verify behavior under concurrent access conditions.

---

*Last updated: 2025-11-22*
