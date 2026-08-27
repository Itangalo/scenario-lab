"""Sample an actor's choice many times under identical conditions.

A branch answers "what futures follow from here"; this answers the narrower
question "what would this actor have done, given exactly this situation". The
difference matters because the turn pipeline settles the world before the actor
speaks: ``_run_events_step`` runs first, and its LLM call proposes emergent
events even when the catalogue events are pinned with ``--force-event``. Ten
branches therefore give ten actors ten slightly different situations, and any
variation in their choices is confounded with that.

Here the actor prompt is built once and sent N times. The conditions are
identical by construction rather than by argument, and the prompt is persisted
alongside the samples so a reader can verify that for themselves.

For turn N >= 2 the situation comes from a turn that has already been
simulated: state is restored as of the end of turn N-1, and turn N's recorded
events are reused, so the prompt is the one that turn's actor actually saw.

Turn 1 is the opening move, where the actor acts on the scenario's initial
state rather than on any recorded turn. It can therefore be sampled from a
scenario or variant directly, before a single run exists, as well as from a run
that has already played it. Events are optional there: an authored world before
anything has happened is a legitimate situation, so turn 1 defaults to none
while turns after it require them.

``--events-from`` borrows another run's events for the same turn, which is how
a situation gets composed deliberately instead of being whatever the dice
produced.
"""

from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .llm import LLMResponse
from .models import Scenario
from .orchestrator import Orchestrator
from .resume import load_run_state


@dataclass
class ActorSample:
    """One sampled response, with the cost of producing it."""

    index: int
    content: str
    tokens: int
    cost_usd: float


@dataclass
class SamplingResult:
    """The shared prompt plus every sample drawn against it."""

    actor_id: str
    turn: int
    system_prompt: str
    user_prompt: str
    triggered_events: list[dict]
    samples: list[ActorSample]
    model: str
    temperature: float

    @property
    def prompt_hash(self) -> str:
        """Digest of the exact prompt every sample was drawn against."""
        payload = f"{self.system_prompt}\x00{self.user_prompt}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()[:16]

    @property
    def total_cost_usd(self) -> float:
        return sum(sample.cost_usd for sample in self.samples)

    @property
    def total_tokens(self) -> int:
        return sum(sample.tokens for sample in self.samples)


def is_run_dir(path: Path) -> bool:
    """True if the path is a run directory rather than a scenario."""
    return (
        path.is_dir()
        and (path / "config.json").exists()
        and path.parent.name == "runs"
    )


def load_triggered_events(
    run_dir: Path, turn: int, required: bool = True
) -> list[dict]:
    """Read the events recorded for a turn.

    Args:
        run_dir: Run directory holding the turn
        turn: Turn number
        required: Raise when the turn has no recorded events file. False for
            the opening move, where "nothing has happened yet" is a legitimate
            situation rather than missing data.

    Returns:
        The turn's triggered events, empty if the turn fired none

    Raises:
        ValueError: If the events file is missing while required, or malformed
    """
    events_file = run_dir / f"turn-{turn:02d}" / "1-events.json"
    if not events_file.exists():
        if not required:
            return []
        raise ValueError(
            f"Turn {turn} has no recorded events in {run_dir.name}. "
            "Sampling reuses a simulated turn's conditions, so that turn must "
            "already exist."
        )
    events = json.loads(events_file.read_text(encoding="utf-8"))
    if not isinstance(events, list):
        raise ValueError(f"Malformed events file: {events_file}")
    return events


def load_opening_state(target: Path, initial_state: Optional[Path] = None) -> Scenario:
    """Load a scenario at its initial state, as turn 1's actor sees it.

    Args:
        target: A run directory, or a scenario directory or variant YAML
        initial_state: Starting-state overrides to apply, for scenario targets

    Returns:
        The scenario before any turn has been played

    Raises:
        ValueError: If a run's recorded starting-state draw cannot be honoured
    """
    from .loader import apply_initial_state, load_initial_state, load_scenario

    if not is_run_dir(target):
        return load_scenario(target, initial_state=initial_state)

    # A run's opening state is its scenario source plus whatever starting-state
    # draw it was given, so a sampled turn 1 matches the world that run began in.
    from .resume import get_scenario_source_from_run

    scenario = load_scenario(get_scenario_source_from_run(target))

    if initial_state is not None:
        apply_initial_state(scenario, load_initial_state(initial_state))
        return scenario

    config = json.loads((target / "config.json").read_text(encoding="utf-8"))
    recorded = config.get("initial_state")
    if isinstance(recorded, dict):
        from .models import InitialState

        apply_initial_state(
            scenario,
            InitialState(
                metrics=dict(recorded.get("metrics") or {}),
                context=recorded.get("context") or "",
                notes=recorded.get("notes") or "",
                source=recorded.get("source"),
            ),
        )
    return scenario


