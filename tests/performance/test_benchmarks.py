"""
Benchmark tests for the Django GraphQL Multi-Schema System.

This module contains benchmark tests that measure and compare performance
across different scenarios, configurations, and system states to establish
performance baselines and detect regressions.
"""

import time
import statistics
import json
import os
from datetime import datetime
from contextlib import contextmanager
from unittest.mock import patch, MagicMock
import pytest
from django.test import TestCase, override_settings
from django.core.cache import cache
from django.conf import settings

from rail_django_graphql.core.registry import schema_registry, SchemaInfo
from rail_django_graphql.decorators import graphql_model, graphql_schema
from rail_django_graphql.plugins.base import BasePlugin, PluginManager
from rail_django_graphql.plugins.hooks import hook_registry


class BenchmarkTestCase(TestCase):
    """Base class for benchmark testing with timing and measurement utilities."""
    
    def setUp(self):
        """Set up benchmark testing environment."""
        super().setUp()
        # Clear registry and cache before each test
        schema_registry.clear()
        cache.clear()
        hook_registry.clear()
        
        # Benchmark configuration
        self.benchmark_config = {
            'iterations': 1000,
            'warmup_iterations': 100,
            'measurement_precision': 6,  # microseconds
            'outlier_threshold': 3.0,    # standard deviations
        }
        
        # Results storage
        self.benchmark_results = {}
    
    def tearDown(self):
        """Clean up after benchmark tests."""
        super().tearDown()
        schema_registry.clear()
        cache.clear()
        hook_registry.clear()
    
    @contextmanager
    def benchmark_timer(self, operation_name):
        """Context manager for timing operations with high precision."""
        start_time = time.perf_counter_ns()
        try:
            yield
        finally:
            end_time = time.perf_counter_ns()
            duration_ns = end_time - start_time
            duration_ms = duration_ns / 1_000_000  # Convert to milliseconds
            
            if operation_name not in self.benchmark_results:
                self.benchmark_results[operation_name] = []
            
            self.benchmark_results[operation_name].append(duration_ms)
    
    def run_benchmark(self, operation, operation_name, iterations=None, warmup=None):
        """
        Run a benchmark test for a specific operation.
        
        Args:
            operation: Function to benchmark
            operation_name: Name for the operation (used in results)
            iterations: Number of iterations (defaults to config)
            warmup: Number of warmup iterations (defaults to config)
            
        Returns:
            dict: Benchmark results with timing statistics
        """
        iterations = iterations or self.benchmark_config['iterations']
        warmup = warmup or self.benchmark_config['warmup_iterations']
        
        # Warmup phase
        for _ in range(warmup):
            try:
                operation()
            except Exception:
                pass  # Ignore warmup errors
        
        # Measurement phase
        timings = []
        
        for i in range(iterations):
            with self.benchmark_timer(f"{operation_name}_iteration_{i}"):
                try:
                    result = operation()
                except Exception as e:
                    # Record failed operations but continue
                    timings.append(None)
                    continue
            
            # Get the timing from the last measurement
            if f"{operation_name}_iteration_{i}" in self.benchmark_results:
                timing = self.benchmark_results[f"{operation_name}_iteration_{i}"][-1]
                timings.append(timing)
        
        # Filter out failed operations
        valid_timings = [t for t in timings if t is not None]
        
        if not valid_timings:
            return {
                'operation': operation_name,
                'iterations': iterations,
                'successful_iterations': 0,
                'failed_iterations': iterations,
                'error': 'All iterations failed'
            }
        
        # Calculate statistics
        results = self.calculate_benchmark_statistics(operation_name, valid_timings, iterations)
        
        # Store in benchmark results
        self.benchmark_results[operation_name] = results
        
        return results
    
    def calculate_benchmark_statistics(self, operation_name, timings, total_iterations):
        """Calculate comprehensive statistics for benchmark timings."""
        if not timings:
            return {}
        
        # Remove outliers
        filtered_timings = self.remove_outliers(timings)
        
        # Sort for percentile calculations
        sorted_timings = sorted(filtered_timings)
        n = len(sorted_timings)
        
        statistics_dict = {
            'operation': operation_name,
            'iterations': total_iterations,
            'successful_iterations': len(timings),
            'failed_iterations': total_iterations - len(timings),
            'outliers_removed': len(timings) - len(filtered_timings),
            
            # Basic statistics (in milliseconds)
            'min_time_ms': min(filtered_timings),
            'max_time_ms': max(filtered_timings),
            'mean_time_ms': statistics.mean(filtered_timings),
            'median_time_ms': statistics.median(filtered_timings),
            'std_dev_ms': statistics.stdev(filtered_timings) if len(filtered_timings) > 1 else 0,
            
            # Percentiles
            'p25_time_ms': sorted_timings[int(0.25 * n)] if n > 0 else 0,
            'p75_time_ms': sorted_timings[int(0.75 * n)] if n > 0 else 0,
            'p90_time_ms': sorted_timings[int(0.90 * n)] if n > 0 else 0,
            'p95_time_ms': sorted_timings[int(0.95 * n)] if n > 0 else 0,
            'p99_time_ms': sorted_timings[int(0.99 * n)] if n > 0 else 0,
            
            # Performance metrics
            'operations_per_second': 1000 / statistics.mean(filtered_timings) if filtered_timings else 0,
            'coefficient_of_variation': (statistics.stdev(filtered_timings) / statistics.mean(filtered_timings)) if len(filtered_timings) > 1 and statistics.mean(filtered_timings) > 0 else 0,
            
            # Timestamps
            'timestamp': datetime.now().isoformat(),
            'raw_timings': timings[:100],  # Store first 100 raw timings for analysis
        }
        
        return statistics_dict
    
    def remove_outliers(self, timings, threshold=None):
        """Remove statistical outliers from timing measurements."""
        if len(timings) < 3:
            return timings
        
        threshold = threshold or self.benchmark_config['outlier_threshold']
        
        mean_time = statistics.mean(timings)
        std_dev = statistics.stdev(timings)
        
        if std_dev == 0:
            return timings
        
        # Remove values more than threshold standard deviations from mean
        filtered = [
            t for t in timings 
            if abs(t - mean_time) <= threshold * std_dev
        ]
        
        return filtered if filtered else timings  # Return original if all filtered out
    
    def compare_benchmarks(self, baseline_results, current_results, tolerance=0.1):
        """
        Compare current benchmark results with baseline results.
        
        Args:
            baseline_results: Previous benchmark results
            current_results: Current benchmark results
            tolerance: Acceptable performance degradation (10% by default)
            
        Returns:
            dict: Comparison results with performance changes
        """
        comparison = {
            'baseline_mean': baseline_results.get('mean_time_ms', 0),
            'current_mean': current_results.get('mean_time_ms', 0),
            'performance_change_percent': 0,
            'performance_status': 'unknown',
            'recommendations': []
        }
        
        if baseline_results.get('mean_time_ms', 0) > 0:
            baseline_mean = baseline_results['mean_time_ms']
            current_mean = current_results['mean_time_ms']
            
            change_percent = ((current_mean - baseline_mean) / baseline_mean) * 100
            comparison['performance_change_percent'] = change_percent
            
            if change_percent <= -5:  # 5% improvement
                comparison['performance_status'] = 'improved'
            elif change_percent <= tolerance * 100:  # Within tolerance
                comparison['performance_status'] = 'stable'
            elif change_percent <= (tolerance * 2) * 100:  # Moderate degradation
                comparison['performance_status'] = 'degraded'
                comparison['recommendations'].append('Performance degradation detected. Consider optimization.')
            else:  # Significant degradation
                comparison['performance_status'] = 'significantly_degraded'
                comparison['recommendations'].append('Significant performance regression detected. Immediate investigation required.')
        
        return comparison


