"""
Performance tests for the Django GraphQL Multi-Schema System.

This module contains comprehensive performance tests for schema registry operations,
including registration, discovery, query execution, and concurrent access patterns.
"""

import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock
import pytest
from django.test import TestCase, TransactionTestCase
from django.core.cache import cache
from django.db import transaction
from django.apps import apps

from rail_django_graphql.core.registry import schema_registry, SchemaInfo
from rail_django_graphql.decorators import graphql_model, graphql_schema
from rail_django_graphql.plugins.base import BasePlugin, PluginManager
from rail_django_graphql.plugins.hooks import hook_registry


class PerformanceTestCase(TestCase):
    """Base class for performance tests with timing utilities."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Clear registry and cache before each test
        schema_registry.clear()
        cache.clear()
        hook_registry.clear()
        
        # Performance thresholds (in seconds)
        self.thresholds = {
            'schema_registration': 0.1,  # 100ms
            'schema_discovery': 0.5,     # 500ms
            'schema_lookup': 0.01,       # 10ms
            'bulk_operations': 2.0,      # 2s for bulk operations
            'concurrent_access': 1.0,    # 1s for concurrent operations
        }
    
    def tearDown(self):
        """Clean up after tests."""
        super().tearDown()
        schema_registry.clear()
        cache.clear()
        hook_registry.clear()
    
    def time_operation(self, operation, *args, **kwargs):
        """Time an operation and return (result, duration)."""
        start_time = time.perf_counter()
        result = operation(*args, **kwargs)
        end_time = time.perf_counter()
        duration = end_time - start_time
        return result, duration
    
    def assert_performance(self, duration, threshold_key, operation_name=""):
        """Assert that operation meets performance threshold."""
        threshold = self.thresholds[threshold_key]
        self.assertLess(
            duration, 
            threshold,
            f"{operation_name} took {duration:.3f}s, exceeds threshold of {threshold}s"
        )
    
    def measure_multiple_operations(self, operation, iterations=100, *args, **kwargs):
        """Measure multiple iterations of an operation."""
        durations = []
        
        for _ in range(iterations):
            _, duration = self.time_operation(operation, *args, **kwargs)
            durations.append(duration)
        
        return {
            'min': min(durations),
            'max': max(durations),
            'mean': statistics.mean(durations),
            'median': statistics.median(durations),
            'stdev': statistics.stdev(durations) if len(durations) > 1 else 0,
            'p95': sorted(durations)[int(0.95 * len(durations))],
            'p99': sorted(durations)[int(0.99 * len(durations))],
        }


class SchemaRegistrationPerformanceTest(PerformanceTestCase):
    """Performance tests for schema registration operations."""
    
    def test_single_schema_registration_performance(self):
        """Test performance of registering a single schema."""
        def register_schema():
            return schema_registry.register_schema(
                name=f'test_schema_{int(time.time() * 1000000)}',
                description='Performance test schema',
                version='1.0.0'
            )
        
        result, duration = self.time_operation(register_schema)
        
        self.assertIsNotNone(result)
        self.assert_performance(duration, 'schema_registration', 'Single schema registration')
    
    def test_bulk_schema_registration_performance(self):
        """Test performance of registering multiple schemas."""
        schema_count = 50
        
        def register_bulk_schemas():
            schemas = []
            for i in range(schema_count):
                schema = schema_registry.register_schema(
                    name=f'bulk_schema_{i}',
                    description=f'Bulk test schema {i}',
                    version='1.0.0'
                )
                schemas.append(schema)
            return schemas
        
        result, duration = self.time_operation(register_bulk_schemas)
        
        self.assertEqual(len(result), schema_count)
        self.assert_performance(duration, 'bulk_operations', f'Bulk registration of {schema_count} schemas')
        
        # Test average per-schema time
        avg_per_schema = duration / schema_count
        self.assertLess(avg_per_schema, 0.05, f"Average per-schema registration time: {avg_per_schema:.3f}s")
    
    def test_schema_registration_with_hooks_performance(self):
        """Test performance impact of discovery hooks on registration."""
        # Add multiple hooks
        hook_calls = []
        
        def slow_pre_hook(schema_name, **kwargs):
            time.sleep(0.01)  # Simulate some processing
            hook_calls.append(f'pre_{schema_name}')
            return kwargs
        
        def slow_post_hook(schema_name, schema_info, **kwargs):
            time.sleep(0.01)  # Simulate some processing
            hook_calls.append(f'post_{schema_name}')
        
        # Register hooks
        hook_registry.register_hook('pre_registration', slow_pre_hook)
        hook_registry.register_hook('post_registration', slow_post_hook)
        
        def register_with_hooks():
            return schema_registry.register_schema(
                name='hooked_schema',
                description='Schema with hooks',
                version='1.0.0'
            )
        
        result, duration = self.time_operation(register_with_hooks)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(hook_calls), 2)  # Pre and post hooks called
        # Allow more time due to hook processing
        self.assertLess(duration, 0.5, f"Registration with hooks took {duration:.3f}s")
    
    def test_schema_registration_memory_usage(self):
        """Test memory usage during schema registration."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Register many schemas
        schema_count = 100
        for i in range(schema_count):
            schema_registry.register_schema(
                name=f'memory_test_schema_{i}',
                description=f'Memory test schema {i}',
                version='1.0.0'
            )
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        memory_per_schema = memory_increase / schema_count
        
        # Memory increase should be reasonable (less than 1MB per schema)
        self.assertLess(
            memory_per_schema, 
            1024 * 1024,  # 1MB
            f"Memory usage per schema: {memory_per_schema / 1024:.2f} KB"
        )


