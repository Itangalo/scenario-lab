"""
Tests for graceful_fallback.py - Graceful degradation for missing dependencies
"""
import pytest
import sys
from pathlib import Path
from io import StringIO

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from graceful_fallback import (
    GracefulImports,
    SimplifiedConsole,
    SimplifiedProgress,
    SimplifiedTable,
    get_console,
    get_progress,
    get_table,
    is_rich_available,
    print_with_fallback
)


class TestGracefulImports:
    """Test GracefulImports"""

    def test_try_import_available(self):
        """Test importing available module"""
        imports = GracefulImports()
        assert imports.try_import('json') is True

    def test_try_import_unavailable(self):
        """Test importing unavailable module"""
        imports = GracefulImports()
        assert imports.try_import('nonexistent_module_12345') is False

    def test_try_import_caching(self):
        """Test that import results are cached"""
        imports = GracefulImports()

        # First call
        result1 = imports.try_import('json')

        # Second call (should use cache)
        result2 = imports.try_import('json')

        assert result1 == result2
        assert 'json' in imports.available_modules

    def test_warning_shown_once(self):
        """Test that warning is only shown once per module"""
        imports = GracefulImports()

        # First import attempt
        imports.try_import('nonexistent_module_xyz')
        assert 'nonexistent_module_xyz' in imports.warnings_shown

        # Second attempt should not show warning again
        imports.try_import('nonexistent_module_xyz')


class TestSimplifiedConsole:
    """Test SimplifiedConsole fallback"""

    def test_console_creation(self):
        """Test creating a SimplifiedConsole"""
        console = SimplifiedConsole()
        assert console is not None

    def test_console_print(self):
        """Test printing to console"""
        output = StringIO()
        console = SimplifiedConsole(file=output)

        console.print("Test message")

        assert "Test message" in output.getvalue()

    def test_console_print_ignores_rich_kwargs(self):
        """Test that rich-specific kwargs are ignored"""
        output = StringIO()
        console = SimplifiedConsole(file=output)

        # Should not raise error
        console.print("Test", style="bold", justify="center", overflow="fold")

        assert "Test" in output.getvalue()

    def test_console_rule(self):
        """Test printing a rule"""
        output = StringIO()
        console = SimplifiedConsole(file=output)

        console.rule("Test Title")

        result = output.getvalue()
        assert "=" in result
        assert "Test Title" in result

    def test_console_rule_no_title(self):
        """Test printing rule without title"""
        output = StringIO()
        console = SimplifiedConsole(file=output)

        console.rule()

        assert "=" in output.getvalue()


class TestSimplifiedProgress:
    """Test SimplifiedProgress fallback"""

    def test_progress_creation(self):
        """Test creating a SimplifiedProgress"""
        progress = SimplifiedProgress()
        assert progress is not None

    def test_add_task(self):
        """Test adding a task"""
        progress = SimplifiedProgress()
        task_id = progress.add_task("Test task", total=100)

        assert task_id is not None
        assert task_id in progress.tasks

    def test_update_task(self):
        """Test updating task progress"""
        progress = SimplifiedProgress()
        task_id = progress.add_task("Test task", total=100)

        progress.update(task_id, advance=10)

        assert progress.tasks[task_id]['completed'] == 10

    def test_update_multiple_times(self):
        """Test updating task multiple times"""
        progress = SimplifiedProgress()
        task_id = progress.add_task("Test task", total=100)

        progress.update(task_id, advance=25)
        progress.update(task_id, advance=25)
        progress.update(task_id, advance=25)

        assert progress.tasks[task_id]['completed'] == 75

    def test_context_manager(self):
        """Test using progress as context manager"""
        with SimplifiedProgress() as progress:
            task_id = progress.add_task("Test task", total=10)
            progress.update(task_id, advance=5)
            assert progress.tasks[task_id]['completed'] == 5


class TestSimplifiedTable:
    """Test SimplifiedTable fallback"""

    def test_table_creation(self):
        """Test creating a SimplifiedTable"""
        table = SimplifiedTable()
        assert table is not None

    def test_add_column(self):
        """Test adding columns"""
        table = SimplifiedTable()
        table.add_column("Name")
        table.add_column("Age")

        assert len(table.columns) == 2
        assert table.columns[0] == "Name"
        assert table.columns[1] == "Age"

    def test_add_row(self):
        """Test adding rows"""
        table = SimplifiedTable()
        table.add_column("Name")
        table.add_column("Age")

        table.add_row("Alice", "30")
        table.add_row("Bob", "25")

        assert len(table.rows) == 2

    def test_table_rendering(self):
        """Test rendering table as string"""
        table = SimplifiedTable()
        table.add_column("Name")
        table.add_column("Value")

        table.add_row("Item 1", "100")
        table.add_row("Item 2", "200")

        result = str(table)

        assert "Name" in result
        assert "Value" in result
        assert "Item 1" in result
        assert "Item 2" in result
        assert "100" in result
        assert "200" in result
        assert "|" in result
        assert "-" in result

    def test_empty_table(self):
        """Test rendering empty table"""
        table = SimplifiedTable()
        assert str(table) == ""


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_get_console(self):
        """Test get_console function"""
        console = get_console()
        assert console is not None

    def test_get_progress(self):
        """Test get_progress function"""
        progress = get_progress()
        assert progress is not None

    def test_get_table(self):
        """Test get_table function"""
        table = get_table()
        assert table is not None

    def test_is_rich_available(self):
        """Test is_rich_available function"""
        result = is_rich_available()
        assert isinstance(result, bool)

    def test_print_with_fallback(self):
        """Test print_with_fallback function"""
        # Should not raise error
        print_with_fallback("Test message", style="bold")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
