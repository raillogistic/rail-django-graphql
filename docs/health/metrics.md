# Metrics and Performance Monitoring

Django GraphQL Auto provides comprehensive metrics collection and performance monitoring capabilities to help you understand and optimize your GraphQL API performance.

## Overview

The metrics system tracks:
- Query execution times
- Schema usage statistics
- Error rates and types
- Resource utilization
- Cache hit/miss ratios
- Database query performance

## Basic Metrics Collection

### Enabling Metrics

```python
# settings.py
RAIL_GRAPHQL_METRICS = {
    'ENABLED': True,
    'COLLECTION_INTERVAL': 60,  # seconds
    'RETENTION_DAYS': 30,
    'STORAGE_BACKEND': 'database',  # 'database', 'redis', 'memory'
}
```

### Query Performance Metrics

```python
from rail_django_graphql.metrics import QueryMetrics

# Get query performance metrics
metrics = QueryMetrics()
performance_data = metrics.get_query_performance(
    schema_name='my_schema',
    time_range='1h'
)

print(f"Average response time: {performance_data.avg_response_time}ms")
print(f"Total queries: {performance_data.total_queries}")
print(f"Error rate: {performance_data.error_rate}%")
```

## Metrics Types

### Performance Metrics

```python
from rail_django_graphql.metrics import PerformanceCollector

collector = PerformanceCollector()

# Collect performance metrics
metrics = collector.collect_metrics()
print(f"Response times: {metrics.response_times}")
print(f"Query complexity: {metrics.query_complexity}")
print(f"Database queries: {metrics.db_query_count}")
```

### Usage Metrics

```python
from rail_django_graphql.metrics import UsageMetrics

usage = UsageMetrics()
stats = usage.get_usage_statistics(period='24h')

print(f"Most used queries: {stats.top_queries}")
print(f"Schema usage: {stats.schema_usage}")
print(f"Field access patterns: {stats.field_usage}")
```

### Error Metrics

```python
from rail_django_graphql.metrics import ErrorMetrics

error_metrics = ErrorMetrics()
error_stats = error_metrics.get_error_statistics()

print(f"Error rate: {error_stats.error_rate}%")
print(f"Common errors: {error_stats.common_errors}")
print(f"Error trends: {error_stats.trends}")
```

## Custom Metrics

### Creating Custom Metrics

```python
from rail_django_graphql.metrics import BaseMetric, MetricType

class CustomBusinessMetric(BaseMetric):
    name = "business_operations"
    metric_type = MetricType.COUNTER
    
    def collect(self):
        # Custom metric collection logic
        return {
            'orders_processed': self.count_orders(),
            'revenue_generated': self.calculate_revenue(),
            'user_interactions': self.count_interactions()
        }

# Register custom metric
from rail_django_graphql.metrics import register_metric
register_metric(CustomBusinessMetric())
```

### Metric Decorators

```python
from rail_django_graphql.metrics.decorators import track_performance, count_calls

@track_performance
@count_calls
def my_resolver(self, info, **kwargs):
    # Your resolver logic
    return result
```

## Metrics Storage Backends

### Database Backend

```python
# settings.py
RAIL_GRAPHQL_METRICS = {
    'STORAGE_BACKEND': 'database',
    'DATABASE_CONFIG': {
        'TABLE_PREFIX': 'graphql_metrics_',
        'BATCH_SIZE': 1000,
        'COMPRESSION': True,
    }
}
```

### Redis Backend

```python
# settings.py
RAIL_GRAPHQL_METRICS = {
    'STORAGE_BACKEND': 'redis',
    'REDIS_CONFIG': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 1,
        'KEY_PREFIX': 'graphql:metrics:',
        'TTL': 86400,  # 24 hours
    }
}
```

### Memory Backend (Development)

```python
# settings.py
RAIL_GRAPHQL_METRICS = {
    'STORAGE_BACKEND': 'memory',
    'MEMORY_CONFIG': {
        'MAX_ENTRIES': 10000,
        'CLEANUP_INTERVAL': 300,  # seconds
    }
}
```

## Metrics API

### REST API Endpoints

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path('api/metrics/', include('rail_django_graphql.metrics.urls')),
    # Other URLs...
]
```

Available endpoints:
- `GET /api/metrics/performance/` - Performance metrics
- `GET /api/metrics/usage/` - Usage statistics
- `GET /api/metrics/errors/` - Error metrics
- `GET /api/metrics/schemas/{schema_name}/` - Schema-specific metrics

### GraphQL Metrics Query

```graphql
query GetMetrics($timeRange: String!, $schemaName: String) {
  metrics(timeRange: $timeRange, schemaName: $schemaName) {
    performance {
      averageResponseTime
      totalQueries
      errorRate
    }
    usage {
      topQueries
      fieldUsage
      schemaUsage
    }
    errors {
      errorTypes
      errorTrends
    }
  }
}
```

## Real-time Metrics

### WebSocket Metrics Stream

```python
from rail_django_graphql.metrics import MetricsStreamer

# Set up real-time metrics streaming
streamer = MetricsStreamer()
streamer.start_streaming(
    metrics=['performance', 'usage', 'errors'],
    interval=5  # seconds
)
```

### Server-Sent Events

```python
# views.py
from rail_django_graphql.metrics.views import MetricsStreamView

class RealtimeMetricsView(MetricsStreamView):
    metrics_types = ['performance', 'usage']
    update_interval = 10  # seconds
```

## Metrics Visualization

### Built-in Dashboard

```python
# urls.py
urlpatterns = [
    path('metrics/dashboard/', include('rail_django_graphql.metrics.dashboard.urls')),
]
```

### Custom Dashboards

```python
from rail_django_graphql.metrics import MetricsDashboard

