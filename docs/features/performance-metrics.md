# Performance Metrics Guide

This guide provides comprehensive information about all performance metrics collected by the `rail_django_graphql` performance monitoring system.

## Metric Categories

### 🚀 Request-Level Metrics

Metrics collected for each HTTP request containing GraphQL operations.

#### Response Time Metrics

| Metric | Description | Unit | Threshold |
|--------|-------------|------|-----------|
| `total_request_time` | Complete request processing duration | milliseconds | 1000ms (slow) |
| `graphql_execution_time` | Time spent executing GraphQL operations | milliseconds | 800ms (slow) |
| `middleware_overhead` | Time spent in middleware processing | milliseconds | 50ms (high) |
| `response_serialization_time` | Time to serialize response data | milliseconds | 100ms (slow) |

#### Database Metrics

| Metric | Description | Unit | Threshold |
|--------|-------------|------|-----------|
| `database_query_time` | Total time spent on database operations | milliseconds | 500ms (slow) |
| `database_query_count` | Number of database queries executed | count | 50 (high) |
| `database_connection_time` | Time to acquire database connections | milliseconds | 100ms (slow) |
| `slow_database_queries` | Number of individual slow DB queries | count | 5 (high) |

#### Cache Metrics

| Metric | Description | Unit | Threshold |
|--------|-------------|------|-----------|
| `cache_operation_time` | Time spent on cache operations | milliseconds | 50ms (slow) |
| `cache_hits` | Number of successful cache retrievals | count | - |
| `cache_misses` | Number of failed cache retrievals | count | - |
| `cache_hit_rate` | Percentage of successful cache operations | percentage | 80% (low) |
| `cache_memory_usage` | Memory used by cache operations | MB | 50MB (high) |

### 📊 Query-Level Metrics

Metrics specific to individual GraphQL queries and operations.

#### Query Execution Metrics

| Metric | Description | Unit | Threshold |
|--------|-------------|------|-----------|
| `query_parsing_time` | Time to parse GraphQL query | milliseconds | 10ms (slow) |
| `query_validation_time` | Time to validate query against schema | milliseconds | 20ms (slow) |
| `field_resolution_time` | Time spent resolving individual fields | milliseconds | 500ms (slow) |
| `query_depth` | Maximum nesting depth of the query | levels | 10 (deep) |
| `query_breadth` | Number of fields at each level | count | 50 (wide) |

#### Query Complexity Metrics

| Metric | Description | Unit | Threshold |
|--------|-------------|------|-----------|
| `complexity_score` | Calculated query complexity | points | 100 (high) |
| `complexity_depth_weight` | Contribution of depth to complexity | points | - |
| `complexity_breadth_weight` | Contribution of breadth to complexity | points | - |
| `estimated_cost` | Estimated resource cost of query | cost units | 1000 (expensive) |

#### Operation Type Metrics

| Metric | Description | Unit | Threshold |
|--------|-------------|------|-----------|
| `query_operations` | Number of Query operations | count | - |
| `mutation_operations` | Number of Mutation operations | count | - |
| `subscription_operations` | Number of Subscription operations | count | - |
| `introspection_queries` | Number of schema introspection queries | count | 10/min (high) |

### 💾 Resource Metrics

System resource utilization during GraphQL operations.

#### Memory Metrics

| Metric | Description | Unit | Threshold |
|--------|-------------|------|-----------|
| `memory_usage` | Current memory consumption | MB | 100MB (high) |
| `peak_memory_usage` | Maximum memory used during request | MB | 150MB (very high) |
| `memory_growth` | Memory increase during request | MB | 50MB (high growth) |
| `garbage_collection_time` | Time spent in garbage collection | milliseconds | 100ms (high) |

#### CPU Metrics

| Metric | Description | Unit | Threshold |
|--------|-------------|------|-----------|
| `cpu_usage` | Processor utilization percentage | percentage | 80% (high) |
| `cpu_time` | Total CPU time consumed | milliseconds | 1000ms (high) |
| `thread_count` | Number of active threads | count | 50 (high) |

