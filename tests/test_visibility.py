import pytest
from scenario_lab.models import WorldState, Metrics, ActorMetricsData
from scenario_lab.utils import get_visible_metrics

@pytest.fixture
def sample_world_state_metrics():
    """Provides a sample Metrics object for testing."""
    return Metrics(
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
    )

def test_usa_sees_world_metrics(sample_world_state_metrics):
    """Test that USA can see world metrics."""
    result = get_visible_metrics(sample_world_state_metrics, "USA")
    assert result.world["global_temperature"] == 2.0

def test_usa_sees_own_private_metrics(sample_world_state_metrics):
    """Test that USA can see its own private metrics."""
    result = get_visible_metrics(sample_world_state_metrics, "USA")
    assert result.actors["USA"].private["military_capacity"] == 100.0

def test_usa_does_not_see_china_private_metrics(sample_world_state_metrics):
    """Test that USA does not see China's private metrics."""
    result = get_visible_metrics(sample_world_state_metrics, "USA")
    assert "China" in result.actors
    assert result.actors["China"].private == {}

def test_usa_sees_china_public_metrics(sample_world_state_metrics):
    """Test that USA can see China's public metrics."""
    result = get_visible_metrics(sample_world_state_metrics, "USA")
    assert result.actors["China"].public["budget"] == 20.0