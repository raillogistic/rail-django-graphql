Metrics & Performance Monitoring
=================================

Comprehensive metrics collection and performance monitoring for Django GraphQL Auto applications.

Overview
--------

The metrics system provides detailed insights into your GraphQL application's performance, usage patterns, and system health through automated collection and analysis of key performance indicators.

Basic Metrics Collection
-------------------------

Configuration
~~~~~~~~~~~~~

Enable metrics collection in your Django settings:

.. code-block:: python

   # settings.py
   GRAPHQL_AUTO = {
       'METRICS': {
           'ENABLED': True,
           'BACKEND': 'django_graphql_auto.metrics.backends.PrometheusBackend',
           'COLLECTION_INTERVAL': 60,  # seconds
           'RETENTION_DAYS': 30,
       }
   }

Default Metrics
~~~~~~~~~~~~~~~

Django GraphQL Auto automatically collects these metrics:

**Request Metrics**:
- ``graphql_requests_total``: Total number of GraphQL requests
- ``graphql_request_duration_seconds``: Request processing time
- ``graphql_request_size_bytes``: Request payload size
- ``graphql_response_size_bytes``: Response payload size

**Query Metrics**:
- ``graphql_query_complexity``: Query complexity score
- ``graphql_query_depth``: Query nesting depth
- ``graphql_resolver_duration_seconds``: Individual resolver execution time
- ``graphql_database_queries_total``: Number of database queries per request

**Error Metrics**:
- ``graphql_errors_total``: Total number of GraphQL errors
- ``graphql_validation_errors_total``: Schema validation errors
- ``graphql_execution_errors_total``: Query execution errors

Performance Metrics
--------------------

Query Performance
~~~~~~~~~~~~~~~~~

Monitor query execution performance:

.. code-block:: python

   from django_graphql_auto.metrics import performance_monitor
   
   @performance_monitor.track_query
   def resolve_users(self, info, **kwargs):
       # Your resolver logic
       return User.objects.all()

Database Performance
~~~~~~~~~~~~~~~~~~~~

Track database query performance:

.. code-block:: python

   # Automatic database query tracking
   GRAPHQL_AUTO = {
       'METRICS': {
           'TRACK_DATABASE_QUERIES': True,
           'SLOW_QUERY_THRESHOLD': 1.0,  # seconds
       }
   }

Memory Usage
~~~~~~~~~~~~

Monitor memory consumption:

.. code-block:: python

   from django_graphql_auto.metrics.collectors import MemoryCollector
   
   # Enable memory tracking
   GRAPHQL_AUTO = {
       'METRICS': {
           'COLLECTORS': [
               'django_graphql_auto.metrics.collectors.MemoryCollector',
           ]
       }
   }

Usage Metrics
-------------

User Activity
~~~~~~~~~~~~~

Track user engagement and activity:

.. code-block:: python

   # User activity metrics
   GRAPHQL_AUTO = {
       'METRICS': {
           'TRACK_USER_ACTIVITY': True,
           'USER_METRICS': {
               'ACTIVE_USERS': True,
               'QUERY_PATTERNS': True,
               'FEATURE_USAGE': True,
           }
       }
   }

API Usage
~~~~~~~~~

Monitor API endpoint usage:

.. code-block:: python

   from django_graphql_auto.metrics import api_metrics
   
   # Track specific operations
   @api_metrics.track_operation('user_creation')
   def create_user(self, info, input):
       # User creation logic
       return CreateUser(user=user)

Feature Usage
~~~~~~~~~~~~~

Track feature adoption and usage:

.. code-block:: python

   from django_graphql_auto.metrics import feature_tracker
   
   # Track feature usage
   feature_tracker.track('advanced_search', user_id=user.id)
   feature_tracker.track('bulk_operations', count=len(items))

Error Metrics
-------------

Error Tracking
~~~~~~~~~~~~~~

Comprehensive error monitoring:

.. code-block:: python

   # Error tracking configuration
   GRAPHQL_AUTO = {
       'METRICS': {
           'ERROR_TRACKING': {
               'ENABLED': True,
               'TRACK_STACK_TRACES': True,
               'CATEGORIZE_ERRORS': True,
               'ALERT_THRESHOLD': 10,  # errors per minute
           }
       }
   }

Error Categories
~~~~~~~~~~~~~~~~

Errors are automatically categorized:

- **Validation Errors**: Schema validation failures
- **Authentication Errors**: Authentication and authorization failures
- **Business Logic Errors**: Application-specific errors
- **System Errors**: Database, network, and infrastructure errors

Custom Metrics
--------------

Creating Custom Metrics
~~~~~~~~~~~~~~~~~~~~~~~~

Define application-specific metrics:

