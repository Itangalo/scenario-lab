#!/usr/bin/env python3
"""
Test V2 Memory Optimizer

Tests the memory optimization utilities for large batch runs.
"""
import sys
import tempfile
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scenario_lab.utils.memory_optimizer import (
    MemoryStats, MemoryMonitor, StreamingWriter,
    chunked_iterator, optimize_memory, get_object_size,
    MemoryEfficientDict, reduce_dict_memory,
    MemoryOptimizedBatchRunner, get_memory_monitor
)


def test_memory_stats():
    """Test MemoryStats dataclass"""
    print("=" * 70)
    print("TEST 1: MemoryStats dataclass")
    print("=" * 70)
    print()

    stats = MemoryStats(
        total_mb=16384.0,
        available_mb=8192.0,
        used_mb=8192.0,
        percent_used=50.0,
        process_mb=512.0
    )

    assert stats.total_mb == 16384.0
    assert stats.available_mb == 8192.0
    assert stats.percent_used == 50.0
    assert stats.process_mb == 512.0

    print(f"  ✓ MemoryStats created")
    print(f"  ✓ Total: {stats.total_mb:,.0f} MB")
    print(f"  ✓ Available: {stats.available_mb:,.0f} MB")
    print(f"  ✓ Used: {stats.percent_used:.1f}%")
    print(f"  ✓ Process: {stats.process_mb:,.0f} MB")

    print()
    print("✅ Test 1 passed: MemoryStats works correctly")
    print()
    return True


def test_memory_monitor_graceful_degradation():
    """Test MemoryMonitor graceful degradation without psutil"""
    print("=" * 70)
    print("TEST 2: MemoryMonitor graceful degradation")
    print("=" * 70)
    print()

    monitor = MemoryMonitor()

    # Should work even if psutil not available
    assert monitor.warning_threshold == 80.0
    assert monitor.critical_threshold == 90.0
    print(f"  ✓ Monitor created with thresholds")
    print(f"  ✓ Warning threshold: {monitor.warning_threshold}%")
    print(f"  ✓ Critical threshold: {monitor.critical_threshold}%")

    # check_memory should return True even without psutil
    result = monitor.check_memory("Test context")
    assert result is True
    print(f"  ✓ check_memory returns True (safe mode)")

    # log_memory_summary should not crash
    monitor.log_memory_summary()
    print(f"  ✓ log_memory_summary works (may show 'not available' message)")

    print()
    print("✅ Test 2 passed: Graceful degradation works correctly")
    print()
    return True


def test_streaming_writer():
    """Test StreamingWriter for memory-efficient file writes"""
    print("=" * 70)
    print("TEST 3: StreamingWriter")
    print("=" * 70)
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "test_output.txt"

        # Write with StreamingWriter
        with StreamingWriter(str(output_file)) as writer:
            writer.write("Line 1\n")
            writer.writeline("Line 2")
            writer.write("Line 3\n")

        # Verify output
        content = output_file.read_text()
        lines = content.strip().split('\n')

        assert len(lines) == 3
        assert "Line 1" in content
        assert "Line 2" in content
        assert "Line 3" in content

        print(f"  ✓ StreamingWriter created file")
        print(f"  ✓ Wrote {len(lines)} lines")
        print(f"  ✓ File size: {len(content)} bytes")

    print()
    print("✅ Test 3 passed: StreamingWriter works correctly")
    print()
    return True


def test_chunked_iterator():
    """Test chunked iterator for batch processing"""
    print("=" * 70)
    print("TEST 4: Chunked iterator")
    print("=" * 70)
    print()

    # Test with 100 items, chunk size 25
    items = list(range(100))
    chunks = list(chunked_iterator(items, chunk_size=25))

    assert len(chunks) == 4
    assert len(chunks[0]) == 25
    assert len(chunks[1]) == 25
    assert len(chunks[2]) == 25
    assert len(chunks[3]) == 25

    print(f"  ✓ Created {len(chunks)} chunks from 100 items")
    print(f"  ✓ Chunk size: 25")
    print(f"  ✓ All chunks have correct size")

    # Test with uneven division
    items = list(range(105))
    chunks = list(chunked_iterator(items, chunk_size=25))

    assert len(chunks) == 5
    assert len(chunks[4]) == 5  # Last chunk has remainder

    print(f"  ✓ Handles uneven division (105 items → 5 chunks)")
    print(f"  ✓ Last chunk size: {len(chunks[4])}")

    print()
    print("✅ Test 4 passed: Chunked iterator works correctly")
    print()
    return True


def test_optimize_memory():
    """Test memory optimization function"""
    print("=" * 70)
    print("TEST 5: Memory optimization")
    print("=" * 70)
    print()

    # Should not crash
    optimize_memory()
    print(f"  ✓ optimize_memory() executed")
    print(f"  ✓ Garbage collection triggered")

    # Test get_object_size
    small_obj = "Hello"
    large_obj = "A" * 10000

    small_size = get_object_size(small_obj)
    large_size = get_object_size(large_obj)

    assert large_size > small_size
    print(f"  ✓ get_object_size() works")
    print(f"    - Small string: {small_size} bytes")
    print(f"    - Large string: {large_size} bytes")

    print()
    print("✅ Test 5 passed: Memory optimization works correctly")
    print()
    return True


