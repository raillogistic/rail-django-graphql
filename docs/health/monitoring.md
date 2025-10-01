# Monitoring Guide

This guide covers comprehensive monitoring strategies for Django GraphQL Auto applications, including setup, best practices, and integration with popular monitoring tools.

## Overview

Effective monitoring of GraphQL APIs requires tracking multiple layers:
- Application performance and health
- GraphQL-specific metrics (query complexity, execution time)
- Infrastructure metrics (CPU, memory, database)
- Business metrics (user engagement, feature usage)
- Error tracking and alerting

## Monitoring Architecture

### Multi-Layer Monitoring

```
┌─────────────────────────────────────────┐
│              Business Layer             │
│  (User metrics, feature usage, KPIs)   │
├─────────────────────────────────────────┤
│            Application Layer            │
│   (GraphQL metrics, response times)    │
├─────────────────────────────────────────┤
│           Infrastructure Layer          │
│    (CPU, memory, database, network)    │
├─────────────────────────────────────────┤
│              System Layer               │
│      (OS metrics, disk, processes)     │
└─────────────────────────────────────────┘
```

## Setting Up Monitoring

### Basic Monitoring Setup

```python
# settings.py
RAIL_GRAPHQL_MONITORING = {
    'ENABLED': True,
    'COLLECTORS': [
        'performance',
        'health',
        'usage',
        'errors',
        'business',
    ],
    'STORAGE_BACKEND': 'prometheus',
    'ALERT_MANAGER': 'integrated',
}
```

### Monitoring Middleware

```python
# settings.py
MIDDLEWARE = [
    'rail_django_graphql.middleware.MonitoringMiddleware',
    # Other middleware...
]

RAIL_GRAPHQL_MONITORING_MIDDLEWARE = {
    'TRACK_REQUESTS': True,
    'TRACK_RESPONSES': True,
    'TRACK_ERRORS': True,
    'SAMPLE_RATE': 1.0,  # 100% sampling
}
```

## Application Performance Monitoring (APM)

### Django Integration

```python
from rail_django_graphql.monitoring import APMCollector

class GraphQLAPMCollector(APMCollector):
    def collect_metrics(self):
        return {
            'response_time': self.get_response_times(),
            'throughput': self.get_throughput(),
            'error_rate': self.get_error_rate(),
            'apdex_score': self.calculate_apdex(),
        }

# Register APM collector
from rail_django_graphql.monitoring import register_collector
register_collector('apm', GraphQLAPMCollector())
```

### Query Performance Monitoring

```python
from rail_django_graphql.monitoring import QueryMonitor

monitor = QueryMonitor()

# Track query execution
@monitor.track_query
def resolve_users(self, info, **kwargs):
    # Resolver logic
    return User.objects.all()

# Get performance data
performance_data = monitor.get_query_performance('resolve_users')
print(f"Average execution time: {performance_data.avg_time}ms")
```

## Infrastructure Monitoring

### System Metrics Collection

```python
from rail_django_graphql.monitoring import SystemMetricsCollector

system_collector = SystemMetricsCollector()
metrics = system_collector.collect()

print(f"CPU usage: {metrics.cpu_percent}%")
print(f"Memory usage: {metrics.memory_percent}%")
print(f"Disk usage: {metrics.disk_percent}%")
```

### Database Monitoring

```python
from rail_django_graphql.monitoring import DatabaseMonitor

db_monitor = DatabaseMonitor()
db_metrics = db_monitor.collect_metrics()

print(f"Active connections: {db_metrics.active_connections}")
print(f"Query execution time: {db_metrics.avg_query_time}ms")
print(f"Slow queries: {db_metrics.slow_query_count}")
```

## Prometheus Integration

### Metrics Export

```python
from rail_django_graphql.monitoring.prometheus import PrometheusExporter
from prometheus_client import Counter, Histogram, Gauge

# Define custom metrics
GRAPHQL_REQUESTS = Counter(
    'graphql_requests_total',
    'Total GraphQL requests',
    ['schema', 'operation_type']
)

QUERY_DURATION = Histogram(
    'graphql_query_duration_seconds',
    'GraphQL query duration',
    ['schema', 'query_name']
)

ACTIVE_SCHEMAS = Gauge(
    'graphql_active_schemas',
    'Number of active GraphQL schemas'
)

# Export metrics
exporter = PrometheusExporter()
exporter.register_metrics([
    GRAPHQL_REQUESTS,
    QUERY_DURATION,
    ACTIVE_SCHEMAS
])
```

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'django-graphql-auto'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics/'
    scrape_interval: 30s
