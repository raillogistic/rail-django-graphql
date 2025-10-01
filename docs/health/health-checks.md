# Health Checks

Django GraphQL Auto provides comprehensive health check capabilities to monitor the status and performance of your GraphQL schemas and endpoints.

## Overview

The health check system allows you to:
- Monitor schema availability and performance
- Check database connectivity
- Validate GraphQL endpoint responses
- Track system resource usage
- Set up automated health monitoring

## Basic Health Checks

### Schema Health Check

```python
from rail_django_graphql.health import SchemaHealthChecker

# Basic schema health check
checker = SchemaHealthChecker()
health_status = checker.check_schema_health('my_schema')

if health_status.is_healthy:
    print("Schema is healthy")
else:
    print(f"Schema issues: {health_status.errors}")
```

### Endpoint Health Check

```python
from rail_django_graphql.health import EndpointHealthChecker

# Check GraphQL endpoint health
endpoint_checker = EndpointHealthChecker()
result = endpoint_checker.check_endpoint('/graphql/')

print(f"Response time: {result.response_time}ms")
print(f"Status: {result.status}")
```

## Advanced Health Checks

### Database Connectivity

```python
from rail_django_graphql.health import DatabaseHealthChecker

# Check database connectivity for GraphQL operations
db_checker = DatabaseHealthChecker()
db_status = db_checker.check_database_health()

if db_status.is_connected:
    print(f"Database healthy - Query time: {db_status.query_time}ms")
```

### Custom Health Checks

```python
from rail_django_graphql.health import BaseHealthChecker

class CustomHealthChecker(BaseHealthChecker):
    def check_health(self):
        # Custom health check logic
        try:
            # Your custom checks here
            return self.create_healthy_result("Custom check passed")
        except Exception as e:
            return self.create_unhealthy_result(f"Custom check failed: {e}")

# Register custom health checker
from rail_django_graphql.health import register_health_checker
register_health_checker('custom', CustomHealthChecker())
```

## Health Check Configuration

### Django Settings

```python
# settings.py
RAIL_GRAPHQL_HEALTH = {
    'ENABLED': True,
    'CHECK_INTERVAL': 60,  # seconds
    'TIMEOUT': 30,  # seconds
    'CHECKS': [
        'schema',
        'database',
        'endpoint',
        'custom',
    ],
    'ALERT_THRESHOLDS': {
        'response_time': 1000,  # ms
        'error_rate': 0.05,  # 5%
    }
}
```

### Health Check Endpoints

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path('health/', include('rail_django_graphql.health_urls')),
    # Other URLs...
]
```

Available endpoints:
- `/health/` - Overall health status
- `/health/schema/` - Schema-specific health
- `/health/database/` - Database connectivity
- `/health/detailed/` - Detailed health report

## Automated Health Monitoring

### Periodic Health Checks

```python
from rail_django_graphql.health import HealthMonitor

# Set up automated monitoring
monitor = HealthMonitor()
monitor.start_monitoring(interval=60)  # Check every 60 seconds

# Stop monitoring
monitor.stop_monitoring()
```

### Health Check Middleware

```python
# settings.py
MIDDLEWARE = [
    'rail_django_graphql.middleware.HealthCheckMiddleware',
    # Other middleware...
]

# Middleware configuration
RAIL_GRAPHQL_HEALTH_MIDDLEWARE = {
    'ENABLED': True,
    'CHECK_ON_REQUEST': True,
    'LOG_UNHEALTHY': True,
}
```

## Health Check Results

### Result Structure

```python
class HealthCheckResult:
    is_healthy: bool
    status: str  # 'healthy', 'warning', 'critical'
    message: str
    details: dict
    timestamp: datetime
    response_time: float  # milliseconds
    errors: list
```

### Example Response

```json
{
    "is_healthy": true,
    "status": "healthy",
    "message": "All systems operational",
    "details": {
        "schema": {
            "status": "healthy",
            "schemas_count": 3,
            "last_check": "2024-01-15T10:30:00Z"
        },
        "database": {
            "status": "healthy",
            "connection_time": 15,
            "query_time": 8
        },
        "endpoint": {
            "status": "healthy",
            "response_time": 120,
            "success_rate": 0.99
        }
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "response_time": 45.2
}
```

## Integration with Monitoring Systems

### Prometheus Metrics

```python
from rail_django_graphql.health.prometheus import PrometheusHealthExporter

# Export health metrics to Prometheus
exporter = PrometheusHealthExporter()
exporter.export_health_metrics()
```

### Custom Alerting

```python
from rail_django_graphql.health import HealthAlertManager

# Set up custom alerting
alert_manager = HealthAlertManager()
alert_manager.add_alert_handler('email', email_handler)
alert_manager.add_alert_handler('slack', slack_handler)

# Configure alert thresholds
alert_manager.set_threshold('response_time', 1000)  # ms
alert_manager.set_threshold('error_rate', 0.05)  # 5%
```

## Troubleshooting Health Issues

### Common Issues

1. **Schema Not Found**
   ```python
   # Check if schema is properly registered
   from rail_django_graphql.registry import schema_registry
   print(schema_registry.list_schemas())
   ```

2. **Database Connection Issues**
   ```python
   # Test database connectivity
   from django.db import connection
   with connection.cursor() as cursor:
       cursor.execute("SELECT 1")
   ```

3. **High Response Times**
   ```python
   # Enable query profiling
   RAIL_GRAPHQL_HEALTH = {
       'PROFILING_ENABLED': True,
       'SLOW_QUERY_THRESHOLD': 500,  # ms
   }
   ```

### Debug Mode

```python
# Enable debug mode for detailed health information
RAIL_GRAPHQL_HEALTH = {
    'DEBUG': True,
    'VERBOSE_LOGGING': True,
}
```

## Best Practices

1. **Regular Monitoring**: Set up automated health checks with appropriate intervals
2. **Threshold Configuration**: Configure realistic thresholds based on your application requirements
3. **Alert Integration**: Integrate with your existing monitoring and alerting systems
4. **Custom Checks**: Implement custom health checks for application-specific requirements
5. **Performance Impact**: Monitor the performance impact of health checks themselves

## See Also

- [Monitoring Guide](monitoring.md)
- [Metrics Documentation](metrics.md)
- [Alerting Configuration](alerting.md)
- [Performance Optimization](../development/performance.md)