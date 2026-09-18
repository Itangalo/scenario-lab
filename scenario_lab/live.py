"""Live workshop mode: human teams play the actors from printed menus.

A live game alternates two commands per turn. ``live-menu`` rolls the turn's
events (same seeded dice as a simulated turn) and generates one short menu of
options per actor, written as printable handouts under ``turn-NN/live/``.
After the teams deliberate off-computer, ``live-resolve`` collects exactly one
pick per actor and runs the standard rules → metrics → referee → summary
chain with identical persistence. Human picks enter the pipeline as
``actor_outputs`` between the actor and rules steps; everything downstream is
untouched, so a live turn is an ordinary turn in the artifacts.
"""

import json
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .actor_sampling import is_run_dir, load_opening_state, load_triggered_events
from .models import Scenario, TurnResult

MENU_VERSION = 1
LIVE_RUN_PREFIX = "live-"
MENU_DIRNAME = "live"
MENU_FILENAME = "menu.json"

DIRECT_STRATEGY = "direct"
SAMPLE_DISTILL_STRATEGY = "sample-distill"
MENU_STRATEGIES = (DIRECT_STRATEGY, SAMPLE_DISTILL_STRATEGY)

_INDEX_SPEC = re.compile(r"^\s*(?:action|option|#)?\s*(\d+)\s*$", re.IGNORECASE)


class LiveError(ValueError):
    """A live-workshop precondition failure (missing menu, bad pick, ...)."""


class LiveCancelled(RuntimeError):
    """The facilitator aborted the interactive picker."""


@dataclass
class MenuOption:
    """One numbered option on an actor's menu."""

    index: int
    title: str
    text: str

    def to_dict(self) -> dict:
        return {"index": self.index, "title": self.title, "text": self.text}

    @staticmethod
    def from_dict(data: dict) -> "MenuOption":
        return MenuOption(
            index=int(data["index"]),
            title=str(data["title"]),
            text=str(data["text"]),
        )


@dataclass
class ActorMenu:
    """The generated menu for one actor and turn."""

    actor_id: str
    actor_name: str
    turn: int
    strategy: str
    options: list[MenuOption] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "turn": self.turn,
            "strategy": self.strategy,
            "options": [o.to_dict() for o in self.options],
        }

    @staticmethod
    def from_dict(data: dict) -> "ActorMenu":
        return ActorMenu(
            actor_id=str(data["actor_id"]),
            actor_name=str(data.get("actor_name", data["actor_id"])),
            turn=int(data["turn"]),
            strategy=str(data.get("strategy", DIRECT_STRATEGY)),
            options=[MenuOption.from_dict(o) for o in data.get("options", [])],
        )


@dataclass
class Pick:
    """One team's resolved choice: a menu option or free text."""

    kind: str  # "menu" or "free"
    title: str
    text: str
    index: Optional[int] = None


def live_dir(run_dir: Path, turn: int) -> Path:
    """Handout directory for a turn, created on demand."""
    path = run_dir / f"turn-{turn:02d}" / MENU_DIRNAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def menu_json_path(run_dir: Path, turn: int) -> Path:
    return live_dir(run_dir, turn) / MENU_FILENAME


