"""Tests for progress display helpers."""

from scenario_lab.progress import ProgressTracker


def test_progress_tracker_labels_three_phases(capsys):
    """Steps follow the three-phase cycle, with no generic fallback."""
    tracker = ProgressTracker(
        total_turns=10,
        actors=[],
        enabled=False,
        has_constitution=True,
    )

    tracker._update_step_display(3, "", "start")

    captured = capsys.readouterr()
    assert "[3/3] Updating the world..." in captured.out
