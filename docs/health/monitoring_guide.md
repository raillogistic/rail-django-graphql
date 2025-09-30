# Health Monitoring Guide

## 🎯 Overview

This guide provides comprehensive instructions for setting up, configuring, and managing continuous health monitoring for your Django GraphQL Auto-Generation system. Learn how to implement proactive monitoring, alerting, and automated recovery procedures.

## 🚀 Quick Start

### 1. Enable Health Monitoring

```bash
# Start continuous monitoring with default settings
python manage.py health_monitor

# Start with custom interval (30 seconds)
python manage.py health_monitor --interval 30

# Enable email alerts
python manage.py health_monitor --email-alerts

# Run in verbose mode for debugging
python manage.py health_monitor --verbose
```

### 2. Basic Configuration

```python
# settings.py
HEALTH_CHECK_SETTINGS = {
    'MONITORING_INTERVAL': 60,  # Check every 60 seconds
    'ALERT_EMAIL_RECIPIENTS': ['admin@example.com'],
    'PERFORMANCE_THRESHOLD_MS': 1000,  # Alert if response > 1s
    'MEMORY_THRESHOLD_PERCENT': 80,    # Alert if memory > 80%
    'CPU_THRESHOLD_PERCENT': 75,       # Alert if CPU > 75%
}
```

### 3. Verify Setup

```bash
# Test health endpoints
curl http://localhost:8000/health/check/
curl http://localhost:8000/health/api/

# Check dashboard
# Visit: http://localhost:8000/health/dashboard/
```

## 📊 Monitoring Components

### System Metrics Monitoring

#### CPU Usage Monitoring

```python
# Automatic CPU monitoring with thresholds
HEALTH_CHECK_SETTINGS = {
    'CPU_THRESHOLD_PERCENT': 75,      # Warning threshold
    'CPU_CRITICAL_PERCENT': 90,       # Critical threshold
    'CPU_MONITORING_ENABLED': True,
}
```

**Alert Triggers:**

- **Warning**: CPU usage > 75% for 5 minutes
- **Critical**: CPU usage > 90% for 2 minutes
- **Recovery**: CPU usage < 70% for 3 minutes

#### Memory Usage Monitoring

```python
# Memory monitoring configuration
HEALTH_CHECK_SETTINGS = {
    'MEMORY_THRESHOLD_PERCENT': 80,   # Warning threshold
    'MEMORY_CRITICAL_PERCENT': 95,    # Critical threshold
    'MEMORY_MONITORING_ENABLED': True,
}
```

**Alert Triggers:**

- **Warning**: Memory usage > 80% for 5 minutes
- **Critical**: Memory usage > 95% for 1 minute
- **Recovery**: Memory usage < 75% for 3 minutes

#### Disk Usage Monitoring

```python
# Disk space monitoring
HEALTH_CHECK_SETTINGS = {
    'DISK_THRESHOLD_PERCENT': 85,     # Warning threshold
    'DISK_CRITICAL_PERCENT': 95,      # Critical threshold
    'DISK_MONITORING_ENABLED': True,
}
```

### Application Component Monitoring

#### GraphQL Schema Health

```python
# Schema monitoring configuration
HEALTH_CHECK_SETTINGS = {
    'SCHEMA_BUILD_TIMEOUT': 30,       # Max build time (seconds)
    'SCHEMA_MONITORING_ENABLED': True,
    'SCHEMA_BUILD_ALERTS': True,
}
```

**Monitored Metrics:**

- Schema build time and success rate
- Type count and complexity
- Query/mutation availability
- Schema validation errors

#### Database Connection Monitoring

```python
# Database monitoring settings
HEALTH_CHECK_SETTINGS = {
    'DATABASE_QUERY_TIMEOUT': 10,     # Max query time (seconds)
    'DATABASE_CONNECTION_POOL_MIN': 5, # Min connections
    'DATABASE_CONNECTION_POOL_MAX': 20, # Max connections
    'DATABASE_MONITORING_ENABLED': True,
}
```

**Monitored Metrics:**

- Connection pool status
- Query response times
- Connection failures
- Database availability

#### Cache System Monitoring

```python
# Cache monitoring configuration
HEALTH_CHECK_SETTINGS = {
    'CACHE_OPERATION_TIMEOUT': 5,     # Max operation time (seconds)
    'CACHE_HIT_RATE_THRESHOLD': 0.8,  # Min acceptable hit rate
    'CACHE_MONITORING_ENABLED': True,
}
```

