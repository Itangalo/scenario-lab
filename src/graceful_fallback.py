"""
Graceful Fallback - Handles missing dependencies gracefully with degraded functionality

This module provides fallback implementations for optional dependencies:
- rich: Terminal formatting and progress bars
- Other visualization libraries

When dependencies are missing, the system continues to work with simplified output.
"""
import sys
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


class GracefulImports:
    """
    Manages optional imports with graceful degradation

    Usage:
        imports = GracefulImports()
        rich_available = imports.try_import('rich')

        if rich_available:
            from rich.console import Console
            console = Console()
        else:
            console = imports.get_fallback('rich_console')
    """

    def __init__(self):
        self.available_modules = {}
        self.warnings_shown = set()

    def try_import(self, module_name: str) -> bool:
        """
        Try to import a module and return whether it's available

        Args:
            module_name: Name of module to import

        Returns:
            True if module is available, False otherwise
        """
        if module_name in self.available_modules:
            return self.available_modules[module_name]

        try:
            __import__(module_name)
            self.available_modules[module_name] = True
            logger.debug(f"Module '{module_name}' is available")
            return True
        except ImportError:
            self.available_modules[module_name] = False

            # Show warning once
            if module_name not in self.warnings_shown:
                logger.warning(
                    f"Module '{module_name}' not available. "
                    f"Using simplified fallback. "
                    f"Install with: pip install {module_name}"
                )
                self.warnings_shown.add(module_name)

            return False

    def get_fallback(self, feature: str) -> Any:
        """
        Get a fallback implementation for a missing feature

        Args:
            feature: Name of feature to get fallback for

        Returns:
            Fallback implementation
        """
        fallbacks = {
            'rich_console': SimplifiedConsole,
            'rich_progress': SimplifiedProgress,
            'rich_table': SimplifiedTable,
        }

        return fallbacks.get(feature)


class SimplifiedConsole:
    """Fallback console when rich is not available"""

    def __init__(self, file=None):
        self.file = file or sys.stdout

    def print(self, *args, **kwargs):
        """Print without rich formatting"""
        # Remove rich-specific kwargs
        kwargs.pop('style', None)
        kwargs.pop('justify', None)
        kwargs.pop('overflow', None)

        print(*args, file=self.file, **kwargs)

    def rule(self, title: str = "", **kwargs):
        """Print a simple horizontal rule"""
        width = 70
        if title:
            print(f"\n{'=' * width}", file=self.file)
            print(f"{title:^{width}}", file=self.file)
            print(f"{'=' * width}\n", file=self.file)
        else:
            print(f"{'=' * width}", file=self.file)


class SimplifiedProgress:
    """Fallback progress tracker when rich is not available"""

    def __init__(self):
        self.tasks = {}
        self.task_counter = 0

    def add_task(self, description: str, total: Optional[int] = None, **kwargs):
        """Add a task"""
        task_id = self.task_counter
        self.task_counter += 1

        self.tasks[task_id] = {
            'description': description,
            'total': total,
            'completed': 0
        }

        print(f"Starting: {description}", file=sys.stderr)
        return task_id

    def update(self, task_id: int, advance: int = 1, **kwargs):
        """Update task progress"""
        if task_id in self.tasks:
            self.tasks[task_id]['completed'] += advance

            task = self.tasks[task_id]
            if task['total']:
                pct = (task['completed'] / task['total']) * 100
                print(
                    f"\r{task['description']}: {task['completed']}/{task['total']} ({pct:.1f}%)",
                    end='',
                    file=sys.stderr,
                    flush=True
                )

    def start(self):
        """Start progress tracking (no-op for fallback)"""
        pass

    def stop(self):
        """Stop progress tracking"""
        print(file=sys.stderr)  # Newline after progress

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class SimplifiedTable:
    """Fallback table when rich is not available"""

    def __init__(self, *args, **kwargs):
        self.columns = []
        self.rows = []

    def add_column(self, header: str, **kwargs):
        """Add a column"""
        self.columns.append(header)

    def add_row(self, *values):
        """Add a row"""
        self.rows.append(values)

    def __str__(self):
        """Render as simple text table"""
        if not self.columns:
            return ""

        # Calculate column widths
        widths = [len(col) for col in self.columns]
        for row in self.rows:
            for i, val in enumerate(row):
                if i < len(widths):
                    widths[i] = max(widths[i], len(str(val)))

        # Build table
        lines = []

        # Header
        header = " | ".join(
            col.ljust(widths[i]) for i, col in enumerate(self.columns)
        )
        lines.append(header)
        lines.append("-" * len(header))

        # Rows
        for row in self.rows:
            line = " | ".join(
                str(val).ljust(widths[i]) for i, val in enumerate(row)
            )
            lines.append(line)

        return "\n".join(lines)


# Global instance
_graceful_imports = GracefulImports()


def get_console():
    """Get console (rich or fallback)"""
    if _graceful_imports.try_import('rich'):
        from rich.console import Console
        return Console()
    else:
        return SimplifiedConsole()


def get_progress():
    """Get progress tracker (rich or fallback)"""
    if _graceful_imports.try_import('rich'):
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
        )
    else:
        return SimplifiedProgress()


def get_table(*args, **kwargs):
    """Get table (rich or fallback)"""
    if _graceful_imports.try_import('rich'):
        from rich.table import Table
        return Table(*args, **kwargs)
    else:
        return SimplifiedTable(*args, **kwargs)


def is_rich_available() -> bool:
    """Check if rich library is available"""
    return _graceful_imports.try_import('rich')


def print_with_fallback(*args, style: Optional[str] = None, **kwargs):
    """
    Print with rich styling if available, otherwise plain text

    Args:
        *args: Print arguments
        style: Rich style string (ignored in fallback)
        **kwargs: Print keyword arguments
    """
    if is_rich_available():
        from rich.console import Console
        console = Console()
        console.print(*args, style=style, **kwargs)
    else:
        # Remove rich-specific kwargs
        kwargs.pop('justify', None)
        kwargs.pop('overflow', None)
        print(*args, **kwargs)
