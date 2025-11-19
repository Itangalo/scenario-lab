"""
CLI helper utilities for Scenario Lab V2

Provides common styling and formatting functions for consistent CLI output.
"""
import click
from typing import Optional


def print_header(title: str, subtitle: Optional[str] = None) -> None:
    """
    Print a styled header

    Args:
        title: Main title text
        subtitle: Optional subtitle text
    """
    click.echo()
    click.echo(click.style(f"✨ {title}", fg="bright_cyan", bold=True))
    click.echo(click.style("─" * 40, fg="cyan"))
    if subtitle:
        click.echo(click.style(subtitle, fg="cyan", dim=True))


def print_info(label: str, value: str, color: str = "green") -> None:
    """
    Print an info line with icon, label and colored value

    Args:
        label: The label text (e.g., "Scenario:")
        value: The value to display
        color: Color for the value
    """
    # Map common labels to emojis
    icons = {
        "Scenario": "📂",
        "Path": "📂",
        "Max turns": "🔢",
        "Turns": "🔢",
        "Credit limit": "💰",
        "Resuming": "▶️",
        "Branching from": "🌿",
        "Version": "📦",
        "Architecture": "🏗️",
        "Status": "🚀",
    }

    icon = icons.get(label, "•")
    click.echo(f"{icon} {label}: " + click.style(value, fg=color))


def print_success(message: str) -> None:
    """
    Print a success message

    Args:
        message: Success message to display
    """
    click.echo()
    click.echo(click.style(f"✓ {message}", fg="bright_green", bold=True))


def print_error(message: str, details: Optional[str] = None, tip: Optional[str] = None) -> None:
    """
    Print an error message with optional details and tip

    Args:
        message: Main error message
        details: Optional error details
        tip: Optional tip for resolution
    """
    click.echo()
    click.echo(click.style(f"✗ Error:", fg="bright_red", bold=True) + f" {message}", err=True)

    if details:
        click.echo(click.style(f"  {details}", fg="red", dim=True), err=True)

    if tip:
        click.echo()
        click.echo(click.style("💡 Tip:", fg="bright_blue") + f" {tip}", err=True)


def print_warning(message: str) -> None:
    """
    Print a warning message

    Args:
        message: Warning message to display
    """
    click.echo(click.style(f"⚠️  {message}", fg="yellow", bold=True))


def print_alpha_notice(feature: str = "Full V2 execution engine") -> None:
    """
    Print the V2 alpha notice

    Args:
        feature: What feature is coming in the next phase
    """
    click.echo()
    click.echo(click.style("⚠️  V2 Alpha:", fg="yellow", bold=True) + " Delegating to V1 runner...")
    click.echo(click.style(f"   {feature} coming in Phase 2.1", fg="yellow", dim=True))
    click.echo()


def print_section(title: str) -> None:
    """
    Print a section header

    Args:
        title: Section title
    """
    click.echo()
    click.echo(click.style(title, fg="bright_white", bold=True))


def print_checklist_item(label: str, status: str = "✓") -> None:
    """
    Print a checklist item

    Args:
        label: Item label
        status: Status symbol (✓, ⏳, etc.)
    """
    if status == "✓":
        color = "green"
    elif status == "⏳":
        color = "yellow"
    else:
        color = "white"

    click.echo(f"  {click.style(status, fg=color)} {label}")
