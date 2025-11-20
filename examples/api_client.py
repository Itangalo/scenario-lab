"""
Example API Client for Scenario Lab V2

Demonstrates how to programmatically execute scenarios and monitor progress
via the REST API and WebSocket.
"""
import asyncio
import json
from typing import Optional

import httpx
import websockets


class ScenarioLabClient:
    """Client for Scenario Lab API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize client

        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url
        self.http_client = httpx.AsyncClient(base_url=base_url, timeout=300.0)

    async def execute_scenario(
        self,
        scenario_path: str,
        end_turn: Optional[int] = None,
        credit_limit: Optional[float] = None,
    ) -> dict:
        """
        Execute a scenario

        Args:
            scenario_path: Path to scenario directory
            end_turn: Turn number to stop at
            credit_limit: Maximum cost in USD

        Returns:
            Initial status response
        """
        payload = {
            "scenario_path": scenario_path,
            "enable_database": True,
        }
        if end_turn:
            payload["end_turn"] = end_turn
        if credit_limit:
            payload["credit_limit"] = credit_limit

        response = await self.http_client.post("/api/scenarios/execute", json=payload)
        response.raise_for_status()
        return response.json()

    async def get_status(self, scenario_id: str) -> dict:
        """
        Get scenario status

        Args:
            scenario_id: Scenario identifier

        Returns:
            Status information
        """
        response = await self.http_client.get(f"/api/scenarios/{scenario_id}/status")
        response.raise_for_status()
        return response.json()

    async def list_runs(self, scenario: Optional[str] = None) -> list[dict]:
        """
        List all runs

        Args:
            scenario: Optional scenario filter

        Returns:
            List of run summaries
        """
        params = {"scenario": scenario} if scenario else {}
        response = await self.http_client.get("/api/runs", params=params)
        response.raise_for_status()
        return response.json()

    async def get_run_statistics(self, run_id: str) -> dict:
        """
        Get run statistics

        Args:
            run_id: Run identifier

        Returns:
            Run statistics
        """
        response = await self.http_client.get(f"/api/runs/{run_id}/statistics")
        response.raise_for_status()
        return response.json()

    async def compare_runs(self, run_ids: list[str]) -> dict:
        """
        Compare multiple runs

        Args:
            run_ids: List of run IDs to compare

        Returns:
            Comparison data
        """
        response = await self.http_client.post("/api/runs/compare", json=run_ids)
        response.raise_for_status()
        return response.json()

    async def stream_scenario(self, scenario_id: str):
        """
        Stream scenario execution via WebSocket

        Args:
            scenario_id: Scenario identifier

        Yields:
            Event dictionaries as they occur
        """
        ws_url = f"{self.base_url.replace('http', 'ws')}/api/scenarios/{scenario_id}/stream"

        async with websockets.connect(ws_url) as websocket:
            while True:
                try:
                    message = await websocket.recv()
                    event = json.loads(message)

                    # Check for completion
                    if event.get("type") == "scenario_finished":
                        yield event
                        break

                    yield event

                except websockets.exceptions.ConnectionClosed:
                    break

    async def close(self):
        """Close the HTTP client"""
        await self.http_client.aclose()


async def example_execute_and_monitor():
    """Example: Execute a scenario and monitor progress"""
    client = ScenarioLabClient()

    try:
        # Start execution
        print("🚀 Starting scenario execution...")
        result = await client.execute_scenario(
            scenario_path="scenarios/test-regulation-negotiation",
            max_turns=3,
            credit_limit=1.0,
        )

        scenario_id = result["scenario_id"]
        print(f"✓ Scenario started: {scenario_id}")
        print()

        # Poll for status
        print("📊 Monitoring progress...")
        while True:
            status = await client.get_status(scenario_id)
            print(
                f"  Status: {status['status']} | Turn: {status['current_turn']} | Cost: ${status['total_cost']:.2f}"
            )

            if status["status"] in ["completed", "failed", "halted"]:
                print()
                print(f"✓ Scenario {status['status']}")
                break

            await asyncio.sleep(2)

    finally:
        await client.close()


async def example_with_websocket():
    """Example: Execute a scenario and stream events via WebSocket"""
    client = ScenarioLabClient()

    try:
        # Start execution
        print("🚀 Starting scenario with WebSocket streaming...")
        result = await client.execute_scenario(
            scenario_path="scenarios/test-regulation-negotiation",
            max_turns=3,
        )

        scenario_id = result["scenario_id"]
        print(f"✓ Scenario started: {scenario_id}")
        print()

        # Stream events
        print("📡 Streaming real-time events...")
        async for event in client.stream_scenario(scenario_id):
            event_type = event.get("type", "unknown")
            print(f"  [{event_type}]", event.get("data", {}))

            if event_type == "scenario_finished":
                break

    finally:
        await client.close()


async def example_analytics():
    """Example: Query analytics from database"""
    client = ScenarioLabClient()

    try:
        # List recent runs
        print("📊 Recent runs:")
        runs = await client.list_runs()
        for run in runs[:5]:
            print(
                f"  {run['run_id']}: {run['scenario_name']} - {run['turns']} turns, ${run['total_cost']:.2f}"
            )
        print()

        if runs:
            # Get detailed statistics
            run_id = runs[0]["run_id"]
            print(f"📈 Statistics for {run_id}:")
            stats = await client.get_run_statistics(run_id)
            print(f"  Turns: {stats['turns']}")
            print(f"  Decisions: {stats['decisions']}")
            print(f"  Communications: {stats['communications']}")
            print(f"  Metrics: {stats['metrics']}")
            print(f"  Total cost: ${stats['total_cost']:.2f}")
            print(f"  Cost by phase: {stats['cost_by_phase']}")

    finally:
        await client.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Scenario Lab API Client Examples")
    print("=" * 60)
    print()

    # Choose which example to run
    import sys

    if len(sys.argv) > 1:
        example = sys.argv[1]
    else:
        print("Usage: python api_client.py [example]")
        print()
        print("Available examples:")
        print("  poll     - Execute and poll for status")
        print("  stream   - Execute and stream events via WebSocket")
        print("  analytics - Query run analytics")
        sys.exit(1)

    if example == "poll":
        asyncio.run(example_execute_and_monitor())
    elif example == "stream":
        asyncio.run(example_with_websocket())
    elif example == "analytics":
        asyncio.run(example_analytics())
    else:
        print(f"Unknown example: {example}")
        sys.exit(1)