**Monitored Metrics:**

- Cache hit/miss rates
- Operation response times
- Memory usage
- Connection status

## 🚨 Alert Configuration

### Email Alerts Setup

#### Basic Email Configuration

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-app@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'

HEALTH_CHECK_SETTINGS = {
    'ALERT_EMAIL_RECIPIENTS': [
        'admin@example.com',
        'devops@example.com',
        'oncall@example.com'
    ],
    'ALERT_EMAIL_SUBJECT_PREFIX': '[PROD Alert]',
    'ALERT_COOLDOWN_MINUTES': 15,  # Prevent spam
}
```

#### Advanced Email Configuration

```python
# Custom email templates and formatting
HEALTH_CHECK_SETTINGS = {
    'ALERT_EMAIL_TEMPLATE': 'health/alert_email.html',
    'ALERT_EMAIL_FROM': 'Health Monitor <noreply@example.com>',
    'ALERT_EMAIL_INCLUDE_METRICS': True,
    'ALERT_EMAIL_INCLUDE_RECOMMENDATIONS': True,
    'ALERT_EMAIL_FORMAT': 'html',  # 'html' or 'text'
}
```

### Alert Severity Levels

#### Critical Alerts

Immediate attention required - system functionality at risk.

```python
# Critical alert triggers
CRITICAL_THRESHOLDS = {
    'database_down': True,           # Database unavailable
    'cache_down': True,              # Cache system unavailable
    'memory_usage': 95,              # Memory > 95%
    'cpu_usage': 90,                 # CPU > 90%
    'disk_usage': 95,                # Disk > 95%
    'response_time_ms': 5000,        # Response > 5 seconds
}
```

#### Warning Alerts

Performance degradation detected - monitoring required.

```python
# Warning alert triggers
WARNING_THRESHOLDS = {
    'memory_usage': 80,              # Memory > 80%
    'cpu_usage': 75,                 # CPU > 75%
    'disk_usage': 85,                # Disk > 85%
    'response_time_ms': 1000,        # Response > 1 second
    'cache_hit_rate': 0.8,           # Hit rate < 80%
    'database_connections': 18,       # Connections > 90% of pool
}
```

#### Info Alerts

General system information and recommendations.

```python
# Info alert triggers
INFO_THRESHOLDS = {
    'uptime_days': 30,               # System uptime milestones
    'schema_rebuild': True,          # Schema rebuild notifications
    'cache_clear': True,             # Cache clear notifications
    'maintenance_mode': True,        # Maintenance mode changes
}
```

### Alert Customization

#### Custom Alert Templates

```html
<!-- health/alert_email.html -->
<!DOCTYPE html>
<html>
  <head>
    <title>Health Alert: {{ alert.severity|title }}</title>
    <style>
      .critical {
        color: #d32f2f;
      }
      .warning {
        color: #f57c00;
      }
      .info {
        color: #1976d2;
      }
    </style>
  </head>
  <body>
    <h2 class="{{ alert.severity }}">
      {{ alert.severity|title }} Alert: {{ alert.component }}
    </h2>

    <p><strong>Time:</strong> {{ alert.timestamp }}</p>
    <p><strong>Message:</strong> {{ alert.message }}</p>

    {% if alert.metrics %}
    <h3>Current Metrics</h3>
    <ul>
      <li>CPU Usage: {{ alert.metrics.cpu_usage_percent }}%</li>
      <li>Memory Usage: {{ alert.metrics.memory_usage_percent }}%</li>
      <li>Response Time: {{ alert.response_time_ms }}ms</li>
    </ul>
    {% endif %} {% if alert.recommendations %}
    <h3>Recommended Actions</h3>
    <ul>
      {% for recommendation in alert.recommendations %}
      <li>{{ recommendation }}</li>
      {% endfor %}
    </ul>
    {% endif %}

    <p><a href="{{ dashboard_url }}">View Health Dashboard</a></p>
  </body>
