"""
Communication Manager - Handles different types of communication between actors
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class ChannelType(Enum):
    """Types of communication channels"""
    PUBLIC = "public"
    BILATERAL = "bilateral"
    COALITION = "coalition"


class CommunicationChannel:
    """Represents a communication channel between actors"""

    def __init__(
        self,
        channel_type: ChannelType,
        participants: List[str],
        turn: int,
        channel_id: Optional[str] = None
    ):
        self.channel_type = channel_type
        self.participants = sorted(participants)  # Sort for consistency
        self.turn = turn
        self.messages = []
        self.channel_id = channel_id or self._generate_id()

    def _generate_id(self) -> str:
        """Generate channel ID based on type and participants"""
        if self.channel_type == ChannelType.PUBLIC:
            return f"public-{self.turn}"
        elif self.channel_type == ChannelType.BILATERAL:
            return f"bilateral-{'-'.join(self.participants)}-{self.turn}"
        else:  # COALITION
            return f"coalition-{'-'.join(self.participants)}-{self.turn}"

    def add_message(self, sender: str, content: str):
        """Add a message to the channel"""
        if sender not in self.participants and self.channel_type != ChannelType.PUBLIC:
            raise ValueError(f"{sender} is not a participant in this channel")

        self.messages.append({
            'sender': sender,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })

    def is_visible_to(self, actor_name: str) -> bool:
        """Check if this channel is visible to an actor"""
        if self.channel_type == ChannelType.PUBLIC:
            return True
        return actor_name in self.participants

    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages in this channel"""
        return self.messages.copy()


