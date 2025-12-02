"""Output management for saving simulation results."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from .models import Scenario, TurnResult


class OutputManager:
    """Manages saving simulation results to disk."""

    def __init__(self, scenario: Scenario, base_path: Path):
        """Initialize output manager.

        Args:
            scenario: The scenario being run
            base_path: Base path to scenario directory (will create runs/ inside)
        """
        self.scenario = scenario
        self.base_path = Path(base_path)
        self.run_dir: Optional[Path] = None

    def start_run(self) -> Path:
        """Create a new run directory.

        Returns:
            Path to the created run directory
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.run_dir = self.base_path / "runs" / f"run-{timestamp}"
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Save config snapshot
        self._save_config()

        return self.run_dir

    def get_turn_dir(self, turn: int) -> Path:
        """Get turn directory path (creates if needed).

        Args:
            turn: Turn number

        Returns:
            Path to turn directory
        """
        if not self.run_dir:
            raise RuntimeError("Must call start_run() first")

        turn_dir = self.run_dir / f"turn-{turn:02d}"
        turn_dir.mkdir(exist_ok=True)
        return turn_dir

    def save_events(self, turn: int, triggered_events: list[dict]):
        """Save events for a turn immediately after determination.

        Args:
            turn: Turn number
            triggered_events: List of triggered events
        """
        turn_dir = self.get_turn_dir(turn)
        (turn_dir / "1-events.json").write_text(
            json.dumps(triggered_events, indent=2, ensure_ascii=False)
        )

    def save_actor_output(self, turn: int, actor_id: str, output: str):
        """Save single actor output immediately after generation.

        Args:
            turn: Turn number
            actor_id: Actor identifier
            output: Actor's markdown output
        """
        turn_dir = self.get_turn_dir(turn)
        actors_dir = turn_dir / "2-actors"
        actors_dir.mkdir(exist_ok=True)
        (actors_dir / f"{actor_id}.md").write_text(output, encoding="utf-8")

    def save_metric_rules(self, turn: int, rules: str):
        """Save metric rules immediately after generation.

        Args:
            turn: Turn number
            rules: Metric rules markdown
        """
        turn_dir = self.get_turn_dir(turn)
        (turn_dir / "3-metric-rules.md").write_text(rules, encoding="utf-8")

    def save_metrics_and_narrative(self, turn: int, metrics: dict, narrative: str):
        """Save metrics and narrative immediately after generation.

        Args:
            turn: Turn number
            metrics: Updated metrics dict
            narrative: World state narrative
        """
        turn_dir = self.get_turn_dir(turn)
        (turn_dir / "4-metrics.json").write_text(
            json.dumps(metrics, indent=2, ensure_ascii=False)
        )
        (turn_dir / "4-world-state.md").write_text(narrative, encoding="utf-8")

    def save_turn(self, result: TurnResult):
        """Save results from a single turn.

        Args:
            result: TurnResult containing all outputs for the turn

        Note: This method now delegates to individual save methods.
              For incremental writing, use the individual methods instead.
        """
        if not self.run_dir:
            raise RuntimeError("Must call start_run() first")

        turn_dir = self.run_dir / f"turn-{result.turn:02d}"
        turn_dir.mkdir(exist_ok=True)

        # 1. Events
        (turn_dir / "1-events.json").write_text(
            json.dumps(result.triggered_events, indent=2, ensure_ascii=False)
        )

        # 2. Actor outputs
        actors_dir = turn_dir / "2-actors"
        actors_dir.mkdir(exist_ok=True)
        for actor_id, output in result.actor_outputs.items():
            (actors_dir / f"{actor_id}.md").write_text(output, encoding="utf-8")

        # 3. Metric rules
        (turn_dir / "3-metric-rules.md").write_text(result.metric_rules, encoding="utf-8")

        # 4. Metrics
        (turn_dir / "4-metrics.json").write_text(
            json.dumps(result.metrics, indent=2, ensure_ascii=False)
        )

        # 5. World state narrative
        (turn_dir / "4-world-state.md").write_text(result.narrative, encoding="utf-8")

    def update_summary(self, current_turn: int, latest_metrics: dict):
        """Update summary after each turn (incremental).

        Args:
            current_turn: Current turn number
            latest_metrics: Metrics from the latest turn
        """
        if not self.run_dir:
            raise RuntimeError("Must call start_run() first")

        summary = {
            "scenario": self.scenario.config.name,
            "total_turns": current_turn,
            "final_metrics": latest_metrics,
            "occurred_events": list(self.scenario.occurred_events),
            "last_updated": datetime.now().isoformat(),
            "status": "running",
        }

        (self.run_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False)
        )

    def finalize_summary(self, results: list[TurnResult]):
        """Mark summary as complete after simulation finishes.

        Args:
            results: List of all TurnResults from the simulation
        """
        if not self.run_dir:
            raise RuntimeError("Must call start_run() first")

        summary = {
            "scenario": self.scenario.config.name,
            "total_turns": len(results),
            "final_metrics": results[-1].metrics if results else {},
            "occurred_events": list(self.scenario.occurred_events),
            "completed_at": datetime.now().isoformat(),
            "status": "completed",
        }

        (self.run_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False)
        )

    def save_summary(self, results: list[TurnResult]):
        """Save final summary of the simulation run.

        Args:
            results: List of all TurnResults from the simulation

        Note: This is kept for backward compatibility. Use finalize_summary() instead.
        """
        self.finalize_summary(results)

    def _save_config(self):
        """Save scenario configuration snapshot."""
        config = {
            "name": self.scenario.config.name,
            "description": self.scenario.config.description,
            "start_date": self.scenario.config.start_date,
            "time_scale": self.scenario.config.time_scale,
            "max_turns": self.scenario.config.max_turns,
            "actors": self.scenario.config.actor_ids,
            "llm": {
                "events": self.scenario.config.llm.events,
                "actors": self.scenario.config.llm.actors,
                "rules": self.scenario.config.llm.rules,
                "metrics": self.scenario.config.llm.metrics,
                "temperature": self.scenario.config.llm.temperature,
                "max_tokens": self.scenario.config.llm.max_tokens,
            },
        }
        (self.run_dir / "config.json").write_text(
            json.dumps(config, indent=2, ensure_ascii=False)
        )
