from scenario_lab.models import WorldState

def get_visible_metrics(state: WorldState, actor_name: str) -> dict:
    """
    Returns a dictionary of metrics visible to the given actor.

    Args:
        state: The current world state.
        actor_name: The name of the actor.

    Returns:
        A dictionary of visible metrics.
    """
    visible_metrics = {}

    # World metrics are always visible
    visible_metrics.update(state.metrics.world)

    for actor, metrics_data in state.metrics.actors.items():
        if actor == actor_name:
            # Actor's own metrics (public and private)
            visible_metrics.update(metrics_data.public)
            visible_metrics.update(metrics_data.private)
        else:
            # Other actors' public metrics
            visible_metrics.update(metrics_data.public)

    return visible_metrics

def generate_actor_view(state: WorldState, actor_name: str) -> dict:
    """
    Generates a complete "view" for the actor.

    Args:
        state: The current world state.
        actor_name: The name of the actor.

    Returns:
        A dictionary representing the actor's view.
    """
    actor_view = {
        "metrics": get_visible_metrics(state, actor_name),
        "relationships": state.relationships,
        "fact_ledger": state.fact_ledger,
        "narrative_state": state.narrative_state,
        "goals": state.actors.get(actor_name, {}).get("goals", []),
    }
    return actor_view
