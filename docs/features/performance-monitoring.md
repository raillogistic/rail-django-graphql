# Performance Monitoring

The `rail_django_graphql` library provides comprehensive performance monitoring capabilities for GraphQL operations, helping you identify bottlenecks, track query performance, and optimize your GraphQL API.

## Overview

The performance monitoring system consists of two main components:

1. **GraphQLPerformanceMiddleware** - Django middleware for request-level monitoring
2. **GraphQLExecutionMiddleware** - GraphQL execution middleware for query-level monitoring

## Key Features

### 🚀 **Real-time Performance Tracking**
- Query execution time monitoring
- Memory usage tracking
- Database query analysis
- Cache hit/miss ratios

### 📊 **Comprehensive Metrics Collection**
- Slow query detection and logging
- Query complexity analysis
- Performance trend analysis
- Resource utilization monitoring

### 🔍 **Advanced Monitoring Capabilities**
- GraphQL query introspection
- Operation type classification (Query/Mutation/Subscription)
- Field-level performance analysis
- Nested query depth tracking

### 🚨 **Alert System**
- Configurable performance thresholds
- Automatic slow query alerts
- Memory usage warnings
- Performance degradation notifications

### 📈 **Performance Analytics**
- Historical performance data
- Query performance benchmarks
- Resource usage trends
- Performance optimization recommendations

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Django Request                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│            GraphQLPerformanceMiddleware                     │
│  • Request/Response timing                                  │
│  • Memory usage tracking                                    │
│  • Database query monitoring                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                GraphQL Execution                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│           GraphQLExecutionMiddleware                        │
│  • Query parsing and analysis                              │
│  • Field-level performance tracking                        │
│  • Query complexity calculation                            │
│  • Operation type detection                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Performance Aggregator                        │
│  • Metrics collection and storage                          │
│  • Alert generation                                        │
│  • Performance analysis                                    │
└─────────────────────────────────────────────────────────────┘
```

## Performance Metrics

### Request-Level Metrics
- **Total Request Time**: Complete request processing duration
- **GraphQL Execution Time**: Time spent executing GraphQL operations
- **Database Query Time**: Time spent on database operations
- **Cache Operations**: Cache hit/miss ratios and timing

### Query-Level Metrics
- **Query Parsing Time**: Time to parse GraphQL query
- **Query Validation Time**: Time to validate query against schema
- **Field Resolution Time**: Time spent resolving individual fields
- **Query Complexity Score**: Calculated complexity based on depth and breadth

### Resource Metrics
- **Memory Usage**: Peak memory consumption during request
- **CPU Usage**: Processor utilization during execution
- **Database Connections**: Active database connection count
- **Cache Memory**: Cache storage utilization

## Integration Points

### Sentry Integration
Automatic error tracking and performance monitoring integration with Sentry for production environments.

### Database Monitoring
Deep integration with Django ORM to track:
- Query count per request
- Slow query identification
- N+1 query detection
- Database connection pooling metrics

### Cache Monitoring
Comprehensive cache performance tracking:
- Redis/Memcached integration
- Cache hit/miss ratios
- Cache invalidation patterns
- Memory usage optimization

## Performance Thresholds

Default performance thresholds can be customized:

```python
# Default thresholds
PERFORMANCE_THRESHOLDS = {
    'slow_query_ms': 1000,      # Queries slower than 1 second
    'high_complexity': 100,      # Query complexity score
    'memory_mb': 100,           # Memory usage in MB
    'db_query_count': 50,       # Database queries per request
}
```

## Benefits

### 🎯 **Proactive Performance Management**
- Identify performance issues before they impact users
- Track performance trends over time
- Optimize resource allocation

### 🔧 **Development Optimization**
- Pinpoint slow GraphQL operations
- Optimize query structures
- Improve field resolver efficiency

### 📊 **Production Monitoring**
- Real-time performance dashboards
- Automated alerting systems
- Performance regression detection

### 💡 **Data-Driven Decisions**
- Performance benchmarking
- Resource planning insights
- Optimization priority identification

## Next Steps

- [Setup and Configuration](../setup/performance-setup.md)
- [API Reference](../api/performance-api.md)
- [Troubleshooting Guide](../troubleshooting/performance-troubleshooting.md)
- [Best Practices](../project/performance-best-practices.md)