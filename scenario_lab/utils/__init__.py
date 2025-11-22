"""Utility functions for Scenario Lab V2"""

from scenario_lab.utils.cli_helpers import (
    print_header,
    print_info,
    print_success,
    print_error,
    print_warning,
    print_alpha_notice,
    print_section,
    print_checklist_item,
    print_table,
    print_key_value_table,
    print_panel,
    print_turn_header,
    print_phase_complete,
    print_cost,
    print_link,
)
from scenario_lab.utils.rich_console import (
    console,
    error_console,
    Icons,
    Styles,
    get_cost_style,
    get_status_style,
)
from scenario_lab.utils.state_persistence import StatePersistence
from scenario_lab.utils.cost_estimator import CostEstimator, CostEstimate
from scenario_lab.utils.model_pricing import (
    get_model_pricing,
    estimate_cost,
    is_expensive_model,
    is_free_model,
)
from scenario_lab.utils.logging_config import (
    setup_logging,
    set_context,
    clear_context,
    log_cost,
)

__all__ = [
    # CLI helpers
    "print_header",
    "print_info",
    "print_success",
    "print_error",
    "print_warning",
    "print_alpha_notice",
    "print_section",
    "print_checklist_item",
    "print_table",
    "print_key_value_table",
    "print_panel",
    "print_turn_header",
    "print_phase_complete",
    "print_cost",
    "print_link",
    # Rich console
    "console",
    "error_console",
    "Icons",
    "Styles",
    "get_cost_style",
    "get_status_style",
    # State persistence
    "StatePersistence",
    # Cost estimation
    "CostEstimator",
    "CostEstimate",
    "get_model_pricing",
    "estimate_cost",
    "is_expensive_model",
    "is_free_model",
    # Logging
    "setup_logging",
    "set_context",
    "clear_context",
    "log_cost",
]
