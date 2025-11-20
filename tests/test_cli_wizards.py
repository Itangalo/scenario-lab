"""
Tests for CLI wizard commands (create and create-batch)
"""
import unittest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
import sys
import os

# Import CLI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scenario_lab.interfaces.cli import cli


class TestCLIWizardCommands(unittest.TestCase):
    """Tests for CLI wizard integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.runner = CliRunner()

    def test_create_command_exists(self):
        """Test that 'create' command is registered"""
        result = self.runner.invoke(cli, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('create', result.output)
        self.assertIn('Create a new scenario using interactive wizard', result.output)

    def test_create_batch_command_exists(self):
        """Test that 'create-batch' command is registered"""
        result = self.runner.invoke(cli, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('create-batch', result.output)
        self.assertIn('Create a batch configuration using interactive wizard', result.output)

    def test_create_command_help(self):
        """Test 'create' command help output"""
        result = self.runner.invoke(cli, ['create', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('OUTPUT_DIR', result.output)
        self.assertIn('wizard', result.output.lower())
        self.assertIn('actor', result.output.lower())

    def test_create_batch_command_help(self):
        """Test 'create-batch' command help output"""
        result = self.runner.invoke(cli, ['create-batch', '--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('OUTPUT_PATH', result.output)
        self.assertIn('wizard', result.output.lower())
        self.assertIn('experiment', result.output.lower())

    @patch('create_scenario.create_scenario_interactive')
    def test_create_command_invokes_v1_wizard(self, mock_wizard):
        """Test that 'create' command calls V1 wizard"""
        # Mock successful wizard execution
        mock_wizard.return_value = '/tmp/test-scenario'

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['create'])

            # Should call the V1 wizard
            mock_wizard.assert_called_once()

            # Should display success message
            self.assertIn('successfully', result.output.lower())

    @patch('create_batch_config.create_batch_config_interactive')
    def test_create_batch_command_invokes_v1_wizard(self, mock_wizard):
        """Test that 'create-batch' command calls V1 wizard"""
        # Mock successful wizard execution
        mock_wizard.return_value = '/tmp/test-batch.yaml'

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['create-batch'])

            # Should call the V1 wizard
            mock_wizard.assert_called_once()

            # Should display success message
            self.assertIn('successfully', result.output.lower())

    @patch('create_scenario.create_scenario_interactive')
    def test_create_command_handles_cancellation(self, mock_wizard):
        """Test that 'create' command handles wizard cancellation"""
        # Mock wizard cancellation (returns None)
        mock_wizard.return_value = None

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['create'])

            # Should exit with error code
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn('cancelled', result.output.lower())

    @patch('create_batch_config.create_batch_config_interactive')
    def test_create_batch_command_handles_cancellation(self, mock_wizard):
        """Test that 'create-batch' command handles wizard cancellation"""
        # Mock wizard cancellation (returns None)
        mock_wizard.return_value = None

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['create-batch'])

            # Should exit with error code
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn('cancelled', result.output.lower())

    @patch('create_scenario.create_scenario_interactive')
    def test_create_command_with_output_dir(self, mock_wizard):
        """Test that 'create' command passes output_dir argument"""
        mock_wizard.return_value = '/custom/path/scenario'

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['create', '/custom/path'])

            # Should pass output_dir to wizard
            mock_wizard.assert_called_once_with('/custom/path')

    @patch('create_batch_config.create_batch_config_interactive')
    def test_create_batch_command_with_output_path(self, mock_wizard):
        """Test that 'create-batch' command passes output_path argument"""
        mock_wizard.return_value = '/custom/batch.yaml'

        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['create-batch', '/custom/batch.yaml'])

            # Should pass output_path to wizard
            mock_wizard.assert_called_once_with('/custom/batch.yaml')


if __name__ == '__main__':
    unittest.main()
