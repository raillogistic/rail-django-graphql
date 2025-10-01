"""
Performance tests for the Django GraphQL Multi-Schema System.

This package contains comprehensive performance tests to measure and validate
the system's behavior under various load conditions and usage patterns.

Test Categories:
    - Schema Registration Performance: Tests for schema registration operations
      including single, bulk, concurrent, and with hooks scenarios
    - Schema Discovery Performance: Tests for model discovery and schema
      auto-detection performance under various conditions
    - Schema Lookup Performance: Tests for schema retrieval operations
      including by name, existence checks, and listing operations
    - Concurrent Access Performance: Tests for thread-safe operations
      and concurrent access patterns
    - Plugin System Performance: Tests for plugin loading and execution
      performance impact
    - Caching Performance: Tests for cache effectiveness and performance
      improvements
    - Memory Leak Detection: Tests to detect memory leaks and resource
      management issues
    - Load Testing: Stress tests simulating high-traffic scenarios and
      system limits under various load conditions
    - Benchmarking: Performance measurement and comparison tests for
      establishing baselines and detecting regressions

Usage:
    Run all performance tests:
        python -m pytest tests/performance/
    
    Run specific test category:
        python -m pytest tests/performance/test_schema_registry_performance.py
        python -m pytest tests/performance/test_load_testing.py
        python -m pytest tests/performance/test_benchmarks.py
    
    Run with performance reporting:
        python tests/performance/test_schema_registry_performance.py
        python tests/performance/test_load_testing.py
        python tests/performance/test_benchmarks.py
    
    Run load tests:
        python tests/performance/test_load_testing.py
    
    Run benchmarks:
        python tests/performance/test_benchmarks.py
"""

from .test_schema_registry_performance import (
    SchemaRegistrationPerformanceTest,
    SchemaDiscoveryPerformanceTest,
    SchemaLookupPerformanceTest,
    ConcurrentAccessPerformanceTest,
    PluginSystemPerformanceTest,
    CachingPerformanceTest,
    MemoryLeakDetectionTest,
    PerformanceTestRunner,
)

from .test_load_testing import (
    LoadTestCase,
    SchemaRegistrationLoadTest,
    SchemaLookupLoadTest,
    SchemaDiscoveryLoadTest,
    MixedOperationsLoadTest,
    StressTest,
    LoadTestRunner,
)

from .test_benchmarks import (
    BenchmarkTestCase,
    SchemaRegistrationBenchmarks,
    SchemaLookupBenchmarks,
    SchemaDiscoveryBenchmarks,
    CachingBenchmarks,
    PluginSystemBenchmarks,
    HookSystemBenchmarks,
    BenchmarkRunner,
)

__all__ = [
    'SchemaRegistrationPerformanceTest',
    'SchemaDiscoveryPerformanceTest',
    'SchemaLookupPerformanceTest',
    'ConcurrentAccessPerformanceTest',
    'PluginSystemPerformanceTest',
    'CachingPerformanceTest',
    'MemoryLeakDetectionTest',
    'PerformanceTestRunner',
    'LoadTestCase',
    'SchemaRegistrationLoadTest',
    'SchemaLookupLoadTest',
    'SchemaDiscoveryLoadTest',
    'MixedOperationsLoadTest',
    'StressTest',
    'LoadTestRunner',
    'BenchmarkTestCase',
    'SchemaRegistrationBenchmarks',
    'SchemaLookupBenchmarks',
    'SchemaDiscoveryBenchmarks',
    'CachingBenchmarks',
    'PluginSystemBenchmarks',
    'HookSystemBenchmarks',
    'BenchmarkRunner',
]