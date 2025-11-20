"""
Communication Manager for Scenario Lab V2

Manages different types of communication between actors.
Adapted from V1 to work with immutable ScenarioState.

Communication Types:
- Public: Visible to all actors
- Bilateral: Private negotiation between 2 actors
- Coalition: Private discussion among 3+ actors
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from scenario_lab.models.state import ScenarioState, Communication


def get_communications_for_actor(
    state: ScenarioState,
    actor_name: str,
    turn: Optional[int] = None
) -> List[Communication]:
    """
    Get all communications visible to an actor

    Args:
        state: Current scenario state
        actor_name: Name of the actor
        turn: Optional turn filter (None = all turns)

    Returns:
        List of Communication objects visible to the actor
    """
    visible = []

    for comm in state.communications:
        # Filter by turn if specified
        if turn is not None and comm.turn != turn:
            continue

        # Check visibility
        # Public communications are visible to all
        if comm.type == "public":
            visible.append(comm)
        # Private communications only visible to participants
        elif actor_name in comm.recipients or comm.sender == actor_name:
            visible.append(comm)

    return visible


def format_communications_for_context(
    state: ScenarioState,
    actor_name: str,
    turn: int
) -> str:
    """
    Format communications visible to an actor as context for decision-making

    Args:
        state: Current scenario state
        actor_name: Name of the actor
        turn: Turn number to get communications for

    Returns:
        Formatted string for inclusion in actor prompts (empty if no communications)
    """
    comms = get_communications_for_actor(state, actor_name, turn)

    if not comms:
        return ""

    context = "## Communications This Turn\n\n"

    # Group by type and participants
    by_channel: Dict[str, List[Communication]] = {}
    for comm in comms:
        # Create channel key
        if comm.type == "public":
            channel_key = "public"
        elif comm.type == "bilateral":
            # Sort participants for consistent key
            participants = sorted([comm.sender] + comm.recipients)
            channel_key = f"bilateral-{'-'.join(participants)}"
        else:  # coalition
            participants = sorted([comm.sender] + comm.recipients)
            channel_key = f"coalition-{'-'.join(participants)}"

        if channel_key not in by_channel:
            by_channel[channel_key] = []
        by_channel[channel_key].append(comm)

    # Format each channel
    for channel_key, channel_comms in by_channel.items():
        first = channel_comms[0]

        if first.type == "public":
            context += "### Public Statements\n\n"
        elif first.type == "bilateral":
            # Find the other participant
            all_participants = set([first.sender] + first.recipients)
            other_participant = [p for p in all_participants if p != actor_name][0]
            context += f"### Private Negotiation with {other_participant}\n\n"
        else:  # coalition
            all_participants = set([first.sender] + first.recipients)
            context += f"### Coalition Discussion ({', '.join(sorted(all_participants))})\n\n"

        # List messages in chronological order
        for comm in sorted(channel_comms, key=lambda c: c.timestamp):
            context += f"**{comm.sender}:** {comm.content}\n\n"

        context += "---\n\n"

    return context


def create_communication(
    sender: str,
    recipients: List[str],
    content: str,
    turn: int,
    comm_type: str = "bilateral",
    comm_id: Optional[str] = None
) -> Communication:
    """
    Create a new Communication object

    Args:
        sender: Name of the sender
        recipients: List of recipient names
        content: Message content
        turn: Turn number
        comm_type: Type of communication ("public", "bilateral", "coalition")
        comm_id: Optional communication ID (auto-generated if not provided)

    Returns:
        New Communication object

    Raises:
        ValueError: If comm_type is invalid or participants don't match type
    """
    if comm_type not in ["public", "bilateral", "coalition"]:
        raise ValueError(f"Invalid communication type: {comm_type}")

    if comm_type == "bilateral" and len(recipients) != 1:
        raise ValueError("Bilateral communications must have exactly 1 recipient")

    if comm_type == "coalition" and len(recipients) < 2:
        raise ValueError("Coalition communications must have at least 2 recipients")

    # Generate ID if not provided
    if comm_id is None:
        timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S%f")
        comm_id = f"{comm_type}-{turn}-{timestamp_str}"

    return Communication(
        id=comm_id,
        turn=turn,
        type=comm_type,
        sender=sender,
        recipients=recipients,
        content=content,
        timestamp=datetime.now()
    )


def format_communication_markdown(
    comms: List[Communication],
    scenario_name: str
) -> str:
    """
    Format communications as markdown

    Args:
        comms: List of communications (should all be from same channel)
        scenario_name: Name of the scenario

    Returns:
        Markdown formatted string
    """
    if not comms:
        return ""

    first = comms[0]

    # Determine title
    if first.type == "public":
        title = f"Public Communication - Turn {first.turn}"
        subtitle = ""
    elif first.type == "bilateral":
        title = f"Bilateral Negotiation - Turn {first.turn}"
        all_participants = sorted(set([first.sender] + first.recipients))
        subtitle = f"**Participants:** {', '.join(all_participants)}\n\n"
    else:  # coalition
        title = f"Coalition Communication - Turn {first.turn}"
        all_participants = sorted(set([first.sender] + first.recipients))
        subtitle = f"**Participants:** {', '.join(all_participants)}\n\n"

    md = f"# {title}\n\n"
    md += f"**Scenario:** {scenario_name}\n\n"
    md += subtitle
    md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += "---\n\n"

    if not comms:
        md += "*No messages in this channel*\n\n"
    else:
        md += "## Messages\n\n"
        for comm in sorted(comms, key=lambda c: c.timestamp):
            md += f"### {comm.sender}\n\n"
            md += f"{comm.content}\n\n"
            md += "---\n\n"

    return md


def export_communications_to_files(
    state: ScenarioState,
    output_dir: str,
    turn: int
):
    """
    Export communications for a turn to markdown files

    Args:
        state: Current scenario state
        output_dir: Directory to write files to
        turn: Turn number to export
    """
    from pathlib import Path

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Get communications for this turn (excluding public)
    turn_comms = [c for c in state.communications if c.turn == turn and c.type != "public"]

    # Group by channel
    by_channel: Dict[str, List[Communication]] = {}
    for comm in turn_comms:
        if comm.type == "bilateral":
            participants = sorted([comm.sender] + comm.recipients)
            channel_key = f"bilateral-{'-'.join(participants)}"
        else:  # coalition
            participants = sorted(set([comm.sender] + comm.recipients))
            channel_key = f"coalition-{'-'.join(participants)}"

        if channel_key not in by_channel:
            by_channel[channel_key] = []
        by_channel[channel_key].append(comm)

    # Write each channel to a file
    for channel_key, channel_comms in by_channel.items():
        md = format_communication_markdown(channel_comms, state.scenario_name)

        # Sanitize filename
        safe_key = channel_key.replace('/', '-').replace('\\', '-')
        filename = f"{safe_key}-{turn:03d}.md"

        filepath = output_path / filename
        with open(filepath, 'w') as f:
            f.write(md)
