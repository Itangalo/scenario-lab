"""Tests for progress display helpers."""

from scenario_lab.progress import ProgressTracker


def test_progress_tracker_labels_step_six_when_constitution_enabled(capsys):
    """The final summary step should not fall back to generic 'Step 6'."""
    tracker = ProgressTracker(
        total_turns=10,
        actors=[],
        enabled=False,
        has_constitution=True,
    )

    tracker._update_step_display(6, "", "start")

    captured = capsys.readouterr()
    assert "[6/6] Updating historical summary..." in captured.out
