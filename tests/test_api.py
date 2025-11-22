"""
Tests for API Endpoints

Comprehensive tests for all REST API and WebSocket endpoints in scenario_lab/api/app.py.
Uses FastAPI's TestClient for HTTP endpoints and WebSocket testing.
"""
import os
import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from scenario_lab.api.settings import reset_settings
from scenario_lab.api.rate_limit import reset_rate_limiter


@pytest.fixture(autouse=True)
def reset_state():
    """Reset settings and rate limiter before each test"""
    reset_settings()
    reset_rate_limiter()
    # Set dev mode to disable auth/rate limiting by default for most tests
    os.environ["SCENARIO_LAB_DEV_MODE"] = "true"
    yield
    reset_settings()
    reset_rate_limiter()
    for key in [
        "SCENARIO_LAB_API_KEY",
        "SCENARIO_LAB_AUTH_ENABLED",
        "SCENARIO_LAB_DEV_MODE",
        "SCENARIO_LAB_RATE_LIMIT_ENABLED",
    ]:
        os.environ.pop(key, None)


@pytest.fixture
def client():
    """Create a test client for the API"""
    from scenario_lab.api.app import app
    return TestClient(app)


@pytest.fixture
def mock_database():
    """Create a mock database"""
    mock_db = MagicMock()
    return mock_db


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_returns_api_info(self, client):
        """Test that root endpoint returns API information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Scenario Lab API"
        assert "version" in data
        assert data["status"] == "running"
        assert "endpoints" in data

    def test_root_contains_endpoint_list(self, client):
        """Test that root endpoint lists available endpoints"""
        response = client.get("/")
        data = response.json()
        endpoints = data["endpoints"]
        assert "scenarios" in endpoints
        assert "runs" in endpoints
        assert "docs" in endpoints
        assert "openapi" in endpoints


class TestHealthEndpoint:
    """Tests for the health check endpoint"""

    def test_health_returns_healthy_status(self, client):
        """Test that health endpoint returns healthy status"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "database" in data
        assert "running_scenarios" in data

    def test_health_shows_auth_status(self, client):
        """Test that health endpoint shows authentication status"""
        response = client.get("/api/health")
        data = response.json()
        assert "auth_enabled" in data
        assert "rate_limit_enabled" in data
        assert "dev_mode" in data

    def test_health_shows_running_scenarios_count(self, client):
        """Test that health endpoint shows count of running scenarios"""
        response = client.get("/api/health")
        data = response.json()
        assert isinstance(data["running_scenarios"], int)
        assert data["running_scenarios"] >= 0


class TestScenarioExecuteEndpoint:
    """Tests for the scenario execution endpoint"""

    def test_execute_returns_404_for_nonexistent_scenario(self, client):
        """Test that execute returns 404 for non-existent scenario path"""
        response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": "/nonexistent/path/to/scenario"}
        )
        assert response.status_code == 404
        assert "Scenario not found" in response.json()["detail"]

    def test_execute_returns_scenario_status(self, client, tmp_path):
        """Test that execute returns scenario status for valid scenario"""
        # Create a minimal valid scenario directory
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        assert response.status_code == 200
        data = response.json()
        assert "scenario_id" in data
        assert data["status"] == "initializing"
        assert data["current_turn"] == 0
        assert data["total_cost"] == 0.0

    def test_execute_accepts_optional_parameters(self, client, tmp_path):
        """Test that execute accepts optional parameters"""
        # Create a minimal valid scenario directory
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        response = client.post(
            "/api/scenarios/execute",
            json={
                "scenario_path": str(scenario_dir),
                "end_turn": 5,
                "credit_limit": 10.0,
                "enable_database": False
            }
        )
        assert response.status_code == 200


