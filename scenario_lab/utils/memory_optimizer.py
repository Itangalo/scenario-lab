"""
Memory Optimizer - Reduces memory usage for large batch runs (V2)

Features:
- Streaming file writes to avoid loading entire outputs in memory
- Chunked processing of large datasets
- Memory-efficient data structures
- Garbage collection hints
- Memory monitoring and warnings
- Graceful degradation without psutil

V2 Design:
- No V1 dependencies
- Pure utility functions
- Graceful fallback if psutil unavailable
"""
import gc
import sys
import logging
import os
from typing import Optional, List, Dict, Any, Iterator
from dataclasses import dataclass

# Optional psutil import for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory usage statistics"""
    total_mb: float
    available_mb: float
    used_mb: float
    percent_used: float
    process_mb: float


class MemoryMonitor:
    """
    Monitor memory usage and provide warnings (V2)

    Helps prevent out-of-memory errors in large batch runs.
    Gracefully degrades if psutil not available.
    """

    def __init__(self, warning_threshold: float = 80.0, critical_threshold: float = 90.0):
        """
        Initialize memory monitor

        Args:
            warning_threshold: Percent of memory usage to trigger warning
            critical_threshold: Percent of memory usage to trigger critical warning
        """
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.warnings_shown = set()

        # Check if psutil is available
        self.psutil_available = PSUTIL_AVAILABLE
        if not self.psutil_available:
            logger.debug(
                "psutil not available. Memory monitoring disabled. "
                "Install with: pip install psutil"
            )

    def get_memory_stats(self) -> Optional[MemoryStats]:
        """
        Get current memory statistics

        Returns:
            MemoryStats object or None if psutil not available
        """
        if not self.psutil_available:
            return None

        try:
            # System memory
            mem = psutil.virtual_memory()

            # Process memory
            process = psutil.Process(os.getpid())
            process_mem = process.memory_info().rss / (1024 * 1024)  # MB

            return MemoryStats(
                total_mb=mem.total / (1024 * 1024),
                available_mb=mem.available / (1024 * 1024),
                used_mb=mem.used / (1024 * 1024),
                percent_used=mem.percent,
                process_mb=process_mem
            )
        except Exception as e:
            logger.debug(f"Failed to get memory stats: {e}")
            return None

    def check_memory(self, context: str = "") -> bool:
        """
        Check memory usage and log warnings if thresholds exceeded

        Args:
            context: Context string for logging (e.g., "After turn 5")

        Returns:
            True if memory is within safe limits, False if critical
        """
        stats = self.get_memory_stats()
        if stats is None:
            return True  # Can't check, assume OK

        context_str = f" ({context})" if context else ""

        if stats.percent_used >= self.critical_threshold:
            logger.error(
                f"CRITICAL: Memory usage at {stats.percent_used:.1f}%{context_str}. "
                f"Process using {stats.process_mb:.1f}MB. "
                f"Consider reducing batch size or enabling memory optimization."
            )
            return False

        elif stats.percent_used >= self.warning_threshold:
            # Only warn once per threshold
            key = f"warning_{int(stats.percent_used)}"
            if key not in self.warnings_shown:
                logger.warning(
                    f"Memory usage at {stats.percent_used:.1f}%{context_str}. "
                    f"Process using {stats.process_mb:.1f}MB."
                )
                self.warnings_shown.add(key)

        return True

    def log_memory_summary(self):
        """Log a summary of memory usage"""
        stats = self.get_memory_stats()
        if stats is None:
            logger.info("Memory monitoring not available (install psutil)")
            return

        logger.info(f"\n{'='*60}")
        logger.info(f"MEMORY USAGE SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total RAM:       {stats.total_mb:,.1f} MB")
        logger.info(f"Available:       {stats.available_mb:,.1f} MB")
        logger.info(f"Used:            {stats.used_mb:,.1f} MB ({stats.percent_used:.1f}%)")
        logger.info(f"This process:    {stats.process_mb:,.1f} MB")
        logger.info(f"{'='*60}\n")


class StreamingWriter:
    """
    Write large outputs to file in streaming fashion

    Avoids loading entire output in memory
    """

    def __init__(self, file_path: str, buffer_size: int = 8192):
        """
        Initialize streaming writer

        Args:
            file_path: Path to output file
            buffer_size: Buffer size in bytes (default: 8KB)
        """
        self.file_path = file_path
        self.buffer_size = buffer_size
        self.file_handle = None

    def __enter__(self):
        self.file_handle = open(self.file_path, 'w', buffering=self.buffer_size)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file_handle:
            self.file_handle.close()

    def write(self, content: str):
        """Write content to file"""
        if self.file_handle:
            self.file_handle.write(content)

    def writeline(self, line: str):
        """Write a line to file"""
        if self.file_handle:
            self.file_handle.write(line + '\n')


