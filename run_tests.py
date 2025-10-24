#!/usr/bin/env python3
"""
Test runner for Scenario Lab

Runs all unit tests and provides summary
"""
import unittest
import sys
import os

# Add src and tests to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))


def run_tests(verbosity=2):
    """
    Run all tests in the tests directory

    Args:
        verbosity: Level of output detail (0=quiet, 1=normal, 2=verbose)

    Returns:
        True if all tests passed, False otherwise
    """
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    return result.wasSuccessful()


if __name__ == '__main__':
    # Parse command line arguments
    verbosity = 2
    if len(sys.argv) > 1:
        if sys.argv[1] == '-q' or sys.argv[1] == '--quiet':
            verbosity = 0
        elif sys.argv[1] == '-v' or sys.argv[1] == '--verbose':
            verbosity = 2

    success = run_tests(verbosity)
    sys.exit(0 if success else 1)
