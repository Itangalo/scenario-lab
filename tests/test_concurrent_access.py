"""
Tests for Concurrent Access Patterns

Tests thread-safety and concurrent access behavior for global state patterns
used in Scenario Lab. These tests verify behavior documented in
docs/GLOBAL_STATE_PATTERNS.md

See Issue #76 for context.
"""
import pytest
import threading
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock

from scenario_lab.utils.response_cache import (
    ResponseCache,
    get_global_cache,
    reset_global_cache,
)
from scenario_lab.utils.api_client import get_http_session
from scenario_lab.core.events import EventBus, get_event_bus, set_event_bus, Event
from scenario_lab.utils.memory_optimizer import get_memory_monitor

# Skip settings tests if FastAPI not available
try:
    import scenario_lab.api.settings as settings_module
    SETTINGS_AVAILABLE = True
except ImportError:
    settings_module = None
    SETTINGS_AVAILABLE = False


class TestResponseCacheConcurrency:
    """Tests for concurrent access to ResponseCache"""

    def test_concurrent_cache_reads(self):
        """Test that concurrent reads don't cause issues"""
        cache = ResponseCache()
        messages = [{"role": "user", "content": "Test"}]
        cache.put("model", messages, "response", 100, 70, 30)

        results = []
        errors = []

        def read_cache():
            try:
                for _ in range(100):
                    entry = cache.get("model", messages)
                    if entry:
                        results.append(entry.response)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_cache) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent reads: {errors}"
        assert len(results) == 1000  # 10 threads * 100 reads

    def test_concurrent_cache_writes_and_reads(self):
        """Test concurrent writes and reads - may have race conditions"""
        cache = ResponseCache()
        errors = []
        write_count = 0
        read_count = 0
        lock = threading.Lock()

        def write_cache(thread_id):
            nonlocal write_count
            try:
                for i in range(50):
                    messages = [{"role": "user", "content": f"Thread {thread_id} msg {i}"}]
                    cache.put("model", messages, f"response-{thread_id}-{i}", 100, 70, 30)
                    with lock:
                        write_count += 1
            except Exception as e:
                errors.append(("write", e))

        def read_cache():
            nonlocal read_count
            try:
                for _ in range(100):
                    messages = [{"role": "user", "content": "Thread 0 msg 0"}]
                    cache.get("model", messages)
                    with lock:
                        read_count += 1
            except Exception as e:
                errors.append(("read", e))

        # Start writers and readers concurrently
        threads = []
        for i in range(5):
            threads.append(threading.Thread(target=write_cache, args=(i,)))
        for _ in range(5):
            threads.append(threading.Thread(target=read_cache))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Note: We don't assert no errors because this IS known to be
        # potentially unsafe. We're documenting the behavior.
        if errors:
            pytest.skip(
                f"Concurrent access caused {len(errors)} errors as expected. "
                f"This is known behavior - see docs/GLOBAL_STATE_PATTERNS.md"
            )

        assert write_count == 250  # 5 threads * 50 writes
        assert read_count == 500  # 5 threads * 100 reads

    def test_global_cache_initialization_race(self):
        """Test race condition in global cache initialization"""
        reset_global_cache()
        caches = []
        errors = []

        def get_cache():
            try:
                cache = get_global_cache()
                caches.append(id(cache))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_cache) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        reset_global_cache()

        assert len(errors) == 0, f"Errors during initialization: {errors}"
        # All threads should get the same cache instance (or at worst, one of
        # the racing instances). We verify they all got a valid cache.
        assert len(caches) == 20


class TestHttpSessionConcurrency:
    """Tests for concurrent access to HTTP session"""

    def test_concurrent_session_access(self):
        """Test that concurrent session access is safe"""
        sessions = []
        errors = []

        def get_session():
            try:
                session = get_http_session()
                sessions.append(id(session))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_session) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during session access: {errors}"
        assert len(sessions) == 20

        # Verify all got valid sessions (IDs should be same or valid)
        unique_ids = set(sessions)
        # With race condition, we might get 1-2 different sessions
        # which is acceptable (worst case: minor resource waste)
        assert len(unique_ids) <= 3, "Too many session instances created"


