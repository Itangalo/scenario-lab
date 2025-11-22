"""
CLI helper utilities for Scenario Lab V2

Provides common styling and formatting functions for consistent CLI output.
Uses Rich library for enhanced terminal display.
"""
from __future__ import annotations

from typing import Any, Optional, Sequence

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from scenario_lab.utils.rich_console import (
    console,
    error_console,
    Icons,
    Styles,
    get_cost_style,
)


# Icon mapping for common labels
LABEL_ICONS = {
    "Scenario": Icons.FOLDER,
    "Path": Icons.FOLDER,
    "Max turns": Icons.NUMBER,
    "Turns": Icons.NUMBER,
    "End turn": Icons.NUMBER,
    "Credit limit": Icons.MONEY,
    "Resuming": Icons.PLAY,
    "Branching from": Icons.BRANCH,
    "Version": Icons.PACKAGE,
    "Architecture": Icons.BUILDING,
    "Status": Icons.ROCKET,
    "Host": Icons.GLOBE,
    "Port": Icons.GLOBE,
    "Reload": Icons.ROCKET,
}


def print_header(title: str, subtitle: Optional[str] = None) -> None:
    """
    Print a styled header with optional subtitle.

    Args:
        title: Main title text
        subtitle: Optional subtitle text
    """
    console.print()
    console.print(f"{Icons.SPARKLE} [header]{title}[/]")
    console.print("[info]\u2500[/]" * 40)
    if subtitle:
        console.print(f"[dim]{subtitle}[/]")


def print_info(label: str, value: str, color: str = "green") -> None:
    """
    Print an info line with icon, label and colored value.

    Args:
        label: The label text (e.g., "Scenario:")
        value: The value to display
        color: Color for the value (green, yellow, blue, red, cyan)
    """
    icon = LABEL_ICONS.get(label, "\u2022")  # Default bullet
    console.print(f"{icon} {label}: [{color}]{value}[/]")


def print_success(message: str) -> None:
    """
    Print a success message.

    Args:
        message: Success message to display
    """
    console.print()
    console.print(f"[{Styles.SUCCESS}]\u2713 {message}[/]")


def print_error(
    message: str,
    details: Optional[str] = None,
    tip: Optional[str] = None
) -> None:
    """
    Print an error message with optional details and tip.

    Args:
        message: Main error message
        details: Optional error details
        tip: Optional tip for resolution
    """
    error_console.print()
    error_console.print(f"[{Styles.ERROR}]\u2717 Error:[/] {message}")

    if details:
        error_console.print(f"  [error dim]{details}[/]")

    if tip:
        error_console.print()
        error_console.print(f"{Icons.BULB} [info.bright]Tip:[/] {tip}")


def print_warning(message: str) -> None:
    """
    Print a warning message.

    Args:
        message: Warning message to display
    """
    console.print(f"[{Styles.WARNING}]\u26a0\ufe0f  {message}[/]")


def print_alpha_notice(feature: str = "Full V2 execution engine") -> None:
    """
    Print the V2 alpha notice.

    Args:
        feature: What feature is coming in the next phase
    """
    console.print()
    console.print(
        f"[{Styles.WARNING}]\u26a0\ufe0f  V2 Alpha:[/] Delegating to V1 runner..."
    )
    console.print(f"   [warning dim]{feature} coming in Phase 2.1[/]")
    console.print()


def print_section(title: str) -> None:
    """
    Print a section header.

    Args:
        title: Section title
    """
    console.print()
    console.print(f"[{Styles.SECTION}]{title}[/]")


def print_checklist_item(label: str, status: str = "\u2713") -> None:
    """
    Print a checklist item with status indicator.

    Args:
        label: Item label
        status: Status symbol (\u2713, \u2717, \u26a0, \u23f3, etc.)
    """
    if status == "\u2713":
        style = Styles.SUCCESS
    elif status == "\u2717":
        style = Styles.ERROR
    elif status in ("\u26a0", "\u26a0\ufe0f"):
        style = Styles.WARNING
    elif status == "\u23f3":
        style = Styles.WARNING
    else:
        style = "dim"

    console.print(f"  [{style}]{status}[/] {label}")


def print_table(
    title: str,
    columns: Sequence[str],
    rows: Sequence[Sequence[Any]],
    show_header: bool = True,
) -> None:
    """
    Print a formatted table.

    Args:
        title: Table title (displayed above table)
        columns: Column headers
        rows: List of row data (each row is a sequence of values)
        show_header: Whether to show column headers
    """
    table = Table(title=title, show_header=show_header)

    for col in columns:
        table.add_column(col, style="cyan")

    for row in rows:
        table.add_row(*[str(v) for v in row])

    console.print(table)


def print_key_value_table(
    title: Optional[str],
    items: dict[str, Any],
    value_style: str = "green",
) -> None:
    """
    Print a key-value table (no headers, just label-value pairs).

    Args:
        title: Optional table title
        items: Dictionary of label-value pairs
        value_style: Style for values
    """
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Label", style="cyan")
    table.add_column("Value", style=value_style)

    for label, value in items.items():
        table.add_row(label, str(value))

    if title:
        console.print(Panel(table, title=title, border_style="green"))
    else:
        console.print(table)


def print_panel(
    content: str,
    title: Optional[str] = None,
    style: str = "info",
    expand: bool = True,
) -> None:
    """
    Print content in a bordered panel.

    Args:
        content: Panel content (supports Rich markup)
        title: Optional panel title
        style: Border style (info, success, warning, error)
        expand: Whether to expand to full width
    """
    border_styles = {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "red",
    }
    border = border_styles.get(style, "cyan")

    panel = Panel(content, title=title, border_style=border, expand=expand)
    console.print(panel)


def print_turn_header(turn: int) -> None:
    """
    Print a turn header for scenario execution.

    Args:
        turn: Turn number
    """
    console.print()
    console.print(f"[turn]\u2501\u2501\u2501 Turn {turn} \u2501\u2501\u2501[/]")


def print_phase_complete(phase: str) -> None:
    """
    Print phase completion indicator.

    Args:
        phase: Phase name
    """
    phase_display = phase.replace("_", " ").title()
    console.print(f"  [{Styles.SUCCESS}]\u2713[/] {phase_display} phase complete")


def print_cost(label: str, cost: float, show_per_unit: Optional[tuple[str, float]] = None) -> None:
    """
    Print a cost value with appropriate styling.

    Args:
        label: Cost label
        cost: Cost value in USD
        show_per_unit: Optional tuple of (unit_name, per_unit_cost)
    """
    style = get_cost_style(cost)
    text = f"  {label}: [{style}]${cost:.2f}[/]"

    if show_per_unit:
        unit_name, per_unit = show_per_unit
        text += f" ([{style}]${per_unit:.3f}[/] per {unit_name})"

    console.print(text)


def print_link(label: str, url: str) -> None:
    """
    Print a clickable link (in supported terminals).

    Args:
        label: Link label
        url: URL to link to
    """
    console.print(f"{label}: [link={url}][path underline]{url}[/][/]")
