# Performance Monitoring Setup

This guide walks you through setting up performance monitoring for your GraphQL API using `rail_django_graphql`.

## Quick Setup

### 1. Enable Performance Middleware

Add the performance middleware to your Django `MIDDLEWARE` setting:

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Add performance monitoring middleware
    'rail_django_graphql.middleware.performance.GraphQLPerformanceMiddleware',
]
```

### 2. Configure Performance Settings

Enable performance monitoring in your `rail_django_graphql` configuration:

```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    # ... other settings ...
    
    # Performance Monitoring
    'PERFORMANCE_MONITORING': True,
    'SLOW_QUERY_THRESHOLD': 1000,  # milliseconds
    'LOG_SLOW_QUERIES': True,
    'ENABLE_QUERY_COMPLEXITY_ANALYSIS': True,
    'MAX_QUERY_COMPLEXITY': 100,
    'ENABLE_MEMORY_TRACKING': True,
    'MEMORY_THRESHOLD_MB': 100,
}
```

### 3. Setup Performance Monitoring

Use the setup utility function to configure default thresholds:

```python
# In your Django app's ready() method or settings.py
from rail_django_graphql.middleware import setup_performance_monitoring

# Configure with default settings
setup_performance_monitoring()

# Or customize thresholds
setup_performance_monitoring(
    slow_query_threshold=500,    # 500ms
    complexity_threshold=50,     # Lower complexity limit
    memory_threshold=50          # 50MB memory limit
)
```

### 4. Add Performance URLs

Include the performance monitoring URLs in your URL configuration:

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ... your other URLs ...
    
    # Include rail_django_graphql URLs (includes performance endpoints)
    path('', include('rail_django_graphql.urls')),
]
```

## Advanced Configuration

### Custom Performance Thresholds

Configure detailed performance thresholds:

```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'PERFORMANCE_MONITORING': True,
    
    # Query Performance
    'SLOW_QUERY_THRESHOLD': 1000,           # Slow query threshold in ms
    'VERY_SLOW_QUERY_THRESHOLD': 5000,      # Very slow query threshold in ms
    'LOG_SLOW_QUERIES': True,               # Log slow queries
    'LOG_QUERY_DETAILS': True,              # Include query text in logs
    
    # Query Complexity
    'ENABLE_QUERY_COMPLEXITY_ANALYSIS': True,
    'MAX_QUERY_COMPLEXITY': 100,            # Maximum allowed complexity
    'COMPLEXITY_DEPTH_WEIGHT': 2,           # Weight for query depth
    'COMPLEXITY_BREADTH_WEIGHT': 1,         # Weight for query breadth
    
    # Memory Monitoring
    'ENABLE_MEMORY_TRACKING': True,
    'MEMORY_THRESHOLD_MB': 100,             # Memory usage threshold
    'TRACK_PEAK_MEMORY': True,              # Track peak memory usage
    
    # Database Monitoring
    'TRACK_DB_QUERIES': True,               # Monitor database queries
    'DB_QUERY_THRESHOLD': 50,               # Max queries per request
    'LOG_DB_QUERIES': False,                # Log individual DB queries
    
    # Cache Monitoring
    'TRACK_CACHE_OPERATIONS': True,         # Monitor cache operations
    'LOG_CACHE_MISSES': False,              # Log cache misses
}
```

### Logging Configuration