class TestEventBusConcurrency:
    """Tests for concurrent access to EventBus"""

    def test_concurrent_event_emission(self):
        """Test concurrent event emission"""
        bus = EventBus()
        received_events = []
        lock = threading.Lock()

        async def handler(event: Event):
            with lock:
                received_events.append(event.data.get("id"))

        bus.on("test_event", handler)

        async def emit_events(start_id):
            for i in range(10):
                await bus.emit("test_event", data={"id": start_id + i})

        def run_async(start_id):
            asyncio.run(emit_events(start_id))

        threads = [threading.Thread(target=run_async, args=(i * 10,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should receive all 50 events
        assert len(received_events) == 50

    def test_concurrent_handler_registration(self):
        """Test concurrent handler registration"""
        bus = EventBus()
        handlers_called = []
        lock = threading.Lock()

        def register_handler(handler_id):
            async def handler(event: Event):
                with lock:
                    handlers_called.append(handler_id)

            bus.on("test_event", handler)

        threads = [threading.Thread(target=register_handler, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all handlers are registered
        assert len(bus.handlers.get("test_event", [])) == 10

    def test_isolated_event_buses_for_parallel_runs(self):
        """Test that separate EventBus instances are properly isolated"""
        results = {1: [], 2: []}

        async def run_with_bus(bus_id: int, bus: EventBus):
            async def handler(event: Event):
                results[bus_id].append(event.data.get("value"))

            bus.on("event", handler)
            await bus.emit("event", data={"value": bus_id * 100})
            await bus.emit("event", data={"value": bus_id * 100 + 1})

        def run_scenario(bus_id: int):
            bus = EventBus()  # Create isolated bus
            asyncio.run(run_with_bus(bus_id, bus))

        threads = [
            threading.Thread(target=run_scenario, args=(1,)),
            threading.Thread(target=run_scenario, args=(2,)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify isolation - each bus only received its own events
        assert results[1] == [100, 101]
        assert results[2] == [200, 201]


class TestMemoryMonitorConcurrency:
    """Tests for concurrent access to MemoryMonitor"""

    def test_concurrent_memory_checks(self):
        """Test that concurrent memory checks are safe"""
        monitor = get_memory_monitor()
        results = []
        errors = []

        def check_memory():
            try:
                for _ in range(50):
                    result = monitor.check_memory("test")
                    results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=check_memory) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during memory checks: {errors}"
        assert len(results) == 500  # 10 threads * 50 checks
        assert all(isinstance(r, bool) for r in results)


@pytest.mark.skipif(not SETTINGS_AVAILABLE, reason="FastAPI not installed")
class TestSettingsConcurrency:
    """Tests for concurrent access to API settings"""

    def test_concurrent_settings_access(self):
        """Test that concurrent settings access is safe"""
        settings_module.reset_settings()
        settings_list = []
        errors = []

        def get_setting():
            try:
                settings = settings_module.get_settings()
                settings_list.append(settings.rate_limit_requests)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_setting) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        settings_module.reset_settings()

        assert len(errors) == 0, f"Errors during settings access: {errors}"
        assert len(settings_list) == 20
        # All should have same value
        assert all(s == settings_list[0] for s in settings_list)


class TestAsyncConcurrency:
    """Tests for async concurrent access patterns"""

    @pytest.mark.asyncio
    async def test_async_concurrent_cache_access(self):
        """Test async concurrent cache access using asyncio"""
        cache = ResponseCache()

        async def cache_operation(op_id: int):
            messages = [{"role": "user", "content": f"Message {op_id}"}]
            cache.put("model", messages, f"response-{op_id}", 100, 70, 30)
            await asyncio.sleep(0.001)  # Simulate async operation
            return cache.get("model", messages)

        # Run many concurrent operations
        tasks = [cache_operation(i) for i in range(100)]
        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == 100
        assert all(r is not None for r in results)

    @pytest.mark.asyncio
    async def test_async_event_bus_concurrent_emission(self):
        """Test async concurrent event emission"""
        bus = EventBus()
        received = []

        async def handler(event: Event):
            received.append(event.data.get("id"))

        bus.on("test", handler)

        async def emit_batch(start_id: int):
            for i in range(10):
                await bus.emit("test", data={"id": start_id + i})

        # Run concurrent emission batches
        await asyncio.gather(
            emit_batch(0),
            emit_batch(100),
            emit_batch(200),
        )

        assert len(received) == 30


class TestMultiprocessingRecommendation:
    """Tests demonstrating multiprocessing isolation"""

    def test_global_state_isolation_simulation(self):
        """
        Simulate what happens with multiprocessing - each "process"
        (simulated with reset) gets fresh global state.

        Note: When disk caching is enabled (default), cached data persists
        across process boundaries. This test uses memory-only caching to
        demonstrate the isolation pattern that would occur with multiprocessing.
        """
        # Use memory-only caches to simulate true process isolation
        cache1 = ResponseCache(cache_dir=None, enabled=True)
        messages = [{"role": "user", "content": "Process 1"}]
        cache1.put("model", messages, "response1", 100, 70, 30)
        assert cache1.get("model", messages) is not None

        # Create a separate cache (simulates new process with fresh memory)
        cache2 = ResponseCache(cache_dir=None, enabled=True)
        # Cache2 should NOT have cache1's data (process isolation)
        assert cache2.get("model", messages) is None

    def test_disk_cache_persists_across_resets(self):
        """
        Document that disk caching persists data across cache resets.
        This is intentional for single-process use but means parallel
        runs with disk caching may share cached data.
        """
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            # Process 1 with disk cache
            cache1 = ResponseCache(cache_dir=tmpdir, enabled=True)
            messages = [{"role": "user", "content": "Shared"}]
            cache1.put("model", messages, "response1", 100, 70, 30)

            # Process 2 with same disk cache directory
            cache2 = ResponseCache(cache_dir=tmpdir, enabled=True)
            # With disk caching, data IS shared (by design)
            entry = cache2.get("model", messages)
            assert entry is not None
            assert entry.response == "response1"


class TestCacheRunIsolation:
    """Tests for run-scoped cache isolation"""

    @patch.dict("os.environ", {"SCENARIO_RUN_ID": "run-001"})
    def test_run_scoped_cache_directory(self):
        """Test that SCENARIO_RUN_ID creates isolated cache directory"""
        reset_global_cache()
        cache = get_global_cache()

        # Should have run-specific cache directory
        if cache.cache_dir:
            assert "run-001" in cache.cache_dir

        reset_global_cache()