.. code-block:: python

   from django_graphql_auto.metrics import MetricCollector
   
   class BusinessMetricsCollector(MetricCollector):
       def collect(self):
           # Collect business-specific metrics
           return {
               'active_subscriptions': self.count_active_subscriptions(),
               'revenue_per_user': self.calculate_revenue_per_user(),
               'conversion_rate': self.calculate_conversion_rate(),
           }
   
       def count_active_subscriptions(self):
           from myapp.models import Subscription
           return Subscription.objects.filter(active=True).count()

Metric Decorators
~~~~~~~~~~~~~~~~~

Use decorators for easy metric collection:

.. code-block:: python

   from django_graphql_auto.metrics.decorators import track_metric
   
   @track_metric('order_processing_time')
   def process_order(order_id):
       # Order processing logic
       pass
   
   @track_metric('cache_hit_rate', metric_type='gauge')
   def get_cached_data(key):
       # Cache retrieval logic
       pass

Storage Backends
----------------

Prometheus Backend
~~~~~~~~~~~~~~~~~~

Export metrics to Prometheus:

.. code-block:: python

   # settings.py
   GRAPHQL_AUTO = {
       'METRICS': {
           'BACKEND': 'django_graphql_auto.metrics.backends.PrometheusBackend',
           'PROMETHEUS': {
               'ENDPOINT': '/metrics/',
               'NAMESPACE': 'django_graphql_auto',
               'LABELS': {
                   'service': 'graphql-api',
                   'environment': 'production',
               }
           }
       }
   }

InfluxDB Backend
~~~~~~~~~~~~~~~~

Store metrics in InfluxDB:

.. code-block:: python

   GRAPHQL_AUTO = {
       'METRICS': {
           'BACKEND': 'django_graphql_auto.metrics.backends.InfluxDBBackend',
           'INFLUXDB': {
               'HOST': 'localhost',
               'PORT': 8086,
               'DATABASE': 'graphql_metrics',
               'USERNAME': 'admin',
               'PASSWORD': 'password',
           }
       }
   }

Database Backend
~~~~~~~~~~~~~~~~

Store metrics in Django database:

.. code-block:: python

   GRAPHQL_AUTO = {
       'METRICS': {
           'BACKEND': 'django_graphql_auto.metrics.backends.DatabaseBackend',
           'DATABASE': {
               'TABLE_PREFIX': 'graphql_metrics_',
               'BATCH_SIZE': 1000,
               'FLUSH_INTERVAL': 60,  # seconds
           }
       }
   }

API Endpoints
-------------

Metrics API
~~~~~~~~~~~

