Health Checks
=============

Comprehensive health monitoring system for Django GraphQL Auto applications.

Overview
--------

The health check system provides real-time monitoring of your GraphQL application's health status, including database connectivity, external service availability, and system performance metrics.

Basic Health Checks
--------------------

Default Health Endpoint
~~~~~~~~~~~~~~~~~~~~~~~~

Django GraphQL Auto provides a built-in health check endpoint:

.. code-block:: python

   # urls.py
   from django_graphql_auto.health import health_check_view
   
   urlpatterns = [
       path('health/', health_check_view, name='health_check'),
   ]

The endpoint returns a JSON response with health status:

.. code-block:: json

   {
       "status": "healthy",
       "timestamp": "2024-01-15T10:30:00Z",
       "checks": {
           "database": "healthy",
           "cache": "healthy",
           "graphql": "healthy"
       }
   }

Configuration
~~~~~~~~~~~~~

Configure health checks in your Django settings:

.. code-block:: python

   # settings.py
   GRAPHQL_AUTO = {
       'HEALTH_CHECKS': {
           'ENABLED': True,
           'ENDPOINT': '/health/',
           'CHECKS': [
               'django_graphql_auto.health.checks.DatabaseCheck',
               'django_graphql_auto.health.checks.CacheCheck',
               'django_graphql_auto.health.checks.GraphQLCheck',
           ],
           'TIMEOUT': 30,  # seconds
       }
   }

Advanced Health Checks
----------------------

Custom Health Checks
~~~~~~~~~~~~~~~~~~~~~

Create custom health checks for your specific needs:

.. code-block:: python

   # health_checks.py
   from django_graphql_auto.health.base import BaseHealthCheck
   
   class CustomServiceCheck(BaseHealthCheck):
       name = "custom_service"
       
       def check_health(self):
           try:
               # Your custom health check logic
               response = requests.get('https://api.example.com/status')
               if response.status_code == 200:
                   return self.success("Service is available")
               else:
                   return self.error(f"Service returned {response.status_code}")
           except Exception as e:
               return self.error(f"Service check failed: {str(e)}")

Register custom checks:

.. code-block:: python

   # settings.py
   GRAPHQL_AUTO = {
       'HEALTH_CHECKS': {
           'CHECKS': [
               'myapp.health_checks.CustomServiceCheck',
           ]
       }
   }

Database Health Checks
~~~~~~~~~~~~~~~~~~~~~~

Monitor database connectivity and performance:

.. code-block:: python

   from django_graphql_auto.health.checks import DatabaseCheck
   
   class ExtendedDatabaseCheck(DatabaseCheck):
       def check_health(self):
           # Basic connectivity check
           basic_result = super().check_health()
           if not basic_result.is_healthy:
               return basic_result
           
           # Additional performance checks
           try:
               from django.db import connection
               with connection.cursor() as cursor:
                   cursor.execute("SELECT 1")
                   result = cursor.fetchone()
                   
               return self.success("Database is responsive")
           except Exception as e:
               return self.error(f"Database performance issue: {str(e)}")

GraphQL Schema Health
~~~~~~~~~~~~~~~~~~~~~

Verify GraphQL schema integrity:

.. code-block:: python

   from django_graphql_auto.health.checks import GraphQLCheck
   
   class SchemaHealthCheck(GraphQLCheck):
       def check_health(self):
           try:
               from django_graphql_auto.schema import get_schema
               schema = get_schema()
               
               # Validate schema
               if schema and hasattr(schema, 'query'):
                   return self.success("GraphQL schema is valid")
               else:
                   return self.error("GraphQL schema is invalid")
           except Exception as e:
               return self.error(f"Schema validation failed: {str(e)}")

Health Check Results
--------------------

Result Structure
~~~~~~~~~~~~~~~~

Health check results follow a consistent structure:

