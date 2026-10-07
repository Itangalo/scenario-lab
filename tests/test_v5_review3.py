"""Third v5 review: hidden subfolders, turn-1 resume, round caps, mid-turn branch, market sources."""

import json
import shutil
from pathlib import Path

import pytest

from scenario_lab.llm import MockLLMClient
from scenario_lab.loader import load_scenario
from scenario_lab.orchestrator import Orchestrator, run_simulation
from scenario_lab.output import OutputManager, iter_run_dirs
from scenario_lab.resume import (
    create_branch,
    detect_last_phase,
    detect_last_turn,
    load_initial_scenario,
    load_run_state,
)

from test_phases import _mock_client, _run_two_turns
from test_negotiations import _message_client, _negotiation_scenario

REPO_ROOT = Path(__file__).resolve().parents[1]


# -- 1. Output subfolders that look like runs --------------------------------


def test_subdir_named_like_a_run_is_rejected(tmp_path):
    scenario = load_scenario("scenarios/sweden-ai-2030")
    for name in ("run-fast", "live-demo"):
        with pytest.raises(ValueError, match="would read as a run directory"):
            OutputManager(scenario, tmp_path).start_run(subdir=name)


def test_existing_run_like_subfolder_is_still_discovered(tmp_path):
    """Runs made before the guard (or by hand) inside 'run-x/' must not vanish."""
    runs = tmp_path / "runs"
    inner = runs / "run-fast" / "run-20261001-100000"
    inner.mkdir(parents=True)
    (inner / "config.json").write_text("{}", encoding="utf-8")
    top = runs / "run-20261002-100000"
    top.mkdir()
    (top / "config.json").write_text("{}", encoding="utf-8")
    assert {p.name for p in iter_run_dirs(runs)} == {inner.name, top.name}


# -- 2. Resuming a turn-1 crash keeps the initial state ----------------------


def test_load_initial_scenario_reapplies_recorded_initial_state(tmp_path):
    fake_dir = tmp_path / "sweden-ai-2030"
    fake_dir.mkdir()
    for name in ("scenario.yaml", "metrics.md"):
        (fake_dir / name).symlink_to(REPO_ROOT / "scenarios/sweden-ai-2030" / name)
    state_file = tmp_path / "draw.json"
    state_file.write_text(
        json.dumps({"metrics": {"unemployment": 11}, "context": "A harsher start."}),
        encoding="utf-8",
    )
    scenario = load_scenario("scenarios/sweden-ai-2030", initial_state=state_file)
    run_dir = OutputManager(scenario, fake_dir).start_run()
    state_file.unlink()  # the original file may have moved: the record suffices

    restored = load_initial_scenario(run_dir)
    assert restored.metrics.metrics["unemployment"].value == 11
    assert "A harsher start." in restored.context
    assert restored.initial_state is not None


# -- 3. Turn 1 is complete only once its summary exists ----------------------


def test_turn_one_needs_its_historical_summary(tmp_path):
    run_dir = _run_two_turns(tmp_path)
    shutil.rmtree(run_dir / "turn-02")
    assert detect_last_turn(run_dir) == 1
    (run_dir / "turn-01" / "6-historical-summary.md").unlink()
    assert detect_last_turn(run_dir) == 0
    assert detect_last_phase(run_dir, 1) == "actors"


# -- 4. `rounds` is a guaranteed minimum even when max_rounds lags -----------


def test_rounds_override_without_max_rounds_still_runs_every_round(tmp_path):
    scenario, manager, _ = _negotiation_scenario(tmp_path, rounds=3, max_rounds=1)
    recipient = list(scenario.actors)[1]
    client = _message_client("Keep talking.", recipient)
    Orchestrator(scenario, client, manager)._run_negotiations(1, [])
    prompts = [u for _, u in client.calls if "private negotiations" in u.lower()]
    assert any("round 3" in p.lower() for p in prompts)


# -- 5. Writers with nobody reachable sit out --------------------------------


def test_writer_with_only_human_recipients_makes_no_call(tmp_path):
    scenario, manager, run_dir = _negotiation_scenario(tmp_path)
    actor_ids = list(scenario.actors)
    lone = actor_ids[0]
    client = _message_client("Anyone?", actor_ids[1])
    orchestrator = Orchestrator(scenario, client, manager)
    inboxes, _, delivered = orchestrator._run_negotiations(
        1, [], writers=[lone],
        unavailable={a: "human-played" for a in actor_ids if a != lone},
    )
    assert client.calls == []
    assert delivered == []
    assert not (run_dir / "turn-01" / "2-negotiations").exists()


