# Performance Monitoring Troubleshooting

This guide helps you diagnose and resolve common issues with the `rail_django_graphql` performance monitoring system.

## Common Issues

### 1. Middleware Not Working

#### Symptoms
- No performance metrics being collected
- Performance endpoints return 404 errors
- No performance logs generated

#### Diagnosis
```python
# Check if middleware is properly installed
from django.conf import settings
print('rail_django_graphql.middleware.performance.GraphQLPerformanceMiddleware' in settings.MIDDLEWARE)

# Check middleware order
print(settings.MIDDLEWARE)

# Verify performance monitoring is enabled
print(getattr(settings, 'RAIL_DJANGO_GRAPHQL', {}).get('PERFORMANCE_MONITORING', False))
```

#### Solutions

**1. Add middleware to settings:**
```python
# settings.py
MIDDLEWARE = [
    # ... other middleware ...
    'rail_django_graphql.middleware.performance.GraphQLPerformanceMiddleware',
]
```

**2. Enable performance monitoring:**
```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'PERFORMANCE_MONITORING': True,
}
```

**3. Check middleware order:**
```python
# Ensure performance middleware is after authentication middleware
MIDDLEWARE = [
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'rail_django_graphql.middleware.performance.GraphQLPerformanceMiddleware',
    # ... other middleware ...
]
```

### 2. Performance Endpoint Returns 404

#### Symptoms
- `/graphql/performance/` returns 404 Not Found
- URL patterns not found

#### Diagnosis
```python
# Check URL configuration
from django.urls import reverse
try:
    url = reverse('graphql_performance')
    print(f"Performance URL: {url}")
except:
    print("Performance URL not found")

# Check if URLs are included
from django.conf import settings
print(settings.ROOT_URLCONF)
```

#### Solutions

**1. Include rail_django_graphql URLs:**
```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ... your other URLs ...
    path('', include('rail_django_graphql.urls')),
]
```

**2. Add performance URLs directly:**
```python
# urls.py
from rail_django_graphql.middleware.performance import GraphQLPerformanceView

urlpatterns = [
    # ... your other URLs ...
    path('graphql/performance/', GraphQLPerformanceView.as_view(), name='graphql_performance'),
]
```

### 3. AttributeError: 'GraphQLPerformanceView' object has no attribute 'as_view'

#### Symptoms
- Error when starting Django server
- `AttributeError` in URL configuration

#### Diagnosis
```python
# Check if GraphQLPerformanceView inherits from Django View
from rail_django_graphql.middleware.performance import GraphQLPerformanceView
print(GraphQLPerformanceView.__bases__)
```

#### Solution
This was fixed in the recent update. Ensure you have the latest version where `GraphQLPerformanceView` inherits from `django.views.View`.

### 4. High Memory Usage

#### Symptoms
- Server memory consumption increases over time
- Memory warnings in performance logs
- Out of memory errors

#### Diagnosis
```python
# Check memory tracking settings
from django.conf import settings
config = settings.RAIL_DJANGO_GRAPHQL

print(f"Memory tracking enabled: {config.get('ENABLE_MEMORY_TRACKING', False)}")
print(f"Memory threshold: {config.get('MEMORY_THRESHOLD_MB', 100)}MB")

# Monitor memory usage
import psutil
import os

process = psutil.Process(os.getpid())
memory_info = process.memory_info()
print(f"Current memory usage: {memory_info.rss / 1024 / 1024:.2f}MB")
```

#### Solutions

**1. Adjust memory tracking:**
```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'ENABLE_MEMORY_TRACKING': False,  # Disable if causing issues
    'MEMORY_THRESHOLD_MB': 200,       # Increase threshold
}
```

**2. Optimize metric collection:**
```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'PERFORMANCE_MONITORING': True,
    'COLLECT_DETAILED_METRICS': False,  # Reduce detail level
    'METRIC_RETENTION_HOURS': 1,        # Reduce retention time
}
```

**3. Use sampling:**
```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'PERFORMANCE_SAMPLING_RATE': 0.1,  # Sample 10% of requests
}
```

### 5. Performance Logs Not Generated

#### Symptoms
- No entries in performance log files
- Missing performance information

