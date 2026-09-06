"""Pin one turn's events and actor output on a branched europe-2032 run.

Stage 2/3 blocks start from a reader's choice: the turn's events are fixed
(by a fixture run branched from the same path) and the actor response is the
selected option file. Everything after the pinned turn runs normally.

Usage:
    python scenarios/europe-2032/story/pin-turn.py \
        scenarios/europe-2032/runs/<path-run> 5 6 \
        scenarios/europe-2032/runs/<fixture-run>/turn-06/1-event-evaluations.json \
        scenarios/europe-2032/story/pool-06-A1/sample-06.md 9

Arguments: parent run dir, branch-from turn, pinned turn, events fixture
(fixture run's 1-event-evaluations.json for the pinned turn — only entries
with triggered=true are used), pinned actor file, total turns to run.

Seeds are never reused: every block draws a fresh random 64-bit seed,
recorded in config.json alongside the pin provenance.
"""

import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from scenario_lab import orchestrator as orch  # noqa: E402
from scenario_lab.orchestrator import run_simulation  # noqa: E402
from scenario_lab.output import OutputManager  # noqa: E402
from scenario_lab.resume import (  # noqa: E402
    create_branch,
    get_scenario_path_from_run,
    load_run_state,
    persist_scenario_state_at_turn,
    sync_summary_turn_state,
)

parent_dir = Path(sys.argv[1])
from_turn = int(sys.argv[2])
PIN_TURN = int(sys.argv[3])
fixture_file = Path(sys.argv[4])
PINNED_ACTOR = Path(sys.argv[5]).read_text(encoding="utf-8")
TOTAL_TURNS = int(sys.argv[6])

fixture = json.loads(fixture_file.read_text(encoding="utf-8"))
PINNED_TRIGGERED = [e for e in fixture if e.get("triggered")]

_orig_actors = orch.Orchestrator._run_actors_step
_orig_events = orch.Orchestrator._evaluate_events


def _pinned_events_step(self, turn):
    if turn != PIN_TURN:
        return _orig_events(self, turn)
    by_id = {e.id: e for e in self.scenario.events}
    triggered = []
    for entry in PINNED_TRIGGERED:
        record = dict(entry)
        record["triggered"] = True
        record["pinned"] = True
        record["roll"] = 0.0
        if not record.get("description") and not record.get("emergent"):
            definition = by_id.get(record["id"])
            if definition is not None:
                record["description"] = definition.description
        triggered.append(record)
        definition = by_id.get(record["id"])
        repeatable = definition.can_repeat if definition is not None else True
        self._record_occurrence(turn, record["id"], repeatable=repeatable)
    evaluations = [dict(record) for record in triggered]
    print(f"  Pinned events for turn {turn}: " + ", ".join(e["id"] for e in triggered))
    return triggered, evaluations


def _pinned_actors_step(self, turn, triggered_events):
    if turn != PIN_TURN:
        return _orig_actors(self, turn, triggered_events)
    outputs = {}
    for actor_id, actor in self.scenario.actors.items():
        print(f"  Actor {actor.name} (pinned)")
        outputs[actor_id] = PINNED_ACTOR
        actor.last_actions = PINNED_ACTOR
        if self.output_manager:
            self.output_manager.save_actor_output(turn, actor_id, PINNED_ACTOR)
    return outputs


orch.Orchestrator._evaluate_events = _pinned_events_step
orch.Orchestrator._run_actors_step = _pinned_actors_step

scenario_path = get_scenario_path_from_run(parent_dir)
output_base = scenario_path if scenario_path.is_dir() else scenario_path.parent

new_run_dir = create_branch(parent_dir, from_turn, output_base)
print(f"  Created branch: {new_run_dir.name}")

scenario, loaded_turn = load_run_state(new_run_dir, from_turn=from_turn)
assert loaded_turn == from_turn, f"branch loaded at {loaded_turn}, expected {from_turn}"

seed = random.getrandbits(64)
scenario.config.random_seed = seed
new_config = json.loads((new_run_dir / "config.json").read_text(encoding="utf-8"))
new_config["random_seed"] = seed
new_config.setdefault("metadata", {})["pinned_turn"] = PIN_TURN
new_config["metadata"]["pinned_events_fixture"] = str(fixture_file)
new_config["metadata"]["pinned_option"] = sys.argv[5]
(new_run_dir / "config.json").write_text(json.dumps(new_config, indent=2, ensure_ascii=False))
print(f"  Random seed: {seed}")

output_manager = OutputManager(scenario, output_base)
output_manager.run_dir = new_run_dir
persist_scenario_state_at_turn(new_run_dir, loaded_turn, scenario)
branch_point_metrics = {m.id: m.value for m in scenario.metrics.metrics.values()}
sync_summary_turn_state(new_run_dir, loaded_turn, branch_point_metrics)

results = run_simulation(
    scenario,
    num_turns=TOTAL_TURNS,
    output_manager=output_manager,
    start_turn=from_turn + 1,
)
output_manager.finalize_summary(results)
print(f"Results saved to: {new_run_dir}")