def test_memory_efficient_dict():
    """Test MemoryEfficientDict with LRU eviction"""
    print("=" * 70)
    print("TEST 6: MemoryEfficientDict with LRU")
    print("=" * 70)
    print()

    # Create dict with max size 3
    mem_dict = MemoryEfficientDict(max_size=3)

    # Add 3 items
    mem_dict['key1'] = 'value1'
    mem_dict['key2'] = 'value2'
    mem_dict['key3'] = 'value3'

    assert len(mem_dict) == 3
    assert 'key1' in mem_dict
    print(f"  ✓ Added 3 items (max_size=3)")

    # Add 4th item - should evict key1 (LRU)
    mem_dict['key4'] = 'value4'

    assert len(mem_dict) == 3
    assert 'key1' not in mem_dict  # Evicted
    assert 'key4' in mem_dict
    print(f"  ✓ Added 4th item → evicted oldest (key1)")

    # Access key2 to make it recently used
    _ = mem_dict['key2']

    # Add key5 - should evict key3 (now LRU)
    mem_dict['key5'] = 'value5'

    assert 'key3' not in mem_dict  # Evicted
    assert 'key2' in mem_dict  # Still there (accessed recently)
    print(f"  ✓ LRU eviction works correctly")
    print(f"  ✓ Recently accessed items are kept")

    # Test get with default
    result = mem_dict.get('nonexistent', 'default')
    assert result == 'default'
    print(f"  ✓ get() with default works")

    # Test clear
    mem_dict.clear()
    assert len(mem_dict) == 0
    print(f"  ✓ clear() works")

    print()
    print("✅ Test 6 passed: MemoryEfficientDict works correctly")
    print()
    return True


def test_reduce_dict_memory():
    """Test dictionary memory reduction"""
    print("=" * 70)
    print("TEST 7: Dictionary memory reduction")
    print("=" * 70)
    print()

    # Create large dict
    large_dict = {
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3',
        'key4': 'value4',
        'key5': 'value5'
    }

    # Reduce to keep only specific keys
    reduced = reduce_dict_memory(large_dict, keep_keys=['key1', 'key3'])

    assert len(reduced) == 2
    assert 'key1' in reduced
    assert 'key3' in reduced
    assert 'key2' not in reduced
    assert 'key4' not in reduced

    print(f"  ✓ Reduced dict from {len(large_dict)} to {len(reduced)} keys")
    print(f"  ✓ Kept only specified keys: {list(reduced.keys())}")

    # Test with None (keep all)
    unchanged = reduce_dict_memory(large_dict, keep_keys=None)
    assert len(unchanged) == len(large_dict)
    print(f"  ✓ keep_keys=None preserves all keys")

    print()
    print("✅ Test 7 passed: Dictionary memory reduction works correctly")
    print()
    return True


def test_memory_optimized_batch_runner():
    """Test MemoryOptimizedBatchRunner"""
    print("=" * 70)
    print("TEST 8: MemoryOptimizedBatchRunner")
    print("=" * 70)
    print()

    runner = MemoryOptimizedBatchRunner(enable_gc=True, gc_interval=2)

    assert runner.enable_gc is True
    assert runner.gc_interval == 2
    assert runner.runs_since_gc == 0
    print(f"  ✓ Runner created")
    print(f"  ✓ GC enabled: {runner.enable_gc}")
    print(f"  ✓ GC interval: {runner.gc_interval}")

    # Simulate runs
    runner.before_run(1)
    runner.after_run(1)
    assert runner.runs_since_gc == 1
    print(f"  ✓ After run 1: runs_since_gc = {runner.runs_since_gc}")

    runner.before_run(2)
    runner.after_run(2)
    # Should have run GC and reset counter
    assert runner.runs_since_gc == 0
    print(f"  ✓ After run 2: GC triggered, counter reset")

    # Test memory summary
    runner.summarize_memory_usage()
    print(f"  ✓ Memory summary generated")

    print()
    print("✅ Test 8 passed: MemoryOptimizedBatchRunner works correctly")
    print()
    return True


def test_global_memory_monitor():
    """Test global memory monitor singleton"""
    print("=" * 70)
    print("TEST 9: Global memory monitor")
    print("=" * 70)
    print()

    monitor1 = get_memory_monitor()
    monitor2 = get_memory_monitor()

    # Should be same instance
    assert monitor1 is monitor2
    print(f"  ✓ get_memory_monitor() returns singleton")
    print(f"  ✓ Multiple calls return same instance")

    print()
    print("✅ Test 9 passed: Global memory monitor works correctly")
    print()
    return True


def run_all_tests():
    """Run all memory optimizer tests"""
    print()
    print("=" * 70)
    print("V2 MEMORY OPTIMIZER TESTS")
    print("=" * 70)
    print()

    tests = [
        test_memory_stats,
        test_memory_monitor_graceful_degradation,
        test_streaming_writer,
        test_chunked_iterator,
        test_optimize_memory,
        test_memory_efficient_dict,
        test_reduce_dict_memory,
        test_memory_optimized_batch_runner,
        test_global_memory_monitor,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("=" * 70)
    print("MEMORY OPTIMIZER TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ ALL MEMORY OPTIMIZER TESTS PASSED")
        print()
        print("Phase 3.7 Complete: Memory Optimization")
        print("  ✓ MemoryStats dataclass")
        print("  ✓ MemoryMonitor with graceful degradation")
        print("  ✓ StreamingWriter for efficient file I/O")
        print("  ✓ Chunked iterator for batch processing")
        print("  ✓ Memory optimization (garbage collection)")
        print("  ✓ MemoryEfficientDict with LRU eviction")
        print("  ✓ Dictionary memory reduction")
        print("  ✓ MemoryOptimizedBatchRunner")
        print("  ✓ Global memory monitor singleton")
        print()
        return True
    else:
        print("❌ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