class SchemaRegistrationBenchmarks(BenchmarkTestCase):
    """Benchmark tests for schema registration operations."""
    
    def test_benchmark_simple_schema_registration(self):
        """Benchmark simple schema registration performance."""
        counter = 0
        
        def register_simple_schema():
            nonlocal counter
            counter += 1
            return schema_registry.register_schema(
                name=f'benchmark_schema_{counter}',
                description=f'Benchmark schema {counter}',
                version='1.0.0'
            )
        
        results = self.run_benchmark(
            register_simple_schema,
            'simple_schema_registration',
            iterations=500
        )
        
        # Assert performance expectations
        self.assertLess(results['mean_time_ms'], 10.0, "Simple registration should be under 10ms")
        self.assertGreater(results['operations_per_second'], 100, "Should handle 100+ registrations per second")
        self.assertLess(results['coefficient_of_variation'], 0.5, "Performance should be consistent")
    
    def test_benchmark_schema_registration_with_metadata(self):
        """Benchmark schema registration with extensive metadata."""
        counter = 0
        
        def register_complex_schema():
            nonlocal counter
            counter += 1
            return schema_registry.register_schema(
                name=f'complex_benchmark_schema_{counter}',
                description='A' * 1000,  # 1KB description
                version='1.0.0',
                metadata={
                    'author': 'benchmark_test',
                    'tags': ['benchmark', 'test', 'performance'],
                    'complexity': 'high',
                    'fields': list(range(100)),  # Large metadata
                }
            )
        
        results = self.run_benchmark(
            register_complex_schema,
            'complex_schema_registration',
            iterations=200
        )
        
        # Complex registration can be slower but should still be reasonable
        self.assertLess(results['mean_time_ms'], 50.0, "Complex registration should be under 50ms")
        self.assertGreater(results['operations_per_second'], 20, "Should handle 20+ complex registrations per second")
    
    def test_benchmark_duplicate_schema_registration(self):
        """Benchmark handling of duplicate schema registrations."""
        # Pre-register a schema
        schema_registry.register_schema(
            name='duplicate_benchmark_schema',
            description='Original schema',
            version='1.0.0'
        )
        
        def register_duplicate_schema():
            try:
                return schema_registry.register_schema(
                    name='duplicate_benchmark_schema',
                    description='Duplicate schema',
                    version='1.0.0'
                )
            except Exception:
                return None  # Expected to fail
        
        results = self.run_benchmark(
            register_duplicate_schema,
            'duplicate_schema_registration',
            iterations=1000
        )
        
        # Duplicate handling should be very fast
        self.assertLess(results['mean_time_ms'], 5.0, "Duplicate detection should be under 5ms")


