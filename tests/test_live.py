"""Tests for live workshop mode (scenario_lab/live.py)."""

import json
import shutil
from pathlib import Path

import pytest

from scenario_lab.live import (
    ActorMenu,
    LiveCancelled,
    LiveError,
    MenuOption,
    _chain_next_menus,
    ask_choice,
    completed_turns,
    find_live_runs,
    find_live_scenarios,
    has_store_tables,
    newest_pending_turn,
    parse_actor_action_specs,
    parse_menu_json,
    pending_live_turns,
    pick_all,
    read_menus,
    render_briefing,
    resolve_pick,
    run_menu_turn,
    run_resolve_turn,
    wrap_human_action,
    write_menus,
)
from scenario_lab.loader import load_scenario
from scenario_lab.llm import MockLLMClient
from scenario_lab.output import OutputManager, _merge_costs_data


def _menu() -> ActorMenu:
    return ActorMenu(
        actor_id="eu",
        actor_name="EU",
        turn=1,
        strategy="direct",
        options=[
            MenuOption(index=1, title="Enforce the Act", text="The EU enforces."),
            MenuOption(index=2, title="Mediate talks", text="The EU mediates."),
        ],
    )


# --- pick resolution ---


def test_resolve_pick_numeric_forms():
    menu = _menu()
    for spec in ("1", " 2 ", "action 1", "Option 2", "#1"):
        pick = resolve_pick(spec, menu)
        assert pick.kind == "menu"
    assert resolve_pick("2", menu).title == "Mediate talks"
    assert resolve_pick("2", menu).index == 2


def test_resolve_pick_free_text():
    pick = resolve_pick("we sign the accord on our own terms", _menu())
    assert pick.kind == "free"
    assert pick.text == "we sign the accord on our own terms"


def test_resolve_pick_rejects_empty_and_out_of_range():
    menu = _menu()
    with pytest.raises(LiveError):
        resolve_pick("   ", menu)
    with pytest.raises(LiveError):
        resolve_pick("3", menu)
    with pytest.raises(LiveError):
        resolve_pick("1, 2", menu)


def test_parse_actor_action_specs():
    assert parse_actor_action_specs(["eu=3", "us-gov=we wait"]) == {
        "eu": "3",
        "us-gov": "we wait",
    }
    assert parse_actor_action_specs(None) == {}
    with pytest.raises(LiveError):
        parse_actor_action_specs(["eu"])
    with pytest.raises(LiveError):
        parse_actor_action_specs(["eu="])
    with pytest.raises(LiveError):
        parse_actor_action_specs(["a=b=c"])


# --- menu parsing ---


def test_parse_menu_json_valid():
    options = parse_menu_json(
        '[{"title": "A", "text": "Do A."}, {"title": "B", "text": "Do B."}]',
        max_options=6,
        actor_name="EU",
    )
    assert [o.index for o in options] == [1, 2]
    assert options[0].title == "A"


def test_parse_menu_json_strips_fences_and_truncates():
    raw = "```json\n" + json.dumps(
        [{"title": f"O{i}", "text": f"T{i}"} for i in range(8)]
    ) + "\n```"
    options = parse_menu_json(raw, max_options=6, actor_name="EU")
    assert len(options) == 6


def test_parse_menu_json_rejects_garbage():
    for raw in ("not json at all", "[]", '{"title": "x"}', '[{"text": "no title"}]'):
        with pytest.raises(LiveError):
            parse_menu_json(raw, max_options=6, actor_name="EU")


# --- wrapping ---


def test_wrap_human_action_no_store():
    doc = wrap_human_action("Enforce the Act", "The EU enforces.", False)
    assert "## Actions" in doc
    assert "### Enforce the Act" in doc
    assert "The EU enforces." in doc
    assert "Statement changes" not in doc
    assert "Store changes" not in doc


def test_wrap_human_action_with_store():
    doc = wrap_human_action("Wait", "We wait.", True)
    assert "## Store changes" in doc
    assert "No changes." in doc


def test_has_store_tables_global_ai_live_has_none():
    assert has_store_tables(load_scenario("scenarios/global-ai-live")) is False


# --- menu persistence roundtrip ---


def test_write_and_read_menus(tmp_path):
    run_dir = tmp_path / "runs" / "live-test"
    (run_dir / "turn-01" / "live").mkdir(parents=True)
    menus = {"eu": _menu()}
    write_menus(run_dir, 1, menus, "direct")
    loaded = read_menus(run_dir, 1)
    assert loaded["eu"].options[1].title == "Mediate talks"