Configure logging for performance monitoring:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'performance': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'performance_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/performance.log',
            'formatter': 'performance',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'performance',
        },
    },
    'loggers': {
        'rail_django_graphql.performance': {
            'handlers': ['performance_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Sentry Integration

Integrate with Sentry for production monitoring:

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(
    level=logging.INFO,        # Capture info and above as breadcrumbs
    event_level=logging.ERROR  # Send errors as events
)

sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN",
    integrations=[
        DjangoIntegration(),
        sentry_logging,
    ],
    traces_sample_rate=1.0,
    send_default_pii=True
)

# Enable Sentry integration in rail_django_graphql
RAIL_DJANGO_GRAPHQL = {
    'PERFORMANCE_MONITORING': True,
    'SENTRY_INTEGRATION': True,
    'SENTRY_PERFORMANCE_TRACES': True,
}
```

## Environment-Specific Configuration

### Development Settings

```python
# settings/development.py
RAIL_DJANGO_GRAPHQL = {
    'PERFORMANCE_MONITORING': True,
    'SLOW_QUERY_THRESHOLD': 100,     # Lower threshold for development
    'LOG_SLOW_QUERIES': True,
    'LOG_QUERY_DETAILS': True,       # Include full query text
    'ENABLE_QUERY_COMPLEXITY_ANALYSIS': True,
    'TRACK_DB_QUERIES': True,
    'LOG_DB_QUERIES': True,          # Log all DB queries in dev
}

# Enable Django Debug Toolbar integration
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

### Production Settings

```python
# settings/production.py
RAIL_DJANGO_GRAPHQL = {
    'PERFORMANCE_MONITORING': True,
    'SLOW_QUERY_THRESHOLD': 1000,    # Higher threshold for production
    'LOG_SLOW_QUERIES': True,
    'LOG_QUERY_DETAILS': False,      # Don't log query text in production
    'ENABLE_QUERY_COMPLEXITY_ANALYSIS': True,
    'MAX_QUERY_COMPLEXITY': 50,      # Stricter complexity limit
    'TRACK_DB_QUERIES': True,
    'LOG_DB_QUERIES': False,         # Don't log individual queries
    'SENTRY_INTEGRATION': True,      # Enable Sentry in production
}
```

### Testing Settings

```python
# settings/testing.py
RAIL_DJANGO_GRAPHQL = {
    'PERFORMANCE_MONITORING': False,  # Disable in tests for speed
    'LOG_SLOW_QUERIES': False,
    'TRACK_DB_QUERIES': False,
}
```

## Verification

### 1. Check Middleware Installation

Verify the middleware is properly installed:

```python
# In Django shell
python manage.py shell

>>> from django.conf import settings
>>> 'rail_django_graphql.middleware.performance.GraphQLPerformanceMiddleware' in settings.MIDDLEWARE
True
```

### 2. Test Performance Endpoint

Access the performance monitoring endpoint:

```bash
# Get performance statistics
curl http://localhost:8000/graphql/performance/?action=stats

# Get recent alerts
curl http://localhost:8000/graphql/performance/?action=alerts

# Get slow queries
curl http://localhost:8000/graphql/performance/?action=slow_queries
```

### 3. Check Logs

Verify performance logging is working:

```bash
# Check performance logs
tail -f logs/performance.log

# Look for performance entries
grep "SLOW_QUERY" logs/performance.log
grep "HIGH_COMPLEXITY" logs/performance.log
grep "MEMORY_WARNING" logs/performance.log
```

## Troubleshooting

### Common Issues

1. **Middleware Not Working**
   - Ensure middleware is in correct order
   - Check Django settings are loaded properly
   - Verify middleware import path

2. **Performance Endpoint 404**
   - Include `rail_django_graphql.urls` in your URL configuration
   - Check URL patterns are loaded correctly

3. **No Performance Logs**
   - Verify logging configuration
   - Check log file permissions
   - Ensure performance monitoring is enabled

4. **High Memory Usage**
   - Adjust memory tracking settings
   - Consider disabling memory tracking in high-traffic environments
   - Monitor for memory leaks

### Debug Mode

Enable debug mode for detailed performance information:

```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'PERFORMANCE_MONITORING': True,
    'DEBUG_PERFORMANCE': True,        # Enable debug mode
    'VERBOSE_LOGGING': True,          # Enable verbose logging
}
```

## Next Steps

- [Performance API Reference](../api/performance-api.md)
- [Performance Metrics Guide](../features/performance-metrics.md)
- [Troubleshooting Guide](../troubleshooting/performance-troubleshooting.md)
- [Best Practices](../project/performance-best-practices.md)