def test_round_prompt_does_not_offer_unavailable_recipients(tmp_path):
    scenario, manager, _ = _negotiation_scenario(tmp_path)
    a, b, human = list(scenario.actors)[:3]
    client = _message_client("Hi.", b)
    Orchestrator(scenario, client, manager)._run_negotiations(
        1, [], writers=[a, b], unavailable={human: "human-played"},
    )
    prompts = [u for _, u in client.calls if "private negotiations" in u.lower()]
    assert prompts
    for prompt in prompts:
        line = next(l for l in prompt.splitlines() if "You may write to:" in l)
        assert human not in line


# -- Anchors are silent ------------------------------------------------------


def test_market_anchor_is_never_rendered_into_the_events_prompt(tmp_path):
    from scenario_lab.prompts import PromptBuilder

    scenario = load_scenario("scenarios/sweden-ai-2030")
    scenario.events[0].market_url = "https://manifold.markets/someone/some-question"
    scenario.events[0].market_retrieved = "2026-10-01"
    scenario.events[0].market_probability = "34%"
    text = PromptBuilder(scenario)._format_events_list()
    assert "manifold" not in text.lower()
    assert "34%" not in text
    assert "anchor" not in text.lower()


def test_anchor_keys_for_each_source_load_into_market_url(tmp_path):
    from scenario_lab.loader import load_events

    for key, url in (
        ("Metaculus", "https://www.metaculus.com/questions/1/x/"),
        ("Manifold", "https://manifold.markets/u/q"),
        ("Polymarket", "https://polymarket.com/event/e/m"),
        ("Market", "https://manifold.markets/u/q"),
    ):
        path = tmp_path / "events.md"
        path.write_text(
            "# Events\n\n## E\n\n**ID:** e\n\n**Condition:** none\n\n"
            "**Probability:** 10 percent\n\n**Can repeat:** No\n\n"
            f"**Description:** x.\n\n**{key}:** {url}\n\n**Retrieved:** 2026-10-01\n\n"
            "**Market probability:** 12%\n",
            encoding="utf-8",
        )
        (event,) = load_events(path)
        assert event.market_url == url, key
        assert event.market_probability == "12%"


# -- Market sources ----------------------------------------------------------


def test_detect_source():
    from scenario_lab.market_sources import detect_source

    assert detect_source("https://www.metaculus.com/questions/12345/x/") == "metaculus"
    assert detect_source("https://manifold.markets/user/slug") == "manifold"
    assert detect_source("https://polymarket.com/event/some-event") == "polymarket"
    assert detect_source("https://polymarket.com/event/some-event/some-market") == "polymarket"
    assert detect_source("https://example.com/poll") is None
    assert detect_source("https://manifold.markets/") is None


def test_fetch_manifold_binary():
    from scenario_lab.market_sources import fetch_quote

    seen = []

    def fake(url):
        seen.append(url)
        return {
            "question": "Will it?", "outcomeType": "BINARY",
            "probability": 0.2345, "closeTime": 1793491140000,
        }

    quote = fetch_quote("https://manifold.markets/user/will-it", http_get=fake)
    assert seen == ["https://api.manifold.markets/v0/slug/will-it"]
    assert quote.figure == "23.4%" or quote.figure == "23.5%"
    assert quote.closes == "2026-10-31"


def test_fetch_manifold_rejects_non_binary():
    from scenario_lab.market_sources import MarketError, fetch_quote

    with pytest.raises(MarketError, match="not BINARY"):
        fetch_quote(
            "https://manifold.markets/u/q",
            http_get=lambda url: {"outcomeType": "MULTIPLE_CHOICE"},
        )


def test_fetch_polymarket_market_and_event():
    from scenario_lab.market_sources import MarketError, fetch_quote

    market = {
        "question": "Q?", "slug": "q", "outcomes": '["Yes", "No"]',
        "outcomePrices": '["0.0265", "0.9735"]', "endDate": "2027-01-01T04:59:00Z",
    }

    def fake(url):
        if "/markets?slug=q" in url:
            return [market]
        if "/events?slug=solo" in url:
            return [{"markets": [market]}]
        if "/events?slug=many" in url:
            return [{"markets": [market, dict(market, slug="r")]}]
        return []

    quote = fetch_quote("https://polymarket.com/event/ev/q", http_get=fake)
    assert quote.figure == "2.6%" or quote.figure == "2.7%"
    assert quote.closes == "2027-01-01"
    assert fetch_quote("https://polymarket.com/event/solo", http_get=fake).title == "Q?"
    with pytest.raises(MarketError, match="holds 2 markets"):
        fetch_quote("https://polymarket.com/event/many", http_get=fake)
    with pytest.raises(MarketError, match="knows no market"):
        fetch_quote("https://polymarket.com/event/nothing", http_get=fake)


