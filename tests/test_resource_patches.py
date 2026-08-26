"""Tests for variant resource patches (partial overrides of shared resources)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scenario_lab.loader import load_config, load_scenario
from scenario_lab.models import Event
from scenario_lab.resource_patches import (
    apply_event_patches,
    apply_metric_rule_patches,
    parse_event_patch,
)


# ---------------------------------------------------------------------------
# Event patches
# ---------------------------------------------------------------------------

def _events() -> list[Event]:
    return [
        Event(
            id="precursor",
            description="A precursor. **This is a precursor.**",
            condition="Possible in any turn.",
            probability="PLATEAU 12%; FAST 18%; RLVR-LIMITED 25%. Add 5 points if gap is below 20.",
            can_repeat=True,
        ),
        Event(
            id="escalation",
            description="The big one.",
            condition="Always eligible; list every turn.",
            probability="Gate open: 22%. Gate shut: 4%.",
            can_repeat=False,
        ),
    ]


def test_event_patch_overrides_only_stated_fields(tmp_path):
    patch = tmp_path / "p.md"
    patch.write_text(
        "## Recon\n"
        "**ID:** precursor\n"
        "**Probability:** 18%. Add 5 points if gap is below 20.\n",
        encoding="utf-8",
    )

    result = apply_event_patches(_events(), patch)

    patched = next(e for e in result if e.id == "precursor")
    assert patched.probability == "18%. Add 5 points if gap is below 20."
    assert patched.condition == "Possible in any turn."          # inherited
    assert "This is a precursor" in patched.description          # inherited
    assert patched.can_repeat is True                            # inherited


def test_event_patch_removes_event(tmp_path):
    patch = tmp_path / "p.md"
    patch.write_text(
        "## Gone\n**ID:** escalation\n**Remove:** yes\n", encoding="utf-8"
    )

    result = apply_event_patches(_events(), patch)

    assert [e.id for e in result] == ["precursor"]


def test_event_patch_remove_unknown_is_error_with_suggestion(tmp_path):
    patch = tmp_path / "p.md"
    patch.write_text("## X\n**ID:** escalaton\n**Remove:** yes\n", encoding="utf-8")

    with pytest.raises(ValueError, match="nearest existing: .*escalation"):
        apply_event_patches(_events(), patch)


def test_event_patch_adds_new_event_when_complete(tmp_path):
    patch = tmp_path / "p.md"
    patch.write_text(
        "## New thing\n"
        "**ID:** brand_new_event\n"
        "**Probability:** 9%.\n"
        "**Description:** Something only this arm has.\n",
        encoding="utf-8",
    )

    result = apply_event_patches(_events(), patch)

    added = result[-1]
    assert added.id == "brand_new_event"
    assert added.description == "Something only this arm has."
    assert added.can_repeat is False
    assert added.condition == ""


def test_event_patch_unknown_incomplete_id_is_error_not_silent_addition(tmp_path):
    """A typo'd override must fail loudly, not silently create a new event."""
    patch = tmp_path / "p.md"
    patch.write_text(
        "## Oops\n**ID:** precusor\n**Probability:** 18%.\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="matches no existing event"):
        apply_event_patches(_events(), patch)


def test_event_patch_rejects_unknown_fields(tmp_path):
    patch = tmp_path / "p.md"
    patch.write_text(
        "## Weird\n**ID:** precursor\n**Probbility:** 50%.\n", encoding="utf-8"
    )

    # 'probbility' is not a known field: hard error rather than ignored.
    with pytest.raises(ValueError, match="unknown field"):
        parse_event_patch(patch)


def test_event_patch_skips_prose_sections_without_ids(tmp_path):
    patch = tmp_path / "p.md"
    patch.write_text(
        "# Patch notes\n\nSome prose explaining the patch.\n\n"
        "## Real change\n**ID:** precursor\n**Condition:** Only in wartime.\n",
        encoding="utf-8",
    )

    result = apply_event_patches(_events(), patch)

    assert len(result) == 2
    assert result[0].condition == "Only in wartime."


# ---------------------------------------------------------------------------
# Metric rule patches
# ---------------------------------------------------------------------------

RULES = "\n".join([
    "# Metric Rules",
    "",
    "Intro line.",
    "",
    "1. **Growth.** Branched text:",
    "   - **FAST:** +2 to +4.",
    "   - **PLATEAU:** +1 to +2.",
    "",
    "2. **Trails.** China follows.",
])


def test_rule_patch_replaces_rule_wholesale():
    patch = tmp_path_file(
        "1. **Growth.** Single-regime text, +3 per turn into **90-100**.\n"
    )

    result = apply_metric_rule_patches(RULES, patch)

    assert "Single-regime text" in result
    assert "- **FAST:**" not in result
    assert "2. **Trails.** China follows." in result      # untouched
    assert "Intro line." in result                        # preamble kept


def test_rule_patch_appends_new_numbers():
    patch = tmp_path_file("3. **Extra physics.** Arm-specific addition.\n")

    result = apply_metric_rule_patches(RULES, patch)

    assert "3. **Extra physics.**" in result


def test_rule_patch_gap_number_is_error():
    """A patch may replace existing numbers or append past the max – not fill
    a gap in the middle of the base's numbering (that signals a mismatch)."""
    gapped = "1. **A.**\n\n3. **C.**\n"
    patch = tmp_path_file("2. **B.**\n")

    with pytest.raises(ValueError, match="rule 2"):
        apply_metric_rule_patches(gapped, patch)


def test_rule_patch_appends_past_max():
    patch = tmp_path_file("7. **Skipped ahead.**\n")
    result = apply_metric_rule_patches(RULES, patch)
    assert "7. **Skipped ahead.**" in result


def tmp_path_file(content: str) -> Path:
    import tempfile

    f = Path(tempfile.mkdtemp()) / "rules.patch.md"
    f.write_text(content, encoding="utf-8")
    return f


# ---------------------------------------------------------------------------
# Loader integration: declaration, inheritance by extension, application
# ---------------------------------------------------------------------------

def _scenario_tree(tmp_path: Path):
    """Base scenario + arm variant + urgent variant chained on the arm."""
    base = tmp_path / "base-scenario"
    base.mkdir()
    (base / "metrics.md").write_text(
        "## m\n**ID:** m\n**Min:** 0\n**Max:** 100\n**Start value:** 10\n"
    )
    (base / "events.md").write_text(
        "## Thing\n**ID:** thing\n**Condition:** Any turn.\n"
        "**Probability:** ARM-A 10%; ARM-B 20%.\n"
        "**Can repeat:** Yes\n**Description:** Base description.\n"
    )
    (base / "metric-rules.md").write_text(
        "1. **Physics A.**\n2. **Physics B.**\n"
    )
    background = base / "background" / "actors"
    background.mkdir(parents=True)
    (base / "background" / "context.md").write_text("World.")
    (background / "reg.md").write_text(
        "# R\n## Short description\nR\n## Long description\nR\n"
        "### Statements\n- `s` (position): x\n"
    )
    (base / "scenario.yaml").write_text(yaml.dump({
        "name": "base", "description": "b", "start_date": "2026-01",
        "time_scale": "months", "max_turns": 2, "actors": ["reg"],
    }))

    variants = base / "variants"
    variants.mkdir()
    (variants / "arm-a.events.patch.md").write_text(
        "## Thing\n**ID:** thing\n**Probability:** 10%.\n", encoding="utf-8"
    )
    (variants / "arm-a.rules.patch.md").write_text(
        "1. **Physics A (arm-a edition).**\n"
        "3. **Arm-specific rule.**\n",
        encoding="utf-8",
    )
    (variants / "arm-b.events.patch.md").write_text(
        "## Thing\n**ID:** thing\n**Probability:** 20%.\n", encoding="utf-8"
    )
    (variants / "arm-a.yaml").write_text(yaml.dump({
        "base": "../scenario.yaml",
        "name": "arm-a",
        "patches": [
            {"resource": "events", "path": "arm-a.events.patch.md"},
            {"resource": "metric_rules", "path": "arm-a.rules.patch.md"},
        ],
    }))
    (variants / "urgent-on-a.yaml").write_text(yaml.dump({
        "base": "arm-a.yaml",
        "name": "urgent-on-a",
        "actors": ["reg-urgent"],
    }))
    return base, variants


def test_variant_patches_apply_and_chain_across_levels(tmp_path):
    _scenario_tree(tmp_path)
    base_dir = tmp_path / "base-scenario"
    variants = base_dir / "variants"

    # The actor file for the chained variant lives where resources resolve.
    (base_dir / "background" / "actors" / "reg-urgent.md").write_text(
        "# RU\n## Short description\nRU\n## Long description\nRU\n"
        "### Statements\n- `s` (position): x\n"
    )

    plain = load_scenario(variants / "arm-a.yaml")
    assert plain.events[0].probability == "10%."
    assert "arm-a edition" in plain.metric_rules
    assert "Arm-specific rule" in plain.metric_rules
    assert [p.resource for p in plain.config.patches] == ["events", "metric_rules"]

    chained = load_scenario(variants / "urgent-on-a.yaml")
    # Patches extend across the chain: urgent-on-arm-a sees arm-a's overrides.
    assert chained.events[0].probability == "10%."
    assert "arm-a edition" in chained.metric_rules
    assert [len(p.path) for p in chained.config.patches] == [
        len(p.path) for p in plain.config.patches
    ]


def test_variant_yaml_records_patches_in_run_snapshot_shape(tmp_path):
    _scenario_tree(tmp_path)
    config = load_config((tmp_path / "base-scenario" / "variants" / "arm-a.yaml"))

    payload = [{"resource": p.resource, "path": p.path} for p in config.patches]
    assert payload == [
        {"resource": "events", "path": payload[0]["path"]},
        {"resource": "metric_rules", "path": payload[1]["path"]},
    ]
    assert all(Path(p["path"]).is_absolute() for p in payload)


def test_variant_patch_missing_file_fails_loudly(tmp_path):
    _scenario_tree(tmp_path)
    variants = tmp_path / "base-scenario" / "variants"
    (variants / "broken.yaml").write_text(yaml.dump({
        "base": "../scenario.yaml",
        "name": "broken",
        "patches": [{"resource": "events", "path": "nope.patch.md"}],
    }))

    with pytest.raises(FileNotFoundError):
        load_scenario(variants / "broken.yaml")


def test_variant_patch_unknown_resource_fails_loudly(tmp_path):
    _scenario_tree(tmp_path)
    variants = tmp_path / "base-scenario" / "variants"
    (variants / "wrong.yaml").write_text(yaml.dump({
        "base": "../scenario.yaml",
        "name": "wrong",
        "patches": [{"resource": "actors_md", "path": "arm-a.events.patch.md"}],
    }))

    with pytest.raises(ValueError, match="unknown patchable resource"):
        load_config(variants / "wrong.yaml")


def test_json_serializable_snapshot_includes_patches(tmp_path):
    _scenario_tree(tmp_path)
    config = load_config((tmp_path / "base-scenario" / "variants" / "arm-a.yaml"))
    snapshot = [{"resource": p.resource, "path": p.path} for p in config.patches]
    assert json.loads(json.dumps(snapshot)) == snapshot