class SchemaLookupBenchmarks(BenchmarkTestCase):
    """Benchmark tests for schema lookup operations."""
    
    def setUp(self):
        """Set up test schemas for lookup benchmarks."""
        super().setUp()
        
        # Pre-register schemas for lookup benchmarks
        self.test_schemas = []
        for i in range(1000):
            schema = schema_registry.register_schema(
                name=f'lookup_benchmark_schema_{i}',
                description=f'Lookup benchmark schema {i}',
                version='1.0.0'
            )
            self.test_schemas.append(schema)
    
    def test_benchmark_schema_lookup_by_name(self):
        """Benchmark schema lookup by name performance."""
        lookup_index = 0
        
        def lookup_schema_by_name():
            nonlocal lookup_index
            schema_name = self.test_schemas[lookup_index % len(self.test_schemas)].name
            lookup_index += 1
            return schema_registry.get_schema(schema_name)
        
        results = self.run_benchmark(
            lookup_schema_by_name,
            'schema_lookup_by_name',
            iterations=2000
        )
        
        # Lookups should be very fast
        self.assertLess(results['mean_time_ms'], 2.0, "Schema lookup should be under 2ms")
        self.assertGreater(results['operations_per_second'], 500, "Should handle 500+ lookups per second")
        self.assertEqual(results['failed_iterations'], 0, "All lookups should succeed")
    
    def test_benchmark_schema_existence_check(self):
        """Benchmark schema existence checking performance."""
        check_index = 0
        
        def check_schema_existence():
            nonlocal check_index
            schema_name = self.test_schemas[check_index % len(self.test_schemas)].name
            check_index += 1
            return schema_registry.schema_exists(schema_name)
        
        results = self.run_benchmark(
            check_schema_existence,
            'schema_existence_check',
            iterations=2000
        )
        
        # Existence checks should be extremely fast
        self.assertLess(results['mean_time_ms'], 1.0, "Existence check should be under 1ms")
        self.assertGreater(results['operations_per_second'], 1000, "Should handle 1000+ existence checks per second")
    
    def test_benchmark_schema_list_all(self):
        """Benchmark listing all schemas performance."""
        def list_all_schemas():
            return schema_registry.list_schemas()
        
        results = self.run_benchmark(
            list_all_schemas,
            'schema_list_all',
            iterations=100  # Fewer iterations as this is more expensive
        )
        
        # Listing all schemas is more expensive but should still be reasonable
        self.assertLess(results['mean_time_ms'], 100.0, "Listing all schemas should be under 100ms")
        self.assertGreater(results['operations_per_second'], 10, "Should handle 10+ list operations per second")
    
    def test_benchmark_nonexistent_schema_lookup(self):
        """Benchmark lookup of nonexistent schemas."""
        lookup_index = 0
        
        def lookup_nonexistent_schema():
            nonlocal lookup_index
            lookup_index += 1
            try:
                return schema_registry.get_schema(f'nonexistent_schema_{lookup_index}')
            except Exception:
                return None  # Expected to fail
        
        results = self.run_benchmark(
            lookup_nonexistent_schema,
            'nonexistent_schema_lookup',
            iterations=1000
        )
        
        # Nonexistent lookups should fail fast
        self.assertLess(results['mean_time_ms'], 5.0, "Nonexistent lookup should be under 5ms")


