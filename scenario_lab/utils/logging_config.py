"""
Structured logging configuration for Scenario Lab V2

Provides centralized logging with context (turn, actor, phase) and
optional JSON formatting for production environments.
"""
import logging
import logging.handlers
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from contextvars import ContextVar


# Context variables for adding metadata to all logs
current_turn: ContextVar[Optional[int]] = ContextVar('current_turn', default=None)
current_actor: ContextVar[Optional[str]] = ContextVar('current_actor', default=None)
current_phase: ContextVar[Optional[str]] = ContextVar('current_phase', default=None)
current_scenario: ContextVar[Optional[str]] = ContextVar('current_scenario', default=None)
current_run_id: ContextVar[Optional[str]] = ContextVar('current_run_id', default=None)


class ContextFilter(logging.Filter):
    """
    Adds context information to log records

    Injects turn, actor, phase, scenario, and run_id into every log record.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to log record"""
        record.turn = current_turn.get()
        record.actor = current_actor.get()
        record.phase = current_phase.get()
        record.scenario = current_scenario.get()
        record.run_id = current_run_id.get()
        return True


class JSONFormatter(logging.Formatter):
    """
    Formats log records as JSON for structured logging

    Useful for production environments and log aggregation systems.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        # Add context if present
        if hasattr(record, 'scenario') and record.scenario:
            log_data['scenario'] = record.scenario

        if hasattr(record, 'run_id') and record.run_id:
            log_data['run_id'] = record.run_id

        if hasattr(record, 'turn') and record.turn is not None:
            log_data['turn'] = record.turn

        if hasattr(record, 'actor') and record.actor:
            log_data['actor'] = record.actor

        if hasattr(record, 'phase') and record.phase:
            log_data['phase'] = record.phase

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, 'cost'):
            log_data['cost'] = record.cost

        if hasattr(record, 'tokens'):
            log_data['tokens'] = record.tokens

        if hasattr(record, 'model'):
            log_data['model'] = record.model

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Formats log records with colors for console output

    Makes logs more readable during development.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )

        # Build context string
        context_parts = []
        if hasattr(record, 'scenario') and record.scenario:
            context_parts.append(f"scenario={record.scenario}")

        if hasattr(record, 'turn') and record.turn is not None:
            context_parts.append(f"turn={record.turn}")

        if hasattr(record, 'actor') and record.actor:
            context_parts.append(f"actor={record.actor}")

        if hasattr(record, 'phase') and record.phase:
            context_parts.append(f"phase={record.phase}")

        context_str = f" [{', '.join(context_parts)}]" if context_parts else ""

        # Format the base message
        formatted = super().format(record)

        # Add context
        if context_str:
            formatted = f"{formatted}{context_str}"

        return formatted


def setup_logging(
    level: str = "INFO",
    format_type: str = "colored",
    log_file: Optional[Path] = None,
    enable_file_logging: bool = False,
) -> None:
    """
    Setup structured logging for Scenario Lab

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Formatter type ("colored", "json", "simple")
        log_file: Path to log file (if enable_file_logging=True)
        enable_file_logging: Whether to write logs to file
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Add context filter
    context_filter = ContextFilter()
    console_handler.addFilter(context_filter)

    # Choose formatter
    if format_type == "json":
        formatter = JSONFormatter()
    elif format_type == "colored":
        formatter = ColoredFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:  # simple
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if requested
    if enable_file_logging:
        if log_file is None:
            log_file = Path("logs/scenario-lab.log")

        # Create log directory
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler (10 MB max, 5 backups)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )
        file_handler.setLevel(logging.DEBUG)  # Always DEBUG for file
        file_handler.addFilter(context_filter)

        # File logs are always JSON for structured analysis
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)


def set_context(
    scenario: Optional[str] = None,
    run_id: Optional[str] = None,
    turn: Optional[int] = None,
    actor: Optional[str] = None,
    phase: Optional[str] = None,
) -> None:
    """
    Set logging context for current execution

    Args:
        scenario: Scenario name/ID
        run_id: Run identifier
        turn: Current turn number
        actor: Current actor name
        phase: Current execution phase
    """
    if scenario is not None:
        current_scenario.set(scenario)

    if run_id is not None:
        current_run_id.set(run_id)

    if turn is not None:
        current_turn.set(turn)

    if actor is not None:
        current_actor.set(actor)

    if phase is not None:
        current_phase.set(phase)


def clear_context() -> None:
    """Clear all logging context"""
    current_scenario.set(None)
    current_run_id.set(None)
    current_turn.set(None)
    current_actor.set(None)
    current_phase.set(None)


def log_cost(
    logger: logging.Logger,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost: float,
    phase: Optional[str] = None,
) -> None:
    """
    Log a cost event with structured data

    Args:
        logger: Logger instance
        model: Model name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        cost: Cost in USD
        phase: Optional phase name
    """
    extra = {
        'model': model,
        'tokens': {
            'input': input_tokens,
            'output': output_tokens,
            'total': input_tokens + output_tokens,
        },
        'cost': cost,
    }

    if phase:
        extra['phase'] = phase

    logger.info(
        f"LLM call: {model} ({input_tokens} in, {output_tokens} out) = ${cost:.4f}",
        extra=extra
    )


# Convenience function to get a logger with the module name
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a module

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
