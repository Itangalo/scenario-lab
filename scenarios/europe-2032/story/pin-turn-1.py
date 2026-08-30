"""Run turn 1 of Europe 2032 with both the event and the actor pinned.

Turn 1 is the story's fixed opening: `cyber_test_shot` alone, and the one
selected opening response in turn-01/opening.md. Neither is drawn, so neither is
asked for here -- the events step and the actor step are replaced, and
everything downstream (statements, rules, metrics, referee, summary) runs
normally against them. 1-events.json holds the single event,
1-event-evaluations.json records it as pinned with roll 0.0.

Run this once per arm. The opening response is arm-independent -- the turn-1
actor prompt hashed identically under all three variants -- but its resolution
is not: the rules patches differ on how fast `ai_capability` grows, and that
applies in turn 1. Sharing one base across arms would hand acceleration a
plateau-rate opening turn on the one metric the arms exist to separate.

Usage:
    python scenarios/europe-2032/story/pin-turn-1.py \
        scenarios/europe-2032/variants/acceleration.yaml \
        scenarios/europe-2032/story/turn-01/opening.md 20261231
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from scenario_lab import orchestrator as orch  # noqa: E402

scenario_path, pinned_path, seed = sys.argv[1], sys.argv[2], sys.argv[3]
PINNED = Path(pinned_path).read_text()
OPENING = "cyber_test_shot"

_orig_actors = orch.Orchestrator._run_actors_step
_orig_events = orch.Orchestrator._evaluate_events


def _pinned_events_step(self, turn):
    if turn != 1:
        return _orig_events(self, turn)
    triggered = [{"id": OPENING, "probability": 1.0, "emergent": False, "description": ""}]
    evaluations = [dict(triggered[0], triggered=True, pinned=True, roll=0.0)]
    print(f"  ✓ Event pinned: {OPENING}")
    self._record_occurrence(turn, OPENING, repeatable=False)
    return triggered, evaluations


def _pinned_actors_step(self, turn, triggered_events):
    if turn != 1:
        return _orig_actors(self, turn, triggered_events)
    outputs = {}
    for actor_id, actor in self.scenario.actors.items():
        print(f"  → {actor.name} (pinned)")
        outputs[actor_id] = PINNED
        actor.last_actions = PINNED
        if self.output_manager:
            self.output_manager.save_actor_output(turn, actor_id, PINNED)
    return outputs


orch.Orchestrator._evaluate_events = _pinned_events_step
orch.Orchestrator._run_actors_step = _pinned_actors_step

from scenario_lab.cli import main  # noqa: E402

sys.argv = ["cli", "run", scenario_path, "--turns", "1", "--seed", seed, "--no-progress"]
main()
