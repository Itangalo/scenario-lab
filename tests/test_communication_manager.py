"""
Unit tests for CommunicationManager
"""
import unittest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from communication_manager import CommunicationManager, ChannelType


class TestCommunicationManager(unittest.TestCase):
    """Test CommunicationManager functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.actor_names = ["Actor A", "Actor B", "Actor C"]
        self.comm_manager = CommunicationManager(self.actor_names)

    def test_initialization(self):
        """Test CommunicationManager initializes correctly"""
        self.assertEqual(self.comm_manager.actor_names, self.actor_names)
        self.assertEqual(len(self.comm_manager.channels), 0)

    def test_create_bilateral_channel(self):
        """Test creating bilateral channel"""
        channel = self.comm_manager.create_channel(
            ChannelType.BILATERAL,
            ["Actor A", "Actor B"],
            turn=1
        )

        self.assertEqual(channel.channel_type, ChannelType.BILATERAL)
        self.assertEqual(sorted(channel.participants), ["Actor A", "Actor B"])
        self.assertEqual(channel.turn, 1)
        self.assertIn(channel.channel_id, self.comm_manager.channels)

    def test_create_coalition_channel(self):
        """Test creating coalition channel"""
        channel = self.comm_manager.create_channel(
            ChannelType.COALITION,
            ["Actor A", "Actor B", "Actor C"],
            turn=1
        )

        self.assertEqual(channel.channel_type, ChannelType.COALITION)
        self.assertEqual(len(channel.participants), 3)
        self.assertEqual(channel.turn, 1)

    def test_bilateral_requires_two_participants(self):
        """Test bilateral channels require exactly 2 participants"""
        with self.assertRaises(ValueError):
            self.comm_manager.create_channel(
                ChannelType.BILATERAL,
                ["Actor A"],
                turn=1
            )

        with self.assertRaises(ValueError):
            self.comm_manager.create_channel(
                ChannelType.BILATERAL,
                ["Actor A", "Actor B", "Actor C"],
                turn=1
            )

    def test_coalition_requires_three_or_more(self):
        """Test coalition channels require at least 3 participants"""
        with self.assertRaises(ValueError):
            self.comm_manager.create_channel(
                ChannelType.COALITION,
                ["Actor A", "Actor B"],
                turn=1
            )

    def test_send_message(self):
        """Test sending messages in channel"""
        channel = self.comm_manager.create_channel(
            ChannelType.BILATERAL,
            ["Actor A", "Actor B"],
            turn=1
        )

        self.comm_manager.send_message(channel.channel_id, "Actor A", "Test message")

        messages = channel.get_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['sender'], "Actor A")
        self.assertEqual(messages[0]['content'], "Test message")

    def test_channel_visibility(self):
        """Test channel visibility rules"""
        bilateral = self.comm_manager.create_channel(
            ChannelType.BILATERAL,
            ["Actor A", "Actor B"],
            turn=1
        )

        # Actor A and B can see bilateral
        self.assertTrue(bilateral.is_visible_to("Actor A"))
        self.assertTrue(bilateral.is_visible_to("Actor B"))
        # Actor C cannot
        self.assertFalse(bilateral.is_visible_to("Actor C"))

    def test_get_visible_channels(self):
        """Test getting visible channels for actor"""
        bilateral_ab = self.comm_manager.create_channel(
            ChannelType.BILATERAL,
            ["Actor A", "Actor B"],
            turn=1
        )

        bilateral_bc = self.comm_manager.create_channel(
            ChannelType.BILATERAL,
            ["Actor B", "Actor C"],
            turn=1
        )

        # Actor A sees only AB channel
        visible_a = self.comm_manager.get_visible_channels("Actor A")
        self.assertEqual(len(visible_a), 1)
        self.assertEqual(visible_a[0].channel_id, bilateral_ab.channel_id)

        # Actor B sees both channels
        visible_b = self.comm_manager.get_visible_channels("Actor B")
        self.assertEqual(len(visible_b), 2)

    def test_get_or_create_bilateral(self):
        """Test get_or_create_bilateral prevents duplicates"""
        channel1 = self.comm_manager.get_or_create_bilateral("Actor A", "Actor B", 1)
        channel2 = self.comm_manager.get_or_create_bilateral("Actor B", "Actor A", 1)

        # Should return same channel regardless of order
        self.assertEqual(channel1.channel_id, channel2.channel_id)

    def test_serialization(self):
        """Test to_dict and from_dict"""
        channel = self.comm_manager.create_channel(
            ChannelType.BILATERAL,
            ["Actor A", "Actor B"],
            turn=1
        )
        self.comm_manager.send_message(channel.channel_id, "Actor A", "Test")

        # Serialize
        data = self.comm_manager.to_dict()

        # Deserialize
        restored = CommunicationManager.from_dict(data)

        self.assertEqual(restored.actor_names, self.comm_manager.actor_names)
        self.assertEqual(len(restored.channels), len(self.comm_manager.channels))

        restored_channel = restored.get_channel(channel.channel_id)
        self.assertIsNotNone(restored_channel)
        self.assertEqual(len(restored_channel.get_messages()), 1)


if __name__ == '__main__':
    unittest.main()
