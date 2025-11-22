"""
Tests for CLI wizard commands (create and create-batch)

Note: V2 wizard commands now show guidance instead of calling V1 wizards.
"""
import unittest
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

    def test_create_command_shows_guidance(self):
        """Test that 'create' command shows guidance (V2 behavior)"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['create'])

            # V2 shows guidance instead of wizard
            self.assertEqual(result.exit_code, 0)
            self.assertIn('wizard not yet available', result.output.lower())
            # Should show manual creation steps
            self.assertIn('scenario.yaml', result.output)
            self.assertIn('mkdir', result.output)

    def test_create_batch_command_shows_guidance(self):
        """Test that 'create-batch' command shows guidance (V2 behavior)"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['create-batch'])

            # V2 shows guidance instead of wizard
            self.assertEqual(result.exit_code, 0)
            self.assertIn('wizard not yet available', result.output.lower())
            # Should show manual creation steps
            self.assertIn('YAML', result.output)

    def test_create_command_with_output_dir(self):
        """Test that 'create' command accepts output_dir argument"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['create', '/custom/path'])

            # Should still show guidance (exit code 0)
            self.assertEqual(result.exit_code, 0)

    def test_create_batch_command_with_output_path(self):
        """Test that 'create-batch' command accepts output_path argument"""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(cli, ['create-batch', '/custom/batch.yaml'])

            # Should still show guidance (exit code 0)
            self.assertEqual(result.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