class TestScenarioStatusEndpoint:
    """Tests for the scenario status endpoint"""

    def test_status_returns_404_for_unknown_scenario(self, client):
        """Test that status returns 404 for unknown scenario ID"""
        response = client.get("/api/scenarios/unknown-scenario-id/status")
        assert response.status_code == 404
        assert "Scenario not found" in response.json()["detail"]

    def test_status_returns_scenario_info(self, client, tmp_path):
        """Test that status returns scenario information after execution starts"""
        # Create a minimal valid scenario directory
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        # Start a scenario
        execute_response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        scenario_id = execute_response.json()["scenario_id"]

        # Get status
        response = client.get(f"/api/scenarios/{scenario_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["scenario_id"] == scenario_id
        assert "status" in data
        assert "current_turn" in data
        assert "total_cost" in data


class TestRunsEndpoints:
    """Tests for the runs-related endpoints"""

    def test_list_runs_returns_503_without_database(self, client):
        """Test that list runs returns 503 when database is not configured"""
        with patch("scenario_lab.api.app.database", None):
            response = client.get("/api/runs")
            assert response.status_code == 503
            assert "Database not configured" in response.json()["detail"]

    def test_list_runs_returns_runs_with_database(self, client, mock_database):
        """Test that list runs returns runs when database is available"""
        mock_run = MagicMock()
        mock_run.id = "run-001"
        mock_run.scenario_name = "Test Scenario"
        mock_run.status = "completed"
        mock_run.total_turns = 5
        mock_run.total_cost = 0.5
        mock_run.created = datetime.now()
        mock_database.list_runs.return_value = [mock_run]

        with patch("scenario_lab.api.app.database", mock_database):
            response = client.get("/api/runs")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["run_id"] == "run-001"
            assert data[0]["scenario_name"] == "Test Scenario"

    def test_list_runs_accepts_scenario_filter(self, client, mock_database):
        """Test that list runs accepts scenario filter"""
        mock_database.list_runs.return_value = []

        with patch("scenario_lab.api.app.database", mock_database):
            response = client.get("/api/runs?scenario=test-scenario")
            assert response.status_code == 200
            mock_database.list_runs.assert_called_once_with(scenario_id="test-scenario")

    def test_get_run_returns_503_without_database(self, client):
        """Test that get run returns 503 when database is not configured"""
        with patch("scenario_lab.api.app.database", None):
            response = client.get("/api/runs/run-001")
            assert response.status_code == 503
            assert "Database not configured" in response.json()["detail"]

    def test_get_run_returns_404_for_unknown_run(self, client, mock_database):
        """Test that get run returns 404 for unknown run ID"""
        mock_database.get_run.return_value = None

        with patch("scenario_lab.api.app.database", mock_database):
            response = client.get("/api/runs/unknown-run")
            assert response.status_code == 404
            assert "Run not found" in response.json()["detail"]

    def test_get_run_returns_statistics(self, client, mock_database):
        """Test that get run returns run statistics"""
        mock_run = MagicMock()
        mock_database.get_run.return_value = mock_run
        mock_database.get_run_statistics.return_value = {
            "run_id": "run-001",
            "total_turns": 5,
            "total_cost": 0.5
        }

        with patch("scenario_lab.api.app.database", mock_database):
            response = client.get("/api/runs/run-001")
            assert response.status_code == 200
            data = response.json()
            assert data["run_id"] == "run-001"

    def test_get_run_statistics_returns_503_without_database(self, client):
        """Test that get run statistics returns 503 when database not configured"""
        with patch("scenario_lab.api.app.database", None):
            response = client.get("/api/runs/run-001/statistics")
            assert response.status_code == 503

    def test_get_run_statistics_returns_404_for_unknown_run(self, client, mock_database):
        """Test that get run statistics returns 404 for unknown run"""
        mock_database.get_run_statistics.return_value = None

        with patch("scenario_lab.api.app.database", mock_database):
            response = client.get("/api/runs/unknown-run/statistics")
            assert response.status_code == 404

    def test_get_run_statistics_returns_data(self, client, mock_database):
        """Test that get run statistics returns statistics data"""
        mock_database.get_run_statistics.return_value = {
            "run_id": "run-001",
            "metrics": {"metric1": 0.5}
        }

        with patch("scenario_lab.api.app.database", mock_database):
            response = client.get("/api/runs/run-001/statistics")
            assert response.status_code == 200
            data = response.json()
            assert "metrics" in data


class TestCompareRunsEndpoint:
    """Tests for the compare runs endpoint"""

    def test_compare_runs_returns_503_without_database(self, client):
        """Test that compare runs returns 503 when database not configured"""
        with patch("scenario_lab.api.app.database", None):
            response = client.post("/api/runs/compare", json=["run-001", "run-002"])
            assert response.status_code == 503

    def test_compare_runs_returns_comparison_data(self, client, mock_database):
        """Test that compare runs returns comparison data"""
        mock_database.compare_runs.return_value = {
            "runs": ["run-001", "run-002"],
            "comparison": {}
        }

        with patch("scenario_lab.api.app.database", mock_database):
            response = client.post("/api/runs/compare", json=["run-001", "run-002"])
            assert response.status_code == 200
            data = response.json()
            assert "runs" in data


class TestMetricsAggregateEndpoint:
    """Tests for the metrics aggregation endpoint"""

    def test_aggregate_metric_returns_503_without_database(self, client):
        """Test that aggregate metric returns 503 when database not configured"""
        with patch("scenario_lab.api.app.database", None):
            response = client.get("/api/metrics/test_metric/aggregate")
            assert response.status_code == 503

    def test_aggregate_metric_returns_aggregation_data(self, client, mock_database):
        """Test that aggregate metric returns aggregation data"""
        mock_database.aggregate_metrics.return_value = {
            "metric": "test_metric",
            "values": [0.5, 0.6, 0.7],
            "mean": 0.6
        }

        with patch("scenario_lab.api.app.database", mock_database):
            response = client.get("/api/metrics/test_metric/aggregate")
            assert response.status_code == 200
            data = response.json()
            assert data["metric"] == "test_metric"

    def test_aggregate_metric_accepts_scenario_filter(self, client, mock_database):
        """Test that aggregate metric accepts scenario filter"""
        mock_database.aggregate_metrics.return_value = {}

        with patch("scenario_lab.api.app.database", mock_database):
            response = client.get("/api/metrics/test_metric/aggregate?scenario=test-scenario")
            assert response.status_code == 200
            mock_database.aggregate_metrics.assert_called_once_with(
                "test_metric",
                scenario="test-scenario"
            )


class TestPauseResumeEndpoints:
    """Tests for the pause and resume endpoints"""

    def test_pause_returns_404_for_unknown_scenario(self, client):
        """Test that pause returns 404 for unknown scenario"""
        response = client.post("/api/scenarios/unknown-id/pause")
        assert response.status_code == 404
        assert "Scenario not found" in response.json()["detail"]

    def test_pause_returns_400_for_uninitialized_scenario(self, client, tmp_path):
        """Test that pause returns 400 for scenario without runner"""
        # Create and start a scenario
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        execute_response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        scenario_id = execute_response.json()["scenario_id"]

        # Immediately try to pause before runner is initialized
        from scenario_lab.api.app import running_scenarios
        # Remove runner to simulate not yet initialized state
        running_scenarios[scenario_id]["runner"] = None

        response = client.post(f"/api/scenarios/{scenario_id}/pause")
        assert response.status_code == 400
        assert "not yet initialized" in response.json()["detail"]

    def test_resume_returns_404_for_unknown_scenario(self, client):
        """Test that resume returns 404 for unknown scenario"""
        response = client.post("/api/scenarios/unknown-id/resume")
        assert response.status_code == 404
        assert "Scenario not found" in response.json()["detail"]

    def test_resume_returns_400_for_uninitialized_scenario(self, client, tmp_path):
        """Test that resume returns 400 for scenario without runner"""
        # Create and start a scenario
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        execute_response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        scenario_id = execute_response.json()["scenario_id"]

        # Remove runner to simulate not yet initialized state
        from scenario_lab.api.app import running_scenarios
        running_scenarios[scenario_id]["runner"] = None

        response = client.post(f"/api/scenarios/{scenario_id}/resume")
        assert response.status_code == 400
        assert "not yet initialized" in response.json()["detail"]


class TestHumanDecisionEndpoint:
    """Tests for the human decision submission endpoint"""

    def test_human_decision_returns_404_for_unknown_scenario(self, client):
        """Test that human decision returns 404 for unknown scenario"""
        response = client.post(
            "/api/scenarios/unknown-id/human-decision",
            json={
                "actor": "Human Actor",
                "long_term_goals": ["Goal 1"],
                "short_term_priorities": ["Priority 1"],
                "reasoning": "Test reasoning",
                "action": "Test action"
            }
        )
        assert response.status_code == 404
        assert "Scenario not found" in response.json()["detail"]

    def test_human_decision_returns_400_for_uninitialized_scenario(self, client, tmp_path):
        """Test that human decision returns 400 for scenario without runner"""
        # Create and start a scenario
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        execute_response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        scenario_id = execute_response.json()["scenario_id"]

        # Remove runner to simulate not yet initialized state
        from scenario_lab.api.app import running_scenarios
        running_scenarios[scenario_id]["runner"] = None

        response = client.post(
            f"/api/scenarios/{scenario_id}/human-decision",
            json={
                "actor": "Human Actor",
                "long_term_goals": ["Goal 1"],
                "short_term_priorities": ["Priority 1"],
                "reasoning": "Test reasoning",
                "action": "Test action"
            }
        )
        assert response.status_code == 400
        assert "not yet initialized" in response.json()["detail"]

    def test_human_decision_accepts_valid_decision(self, client, tmp_path):
        """Test that human decision accepts valid decision data"""
        # Create and start a scenario
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        execute_response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        scenario_id = execute_response.json()["scenario_id"]

        # Set up a mock runner
        from scenario_lab.api.app import running_scenarios
        running_scenarios[scenario_id]["runner"] = MagicMock()

        response = client.post(
            f"/api/scenarios/{scenario_id}/human-decision",
            json={
                "actor": "Human Actor",
                "long_term_goals": ["Achieve goal 1", "Achieve goal 2"],
                "short_term_priorities": ["Priority 1"],
                "reasoning": "Test reasoning for the decision",
                "action": "Take test action"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Decision received"
        assert data["actor"] == "Human Actor"
        assert data["scenario_id"] == scenario_id


class TestWebSocketStreaming:
    """Tests for WebSocket streaming endpoint"""

    def test_websocket_timeout_for_nonexistent_scenario(self, client):
        """Test that WebSocket times out for non-existent scenario"""
        with client.websocket_connect("/api/scenarios/nonexistent/stream") as websocket:
            # Should receive error and close
            data = websocket.receive_json()
            assert "error" in data
            assert "not found" in data["error"] or "timeout" in data["error"]

    def test_websocket_connects_for_existing_scenario(self, client, tmp_path):
        """Test that WebSocket connects for existing scenario"""
        # Create and start a scenario
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        # Start the scenario first
        execute_response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        scenario_id = execute_response.json()["scenario_id"]

        # Set up mock runner with event bus
        from scenario_lab.api.app import running_scenarios
        mock_runner = MagicMock()
        mock_event_bus = MagicMock()
        mock_runner.event_bus = mock_event_bus
        running_scenarios[scenario_id]["runner"] = mock_runner
        running_scenarios[scenario_id]["status"] = "completed"

        # Connect to WebSocket
        with client.websocket_connect(f"/api/scenarios/{scenario_id}/stream") as websocket:
            # Should receive scenario_finished message since status is completed
            data = websocket.receive_json()
            assert data["type"] == "scenario_finished"
            assert "status" in data["data"]


class TestRequestValidation:
    """Tests for request validation"""

    def test_execute_requires_scenario_path(self, client):
        """Test that execute requires scenario_path field"""
        response = client.post(
            "/api/scenarios/execute",
            json={}
        )
        assert response.status_code == 422  # Validation error

    def test_human_decision_requires_all_fields(self, client, tmp_path):
        """Test that human decision requires all required fields"""
        # Create and start a scenario
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        execute_response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        scenario_id = execute_response.json()["scenario_id"]

        # Missing required fields
        response = client.post(
            f"/api/scenarios/{scenario_id}/human-decision",
            json={"actor": "Human Actor"}  # Missing other required fields
        )
        assert response.status_code == 422  # Validation error

    def test_compare_runs_requires_list(self, client, mock_database):
        """Test that compare runs requires a list of run IDs"""
        with patch("scenario_lab.api.app.database", mock_database):
            response = client.post(
                "/api/runs/compare",
                json="not-a-list"
            )
            assert response.status_code == 422


class TestAPIDocumentation:
    """Tests for API documentation endpoints"""

    def test_openapi_spec_available(self, client):
        """Test that OpenAPI spec is available"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Scenario Lab API"

    def test_docs_endpoint_available(self, client):
        """Test that Swagger docs endpoint is available"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint_available(self, client):
        """Test that ReDoc endpoint is available"""
        response = client.get("/redoc")
        assert response.status_code == 200


class TestCORSConfiguration:
    """Tests for CORS configuration"""

    def test_cors_headers_present_for_allowed_origin(self, client):
        """Test that CORS headers are present for allowed origins"""
        # Preflight OPTIONS request with proper CORS headers
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "X-API-Key",
            }
        )
        # CORS preflight should return 200
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_allows_credentials(self, client):
        """Test that CORS allows credentials"""
        response = client.get(
            "/api/health",
            headers={"Origin": "http://localhost:3000"}
        )
        # Request should succeed
        assert response.status_code == 200

    def test_cors_response_headers_on_get(self, client):
        """Test that CORS response headers are set on GET requests"""
        response = client.get(
            "/",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
        # Check that CORS headers are present
        assert "access-control-allow-origin" in response.headers or "Access-Control-Allow-Origin" in response.headers


class TestErrorHandling:
    """Tests for error handling"""

    def test_invalid_json_returns_422(self, client):
        """Test that invalid JSON returns 422"""
        response = client.post(
            "/api/scenarios/execute",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_method_not_allowed_returns_405(self, client):
        """Test that unsupported method returns 405"""
        response = client.delete("/api/health")
        assert response.status_code == 405


class TestPauseResumeSuccessPaths:
    """Tests for successful pause and resume operations"""

    def test_pause_scenario_with_runner(self, client, tmp_path):
        """Test pausing a scenario that has a runner initialized"""
        # Create and start a scenario
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        execute_response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        scenario_id = execute_response.json()["scenario_id"]

        # Set up a mock runner
        from scenario_lab.api.app import running_scenarios
        running_scenarios[scenario_id]["runner"] = MagicMock()

        # Pause the scenario
        response = client.post(f"/api/scenarios/{scenario_id}/pause")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Scenario paused"
        assert data["scenario_id"] == scenario_id
        assert running_scenarios[scenario_id]["paused"] is True

    def test_resume_scenario_with_runner(self, client, tmp_path):
        """Test resuming a paused scenario"""
        # Create and start a scenario
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        execute_response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        scenario_id = execute_response.json()["scenario_id"]

        # Set up a mock runner and pause state
        from scenario_lab.api.app import running_scenarios
        running_scenarios[scenario_id]["runner"] = MagicMock()
        running_scenarios[scenario_id]["paused"] = True

        # Resume the scenario
        response = client.post(f"/api/scenarios/{scenario_id}/resume")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Scenario resumed"
        assert data["scenario_id"] == scenario_id
        assert running_scenarios[scenario_id]["paused"] is False


class TestRateLimitMiddleware:
    """Tests for rate limiting middleware behavior"""

    def test_rate_limit_headers_added_to_response(self, client):
        """Test that rate limit headers are added to responses"""
        reset_settings()
        reset_rate_limiter()
        os.environ["SCENARIO_LAB_DEV_MODE"] = "false"
        os.environ["SCENARIO_LAB_AUTH_ENABLED"] = "false"
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_REQUESTS"] = "100"

        from scenario_lab.api.app import app
        test_client = TestClient(app)

        response = test_client.get("/api/runs")
        # Even though database returns 503, rate limit headers should be present
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers

    def test_rate_limit_excludes_health_endpoint(self, client):
        """Test that health endpoint is excluded from rate limiting"""
        reset_settings()
        reset_rate_limiter()
        os.environ["SCENARIO_LAB_DEV_MODE"] = "false"
        os.environ["SCENARIO_LAB_AUTH_ENABLED"] = "false"
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_REQUESTS"] = "1"  # Very low limit

        from scenario_lab.api.app import app
        test_client = TestClient(app)

        # Health endpoint should not be rate limited
        for _ in range(5):
            response = test_client.get("/api/health")
            assert response.status_code == 200

    def test_rate_limit_excludes_root_endpoint(self, client):
        """Test that root endpoint is excluded from rate limiting"""
        reset_settings()
        reset_rate_limiter()
        os.environ["SCENARIO_LAB_DEV_MODE"] = "false"
        os.environ["SCENARIO_LAB_AUTH_ENABLED"] = "false"
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_REQUESTS"] = "1"

        from scenario_lab.api.app import app
        test_client = TestClient(app)

        # Root endpoint should not be rate limited
        for _ in range(5):
            response = test_client.get("/")
            assert response.status_code == 200

    def test_rate_limit_exceeded_returns_429(self, client):
        """Test that exceeding rate limit returns 429 with proper headers"""
        reset_settings()
        reset_rate_limiter()
        os.environ["SCENARIO_LAB_DEV_MODE"] = "false"
        os.environ["SCENARIO_LAB_AUTH_ENABLED"] = "false"
        os.environ["SCENARIO_LAB_RATE_LIMIT_ENABLED"] = "true"
        os.environ["SCENARIO_LAB_RATE_LIMIT_REQUESTS"] = "2"
        os.environ["SCENARIO_LAB_RATE_LIMIT_WINDOW"] = "60"

        from scenario_lab.api.app import app
        test_client = TestClient(app)

        # Make requests up to limit
        test_client.get("/api/runs")
        test_client.get("/api/runs")

        # Next request should be rate limited
        response = test_client.get("/api/runs")
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers


class TestHumanDecisionStorage:
    """Tests for human decision storage functionality"""

    def test_human_decision_stores_decision_data(self, client, tmp_path):
        """Test that human decisions are stored properly"""
        # Create and start a scenario
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        execute_response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        scenario_id = execute_response.json()["scenario_id"]

        # Set up a mock runner and waiting state
        from scenario_lab.api.app import running_scenarios
        running_scenarios[scenario_id]["runner"] = MagicMock()
        running_scenarios[scenario_id]["waiting_for_human"] = "Human Actor"

        # Submit decision
        response = client.post(
            f"/api/scenarios/{scenario_id}/human-decision",
            json={
                "actor": "Human Actor",
                "long_term_goals": ["Goal 1", "Goal 2"],
                "short_term_priorities": ["Priority 1"],
                "reasoning": "My reasoning",
                "action": "My action"
            }
        )
        assert response.status_code == 200

        # Verify decision was stored
        assert "human_decisions" in running_scenarios[scenario_id]
        decision = running_scenarios[scenario_id]["human_decisions"]["Human Actor"]
        assert decision["long_term_goals"] == ["Goal 1", "Goal 2"]
        assert decision["short_term_priorities"] == ["Priority 1"]
        assert decision["reasoning"] == "My reasoning"
        assert decision["action"] == "My action"

        # Verify waiting status was cleared
        assert running_scenarios[scenario_id]["waiting_for_human"] is None


class TestScenarioIdGeneration:
    """Tests for scenario ID generation"""

    def test_scenario_id_format(self, client, tmp_path):
        """Test that scenario ID follows expected format"""
        # Create a minimal valid scenario directory
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]

        # Verify ID format: scenario-YYYYMMDD-HHMMSS
        assert scenario_id.startswith("scenario-")
        parts = scenario_id.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 8  # YYYYMMDD
        assert len(parts[2]) == 6  # HHMMSS


class TestScenarioStatusFields:
    """Tests for scenario status response fields"""

    def test_status_includes_all_fields(self, client, tmp_path):
        """Test that status response includes all expected fields"""
        # Create and start a scenario
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        execute_response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        scenario_id = execute_response.json()["scenario_id"]

        # Get status
        response = client.get(f"/api/scenarios/{scenario_id}/status")
        assert response.status_code == 200
        data = response.json()

        # Verify all expected fields
        assert "scenario_id" in data
        assert "status" in data
        assert "current_turn" in data
        assert "total_cost" in data
        assert "started_at" in data
        # Optional fields should be present (may be None)
        assert "completed_at" in data
        assert "error" in data
        assert "waiting_for_human" in data

    def test_status_reflects_waiting_for_human(self, client, tmp_path):
        """Test that status reflects waiting_for_human state"""
        # Create and start a scenario
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        execute_response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        scenario_id = execute_response.json()["scenario_id"]

        # Set waiting_for_human
        from scenario_lab.api.app import running_scenarios
        running_scenarios[scenario_id]["waiting_for_human"] = "Human Actor"

        # Get status
        response = client.get(f"/api/scenarios/{scenario_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["waiting_for_human"] == "Human Actor"


class TestRunsEmptyDatabase:
    """Tests for runs endpoints with empty database"""

    def test_list_runs_returns_empty_list(self, client, mock_database):
        """Test that list runs returns empty list when no runs exist"""
        mock_database.list_runs.return_value = []

        with patch("scenario_lab.api.app.database", mock_database):
            response = client.get("/api/runs")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0


class TestWebSocketAdvanced:
    """Advanced tests for WebSocket streaming"""

    def test_websocket_runner_timeout(self, client, tmp_path):
        """Test WebSocket times out waiting for runner initialization"""
        # Create and start a scenario
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        # Start the scenario
        execute_response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        scenario_id = execute_response.json()["scenario_id"]

        # Ensure runner is None to trigger timeout path
        from scenario_lab.api.app import running_scenarios
        running_scenarios[scenario_id]["runner"] = None

        # Connect to WebSocket - should timeout waiting for runner
        # Note: TestClient websocket doesn't support timeout, but this tests the path
        with client.websocket_connect(f"/api/scenarios/{scenario_id}/stream") as websocket:
            # Should receive error about runner initialization timeout
            data = websocket.receive_json()
            assert "error" in data

    def test_websocket_receives_scenario_finished(self, client, tmp_path):
        """Test WebSocket sends scenario_finished message when done"""
        # Create and start a scenario
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        execute_response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        scenario_id = execute_response.json()["scenario_id"]

        # Set up mock runner with event bus
        from scenario_lab.api.app import running_scenarios
        mock_runner = MagicMock()
        mock_event_bus = MagicMock()

        def mock_on(event_type, handler):
            pass

        mock_event_bus.on = mock_on
        mock_runner.event_bus = mock_event_bus
        running_scenarios[scenario_id]["runner"] = mock_runner
        running_scenarios[scenario_id]["status"] = "failed"
        running_scenarios[scenario_id]["current_turn"] = 3
        running_scenarios[scenario_id]["total_cost"] = 1.5

        # Connect to WebSocket
        with client.websocket_connect(f"/api/scenarios/{scenario_id}/stream") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "scenario_finished"
            assert data["data"]["status"] == "failed"
            assert data["data"]["final_turn"] == 3
            assert data["data"]["total_cost"] == 1.5

    def test_websocket_halted_status(self, client, tmp_path):
        """Test WebSocket sends scenario_finished for halted status"""
        # Create and start a scenario
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        execute_response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        scenario_id = execute_response.json()["scenario_id"]

        # Set up mock runner with event bus
        from scenario_lab.api.app import running_scenarios
        mock_runner = MagicMock()
        mock_event_bus = MagicMock()
        mock_event_bus.on = MagicMock()
        mock_runner.event_bus = mock_event_bus
        running_scenarios[scenario_id]["runner"] = mock_runner
        running_scenarios[scenario_id]["status"] = "halted"

        # Connect to WebSocket
        with client.websocket_connect(f"/api/scenarios/{scenario_id}/stream") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "scenario_finished"
            assert data["data"]["status"] == "halted"


class TestMultipleRuns:
    """Tests for listing multiple runs"""

    def test_list_multiple_runs(self, client, mock_database):
        """Test listing multiple runs"""
        mock_run1 = MagicMock()
        mock_run1.id = "run-001"
        mock_run1.scenario_name = "Scenario A"
        mock_run1.status = "completed"
        mock_run1.total_turns = 5
        mock_run1.total_cost = 0.5
        mock_run1.created = datetime.now()

        mock_run2 = MagicMock()
        mock_run2.id = "run-002"
        mock_run2.scenario_name = "Scenario B"
        mock_run2.status = "halted"
        mock_run2.total_turns = 3
        mock_run2.total_cost = 0.3
        mock_run2.created = datetime.now()

        mock_database.list_runs.return_value = [mock_run1, mock_run2]

        with patch("scenario_lab.api.app.database", mock_database):
            response = client.get("/api/runs")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["run_id"] == "run-001"
            assert data[1]["run_id"] == "run-002"
            assert data[0]["status"] == "completed"
            assert data[1]["status"] == "halted"


class TestScenarioExecuteFields:
    """Tests for execute endpoint field handling"""

    def test_execute_with_output_path(self, client, tmp_path):
        """Test execute with custom output path"""
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        response = client.post(
            "/api/scenarios/execute",
            json={
                "scenario_path": str(scenario_dir),
                "output_path": str(output_dir)
            }
        )
        assert response.status_code == 200

    def test_execute_started_at_timestamp(self, client, tmp_path):
        """Test that execute returns valid started_at timestamp"""
        scenario_dir = tmp_path / "test-scenario"
        scenario_dir.mkdir()
        scenario_yaml = scenario_dir / "scenario.yaml"
        scenario_yaml.write_text("""
name: Test Scenario
description: A test scenario
initial_world_state: "Initial state"
turns: 3
""")
        actors_dir = scenario_dir / "actors"
        actors_dir.mkdir()
        actor_yaml = actors_dir / "actor1.yaml"
        actor_yaml.write_text("""
name: Actor 1
model: openai/gpt-4o-mini
goal: Test goal
description: Test actor
""")

        response = client.post(
            "/api/scenarios/execute",
            json={"scenario_path": str(scenario_dir)}
        )
        assert response.status_code == 200
        data = response.json()
        # started_at should be a valid ISO timestamp
        assert "started_at" in data
        assert "T" in data["started_at"]  # ISO format contains T separator


class TestConfigure:
    """Tests for API configuration"""

    def test_app_has_correct_title(self, client):
        """Test that app has correct title in OpenAPI spec"""
        response = client.get("/openapi.json")
        data = response.json()
        assert data["info"]["title"] == "Scenario Lab API"
        assert "AI-powered" in data["info"]["description"]

    def test_version_in_health_response(self, client):
        """Test that version is included in health response"""
        response = client.get("/api/health")
        data = response.json()
        assert "version" in data
        # Version should be a string
        assert isinstance(data["version"], str)