def test_read_menus_missing_raises(tmp_path):
    with pytest.raises(LiveError):
        read_menus(tmp_path / "nope", 1)


# --- interactive picker ---


def test_pick_all_collects_missing_and_keeps_given():
    menu = _menu()
    answers = iter(["2", "y"])
    picks = pick_all(
        {"eu": menu}, {}, input_fn=lambda prompt: next(answers)
    )
    assert picks["eu"].index == 2


def test_pick_all_quit_cancels():
    with pytest.raises(LiveCancelled):
        pick_all({"eu": _menu()}, {}, input_fn=lambda prompt: "q")


def test_pick_all_non_interactive_errors():
    with pytest.raises(LiveError):
        pick_all({"eu": _menu()}, {}, interactive=False)


def _menu2() -> ActorMenu:
    return ActorMenu(
        actor_id="us-gov",
        actor_name="US Government",
        turn=1,
        strategy="direct",
        options=[
            MenuOption(index=1, title="Lead the race", text="The US leads."),
            MenuOption(index=2, title="Sign a deal", text="The US signs."),
        ],
    )


def test_pick_all_shows_headers_only(capsys):
    answers = iter(["1", "y"])
    pick_all({"eu": _menu()}, {}, input_fn=lambda prompt: next(answers))
    out = capsys.readouterr().out
    assert "1. Enforce the Act" in out
    assert "2. Mediate talks" in out
    assert "The EU enforces." not in out
    assert "The EU mediates." not in out


def test_pick_all_back_revisits_previous_team():
    menus = {"us-gov": _menu2(), "eu": _menu()}
    answers = iter(["1", "back", "2", "2", "y"])
    picks = pick_all(menus, {}, input_fn=lambda prompt: next(answers))
    assert picks["us-gov"].index == 2
    assert picks["eu"].index == 2


def test_pick_all_back_at_first_team_stays():
    answers = iter(["back", "1", "y"])
    picks = pick_all({"eu": _menu()}, {}, input_fn=lambda prompt: next(answers))
    assert picks["eu"].index == 1


def test_pick_all_confirm_redo_by_name():
    answers = iter(["1", "EU", "2", "y"])
    picks = pick_all({"eu": _menu()}, {}, input_fn=lambda prompt: next(answers))
    assert picks["eu"].index == 2


def test_pick_all_confirm_quit_cancels():
    answers = iter(["1", "q"])
    with pytest.raises(LiveCancelled):
        pick_all({"eu": _menu()}, {}, input_fn=lambda prompt: next(answers))


# --- cost merge ---


def test_merge_costs_data_unions_turns_taskwise():
    old = {
        "total_cost_usd": 0.01,
        "total_tokens": 100,
        "by_turn": [
            {
                "turn": 1,
                "cost_usd": 0.01,
                "tokens": 100,
                "prompt_tokens": 80,
                "completion_tokens": 20,
                "by_task": {
                    "menu:eu": {
                        "cost_usd": 0.01, "tokens": 100,
                        "prompt_tokens": 80, "completion_tokens": 20, "calls": 1,
                    }
                },
            }
        ],
        "by_task_total": {},
    }
    new = {
        "total_cost_usd": 0.02,
        "total_tokens": 200,
        "by_turn": [
            {
                "turn": 1,
                "cost_usd": 0.02,
                "tokens": 200,
                "prompt_tokens": 150,
                "completion_tokens": 50,
                "by_task": {
                    "metrics": {
                        "cost_usd": 0.02, "tokens": 200,
                        "prompt_tokens": 150, "completion_tokens": 50, "calls": 1,
                    }
                },
            }
        ],
        "by_task_total": {},
    }
    merged = _merge_costs_data(old, new)
    assert len(merged["by_turn"]) == 1
    turn = merged["by_turn"][0]
    # Both tasks survive under the same turn; totals re-sum exactly.
    assert set(turn["by_task"]) == {"menu:eu", "metrics"}
    assert turn["tokens"] == 300
    assert merged["total_tokens"] == 300
    assert set(merged["by_task_total"]) == {"menu:eu", "metrics"}


def test_merge_costs_data_no_old():
    new = {"by_turn": [], "total_cost_usd": 0.0, "total_tokens": 0}
    assert _merge_costs_data(None, new) == new


# --- full live turn roundtrip with mocks ---


MENU_JSON = json.dumps([
    {"title": "Sign the accord", "text": "The actor signs the accord this turn."},
    {"title": "Hold back", "text": "The actor waits and watches this turn."},
])