#### Connection Metrics

| Metric | Description | Unit | Threshold |
|--------|-------------|------|-----------|
| `active_connections` | Current active database connections | count | 20 (high) |
| `connection_pool_usage` | Percentage of connection pool used | percentage | 80% (high) |
| `connection_wait_time` | Time waiting for available connections | milliseconds | 100ms (slow) |

## Metric Collection

### Automatic Collection

Metrics are automatically collected when performance monitoring is enabled:

```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'PERFORMANCE_MONITORING': True,
    'COLLECT_REQUEST_METRICS': True,
    'COLLECT_QUERY_METRICS': True,
    'COLLECT_RESOURCE_METRICS': True,
}
```

### Custom Metric Collection

Add custom metrics to your GraphQL resolvers:

```python
from rail_django_graphql.middleware.performance import get_performance_monitor

def resolve_complex_field(self, info, **kwargs):
    monitor = get_performance_monitor()
    
    # Start custom metric tracking
    with monitor.track_custom_metric('complex_calculation'):
        result = perform_complex_calculation()
    
    # Record custom counter
    monitor.increment_counter('complex_field_requests')
    
    # Record custom gauge
    monitor.record_gauge('calculation_result_size', len(result))
    
    return result
```

## Metric Aggregation

### Time-Based Aggregation

Metrics are aggregated over different time periods:

- **Real-time**: Current request metrics
- **1 minute**: Rolling average for immediate monitoring
- **5 minutes**: Short-term trend analysis
- **1 hour**: Medium-term performance tracking
- **24 hours**: Daily performance overview
- **7 days**: Weekly performance trends

### Statistical Aggregation

For each metric, the following statistics are calculated:

- **Average (Mean)**: Typical performance
- **Median (P50)**: Middle value performance
- **95th Percentile (P95)**: High-end performance
- **99th Percentile (P99)**: Extreme performance
- **Maximum**: Worst-case performance
- **Minimum**: Best-case performance
- **Standard Deviation**: Performance consistency

### Example Aggregated Data

```json
{
  "query_execution_time": {
    "current": 245,
    "1min_avg": 198,
    "5min_avg": 210,
    "1hour_avg": 185,
    "24hour_avg": 175,
    "percentiles": {
      "p50": 150,
      "p95": 450,
      "p99": 800
    },
    "min": 45,
    "max": 2340,
    "std_dev": 125.6
  }
}
```

## Performance Thresholds

### Default Thresholds

```python
DEFAULT_THRESHOLDS = {
    # Request-level thresholds
    'slow_request_ms': 1000,
    'very_slow_request_ms': 5000,
    
    # Query-level thresholds
    'slow_query_ms': 800,
    'very_slow_query_ms': 3000,
    'high_complexity': 100,
    'very_high_complexity': 200,
    
    # Database thresholds
    'slow_db_query_ms': 100,
    'high_db_query_count': 50,
    'very_high_db_query_count': 100,
    
    # Memory thresholds
    'high_memory_mb': 100,
    'very_high_memory_mb': 200,
    
    # Cache thresholds
    'low_cache_hit_rate': 0.8,
    'very_low_cache_hit_rate': 0.6,
}
```

### Custom Thresholds

Configure custom thresholds for your application:

```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'PERFORMANCE_THRESHOLDS': {
        'slow_query_ms': 500,        # Stricter threshold
        'high_complexity': 50,       # Lower complexity limit
        'high_memory_mb': 75,        # Lower memory threshold
        'low_cache_hit_rate': 0.9,   # Higher cache expectation
    }
}
```

## Alerting System

### Alert Types

| Alert Type | Trigger Condition | Severity | Action |
|------------|-------------------|----------|--------|
| `slow_query` | Query time > threshold | Warning | Log and monitor |
| `very_slow_query` | Query time > 2x threshold | Error | Alert and investigate |
| `high_complexity` | Complexity > threshold | Warning | Review query |
| `very_high_complexity` | Complexity > 2x threshold | Error | Block or limit |
| `memory_warning` | Memory > threshold | Warning | Monitor usage |
| `memory_critical` | Memory > 2x threshold | Critical | Scale or optimize |
| `db_performance` | DB time > threshold | Warning | Optimize queries |
| `cache_miss_rate` | Hit rate < threshold | Warning | Review caching |

