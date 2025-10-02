"""
Middleware package for Django GraphQL Auto.

This package contains middleware components for:
- Performance monitoring
- Query optimization
- Caching integration
- Security enhancements
"""

from .performance import (
    GraphQLPerformanceMiddleware,
    GraphQLPerformanceView,
    get_performance_aggregator,
    setup_performance_monitoring,
    monitor_performance
)

__all__ = [
    'GraphQLPerformanceMiddleware',
    'GraphQLPerformanceView', 
    'get_performance_aggregator',
    'setup_performance_monitoring',
    'monitor_performance'
]