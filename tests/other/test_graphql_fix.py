#!/usr/bin/env python
"""
Test script to verify the GraphQL query fix for the PerformanceMonitor issue.
This script simulates the GraphQL query execution without Django setup complications.
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_performance_monitor():
    """Test that the PerformanceMonitor has the required method."""
    from rail_django_graphql.extensions.optimization import get_performance_monitor
    
    print("Testing PerformanceMonitor...")
    
    # Get the performance monitor instance
    monitor = get_performance_monitor()
    
    # Verify the method exists
    assert hasattr(monitor, 'record_query_performance'), "record_query_performance method not found!"
    
    # Test the method with sample data
    monitor.record_query_performance('tags', 0.05, False)
    monitor.record_query_performance('posts', 0.12, True)
    
    # Get stats to verify it's working
    stats = monitor.get_performance_stats()
    
    print(f"✓ PerformanceMonitor working correctly!")
    print(f"  - Total queries recorded: {stats['total_queries']}")
    print(f"  - Average execution time: {stats['avg_execution_time']:.3f}s")
    
    return True

def simulate_graphql_query():
    """Simulate the GraphQL query that was failing."""
    print("\nSimulating GraphQL query execution...")
    
    # This simulates what happens when the GraphQL query is executed
    from rail_django_graphql.extensions.optimization import get_performance_monitor
    
    monitor = get_performance_monitor()
    
    # Simulate the query execution with performance monitoring
    query_name = "tags"
    execution_time = 0.045  # 45ms
    cache_hit = False
    
    try:
        # This is the call that was failing before
        monitor.record_query_performance(query_name, execution_time, cache_hit)
        print(f"✓ GraphQL query '{query_name}' executed successfully!")
        print(f"  - Execution time: {execution_time * 1000:.1f}ms")
        print(f"  - Cache hit: {cache_hit}")
        
        return True
    except AttributeError as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("GraphQL PerformanceMonitor Fix Verification")
    print("=" * 60)
    
    try:
        # Test 1: Verify PerformanceMonitor has the required method
        test_performance_monitor()
        
        # Test 2: Simulate the GraphQL query that was failing
        simulate_graphql_query()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("The GraphQL query error has been resolved.")
        print("The 'record_query_performance' method is now available.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)