.. code-block:: python

   {
       "name": "database",
       "status": "healthy",  # healthy, unhealthy, unknown
       "message": "Database connection successful",
       "timestamp": "2024-01-15T10:30:00Z",
       "duration_ms": 45,
       "metadata": {
           "connection_pool_size": 10,
           "active_connections": 3
       }
   }

Status Levels
~~~~~~~~~~~~~

- **healthy**: Check passed successfully
- **unhealthy**: Check failed, requires attention
- **unknown**: Check could not be completed

Monitoring Integration
----------------------

Prometheus Metrics
~~~~~~~~~~~~~~~~~~

Export health check metrics to Prometheus:

.. code-block:: python

   # settings.py
   GRAPHQL_AUTO = {
       'HEALTH_CHECKS': {
           'PROMETHEUS_METRICS': True,
           'METRICS_PREFIX': 'django_graphql_auto_health',
       }
   }

Metrics exported:

- ``health_check_status``: Current health status (0=unhealthy, 1=healthy)
- ``health_check_duration_seconds``: Check execution time
- ``health_check_total``: Total number of checks performed

Automated Monitoring
~~~~~~~~~~~~~~~~~~~~

Set up automated health monitoring:

.. code-block:: python

   # monitoring.py
   from django_graphql_auto.health.monitor import HealthMonitor
   
   monitor = HealthMonitor()
   
   # Schedule periodic health checks
   monitor.schedule_checks(interval=60)  # Every 60 seconds
   
   # Set up alerting
   monitor.add_alert_handler('email', {
       'recipients': ['admin@example.com'],
       'threshold': 'unhealthy'
   })

API Endpoints
-------------

Health Check API
~~~~~~~~~~~~~~~~

**GET /health/**

Returns overall health status:

.. code-block:: http

   GET /health/ HTTP/1.1
   Host: example.com
   
   HTTP/1.1 200 OK
   Content-Type: application/json
   
   {
       "status": "healthy",
       "timestamp": "2024-01-15T10:30:00Z",
       "checks": {
           "database": "healthy",
           "cache": "healthy"
       }
   }

**GET /health/detailed/**

Returns detailed health information:

.. code-block:: http

   GET /health/detailed/ HTTP/1.1
   Host: example.com
   
   HTTP/1.1 200 OK
   Content-Type: application/json
   
   {
       "status": "healthy",
       "timestamp": "2024-01-15T10:30:00Z",
       "checks": [
           {
               "name": "database",
               "status": "healthy",
               "message": "Connection successful",
               "duration_ms": 45
           }
       ]
   }

GraphQL Health Queries
~~~~~~~~~~~~~~~~~~~~~~

Query health status through GraphQL:

.. code-block:: graphql

   query {
       healthStatus {
           status
           timestamp
           checks {
               name
               status
               message
               durationMs
           }
       }
   }

Best Practices
--------------

1. **Comprehensive Coverage**: Include checks for all critical dependencies
2. **Appropriate Timeouts**: Set reasonable timeouts to avoid blocking
3. **Meaningful Messages**: Provide clear, actionable error messages
4. **Regular Testing**: Test health checks regularly in development
5. **Monitoring Integration**: Connect to your monitoring infrastructure
6. **Graceful Degradation**: Handle partial failures appropriately

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Health checks timing out**:

.. code-block:: python

   GRAPHQL_AUTO = {
       'HEALTH_CHECKS': {
           'TIMEOUT': 60,  # Increase timeout
           'ASYNC_CHECKS': True,  # Enable async execution
       }
   }

**Database connection issues**:

.. code-block:: python

   # Check database configuration
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'CONN_MAX_AGE': 600,  # Connection pooling
       }
   }

**Memory usage during checks**:

.. code-block:: python

   GRAPHQL_AUTO = {
       'HEALTH_CHECKS': {
           'CACHE_RESULTS': True,
           'CACHE_TTL': 30,  # Cache results for 30 seconds
       }
   }

---

*Last Updated: January 2024*