class CommunicationManager:
    """Manages all communication channels in a scenario"""

    def __init__(self, actor_names: List[str]):
        self.actor_names = actor_names
        self.channels: Dict[str, CommunicationChannel] = {}
        self.channels_by_turn: Dict[int, List[str]] = {}  # turn -> list of channel_ids

    def create_channel(
        self,
        channel_type: ChannelType,
        participants: List[str],
        turn: int
    ) -> CommunicationChannel:
        """Create a new communication channel"""

        # Validate participants
        for participant in participants:
            if participant not in self.actor_names:
                raise ValueError(f"Unknown actor: {participant}")

        # Validate channel type constraints
        if channel_type == ChannelType.BILATERAL and len(participants) != 2:
            raise ValueError("Bilateral channels require exactly 2 participants")

        if channel_type == ChannelType.COALITION and len(participants) < 3:
            raise ValueError("Coalition channels require at least 3 participants")

        # Create channel
        channel = CommunicationChannel(channel_type, participants, turn)

        # Store channel
        self.channels[channel.channel_id] = channel

        # Track by turn
        if turn not in self.channels_by_turn:
            self.channels_by_turn[turn] = []
        self.channels_by_turn[turn].append(channel.channel_id)

        return channel

    def get_channel(self, channel_id: str) -> Optional[CommunicationChannel]:
        """Get a channel by ID"""
        return self.channels.get(channel_id)

    def send_message(self, channel_id: str, sender: str, content: str):
        """Send a message in a channel"""
        channel = self.get_channel(channel_id)
        if not channel:
            raise ValueError(f"Channel not found: {channel_id}")

        channel.add_message(sender, content)

    def get_visible_channels(self, actor_name: str, turn: Optional[int] = None) -> List[CommunicationChannel]:
        """Get all channels visible to an actor, optionally filtered by turn"""
        visible = []

        for channel in self.channels.values():
            # Filter by turn if specified
            if turn is not None and channel.turn != turn:
                continue

            # Check visibility
            if channel.is_visible_to(actor_name):
                visible.append(channel)

        return visible

    def get_visible_messages(self, actor_name: str, turn: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get all messages visible to an actor

        Returns list of dicts with: channel_id, channel_type, sender, content, timestamp
        """
        messages = []

        for channel in self.get_visible_channels(actor_name, turn):
            for message in channel.get_messages():
                messages.append({
                    'channel_id': channel.channel_id,
                    'channel_type': channel.channel_type.value,
                    'participants': channel.participants,
                    'sender': message['sender'],
                    'content': message['content'],
                    'timestamp': message['timestamp']
                })

        # Sort by timestamp
        messages.sort(key=lambda m: m['timestamp'])
        return messages

    def channel_to_markdown(self, channel: CommunicationChannel, scenario_name: str) -> str:
        """Generate markdown representation of a channel"""

        if channel.channel_type == ChannelType.PUBLIC:
            title = f"Public Communication - Turn {channel.turn}"
        elif channel.channel_type == ChannelType.BILATERAL:
            title = f"Bilateral Negotiation - Turn {channel.turn}"
            subtitle = f"**Participants:** {', '.join(channel.participants)}"
        else:  # COALITION
            title = f"Coalition Communication - Turn {channel.turn}"
            subtitle = f"**Participants:** {', '.join(channel.participants)}"

        md = f"# {title}\n\n"
        md += f"**Scenario:** {scenario_name}\n\n"

        if channel.channel_type != ChannelType.PUBLIC:
            md += f"{subtitle}\n\n"

        md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += "---\n\n"

        if not channel.messages:
            md += "*No messages in this channel*\n\n"
        else:
            md += "## Messages\n\n"
            for message in channel.messages:
                md += f"### {message['sender']}\n\n"
                md += f"{message['content']}\n\n"
                md += "---\n\n"

        return md

    def format_messages_for_context(self, actor_name: str, turn: int) -> str:
        """
        Format messages visible to an actor as context for their decision

        Returns formatted string suitable for including in actor prompts
        """
        messages = self.get_visible_messages(actor_name, turn)

        if not messages:
            return ""

        context = "## Communications This Turn\n\n"

        # Group by channel
        by_channel: Dict[str, List[Dict]] = {}
        for msg in messages:
            channel_id = msg['channel_id']
            if channel_id not in by_channel:
                by_channel[channel_id] = []
            by_channel[channel_id].append(msg)

        # Format each channel
        for channel_id, channel_messages in by_channel.items():
            first_msg = channel_messages[0]
            channel_type = first_msg['channel_type']

            if channel_type == 'public':
                context += "### Public Statements\n\n"
            elif channel_type == 'bilateral':
                other_participant = [p for p in first_msg['participants'] if p != actor_name][0]
                context += f"### Private Negotiation with {other_participant}\n\n"
            else:  # coalition
                context += f"### Coalition Discussion ({', '.join(first_msg['participants'])})\n\n"

            for msg in channel_messages:
                context += f"**{msg['sender']}:** {msg['content']}\n\n"

            context += "---\n\n"

        return context

    def has_bilateral_with(self, actor1: str, actor2: str, turn: int) -> bool:
        """Check if a bilateral channel exists between two actors for a turn"""
        participants = sorted([actor1, actor2])
        channel_id = f"bilateral-{'-'.join(participants)}-{turn}"
        return channel_id in self.channels

    def get_or_create_bilateral(self, actor1: str, actor2: str, turn: int) -> CommunicationChannel:
        """Get existing bilateral channel or create new one"""
        participants = sorted([actor1, actor2])
        channel_id = f"bilateral-{'-'.join(participants)}-{turn}"

        if channel_id in self.channels:
            return self.channels[channel_id]

        return self.create_channel(ChannelType.BILATERAL, participants, turn)

    def export_channels_to_files(self, output_path: str, scenario_name: str, turn: int):
        """
        Export all non-public channels for a turn to markdown files

        Public communications are in world state and actor decision files
        """
        import os

        turn_channels = self.channels_by_turn.get(turn, [])

        for channel_id in turn_channels:
            channel = self.channels[channel_id]

            # Skip public channels (handled elsewhere)
            if channel.channel_type == ChannelType.PUBLIC:
                continue

            # Generate markdown
            md = self.channel_to_markdown(channel, scenario_name)

            # Determine filename (sanitize participant names for filesystem)
            safe_participants = [p.replace('/', '-').replace('\\', '-') for p in channel.participants]
            if channel.channel_type == ChannelType.BILATERAL:
                filename = f"bilateral-{'-'.join(safe_participants)}-{turn:03d}.md"
            else:  # COALITION
                filename = f"coalition-{'-'.join(safe_participants)}-{turn:03d}.md"

            # Write file
            filepath = os.path.join(output_path, filename)
            with open(filepath, 'w') as f:
                f.write(md)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize communication manager state to dict for saving"""
        return {
            'actor_names': self.actor_names,
            'channels': {
                channel_id: {
                    'channel_type': channel.channel_type.value,
                    'participants': channel.participants,
                    'turn': channel.turn,
                    'messages': channel.messages
                }
                for channel_id, channel in self.channels.items()
            },
            'channels_by_turn': self.channels_by_turn
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommunicationManager':
        """Deserialize communication manager from dict"""
        manager = cls(data['actor_names'])

        # Restore channels
        for channel_id, channel_data in data['channels'].items():
            channel = CommunicationChannel(
                channel_type=ChannelType(channel_data['channel_type']),
                participants=channel_data['participants'],
                turn=channel_data['turn'],
                channel_id=channel_id
            )
            channel.messages = channel_data['messages']
            manager.channels[channel_id] = channel

        # Restore turn index
        manager.channels_by_turn = data['channels_by_turn']

        return manager