#### Diagnosis
```python
# Check logging configuration
import logging
logger = logging.getLogger('rail_django_graphql.performance')
print(f"Logger level: {logger.level}")
print(f"Logger handlers: {logger.handlers}")

# Test logging
logger.info("Test performance log message")
```

#### Solutions

**1. Configure logging:**
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'performance_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/performance.log',
        },
    },
    'loggers': {
        'rail_django_graphql.performance': {
            'handlers': ['performance_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

**2. Create log directory:**
```bash
mkdir -p logs
chmod 755 logs
```

**3. Enable performance logging:**
```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'LOG_SLOW_QUERIES': True,
    'LOG_PERFORMANCE_METRICS': True,
    'VERBOSE_LOGGING': True,
}
```

### 6. Database Performance Issues

#### Symptoms
- High database query counts
- Slow database operations
- Connection pool exhaustion

#### Diagnosis
```python
# Check database settings
from django.conf import settings
print(settings.DATABASES)

# Monitor database connections
from django.db import connections
for alias in connections:
    connection = connections[alias]
    print(f"Database {alias}: {connection.queries_logged} queries")
```

#### Solutions

**1. Optimize database queries:**
```python
# Use select_related and prefetch_related
queryset = MyModel.objects.select_related('related_field').prefetch_related('many_to_many_field')
```

**2. Configure connection pooling:**
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        }
    }
}
```

**3. Adjust performance thresholds:**
```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'DB_QUERY_THRESHOLD': 100,        # Increase threshold
    'SLOW_DB_QUERY_MS': 200,          # Increase slow query threshold
}
```

### 7. Cache Performance Issues

#### Symptoms
- Low cache hit rates
- Slow cache operations
- Cache-related errors

#### Diagnosis
```python
# Check cache configuration
from django.conf import settings
print(settings.CACHES)

# Test cache operations
from django.core.cache import cache
cache.set('test_key', 'test_value', 60)
result = cache.get('test_key')
print(f"Cache test result: {result}")
```

#### Solutions

**1. Configure cache properly:**
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50}
        }
    }
}
```

**2. Optimize cache usage:**
```python
# Use cache versioning
from django.core.cache import cache
cache.set('key', 'value', 300, version=2)
```

**3. Monitor cache performance:**
```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'TRACK_CACHE_OPERATIONS': True,
    'LOG_CACHE_MISSES': True,
    'CACHE_HIT_RATE_THRESHOLD': 0.8,
}
```

## Performance Optimization

### 1. Query Optimization

#### Identify Slow Queries
```python
# Get slow queries from API
import requests
response = requests.get('http://localhost:8000/graphql/performance/?action=slow_queries&limit=10')
slow_queries = response.json()['data']['slow_queries']

for query in slow_queries:
    print(f"Query: {query['operation_name']}")
    print(f"Time: {query['execution_time_ms']}ms")
    print(f"Complexity: {query['complexity_score']}")
    print("---")
```

#### Optimize Query Structure
```graphql
# Bad: Deep nesting
query GetUserData {
  user(id: "123") {
    posts {
      comments {
        author {
          posts {
            comments {
              text
            }
          }
        }
      }
    }
  }
}

# Good: Flatter structure with pagination
query GetUserData {
  user(id: "123") {
    id
    name
    posts(first: 10) {
      edges {
        node {
          id
          title
          commentCount
        }
      }
    }
  }
}
```

### 2. Memory Optimization

#### Monitor Memory Usage
```python
# Custom memory monitoring
import psutil
import os

def log_memory_usage():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    print(f"RSS: {memory_info.rss / 1024 / 1024:.2f}MB")
    print(f"VMS: {memory_info.vms / 1024 / 1024:.2f}MB")
```

#### Optimize Memory Usage
```python
# Use generators for large datasets
def get_large_dataset():
    for item in Model.objects.iterator(chunk_size=1000):
        yield item

# Clear unused variables
def process_data():
    large_data = get_large_data()
    result = process(large_data)
    del large_data  # Free memory
    return result
```

### 3. Complexity Management

