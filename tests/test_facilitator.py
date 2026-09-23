"""Tests for the facilitator web UI (scenario_lab/facilitator.py).

Uses the same MockLLMClient pattern as test_live.py so no network is needed.
"""

import json
import shutil
import threading
import time
import urllib.request
from pathlib import Path

import pytest

import scenario_lab.facilitator as fac
from scenario_lab.facilitator import (
    LiveError,
    create_server,
    game_state,
    get_job,
    list_runs,
    list_scenarios,
    prepare_turn,
    resolve_turn,
    submit_job,
    turn_payload,
    validate_picks,
)
from scenario_lab.llm import MockLLMClient


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


@pytest.fixture
def scenario_dir(tmp_path, monkeypatch):
    """Copied global-ai-live under tmp; runs resolve under <scenario>/runs/."""
    dest = tmp_path / "global-ai-live"
    shutil.copytree(
        Path("scenarios/global-ai-live"), dest, ignore=shutil.ignore_patterns("runs")
    )
    monkeypatch.setattr(fac, "LLM_CLIENT", _live_mock())
    return dest


@pytest.fixture
def prepared_game(scenario_dir):
    """A new game with turn-1 menus prepared; returns the run dir string."""
    result = prepare_turn(str(scenario_dir), turn=1, max_options=3)
    return result["run_dir"]


def test_list_scenarios_finds_workshop_only(tmp_path):
    (tmp_path / "plain").mkdir()
    (tmp_path / "plain" / "scenario.yaml").write_text("name: Plain\n")
    live = tmp_path / "live-one"
    live.mkdir()
    (live / "scenario.yaml").write_text("name: Live One\nworkshop:\n  tone: plain\n")
    found = list_scenarios(tmp_path)
    assert [s["name"] for s in found] == ["Live One"]


def test_prepare_turn_starts_new_game(scenario_dir):
    result = prepare_turn(str(scenario_dir), turn=1, max_options=3)
    run_dir = Path(result["run_dir"])
    assert run_dir.name.startswith("live-")
    assert (run_dir / "turn-01" / "live" / "menu.json").exists()
    assert (run_dir / "turn-01" / "live" / "briefing.md").exists()


def test_prepare_turn_records_overrides(scenario_dir):
    result = prepare_turn(
        str(scenario_dir), turn=1, max_options=3,
        overrides=["output_language=German"],
    )
    menu_json = Path(result["run_dir"]) / "turn-01" / "live" / "menu.json"
    assert json.loads(menu_json.read_text())["config_overrides"] == [
        "output_language=German"
    ]


def test_game_state_pending_after_prepare(prepared_game):
    state = game_state(prepared_game)
    assert state["pending_turn"] == 1
    assert state["completed_turns"] == 0
    assert {a["id"] for a in state["actors"]} == {"us-gov", "us-labs", "china", "eu"}
    assert state["turns"] == [{"turn": 1, "has_menus": True, "resolved": False}]


def test_turn_payload_carries_menus(prepared_game):
    payload = turn_payload(prepared_game, 1)
    assert payload["resolved"] is False
    assert set(payload["menus"]) == {"us-gov", "us-labs", "china", "eu"}
    assert payload["menus"]["eu"]["options"][0]["title"] == "Sign the accord"
    assert "Workshop briefing" in payload["briefing_md"]


def test_validate_picks_ok_missing_unknown(prepared_game):
    picks = {"us-gov": "1", "us-labs": "2", "china": "1", "eu": "Hold firm"}
    assert validate_picks(prepared_game, 1, picks) == picks
    with pytest.raises(LiveError):
        validate_picks(prepared_game, 1, {"eu": "1"})
    with pytest.raises(LiveError):
        validate_picks(
            prepared_game, 1,
            {"us-gov": "1", "us-labs": "1", "china": "1", "eu": "1", "narnia": "1"},
        )
    with pytest.raises(LiveError):
        validate_picks(
            prepared_game, 1,
            {"us-gov": "9", "us-labs": "1", "china": "1", "eu": "1"},
        )


def test_resolve_turn_advances_game(prepared_game):
    result = resolve_turn(
        prepared_game, 1,
        {"us-gov": "1", "us-labs": "2", "china": "1", "eu": "Hold firm"},
    )
    assert result["turn"] == 1
    state = result["game"]
    assert state["completed_turns"] == 1
    assert state["pending_turn"] == 2  # next menus chained automatically
    assert turn_payload(prepared_game, 1)["resolved"] is True


def test_list_runs_sees_prepared_game(scenario_dir, prepared_game):
    runs = list_runs(str(scenario_dir))
    assert len(runs) == 1
    assert runs[0]["pending_turn"] == 1


def test_jobs_run_in_background_with_log():
    events: list[str] = []

    def fn(log):
        log("halfway")
        events.append("ran")
        return {"ok": True}

    job_id = submit_job("test", fn)
    for _ in range(100):
        job = get_job(job_id)
        assert job is not None
        if job["status"] == "done":
            break
        time.sleep(0.05)
    assert job["status"] == "done"
    assert job["result"] == {"ok": True}
    assert job["log"] == ["Started.", "halfway", "Done."]
    assert get_job("job-nope") is None


def _get(server, path):
    port = server.server_address[1]
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}") as r:
        return r.status, r.read().decode("utf-8")


def test_http_api_smoke(tmp_path, scenario_dir, prepared_game):
    server = create_server(port=0, scenarios_dir=tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        status, body = _get(server, "/")
        assert status == 200 and "Facilitator" in body

        status, body = _get(server, "/api/scenarios")
        assert status == 200 and "Global AI Live" in body

        run = prepared_game
        status, body = _get(server, f"/api/game?run={run}")
        assert status == 200
        assert json.loads(body)["pending_turn"] == 1

        status, body = _get(server, f"/api/turn?run={run}&turn=1")
        assert status == 200
        payload = json.loads(body)
        assert payload["menus"]["eu"]["options"][0]["title"] == "Sign the accord"
    finally:
        server.shutdown()
        thread.join()
