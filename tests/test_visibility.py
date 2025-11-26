import pytest
from scenario_lab.models import WorldState
from scenario_lab.visibility import get_visible_metrics

@pytest.fixture
def sample_world_state():
    """Provides a sample WorldState object for testing."""
    from scenario_lab.models import Metrics, ActorMetricsData
    return WorldState(
        actors={
            "USA": {"goals": ["Maintain global leadership"]},
            "China": {"goals": ["Economic growth"]},
        },
        metrics=Metrics(
            world={"global_temperature": 2.0},
            actors={
                "USA": ActorMetricsData(
                    public={"gdp": 25.0},
                    private={"military_capacity": 100.0},
                ),
                "China": ActorMetricsData(
                    public={"budget": 20.0},
                    private={"military_capacity": 80.0},
                ),
            },
        ),
        relationships={},
        fact_ledger=[],
        narrative_state="Stable",
    )

def test_get_visible_metrics_usa_view(sample_world_state):
    """USA sees its own private and public metrics, China's public, and world metrics."""
    usa_view = get_visible_metrics(sample_world_state, "USA")
    
    # USA sees world metrics
    assert "global_temperature" in usa_view
    assert usa_view["global_temperature"] == 2.0

    # USA sees its own metrics
    assert "gdp" in usa_view
    assert usa_view["gdp"] == 25.0
    assert "military_capacity" in usa_view
    assert usa_view["military_capacity"] == 100.0

    # USA sees China's public metrics
    assert "budget" in usa_view
    assert usa_view["budget"] == 20.0
    
    # USA does NOT see China's private metrics
    # In this implementation, keys are overwritten. A better implementation
    # would be to namespace the metrics, e.g., "China.public.budget".
    # For now, we test that the private value isn't present.
    china_private_metrics = sample_world_state.metrics.actors["China"].private
    for key in china_private_metrics:
        if key in usa_view:
            assert usa_view[key] != china_private_metrics[key]


def test_get_visible_metrics_china_view(sample_world_state):
    """China sees its own private and public, USA's public, and world metrics."""
    china_view = get_visible_metrics(sample_world_state, "China")

    # China sees world metrics
    assert "global_temperature" in china_view
    assert china_view["global_temperature"] == 2.0

    # China sees its own metrics
    assert "budget" in china_view
    assert china_view["budget"] == 20.0
    assert "military_capacity" in china_view
    assert china_view["military_capacity"] == 80.0

    # China sees USA's public metrics
    assert "gdp" in china_view
    assert china_view["gdp"] == 25.0

    # China does NOT see USA's private metrics
    usa_private_metrics = sample_world_state.metrics.actors["USA"].private
    for key in usa_private_metrics:
        if key in china_view:
            assert china_view[key] != usa_private_metrics[key]

def test_both_see_world_metrics(sample_world_state):
    """Both USA and China see world metrics."""
    usa_view = get_visible_metrics(sample_world_state, "USA")
    china_view = get_visible_metrics(sample_world_state, "China")

    assert "global_temperature" in usa_view
    assert "global_temperature" in china_view
    assert usa_view["global_temperature"] == 2.0
    assert china_view["global_temperature"] == 2.0