#### Set Complexity Limits
```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'ENABLE_QUERY_COMPLEXITY_ANALYSIS': True,
    'MAX_QUERY_COMPLEXITY': 50,
    'COMPLEXITY_DEPTH_WEIGHT': 2,
    'COMPLEXITY_BREADTH_WEIGHT': 1,
}
```

#### Implement Query Whitelisting
```python
# Allow only pre-approved queries in production
RAIL_DJANGO_GRAPHQL = {
    'ENABLE_QUERY_WHITELISTING': True,
    'ALLOWED_QUERIES_FILE': 'allowed_queries.json',
}
```

## Monitoring and Alerting

### 1. Set Up Alerts

#### Email Alerts
```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'PERFORMANCE_ALERTS': {
        'ENABLE_EMAIL_ALERTS': True,
        'ALERT_EMAIL_RECIPIENTS': ['admin@example.com'],
        'ALERT_EMAIL_THRESHOLD': 'error',
    }
}
```

#### Slack Integration
```python
# Custom alert handler
import requests

def send_slack_alert(alert):
    webhook_url = 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    message = {
        'text': f"Performance Alert: {alert['message']}",
        'color': 'danger' if alert['severity'] == 'error' else 'warning'
    }
    requests.post(webhook_url, json=message)
```

### 2. Dashboard Setup

#### Grafana Dashboard
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
      }
    ]
  }
}
```

#### Custom Dashboard
```python
# Django view for performance dashboard
def performance_dashboard(request):
    # Get performance metrics
    stats = get_performance_stats()
    alerts = get_recent_alerts()
    
    context = {
        'stats': stats,
        'alerts': alerts,
        'charts_data': prepare_charts_data(stats)
    }
    return render(request, 'performance_dashboard.html', context)
```

## Debug Mode

### Enable Debug Mode
```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'DEBUG_PERFORMANCE': True,
    'VERBOSE_LOGGING': True,
    'LOG_ALL_QUERIES': True,  # Only in development
}
```

### Debug Tools
```python
# Performance debugging decorator
from functools import wraps
import time

def debug_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {(end_time - start_time) * 1000:.2f}ms")
        return result
    return wrapper

# Use in resolvers
@debug_performance
def resolve_complex_field(self, info, **kwargs):
    return expensive_operation()
```

## Getting Help

### 1. Enable Verbose Logging
```python
# settings.py
LOGGING = {
    'loggers': {
        'rail_django_graphql': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

### 2. Collect Diagnostic Information
```python
# Diagnostic script
import django
from django.conf import settings

def collect_diagnostics():
    print("=== Django Configuration ===")
    print(f"Django version: {django.VERSION}")
    print(f"Debug mode: {settings.DEBUG}")
    
    print("\n=== Middleware Configuration ===")
    for middleware in settings.MIDDLEWARE:
        print(f"  {middleware}")
    
    print("\n=== Performance Configuration ===")
    config = getattr(settings, 'RAIL_DJANGO_GRAPHQL', {})
    for key, value in config.items():
        if 'PERFORMANCE' in key:
            print(f"  {key}: {value}")
    
    print("\n=== Database Configuration ===")
    for alias, db_config in settings.DATABASES.items():
        print(f"  {alias}: {db_config['ENGINE']}")
```

### 3. Performance Profiling
```python
# Profile GraphQL queries
import cProfile
import pstats

def profile_graphql_query(query, variables=None):
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Execute GraphQL query
    result = execute_graphql_query(query, variables)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
    
    return result
```

## Best Practices

### 1. Gradual Rollout
- Start with basic monitoring
- Add detailed metrics gradually
- Monitor performance impact

### 2. Threshold Tuning
- Start with conservative thresholds
- Adjust based on actual usage patterns
- Monitor false positive rates

### 3. Regular Maintenance
- Review performance logs weekly
- Update thresholds based on trends
- Archive old performance data

### 4. Team Training
- Document performance monitoring setup
- Train team on interpreting metrics
- Establish performance review processes

## Next Steps

- [Performance Monitoring Overview](../features/performance-monitoring.md)
- [Setup Guide](../setup/performance-setup.md)
- [Performance API Reference](../api/performance-api.md)
- [Best Practices](../project/performance-best-practices.md)