class SchemaDiscoveryPerformanceTest(PerformanceTestCase):
    """Performance tests for schema discovery operations."""
    
    def setUp(self):
        """Set up test models for discovery."""
        super().setUp()
        
        # Create test models dynamically
        from django.db import models
        
        class TestModel1(models.Model):
            name = models.CharField(max_length=100)
            
            class Meta:
                app_label = 'test_app'
        
        class TestModel2(models.Model):
            title = models.CharField(max_length=200)
            description = models.TextField()
            
            class Meta:
                app_label = 'test_app'
        
        # Apply decorators
        graphql_model(TestModel1)
        graphql_model(TestModel2)
        
        self.test_models = [TestModel1, TestModel2]
    
    def test_model_discovery_performance(self):
        """Test performance of discovering GraphQL models."""
        def discover_models():
            return schema_registry.discover_schemas()
        
        result, duration = self.time_operation(discover_models)
        
        self.assertIsInstance(result, list)
        self.assert_performance(duration, 'schema_discovery', 'Model discovery')
    
    def test_repeated_discovery_performance(self):
        """Test performance of repeated discovery operations."""
        iterations = 10
        
        def repeated_discovery():
            results = []
            for _ in range(iterations):
                result = schema_registry.discover_schemas()
                results.append(result)
            return results
        
        result, duration = self.time_operation(repeated_discovery)
        
        self.assertEqual(len(result), iterations)
        avg_per_discovery = duration / iterations
        self.assertLess(avg_per_discovery, 0.1, f"Average discovery time: {avg_per_discovery:.3f}s")
    
    def test_discovery_with_large_app_registry(self):
        """Test discovery performance with many registered apps."""
        # Mock a large number of apps
        with patch('django.apps.apps.get_models') as mock_get_models:
            # Create mock models
            mock_models = []
            for i in range(200):  # Simulate 200 models
                mock_model = MagicMock()
                mock_model._meta.app_label = f'app_{i % 20}'  # 20 apps with 10 models each
                mock_model.__name__ = f'Model{i}'
                mock_models.append(mock_model)
            
            mock_get_models.return_value = mock_models
            
            def discover_large_registry():
                return schema_registry.discover_schemas()
            
            result, duration = self.time_operation(discover_large_registry)
            
            self.assertIsInstance(result, list)
            self.assert_performance(duration, 'schema_discovery', 'Large app registry discovery')


