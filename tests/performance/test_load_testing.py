"""
Load testing for the Django GraphQL Multi-Schema System.

This module contains load tests that simulate high-traffic scenarios and stress
conditions to validate system behavior under load and identify performance
bottlenecks and scalability limits.
"""

import time
import threading
import queue
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock
import pytest
from django.test import TestCase, TransactionTestCase
from django.core.cache import cache
from django.db import transaction, connections
from django.test.utils import override_settings

from rail_django_graphql.core.registry import schema_registry, SchemaInfo
from rail_django_graphql.decorators import graphql_model, graphql_schema
from rail_django_graphql.plugins.base import BasePlugin, PluginManager
from rail_django_graphql.plugins.hooks import hook_registry


class LoadTestCase(TestCase):
    """Base class for load testing with utilities for stress testing."""
    
    def setUp(self):
        """Set up load testing environment."""
        super().setUp()
        # Clear registry and cache before each test
        schema_registry.clear()
        cache.clear()
        hook_registry.clear()
        
        # Load test configuration
        self.load_config = {
            'light_load': {
                'concurrent_users': 10,
                'requests_per_user': 50,
                'duration_seconds': 30,
            },
            'medium_load': {
                'concurrent_users': 50,
                'requests_per_user': 100,
                'duration_seconds': 60,
            },
            'heavy_load': {
                'concurrent_users': 100,
                'requests_per_user': 200,
                'duration_seconds': 120,
            },
            'stress_load': {
                'concurrent_users': 200,
                'requests_per_user': 500,
                'duration_seconds': 300,
            }
        }
        
        # Performance thresholds
        self.thresholds = {
            'max_response_time': 1.0,      # 1 second max response time
            'p95_response_time': 0.5,      # 500ms for 95th percentile
            'error_rate': 0.01,            # 1% max error rate
            'throughput_rps': 100,         # 100 requests per second minimum
        }
    
    def tearDown(self):
        """Clean up after load tests."""
        super().tearDown()
        schema_registry.clear()
        cache.clear()
        hook_registry.clear()
    
    def run_load_test(self, operation, load_type='light_load', **kwargs):
        """
        Run a load test with specified parameters.
        
        Args:
            operation: Function to execute under load
            load_type: Type of load ('light_load', 'medium_load', 'heavy_load', 'stress_load')
            **kwargs: Additional arguments for the operation
            
        Returns:
            dict: Load test results with metrics
        """
        config = self.load_config[load_type]
        
        results = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'errors': [],
            'start_time': None,
            'end_time': None,
            'duration': 0,
        }
        
        # Shared queue for collecting results
        result_queue = queue.Queue()
        
        def worker(user_id):
            """Worker function for load testing."""
            user_results = {
                'user_id': user_id,
                'requests': 0,
                'successes': 0,
                'failures': 0,
                'response_times': [],
                'errors': []
            }
            
            for request_num in range(config['requests_per_user']):
                start_time = time.perf_counter()
                
                try:
                    # Execute the operation
                    result = operation(user_id=user_id, request_num=request_num, **kwargs)
                    
                    end_time = time.perf_counter()
                    response_time = end_time - start_time
                    
                    user_results['requests'] += 1
                    user_results['successes'] += 1
                    user_results['response_times'].append(response_time)
                    
                except Exception as e:
                    end_time = time.perf_counter()
                    response_time = end_time - start_time
                    
                    user_results['requests'] += 1
                    user_results['failures'] += 1
                    user_results['response_times'].append(response_time)
                    user_results['errors'].append(str(e))
            
            result_queue.put(user_results)
        
        # Start load test
        results['start_time'] = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=config['concurrent_users']) as executor:
            futures = [
                executor.submit(worker, user_id) 
                for user_id in range(config['concurrent_users'])
            ]
            
            # Wait for all workers to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    results['errors'].append(f"Worker error: {str(e)}")
        
        results['end_time'] = time.perf_counter()
        results['duration'] = results['end_time'] - results['start_time']
        
        # Collect results from queue
        while not result_queue.empty():
            user_result = result_queue.get()
            results['total_requests'] += user_result['requests']
            results['successful_requests'] += user_result['successes']
            results['failed_requests'] += user_result['failures']
            results['response_times'].extend(user_result['response_times'])
            results['errors'].extend(user_result['errors'])
        
        # Calculate metrics
        if results['response_times']:
            results['metrics'] = self.calculate_metrics(results)
        
        return results
    
    def calculate_metrics(self, results):
        """Calculate performance metrics from load test results."""
        response_times = results['response_times']
        
        if not response_times:
            return {}
        
        sorted_times = sorted(response_times)
        total_requests = results['total_requests']
        duration = results['duration']
        
        metrics = {
            'throughput_rps': total_requests / duration if duration > 0 else 0,
            'avg_response_time': statistics.mean(response_times),
            'median_response_time': statistics.median(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'p95_response_time': sorted_times[int(0.95 * len(sorted_times))],
            'p99_response_time': sorted_times[int(0.99 * len(sorted_times))],
            'error_rate': results['failed_requests'] / total_requests if total_requests > 0 else 0,
            'success_rate': results['successful_requests'] / total_requests if total_requests > 0 else 0,
            'std_dev': statistics.stdev(response_times) if len(response_times) > 1 else 0,
        }
        
        return metrics
    
    def assert_load_test_thresholds(self, results):
        """Assert that load test results meet performance thresholds."""
        metrics = results.get('metrics', {})
        
        if not metrics:
            self.fail("No metrics available for load test")
        
        # Check error rate
        self.assertLessEqual(
            metrics['error_rate'],
            self.thresholds['error_rate'],
            f"Error rate {metrics['error_rate']:.3f} exceeds threshold {self.thresholds['error_rate']}"
        )
        
        # Check maximum response time
        self.assertLessEqual(
            metrics['max_response_time'],
            self.thresholds['max_response_time'],
            f"Max response time {metrics['max_response_time']:.3f}s exceeds threshold {self.thresholds['max_response_time']}s"
        )
        
        # Check 95th percentile response time
        self.assertLessEqual(
            metrics['p95_response_time'],
            self.thresholds['p95_response_time'],
            f"P95 response time {metrics['p95_response_time']:.3f}s exceeds threshold {self.thresholds['p95_response_time']}s"
        )
        
        # Check throughput (for medium+ loads)
        if results['total_requests'] > 1000:  # Only check for significant loads
            self.assertGreaterEqual(
                metrics['throughput_rps'],
                self.thresholds['throughput_rps'],
                f"Throughput {metrics['throughput_rps']:.1f} RPS below threshold {self.thresholds['throughput_rps']} RPS"
            )


class SchemaRegistrationLoadTest(LoadTestCase):
    """Load tests for schema registration operations."""
    
    def test_concurrent_schema_registration_light_load(self):
        """Test schema registration under light concurrent load."""
        def register_schema_operation(user_id, request_num, **kwargs):
            return schema_registry.register_schema(
                name=f'load_test_schema_{user_id}_{request_num}',
                description=f'Load test schema for user {user_id}, request {request_num}',
                version='1.0.0'
            )
        
        results = self.run_load_test(register_schema_operation, 'light_load')
        
        # Verify all registrations succeeded
        self.assertEqual(results['failed_requests'], 0, f"Registration failures: {results['errors']}")
        self.assertEqual(
            results['successful_requests'],
            self.load_config['light_load']['concurrent_users'] * self.load_config['light_load']['requests_per_user']
        )
        
        # Check performance thresholds
        self.assert_load_test_thresholds(results)
    
    def test_concurrent_schema_registration_medium_load(self):
        """Test schema registration under medium concurrent load."""
        def register_schema_operation(user_id, request_num, **kwargs):
            return schema_registry.register_schema(
                name=f'medium_load_schema_{user_id}_{request_num}',
                description=f'Medium load test schema for user {user_id}, request {request_num}',
                version='1.0.0'
            )
        
        results = self.run_load_test(register_schema_operation, 'medium_load')
        
        # Allow some failures under medium load
        error_rate = results['failed_requests'] / results['total_requests'] if results['total_requests'] > 0 else 0
        self.assertLessEqual(error_rate, 0.05, f"Error rate {error_rate:.3f} too high for medium load")
        
        # Check that most registrations succeeded
        self.assertGreaterEqual(results['successful_requests'], results['total_requests'] * 0.95)
    
    def test_schema_registration_with_hooks_load(self):
        """Test schema registration with hooks under load."""
        # Add hooks that simulate processing time
        def slow_pre_hook(schema_name, **kwargs):
            time.sleep(0.001)  # 1ms processing time
            return kwargs
        
        def slow_post_hook(schema_name, schema_info, **kwargs):
            time.sleep(0.001)  # 1ms processing time
        
        hook_registry.register_hook('pre_registration', slow_pre_hook)
        hook_registry.register_hook('post_registration', slow_post_hook)
        
        def register_with_hooks_operation(user_id, request_num, **kwargs):
            return schema_registry.register_schema(
                name=f'hooked_load_schema_{user_id}_{request_num}',
                description=f'Hooked load test schema for user {user_id}, request {request_num}',
                version='1.0.0'
            )
        
        results = self.run_load_test(register_with_hooks_operation, 'light_load')
        
        # Verify registrations with hooks
        self.assertGreaterEqual(results['successful_requests'], results['total_requests'] * 0.9)
        
        # Response times should be higher due to hooks but still reasonable
        if results['metrics']:
            self.assertLessEqual(results['metrics']['p95_response_time'], 1.0)  # Allow 1s for hooks


class SchemaLookupLoadTest(LoadTestCase):
    """Load tests for schema lookup operations."""
    
    def setUp(self):
        """Set up test schemas for lookup load tests."""
        super().setUp()
        
        # Pre-register schemas for lookup tests
        self.test_schemas = []
        for i in range(100):
            schema = schema_registry.register_schema(
                name=f'lookup_load_schema_{i}',
                description=f'Lookup load test schema {i}',
                version='1.0.0'
            )
            self.test_schemas.append(schema)
    
    def test_concurrent_schema_lookup_light_load(self):
        """Test schema lookups under light concurrent load."""
        def lookup_schema_operation(user_id, request_num, **kwargs):
            schema_index = (user_id * 1000 + request_num) % len(self.test_schemas)
            schema_name = self.test_schemas[schema_index].name
            return schema_registry.get_schema(schema_name)
        
        results = self.run_load_test(lookup_schema_operation, 'light_load')
        
        # All lookups should succeed
        self.assertEqual(results['failed_requests'], 0, f"Lookup failures: {results['errors']}")
        self.assert_load_test_thresholds(results)
    
    def test_concurrent_schema_lookup_heavy_load(self):
        """Test schema lookups under heavy concurrent load."""
        def lookup_schema_operation(user_id, request_num, **kwargs):
            schema_index = (user_id * 1000 + request_num) % len(self.test_schemas)
            schema_name = self.test_schemas[schema_index].name
            return schema_registry.get_schema(schema_name)
        
        results = self.run_load_test(lookup_schema_operation, 'heavy_load')
        
        # Lookups should be very reliable even under heavy load
        error_rate = results['failed_requests'] / results['total_requests'] if results['total_requests'] > 0 else 0
        self.assertLessEqual(error_rate, 0.01, f"Error rate {error_rate:.3f} too high for lookups")
        
        # Lookups should be fast
        if results['metrics']:
            self.assertLessEqual(results['metrics']['p95_response_time'], 0.1)  # 100ms max for lookups
    
    def test_mixed_lookup_operations_load(self):
        """Test mixed lookup operations under load."""
        def mixed_lookup_operation(user_id, request_num, **kwargs):
            operation_type = request_num % 4
            
            if operation_type == 0:
                # Get specific schema
                schema_index = user_id % len(self.test_schemas)
                schema_name = self.test_schemas[schema_index].name
                return schema_registry.get_schema(schema_name)
            
            elif operation_type == 1:
                # List all schemas
                return schema_registry.list_schemas()
            
            elif operation_type == 2:
                # Check schema existence
                schema_index = user_id % len(self.test_schemas)
                schema_name = self.test_schemas[schema_index].name
                return schema_registry.schema_exists(schema_name)
            
            else:
                # Get schema count
                return len(schema_registry.list_schemas())
        
        results = self.run_load_test(mixed_lookup_operation, 'medium_load')
        
        # Mixed operations should be reliable
        error_rate = results['failed_requests'] / results['total_requests'] if results['total_requests'] > 0 else 0
        self.assertLessEqual(error_rate, 0.02, f"Error rate {error_rate:.3f} too high for mixed operations")


class SchemaDiscoveryLoadTest(LoadTestCase):
    """Load tests for schema discovery operations."""
    
    def setUp(self):
        """Set up test models for discovery load tests."""
        super().setUp()
        
        # Create mock models for discovery
        self.mock_models = []
        for i in range(50):
            mock_model = MagicMock()
            mock_model._meta.app_label = f'test_app_{i % 10}'
            mock_model.__name__ = f'TestModel{i}'
            mock_model._graphql_enabled = True
            self.mock_models.append(mock_model)
    
    def test_concurrent_schema_discovery_load(self):
        """Test schema discovery under concurrent load."""
        with patch('django.apps.apps.get_models') as mock_get_models:
            mock_get_models.return_value = self.mock_models
            
            def discovery_operation(user_id, request_num, **kwargs):
                return schema_registry.discover_schemas()
            
            results = self.run_load_test(discovery_operation, 'light_load')
            
            # Discovery should be reliable
            error_rate = results['failed_requests'] / results['total_requests'] if results['total_requests'] > 0 else 0
            self.assertLessEqual(error_rate, 0.05, f"Discovery error rate {error_rate:.3f} too high")
            
            # Discovery can be slower, so use relaxed thresholds
            if results['metrics']:
                self.assertLessEqual(results['metrics']['p95_response_time'], 2.0)  # 2s max for discovery


class MixedOperationsLoadTest(LoadTestCase):
    """Load tests for mixed operations simulating real-world usage."""
    
    def setUp(self):
        """Set up mixed operations test environment."""
        super().setUp()
        
        # Pre-register some schemas
        self.existing_schemas = []
        for i in range(50):
            schema = schema_registry.register_schema(
                name=f'existing_schema_{i}',
                description=f'Existing schema {i}',
                version='1.0.0'
            )
            self.existing_schemas.append(schema)
    
    def test_realistic_workload_simulation(self):
        """Test realistic workload with mixed operations."""
        def realistic_operation(user_id, request_num, **kwargs):
            # Simulate realistic usage patterns
            operation_type = request_num % 10
            
            if operation_type < 6:  # 60% lookups
                schema_index = (user_id + request_num) % len(self.existing_schemas)
                schema_name = self.existing_schemas[schema_index].name
                return schema_registry.get_schema(schema_name)
            
            elif operation_type < 8:  # 20% listings
                return schema_registry.list_schemas()
            
            elif operation_type < 9:  # 10% existence checks
                schema_index = (user_id + request_num) % len(self.existing_schemas)
                schema_name = self.existing_schemas[schema_index].name
                return schema_registry.schema_exists(schema_name)
            
            else:  # 10% new registrations
                return schema_registry.register_schema(
                    name=f'new_schema_{user_id}_{request_num}',
                    description=f'New schema from user {user_id}, request {request_num}',
                    version='1.0.0'
                )
        
        results = self.run_load_test(realistic_operation, 'medium_load')
        
        # Realistic workload should be very reliable
        error_rate = results['failed_requests'] / results['total_requests'] if results['total_requests'] > 0 else 0
        self.assertLessEqual(error_rate, 0.02, f"Realistic workload error rate {error_rate:.3f} too high")
        
        # Performance should meet thresholds
        self.assert_load_test_thresholds(results)
    
    def test_burst_traffic_simulation(self):
        """Test system behavior under burst traffic conditions."""
        def burst_operation(user_id, request_num, **kwargs):
            # Simulate burst of registrations followed by lookups
            if request_num < 10:  # First 10 requests are registrations
                return schema_registry.register_schema(
                    name=f'burst_schema_{user_id}_{request_num}',
                    description=f'Burst schema from user {user_id}, request {request_num}',
                    version='1.0.0'
                )
            else:  # Remaining requests are lookups
                # Look up recently registered schemas
                lookup_request = request_num - 10
                target_user = (user_id + lookup_request) % self.load_config['medium_load']['concurrent_users']
                target_request = lookup_request % 10
                schema_name = f'burst_schema_{target_user}_{target_request}'
                
                # Try to get the schema, might not exist yet due to timing
                try:
                    return schema_registry.get_schema(schema_name)
                except:
                    # Fall back to existing schema
                    schema_index = lookup_request % len(self.existing_schemas)
                    return self.existing_schemas[schema_index]
        
        results = self.run_load_test(burst_operation, 'medium_load')
        
        # Burst traffic might have higher error rates due to timing
        error_rate = results['failed_requests'] / results['total_requests'] if results['total_requests'] > 0 else 0
        self.assertLessEqual(error_rate, 0.1, f"Burst traffic error rate {error_rate:.3f} too high")


class StressTest(LoadTestCase):
    """Stress tests to find system limits and breaking points."""
    
    def test_memory_stress_test(self):
        """Test system behavior under memory stress."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        def memory_stress_operation(user_id, request_num, **kwargs):
            # Create schemas with large descriptions to use memory
            large_description = "A" * 1000  # 1KB description
            return schema_registry.register_schema(
                name=f'memory_stress_schema_{user_id}_{request_num}',
                description=large_description,
                version='1.0.0'
            )
        
        results = self.run_load_test(memory_stress_operation, 'medium_load')
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        max_expected_memory = 100 * 1024 * 1024  # 100MB
        self.assertLess(
            memory_increase,
            max_expected_memory,
            f"Memory increased by {memory_increase / 1024 / 1024:.2f} MB"
        )
        
        # Most operations should succeed even under memory stress
        error_rate = results['failed_requests'] / results['total_requests'] if results['total_requests'] > 0 else 0
        self.assertLessEqual(error_rate, 0.1, f"Memory stress error rate {error_rate:.3f} too high")
    
    def test_connection_stress_test(self):
        """Test system behavior under database connection stress."""
        def connection_stress_operation(user_id, request_num, **kwargs):
            # Force database access by checking schema existence
            schema_name = f'connection_stress_schema_{user_id}_{request_num}'
            
            # Register schema (uses database)
            schema = schema_registry.register_schema(
                name=schema_name,
                description=f'Connection stress schema {user_id}-{request_num}',
                version='1.0.0'
            )
            
            # Immediately look it up (uses database/cache)
            return schema_registry.get_schema(schema_name)
        
        results = self.run_load_test(connection_stress_operation, 'medium_load')
        
        # Connection stress might cause some failures
        error_rate = results['failed_requests'] / results['total_requests'] if results['total_requests'] > 0 else 0
        self.assertLessEqual(error_rate, 0.15, f"Connection stress error rate {error_rate:.3f} too high")
    
    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    })
    def test_no_cache_stress_test(self):
        """Test system behavior without caching under stress."""
        def no_cache_operation(user_id, request_num, **kwargs):
            # Mix of operations without cache benefits
            if request_num % 2 == 0:
                return schema_registry.register_schema(
                    name=f'no_cache_schema_{user_id}_{request_num}',
                    description=f'No cache schema {user_id}-{request_num}',
                    version='1.0.0'
                )
            else:
                # Look up a schema (no cache benefit)
                target_request = request_num - 1 if request_num > 0 else 0
                schema_name = f'no_cache_schema_{user_id}_{target_request}'
                try:
                    return schema_registry.get_schema(schema_name)
                except:
                    # Schema might not exist, return None
                    return None
        
        results = self.run_load_test(no_cache_operation, 'light_load')
        
        # Without caching, performance will be worse but should still work
        error_rate = results['failed_requests'] / results['total_requests'] if results['total_requests'] > 0 else 0
        self.assertLessEqual(error_rate, 0.2, f"No cache error rate {error_rate:.3f} too high")


# Load test runner and reporting
class LoadTestRunner:
    """Utility class for running load tests and generating reports."""
    
    @staticmethod
    def run_load_test_suite():
        """Run all load tests and generate a comprehensive report."""
        import unittest
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add test classes
        test_classes = [
            SchemaRegistrationLoadTest,
            SchemaLookupLoadTest,
            SchemaDiscoveryLoadTest,
            MixedOperationsLoadTest,
            StressTest,
        ]
        
        for test_class in test_classes:
            tests = loader.loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result
    
    @staticmethod
    def generate_load_test_report(results):
        """Generate a detailed load test report."""
        report = {
            'summary': {
                'total_tests': len(results),
                'passed_tests': sum(1 for r in results if r['success']),
                'failed_tests': sum(1 for r in results if not r['success']),
            },
            'performance_metrics': {},
            'recommendations': []
        }
        
        # Aggregate performance metrics
        all_response_times = []
        all_throughputs = []
        all_error_rates = []
        
        for result in results:
            if result.get('metrics'):
                metrics = result['metrics']
                all_response_times.extend(result.get('response_times', []))
                all_throughputs.append(metrics.get('throughput_rps', 0))
                all_error_rates.append(metrics.get('error_rate', 0))
        
        if all_response_times:
            report['performance_metrics'] = {
                'overall_avg_response_time': statistics.mean(all_response_times),
                'overall_p95_response_time': sorted(all_response_times)[int(0.95 * len(all_response_times))],
                'avg_throughput_rps': statistics.mean(all_throughputs) if all_throughputs else 0,
                'avg_error_rate': statistics.mean(all_error_rates) if all_error_rates else 0,
            }
        
        # Generate recommendations
        if report['performance_metrics'].get('avg_error_rate', 0) > 0.05:
            report['recommendations'].append("High error rate detected. Consider optimizing error handling and retry logic.")
        
        if report['performance_metrics'].get('overall_p95_response_time', 0) > 1.0:
            report['recommendations'].append("High response times detected. Consider implementing caching and query optimization.")
        
        if report['performance_metrics'].get('avg_throughput_rps', 0) < 50:
            report['recommendations'].append("Low throughput detected. Consider scaling horizontally or optimizing bottlenecks.")
        
        return report


if __name__ == '__main__':
    # Run load tests
    runner = LoadTestRunner()
    
    print("Running Load Test Suite...")
    result = runner.run_load_test_suite()
    
    print(f"\nLoad Test Results:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")