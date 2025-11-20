#!/usr/bin/env python3
"""
Test V2 Batch Analyzer

Tests the statistical analysis and pattern recognition for batch results.
"""
import sys
import os
import json
import yaml
import tempfile
import shutil
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from scenario_lab.batch.batch_analyzer import BatchAnalyzer


def create_test_batch_output(base_dir: str) -> str:
    """Create a test batch output directory with mock data"""
    batch_dir = os.path.join(base_dir, 'test-batch')
    runs_dir = os.path.join(batch_dir, 'runs')
    os.makedirs(runs_dir, exist_ok=True)

    # Create batch config
    config = {
        'experiment_name': 'Test Experiment',
        'description': 'Test batch for analysis',
        'base_scenario': '/test/scenario',
        'output_dir': batch_dir
    }
    with open(os.path.join(batch_dir, 'batch-config.yaml'), 'w') as f:
        yaml.dump(config, f)

    # Create batch summary
    summary = {
        'experiment_name': 'Test Experiment',
        'total_variations': 2,
        'runs_per_variation': 3,
        'total_runs_planned': 6,
        'runs_completed': 5,
        'runs_failed': 1
    }
    with open(os.path.join(batch_dir, 'batch-summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

    # Create batch costs
    costs = {
        'total_spent': 5.5,
        'budget_limit': 10.0,
        'runs': []
    }
    with open(os.path.join(batch_dir, 'batch-costs.json'), 'w') as f:
        json.dump(costs, f, indent=2)

    # Create batch state with variations
    state = {
        'experiment_name': 'Test Experiment',
        'variations': [
            {'variation_id': 1, 'description': 'Model A'},
            {'variation_id': 2, 'description': 'Model B'}
        ]
    }
    with open(os.path.join(batch_dir, 'batch-state.json'), 'w') as f:
        json.dump(state, f, indent=2)

    # Create test runs
    # Variation 1: 3 runs (2 successful, 1 failed)
    create_run(runs_dir, 'var-001-run-001', 1, True, {'accuracy': 0.85, 'speed': 120}, 1.0, 5)
    create_run(runs_dir, 'var-001-run-002', 1, True, {'accuracy': 0.90, 'speed': 115}, 1.1, 5)
    create_run(runs_dir, 'var-001-run-003', 1, False, {}, 0.5, 2)  # Failed run

    # Variation 2: 2 runs (both successful)
    create_run(runs_dir, 'var-002-run-001', 2, True, {'accuracy': 0.80, 'speed': 130}, 0.8, 5)
    create_run(runs_dir, 'var-002-run-002', 2, True, {'accuracy': 0.82, 'speed': 125}, 0.9, 5)

    return batch_dir


def create_run(
    runs_dir: str,
    run_id: str,
    variation_id: int,
    success: bool,
    metrics: dict,
    cost: float,
    turns: int
):
    """Create a mock run directory with data"""
    run_dir = os.path.join(runs_dir, run_id)
    os.makedirs(run_dir, exist_ok=True)

    # Create metrics.json
    metrics_data = {
        'final_metrics': metrics
    }
    with open(os.path.join(run_dir, 'metrics.json'), 'w') as f:
        json.dump(metrics_data, f, indent=2)

    # Create costs.json
    costs_data = {
        'total_cost': cost
    }
    with open(os.path.join(run_dir, 'costs.json'), 'w') as f:
        json.dump(costs_data, f, indent=2)

    # Create scenario-state.json
    state_data = {
        'status': 'completed' if success else 'failed',
        'current_turn': turns
    }
    with open(os.path.join(run_dir, 'scenario-state.json'), 'w') as f:
        json.dump(state_data, f, indent=2)


def test_analyzer_initialization():
    """Test analyzer initialization"""
    print("=" * 70)
    print("TEST 1: Analyzer initialization")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        batch_dir = create_test_batch_output(temp_dir)
        analyzer = BatchAnalyzer(batch_dir)

        assert analyzer.batch_dir == Path(batch_dir)
        assert analyzer.runs_dir == Path(batch_dir) / 'runs'
        assert analyzer.analysis_dir == Path(batch_dir) / 'analysis'
        assert analyzer.analysis_dir.exists()

        print(f"  ✓ Analyzer initialized")
        print(f"  ✓ Batch dir: {analyzer.batch_dir}")
        print(f"  ✓ Runs dir: {analyzer.runs_dir}")
        print(f"  ✓ Analysis dir: {analyzer.analysis_dir}")

        print()
        print("✅ Test 1 passed: Analyzer initialization works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_metadata_loading():
    """Test loading batch metadata"""
    print("=" * 70)
    print("TEST 2: Metadata loading")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        batch_dir = create_test_batch_output(temp_dir)
        analyzer = BatchAnalyzer(batch_dir)

        assert analyzer.batch_config is not None
        assert analyzer.batch_config['experiment_name'] == 'Test Experiment'

        assert analyzer.batch_summary is not None
        assert analyzer.batch_summary['runs_completed'] == 5

        assert analyzer.batch_costs is not None
        assert analyzer.batch_costs['total_spent'] == 5.5

        print(f"  ✓ Batch config loaded")
        print(f"  ✓ Batch summary loaded")
        print(f"  ✓ Batch costs loaded")

        print()
        print("✅ Test 2 passed: Metadata loading works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_run_data_collection():
    """Test collecting run data"""
    print("=" * 70)
    print("TEST 3: Run data collection")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        batch_dir = create_test_batch_output(temp_dir)
        analyzer = BatchAnalyzer(batch_dir)

        analyzer.collect_run_data()

        assert len(analyzer.run_data) == 5  # 5 runs total
        assert len(analyzer.variation_data) == 2  # 2 variations

        # Check variation 1 data
        var1_runs = analyzer.variation_data[1]['runs']
        assert len(var1_runs) == 3
        successful_var1 = [r for r in var1_runs if r['success']]
        assert len(successful_var1) == 2

        # Check variation 2 data
        var2_runs = analyzer.variation_data[2]['runs']
        assert len(var2_runs) == 2
        successful_var2 = [r for r in var2_runs if r['success']]
        assert len(successful_var2) == 2

        print(f"  ✓ Collected {len(analyzer.run_data)} runs")
        print(f"  ✓ Found {len(analyzer.variation_data)} variations")
        print(f"  ✓ Variation 1: {len(var1_runs)} runs ({len(successful_var1)} successful)")
        print(f"  ✓ Variation 2: {len(var2_runs)} runs ({len(successful_var2)} successful)")

        print()
        print("✅ Test 3 passed: Run data collection works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_metric_statistics():
    """Test calculating metric statistics"""
    print("=" * 70)
    print("TEST 4: Metric statistics")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        batch_dir = create_test_batch_output(temp_dir)
        analyzer = BatchAnalyzer(batch_dir)
        analyzer.collect_run_data()

        stats = analyzer.calculate_metric_statistics()

        assert 'accuracy' in stats
        assert 'speed' in stats

        # Check accuracy stats (4 successful runs)
        acc_stats = stats['accuracy']
        assert acc_stats['count'] == 4
        assert 0.80 <= acc_stats['mean'] <= 0.90
        assert acc_stats['min'] == 0.80
        assert acc_stats['max'] == 0.90

        # Check speed stats
        speed_stats = stats['speed']
        assert speed_stats['count'] == 4
        assert speed_stats['min'] == 115
        assert speed_stats['max'] == 130

        print(f"  ✓ Calculated statistics for {len(stats)} metrics")
        print(f"  ✓ Accuracy: mean={acc_stats['mean']:.2f}, stdev={acc_stats['stdev']:.2f}")
        print(f"  ✓ Speed: mean={speed_stats['mean']:.2f}, stdev={speed_stats['stdev']:.2f}")

        print()
        print("✅ Test 4 passed: Metric statistics work")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_variation_statistics():
    """Test calculating variation statistics"""
    print("=" * 70)
    print("TEST 5: Variation statistics")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        batch_dir = create_test_batch_output(temp_dir)
        analyzer = BatchAnalyzer(batch_dir)
        analyzer.collect_run_data()

        var_stats = analyzer.calculate_variation_statistics()

        assert 1 in var_stats
        assert 2 in var_stats

        # Check variation 1
        var1 = var_stats[1]
        assert var1['total_runs'] == 3
        assert var1['successful_runs'] == 2
        assert var1['success_rate'] == 2/3

        # Check variation 2
        var2 = var_stats[2]
        assert var2['total_runs'] == 2
        assert var2['successful_runs'] == 2
        assert var2['success_rate'] == 1.0

        # Check metrics exist
        assert 'accuracy' in var1['metrics']
        assert 'accuracy' in var2['metrics']

        print(f"  ✓ Calculated statistics for {len(var_stats)} variations")
        print(f"  ✓ Variation 1: {var1['successful_runs']}/{var1['total_runs']} successful")
        print(f"  ✓ Variation 2: {var2['successful_runs']}/{var2['total_runs']} successful")
        print(f"  ✓ Variation 1 accuracy: {var1['metrics']['accuracy']['mean']:.2f}")
        print(f"  ✓ Variation 2 accuracy: {var2['metrics']['accuracy']['mean']:.2f}")

        print()
        print("✅ Test 5 passed: Variation statistics work")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_variation_comparison():
    """Test comparing variations"""
    print("=" * 70)
    print("TEST 6: Variation comparison")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        batch_dir = create_test_batch_output(temp_dir)
        analyzer = BatchAnalyzer(batch_dir)
        analyzer.collect_run_data()

        # Compare variations by accuracy
        comparison = analyzer.compare_variations('accuracy')

        assert len(comparison) == 2
        # Variation 1 should have higher average accuracy (0.875 vs 0.81)
        assert comparison[0][0] == 1  # Variation 1 is first
        assert comparison[1][0] == 2  # Variation 2 is second

        print(f"  ✓ Compared {len(comparison)} variations")
        print(f"  ✓ Best variation: {comparison[0][0]} (accuracy={comparison[0][1]:.2f})")
        print(f"  ✓ Second: {comparison[1][0]} (accuracy={comparison[1][1]:.2f})")

        print()
        print("✅ Test 6 passed: Variation comparison works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_pattern_identification():
    """Test identifying patterns"""
    print("=" * 70)
    print("TEST 7: Pattern identification")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        batch_dir = create_test_batch_output(temp_dir)
        analyzer = BatchAnalyzer(batch_dir)
        analyzer.collect_run_data()

        patterns = analyzer.identify_patterns()

        assert 'success_rate' in patterns
        assert 'total_runs' in patterns
        assert 'successful_runs' in patterns
        assert 'failed_runs' in patterns
        assert 'best_variation' in patterns
        assert 'cost_efficiency' in patterns

        assert patterns['total_runs'] == 5
        assert patterns['successful_runs'] == 4
        assert patterns['failed_runs'] == 1
        assert patterns['success_rate'] == 0.8  # 4/5

        # Check best variation
        best_var = patterns['best_variation']
        assert best_var['variation_id'] == 2  # 100% success rate
        assert best_var['success_rate'] == 1.0

        # Check cost efficiency
        assert len(patterns['cost_efficiency']) == 2

        print(f"  ✓ Success rate: {patterns['success_rate']*100:.1f}%")
        print(f"  ✓ Best variation: {best_var['variation_id']} ({best_var['success_rate']*100:.1f}%)")
        print(f"  ✓ Cost efficiency rankings: {len(patterns['cost_efficiency'])}")

        print()
        print("✅ Test 7 passed: Pattern identification works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_report_generation():
    """Test generating analysis report"""
    print("=" * 70)
    print("TEST 8: Report generation")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        batch_dir = create_test_batch_output(temp_dir)
        analyzer = BatchAnalyzer(batch_dir)

        report = analyzer.generate_analysis_report()

        assert len(report) > 0
        assert 'Test Experiment' in report
        assert 'Overall Metrics' in report
        assert 'Variation Comparison' in report
        assert 'accuracy' in report
        assert 'speed' in report

        # Check report file created
        report_path = Path(batch_dir) / 'analysis' / 'analysis-report.md'
        assert report_path.exists()

        print(f"  ✓ Report generated ({len(report)} chars)")
        print(f"  ✓ Report saved to: {report_path}")
        print(f"  ✓ Contains experiment name")
        print(f"  ✓ Contains metrics analysis")
        print(f"  ✓ Contains variation comparison")

        print()
        print("✅ Test 8 passed: Report generation works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_data_export():
    """Test saving analysis data"""
    print("=" * 70)
    print("TEST 9: Data export")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        batch_dir = create_test_batch_output(temp_dir)
        analyzer = BatchAnalyzer(batch_dir)

        analyzer.save_analysis_data()

        analysis_dir = Path(batch_dir) / 'analysis'

        # Check files created
        metrics_path = analysis_dir / 'metrics-analysis.json'
        variation_path = analysis_dir / 'variation-statistics.json'
        patterns_path = analysis_dir / 'patterns.json'

        assert metrics_path.exists()
        assert variation_path.exists()
        assert patterns_path.exists()

        # Load and verify metrics analysis
        with open(metrics_path, 'r') as f:
            metrics_data = json.load(f)
        assert 'accuracy' in metrics_data
        assert 'speed' in metrics_data

        # Load and verify variation statistics
        with open(variation_path, 'r') as f:
            var_data = json.load(f)
        # JSON keys are strings, not ints
        assert '1' in var_data or 1 in var_data
        assert '2' in var_data or 2 in var_data

        # Load and verify patterns
        with open(patterns_path, 'r') as f:
            patterns_data = json.load(f)
        assert 'success_rate' in patterns_data
        assert 'best_variation' in patterns_data

        print(f"  ✓ Metrics analysis saved: {metrics_path}")
        print(f"  ✓ Variation statistics saved: {variation_path}")
        print(f"  ✓ Patterns saved: {patterns_path}")
        print(f"  ✓ All data verified")

        print()
        print("✅ Test 9 passed: Data export works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_empty_batch():
    """Test handling empty batch directory"""
    print("=" * 70)
    print("TEST 10: Empty batch handling")
    print("=" * 70)
    print()

    temp_dir = tempfile.mkdtemp()

    try:
        batch_dir = os.path.join(temp_dir, 'empty-batch')
        os.makedirs(os.path.join(batch_dir, 'runs'), exist_ok=True)

        analyzer = BatchAnalyzer(batch_dir)

        # Should not crash on empty batch
        analyzer.collect_run_data()
        assert len(analyzer.run_data) == 0
        assert len(analyzer.variation_data) == 0

        # Statistics should handle empty data gracefully
        metric_stats = analyzer.calculate_metric_statistics()
        assert len(metric_stats) == 0

        var_stats = analyzer.calculate_variation_statistics()
        assert len(var_stats) == 0

        patterns = analyzer.identify_patterns()
        assert patterns['total_runs'] == 0
        assert patterns['success_rate'] == 0.0

        print(f"  ✓ Handled empty batch gracefully")
        print(f"  ✓ No runs collected")
        print(f"  ✓ Statistics returned empty")
        print(f"  ✓ Patterns calculated with zero values")

        print()
        print("✅ Test 10 passed: Empty batch handling works")
        print()
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def run_all_tests():
    """Run all batch analyzer tests"""
    print()
    print("=" * 70)
    print("V2 BATCH ANALYZER TESTS")
    print("=" * 70)
    print()

    tests = [
        test_analyzer_initialization,
        test_metadata_loading,
        test_run_data_collection,
        test_metric_statistics,
        test_variation_statistics,
        test_variation_comparison,
        test_pattern_identification,
        test_report_generation,
        test_data_export,
        test_empty_batch,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ TEST FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("=" * 70)
    print("BATCH ANALYZER TEST SUMMARY")
    print("=" * 70)
    print()

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ ALL BATCH ANALYZER TESTS PASSED")
        print()
        print("Phase 4.6 Complete: Batch Analyzer")
        print("  ✓ Analyzer initialization")
        print("  ✓ Metadata loading (config, summary, costs)")
        print("  ✓ Run data collection")
        print("  ✓ Metric statistics (mean, median, std, min, max)")
        print("  ✓ Variation statistics and comparison")
        print("  ✓ Variation comparison by metrics")
        print("  ✓ Pattern identification (success factors, cost efficiency)")
        print("  ✓ Markdown report generation")
        print("  ✓ JSON data export")
        print("  ✓ Empty batch handling")
        print()
        return True
    else:
        print("❌ SOME TESTS FAILED")
        return False


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