class SchemaLookupPerformanceTest(PerformanceTestCase):
    """Performance tests for schema lookup operations."""
    
    def setUp(self):
        """Set up test schemas for lookup tests."""
        super().setUp()
        
        # Register test schemas
        self.test_schemas = []
        for i in range(50):
            schema = schema_registry.register_schema(
                name=f'lookup_test_schema_{i}',
                description=f'Lookup test schema {i}',
                version='1.0.0'
            )
            self.test_schemas.append(schema)
    
    def test_schema_lookup_by_name_performance(self):
        """Test performance of looking up schemas by name."""
        schema_name = self.test_schemas[25].name  # Middle schema
        
        def lookup_schema():
            return schema_registry.get_schema(schema_name)
        
        result, duration = self.time_operation(lookup_schema)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.name, schema_name)
        self.assert_performance(duration, 'schema_lookup', 'Schema lookup by name')
    
    def test_multiple_schema_lookups_performance(self):
        """Test performance of multiple schema lookups."""
        lookup_count = 100
        
        def multiple_lookups():
            results = []
            for i in range(lookup_count):
                schema_index = i % len(self.test_schemas)
                schema_name = self.test_schemas[schema_index].name
                result = schema_registry.get_schema(schema_name)
                results.append(result)
            return results
        
        result, duration = self.time_operation(multiple_lookups)
        
        self.assertEqual(len(result), lookup_count)
        avg_per_lookup = duration / lookup_count
        self.assertLess(avg_per_lookup, 0.001, f"Average lookup time: {avg_per_lookup:.6f}s")
    
    def test_schema_listing_performance(self):
        """Test performance of listing all schemas."""
        def list_schemas():
            return schema_registry.list_schemas()
        
        result, duration = self.time_operation(list_schemas)
        
        self.assertEqual(len(result), len(self.test_schemas))
        self.assert_performance(duration, 'schema_lookup', 'Schema listing')
    
    def test_schema_exists_check_performance(self):
        """Test performance of schema existence checks."""
        existing_schema = self.test_schemas[0].name
        non_existing_schema = 'non_existing_schema'
        
        def check_existence():
            results = []
            for _ in range(100):
                results.append(schema_registry.schema_exists(existing_schema))
                results.append(schema_registry.schema_exists(non_existing_schema))
            return results
        
        result, duration = self.time_operation(check_existence)
        
        self.assertEqual(len(result), 200)
        self.assertEqual(sum(result), 100)  # Only existing schema returns True
        avg_per_check = duration / 200
        self.assertLess(avg_per_check, 0.0005, f"Average existence check time: {avg_per_check:.6f}s")