```

## Grafana Dashboards

### GraphQL Performance Dashboard

```json
{
  "dashboard": {
    "title": "Django GraphQL Auto - Performance",
    "panels": [
      {
        "title": "Query Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(graphql_query_duration_seconds_sum[5m]) / rate(graphql_query_duration_seconds_count[5m])",
            "legendFormat": "Average Response Time"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(graphql_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(graphql_requests_total{status=\"error\"}[5m]) / rate(graphql_requests_total[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ]
      }
    ]
  }
}
```

### System Resources Dashboard

```json
{
  "dashboard": {
    "title": "Django GraphQL Auto - System Resources",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "system_cpu_percent",
            "legendFormat": "CPU %"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "system_memory_percent",
            "legendFormat": "Memory %"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "database_active_connections",
            "legendFormat": "Active Connections"
          }
        ]
      }
    ]
  }
}
```

## Alerting

### Alert Rules

```yaml
# alert_rules.yml
groups:
  - name: graphql_alerts
    rules:
      - alert: HighResponseTime
        expr: graphql_query_duration_seconds > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High GraphQL response time"
          description: "GraphQL queries are taking longer than 1 second"

      - alert: HighErrorRate
        expr: rate(graphql_requests_total{status="error"}[5m]) / rate(graphql_requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High GraphQL error rate"
          description: "GraphQL error rate is above 5%"

      - alert: SchemaDown
        expr: up{job="django-graphql-auto"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "GraphQL service is down"
          description: "GraphQL service is not responding"
```

### Custom Alert Handlers

```python
from rail_django_graphql.monitoring.alerts import BaseAlertHandler

class SlackAlertHandler(BaseAlertHandler):
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
    
    def send_alert(self, alert):
        payload = {
            'text': f"🚨 {alert.title}",
            'attachments': [{
                'color': 'danger' if alert.severity == 'critical' else 'warning',
                'fields': [
                    {'title': 'Metric', 'value': alert.metric, 'short': True},
                    {'title': 'Value', 'value': alert.value, 'short': True},
                    {'title': 'Threshold', 'value': alert.threshold, 'short': True},
                ]
            }]
        }
        requests.post(self.webhook_url, json=payload)

# Register alert handler
from rail_django_graphql.monitoring.alerts import register_alert_handler
register_alert_handler('slack', SlackAlertHandler('your-webhook-url'))
```

## Log Monitoring

### Structured Logging

```python
import logging
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Use structured logging in resolvers
logger = structlog.get_logger()

def resolve_user(self, info, user_id):
    logger.info(
        "user_query_started",
        user_id=user_id,
        query_complexity=info.context.query_complexity,
        schema=info.schema.name
    )
    
    try:
        user = User.objects.get(id=user_id)
        logger.info("user_query_completed", user_id=user_id, execution_time=0.05)
        return user
    except User.DoesNotExist:
        logger.warning("user_not_found", user_id=user_id)
        raise
```

### ELK Stack Integration

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
        },
    },
    'handlers': {
        'elasticsearch': {
            'level': 'INFO',
            'class': 'cmreslogging.handlers.CMRESHandler',
            'hosts': [{'host': 'localhost', 'port': 9200}],
            'es_index_name': 'django-graphql-auto',
            'formatter': 'json',
        },
    },
    'loggers': {
        'rail_django_graphql': {
            'handlers': ['elasticsearch'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Business Metrics Monitoring

### Custom Business Metrics

```python
from rail_django_graphql.monitoring import BusinessMetricsCollector

class ECommerceMetricsCollector(BusinessMetricsCollector):
    def collect_metrics(self):
        return {
            'orders_per_minute': self.count_orders_per_minute(),
            'revenue_per_hour': self.calculate_revenue_per_hour(),
            'user_engagement_score': self.calculate_engagement(),
            'cart_abandonment_rate': self.calculate_abandonment_rate(),
        }

# Register business metrics
register_collector('ecommerce', ECommerceMetricsCollector())
```

### Feature Usage Tracking

```python
from rail_django_graphql.monitoring.decorators import track_feature_usage

@track_feature_usage('user_search')
def resolve_search_users(self, info, query):
    # Track feature usage
    return User.objects.filter(name__icontains=query)

# Get feature usage statistics
from rail_django_graphql.monitoring import get_feature_usage
usage_stats = get_feature_usage('user_search', period='7d')
print(f"Feature used {usage_stats.total_uses} times in the last 7 days")
```

## Real-time Monitoring

### WebSocket Monitoring Stream

```python
from rail_django_graphql.monitoring import MonitoringStreamer

# Set up real-time monitoring
streamer = MonitoringStreamer()
streamer.start_streaming(
    metrics=['performance', 'errors', 'system'],
    interval=5,  # seconds
    clients=['dashboard', 'mobile_app']
)
```

### Live Dashboard

```html
<!-- monitoring_dashboard.html -->
<div id="live-metrics">
    <div class="metric-card">
        <h3>Response Time</h3>
        <span id="response-time">--</span>ms
    </div>
    <div class="metric-card">
        <h3>Requests/sec</h3>
        <span id="request-rate">--</span>
    </div>
    <div class="metric-card">
        <h3>Error Rate</h3>
        <span id="error-rate">--</span>%
    </div>
</div>

<script>
const ws = new WebSocket('ws://localhost:8000/monitoring/stream/');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    document.getElementById('response-time').textContent = data.response_time;
    document.getElementById('request-rate').textContent = data.request_rate;
    document.getElementById('error-rate').textContent = data.error_rate;
};
</script>
```

## Monitoring Best Practices

### 1. Define SLIs and SLOs

```python
# Service Level Indicators (SLIs)
SLI_CONFIG = {
    'availability': {
        'target': 99.9,  # 99.9% uptime
        'measurement': 'uptime_percentage'
    },
    'latency': {
        'target': 200,  # 200ms average response time
        'measurement': 'p95_response_time'
    },
    'error_rate': {
        'target': 0.1,  # 0.1% error rate
        'measurement': 'error_percentage'
    }
}
```

### 2. Implement Circuit Breakers

```python
from rail_django_graphql.monitoring import CircuitBreaker

circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception
)