def sample_actor(
    target: Path,
    turn: int,
    samples: int,
    actor_id: Optional[str] = None,
    events_from: Optional[Path] = None,
    initial_state: Optional[Path] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_concurrency: int = 4,
    on_sample=None,
) -> SamplingResult:
    """Draw an actor's choice repeatedly against one fixed situation.

    Args:
        target: Run directory whose turn supplies the situation, or -- for
            turn 1 only -- a scenario directory or variant YAML to sample the
            opening move from before any run exists
        turn: Turn to sample the actor step of. Turns after the first must
            already be simulated; turn 1 needs only the scenario
        samples: How many responses to draw
        actor_id: Which actor, defaulting to the only one when unambiguous
        events_from: Borrow this run's turn-N events instead of the target's
        initial_state: Starting-state overrides, for turn 1
        model: Override the actor model
        temperature: Override the sampling temperature
        max_concurrency: How many samples to draw at once
        on_sample: Called with each ActorSample as it lands, for incremental
            persistence

    Returns:
        The shared prompt and every sample drawn against it

    Raises:
        ValueError: If the target, turn, actor, or sample count is invalid
    """
    if samples < 1:
        raise ValueError(f"samples must be at least 1, got {samples}")
    if turn < 1:
        raise ValueError(f"turn must be at least 1, got {turn}")

    if turn == 1:
        # The opening move: the actor acts on the scenario's initial state,
        # which no recorded turn expresses.
        scenario = load_opening_state(target, initial_state=initial_state)
    else:
        if not is_run_dir(target):
            raise ValueError(
                f"Turn {turn} needs a run directory: only turn 1 can be sampled "
                f"from a scenario, since later turns act on a simulated past. "
                f"Got: {target}"
            )
        if initial_state is not None:
            raise ValueError(
                "--initial-state applies to turn 1 only; later turns take their "
                "state from the run."
            )
        # Everything settled through the end of the previous turn.
        scenario, _ = load_run_state(target, from_turn=turn - 1)

    # Turn 1 may legitimately have no events: an authored world before anything
    # has happened is a situation in its own right. Later turns must have them.
    triggered_events = load_triggered_events(
        events_from or target,
        turn,
        required=turn > 1 or events_from is not None,
    )

    actor_id = _resolve_actor(scenario, actor_id)

    if temperature is not None:
        scenario.config.llm.temperature = temperature
    if model is not None:
        from .cli import apply_model_override

        apply_model_override(scenario.config.llm, model)

    # Build through the real Orchestrator so prompts, model routing and cost
    # accounting match what a simulated turn would have done.
    orchestrator = Orchestrator(scenario)
    try:
        system_prompt, user_prompt = orchestrator.prompt_builder.build_actor_prompt(
            actor_id,
            turn,
            triggered_events,
            previous_actions=scenario.actors[actor_id].last_actions,
        )
        client = orchestrator.client_for_actor(actor_id)

        collected: list[ActorSample] = []

        def draw(index: int) -> tuple[int, LLMResponse]:
            return index, client.complete(system_prompt, user_prompt)

        workers = max(1, min(samples, max_concurrency))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(draw, i) for i in range(1, samples + 1)]
            for future in as_completed(futures):
                index, response = future.result()
                orchestrator._record_llm_call(turn, f"actor-sample:{actor_id}", response)
                sample = ActorSample(
                    index=index,
                    content=response.content,
                    **_usage_of(response),
                )
                collected.append(sample)
                if on_sample is not None:
                    on_sample(sample)

        collected.sort(key=lambda s: s.index)

        return SamplingResult(
            actor_id=actor_id,
            turn=turn,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            triggered_events=triggered_events,
            samples=collected,
            model=_actor_model(scenario, actor_id),
            temperature=scenario.config.llm.temperature,
        )
    finally:
        orchestrator.close()


def _resolve_actor(scenario: Scenario, actor_id: Optional[str]) -> str:
    """Pick the actor to sample, requiring a choice only when it is ambiguous."""
    available = list(scenario.actors.keys())
    if actor_id is None:
        if len(available) != 1:
            raise ValueError(
                f"Scenario has {len(available)} actors ({', '.join(available)}); "
                "name one with --actor."
            )
        return available[0]
    if actor_id not in scenario.actors:
        raise ValueError(
            f"Unknown actor '{actor_id}'. Available: {', '.join(available)}"
        )
    return actor_id


def _actor_model(scenario: Scenario, actor_id: str) -> str:
    """Name the model this actor is routed to, for the samples' index."""
    routes = scenario.config.llm.actors
    if isinstance(routes, dict):
        routes = routes.get(actor_id, scenario.config.llm.events)
    primary = routes[0] if isinstance(routes, list) else routes
    return str(primary)


def _usage_of(response: LLMResponse) -> dict:
    """Token and cost figures for one response, zeroed when unreported."""
    from .cost import CostCalculator

    usage = response.get_usage()
    if not usage:
        return {"tokens": 0, "cost_usd": 0.0}
    details = CostCalculator.calculate_cost(usage)
    return {
        "tokens": details.usage.total_tokens,
        "cost_usd": details.total_cost_usd,
    }


def write_samples(result: SamplingResult, output_dir: Path) -> None:
    """Persist the shared prompt, the samples, and an index describing both.

    The prompt is written first and kept beside the samples on purpose: it is
    the evidence that every sample answered the same question.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "prompt-system.md").write_text(result.system_prompt, encoding="utf-8")
    (output_dir / "prompt-user.md").write_text(result.user_prompt, encoding="utf-8")

    for sample in result.samples:
        (output_dir / f"sample-{sample.index:02d}.md").write_text(
            sample.content, encoding="utf-8"
        )

    index = {
        "actor": result.actor_id,
        "turn": result.turn,
        "model": result.model,
        "temperature": result.temperature,
        "prompt_hash": result.prompt_hash,
        "triggered_events": [event.get("id") for event in result.triggered_events],
        "samples": [
            {
                "index": sample.index,
                "file": f"sample-{sample.index:02d}.md",
                "tokens": sample.tokens,
                "cost_usd": round(sample.cost_usd, 6),
            }
            for sample in result.samples
        ],
        "total_tokens": result.total_tokens,
        "total_cost_usd": round(result.total_cost_usd, 6),
    }
    (output_dir / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
    )
