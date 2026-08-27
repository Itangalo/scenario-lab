"""The trajectory regime must never reach the regulator's own prompt.

Forking Futures asks whether a regulator can tell which world it is in from
what happens to it. That question only exists while the regime is withheld
from the actor, so the withholding is a property worth testing rather than
trusting.

The leak this guards against is not hypothetical. When the arms moved from
draws to variants, each variant gained its own ``description``, and the actor
system prompt renders ``scenario_description`` verbatim ("The simulation
focuses on ..."). Every run of the 2026-08-26 batch therefore opened by telling
the regulator the regime it was supposed to infer. The old ``<!-- GM-ONLY -->``
truncation did not catch it: that guards background_context and world_state,
and the description reaches the prompt through neither.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scenario_lab.loader import load_scenario
from scenario_lab.prompts import PromptBuilder

VARIANTS_DIR = Path(__file__).parent.parent / "scenarios" / "forking-futures" / "variants"

# Strings that identify one arm. The regulator may reason over all three
# regimes as a hypothesis space -- that block is identical in every arm and is
# the point of the exercise -- so these are checked against the description
# slot, not against the whole prompt.
ARM_TELLS = (
    "FAST",
    "PLATEAU",
    "RLVR-LIMITED",
    "Trajectory arm",
    "saturates early",
    "decelerates visibly",
    "compounds through the whole horizon",
    "verifiable reward",
)

FOCUS_MARKER = "The simulation focuses on "


def _variant_files() -> list[Path]:
    return sorted(VARIANTS_DIR.glob("*.yaml"))


def test_variant_files_exist() -> None:
    """Guard the guard: a glob that silently matches nothing proves nothing."""
    assert len(_variant_files()) >= 6


@pytest.mark.parametrize("variant", _variant_files(), ids=lambda p: p.stem)
def test_arm_identity_absent_from_actor_description(variant: Path) -> None:
    """No variant may name its own arm in the actor's scenario description."""
    scenario = load_scenario(variant)
    builder = PromptBuilder(scenario)

    actors = scenario.actors
    actor_id = actors[0] if isinstance(actors, list) else next(iter(actors))
    actor_id = actor_id if isinstance(actor_id, str) else getattr(actor_id, "id", actor_id)

    system_prompt, _ = builder.build_actor_prompt(actor_id, 1, [])

    assert FOCUS_MARKER in system_prompt, "actor system prompt no longer renders a description"
    description = system_prompt.split(FOCUS_MARKER, 1)[1][:600]

    leaked = [tell for tell in ARM_TELLS if tell in description]
    assert not leaked, (
        f"{variant.name} leaks arm identity {leaked} into the regulator's prompt via "
        f"scenario_description. Variants must inherit the regime-neutral description "
        f"from scenario.yaml; keep arm-specific wording in a YAML comment."
    )


@pytest.mark.parametrize("variant", _variant_files(), ids=lambda p: p.stem)
def test_variants_do_not_define_their_own_description(variant: Path) -> None:
    """Catch the leak at its source, before it has to be found in a prompt."""
    assert "\ndescription:" not in variant.read_text(), (
        f"{variant.name} defines its own description. That field is rendered "
        f"verbatim into the actor prompt; inherit it from scenario.yaml instead."
    )