METRICS_MD = """## Metrics

```json
{"frontier_capability": 34, "governance_strength": 37, "us_china_cooperation": 39, "public_trust": 48}
```

## Narrative

The teams made their moves. Capability crept forward while cooperation slipped a point.

## Notepad

Live turn resolved from team picks.
"""


def _live_mock() -> MockLLMClient:
    return MockLLMClient(
        {
            "list of potential external events": "[]",
            "propose at most": MENU_JSON,
            "A JSON object describing all metrics": METRICS_MD,
            "CURRENT NARRATIVE": "Live turn summarized.",
        }
    )


def _live_scenario_copy(tmp_path) -> Path:
    """Copy global-ai-live to tmp so live runs sit in <scenario>/runs/<run>.

    The framework resolves a run's scenario by walking up to runs/../, so a
    live run must live under a directory holding the scenario files.
    """
    dest = tmp_path / "global-ai-live"
    shutil.copytree(
        Path("scenarios/global-ai-live"), dest, ignore=shutil.ignore_patterns("runs")
    )
    return dest


def test_live_menu_then_resolve_roundtrip(tmp_path):
    scenario = load_scenario(_live_scenario_copy(tmp_path))
    scenario.config.random_seed = 7
    output_manager = OutputManager(scenario, tmp_path / "global-ai-live")
    run_dir = output_manager.start_run(prefix="live-")
    assert run_dir.name.startswith("live-")

    mock = _live_mock()
    menus = run_menu_turn(
        scenario, output_manager, run_dir, 1, max_options=3, llm_client=mock
    )
    assert set(menus) == {"us-gov", "us-labs", "china", "eu"}
    assert all(len(m.options) == 2 for m in menus.values())
    assert (run_dir / "turn-01" / "live" / "menu.json").exists()
    assert (run_dir / "turn-01" / "live" / "briefing.md").exists()
    assert (run_dir / "turn-01" / "live" / "menu-eu.md").exists()
    assert (run_dir / "turn-01" / "1-events.json").exists()

    result = run_resolve_turn(
        run_dir,
        1,
        {"us-gov": "1", "us-labs": "2", "china": "1", "eu": "Hold firm on standards"},
        interactive=False,
        llm_client=_live_mock(),
    )
    assert result.turn == 1
    assert set(result.actor_outputs) == {"us-gov", "us-labs", "china", "eu"}
    assert "Sign the accord" in result.actor_outputs["us-gov"]
    assert "Hold firm on standards" in result.actor_outputs["eu"]
    assert result.metrics["frontier_capability"] == 34
    assert (run_dir / "turn-01" / "4-metrics.json").exists()
    assert (run_dir / "turn-01" / "4-world-state.md").exists()

    # Costs from both invocations merged, not overwritten.
    costs = json.loads((run_dir / "costs.json").read_text())
    tasks = costs["by_turn"][0]["by_task"]
    assert any(t.startswith("menu:") for t in tasks)
    assert "metrics" in tasks

    # Resolve chains the next turn's menus with no new input.
    assert (run_dir / "turn-02" / "live" / "menu.json").exists()
    assert (run_dir / "turn-02" / "live" / "briefing.md").exists()
    next_menus = read_menus(run_dir, 2)
    assert set(next_menus) == {"us-gov", "us-labs", "china", "eu"}

    # The chained-but-unresolved turn is legitimate pending state, not a
    # broken run: integrity passes with an explanatory warning.
    from scenario_lab.regression import check_run_integrity

    report = check_run_integrity(run_dir)
    assert report["is_valid"] is True
    assert any("pending live turn" in w for w in report["warnings"])


def test_resolve_requires_menu(tmp_path):
    scenario = load_scenario(_live_scenario_copy(tmp_path))
    scenario.config.random_seed = 7
    output_manager = OutputManager(scenario, tmp_path / "global-ai-live")
    run_dir = output_manager.start_run(prefix="live-")
    with pytest.raises(LiveError):
        run_resolve_turn(run_dir, 1, {"eu": "1"}, interactive=False)