dashboard = MetricsDashboard()
dashboard.add_chart('response_time', chart_type='line')
dashboard.add_chart('query_volume', chart_type='bar')
dashboard.add_chart('error_rate', chart_type='gauge')

# Render dashboard
dashboard_html = dashboard.render()
```

## Integration with Monitoring Systems

### Prometheus Integration

```python
from rail_django_graphql.metrics.exporters import PrometheusExporter

# Export metrics to Prometheus
exporter = PrometheusExporter()
exporter.export_metrics()

# Custom Prometheus metrics
from prometheus_client import Counter, Histogram

GRAPHQL_QUERIES = Counter('graphql_queries_total', 'Total GraphQL queries')
QUERY_DURATION = Histogram('graphql_query_duration_seconds', 'Query duration')
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Django GraphQL Auto Metrics",
    "panels": [
      {
        "title": "Query Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "graphql_query_duration_seconds",
            "legendFormat": "Response Time"
          }
        ]
      }
    ]
  }
}
```

### DataDog Integration

```python
from rail_django_graphql.metrics.exporters import DataDogExporter

# Export metrics to DataDog
datadog_exporter = DataDogExporter(
    api_key='your-api-key',
    app_key='your-app-key'
)
datadog_exporter.export_metrics()
```

## Performance Analysis

### Query Analysis

```python
from rail_django_graphql.metrics import QueryAnalyzer

analyzer = QueryAnalyzer()
analysis = analyzer.analyze_query_performance(
    query_hash='abc123',
    time_range='7d'
)

print(f"Average execution time: {analysis.avg_time}ms")
print(f"Slowest execution: {analysis.max_time}ms")
print(f"Performance trend: {analysis.trend}")
```

### Schema Performance

```python
from rail_django_graphql.metrics import SchemaAnalyzer

schema_analyzer = SchemaAnalyzer()
schema_performance = schema_analyzer.analyze_schema('my_schema')

print(f"Schema efficiency: {schema_performance.efficiency_score}")
print(f"Bottleneck fields: {schema_performance.bottlenecks}")
print(f"Optimization suggestions: {schema_performance.suggestions}")
```

## Alerting Based on Metrics

### Threshold-based Alerts

```python
from rail_django_graphql.metrics.alerts import MetricAlert

# Set up performance alerts
performance_alert = MetricAlert(
    metric='response_time',
    threshold=1000,  # ms
    condition='greater_than',
    action='send_email'
)

# Error rate alerts
error_alert = MetricAlert(
    metric='error_rate',
    threshold=0.05,  # 5%
    condition='greater_than',
    action='send_slack_notification'
)
```

### Custom Alert Handlers

```python
from rail_django_graphql.metrics.alerts import BaseAlertHandler

class CustomAlertHandler(BaseAlertHandler):
    def handle_alert(self, metric_name, value, threshold):
        # Custom alert handling logic
        self.send_custom_notification(
            f"Metric {metric_name} exceeded threshold: {value} > {threshold}"
        )

# Register custom handler
from rail_django_graphql.metrics.alerts import register_alert_handler
register_alert_handler('custom', CustomAlertHandler())
```

## Metrics Configuration

### Advanced Configuration

```python
# settings.py
RAIL_GRAPHQL_METRICS = {
    'ENABLED': True,
    'COLLECTION_INTERVAL': 30,
    'RETENTION_DAYS': 90,
    'STORAGE_BACKEND': 'redis',
    
    # Performance metrics
    'TRACK_QUERY_PERFORMANCE': True,
    'TRACK_RESOLVER_PERFORMANCE': True,
    'TRACK_DATABASE_QUERIES': True,
    
    # Usage metrics
    'TRACK_FIELD_USAGE': True,
    'TRACK_SCHEMA_USAGE': True,
    'TRACK_USER_PATTERNS': True,
    
    # Error metrics
    'TRACK_ERRORS': True,
    'TRACK_VALIDATION_ERRORS': True,
    'TRACK_EXECUTION_ERRORS': True,
    
    # Sampling
    'SAMPLING_RATE': 1.0,  # 100% sampling
    'SLOW_QUERY_THRESHOLD': 500,  # ms
    
    # Aggregation
    'AGGREGATION_INTERVALS': ['1m', '5m', '1h', '1d'],
    'PERCENTILES': [50, 90, 95, 99],
    
    # Export
    'EXPORT_ENABLED': True,
    'EXPORT_FORMATS': ['prometheus', 'json', 'csv'],
    'EXPORT_INTERVAL': 300,  # seconds
}
```

## Best Practices

1. **Selective Tracking**: Only track metrics that provide actionable insights
2. **Sampling**: Use sampling for high-traffic applications to reduce overhead
3. **Retention**: Set appropriate retention periods based on your needs
4. **Aggregation**: Use pre-aggregated metrics for better query performance
5. **Alerting**: Set up meaningful alerts with appropriate thresholds
6. **Privacy**: Be mindful of sensitive data in metrics collection

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```python
   # Reduce sampling rate
   RAIL_GRAPHQL_METRICS = {
       'SAMPLING_RATE': 0.1,  # 10% sampling
   }
   ```

2. **Storage Performance**
   ```python
   # Use batch processing
   RAIL_GRAPHQL_METRICS = {
       'BATCH_SIZE': 1000,
       'BATCH_TIMEOUT': 30,
   }
   ```

3. **Missing Metrics**
   ```python
   # Check metric registration
   from rail_django_graphql.metrics import list_registered_metrics
   print(list_registered_metrics())
   ```

## See Also

- [Health Checks](health-checks.md)
- [Monitoring Guide](monitoring.md)
- [Performance Optimization](../development/performance.md)
- [Alerting Configuration](alerting.md)