def test_fetch_polymarket_rejects_non_yes_no():
    from scenario_lab.market_sources import MarketError, fetch_quote

    with pytest.raises(MarketError, match="not Yes/No"):
        fetch_quote(
            "https://polymarket.com/event/e/m",
            http_get=lambda url: [{
                "question": "Who?", "outcomes": '["A", "B"]', "outcomePrices": '["0.5", "0.5"]',
            }],
        )


def test_fetch_metaculus_is_manual():
    from scenario_lab.market_sources import MarketError, fetch_quote

    with pytest.raises(MarketError, match="by hand"):
        fetch_quote("https://www.metaculus.com/questions/1/x/", http_get=lambda u: {})


def test_validator_accepts_each_source_and_rejects_unknown_hosts():
    from scenario_lab.validator import validate_market_anchors

    scenario = load_scenario("scenarios/sweden-ai-2030")
    event = scenario.events[0]
    event.market_retrieved = "2026-10-01"
    event.market_probability = "10%"
    scenario.events = [event]
    for url in (
        "https://www.metaculus.com/questions/1/x/",
        "https://manifold.markets/u/q",
        "https://polymarket.com/event/e",
    ):
        event.market_url = url
        errors, _ = validate_market_anchors(scenario)
        assert errors == [], url
    event.market_url = "https://example.com/poll"
    errors, _ = validate_market_anchors(scenario)
    assert any("not a recognised market question URL" in e for e in errors)


# -- branch --from-phase -----------------------------------------------------


def test_branch_inside_a_turn_keeps_events_and_reruns_the_rest(tmp_path):
    run_dir = _run_two_turns(tmp_path)
    fake_dir = run_dir.parent.parent
    child = create_branch(run_dir, 2, fake_dir, from_phase="events")

    kept = sorted(p.name for p in (child / "turn-02").iterdir())
    assert kept and all(name.startswith("1-") for name in kept)
    assert (child / "turn-01" / "6-historical-summary.md").is_file()
    assert (
        (child / "turn-02" / "1-events.json").read_bytes()
        == (run_dir / "turn-02" / "1-events.json").read_bytes()
    )
    summary = json.loads((child / "summary.json").read_text())
    assert summary["total_turns"] == 1
    assert summary["phases"] == {"1": "world", "2": "events"}
    assert summary["metadata"]["branch_phase"] == "events"
    assert detect_last_phase(child, 2) == "events"

    # Continue the branch turn from the actors phase: events are reloaded,
    # not redrawn, and the turn completes.
    scenario, loaded = load_run_state(child, 1)
    manager = OutputManager(scenario, fake_dir)
    manager.run_dir = child
    client = _mock_client()
    run_simulation(
        scenario, client, num_turns=2, output_manager=manager,
        start_turn=loaded + 1, start_phase="actors",
    )
    assert detect_last_turn(child) == 2
    assert "list of potential external events looks like this" not in " ".join(
        s for call in client.calls for s in call
    )


def test_branch_after_actors_keeps_actor_files(tmp_path):
    run_dir = _run_two_turns(tmp_path)
    child = create_branch(run_dir, 2, run_dir.parent.parent, from_phase="actors")
    names = {p.name for p in (child / "turn-02").iterdir()}
    assert "2-actors" in names and "1-events.json" in names
    assert not any(n.startswith(("3-", "4-", "5-", "6-")) for n in names)
    assert detect_last_phase(child, 2) == "actors"


def test_branch_phase_must_have_been_reached(tmp_path):
    run_dir = _run_two_turns(tmp_path)
    shutil.rmtree(run_dir / "turn-02" / "2-actors")
    for path in (run_dir / "turn-02").iterdir():
        if path.name[0] in "3456":
            path.unlink()
    with pytest.raises(ValueError, match="has not completed the actors phase"):
        create_branch(run_dir, 2, run_dir.parent.parent, from_phase="actors")
    # An events-phase branch of the same unfinished turn is fine.
    create_branch(run_dir, 2, run_dir.parent.parent, from_phase="events")


def test_branch_phase_world_means_end_of_turn(tmp_path):
    run_dir = _run_two_turns(tmp_path)
    child = create_branch(run_dir, 1, run_dir.parent.parent, from_phase="world")
    assert not (child / "turn-02").exists()
    assert "branch_phase" not in json.loads((child / "summary.json").read_text())["metadata"]


def test_branch_unknown_phase_rejected(tmp_path):
    run_dir = _run_two_turns(tmp_path)
    with pytest.raises(ValueError, match="Unknown phase"):
        create_branch(run_dir, 1, run_dir.parent.parent, from_phase="midnight")