@circuit_breaker
def external_api_call():
    # Call to external service
    pass
```

### 3. Use Sampling for High Traffic

```python
# settings.py
RAIL_GRAPHQL_MONITORING = {
    'SAMPLING_STRATEGY': 'adaptive',
    'BASE_SAMPLING_RATE': 0.1,  # 10% base sampling
    'HIGH_TRAFFIC_THRESHOLD': 1000,  # requests/minute
    'ERROR_SAMPLING_RATE': 1.0,  # Always sample errors
}
```

### 4. Monitor Query Complexity

```python
from rail_django_graphql.monitoring import ComplexityMonitor

complexity_monitor = ComplexityMonitor(
    max_complexity=1000,
    alert_threshold=800
)

# Track query complexity
@complexity_monitor.track
def resolve_complex_query(self, info, **kwargs):
    # Complex resolver logic
    pass
```

## Troubleshooting Monitoring Issues

### Common Problems

1. **High Monitoring Overhead**
   ```python
   # Reduce sampling rate
   RAIL_GRAPHQL_MONITORING = {
       'SAMPLE_RATE': 0.01,  # 1% sampling
       'ASYNC_COLLECTION': True,
   }
   ```

2. **Missing Metrics**
   ```python
   # Check collector registration
   from rail_django_graphql.monitoring import list_collectors
   print(list_collectors())
   ```

3. **Alert Fatigue**
   ```python
   # Implement alert suppression
   RAIL_GRAPHQL_MONITORING = {
       'ALERT_SUPPRESSION': {
           'ENABLED': True,
           'COOLDOWN_PERIOD': 300,  # 5 minutes
           'MAX_ALERTS_PER_HOUR': 10,
       }
   }
   ```

## Integration Examples

### New Relic Integration

```python
import newrelic.agent

@newrelic.agent.function_trace()
def resolve_user(self, info, user_id):
    newrelic.agent.add_custom_attribute('user_id', user_id)
    newrelic.agent.add_custom_attribute('schema', info.schema.name)
    return User.objects.get(id=user_id)
```

### DataDog Integration

```python
from datadog import DogStatsdClient

statsd = DogStatsdClient(host='localhost', port=8125)

def track_query_execution(query_name, execution_time):
    statsd.histogram('graphql.query.duration', execution_time, tags=[f'query:{query_name}'])
    statsd.increment('graphql.query.count', tags=[f'query:{query_name}'])
```

## See Also

- [Health Checks](health-checks.md)
- [Metrics Documentation](metrics.md)
- [Alerting Configuration](alerting.md)
- [Performance Optimization](../development/performance.md)
- [Troubleshooting Guide](../development/troubleshooting.md)