</html>
```

#### Webhook Alerts

```python
# Webhook integration for Slack, Discord, etc.
HEALTH_CHECK_SETTINGS = {
    'WEBHOOK_ALERTS_ENABLED': True,
    'WEBHOOK_URLS': {
        'slack': 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK',
        'discord': 'https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK',
        'teams': 'https://outlook.office.com/webhook/YOUR/TEAMS/WEBHOOK'
    },
    'WEBHOOK_ALERT_LEVELS': ['critical', 'warning'],  # Which levels to send
}
```

## 📈 Performance Monitoring

### Response Time Monitoring

#### Endpoint Performance Tracking

```python
# Monitor specific endpoint performance
HEALTH_CHECK_SETTINGS = {
    'MONITOR_ENDPOINTS': [
        '/graphql/',
        '/health/api/',
        '/admin/',
    ],
    'ENDPOINT_TIMEOUT_MS': 2000,      # Alert if > 2 seconds
    'ENDPOINT_MONITORING_INTERVAL': 30, # Check every 30 seconds
}
```

#### Database Query Performance

```python
# Database query monitoring
HEALTH_CHECK_SETTINGS = {
    'MONITOR_SLOW_QUERIES': True,
    'SLOW_QUERY_THRESHOLD_MS': 500,   # Queries > 500ms
    'QUERY_MONITORING_ENABLED': True,
    'LOG_SLOW_QUERIES': True,
}
```

### Resource Usage Trends

#### Historical Data Collection

```python
# Historical monitoring configuration
HEALTH_CHECK_SETTINGS = {
    'HISTORY_RETENTION_DAYS': 30,     # Keep 30 days of data
    'HISTORY_COLLECTION_INTERVAL': 300, # Collect every 5 minutes
    'HISTORY_STORAGE_BACKEND': 'database', # 'database' or 'file'
    'HISTORY_COMPRESSION': True,       # Compress old data
}
```

#### Trend Analysis

```python
# Automatic trend analysis
HEALTH_CHECK_SETTINGS = {
    'TREND_ANALYSIS_ENABLED': True,
    'TREND_ANALYSIS_WINDOW_HOURS': 24, # Analyze last 24 hours
    'TREND_ALERT_THRESHOLD': 0.2,     # Alert on 20% degradation
    'TREND_ANALYSIS_METRICS': [
        'cpu_usage',
        'memory_usage',
        'response_time',
        'cache_hit_rate'
    ]
}
```

## 🔧 Advanced Configuration

### Custom Health Checks

#### Creating Custom Checks

```python
# custom_health_checks.py
from rail_django_graphql.extensions.health import HealthChecker

class CustomHealthChecker(HealthChecker):
    def check_external_api_health(self):
        """Check external API dependency health."""
        import requests
        import time

        start_time = time.time()
        try:
            response = requests.get(
                'https://api.external-service.com/health',
                timeout=10
            )
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return {
                    'component': 'External API',
                    'status': 'healthy',
                    'message': 'API responding normally',
                    'response_time_ms': response_time,
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ')
                }
            else:
                return {
                    'component': 'External API',
                    'status': 'degraded',
                    'message': f'API returned status {response.status_code}',
                    'response_time_ms': response_time,
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ')
                }
        except Exception as e:
            return {
                'component': 'External API',
                'status': 'unhealthy',
                'message': f'API check failed: {str(e)}',
                'response_time_ms': (time.time() - start_time) * 1000,
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }

    def check_message_queue_health(self):
        """Check message queue health (Redis, RabbitMQ, etc.)."""
        # Implementation for message queue health check
        pass

    def check_file_storage_health(self):
        """Check file storage system health (S3, local storage, etc.)."""
        # Implementation for file storage health check
        pass
