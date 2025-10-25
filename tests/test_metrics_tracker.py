"""
Unit tests for MetricsTracker
"""
import unittest
import sys
import os
import tempfile
import shutil
import yaml
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from metrics_tracker import MetricsTracker


class TestMetricsTracker(unittest.TestCase):
    """Test MetricsTracker functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary scenario directory
        self.temp_dir = tempfile.mkdtemp()
        self.scenario_path = os.path.join(self.temp_dir, 'test-scenario')
        os.makedirs(self.scenario_path)

        # Create a metrics.yaml with patterns that have multiple groups
        self.metrics_config = {
            'scenario_name': 'Test Scenario',
            'metrics': {
                'reporting_timeline': {
                    'description': 'Timeline for reporting in hours',
                    'type': 'integer',
                    'unit': 'hours',
                    'extraction_method': 'regex',
                    # Pattern with multiple groups (this was causing the tuple bug)
                    'pattern': r'(\d+)\s*[-]?hours?|within\s*(\d+)',
                    'actor_specific': False
                },
                'consensus_level': {
                    'description': 'Consensus percentage',
                    'type': 'integer',
                    'unit': 'percent',
                    'extraction_method': 'regex',
                    # Pattern with single group (no tuple issue)
                    'pattern': r'consensus.*?(\d+)%|(\d+)%.*?consensus',
                    'actor_specific': False
                },
                'testing_required': {
                    'description': 'Whether testing is required',
                    'type': 'boolean',
                    'extraction_method': 'regex',
                    'pattern': r'mandatory\s*testing|required.*?testing',
                    'actor_specific': False
                }
            }
        }

        self.metrics_file = os.path.join(self.scenario_path, 'metrics.yaml')
        with open(self.metrics_file, 'w') as f:
            yaml.dump(self.metrics_config, f)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test MetricsTracker initializes correctly"""
        tracker = MetricsTracker(self.metrics_file)

        self.assertEqual(tracker.scenario_name, 'Test Scenario')
        self.assertIn('reporting_timeline', tracker.metrics_definitions)
        self.assertEqual(len(tracker.metrics_by_turn), 0)

    def test_extract_metrics_single_group(self):
        """Test extracting metrics from text with single-group pattern"""
        tracker = MetricsTracker(self.metrics_file)

        text = "The consensus reached 75% agreement among stakeholders."
        tracker.extract_metrics_from_text(1, text)

        self.assertIn(1, tracker.metrics_by_turn)
        self.assertEqual(tracker.metrics_by_turn[1]['consensus_level'], 75)

    def test_extract_metrics_multiple_groups(self):
        """Test extracting metrics with multi-group regex pattern (regression test for tuple bug)"""
        tracker = MetricsTracker(self.metrics_file)

        # Text that should match the first group of the pattern
        text1 = "Incident reporting must be completed within 48 hours of detection."
        tracker.extract_metrics_from_text(1, text1)

        # Should extract 48, not ('48', '') tuple
        self.assertIn(1, tracker.metrics_by_turn)
        self.assertEqual(tracker.metrics_by_turn[1]['reporting_timeline'], 48)
        self.assertIsInstance(tracker.metrics_by_turn[1]['reporting_timeline'], int)

        # Text that should match the second group of the pattern
        text2 = "All incidents must be reported within 72 hours."
        tracker.extract_metrics_from_text(2, text2)

        # Should extract 72, not ('', '72') tuple
        self.assertIn(2, tracker.metrics_by_turn)
        self.assertEqual(tracker.metrics_by_turn[2]['reporting_timeline'], 72)
        self.assertIsInstance(tracker.metrics_by_turn[2]['reporting_timeline'], int)

    def test_extract_boolean_metrics(self):
        """Test extracting boolean metrics"""
        tracker = MetricsTracker(self.metrics_file)

        text = "All systems must undergo mandatory testing before deployment."
        tracker.extract_metrics_from_text(1, text)

        self.assertIn(1, tracker.metrics_by_turn)
        # Check that testing_required was extracted
        self.assertIn('testing_required', tracker.metrics_by_turn[1])
        # The value should be True when "mandatory testing" is found
        self.assertTrue(tracker.metrics_by_turn[1]['testing_required'])

    def test_calculate_summary_statistics(self):
        """Test calculating summary statistics doesn't crash on integer metrics"""
        tracker = MetricsTracker(self.metrics_file)

        # Add some metrics across turns
        tracker.record_metric(1, 'reporting_timeline', 48)
        tracker.record_metric(2, 'reporting_timeline', 72)
        tracker.record_metric(3, 'reporting_timeline', 24)

        # This should not crash with TypeError
        stats = tracker._calculate_summary_statistics()

        self.assertIn('reporting_timeline', stats)
        self.assertEqual(stats['reporting_timeline']['min'], 24)
        self.assertEqual(stats['reporting_timeline']['max'], 72)
        self.assertEqual(stats['reporting_timeline']['mean'], 48)

    def test_print_summary_no_crash(self):
        """Test that print_summary doesn't crash when metrics contain integers"""
        tracker = MetricsTracker(self.metrics_file)

        # Simulate the scenario that caused the original crash
        text = "Reporting timeline set at 48 hours."
        tracker.extract_metrics_from_text(1, text)
        tracker.extract_metrics_from_text(2, text)

        # This should not crash
        try:
            tracker.print_summary()
        except TypeError as e:
            self.fail(f"print_summary() raised TypeError: {e}")

    def test_save_and_load_metrics(self):
        """Test saving metrics to file"""
        tracker = MetricsTracker(self.metrics_file)

        tracker.record_metric(1, 'consensus_level', 50)
        tracker.record_metric(2, 'consensus_level', 75)

        output_file = os.path.join(self.temp_dir, 'metrics.json')
        tracker.save_to_file(output_file)

        self.assertTrue(os.path.exists(output_file))

        # Load and verify
        with open(output_file, 'r') as f:
            data = json.load(f)

        self.assertEqual(data['scenario'], 'Test Scenario')
        self.assertIn('metrics_by_turn', data)


if __name__ == '__main__':
    unittest.main()