class ConcurrentAccessPerformanceTest(TransactionTestCase):
    """Performance tests for concurrent access to schema registry."""
    
    def setUp(self):
        """Set up test environment for concurrent tests."""
        super().setUp()
        schema_registry.clear()
        cache.clear()
    
    def tearDown(self):
        """Clean up after concurrent tests."""
        super().tearDown()
        schema_registry.clear()
        cache.clear()
    
    def test_concurrent_schema_registration(self):
        """Test performance of concurrent schema registration."""
        thread_count = 10
        schemas_per_thread = 5
        results = []
        errors = []
        
        def register_schemas_worker(thread_id):
            """Worker function for concurrent registration."""
            thread_results = []
            try:
                for i in range(schemas_per_thread):
                    schema = schema_registry.register_schema(
                        name=f'concurrent_schema_{thread_id}_{i}',
                        description=f'Concurrent test schema {thread_id}-{i}',
                        version='1.0.0'
                    )
                    thread_results.append(schema)
            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")
            return thread_results
        
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = [
                executor.submit(register_schemas_worker, i) 
                for i in range(thread_count)
            ]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.extend(result)
                except Exception as e:
                    errors.append(str(e))
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # Verify results
        expected_count = thread_count * schemas_per_thread
        self.assertEqual(len(results), expected_count, f"Errors: {errors}")
        self.assertEqual(len(errors), 0, f"Concurrent registration errors: {errors}")
        
        # Performance assertion
        self.assertLess(
            duration, 
            self.thresholds['concurrent_access'],
            f"Concurrent registration took {duration:.3f}s"
        )
    
    def test_concurrent_schema_lookup(self):
        """Test performance of concurrent schema lookups."""
        # Pre-register schemas
        test_schemas = []
        for i in range(20):
            schema = schema_registry.register_schema(
                name=f'lookup_schema_{i}',
                description=f'Lookup test schema {i}',
                version='1.0.0'
            )
            test_schemas.append(schema)
        
        thread_count = 20
        lookups_per_thread = 50
        results = []
        errors = []
        
        def lookup_worker(thread_id):
            """Worker function for concurrent lookups."""
            thread_results = []
            try:
                for i in range(lookups_per_thread):
                    schema_index = (thread_id + i) % len(test_schemas)
                    schema_name = test_schemas[schema_index].name
                    result = schema_registry.get_schema(schema_name)
                    thread_results.append(result)
            except Exception as e:
                errors.append(f"Thread {thread_id}: {str(e)}")
            return thread_results
        
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = [
                executor.submit(lookup_worker, i) 
                for i in range(thread_count)
            ]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.extend(result)
                except Exception as e:
                    errors.append(str(e))
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # Verify results
        expected_count = thread_count * lookups_per_thread
        self.assertEqual(len(results), expected_count, f"Errors: {errors}")
        self.assertEqual(len(errors), 0, f"Concurrent lookup errors: {errors}")
        
        # Performance assertion
        self.assertLess(
            duration, 
            self.thresholds['concurrent_access'],
            f"Concurrent lookups took {duration:.3f}s"
        )
    
    def test_mixed_concurrent_operations(self):
        """Test performance of mixed concurrent operations."""
        registration_threads = 5
        lookup_threads = 10
        listing_threads = 3
        
        results = {'registrations': [], 'lookups': [], 'listings': []}
        errors = []
        
        # Pre-register some schemas for lookups
        initial_schemas = []
        for i in range(10):
            schema = schema_registry.register_schema(
                name=f'initial_schema_{i}',
                description=f'Initial schema {i}',
                version='1.0.0'
            )
            initial_schemas.append(schema)
        
        def registration_worker(thread_id):
            """Worker for schema registration."""
            try:
                for i in range(3):
                    schema = schema_registry.register_schema(
                        name=f'mixed_reg_schema_{thread_id}_{i}',
                        description=f'Mixed test registration {thread_id}-{i}',
                        version='1.0.0'
                    )
                    results['registrations'].append(schema)
            except Exception as e:
                errors.append(f"Registration thread {thread_id}: {str(e)}")
        
        def lookup_worker(thread_id):
            """Worker for schema lookups."""
            try:
                for i in range(10):
                    schema_index = (thread_id + i) % len(initial_schemas)
                    schema_name = initial_schemas[schema_index].name
                    result = schema_registry.get_schema(schema_name)
                    results['lookups'].append(result)
            except Exception as e:
                errors.append(f"Lookup thread {thread_id}: {str(e)}")
        
        def listing_worker(thread_id):
            """Worker for schema listing."""
            try:
                for i in range(5):
                    schemas = schema_registry.list_schemas()
                    results['listings'].append(len(schemas))
            except Exception as e:
                errors.append(f"Listing thread {thread_id}: {str(e)}")
        
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            
            # Submit registration workers
            for i in range(registration_threads):
                futures.append(executor.submit(registration_worker, i))
            
            # Submit lookup workers
            for i in range(lookup_threads):
                futures.append(executor.submit(lookup_worker, i))
            
            # Submit listing workers
            for i in range(listing_threads):
                futures.append(executor.submit(listing_worker, i))
            
            # Wait for all to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    errors.append(str(e))
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # Verify results
        self.assertEqual(len(results['registrations']), registration_threads * 3)
        self.assertEqual(len(results['lookups']), lookup_threads * 10)
        self.assertEqual(len(results['listings']), listing_threads * 5)
        self.assertEqual(len(errors), 0, f"Mixed concurrent operation errors: {errors}")
        
        # Performance assertion
        self.assertLess(
            duration, 
            2.0,  # Allow more time for mixed operations
            f"Mixed concurrent operations took {duration:.3f}s"
        )


