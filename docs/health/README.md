# Health Checks & Diagnostics System

## 🏥 Overview

The Health Checks & Diagnostics system provides comprehensive monitoring and diagnostics capabilities for the Django GraphQL Auto-Generation system. It includes real-time health monitoring, performance metrics collection, interactive dashboards, and automated alerting.

## 🚀 Features

### Core Health Monitoring

- **Schema Health Checks**: Validates GraphQL schema integrity and build status
- **Database Monitoring**: Tracks database connection health and response times
- **Cache System Checks**: Monitors Redis/cache performance and availability
- **System Metrics**: CPU, memory, disk usage, and uptime tracking
- **Performance Analytics**: Request timing, query optimization, and bottleneck detection

### Interactive Dashboard

- **Real-time Metrics**: Live updating charts and graphs
- **Component Status**: Visual health indicators for all system components
- **Historical Trends**: Performance data over time with trend analysis
- **Alert Management**: Centralized alert viewing and management
- **Auto-refresh**: Configurable automatic data refresh intervals

### API Endpoints

- **REST API**: JSON endpoints for health data integration
- **GraphQL API**: Native GraphQL queries for health information
- **Simple Health Check**: Load balancer-friendly health endpoints
- **Detailed Metrics**: Comprehensive system metrics for monitoring tools

### Monitoring & Alerting

- **Continuous Monitoring**: Background health monitoring with configurable intervals
- **Email Alerts**: Automated notifications for system issues
- **Recovery Suggestions**: Intelligent recommendations for resolving issues
- **Historical Tracking**: Long-term health data storage and analysis

## 📁 System Architecture

```
rail_django_graphql/
├── extensions/
│   └── health.py                    # Core health checking logic
├── management/commands/
│   └── health_monitor.py           # Continuous monitoring command
├── templates/
│   └── health_dashboard.html       # Interactive dashboard UI
├── views/
│   └── health_views.py            # Django views for health endpoints
├── urls/
│   └── health_urls.py             # URL routing for health system
└── tests/
    └── test_health_system.py      # Comprehensive test suite
```

## 🔧 Installation & Setup

### 1. Add to Django Settings

```python
# settings.py
INSTALLED_APPS = [
    # ... your apps
    'rail_django_graphql',
]

# Health monitoring configuration
HEALTH_CHECK_SETTINGS = {
    'CACHE_TIMEOUT': 300,  # 5 minutes
    'ALERT_EMAIL_RECIPIENTS': ['admin@example.com'],
    'MONITORING_INTERVAL': 60,  # 1 minute
    'PERFORMANCE_THRESHOLD_MS': 1000,
    'MEMORY_THRESHOLD_PERCENT': 80,
    'CPU_THRESHOLD_PERCENT': 75,
}

# Email configuration for alerts
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your-smtp-server.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
```

### 2. Include Health URLs

```python
# urls.py
from django.urls import path, include
from rail_django_graphql.urls.health_urls import get_health_urlpatterns

urlpatterns = [
    # ... your URLs
    path('', include(get_health_urlpatterns())),
]
```

### 3. Run Migrations (if needed)

```bash
python manage.py migrate
```

## 🌐 Available Endpoints

### Dashboard & UI

- **`/health/`** - Interactive health dashboard
- **`/health/dashboard/`** - Alternative dashboard URL

### API Endpoints

- **`/health/api/`** - Complete health data (JSON/GraphQL)
- **`/health/check/`** - Simple health check (for load balancers)
- **`/health/metrics/`** - System metrics only
- **`/health/components/`** - Component status details
- **`/health/history/`** - Historical health data

### GraphQL Integration

```graphql
query {
  healthStatus {
    overallStatus
    healthyComponents
    degradedComponents
    unhealthyComponents
    recommendations
    timestamp
  }

  systemMetrics {
    cpuUsagePercent
    memoryUsagePercent
    memoryUsedMb
    memoryAvailableMb
    diskUsagePercent
    activeConnections
    cacheHitRate
    uptimeSeconds
  }
}
```

## 🖥️ Dashboard Features

### Real-time Monitoring

- **System Overview**: CPU, memory, disk usage with live updates
- **Component Health**: Visual status indicators for all components
- **Performance Charts**: Interactive charts showing trends over time
- **Alert Center**: Recent alerts and recommendations

### Interactive Elements