class SchemaDiscoveryBenchmarks(BenchmarkTestCase):
    """Benchmark tests for schema discovery operations."""
    
    def setUp(self):
        """Set up mock models for discovery benchmarks."""
        super().setUp()
        
        # Create mock models for discovery
        self.mock_models = []
        for i in range(100):
            mock_model = MagicMock()
            mock_model._meta.app_label = f'benchmark_app_{i % 10}'
            mock_model.__name__ = f'BenchmarkModel{i}'
            mock_model._graphql_enabled = True
            self.mock_models.append(mock_model)
    
    def test_benchmark_schema_discovery(self):
        """Benchmark schema discovery performance."""
        with patch('django.apps.apps.get_models') as mock_get_models:
            mock_get_models.return_value = self.mock_models
            
            def discover_schemas():
                return schema_registry.discover_schemas()
            
            results = self.run_benchmark(
                discover_schemas,
                'schema_discovery',
                iterations=50  # Discovery is expensive, fewer iterations
            )
            
            # Discovery is more expensive but should complete in reasonable time
            self.assertLess(results['mean_time_ms'], 1000.0, "Schema discovery should be under 1 second")
            self.assertGreater(results['operations_per_second'], 1, "Should handle 1+ discovery per second")
    
    def test_benchmark_incremental_discovery(self):
        """Benchmark incremental schema discovery performance."""
        # Pre-discover some schemas
        with patch('django.apps.apps.get_models') as mock_get_models:
            mock_get_models.return_value = self.mock_models[:50]
            schema_registry.discover_schemas()
            
            # Now benchmark discovering additional schemas
            mock_get_models.return_value = self.mock_models[50:]
            
            def incremental_discover():
                return schema_registry.discover_schemas()
            
            results = self.run_benchmark(
                incremental_discover,
                'incremental_schema_discovery',
                iterations=100
            )
            
            # Incremental discovery should be faster than full discovery
            self.assertLess(results['mean_time_ms'], 500.0, "Incremental discovery should be under 500ms")


