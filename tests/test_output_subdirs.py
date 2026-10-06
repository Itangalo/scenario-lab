"""Output subfolders: runs may sit one level under runs/ and stay discoverable."""

import json
from pathlib import Path

import pytest

from scenario_lab.loader import load_scenario
from scenario_lab.output import OutputManager, iter_run_dirs
from scenario_lab.resume import get_scenario_path_from_run

REPO_ROOT = Path(__file__).resolve().parents[1]


def _scenario_dir(tmp_path):
    scenario_dir = tmp_path / "sweden-ai-2030"
    scenario_dir.mkdir(exist_ok=True)
    link = scenario_dir / "metrics.md"
    if not link.exists():
        link.symlink_to(REPO_ROOT / "scenarios/sweden-ai-2030" / "metrics.md")
    return scenario_dir


def _manager(tmp_path):
    scenario = load_scenario("scenarios/sweden-ai-2030")
    return OutputManager(scenario, tmp_path)


def test_start_run_with_subdir(tmp_path):
    run_dir = _manager(tmp_path).start_run(subdir="arm-fast")
    assert run_dir.parent.name == "arm-fast"
    assert (run_dir / "config.json").is_file()


def test_start_run_rejects_escaping_subdir(tmp_path):
    with pytest.raises(ValueError):
        _manager(tmp_path).start_run(subdir="../elsewhere")
    with pytest.raises(ValueError):
        _manager(tmp_path).start_run(subdir="/abs")
    with pytest.raises(ValueError):
        _manager(tmp_path).start_run(subdir="  ")


def test_iter_run_dirs_finds_nested_and_top_level(tmp_path):
    manager = _manager(tmp_path)
    top = manager.start_run()
    nested = manager.start_run(subdir="arm-fast")
    (tmp_path / "runs" / "batch-logs").mkdir(parents=True)
    found = iter_run_dirs(tmp_path / "runs")
    assert found == sorted([top, nested])


def test_scenario_path_resolves_through_subdir(tmp_path):
    scenario_dir = _scenario_dir(tmp_path)
    scenario = load_scenario("scenarios/sweden-ai-2030")
    manager = OutputManager(scenario, scenario_dir)
    run_dir = manager.start_run(subdir="arm-fast")
    assert get_scenario_path_from_run(run_dir) == scenario_dir


def test_phases_survive_subdir_resume(tmp_path):
    """Mid-turn resume works when the run sits in a subfolder."""
    from scenario_lab.resume import detect_last_phase

    scenario_dir = _scenario_dir(tmp_path)
    scenario = load_scenario("scenarios/sweden-ai-2030")
    manager = OutputManager(scenario, scenario_dir)
    run_dir = manager.start_run(subdir="arm-fast")
    turn_dir = run_dir / "turn-01"
    turn_dir.mkdir()
    (turn_dir / "1-events.json").write_text(json.dumps([]))
    assert detect_last_phase(run_dir, 1) == "events"
    assert get_scenario_path_from_run(run_dir) == scenario_dir