- **Auto-refresh Toggle**: Enable/disable automatic data updates
- **Refresh Controls**: Manual refresh and interval configuration
- **Historical Views**: View performance data over different time periods
- **Export Options**: Download health reports and metrics

### Visual Indicators

- **🟢 Healthy**: All systems operating normally
- **🟡 Degraded**: Some performance issues detected
- **🔴 Unhealthy**: Critical issues requiring attention

## 🔍 Health Check Components

### Schema Health

```python
# Validates GraphQL schema integrity
{
    "component": "GraphQL Schema",
    "status": "healthy",
    "message": "Schema built successfully",
    "response_time_ms": 45.2,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Database Health

```python
# Tests database connectivity and performance
{
    "component": "Database",
    "status": "healthy",
    "message": "Connection successful",
    "response_time_ms": 12.8,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Cache Health

```python
# Monitors cache system performance
{
    "component": "Cache",
    "status": "healthy",
    "message": "Operations successful",
    "response_time_ms": 3.1,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

## 📊 System Metrics

### Performance Metrics

- **CPU Usage**: Current processor utilization percentage
- **Memory Usage**: RAM consumption and availability
- **Disk Usage**: Storage utilization across mounted drives
- **Network**: Active database connections and throughput
- **Cache Performance**: Hit rates and response times

### Application Metrics

- **GraphQL Performance**: Query execution times and complexity
- **Database Queries**: Query count, duration, and optimization
- **Error Rates**: Exception frequency and error patterns
- **Uptime**: System availability and restart frequency

## 🚨 Monitoring & Alerts

### Continuous Monitoring

Start the health monitoring daemon:

```bash
# Run continuous monitoring
python manage.py health_monitor

# Run with custom interval (in seconds)
python manage.py health_monitor --interval 30

# Run with email alerts enabled
python manage.py health_monitor --email-alerts

# Run in verbose mode
python manage.py health_monitor --verbose
```

### Alert Types

- **Critical**: System failures requiring immediate attention
- **Warning**: Performance degradation or resource constraints
- **Info**: General system information and recommendations

### Email Notifications

Automated email alerts include:

- **Issue Description**: Clear explanation of the problem
- **Affected Components**: Which parts of the system are impacted
- **Severity Level**: Critical, warning, or informational
- **Recovery Suggestions**: Recommended actions to resolve issues
- **System Context**: Current metrics and historical trends

## 🧪 Testing

### Run Health System Tests

```bash
# Run all health system tests
python manage.py test rail_django_graphql.tests.test_health_system

# Run specific test classes
python manage.py test rail_django_graphql.tests.test_health_system.HealthCheckerTestCase
python manage.py test rail_django_graphql.tests.test_health_system.HealthViewsTestCase

# Run with coverage
coverage run --source='.' manage.py test rail_django_graphql.tests.test_health_system
coverage report
```

### Test Coverage

The health system includes comprehensive tests covering:

- ✅ Health checker functionality
- ✅ All API endpoints
- ✅ Dashboard rendering
- ✅ Error handling scenarios
- ✅ Performance under load
- ✅ Integration with GraphQL
- ✅ Monitoring command functionality

## 🔧 Configuration Options

### Health Check Settings

```python
HEALTH_CHECK_SETTINGS = {
    # Cache settings
    'CACHE_TIMEOUT': 300,  # Health data cache duration (seconds)
    'CACHE_KEY_PREFIX': 'health_check',  # Cache key prefix

    # Monitoring settings
    'MONITORING_INTERVAL': 60,  # Monitoring check interval (seconds)
    'HISTORY_RETENTION_DAYS': 30,  # How long to keep historical data

    # Performance thresholds
    'PERFORMANCE_THRESHOLD_MS': 1000,  # Max acceptable response time
    'MEMORY_THRESHOLD_PERCENT': 80,    # Memory usage alert threshold
    'CPU_THRESHOLD_PERCENT': 75,       # CPU usage alert threshold
    'DISK_THRESHOLD_PERCENT': 85,      # Disk usage alert threshold

    # Alert settings
    'ALERT_EMAIL_RECIPIENTS': [
        'admin@example.com',
        'devops@example.com'
    ],
    'ALERT_EMAIL_SUBJECT_PREFIX': '[Health Alert]',
    'ALERT_COOLDOWN_MINUTES': 15,  # Minimum time between duplicate alerts

    # Dashboard settings
    'DASHBOARD_REFRESH_INTERVAL': 30,  # Auto-refresh interval (seconds)
    'DASHBOARD_HISTORY_POINTS': 20,    # Number of historical points to show

    # Component-specific settings
    'SCHEMA_BUILD_TIMEOUT': 30,        # Schema build timeout (seconds)
    'DATABASE_QUERY_TIMEOUT': 10,      # Database health check timeout
    'CACHE_OPERATION_TIMEOUT': 5,      # Cache operation timeout
}
```

### Environment Variables

```bash
# Override settings via environment variables
export HEALTH_MONITORING_INTERVAL=30
export HEALTH_ALERT_EMAIL="admin@example.com,ops@example.com"
export HEALTH_PERFORMANCE_THRESHOLD=500
export HEALTH_DASHBOARD_REFRESH=15
```

## 🚀 Production Deployment

### Load Balancer Integration

Use the simple health check endpoint for load balancer health checks:

```bash
# Health check endpoint returns:
# - 200 OK: System healthy
# - 503 Service Unavailable: System unhealthy

curl http://your-app.com/health/check/
```

### Monitoring Integration

Integrate with monitoring tools like Prometheus, Grafana, or New Relic:

```python
# Custom metrics export
from rail_django_graphql.extensions.health import HealthChecker

def export_metrics():
    checker = HealthChecker()
    metrics = checker.get_system_metrics()

    # Export to your monitoring system
    prometheus_client.gauge('cpu_usage', metrics['cpu_usage_percent'])
    prometheus_client.gauge('memory_usage', metrics['memory_usage_percent'])
    # ... etc
```

### Docker Health Checks

```dockerfile
# Dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health/check/ || exit 1
```

## 🔍 Troubleshooting

### Common Issues

#### Schema Build Failures

```python
# Check schema health manually
from rail_django_graphql.extensions.health import HealthChecker
checker = HealthChecker()
result = checker.check_schema_health()
print(result)
```

#### Database Connection Issues

```python
# Test database connectivity
from django.db import connection
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("Database connection: OK")
except Exception as e:
    print(f"Database error: {e}")
```

#### Cache Problems

```python
# Test cache operations
from django.core.cache import cache
try:
    cache.set('test_key', 'test_value', 60)
    value = cache.get('test_key')
    print(f"Cache test: {'OK' if value == 'test_value' else 'FAILED'}")
except Exception as e:
    print(f"Cache error: {e}")
```

### Debug Mode

Enable debug mode for detailed health information:

```python
# settings.py
DEBUG = True
HEALTH_CHECK_SETTINGS = {
    'DEBUG_MODE': True,  # Enable detailed error messages
    'VERBOSE_LOGGING': True,  # Enable verbose logging
}
```

## 📈 Performance Optimization

### Caching Strategy

- Health check results are cached to reduce system load
- Configurable cache timeouts for different check types
- Smart cache invalidation on system changes

### Monitoring Efficiency

- Lightweight health checks with minimal system impact
- Asynchronous monitoring to avoid blocking operations
- Intelligent alerting to prevent notification spam

### Resource Management

- Memory-efficient historical data storage
- Automatic cleanup of old monitoring data
- Optimized database queries for health checks

## 🔮 Future Enhancements

### Planned Features

- **Custom Health Checks**: User-defined health check plugins
- **Advanced Analytics**: Machine learning-based anomaly detection
- **Multi-instance Monitoring**: Health checks across multiple app instances
- **Integration APIs**: Webhooks and third-party monitoring integrations
- **Mobile Dashboard**: Responsive mobile interface for health monitoring

### Extensibility

The health system is designed to be extensible:

```python
# Custom health check example
from rail_django_graphql.extensions.health import HealthChecker

class CustomHealthChecker(HealthChecker):
    def check_custom_service_health(self):
        # Your custom health check logic
        return {
            'component': 'Custom Service',
            'status': 'healthy',
            'message': 'Service operational',
            'response_time_ms': 25.0
        }
```

## 📚 Related Documentation

- [Performance Monitoring](../performance/README.md)
- [Error Handling](../error_handling/README.md)
- [Security Guidelines](../security/README.md)
- [Deployment Guide](../deployment/README.md)

---

**The Health Checks & Diagnostics system provides enterprise-grade monitoring capabilities for your Django GraphQL application, ensuring high availability and optimal performance.**