class PluginPerformanceTest(PerformanceTestCase):
    """Performance tests for plugin system."""
    
    def setUp(self):
        """Set up test plugins."""
        super().setUp()
        
        class FastPlugin(BasePlugin):
            """Fast plugin for performance testing."""
            
            def pre_registration_hook(self, schema_name, **kwargs):
                return kwargs
            
            def post_registration_hook(self, schema_name, schema_info, **kwargs):
                pass
            
            def validate_schema(self, schema_info):
                return True, []
        
        class SlowPlugin(BasePlugin):
            """Slow plugin for performance testing."""
            
            def pre_registration_hook(self, schema_name, **kwargs):
                time.sleep(0.01)  # Simulate slow processing
                return kwargs
            
            def post_registration_hook(self, schema_name, schema_info, **kwargs):
                time.sleep(0.01)  # Simulate slow processing
            
            def validate_schema(self, schema_info):
                time.sleep(0.005)  # Simulate validation work
                return True, []
        
        self.fast_plugin = FastPlugin()
        self.slow_plugin = SlowPlugin()
    
    def test_plugin_loading_performance(self):
        """Test performance of plugin loading."""
        plugin_manager = PluginManager()
        
        def load_plugins():
            # Simulate loading multiple plugins
            plugins = [self.fast_plugin, self.slow_plugin] * 10
            for plugin in plugins:
                plugin_manager.load_plugin(plugin)
            return len(plugin_manager.plugins)
        
        result, duration = self.time_operation(load_plugins)
        
        self.assertEqual(result, 20)  # 2 plugins * 10
        self.assertLess(duration, 0.1, f"Plugin loading took {duration:.3f}s")
    
    def test_plugin_hook_execution_performance(self):
        """Test performance of plugin hook execution."""
        plugin_manager = PluginManager()
        plugin_manager.load_plugin(self.fast_plugin)
        plugin_manager.load_plugin(self.slow_plugin)
        
        def execute_hooks():
            results = []
            for i in range(10):
                # Pre-registration hooks
                pre_result = plugin_manager.run_pre_registration_hooks(
                    f'test_schema_{i}',
                    description='Test schema',
                    version='1.0.0'
                )
                results.append(pre_result)
                
                # Post-registration hooks (mock schema info)
                mock_schema = SchemaInfo(
                    name=f'test_schema_{i}',
                    description='Test schema',
                    version='1.0.0'
                )
                plugin_manager.run_post_registration_hooks(
                    f'test_schema_{i}',
                    mock_schema
                )
            return results
        
        result, duration = self.time_operation(execute_hooks)
        
        self.assertEqual(len(result), 10)
        # Allow time for slow plugin processing
        self.assertLess(duration, 1.0, f"Plugin hook execution took {duration:.3f}s")


class CachePerformanceTest(PerformanceTestCase):
    """Performance tests for caching functionality."""
    
    def setUp(self):
        """Set up caching tests."""
        super().setUp()
        
        # Register test schemas
        self.test_schemas = []
        for i in range(20):
            schema = schema_registry.register_schema(
                name=f'cache_test_schema_{i}',
                description=f'Cache test schema {i}',
                version='1.0.0'
            )
            self.test_schemas.append(schema)
    
    def test_cached_schema_lookup_performance(self):
        """Test performance improvement with caching."""
        schema_name = self.test_schemas[0].name
        
        # First lookup (cache miss)
        def first_lookup():
            return schema_registry.get_schema(schema_name)
        
        result1, duration1 = self.time_operation(first_lookup)
        
        # Second lookup (cache hit)
        def second_lookup():
            return schema_registry.get_schema(schema_name)
        
        result2, duration2 = self.time_operation(second_lookup)
        
        self.assertEqual(result1.name, result2.name)
        # Cache hit should be faster (though this might be minimal for in-memory registry)
        self.assertLessEqual(duration2, duration1 * 2)  # Allow some variance
    
    def test_cache_invalidation_performance(self):
        """Test performance of cache invalidation."""
        # Fill cache with lookups
        for schema in self.test_schemas[:10]:
            schema_registry.get_schema(schema.name)
        
        def clear_cache():
            cache.clear()
            # Verify cache is cleared by doing lookups
            results = []
            for schema in self.test_schemas[:5]:
                result = schema_registry.get_schema(schema.name)
                results.append(result)
            return results
        
        result, duration = self.time_operation(clear_cache)
        
        self.assertEqual(len(result), 5)
        self.assertLess(duration, 0.1, f"Cache invalidation and reload took {duration:.3f}s")