```

#### Registering Custom Checks

```python
# settings.py
HEALTH_CHECK_SETTINGS = {
    'CUSTOM_HEALTH_CHECKER': 'myapp.custom_health_checks.CustomHealthChecker',
    'CUSTOM_CHECKS_ENABLED': True,
    'CUSTOM_CHECKS': [
        'check_external_api_health',
        'check_message_queue_health',
        'check_file_storage_health'
    ]
}
```

### Multi-Environment Configuration

#### Development Environment

```python
# settings/development.py
HEALTH_CHECK_SETTINGS = {
    'MONITORING_INTERVAL': 30,        # More frequent checks
    'ALERT_EMAIL_RECIPIENTS': ['dev@example.com'],
    'PERFORMANCE_THRESHOLD_MS': 2000, # More lenient thresholds
    'MEMORY_THRESHOLD_PERCENT': 90,
    'CPU_THRESHOLD_PERCENT': 85,
    'DEBUG_MODE': True,               # Detailed error messages
    'VERBOSE_LOGGING': True,
}
```

#### Staging Environment

```python
# settings/staging.py
HEALTH_CHECK_SETTINGS = {
    'MONITORING_INTERVAL': 60,
    'ALERT_EMAIL_RECIPIENTS': ['staging@example.com'],
    'PERFORMANCE_THRESHOLD_MS': 1500,
    'MEMORY_THRESHOLD_PERCENT': 85,
    'CPU_THRESHOLD_PERCENT': 80,
    'LOAD_TESTING_MODE': True,        # Special handling for load tests
}
```

#### Production Environment

```python
# settings/production.py
HEALTH_CHECK_SETTINGS = {
    'MONITORING_INTERVAL': 60,
    'ALERT_EMAIL_RECIPIENTS': [
        'admin@example.com',
        'oncall@example.com'
    ],
    'PERFORMANCE_THRESHOLD_MS': 1000, # Strict thresholds
    'MEMORY_THRESHOLD_PERCENT': 80,
    'CPU_THRESHOLD_PERCENT': 75,
    'ALERT_COOLDOWN_MINUTES': 15,     # Prevent alert spam
    'HIGH_AVAILABILITY_MODE': True,   # Enhanced monitoring
}
```

## 🔄 Automated Recovery

### Self-Healing Procedures

#### Automatic Cache Clearing

```python
# Automatic cache clearing on cache health issues
HEALTH_CHECK_SETTINGS = {
    'AUTO_RECOVERY_ENABLED': True,
    'AUTO_CLEAR_CACHE_ON_ISSUES': True,
    'CACHE_CLEAR_THRESHOLD_FAILURES': 3,  # Clear after 3 failures
    'CACHE_CLEAR_COOLDOWN_MINUTES': 10,   # Wait 10 min between clears
}
```

#### Database Connection Pool Reset

```python
# Automatic connection pool reset
HEALTH_CHECK_SETTINGS = {
    'AUTO_RESET_DB_POOL': True,
    'DB_POOL_RESET_THRESHOLD': 5,     # Reset after 5 connection failures
    'DB_POOL_RESET_COOLDOWN_MINUTES': 5,
}
```

#### Schema Rebuild Triggers

```python
# Automatic schema rebuild on schema issues
HEALTH_CHECK_SETTINGS = {
    'AUTO_REBUILD_SCHEMA': True,
    'SCHEMA_REBUILD_THRESHOLD': 2,    # Rebuild after 2 failures
    'SCHEMA_REBUILD_COOLDOWN_MINUTES': 15,
}
```

### Recovery Scripts

#### Custom Recovery Actions

```python
# custom_recovery.py
from rail_django_graphql.extensions.health import HealthChecker

class RecoveryManager:
    def __init__(self):
        self.health_checker = HealthChecker()

    def handle_memory_pressure(self):
        """Handle high memory usage."""
        # Clear unnecessary caches
        from django.core.cache import cache
        cache.clear()

        # Force garbage collection
        import gc
        gc.collect()

        # Log recovery action
        import logging
        logger = logging.getLogger('health_monitor')
        logger.info("Executed memory pressure recovery actions")

    def handle_database_issues(self):
        """Handle database connectivity issues."""
        # Reset connection pool
        from django.db import connections
        for conn in connections.all():
            conn.close()

        # Log recovery action
        import logging
        logger = logging.getLogger('health_monitor')
        logger.info("Reset database connection pool")

    def handle_cache_issues(self):
        """Handle cache system issues."""
        # Clear cache and restart connections
        from django.core.cache import cache
        cache.clear()

        # Log recovery action
        import logging
        logger = logging.getLogger('health_monitor')
        logger.info("Cleared cache due to health issues")
```

## 📊 Monitoring Dashboard

### Dashboard Configuration

#### Real-time Updates

```python
# Dashboard settings
HEALTH_CHECK_SETTINGS = {
    'DASHBOARD_REFRESH_INTERVAL': 30,  # Auto-refresh every 30 seconds
    'DASHBOARD_HISTORY_POINTS': 20,    # Show last 20 data points
    'DASHBOARD_CHART_TYPES': [
        'line',      # Line charts for trends
        'gauge',     # Gauge charts for current values
        'bar'        # Bar charts for comparisons
    ],
    'DASHBOARD_THEME': 'dark',         # 'light' or 'dark'
}
```

#### Custom Dashboard Widgets

```html
<!-- custom_dashboard_widget.html -->
<div class="health-widget" id="custom-widget">
  <h3>Custom Metrics</h3>
  <div class="metric-row">
    <span class="metric-label">API Calls/min:</span>
    <span class="metric-value" id="api-calls-per-minute">--</span>
  </div>
  <div class="metric-row">
    <span class="metric-label">Error Rate:</span>
    <span class="metric-value" id="error-rate">--</span>
  </div>