def chunked_iterator(items: List[Any], chunk_size: int = 100) -> Iterator[List[Any]]:
    """
    Yield chunks of items to process in batches

    Useful for processing large lists without loading everything in memory

    Args:
        items: List of items to process
        chunk_size: Number of items per chunk

    Yields:
        Lists of items (chunks)
    """
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


def optimize_memory():
    """
    Perform memory optimization

    Call this periodically during long-running operations to:
    - Force garbage collection
    - Release unused memory back to OS
    """
    # Force garbage collection
    gc.collect()

    # On some systems, this helps release memory back to OS
    if hasattr(sys, 'gettotalrefcount'):  # Debug build
        logger.debug(f"Total refs: {sys.gettotalrefcount()}")


def get_object_size(obj: Any) -> int:
    """
    Get approximate size of object in bytes

    Args:
        obj: Object to measure

    Returns:
        Size in bytes
    """
    return sys.getsizeof(obj)


class MemoryEfficientDict:
    """
    Dictionary with automatic cleanup of old entries

    Useful for caches or temporary storage that can grow large.
    Uses LRU (Least Recently Used) eviction strategy.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize memory-efficient dictionary

        Args:
            max_size: Maximum number of entries before auto-cleanup
        """
        self.max_size = max_size
        self.data = {}
        self.access_order = []  # Track access order for LRU

    def __setitem__(self, key, value):
        """Set item with LRU tracking"""
        if key in self.data:
            # Move to end (most recently used)
            self.access_order.remove(key)
        elif len(self.data) >= self.max_size:
            # Remove least recently used
            lru_key = self.access_order.pop(0)
            del self.data[lru_key]

        self.data[key] = value
        self.access_order.append(key)

    def __getitem__(self, key):
        """Get item and update access order"""
        if key in self.data:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.data[key]
        raise KeyError(key)

    def __contains__(self, key):
        return key in self.data

    def __len__(self):
        return len(self.data)

    def clear(self):
        """Clear all entries"""
        self.data.clear()
        self.access_order.clear()

    def get(self, key, default=None):
        """Get item with default"""
        try:
            return self[key]
        except KeyError:
            return default


def reduce_dict_memory(data: Dict[str, Any], keep_keys: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Reduce memory usage of dictionary by removing unnecessary keys

    Args:
        data: Dictionary to optimize
        keep_keys: List of keys to keep (if None, keep all)

    Returns:
        Optimized dictionary
    """
    if keep_keys is None:
        return data

    return {k: v for k, v in data.items() if k in keep_keys}


class MemoryOptimizedBatchRunner:
    """
    Wrapper that adds memory optimization to batch runs (V2)

    Features:
    - Periodic garbage collection
    - Memory monitoring
    - Streaming output writes
    - Chunked processing
    """

    def __init__(self, enable_gc: bool = True, gc_interval: int = 10):
        """
        Initialize memory-optimized batch runner

        Args:
            enable_gc: Enable automatic garbage collection
            gc_interval: Run GC every N runs
        """
        self.enable_gc = enable_gc
        self.gc_interval = gc_interval
        self.runs_since_gc = 0
        self.memory_monitor = MemoryMonitor()

    def before_run(self, run_number: int):
        """Call before each run"""
        # Check memory
        self.memory_monitor.check_memory(f"Before run {run_number}")

        # Periodic GC
        if self.enable_gc:
            self.runs_since_gc += 1
            if self.runs_since_gc >= self.gc_interval:
                logger.debug(f"Running garbage collection after {self.runs_since_gc} runs")
                optimize_memory()
                self.runs_since_gc = 0

    def after_run(self, run_number: int):
        """Call after each run"""
        # Check memory again
        self.memory_monitor.check_memory(f"After run {run_number}")

    def summarize_memory_usage(self):
        """Show memory usage summary"""
        self.memory_monitor.log_memory_summary()


# Global memory monitor
_global_memory_monitor = None


def get_memory_monitor() -> MemoryMonitor:
    """Get global memory monitor instance"""
    global _global_memory_monitor

    if _global_memory_monitor is None:
        _global_memory_monitor = MemoryMonitor()

    return _global_memory_monitor