class CachingBenchmarks(BenchmarkTestCase):
    """Benchmark tests for caching performance."""
    
    def setUp(self):
        """Set up caching benchmarks."""
        super().setUp()
        
        # Pre-register schemas
        self.cached_schemas = []
        for i in range(100):
            schema = schema_registry.register_schema(
                name=f'cached_benchmark_schema_{i}',
                description=f'Cached benchmark schema {i}',
                version='1.0.0'
            )
            self.cached_schemas.append(schema)
    
    def test_benchmark_cached_vs_uncached_lookup(self):
        """Compare cached vs uncached lookup performance."""
        lookup_index = 0
        
        def cached_lookup():
            nonlocal lookup_index
            schema_name = self.cached_schemas[lookup_index % len(self.cached_schemas)].name
            lookup_index += 1
            return schema_registry.get_schema(schema_name)
        
        # Benchmark with cache
        cached_results = self.run_benchmark(
            cached_lookup,
            'cached_schema_lookup',
            iterations=1000
        )
        
        # Clear cache and benchmark without cache
        cache.clear()
        lookup_index = 0  # Reset counter
        
        uncached_results = self.run_benchmark(
            cached_lookup,
            'uncached_schema_lookup',
            iterations=1000
        )
        
        # Cached lookups should be significantly faster
        cached_mean = cached_results['mean_time_ms']
        uncached_mean = uncached_results['mean_time_ms']
        
        self.assertLess(cached_mean, uncached_mean, "Cached lookups should be faster")
        
        # Calculate cache performance improvement
        improvement_factor = uncached_mean / cached_mean if cached_mean > 0 else 1
        self.assertGreater(improvement_factor, 1.5, "Cache should provide at least 50% improvement")
    
    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    })
    def test_benchmark_no_cache_performance(self):
        """Benchmark performance without caching."""
        lookup_index = 0
        
        def no_cache_lookup():
            nonlocal lookup_index
            schema_name = self.cached_schemas[lookup_index % len(self.cached_schemas)].name
            lookup_index += 1
            return schema_registry.get_schema(schema_name)
        
        results = self.run_benchmark(
            no_cache_lookup,
            'no_cache_lookup',
            iterations=500
        )
        
        # Without cache, performance should still be acceptable
        self.assertLess(results['mean_time_ms'], 20.0, "No-cache lookup should be under 20ms")


class PluginSystemBenchmarks(BenchmarkTestCase):
    """Benchmark tests for plugin system performance."""
    
    def setUp(self):
        """Set up plugin system benchmarks."""
        super().setUp()
        
        # Create mock plugins
        class FastPlugin(BasePlugin):
            def process_schema(self, schema_info):
                return schema_info
        
        class SlowPlugin(BasePlugin):
            def process_schema(self, schema_info):
                time.sleep(0.001)  # 1ms delay
                return schema_info
        
        self.fast_plugin = FastPlugin()
        self.slow_plugin = SlowPlugin()
    
    def test_benchmark_plugin_execution(self):
        """Benchmark plugin execution performance."""
        # Register plugins
        plugin_manager = PluginManager()
        plugin_manager.register_plugin(self.fast_plugin)
        
        counter = 0
        
        def execute_with_plugins():
            nonlocal counter
            counter += 1
            schema_info = SchemaInfo(
                name=f'plugin_benchmark_schema_{counter}',
                description=f'Plugin benchmark schema {counter}',
                version='1.0.0'
            )
            return plugin_manager.process_schema(schema_info)
        
        results = self.run_benchmark(
            execute_with_plugins,
            'plugin_execution',
            iterations=1000
        )
        
        # Plugin execution should add minimal overhead
        self.assertLess(results['mean_time_ms'], 10.0, "Plugin execution should be under 10ms")
    
    def test_benchmark_multiple_plugins(self):
        """Benchmark performance with multiple plugins."""
        plugin_manager = PluginManager()
        plugin_manager.register_plugin(self.fast_plugin)
        plugin_manager.register_plugin(self.slow_plugin)
        
        counter = 0
        
        def execute_multiple_plugins():
            nonlocal counter
            counter += 1
            schema_info = SchemaInfo(
                name=f'multi_plugin_benchmark_schema_{counter}',
                description=f'Multi-plugin benchmark schema {counter}',
                version='1.0.0'
            )
            return plugin_manager.process_schema(schema_info)
        
        results = self.run_benchmark(
            execute_multiple_plugins,
            'multiple_plugin_execution',
            iterations=500
        )
        
        # Multiple plugins will be slower but should still be reasonable
        self.assertLess(results['mean_time_ms'], 50.0, "Multiple plugin execution should be under 50ms")


class HookSystemBenchmarks(BenchmarkTestCase):
    """Benchmark tests for hook system performance."""
    
    def test_benchmark_hook_execution(self):
        """Benchmark hook execution performance."""
        # Register hooks
        def fast_hook(schema_name, **kwargs):
            return kwargs
        
        def slow_hook(schema_name, **kwargs):
            time.sleep(0.0001)  # 0.1ms delay
            return kwargs
        
        hook_registry.register_hook('pre_registration', fast_hook)
        hook_registry.register_hook('pre_registration', slow_hook)
        
        counter = 0
        
        def execute_with_hooks():
            nonlocal counter
            counter += 1
            return schema_registry.register_schema(
                name=f'hook_benchmark_schema_{counter}',
                description=f'Hook benchmark schema {counter}',
                version='1.0.0'
            )
        
        results = self.run_benchmark(
            execute_with_hooks,
            'hook_execution',
            iterations=500
        )
        
        # Hook execution should add some overhead but remain reasonable
        self.assertLess(results['mean_time_ms'], 20.0, "Hook execution should be under 20ms")