</div>

<script>
  function updateCustomMetrics() {
    fetch("/health/custom-metrics/")
      .then((response) => response.json())
      .then((data) => {
        document.getElementById("api-calls-per-minute").textContent =
          data.api_calls_per_minute;
        document.getElementById("error-rate").textContent =
          data.error_rate + "%";
      });
  }

  // Update every 30 seconds
  setInterval(updateCustomMetrics, 30000);
  updateCustomMetrics(); // Initial load
</script>
```

### Mobile Dashboard

#### Responsive Design

```css
/* Mobile-friendly dashboard styles */
@media (max-width: 768px) {
  .health-dashboard {
    padding: 10px;
  }

  .metric-card {
    width: 100%;
    margin-bottom: 15px;
  }

  .chart-container {
    height: 200px; /* Smaller charts on mobile */
  }

  .alert-list {
    font-size: 14px;
  }
}
```

## 🔍 Troubleshooting

### Common Monitoring Issues

#### High False Positive Rate

```python
# Adjust thresholds to reduce false positives
HEALTH_CHECK_SETTINGS = {
    'PERFORMANCE_THRESHOLD_MS': 2000,  # Increase from 1000ms
    'MEMORY_THRESHOLD_PERCENT': 85,    # Increase from 80%
    'ALERT_COOLDOWN_MINUTES': 20,      # Increase cooldown
    'REQUIRE_CONSECUTIVE_FAILURES': 3, # Require 3 consecutive failures
}
```

#### Missing Alerts

```python
# Ensure alerts are properly configured
HEALTH_CHECK_SETTINGS = {
    'ALERT_EMAIL_RECIPIENTS': ['admin@example.com'],  # Verify email addresses
    'EMAIL_ALERTS_ENABLED': True,                     # Ensure enabled
    'WEBHOOK_ALERTS_ENABLED': True,                   # Enable webhooks
    'ALERT_ALL_SEVERITY_LEVELS': True,               # Don't filter by severity
}
```

#### Performance Impact

```python
# Optimize monitoring performance
HEALTH_CHECK_SETTINGS = {
    'MONITORING_INTERVAL': 120,        # Reduce frequency
    'CACHE_TIMEOUT': 600,             # Increase cache timeout
    'LIGHTWEIGHT_CHECKS_ONLY': True,  # Skip expensive checks
    'ASYNC_MONITORING': True,         # Use async monitoring
}
```

### Debug Mode

#### Enable Detailed Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'health_file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'health_monitor.log',
        },
    },
    'loggers': {
        'health_monitor': {
            'handlers': ['health_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

HEALTH_CHECK_SETTINGS = {
    'DEBUG_MODE': True,
    'VERBOSE_LOGGING': True,
    'LOG_ALL_CHECKS': True,
}
```

#### Manual Health Check Testing

```python
# Test health checks manually
from rail_django_graphql.extensions.health import HealthChecker

checker = HealthChecker()

# Test individual components
print("Schema Health:", checker.check_schema_health())
print("Database Health:", checker.check_database_health())
print("Cache Health:", checker.check_cache_health())

# Test complete health report
print("Full Report:", checker.get_health_report())
```

## 🚀 Production Best Practices

### Monitoring Strategy

1. **Layered Monitoring**: Combine application, system, and infrastructure monitoring
2. **Proactive Alerting**: Alert on trends, not just current values
3. **Alert Fatigue Prevention**: Use appropriate thresholds and cooldowns
4. **Recovery Automation**: Implement self-healing where safe and appropriate
5. **Regular Review**: Periodically review and adjust monitoring configuration

### Security Considerations

1. **Access Control**: Restrict access to detailed health information
2. **Information Disclosure**: Avoid exposing sensitive system details
3. **Rate Limiting**: Implement rate limiting on health endpoints
4. **Audit Logging**: Log access to health monitoring systems

### Performance Optimization

1. **Efficient Checks**: Design health checks to be lightweight and fast
2. **Caching Strategy**: Use appropriate caching to reduce system load
3. **Async Operations**: Use asynchronous monitoring where possible
4. **Resource Management**: Monitor the monitoring system's resource usage

---

**This monitoring guide provides the foundation for maintaining a healthy, high-performance Django GraphQL system with proactive monitoring and automated recovery capabilities.**