def recorded_overrides(run_dir: Path, turn: int) -> list[str]:
    """Raw `--override` flags recorded with a turn's menus (empty if none)."""
    try:
        data = json.loads(menu_json_path(run_dir, turn).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    overrides = data.get("config_overrides", [])
    return [str(o) for o in overrides] if isinstance(overrides, list) else []


def read_menus(run_dir: Path, turn: int) -> dict[str, ActorMenu]:
    """Read the menus ``live-menu`` wrote for a turn.

    Raises:
        LiveError: If the turn has no menu yet (resolve before menu).
    """
    path = run_dir / f"turn-{turn:02d}" / MENU_DIRNAME / MENU_FILENAME
    if not path.exists():
        raise LiveError(
            f"Turn {turn} has no menu in {run_dir.name}. "
            "Run live-menu for this turn first."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        menus = {
            actor_id: ActorMenu.from_dict(entry)
            for actor_id, entry in data["menus"].items()
        }
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
        raise LiveError(f"Malformed menu file {path}: {e}")
    if not menus:
        raise LiveError(f"Malformed menu file {path}: no menus recorded")
    return menus


def write_menus(
    run_dir: Path,
    turn: int,
    menus: dict[str, ActorMenu],
    strategy: str,
    max_options: int = 6,
    samples: int = 4,
    config_overrides: Optional[list[str]] = None,
) -> Path:
    """Persist menus machine-readably for shorthand resolution. Returns path.

    The generation params ride along so ``live-resolve`` can chain the next
    turn's menus with identical settings and no new facilitator input.
    ``config_overrides`` (raw ``--override key=value`` flags) ride along for
    the same reason: later turns run in separate processes and must resolve
    under the same settings (e.g. output_language).
    """
    payload = {
        "version": MENU_VERSION,
        "turn": turn,
        "strategy": strategy,
        "max_options": max_options,
        "samples": samples,
        "config_overrides": list(config_overrides or []),
        "menus": {aid: menu.to_dict() for aid, menu in menus.items()},
    }
    path = menu_json_path(run_dir, turn)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def resolve_pick(spec: str, menu: ActorMenu) -> Pick:
    """Resolve one pick spec against a menu.

    ``"3"``, ``"action 3"``, ``"option 3"`` and ``"#3"`` select the numbered
    option; anything else is free text (the facilitator's escape hatch for a
    team that went off-menu). Exactly one option per team – ranges and lists
    are rejected rather than guessed at.

    Raises:
        LiveError: On an empty spec or an out-of-range index.
    """
    text = (spec or "").strip()
    if not text:
        raise LiveError(f"Empty pick for {menu.actor_name}: choose 1-{len(menu.options)}")
    match = _INDEX_SPEC.match(text)
    if match:
        index = int(match.group(1))
        for option in menu.options:
            if option.index == index:
                return Pick(kind="menu", title=option.title, text=option.text, index=index)
        raise LiveError(
            f"{menu.actor_name}: option {index} is out of range "
            f"(menu holds 1-{len(menu.options)})"
        )
    # A digit-only list ("1, 2", "1 and 3") reads as an attempted multi-pick,
    # not prose – reject it rather than file it as a nonsense free-text move.
    tokens = re.split(r"[\s,;+/]+", text.lower())
    if any(t.isdigit() for t in tokens) and all(
        t.isdigit() or t in {"and", "or", "&", "#"} for t in tokens
    ):
        raise LiveError(
            f"{menu.actor_name}: choose exactly one option "
            f"(1-{len(menu.options)}), not several."
        )
    return Pick(kind="free", title="Chosen action", text=text)


def wrap_human_action(title: str, text: str, has_store_tables: bool) -> str:
    """Wrap a team's pick into a minimal valid actor document.

    The picked text rides verbatim as ``## Actions``; statement changes are
    omitted (absence means the ledger carries forward untouched), and a no-op
    store section is included only for scenarios that declare store tables,
    where an absent section would be recorded as a fault.
    """
    lines = ["## Actions", "", f"### {title}", "", text.strip(), ""]
    if has_store_tables:
        lines += ["## Store changes", "", "No changes.", ""]
    return "\n".join(lines)


def has_store_tables(scenario: Scenario) -> bool:
    """Whether the scenario declares persistent-state tables.

    The loader builds an empty store config even when undeclared, so the
    check is for actual tables rather than a non-None config.
    """
    store = scenario.config.store
    return store is not None and bool(getattr(store, "tables", {}))


def parse_menu_json(content: str, max_options: int, actor_name: str) -> list[MenuOption]:
    """Parse and validate a menu response. Fails loud, never invents options.

    Raises:
        LiveError: If the response is not a non-empty JSON array of
            {title, text} objects. Over-long menus are truncated to
            ``max_options``; everything else is an error.
    """
    text = content.strip()
    fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # A bare array buried in prose still parses; anything else is a miss.
        array = re.search(r"\[.*\]", text, re.DOTALL)
        if not array:
            raise LiveError(
                f"Menu for {actor_name} is not a JSON array – regenerate it."
            )
        try:
            parsed = json.loads(array.group(0))
        except json.JSONDecodeError:
            raise LiveError(
                f"Menu for {actor_name} is not a JSON array – regenerate it."
            )
    if not isinstance(parsed, list) or not parsed:
        raise LiveError(f"Menu for {actor_name} is empty – regenerate it.")
    options = []
    for i, entry in enumerate(parsed[:max_options], start=1):
        if not isinstance(entry, dict) or not str(entry.get("title", "")).strip():
            raise LiveError(
                f"Menu for {actor_name} has a malformed option {i} – regenerate it."
            )
        options.append(
            MenuOption(
                index=i,
                title=str(entry["title"]).strip(),
                text=str(entry.get("text", "")).strip() or str(entry["title"]).strip(),
            )
        )
    return options


def generate_menu(
    orchestrator,
    actor_id: str,
    turn: int,
    triggered_events: list[dict],
    max_options: int,
    strategy: str = DIRECT_STRATEGY,
    samples: int = 4,
) -> ActorMenu:
    """Generate one actor's menu with the given strategy.

    ``direct`` asks for options outright (one call – fastest for a live game);
    ``sample-distill`` draws ``samples`` free-form actor drafts against the
    fixed situation first, then distills them into a menu. Both paths judge in
    the LLM; Python only parses and validates.
    """
    if strategy not in MENU_STRATEGIES:
        raise LiveError(
            f"Unknown menu strategy '{strategy}': choose from {', '.join(MENU_STRATEGIES)}"
        )
    actor = orchestrator.scenario.actors[actor_id]
    client = orchestrator.client_for_actor(actor_id)

    samples_text: Optional[list[str]] = None
    if strategy == SAMPLE_DISTILL_STRATEGY:
        if samples < 1:
            raise LiveError(f"samples must be at least 1, got {samples}")
        print(f"  … {actor.name}: sampling {samples} drafts (waiting for the model)...",
              flush=True)
        samples_text = []
        for _ in range(samples):
            system, user = orchestrator.prompt_builder.build_actor_prompt(
                actor_id,
                turn,
                triggered_events,
                previous_actions=actor.last_actions,
            )
            response = client.complete(system, user)
            orchestrator._record_llm_call(turn, f"menu-sample:{actor_id}", response)
            samples_text.append(response.content)

    system, user = orchestrator.prompt_builder.build_live_menu_prompt(
        actor_id, turn, triggered_events, max_options, samples_text=samples_text
    )
    print(f"  … {actor.name}: requesting options (waiting for the model)...",
          flush=True)
    response = client.complete(system, user)
    orchestrator._record_llm_call(turn, f"menu:{actor_id}", response)
    try:
        options = parse_menu_json(response.content, max_options, actor.name)
    except LiveError:
        print(f"  … {actor.name}: retrying as strict JSON (waiting for the model)...",
              flush=True)
        retry = client.complete(
            system, user + "\n\nReturn ONLY the JSON array, no other text."
        )
        orchestrator._record_llm_call(turn, f"menu:{actor_id}", retry)
        options = parse_menu_json(retry.content, max_options, actor.name)
    return ActorMenu(
        actor_id=actor_id,
        actor_name=actor.name,
        turn=turn,
        strategy=strategy,
        options=options,
    )


def render_briefing(
    scenario: Scenario,
    turn: int,
    time_period: str,
    triggered_events: list[dict],
) -> str:
    """Render the printable world-state handout for a turn."""
    lines = [
        f"# Workshop briefing – turn {turn} ({time_period})",
        "",
        scenario.world_state.narrative.strip(),
        "",
        "## World metrics",
        "",
        "| Metric | Value | Range | Unit |",
        "| --- | --- | --- | --- |",
    ]
    for metric in scenario.metrics.metrics.values():
        lines.append(
            f"| {metric.id} | {metric.value:g} "
            f"| {metric.min_value:g}–{metric.max_value:g} | {metric.unit or '–'} |"
        )
    lines += ["", "## Events this turn", ""]
    if triggered_events:
        for event in triggered_events:
            desc = event.get("description", "")
            lines.append(f"- **{event.get('id')}**" + (f": {desc}" if desc else ""))
    else:
        lines.append("No special events occur this turn.")
    lines += ["", "## Teams", ""]
    for actor_id, actor in scenario.actors.items():
        lines.append(f"- **{actor.name}** (`{actor_id}`)")
    lines.append("")
    return "\n".join(lines)


def render_actor_handout(
    menu: ActorMenu, time_period: str, metrics_lines: list[str]
) -> str:
    """Render one team's printable menu sheet."""
    lines = [
        f"# {menu.actor_name} – turn {menu.turn} ({time_period})",
        "",
        "Reference (shared world metrics):",
        "",
    ]
    lines += [f"- {line}" for line in metrics_lines] if metrics_lines else ["- (see briefing)"]
    lines += ["", "## Your options – choose exactly ONE", ""]
    for option in menu.options:
        lines += [f"### {option.index}. {option.title}", "", option.text, ""]
    lines += [
        "Discuss with your team, negotiate with the other teams, then report "
        "your choice (a number, or your own wording) to the workshop leader.",
        "",
    ]
    return "\n".join(lines)


def write_handouts(
    scenario: Scenario,
    run_dir: Path,
    turn: int,
    time_period: str,
    triggered_events: list[dict],
    menus: dict[str, ActorMenu],
) -> list[Path]:
    """Write briefing.md plus one menu sheet per team. Returns written paths."""
    directory = live_dir(run_dir, turn)
    paths = []
    briefing = directory / "briefing.md"
    briefing.write_text(
        render_briefing(scenario, turn, time_period, triggered_events),
        encoding="utf-8",
    )
    paths.append(briefing)
    metrics_lines = [
        f"{m.id}: {m.value:g}" for m in scenario.metrics.metrics.values()
    ]
    for actor_id in scenario.actors:
        sheet = directory / f"menu-{actor_id}.md"
        sheet.write_text(
            render_actor_handout(menus[actor_id], time_period, metrics_lines),
            encoding="utf-8",
        )
        paths.append(sheet)
    return paths


def open_live_state(
    target: Path, turn: int, initial_state: Optional[Path] = None
) -> tuple[Scenario, Optional[Path]]:
    """Load the state a live turn acts on.

    A run target replays its own history (turn 1 replays the opening state
    including any recorded starting-state draw); a scenario target is allowed
    for turn 1 only and means "start a new live game", returning None as the
    run dir so the caller creates one.

    Raises:
        LiveError: On a scenario target past turn 1, or unrestorable history.
    """
    from .loader import load_scenario

    if turn < 1:
        raise LiveError(f"turn must be at least 1, got {turn}")
    if is_run_dir(target):
        if initial_state is not None:
            raise LiveError("--initial-state applies to a scenario target only")
        if turn == 1:
            return load_opening_state(target), target
        from .resume import load_run_state

        try:
            scenario, _ = load_run_state(target, from_turn=turn - 1)
        except ValueError as e:
            raise LiveError(str(e))
        return scenario, target
    if turn != 1:
        raise LiveError(
            f"Turn {turn} needs a run directory: only turn 1 can start from a "
            f"scenario, since later turns act on a simulated past. Got: {target}"
        )
    return load_scenario(target, initial_state=initial_state), None


def read_run_seed(run_dir: Path) -> Optional[int]:
    """Read the dice seed recorded in a run's config.json, if any."""
    try:
        config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    seed = config.get("random_seed")
    return seed if isinstance(seed, int) else None


def attach_output_manager(scenario: Scenario, run_dir: Path):
    """Attach an OutputManager to an existing run directory (resume pattern)."""
    from .output import OutputManager

    output_manager = OutputManager(scenario, run_dir.parent.parent)
    output_manager.run_dir = run_dir
    return output_manager


def mark_live_run(run_dir: Path) -> None:
    """Stamp a run's config.json as a live workshop game."""
    path = run_dir / "config.json"
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    config["live"] = True
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def is_live_run(run_dir: Path) -> bool:
    """Whether a run directory is marked as a live workshop game."""
    try:
        config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(isinstance(config, dict) and config.get("live"))


def ensure_turn_events(orchestrator, output_manager, run_dir: Path, turn: int) -> list[dict]:
    """Return turn N's triggered events, rolling the dice only once.

    A re-run ``live-menu`` reuses the recorded events so the teams' situation
    cannot silently change under a regenerated menu.
    """
    try:
        return load_triggered_events(run_dir, turn, required=True)
    except ValueError:
        pass
    print(f"Rolling events for turn {turn} (waiting for the model)...")
    triggered = orchestrator._run_events_step(turn)
    output_manager.save_events(turn, triggered)
    print(f"  → {len(triggered)} events triggered")
    return triggered


def run_menu_turn(
    scenario: Scenario,
    output_manager,
    run_dir: Path,
    turn: int,
    max_options: int = 6,
    strategy: str = DIRECT_STRATEGY,
    samples: int = 4,
    llm_client=None,
    config_overrides: Optional[list[str]] = None,
) -> dict[str, ActorMenu]:
    """Roll events (once) and generate every actor's menu for a live turn.

    Menus generate concurrently across actors; each is persisted to
    ``turn-NN/live/`` (menu.json plus printable sheets) as it lands, and the
    invocation's costs merge into the run's costs.json. ``llm_client`` is a
    test seam (a real run passes None and builds routers from config).
    """
    from .loader import get_time_period
    from .orchestrator import Orchestrator

    if max_options < 1:
        raise LiveError(f"max_options must be at least 1, got {max_options}")

    # A run with menus is a live game. Mark it here rather than only in the
    # CLI handler, so every menu-bearing run reads as one downstream
    # (notably the integrity checker's pending-turn leniency).
    mark_live_run(run_dir)

    orchestrator = Orchestrator(
        scenario, llm_client=llm_client, output_manager=output_manager
    )
    try:
        if not (run_dir / "summary.json").exists():
            output_manager.init_summary()
        triggered_events = ensure_turn_events(
            orchestrator, output_manager, run_dir, turn
        )
        actor_ids = list(scenario.actors.keys())
        menus: dict[str, ActorMenu] = {}

        def _generate(actor_id: str) -> ActorMenu:
            return generate_menu(
                orchestrator,
                actor_id,
                turn,
                triggered_events,
                max_options,
                strategy=strategy,
                samples=samples,
            )

        if len(actor_ids) > 1:
            with ThreadPoolExecutor(
                max_workers=min(len(actor_ids), 4)
            ) as executor:
                futures = {
                    executor.submit(_generate, aid): aid for aid in actor_ids
                }
                for future in as_completed(futures):
                    menu = future.result()
                    menus[menu.actor_id] = menu
                    print(f"  → {menu.actor_name}: {len(menu.options)} options")
            menus = {aid: menus[aid] for aid in actor_ids}
        else:
            for actor_id in actor_ids:
                menu = _generate(actor_id)
                menus[actor_id] = menu
                print(f"  → {menu.actor_name}: {len(menu.options)} options")

        write_menus(
            run_dir, turn, menus, strategy, max_options, samples,
            config_overrides=config_overrides,
        )
        time_period = get_time_period(
            scenario.config.start_date, turn, scenario.config.time_scale
        )
        write_handouts(
            scenario, run_dir, turn, time_period, triggered_events, menus
        )
        output_manager.save_costs(orchestrator.get_run_costs(), merge_existing=True)
        return menus
    finally:
        orchestrator.close()


def _show_menu_headers(menu: ActorMenu) -> None:
    """Print one team's options as headers only – details are on paper."""
    print(f"\n--- {menu.actor_name} ---")
    for option in menu.options:
        print(f"  {option.index}. {option.title}")
    print("  (details are on the printed sheet)")


def _match_actor(token: str, order: list[str], menus: dict[str, ActorMenu]) -> Optional[str]:
    """Match a confirm-phase redo token to an actor: number, id, or name."""
    token = token.strip().lower()
    if token.isdigit():
        idx = int(token) - 1
        if 0 <= idx < len(order):
            return order[idx]
        return None
    for actor_id in order:
        if token in {actor_id.lower(), menus[actor_id].actor_name.lower()}:
            return actor_id
    return None


def pick_all(
    menus: dict[str, ActorMenu],
    given: dict[str, Pick],
    interactive: bool = True,
    input_fn=input,
) -> dict[str, Pick]:
    """Collect the missing picks through the interactive picker.

    Already-given picks pass through untouched. Each missing team is shown
    its option headers (descriptions live on the printed sheet); the
    facilitator answers with a number (or option N) or free text for an
    off-menu move. ``back`` steps to the previous team and clears its pick
    for re-entry, ``q`` aborts the whole resolve. A final summary asks for
    confirmation, with any team redoable by number, id, or name.

    Raises:
        LiveError: When non-interactive and picks are missing.
        LiveCancelled: When the facilitator quits.
    """
    picks = dict(given)
    order = list(menus)
    if not interactive:
        missing = [aid for aid in order if aid not in picks]
        if missing:
            raise LiveError(
                "Missing picks for: " + ", ".join(missing) + ". Pass "
                "--actor-action actor_id=pick for each, or run interactively."
            )
        return picks

    def _walk_from(start: int) -> None:
        idx = start
        while idx < len(order) and order[idx] in picks:
            idx += 1
        while idx < len(order):
            actor_id = order[idx]
            menu = menus[actor_id]
            _show_menu_headers(menu)
            try:
                answer = input_fn(
                    f"{menu.actor_name} chooses "
                    f"[1-{len(menu.options)} or free text, back/q]: "
                )
            except EOFError:
                raise LiveCancelled("input closed – resolve aborted")
            command = answer.strip().lower()
            if command in {"q", "quit"}:
                raise LiveCancelled("facilitator aborted the resolve")
            if command == "back":
                if idx == 0:
                    print("  Already at the first team.")
                    continue
                prev = order[idx - 1]
                if prev in picks:
                    del picks[prev]
                    print(f"  {menus[prev].actor_name}'s pick cleared – re-enter below.")
                idx -= 1
                continue
            try:
                picks[actor_id] = resolve_pick(answer, menu)
            except LiveError as e:
                print(f"  {e} – try again.")
                continue
            idx += 1
            while idx < len(order) and order[idx] in picks:
                idx += 1

    _walk_from(0)

    while True:
        print("\n--- Picks ---")
        for num, actor_id in enumerate(order, start=1):
            pick = picks[actor_id]
            shown = (
                f"option {pick.index} ({pick.title})"
                if pick.kind == "menu"
                else f"free text: {pick.text}"
            )
            print(f"  {num}. {menus[actor_id].actor_name}: {shown}")
        try:
            answer = input_fn(
                "Accept these picks? [Y = yes, team number/name = redo, q = abort]: "
            )
        except EOFError:
            raise LiveCancelled("input closed – resolve aborted")
        command = answer.strip().lower()
        if command in {"", "y", "yes"}:
            return picks
        if command in {"q", "quit"}:
            raise LiveCancelled("facilitator aborted the resolve")
        redo = _match_actor(command, order, menus)
        if redo is None:
            print("  No such team – answer Y, a team number/name, or q.")
            continue
        del picks[redo]
        print(f"  Re-entering {menus[redo].actor_name}.")
        _walk_from(order.index(redo))


def parse_actor_action_specs(raw: Optional[list[str]]) -> dict[str, str]:
    """Parse repeatable ``--actor-action actor=pick`` flags.

    Raises:
        LiveError: On a flag without exactly one ``=`` or an empty side.
    """
    specs: dict[str, str] = {}
    for item in raw or []:
        if item.count("=") != 1:
            raise LiveError(
                f"Invalid --actor-action '{item}': use 'actor_id=pick' "
                "(e.g. 'eu=3' or 'us-gov=we sign the accord')."
            )
        actor_id, spec = item.split("=", 1)
        actor_id, spec = actor_id.strip(), spec.strip()
        if not actor_id or not spec:
            raise LiveError(
                f"Invalid --actor-action '{item}': actor and pick must both be non-empty."
            )
        specs[actor_id] = spec
    return specs


def run_resolve_turn(
    run_dir: Path,
    turn: int,
    specs: dict[str, str],
    interactive: bool = True,
    model_override: Optional[str] = None,
    log_llm_io: bool = False,
    llm_client=None,
    auto_menu: bool = True,
    input_fn=input,
) -> TurnResult:
    """Resolve a live turn from the teams' picks.

    Loads the recorded menu (picks are meaningless without the printed
    sheets), resolves every actor to exactly one pick – missing actors are
    collected through the interactive picker when allowed – wraps each pick
    into a minimal valid actor document, and runs the standard rules →
    metrics → referee → summary chain with identical persistence.

    When ``auto_menu`` holds (default), the next turn's menus generate
    immediately with the recorded menu settings, so the facilitator's next
    step is printing handouts rather than running another command. Skipped
    past ``max_turns`` or when a termination condition ends the run.
    """
    from .cli import apply_config_overrides, apply_model_override
    from .loader import get_time_period
    from .orchestrator import Orchestrator

    menus = read_menus(run_dir, turn)
    scenario, _ = open_live_state(run_dir, turn)
    seed = read_run_seed(run_dir)
    if seed is not None:
        scenario.config.random_seed = seed
    if model_override:
        apply_model_override(scenario.config.llm, model_override)
    # Re-apply the game's config overrides (recorded in menu.json): this
    # process loaded the scenario fresh from YAML, so without this the
    # resolve would silently drop settings the menus were generated with
    # (e.g. output_language).
    apply_config_overrides(scenario, recorded_overrides(run_dir, turn))
    if log_llm_io:
        scenario.config.logging.llm_io = True

    actor_ids = list(scenario.actors.keys())
    unknown = sorted(set(specs) - set(actor_ids))
    if unknown:
        raise LiveError(
            f"Unknown actor(s): {', '.join(unknown)} "
            f"(this run has: {', '.join(actor_ids)})"
        )
    menu_missing = sorted(set(actor_ids) - set(menus))
    if menu_missing:
        raise LiveError(
            f"No menu recorded for: {', '.join(menu_missing)}. "
            "Regenerate with live-menu before resolving."
        )

    picks: dict[str, Pick] = {}
    for actor_id, spec in specs.items():
        try:
            picks[actor_id] = resolve_pick(spec, menus[actor_id])
        except LiveError as e:
            raise LiveError(str(e))

    missing = [aid for aid in actor_ids if aid not in picks]
    if missing:
        if not interactive:
            raise LiveError(
                "Missing picks for: " + ", ".join(missing) + ". Pass "
                "--actor-action actor_id=pick for each, or run interactively."
            )
        picks.update(pick_all(menus, picks, input_fn=input_fn))

    output_manager = attach_output_manager(scenario, run_dir)
    orchestrator = Orchestrator(
        scenario, llm_client=llm_client, output_manager=output_manager
    )
    try:
        triggered_events = load_triggered_events(run_dir, turn, required=True)
        store_tables = has_store_tables(scenario)

        print(f"Resolving turn {turn} from team picks...")
        actor_outputs: dict[str, str] = {}
        for actor_id in actor_ids:
            pick = picks[actor_id]
            document = wrap_human_action(pick.title, pick.text, store_tables)
            actor_outputs[actor_id] = document
            scenario.actors[actor_id].last_actions = document
            output_manager.save_actor_output(turn, actor_id, document)
            chosen = f"option {pick.index}" if pick.kind == "menu" else "free text"
            print(f"  → {scenario.actors[actor_id].name}: {chosen}")

        orchestrator._process_statement_changes(turn, actor_outputs, triggered_events)
        orchestrator._process_store_changes(turn, actor_outputs)

        print("  … Updating metric rules (waiting for the model)...", flush=True)
        new_rules = orchestrator._run_rules_step(turn, actor_outputs, triggered_events)
        scenario.metric_rules = new_rules
        output_manager.save_metric_rules(turn, new_rules)

        print("  … Updating metrics and narrative (waiting for the model)...", flush=True)
        new_metrics, narrative, notepad = orchestrator._run_metrics_step(
            turn, actor_outputs, triggered_events
        )
        output_manager.save_metrics_and_narrative(turn, new_metrics, narrative)
        output_manager.save_notepad(turn, notepad)
        output_manager.update_summary(turn, new_metrics)

        if scenario.constitution:
            print("  … Checking constitution (waiting for the model)...", flush=True)
            new_metrics, narrative = (
                orchestrator._run_constitutional_referee_step(
                    turn, new_metrics, narrative, notepad=notepad
                )
            )
            output_manager.save_metrics_and_narrative(turn, new_metrics, narrative)
            output_manager.update_summary(turn, new_metrics)

        print("  … Summarizing the turn (waiting for the model)...", flush=True)
        new_summary = orchestrator._run_summarization_step(turn, narrative)
        output_manager.save_historical_summary(turn, new_summary)

        time_period = get_time_period(
            scenario.config.start_date, turn, scenario.config.time_scale
        )
        orchestrator._update_scenario_state(
            new_metrics, narrative, new_summary, notepad, turn, time_period
        )

        triggered = orchestrator.check_termination()
        if triggered is not None:
            detail = f" – {triggered.description}" if triggered.description else ""
            print(f"\n■ Run ended at turn {turn}: {triggered.id}{detail}")
            output_manager.record_termination(turn, triggered)

        output_manager.save_costs(orchestrator.get_run_costs(), merge_existing=True)

        result = TurnResult(
            turn=turn,
            time_period=time_period,
            triggered_events=triggered_events,
            actor_outputs=actor_outputs,
            metric_rules=new_rules,
            metrics=new_metrics,
            narrative=narrative,
            notepad=notepad,
        )

        if auto_menu and triggered is None:
            _chain_next_menus(
                scenario,
                output_manager,
                run_dir,
                turn,
                menus,
                llm_client=llm_client,
            )

        return result
    finally:
        orchestrator.close()


def _chain_next_menus(
    scenario: Scenario,
    output_manager,
    run_dir: Path,
    resolved_turn: int,
    menus: dict[str, ActorMenu],
    llm_client=None,
) -> Optional[dict[str, ActorMenu]]:
    """Generate the next turn's menus right after a resolve, if any remain.

    Reuses the recorded menu settings so no new facilitator input is needed.
    Returns the next menus, or None past ``max_turns``.
    """
    from .loader import get_time_period
    from .orchestrator import Orchestrator

    next_turn = resolved_turn + 1
    if next_turn > scenario.config.max_turns:
        print(f"\nScenario complete after turn {resolved_turn} – no further menus.")
        return None

    menu_file = menu_json_path(run_dir, resolved_turn)
    strategy = DIRECT_STRATEGY
    max_options = 6
    samples = 4
    try:
        recorded = json.loads(menu_file.read_text(encoding="utf-8"))
        strategy = str(recorded.get("strategy", strategy))
        max_options = int(recorded.get("max_options", max_options))
        samples = int(recorded.get("samples", samples))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        recorded = {}
    chained_overrides = recorded.get("config_overrides", [])
    if not isinstance(chained_overrides, list):
        chained_overrides = []

    print(f"\nPreparing turn {next_turn} menus ({strategy}) – no input needed...")
    next_orchestrator = Orchestrator(
        scenario, llm_client=llm_client, output_manager=output_manager
    )
    try:
        triggered_events = ensure_turn_events(
            next_orchestrator, output_manager, run_dir, next_turn
        )
        actor_ids = list(scenario.actors.keys())
        next_menus: dict[str, ActorMenu] = {}
        for actor_id in actor_ids:
            menu = generate_menu(
                next_orchestrator,
                actor_id,
                next_turn,
                triggered_events,
                max_options,
                strategy=strategy,
                samples=samples,
            )
            next_menus[actor_id] = menu
            print(f"  → {menu.actor_name}: {len(menu.options)} options")
        write_menus(
            run_dir, next_turn, next_menus, strategy, max_options, samples,
            config_overrides=chained_overrides,
        )
        time_period = get_time_period(
            scenario.config.start_date, next_turn, scenario.config.time_scale
        )
        write_handouts(
            scenario, run_dir, next_turn, time_period, triggered_events, next_menus
        )
        output_manager.save_costs(
            next_orchestrator.get_run_costs(), merge_existing=True
        )
        return next_menus
    finally:
        next_orchestrator.close()


# ---------------------------------------------------------------------------
# Launcher: finding live-ready scenarios and games
# ---------------------------------------------------------------------------


@dataclass
class LiveScenario:
    """A scenario directory ready for live play (declares a workshop: block)."""

    path: Path
    name: str


@dataclass
class LiveRun:
    """An existing live game and where it stands."""

    run_dir: Path
    scenario_name: str
    completed_turns: Optional[int]  # highest completed turn; None if unreadable
    pending_turn: Optional[int]  # newest turn with menus but no resolution


def find_live_scenarios(scenarios_root: Path) -> list[LiveScenario]:
    """List scenario directories built for live runs.

    Live-ready means the scenario.yaml declares a ``workshop:`` block – the
    same block that tunes generated language for the room, so any scenario
    prepared for an audience shows up here and simulation-only scenarios do
    not. Read with plain YAML parsing (no full load), sorted by name.
    """
    found: list[LiveScenario] = []
    if not scenarios_root.is_dir():
        return found
    import yaml

    for child in sorted(scenarios_root.iterdir()):
        config_file = child / "scenario.yaml"
        if not child.is_dir() or not config_file.exists():
            continue
        try:
            data = yaml.safe_load(config_file.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            continue
        if not isinstance(data, dict) or "workshop" not in data:
            continue
        found.append(
            LiveScenario(path=child, name=str(data.get("name") or child.name))
        )
    return found


def turn_numbers(run_dir: Path) -> list[int]:
    """Sorted turn numbers present as turn-NN directories, whatever they hold."""
    turns = []
    for child in run_dir.iterdir():
        if not child.is_dir() or not child.name.startswith("turn-"):
            continue
        try:
            turns.append(int(child.name.split("-")[1]))
        except (IndexError, ValueError):
            continue
    return sorted(turns)


def pending_live_turns(run_dir: Path) -> set[int]:
    """Turns holding menus but no resolution (teams still deliberating)."""
    pending = set()
    for turn in turn_numbers(run_dir):
        turn_dir = run_dir / f"turn-{turn:02d}"
        if (turn_dir / MENU_DIRNAME / MENU_FILENAME).exists() and not (
            (turn_dir / "2-actors").is_dir()
            and (turn_dir / "4-metrics.json").exists()
        ):
            pending.add(turn)
    return pending


def newest_pending_turn(run_dir: Path) -> Optional[int]:
    """The newest menu-without-resolution turn, if any."""
    pending = pending_live_turns(run_dir)
    return max(pending) if pending else None


def completed_turns(run_dir: Path) -> Optional[int]:
    """Highest fully completed turn, or None when the run is unreadable."""
    from .resume import detect_last_turn

    try:
        return detect_last_turn(run_dir)
    except (ValueError, OSError):
        return None


def find_live_runs(scenario_path: Path) -> list[LiveRun]:
    """Existing live games for a scenario, newest first."""
    runs_dir = scenario_path / "runs"
    if not runs_dir.is_dir():
        return []
    try:
        name = scenario_path.name
        candidates = sorted(
            (
                d
                for d in runs_dir.iterdir()
                if d.is_dir() and d.name.startswith(LIVE_RUN_PREFIX)
            ),
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return []
    runs = []
    for run_dir in candidates:
        runs.append(
            LiveRun(
                run_dir=run_dir,
                scenario_name=name,
                completed_turns=completed_turns(run_dir),
                pending_turn=newest_pending_turn(run_dir),
            )
        )
    return runs


def ask_choice(prompt: str, options: list[str], input_fn=input) -> int:
    """Numbered interactive choice. Returns the option index.

    Raises:
        LiveCancelled: On q/quit or closed input.
    """
    print(f"\n{prompt}")
    for num, option in enumerate(options, start=1):
        print(f"  {num}. {option}")
    while True:
        try:
            answer = input_fn(f"Choose [1-{len(options)}, q to abort]: ")
        except EOFError:
            raise LiveCancelled("input closed – aborted")
        command = answer.strip().lower()
        if command in {"q", "quit"}:
            raise LiveCancelled("aborted by facilitator")
        if command.isdigit():
            idx = int(command) - 1
            if 0 <= idx < len(options):
                return idx
        print(f"  Answer 1-{len(options)} or q.")