# Benchmark runner and reporting
class BenchmarkRunner:
    """Utility class for running benchmarks and generating reports."""
    
    def __init__(self, output_dir='benchmark_results'):
        """Initialize benchmark runner with output directory."""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def run_all_benchmarks(self):
        """Run all benchmark test suites."""
        import unittest
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add benchmark test classes
        benchmark_classes = [
            SchemaRegistrationBenchmarks,
            SchemaLookupBenchmarks,
            SchemaDiscoveryBenchmarks,
            CachingBenchmarks,
            PluginSystemBenchmarks,
            HookSystemBenchmarks,
        ]
        
        all_results = {}
        
        for benchmark_class in benchmark_classes:
            print(f"Running {benchmark_class.__name__}...")
            
            # Create test instance
            test_instance = benchmark_class()
            test_instance.setUp()
            
            # Run all test methods
            test_methods = [method for method in dir(test_instance) if method.startswith('test_benchmark_')]
            
            for method_name in test_methods:
                print(f"  Running {method_name}...")
                
                try:
                    method = getattr(test_instance, method_name)
                    method()
                    
                    # Collect results
                    if hasattr(test_instance, 'benchmark_results'):
                        all_results.update(test_instance.benchmark_results)
                
                except Exception as e:
                    print(f"    Error in {method_name}: {e}")
                
                # Reset for next test
                test_instance.tearDown()
                test_instance.setUp()
            
            test_instance.tearDown()
        
        return all_results
    
    def save_benchmark_results(self, results, filename=None):
        """Save benchmark results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'benchmark_results_{timestamp}.json'
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Benchmark results saved to {filepath}")
        return filepath
    
    def load_benchmark_results(self, filename):
        """Load benchmark results from JSON file."""
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def generate_benchmark_report(self, results):
        """Generate a comprehensive benchmark report."""
        report = {
            'summary': {
                'total_benchmarks': len(results),
                'timestamp': datetime.now().isoformat(),
                'fastest_operation': None,
                'slowest_operation': None,
                'most_consistent': None,
                'least_consistent': None,
            },
            'performance_analysis': {},
            'recommendations': []
        }
        
        if not results:
            return report
        
        # Find fastest and slowest operations
        operations_by_speed = sorted(
            results.items(),
            key=lambda x: x[1].get('mean_time_ms', float('inf'))
        )
        
        if operations_by_speed:
            report['summary']['fastest_operation'] = {
                'name': operations_by_speed[0][0],
                'mean_time_ms': operations_by_speed[0][1].get('mean_time_ms', 0)
            }
            report['summary']['slowest_operation'] = {
                'name': operations_by_speed[-1][0],
                'mean_time_ms': operations_by_speed[-1][1].get('mean_time_ms', 0)
            }
        
        # Find most and least consistent operations
        operations_by_consistency = sorted(
            results.items(),
            key=lambda x: x[1].get('coefficient_of_variation', float('inf'))
        )
        
        if operations_by_consistency:
            report['summary']['most_consistent'] = {
                'name': operations_by_consistency[0][0],
                'coefficient_of_variation': operations_by_consistency[0][1].get('coefficient_of_variation', 0)
            }
            report['summary']['least_consistent'] = {
                'name': operations_by_consistency[-1][0],
                'coefficient_of_variation': operations_by_consistency[-1][1].get('coefficient_of_variation', 0)
            }
        
        # Performance analysis
        for operation_name, result in results.items():
            mean_time = result.get('mean_time_ms', 0)
            ops_per_sec = result.get('operations_per_second', 0)
            cv = result.get('coefficient_of_variation', 0)
            
            analysis = {
                'performance_rating': 'unknown',
                'consistency_rating': 'unknown',
                'notes': []
            }
            
            # Performance rating
            if mean_time < 1:
                analysis['performance_rating'] = 'excellent'
            elif mean_time < 10:
                analysis['performance_rating'] = 'good'
            elif mean_time < 100:
                analysis['performance_rating'] = 'acceptable'
            else:
                analysis['performance_rating'] = 'poor'
                analysis['notes'].append('High latency detected')
            
            # Consistency rating
            if cv < 0.1:
                analysis['consistency_rating'] = 'excellent'
            elif cv < 0.3:
                analysis['consistency_rating'] = 'good'
            elif cv < 0.5:
                analysis['consistency_rating'] = 'acceptable'
            else:
                analysis['consistency_rating'] = 'poor'
                analysis['notes'].append('High variability detected')
            
            # Throughput analysis
            if ops_per_sec < 10:
                analysis['notes'].append('Low throughput')
            elif ops_per_sec > 1000:
                analysis['notes'].append('High throughput')
            
            report['performance_analysis'][operation_name] = analysis
        
        # Generate recommendations
        slow_operations = [
            name for name, result in results.items()
            if result.get('mean_time_ms', 0) > 100
        ]
        
        if slow_operations:
            report['recommendations'].append(
                f"Optimize slow operations: {', '.join(slow_operations)}"
            )
        
        inconsistent_operations = [
            name for name, result in results.items()
            if result.get('coefficient_of_variation', 0) > 0.5
        ]
        
        if inconsistent_operations:
            report['recommendations'].append(
                f"Investigate performance variability in: {', '.join(inconsistent_operations)}"
            )
        
        return report
    
    def compare_with_baseline(self, current_results, baseline_file):
        """Compare current results with baseline benchmark results."""
        try:
            baseline_results = self.load_benchmark_results(baseline_file)
        except FileNotFoundError:
            return {'error': f'Baseline file {baseline_file} not found'}
        
        comparison = {
            'baseline_file': baseline_file,
            'comparison_timestamp': datetime.now().isoformat(),
            'operations': {},
            'summary': {
                'improved': 0,
                'degraded': 0,
                'stable': 0,
                'new': 0,
                'removed': 0
            }
        }
        
        # Compare each operation
        for operation_name, current_result in current_results.items():
            if operation_name in baseline_results:
                baseline_result = baseline_results[operation_name]
                
                # Use the comparison method from BenchmarkTestCase
                test_case = BenchmarkTestCase()
                op_comparison = test_case.compare_benchmarks(baseline_result, current_result)
                
                comparison['operations'][operation_name] = op_comparison
                
                # Update summary
                status = op_comparison['performance_status']
                if status == 'improved':
                    comparison['summary']['improved'] += 1
                elif status in ['degraded', 'significantly_degraded']:
                    comparison['summary']['degraded'] += 1
                else:
                    comparison['summary']['stable'] += 1
            else:
                comparison['summary']['new'] += 1
                comparison['operations'][operation_name] = {'status': 'new'}
        
        # Check for removed operations
        for operation_name in baseline_results:
            if operation_name not in current_results:
                comparison['summary']['removed'] += 1
                comparison['operations'][operation_name] = {'status': 'removed'}
        
        return comparison


if __name__ == '__main__':
    # Run benchmarks
    runner = BenchmarkRunner()
    
    print("Running Benchmark Suite...")
    results = runner.run_all_benchmarks()
    
    # Save results
    results_file = runner.save_benchmark_results(results)
    
    # Generate report
    report = runner.generate_benchmark_report(results)
    
    print(f"\nBenchmark Summary:")
    print(f"Total benchmarks: {report['summary']['total_benchmarks']}")
    
    if report['summary']['fastest_operation']:
        fastest = report['summary']['fastest_operation']
        print(f"Fastest operation: {fastest['name']} ({fastest['mean_time_ms']:.3f}ms)")
    
    if report['summary']['slowest_operation']:
        slowest = report['summary']['slowest_operation']
        print(f"Slowest operation: {slowest['name']} ({slowest['mean_time_ms']:.3f}ms)")
    
    if report['recommendations']:
        print(f"\nRecommendations:")
        for rec in report['recommendations']:
            print(f"- {rec}")
    
    # Save report
    report_file = runner.save_benchmark_results(report, 'benchmark_report.json')
    print(f"\nDetailed report saved to {report_file}")