def test_resolve_rejects_unknown_actor_and_missing_picks(tmp_path):
    scenario = load_scenario(_live_scenario_copy(tmp_path))
    scenario.config.random_seed = 7
    output_manager = OutputManager(scenario, tmp_path / "global-ai-live")
    run_dir = output_manager.start_run(prefix="live-")
    run_menu_turn(scenario, output_manager, run_dir, 1, llm_client=_live_mock())
    with pytest.raises(LiveError):
        run_resolve_turn(
            run_dir, 1, {"narnia": "1", "eu": "1", "china": "1",
                         "us-gov": "1", "us-labs": "1"},
            interactive=False,
        )
    with pytest.raises(LiveError):
        run_resolve_turn(run_dir, 1, {"eu": "1"}, interactive=False)


def test_menu_only_game_is_valid_pending(tmp_path):
    from scenario_lab.regression import check_run_integrity

    scenario = load_scenario(_live_scenario_copy(tmp_path))
    scenario.config.random_seed = 7
    output_manager = OutputManager(scenario, tmp_path / "global-ai-live")
    run_dir = output_manager.start_run(prefix="live-")
    run_menu_turn(scenario, output_manager, run_dir, 1, llm_client=_live_mock())
    report = check_run_integrity(run_dir)
    assert report["is_valid"] is True
    assert any("pending live turn" in w for w in report["warnings"])


def _full_picks():
    return {"us-gov": "1", "us-labs": "2", "china": "1", "eu": "1"}


def test_resolve_no_auto_menu_skips_chaining(tmp_path):
    scenario = load_scenario(_live_scenario_copy(tmp_path))
    scenario.config.random_seed = 7
    output_manager = OutputManager(scenario, tmp_path / "global-ai-live")
    run_dir = output_manager.start_run(prefix="live-")
    run_menu_turn(scenario, output_manager, run_dir, 1, llm_client=_live_mock())
    run_resolve_turn(
        run_dir, 1, _full_picks(), interactive=False,
        llm_client=_live_mock(), auto_menu=False,
    )
    assert not (run_dir / "turn-02").exists()


def test_chain_stops_past_max_turns(tmp_path):
    scenario = load_scenario(_live_scenario_copy(tmp_path))
    scenario.config.random_seed = 7
    output_manager = OutputManager(scenario, tmp_path / "global-ai-live")
    run_dir = output_manager.start_run(prefix="live-")
    menus = {"eu": _menu()}
    assert (
        _chain_next_menus(scenario, output_manager, run_dir, 3, menus) is None
    )
    assert not (run_dir / "turn-04").exists()


def test_briefing_has_no_presenter_notes():
    scenario = load_scenario("scenarios/global-ai-live")
    text = render_briefing(scenario, 1, "July-December 2026", [])
    assert "Facilitator notes" not in text
    assert text.startswith("# Workshop briefing")


# --- launcher: scanning and selection ---


def _scenario_yaml(path, name, workshop=True):
    import yaml

    data = {"name": name}
    if workshop:
        data["workshop"] = {"audience": "teams", "tone": "plain"}
    path.write_text(yaml.dump(data), encoding="utf-8")


def test_find_live_scenarios_only_workshop_ones(tmp_path):
    root = tmp_path / "scenarios"
    (root / "live-game").mkdir(parents=True)
    _scenario_yaml(root / "live-game" / "scenario.yaml", "Live Game")
    (root / "plain-sim").mkdir(parents=True)
    _scenario_yaml(root / "plain-sim" / "scenario.yaml", "Plain Sim", workshop=False)
    (root / "junk.txt").write_text("junk", encoding="utf-8")
    found = find_live_scenarios(root)
    assert [(s.name, s.path.name) for s in found] == [("Live Game", "live-game")]
    assert find_live_scenarios(tmp_path / "missing") == []


def test_find_live_runs_newest_first(tmp_path):
    import time

    scenario = tmp_path / "game"
    runs = scenario / "runs"
    (runs / "live-old").mkdir(parents=True)
    time.sleep(0.01)
    (runs / "live-new").mkdir(parents=True)
    (runs / "run-plain").mkdir(parents=True)
    found = find_live_runs(scenario)
    assert [r.run_dir.name for r in found] == ["live-new", "live-old"]
    assert find_live_runs(tmp_path / "nope") == []


def test_ask_choice_retries_then_picks():
    answers = iter(["0", "abc", "2"])
    assert ask_choice("Pick?", ["a", "b"], input_fn=lambda p: next(answers)) == 1


def test_ask_choice_quit_cancels():
    with pytest.raises(LiveCancelled):
        ask_choice("Pick?", ["a"], input_fn=lambda p: "q")


