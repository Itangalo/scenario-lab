"""
Logging configuration for Scenario Lab.

Provides structured logging with console and file output, configurable verbosity,
and per-run log files for debugging and analysis.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Formatter that adds color to console output based on log level."""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    verbose: bool = False,
    log_file: Optional[Path] = None,
    module_name: str = "scenario_lab"
) -> logging.Logger:
    """
    Set up logging configuration for the application.

    Args:
        verbose: If True, set log level to DEBUG. Otherwise INFO.
        log_file: Optional path to log file. If provided, logs will be written to file.
        module_name: Name of the module/logger to configure.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(module_name)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Set log level
    log_level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(log_level)

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    console_format = ColoredFormatter(
        fmt='%(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (if log_file provided)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file

        file_format = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Name of the module (typically __name__).

    Returns:
        Logger instance.
    """
    return logging.getLogger(f"scenario_lab.{name}")


def setup_run_logging(output_dir: Path, verbose: bool = False) -> logging.Logger:
    """
    Set up logging for a scenario run with file output.

    Args:
        output_dir: Directory where log file will be created.
        verbose: If True, enable DEBUG logging to console.

    Returns:
        Configured logger instance.
    """
    log_file = output_dir / "scenario.log"
    return setup_logging(verbose=verbose, log_file=log_file)


def log_section(logger: logging.Logger, title: str, level: int = logging.INFO):
    """
    Log a section header for better readability.

    Args:
        logger: Logger instance.
        title: Section title.
        level: Log level (default: INFO).
    """
    separator = "=" * 60
    logger.log(level, "")
    logger.log(level, separator)
    logger.log(level, title)
    logger.log(level, separator)


def log_subsection(logger: logging.Logger, title: str, level: int = logging.INFO):
    """
    Log a subsection header for better readability.

    Args:
        logger: Logger instance.
        title: Subsection title.
        level: Log level (default: INFO).
    """
    separator = "-" * 40
    logger.log(level, "")
    logger.log(level, separator)
    logger.log(level, title)
    logger.log(level, separator)


def log_cost(logger: logging.Logger, description: str, amount: float):
    """
    Log a cost-related message with consistent formatting.

    Args:
        logger: Logger instance.
        description: Description of the cost.
        amount: Cost amount in dollars.
    """
    logger.info(f"💰 {description}: ${amount:.4f}")


def log_metric(logger: logging.Logger, name: str, value: any):
    """
    Log a metric with consistent formatting.

    Args:
        logger: Logger instance.
        name: Metric name.
        value: Metric value.
    """
    logger.info(f"📊 {name}: {value}")


def log_actor_decision(logger: logging.Logger, actor_name: str, turn: int):
    """
    Log that an actor is making a decision.

    Args:
        logger: Logger instance.
        actor_name: Name of the actor.
        turn: Current turn number.
    """
    logger.info(f"🤖 Actor '{actor_name}' deciding for turn {turn}...")


def log_world_update(logger: logging.Logger, turn: int):
    """
    Log that the world state is being updated.

    Args:
        logger: Logger instance.
        turn: Current turn number.
    """
    logger.info(f"🌍 Updating world state for turn {turn}...")


def log_validation(logger: logging.Logger, turn: int, issues_found: int):
    """
    Log validation results.

    Args:
        logger: Logger instance.
        turn: Current turn number.
        issues_found: Number of validation issues found.
    """
    if issues_found > 0:
        logger.warning(f"⚠️  Validation for turn {turn}: {issues_found} issue(s) found")
    else:
        logger.info(f"✓ Validation for turn {turn}: No issues found")


def log_error_with_context(logger: logging.Logger, error: Exception, context: str):
    """
    Log an error with additional context.

    Args:
        logger: Logger instance.
        error: Exception that occurred.
        context: Additional context about where/when the error occurred.
    """
    logger.error(f"❌ Error in {context}: {type(error).__name__}: {str(error)}")
    logger.debug(f"Full traceback:", exc_info=True)