class MemoryLeakTest(PerformanceTestCase):
    """Tests for memory leaks in schema registry operations."""
    
    def test_repeated_registration_memory_stability(self):
        """Test that repeated registrations don't cause memory leaks."""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss
        
        # Perform many registration/deregistration cycles
        for cycle in range(10):
            # Register schemas
            schemas = []
            for i in range(50):
                schema = schema_registry.register_schema(
                    name=f'memory_leak_test_{cycle}_{i}',
                    description=f'Memory leak test schema {cycle}-{i}',
                    version='1.0.0'
                )
                schemas.append(schema)
            
            # Clear registry
            schema_registry.clear()
            
            # Force garbage collection
            gc.collect()
        
        # Final memory check
        final_memory = process.memory_info().rss
        memory_increase = final_memory - baseline_memory
        
        # Memory increase should be minimal (less than 10MB)
        self.assertLess(
            memory_increase,
            10 * 1024 * 1024,  # 10MB
            f"Memory increased by {memory_increase / 1024 / 1024:.2f} MB after repeated operations"
        )


# Performance test runner
class PerformanceTestRunner:
    """Utility class for running performance tests and generating reports."""
    
    @staticmethod
    def run_performance_suite():
        """Run all performance tests and generate a report."""
        import unittest
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add test classes
        test_classes = [
            SchemaRegistrationPerformanceTest,
            SchemaDiscoveryPerformanceTest,
            SchemaLookupPerformanceTest,
            ConcurrentAccessPerformanceTest,
            PluginPerformanceTest,
            CachePerformanceTest,
            MemoryLeakTest,
        ]
        
        for test_class in test_classes:
            tests = loader.loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result
    
    @staticmethod
    def benchmark_operations():
        """Benchmark key operations and return metrics."""
        from django.test.utils import setup_test_environment, teardown_test_environment
        
        setup_test_environment()
        
        try:
            # Initialize test case for utilities
            test_case = PerformanceTestCase()
            test_case.setUp()
            
            benchmarks = {}
            
            # Benchmark schema registration
            def register_schema():
                return schema_registry.register_schema(
                    name=f'benchmark_schema_{int(time.time() * 1000000)}',
                    description='Benchmark schema',
                    version='1.0.0'
                )
            
            benchmarks['schema_registration'] = test_case.measure_multiple_operations(
                register_schema, iterations=100
            )
            
            # Benchmark schema lookup
            # First register some schemas
            test_schemas = []
            for i in range(50):
                schema = schema_registry.register_schema(
                    name=f'lookup_benchmark_schema_{i}',
                    description=f'Lookup benchmark schema {i}',
                    version='1.0.0'
                )
                test_schemas.append(schema)
            
            def lookup_schema():
                schema_name = test_schemas[25].name  # Middle schema
                return schema_registry.get_schema(schema_name)
            
            benchmarks['schema_lookup'] = test_case.measure_multiple_operations(
                lookup_schema, iterations=1000
            )
            
            # Benchmark schema listing
            def list_schemas():
                return schema_registry.list_schemas()
            
            benchmarks['schema_listing'] = test_case.measure_multiple_operations(
                list_schemas, iterations=100
            )
            
            return benchmarks
            
        finally:
            teardown_test_environment()


if __name__ == '__main__':
    # Run performance tests
    runner = PerformanceTestRunner()
    
    print("Running Performance Test Suite...")
    result = runner.run_performance_suite()
    
    print("\nRunning Benchmarks...")
    benchmarks = runner.benchmark_operations()
    
    print("\nBenchmark Results:")
    for operation, metrics in benchmarks.items():
        print(f"\n{operation.replace('_', ' ').title()}:")
        print(f"  Mean: {metrics['mean']:.6f}s")
        print(f"  Median: {metrics['median']:.6f}s")
        print(f"  P95: {metrics['p95']:.6f}s")
        print(f"  P99: {metrics['p99']:.6f}s")
        print(f"  Min: {metrics['min']:.6f}s")
        print(f"  Max: {metrics['max']:.6f}s")
        print(f"  StdDev: {metrics['stdev']:.6f}s")