### Alert Configuration

```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'PERFORMANCE_ALERTS': {
        'ENABLE_ALERTS': True,
        'ALERT_CHANNELS': ['log', 'email', 'sentry'],
        'ALERT_COOLDOWN_MINUTES': 5,
        'BATCH_ALERTS': True,
        'MAX_ALERTS_PER_MINUTE': 10,
    }
}
```

## Monitoring Dashboards

### Real-time Metrics

Display current performance metrics:

```python
# Get real-time metrics
from rail_django_graphql.middleware.performance import get_performance_aggregator

aggregator = get_performance_aggregator()
current_metrics = aggregator.get_current_metrics()

print(f"Current avg response time: {current_metrics['avg_response_time']}ms")
print(f"Active requests: {current_metrics['active_requests']}")
print(f"Memory usage: {current_metrics['memory_usage']}MB")
```

### Historical Trends

Analyze performance trends over time:

```python
# Get historical data
historical_data = aggregator.get_historical_metrics(
    start_time=datetime.now() - timedelta(hours=24),
    end_time=datetime.now(),
    interval='1hour'
)

# Plot performance trends
import matplotlib.pyplot as plt

times = [point['timestamp'] for point in historical_data]
response_times = [point['avg_response_time'] for point in historical_data]

plt.plot(times, response_times)
plt.title('Response Time Trend (24 hours)')
plt.xlabel('Time')
plt.ylabel('Response Time (ms)')
plt.show()
```

## Integration Examples

### Grafana Dashboard

Create Grafana dashboard with performance metrics:

```json
{
  "dashboard": {
    "title": "GraphQL Performance",
    "panels": [
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "avg(graphql_response_time_ms)",
            "legendFormat": "Average Response Time"
          }
        ]
      },
      {
        "title": "Query Complexity",
        "type": "heatmap",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, graphql_complexity_score)",
            "legendFormat": "95th Percentile Complexity"
          }
        ]
      }
    ]
  }
}
```

### Prometheus Metrics

Export metrics to Prometheus:

```python
# Custom Prometheus exporter
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
graphql_requests_total = Counter('graphql_requests_total', 'Total GraphQL requests')
graphql_duration_seconds = Histogram('graphql_duration_seconds', 'GraphQL request duration')
graphql_complexity_score = Gauge('graphql_complexity_score', 'Current query complexity')

# In your middleware
def process_request(self, request):
    graphql_requests_total.inc()
    
    start_time = time.time()
    response = self.get_response(request)
    duration = time.time() - start_time
    
    graphql_duration_seconds.observe(duration)
    
    return response
```

## Best Practices

### 1. Metric Selection

- **Focus on business-critical metrics**: Don't collect everything
- **Balance detail vs. performance**: More metrics = more overhead
- **Use sampling for high-volume metrics**: Reduce collection overhead

### 2. Threshold Configuration

- **Start with defaults**: Adjust based on your application
- **Monitor false positives**: Tune thresholds to reduce noise
- **Consider user experience**: Set thresholds based on user expectations

### 3. Data Retention

- **Real-time data**: Keep for 1 hour
- **Aggregated data**: Keep for 30 days
- **Historical trends**: Keep for 1 year
- **Archive old data**: Move to cold storage

### 4. Performance Impact

- **Async collection**: Don't block request processing
- **Batch operations**: Reduce database writes
- **Sampling**: Collect subset of requests for detailed analysis

## Next Steps

- [Performance Monitoring Setup](../setup/performance-setup.md)
- [Performance API Reference](../api/performance-api.md)
- [Troubleshooting Guide](../troubleshooting/performance-troubleshooting.md)
- [Best Practices](../project/performance-best-practices.md)