def test_pending_live_turns_detects_menu_only(tmp_path):
    run_dir = tmp_path / "live-x"
    pending = run_dir / "turn-02" / "live"
    pending.mkdir(parents=True)
    (pending / "menu.json").write_text("{}", encoding="utf-8")
    resolved = run_dir / "turn-01"
    (resolved / "2-actors").mkdir(parents=True)
    (resolved / "4-metrics.json").write_text("{}", encoding="utf-8")
    (resolved / "live" ).mkdir(parents=True, exist_ok=True)
    (resolved / "live" / "menu.json").write_text("{}", encoding="utf-8")
    assert pending_live_turns(run_dir) == {2}
    assert newest_pending_turn(run_dir) == 2
    assert completed_turns(run_dir) == 0


def _live_ns(**overrides):
    import argparse

    base = dict(
        target=None,
        turn=None,
        scenarios=None,
        max_options=6,
        strategy="direct",
        samples=4,
        initial_state=None,
        model=None,
        actor_action=None,
        override=None,
        seed=7,
        skip_model_checks=True,
        log_llm_io=False,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def _wizard_root(tmp_path):
    root = tmp_path / "scenarios"
    dest = root / "global-ai-live"
    shutil.copytree(
        Path("scenarios/global-ai-live"), dest, ignore=shutil.ignore_patterns("runs")
    )
    return root, dest


def test_live_wizard_starts_new_game_when_alone(tmp_path, capsys):
    from scenario_lab.cli import run_live_command

    root, dest = _wizard_root(tmp_path)
    rc = run_live_command(
        _live_ns(scenarios=root), input_fn=lambda p: "1", llm_client=_live_mock()
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "only live-ready one" in out
    assert "No previous live games" in out
    runs = list((dest / "runs").glob("live-*"))
    assert len(runs) == 1
    assert (runs[0] / "turn-01" / "live" / "menu.json").exists()


def test_live_wizard_resumes_and_spots_pending(tmp_path, capsys):
    from scenario_lab.cli import run_live_command

    root, dest = _wizard_root(tmp_path)
    run_live_command(
        _live_ns(scenarios=root), input_fn=lambda p: "1", llm_client=_live_mock()
    )
    run_dir = next((dest / "runs").glob("live-*"))
    # Fresh game: turn 1 has menus but no resolution, so `live` chains
    # straight into the picker (option 2 = the run, then 4 picks + confirm).
    answers = iter(["2", "1", "1", "1", "1", "y"])
    rc = run_live_command(
        _live_ns(scenarios=root), input_fn=lambda p: next(answers),
        llm_client=_live_mock(),
    )
    assert rc == 0
    assert (run_dir / "turn-01" / "4-metrics.json").exists()
    assert (run_dir / "turn-02" / "live" / "menu.json").exists()
    # Turn 2 now pends: non-interactive `live` prints the pointer instead.
    capsys.readouterr()
    rc = run_live_command(_live_ns(target=run_dir), llm_client=_live_mock())
    assert rc == 0
    assert "live-resolve" in capsys.readouterr().out


def test_live_command_with_run_target_resumes(tmp_path, capsys):
    from scenario_lab.cli import run_live_command

    root, dest = _wizard_root(tmp_path)
    run_live_command(
        _live_ns(scenarios=root), input_fn=lambda p: "1", llm_client=_live_mock()
    )
    run_dir = next((dest / "runs").glob("live-*"))
    # Pending turn resolves in-process through the same single command.
    answers = iter(["2", "1", "2", "1", "y"])
    rc = run_live_command(
        _live_ns(target=run_dir), input_fn=lambda p: next(answers),
        llm_client=_live_mock(),
    )
    assert rc == 0
    assert (run_dir / "turn-01" / "4-metrics.json").exists()
    assert (run_dir / "turn-02" / "live" / "menu.json").exists()


def test_live_explicit_turn_on_pending_resolves(tmp_path):
    # Regression: `live <run> --turn N` on a turn with ready menus must
    # resolve (enter picks), not regenerate menus in a loop. This is the
    # exact command the menu handler used to print.
    from scenario_lab.cli import run_live_command

    root, dest = _wizard_root(tmp_path)
    run_live_command(
        _live_ns(scenarios=root), input_fn=lambda p: "1", llm_client=_live_mock()
    )
    run_dir = next((dest / "runs").glob("live-*"))
    answers = iter(["1", "1", "1", "1", "y"])
    rc = run_live_command(
        _live_ns(target=run_dir, turn=1), input_fn=lambda p: next(answers),
        llm_client=_live_mock(),
    )
    assert rc == 0
    assert (run_dir / "turn-01" / "4-metrics.json").exists()
    assert (run_dir / "turn-02" / "live" / "menu.json").exists()


def test_live_completed_game_points_to_new(tmp_path, capsys):
    from scenario_lab.cli import run_live_command

    root, dest = _wizard_root(tmp_path)
    run_live_command(
        _live_ns(scenarios=root), input_fn=lambda p: "1", llm_client=_live_mock()
    )
    run_dir = next((dest / "runs").glob("live-*"))
    # Play all three turns with mocks; chaining prepares each next menu.
    for turn in (1, 2, 3):
        run_resolve_turn(
            run_dir, turn, _full_picks(), interactive=False,
            llm_client=_live_mock(),
        )
    assert not (run_dir / "turn-04").exists()
    capsys.readouterr()
    rc = run_live_command(
        _live_ns(target=run_dir), input_fn=lambda p: "1", llm_client=_live_mock()
    )
    assert rc == 1
    assert "game is over" in capsys.readouterr().out


def test_live_single_command_resolves_pending(tmp_path):
    from scenario_lab.cli import run_live_command

    root, dest = _wizard_root(tmp_path)
    run_live_command(
        _live_ns(scenarios=root), input_fn=lambda p: "1", llm_client=_live_mock()
    )
    run_dir = next((dest / "runs").glob("live-*"))
    # One `live` on the pending turn enters picks, resolves, and chains.
    answers = iter(["1", "1", "1", "1", "y"])
    rc = run_live_command(
        _live_ns(target=run_dir), input_fn=lambda p: next(answers),
        llm_client=_live_mock(),
    )
    assert rc == 0
    assert (run_dir / "turn-01" / "4-metrics.json").exists()
    assert (run_dir / "turn-02" / "live" / "menu.json").exists()


def test_live_resolve_shows_progress(capsys, tmp_path):
    scenario = load_scenario(_live_scenario_copy(tmp_path))
    scenario.config.random_seed = 7
    output_manager = OutputManager(scenario, tmp_path / "global-ai-live")
    run_dir = output_manager.start_run(prefix="live-")
    run_menu_turn(scenario, output_manager, run_dir, 1, llm_client=_live_mock())
    out = capsys.readouterr().out
    assert "waiting for the model" in out
    capsys.readouterr()
    run_resolve_turn(
        run_dir, 1, _full_picks(), interactive=False,
        llm_client=_live_mock(), auto_menu=False,
    )
    out = capsys.readouterr().out
    assert "Updating metrics and narrative (waiting for the model)" in out


def test_free_tier_model_prices_at_zero(capsys):
    from scenario_lab.cost import CostCalculator

    pricing = CostCalculator.get_model_pricing(
        "opencode/muse-spark-1.3-contributor-free"
    )
    assert pricing == {"prompt": 0.0, "completion": 0.0}
    assert "Could not load" not in capsys.readouterr().out


def test_unknown_models_still_warn(capsys):
    from scenario_lab.cost import CostCalculator

    CostCalculator._unknown_models_warned.clear()
    pricing = CostCalculator.get_model_pricing("nope/definitely-not-a-model")
    assert pricing["prompt"] > 0
    assert "Could not load" in capsys.readouterr().out


def test_apply_config_overrides_sets_language():
    from scenario_lab.cli import apply_config_overrides

    scenario = load_scenario("scenarios/global-ai-live")
    assert scenario.config.output_language in (None, "English")
    apply_config_overrides(scenario, ["output_language=German"])
    assert scenario.config.output_language == "German"


def test_output_language_override_rides_into_every_turn(tmp_path):
    import json

    from scenario_lab.cli import run_live_command

    root, dest = _wizard_root(tmp_path)
    run_live_command(
        _live_ns(scenarios=root, override=["output_language=German"]),
        input_fn=lambda p: "1",
        llm_client=_live_mock(),
    )
    run_dir = next((dest / "runs").glob("live-*"))
    menu_data = json.loads(
        (run_dir / "turn-01" / "live" / "menu.json").read_text(encoding="utf-8")
    )
    assert menu_data["config_overrides"] == ["output_language=German"]
    # A fresh load loses the flag, but resolve re-applies it from menu.json:
    # the metrics call must carry the German instruction.
    mock = _live_mock()
    run_resolve_turn(
        run_dir, 1, _full_picks(), interactive=False,
        llm_client=mock, auto_menu=False,
    )
    prompted = "\n".join(user for _, user in mock.calls)
    assert "German" in prompted
