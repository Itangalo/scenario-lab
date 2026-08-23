"""Flat prompt eval for the statement relevance check.

The check gates every commitment- and identity-tier statement change, so if a
cheap referee model cannot hold it, the whole mechanism either leaks (laundered
triggers accepted) or freezes (real ones rejected). This suite exercises it
directly instead of waiting for a run to happen to produce one, which a 14-turn
run did not.

Live LLM suite: opt-in via `pytest -m integration`.

    OPENROUTER_API_KEY=... python3 -m pytest tests/evals/statement-relevance -m integration -v
"""

import os
import sys
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.integration

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scenario_lab.models import ModelRoute  # noqa: E402
from scenario_lab.orchestrator import _parse_relevance_result  # noqa: E402
from scenario_lab.providers.registry import ProviderRegistry  # noqa: E402
from scenario_lab.router import FallbackRouter  # noqa: E402

EVAL_DIR = Path(__file__).parent
TEMPLATES = PROJECT_ROOT / "templates"

# The models actually plausible as the referee route.
CANDIDATE_MODELS = os.getenv(
    "RELEVANCE_EVAL_MODELS", "qwen/qwen3-235b-a22b-2507"
).split(",")


def load_cases() -> list[dict]:
    data = yaml.safe_load((EVAL_DIR / "cases.yaml").read_text(encoding="utf-8"))
    return data["cases"]


@pytest.fixture(scope="session")
def system_prompt() -> str:
    return (TEMPLATES / "system-prompts" / "statement_relevance.md").read_text(
        encoding="utf-8"
    )


@pytest.fixture(scope="session")
def user_template() -> str:
    return (TEMPLATES / "user-prompts" / "statement_relevance.md").read_text(
        encoding="utf-8"
    )


def build_user_prompt(template: str, case: dict) -> str:
    from jinja2.sandbox import SandboxedEnvironment

    env = SandboxedEnvironment()
    return env.from_string(template).render(
        actor_name="The Actor",
        statement_id=case["statement"]["id"],
        statement_tier=case["statement"]["tier"],
        statement_text=case["statement"]["text"],
        proposal_summary=case["proposal"],
        trigger=case["trigger"],
        triggered_events=case.get("events", "(none this turn)"),
        world_state=case.get("world_state", ""),
        previous_actions="",
    )


@pytest.fixture(scope="session")
def clients() -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    registry = ProviderRegistry()
    built = {}
    for model in CANDIDATE_MODELS:
        model = model.strip()
        if model:
            built[model] = FallbackRouter(
                [ModelRoute(provider="openrouter", model=model)],
                registry,
                temperature=0.0,
                max_tokens=800,
            )
    return built


@pytest.mark.parametrize("case", load_cases(), ids=lambda c: c["id"])
@pytest.mark.parametrize("model", CANDIDATE_MODELS, ids=lambda m: m.strip())
def test_relevance_verdict(case, model, clients, system_prompt, user_template):
    """The referee must separate real, bearing triggers from invented and laundered ones."""
    client = clients[model.strip()]
    user = build_user_prompt(user_template, case)

    response = client.complete(system_prompt, user)
    result = _parse_relevance_result(response.content)

    assert result is not None, (
        f"[{model}] unparseable relevance answer for {case['id']}:\n{response.content}"
    )

    verdict = result["verdict"]
    assert verdict == case["expect"], (
        f"[{model}] {case['id']}: expected {case['expect']}, got {verdict}. "
        f"quote={result.get('quote')!r} reason={result.get('reason')!r}. "
        f"{case.get('note', '')}"
    )

    # A BEARS verdict must be evidenced, or the quotation half has silently
    # stopped working while the relevance half still answers.
    if verdict == "BEARS":
        assert result.get("quote", "").strip(), (
            f"[{model}] {case['id']}: BEARS with no quote is not an answer"
        )
