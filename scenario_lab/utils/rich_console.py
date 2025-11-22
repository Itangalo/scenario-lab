"""
Rich Console utilities for Scenario Lab V2

Provides a shared Console instance and theme constants for consistent
terminal output across all CLI commands.
"""
from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

# Define a consistent color theme for the CLI
SCENARIO_LAB_THEME = Theme({
    # Primary colors
    "info": "cyan",
    "info.bright": "bright_cyan",
    "success": "green",
    "success.bright": "bright_green",
    "warning": "yellow",
    "warning.bright": "bright_yellow",
    "error": "red",
    "error.bright": "bright_red",

    # Structural elements
    "header": "bright_cyan bold",
    "section": "bright_white bold",
    "label": "cyan",
    "value": "green",
    "value.dim": "green dim",

    # Paths and code
    "path": "blue",
    "code": "cyan",
    "command": "cyan",

    # Cost and metrics
    "cost": "green",
    "cost.warning": "yellow",
    "cost.danger": "red",

    # Status indicators
    "status.ok": "green",
    "status.warning": "yellow",
    "status.error": "red",
    "status.pending": "yellow dim",

    # Phase/turn display
    "turn": "bright_cyan bold",
    "phase": "cyan",
})

# Shared console instance - use this throughout the CLI
console = Console(theme=SCENARIO_LAB_THEME)

# Error console (writes to stderr)
error_console = Console(theme=SCENARIO_LAB_THEME, stderr=True)


# Style constants for common use cases
class Styles:
    """Common style strings for Rich markup"""

    # Status colors
    SUCCESS = "success.bright"
    ERROR = "error.bright"
    WARNING = "warning.bright"
    INFO = "info.bright"

    # Structural
    HEADER = "header"
    SECTION = "section"
    LABEL = "label"
    VALUE = "value"
    DIM = "dim"

    # Elements
    PATH = "path"
    COST = "cost"
    TURN = "turn"


# Icon constants for consistent emoji usage
class Icons:
    """Standard icons for CLI output"""

    # Status
    SUCCESS = "[success.bright]\u2713[/]"  # ✓
    ERROR = "[error.bright]\u2717[/]"  # ✗
    WARNING = "[warning.bright]\u26a0\ufe0f[/]"  # ⚠️
    INFO = "[info]\u2022[/]"  # •
    PENDING = "[status.pending]\u23f3[/]"  # ⏳

    # Actions
    SPARKLE = "\u2728"  # ✨
    FOLDER = "\U0001f4c2"  # 📂
    NUMBER = "\U0001f522"  # 🔢
    MONEY = "\U0001f4b0"  # 💰
    PLAY = "\u25b6\ufe0f"  # ▶️
    BRANCH = "\U0001f33f"  # 🌿
    PACKAGE = "\U0001f4e6"  # 📦
    BUILDING = "\U0001f3d7\ufe0f"  # 🏗️
    ROCKET = "\U0001f680"  # 🚀
    CHART = "\U0001f4ca"  # 📊
    BULB = "\U0001f4a1"  # 💡
    GLOBE = "\U0001f310"  # 🌐


def get_cost_style(cost: float) -> str:
    """Get appropriate style for a cost value"""
    if cost > 10.0:
        return "cost.danger"
    elif cost > 1.0:
        return "cost.warning"
    return "cost"


def get_status_style(status: str) -> str:
    """Get appropriate style for a status value"""
    status_lower = status.lower()
    if status_lower in ("ok", "success", "completed", "passed"):
        return "status.ok"
    elif status_lower in ("warning", "pending", "running"):
        return "status.warning"
    elif status_lower in ("error", "failed"):
        return "status.error"
    return "dim"