**GET /metrics/**

Prometheus-formatted metrics:

.. code-block:: http

   GET /metrics/ HTTP/1.1
   Host: example.com
   
   HTTP/1.1 200 OK
   Content-Type: text/plain
   
   # HELP graphql_requests_total Total GraphQL requests
   # TYPE graphql_requests_total counter
   graphql_requests_total{method="POST",status="200"} 1234

**GET /metrics/json/**

JSON-formatted metrics:

.. code-block:: http

   GET /metrics/json/ HTTP/1.1
   Host: example.com
   
   HTTP/1.1 200 OK
   Content-Type: application/json
   
   {
       "timestamp": "2024-01-15T10:30:00Z",
       "metrics": {
           "requests_total": 1234,
           "average_response_time": 0.245,
           "error_rate": 0.02
       }
   }

Real-time Metrics
-----------------

WebSocket Metrics
~~~~~~~~~~~~~~~~~

Stream real-time metrics via WebSocket:

.. code-block:: python

   # Enable real-time metrics
   GRAPHQL_AUTO = {
       'METRICS': {
           'REAL_TIME': {
               'ENABLED': True,
               'WEBSOCKET_ENDPOINT': '/ws/metrics/',
               'UPDATE_INTERVAL': 5,  # seconds
           }
       }
   }

Live Dashboard
~~~~~~~~~~~~~~

Built-in metrics dashboard:

.. code-block:: python

   # urls.py
   from django_graphql_auto.metrics.views import MetricsDashboardView
   
   urlpatterns = [
       path('metrics/dashboard/', MetricsDashboardView.as_view()),
   ]

Visualization
-------------

Grafana Integration
~~~~~~~~~~~~~~~~~~~

Pre-built Grafana dashboards:

.. code-block:: json

   {
       "dashboard": {
           "title": "Django GraphQL Auto Metrics",
           "panels": [
               {
                   "title": "Request Rate",
                   "type": "graph",
                   "targets": [
                       {
                           "expr": "rate(graphql_requests_total[5m])"
                       }
                   ]
               }
           ]
       }
   }

Custom Visualizations
~~~~~~~~~~~~~~~~~~~~~

Create custom metric visualizations:

.. code-block:: python

   from django_graphql_auto.metrics.visualizations import MetricChart
   
   class CustomMetricChart(MetricChart):
       def get_data(self, time_range):
           # Return chart data
           return {
               'labels': ['Jan', 'Feb', 'Mar'],
               'datasets': [{
                   'label': 'Requests',
                   'data': [100, 200, 150]
               }]
           }

Monitoring Integration
----------------------

Prometheus + Grafana
~~~~~~~~~~~~~~~~~~~~~

Complete monitoring stack setup:

.. code-block:: yaml

   # docker-compose.yml
   version: '3.8'
   services:
     prometheus:
       image: prom/prometheus
       ports:
         - "9090:9090"
       volumes:
         - ./prometheus.yml:/etc/prometheus/prometheus.yml
     
     grafana:
       image: grafana/grafana
       ports:
         - "3000:3000"
       environment:
         - GF_SECURITY_ADMIN_PASSWORD=admin

DataDog Integration
~~~~~~~~~~~~~~~~~~~

Send metrics to DataDog:

.. code-block:: python

   GRAPHQL_AUTO = {
       'METRICS': {
           'BACKEND': 'django_graphql_auto.metrics.backends.DataDogBackend',
           'DATADOG': {
               'API_KEY': 'your-api-key',
               'APP_KEY': 'your-app-key',
               'TAGS': ['env:production', 'service:graphql'],
           }
       }
   }

Performance Analysis
--------------------

Query Analysis
~~~~~~~~~~~~~~

Analyze query performance patterns:

.. code-block:: python

   from django_graphql_auto.metrics.analysis import QueryAnalyzer
   
   analyzer = QueryAnalyzer()
   
   # Analyze slow queries
   slow_queries = analyzer.get_slow_queries(threshold=1.0)
   
   # Get query complexity distribution
   complexity_stats = analyzer.get_complexity_distribution()
   
   # Identify N+1 query problems
   n_plus_one_issues = analyzer.detect_n_plus_one_queries()

Trend Analysis
~~~~~~~~~~~~~~

Identify performance trends:

.. code-block:: python

   from django_graphql_auto.metrics.analysis import TrendAnalyzer
   
   trend_analyzer = TrendAnalyzer()
   
   # Analyze response time trends
   response_time_trend = trend_analyzer.analyze_response_times(
       time_range='7d'
   )
   
   # Detect anomalies
   anomalies = trend_analyzer.detect_anomalies(
       metric='request_rate',
       sensitivity=0.95
   )

Alerting
--------

Metric-based Alerts
~~~~~~~~~~~~~~~~~~~

Set up alerts based on metrics:

.. code-block:: python

   from django_graphql_auto.metrics.alerts import MetricAlert
   
   # High error rate alert
   error_rate_alert = MetricAlert(
       name='high_error_rate',
       metric='graphql_errors_total',
       condition='rate > 0.05',
       duration='5m',
       severity='critical'
   )
   
   # Slow response time alert
   response_time_alert = MetricAlert(
       name='slow_response_time',
       metric='graphql_request_duration_seconds',
       condition='p95 > 2.0',
       duration='10m',
       severity='warning'
   )

Alert Handlers
~~~~~~~~~~~~~~

Configure alert notification handlers:

.. code-block:: python

   GRAPHQL_AUTO = {
       'METRICS': {
           'ALERTS': {
               'HANDLERS': [
                   {
                       'type': 'email',
                       'config': {
                           'recipients': ['admin@example.com'],
                           'smtp_server': 'smtp.example.com'
                       }
                   },
                   {
                       'type': 'slack',
                       'config': {
                           'webhook_url': 'https://hooks.slack.com/...',
                           'channel': '#alerts'
                       }
                   }
               ]
           }
       }
   }

Best Practices
--------------

1. **Selective Monitoring**: Monitor what matters most to your application
2. **Appropriate Granularity**: Balance detail with performance impact
3. **Regular Review**: Regularly review and adjust metric collection
4. **Alert Tuning**: Fine-tune alerts to reduce noise
5. **Historical Analysis**: Use historical data for capacity planning
6. **Performance Impact**: Monitor the performance impact of metrics collection

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**High memory usage from metrics collection**:

.. code-block:: python

   GRAPHQL_AUTO = {
       'METRICS': {
           'SAMPLING_RATE': 0.1,  # Sample 10% of requests
           'BATCH_SIZE': 100,
           'FLUSH_INTERVAL': 30,
       }
   }

**Missing metrics data**:

.. code-block:: python

   # Check metric collection is enabled
   GRAPHQL_AUTO = {
       'METRICS': {
           'ENABLED': True,
           'DEBUG': True,  # Enable debug logging
       }
   }

**Slow metric queries**:

.. code-block:: python

   # Optimize database backend
   GRAPHQL_AUTO = {
       'METRICS': {
           'DATABASE': {
               'USE_INDEXES': True,
               'PARTITION_BY_DATE': True,
           }
       }
   }

---

*Last Updated: January 2024*