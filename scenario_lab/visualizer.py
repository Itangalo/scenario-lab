"""Visualization module for Scenario Lab."""

import json
import plotly.graph_objects as go
from pathlib import Path
from typing import List, Dict, Any


def create_visualization(run_dir: Path) -> Path:
    """Generate interactive HTML visualization for a run.

    Args:
        run_dir: Path to the run directory

    Returns:
        Path to the generated HTML file
    """
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"summary.json not found in {run_dir}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    history = summary.get("history", [])
    
    if not history:
        raise ValueError("No history found in summary.json")

    # 1. Prepare Data
    turns = [entry["turn"] for entry in history]
    
    # Collect all metric keys from the first entry (assuming consistent metrics)
    metric_keys = list(history[0]["metrics"].keys())
    
    metric_traces = {key: [] for key in metric_keys}
    for entry in history:
        for key in metric_keys:
            metric_traces[key].append(entry["metrics"].get(key, None))

    # 2. Collect Events
    events_by_turn = {}
    for turn in turns:
        events_file = run_dir / f"turn-{turn:02d}" / "1-events.json"
        if events_file.exists():
            try:
                events = json.loads(events_file.read_text(encoding="utf-8"))
                # Filter only triggered events (though file typically contains triggered ones)
                # The file format is list of dicts: [{"id": "...", "probability": ...}, ...]
                triggered_ids = [e["id"] for e in events]
                if triggered_ids:
                    events_by_turn[turn] = "<br>".join(triggered_ids)
            except Exception:
                pass

    # 3. Create Plot
    fig = go.Figure()

    # Add metric lines
    for key, values in metric_traces.items():
        fig.add_trace(go.Scatter(
            x=turns,
            y=values,
            mode='lines+markers',
            name=key,
            hovertemplate=f'<b>{key}</b>: %{{y}}<br>Turn: %{{x}}<extra></extra>'
        ))

    # Add event annotations (vertical lines or markers)
    # We'll use annotations on the x-axis
    for turn, event_text in events_by_turn.items():
        fig.add_annotation(
            x=turn,
            y=0, # Anchor to bottom (will adjust ref)
            yshift=-40, # Shift down below axis
            text="★", # Star marker for event
            hovertext=f"<b>Events Turn {turn}:</b><br>{event_text}",
            showarrow=False,
            font=dict(size=14, color="red"),
            yref="paper" # Use paper coordinates for y to stick to bottom? No, metrics scale varies.
            # Actually, adding a separate trace for events is cleaner for hover
        )
        
        # Add a vertical line for the event
        fig.add_vline(
            x=turn, 
            line_width=1, 
            line_dash="dash", 
            line_color="gray",
            opacity=0.5
        )

    # 4. Layout
    fig.update_layout(
        title=f"Scenario Metrics Evolution: {summary.get('scenario', 'Unknown')}",
        xaxis_title="Turn",
        yaxis_title="Value",
        legend_title="Metrics",
        hovermode="x unified", # Show all values on hover
        template="plotly_white"
    )

    # Save
    output_path = run_dir / "visualization.html"
    fig.write_html(str(output_path))
    
    return output_path
