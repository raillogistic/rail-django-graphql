Debugging
=========

Comprehensive debugging guide for Django GraphQL Auto development and troubleshooting.

Overview
--------

Debugging GraphQL applications requires understanding both Django and GraphQL-specific concepts. This guide provides tools, techniques, and best practices for debugging Django GraphQL Auto applications.

Debugging Philosophy
--------------------

**Our Debugging Approach:**

1. **Systematic Investigation**: Follow a structured approach to identify issues
2. **Logging First**: Use comprehensive logging before diving into debuggers
3. **Reproduce Consistently**: Create minimal reproducible examples
4. **Test-Driven Debugging**: Write tests that expose the bug
5. **Documentation**: Document solutions for future reference

**Debugging Levels:**

.. code-block:: text

   ┌─────────────────────┐
   │   Application       │  ← Business logic issues
   │     Level           │
   ├─────────────────────┤
   │   GraphQL           │  ← Schema, resolver issues
   │     Level           │
   ├─────────────────────┤
   │   Django            │  ← ORM, middleware issues
   │     Level           │
   ├─────────────────────┤
   │   Database          │  ← Query performance, data issues
   │     Level           │
   └─────────────────────┘

Development Environment Setup
-----------------------------

Debug Configuration
~~~~~~~~~~~~~~~~~~~

**Django Debug Settings:**

.. code-block:: python

   # settings/debug.py
   from .base import *
   
   DEBUG = True
   TEMPLATE_DEBUG = True
   
   # Enable Django Debug Toolbar
   INSTALLED_APPS += [
       'debug_toolbar',
       'django_extensions',
   ]
   
   MIDDLEWARE = [
       'debug_toolbar.middleware.DebugToolbarMiddleware',
   ] + MIDDLEWARE
   
   # Debug Toolbar Configuration
   DEBUG_TOOLBAR_CONFIG = {
       'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
       'SHOW_COLLAPSED': True,
       'SHOW_TEMPLATE_CONTEXT': True,
   }
   
   # GraphQL Auto Debug Settings
   GRAPHQL_AUTO = {
       'DEBUG': True,
       'ENABLE_QUERY_LOGGING': True,
       'ENABLE_PERFORMANCE_MONITORING': True,
       'LOG_LEVEL': 'DEBUG',
       'INTROSPECTION': True,  # Enable in development only
   }
   
   # Database Debug Settings
   DATABASES['default']['OPTIONS'] = {
       'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
       'charset': 'utf8mb4',
   }
   
   # Logging Configuration
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'formatters': {
           'verbose': {
               'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
               'style': '{',
           },
           'simple': {
               'format': '{levelname} {message}',
               'style': '{',
           },
       },
       'handlers': {
           'console': {
               'class': 'logging.StreamHandler',
               'formatter': 'verbose',
           },
           'file': {
               'class': 'logging.FileHandler',
               'filename': 'debug.log',
               'formatter': 'verbose',
           },
       },
       'loggers': {
           'django_graphql_auto': {
               'handlers': ['console', 'file'],
               'level': 'DEBUG',
               'propagate': True,
           },
           'django.db.backends': {
               'handlers': ['console'],
               'level': 'DEBUG',
               'propagate': False,
           },
       },
   }

**IDE Configuration (VS Code):**

.. code-block:: json

   // .vscode/launch.json
   {
       "version": "0.2.0",
       "configurations": [
           {
               "name": "Django Debug",
               "type": "python",
               "request": "launch",
               "program": "${workspaceFolder}/manage.py",
               "args": ["runserver", "0.0.0.0:8000"],
               "django": true,
               "env": {
                   "DJANGO_SETTINGS_MODULE": "myproject.settings.debug"
               },
               "console": "integratedTerminal",
               "justMyCode": false
           },
           {
               "name": "Django Test Debug",
               "type": "python",
               "request": "launch",
               "module": "pytest",
               "args": ["tests/", "-v", "--tb=short"],
               "env": {
                   "DJANGO_SETTINGS_MODULE": "myproject.settings.test"
               },
               "console": "integratedTerminal",
               "justMyCode": false
           }
       ]
   }

Logging and Monitoring
----------------------

GraphQL Query Logging
~~~~~~~~~~~~~~~~~~~~~~

**Custom Query Logger:**

.. code-block:: python

   # django_graphql_auto/logging.py
   import logging
   import time
   import json
   from django.conf import settings
   
   logger = logging.getLogger(__name__)
   
   class GraphQLQueryLogger:
       """Logger for GraphQL queries and performance monitoring."""
       
       def __init__(self):
           self.enabled = getattr(settings, 'GRAPHQL_AUTO', {}).get('ENABLE_QUERY_LOGGING', False)
       
       def log_query(self, query, variables=None, context=None, execution_time=None):
           """Log GraphQL query with context and performance data."""
           if not self.enabled:
               return
           
           log_data = {
               'query': query,
               'variables': variables or {},
               'execution_time_ms': execution_time,
               'user': getattr(context, 'user', None),
               'timestamp': time.time(),
           }
           
           if execution_time and execution_time > 1000:  # Log slow queries
               logger.warning(f"Slow GraphQL query detected: {execution_time}ms", extra=log_data)
           else:
               logger.info("GraphQL query executed", extra=log_data)
       
       def log_error(self, query, error, variables=None, context=None):
           """Log GraphQL query errors."""
           log_data = {
               'query': query,
               'variables': variables or {},
               'error': str(error),
               'error_type': type(error).__name__,
               'user': getattr(context, 'user', None),
               'timestamp': time.time(),
           }
           
           logger.error(f"GraphQL query error: {error}", extra=log_data)

**Query Performance Middleware:**

.. code-block:: python

   # django_graphql_auto/middleware.py
   import time
   import logging
   from django.utils.deprecation import MiddlewareMixin
   
   logger = logging.getLogger(__name__)
   
   class GraphQLPerformanceMiddleware(MiddlewareMixin):
       """Middleware to monitor GraphQL query performance."""
       
       def process_request(self, request):
           if request.path == '/graphql/':
               request._graphql_start_time = time.time()
       
       def process_response(self, request, response):
           if hasattr(request, '_graphql_start_time'):
               execution_time = (time.time() - request._graphql_start_time) * 1000
               
               # Log performance data
               logger.info(f"GraphQL request completed in {execution_time:.2f}ms", extra={
                   'execution_time_ms': execution_time,
                   'status_code': response.status_code,
                   'user': getattr(request, 'user', None),
               })
               
               # Add performance header
               response['X-GraphQL-Execution-Time'] = f"{execution_time:.2f}ms"
           
           return response

Database Query Debugging
~~~~~~~~~~~~~~~~~~~~~~~~~

**Query Analysis Tools:**

.. code-block:: python

   # django_graphql_auto/debug/db.py
   import logging
   from django.db import connection
   from django.conf import settings
   
   logger = logging.getLogger(__name__)
   
   class DatabaseQueryAnalyzer:
       """Analyze database queries for performance issues."""
       
       def __init__(self):
           self.enabled = settings.DEBUG
       
       def analyze_queries(self):
           """Analyze recent database queries."""
           if not self.enabled:
               return
           
           queries = connection.queries
           total_time = sum(float(q['time']) for q in queries)
           
           logger.info(f"Database queries: {len(queries)}, Total time: {total_time:.3f}s")
           
           # Find slow queries
           slow_queries = [q for q in queries if float(q['time']) > 0.1]
           if slow_queries:
               logger.warning(f"Found {len(slow_queries)} slow queries (>100ms)")
               for query in slow_queries:
                   logger.warning(f"Slow query ({query['time']}s): {query['sql'][:200]}...")
       
       def detect_n_plus_one(self):
           """Detect potential N+1 query problems."""
           queries = connection.queries
           query_patterns = {}
           
           for query in queries:
               # Normalize query by removing specific values
               normalized = self._normalize_query(query['sql'])
               query_patterns[normalized] = query_patterns.get(normalized, 0) + 1
           
           # Find patterns that repeat many times
           for pattern, count in query_patterns.items():
               if count > 10:  # Threshold for N+1 detection
                   logger.warning(f"Potential N+1 query detected: {count} similar queries")
                   logger.warning(f"Pattern: {pattern[:200]}...")
       
       def _normalize_query(self, sql):
           """Normalize SQL query by removing specific values."""
           import re
           # Remove specific IDs and values
           normalized = re.sub(r'\b\d+\b', 'N', sql)
           normalized = re.sub(r"'[^']*'", "'VALUE'", normalized)
           return normalized

Error Handling and Debugging
-----------------------------

GraphQL Error Debugging
~~~~~~~~~~~~~~~~~~~~~~~~

**Custom Error Handler:**

.. code-block:: python

   # django_graphql_auto/errors.py
   import logging
   import traceback
   from graphql import GraphQLError
   from django.conf import settings
   
   logger = logging.getLogger(__name__)
   
   class GraphQLErrorHandler:
       """Handle and format GraphQL errors for debugging."""
       
       def __init__(self):
           self.debug = settings.DEBUG
       
       def format_error(self, error):
           """Format GraphQL error with debugging information."""
           formatted_error = {
               'message': str(error),
               'locations': getattr(error, 'locations', None),
               'path': getattr(error, 'path', None),
           }
           
           if self.debug:
               # Add debugging information in development
               formatted_error.update({
                   'exception': type(error).__name__,
                   'traceback': traceback.format_exc() if hasattr(error, '__traceback__') else None,
               })
           
           # Log the error
           logger.error(f"GraphQL Error: {error}", extra={
               'error_type': type(error).__name__,
               'locations': getattr(error, 'locations', None),
               'path': getattr(error, 'path', None),
           })
           
           return formatted_error
       
       def handle_resolver_error(self, error, info):
           """Handle errors that occur in resolvers."""
           logger.error(f"Resolver error in {info.field_name}: {error}", extra={
               'field_name': info.field_name,
               'parent_type': str(info.parent_type),
               'error_type': type(error).__name__,
           })
           
           if self.debug:
               # Re-raise with full traceback in development
               raise error
           else:
               # Return user-friendly error in production
               raise GraphQLError("An error occurred while processing your request")

**Exception Middleware:**

.. code-block:: python

   # django_graphql_auto/middleware/exceptions.py
   import logging
   from graphql import MiddlewareManager
   
   logger = logging.getLogger(__name__)
   
   class ExceptionMiddleware:
       """Middleware to catch and log exceptions in GraphQL execution."""
       
       def resolve(self, next, root, info, **args):
           try:
               return next(root, info, **args)
           except Exception as error:
               # Log the exception with context
               logger.exception(f"Exception in resolver {info.field_name}", extra={
                   'field_name': info.field_name,
                   'parent_type': str(info.parent_type),
                   'args': args,
                   'user': getattr(info.context, 'user', None),
               })
               
               # Re-raise the exception
               raise

Schema Debugging
~~~~~~~~~~~~~~~~~

**Schema Validation Tools:**

.. code-block:: python

   # django_graphql_auto/debug/schema.py
   import logging
   from graphql import validate_schema, build_schema
   from django_graphql_auto.schema import SchemaGenerator
   
   logger = logging.getLogger(__name__)
   
   class SchemaDebugger:
       """Debug GraphQL schema generation and validation."""
       
       def __init__(self):
           self.generator = SchemaGenerator()
       
       def validate_generated_schema(self, models):
           """Validate the generated GraphQL schema."""
           try:
               schema = self.generator.generate_schema(models)
               errors = validate_schema(schema)
               
               if errors:
                   logger.error(f"Schema validation errors: {len(errors)}")
                   for error in errors:
                       logger.error(f"Schema error: {error}")
                   return False
               else:
                   logger.info("Schema validation passed")
                   return True
           except Exception as error:
               logger.exception(f"Schema generation failed: {error}")
               return False
       
       def analyze_schema_complexity(self, schema):
           """Analyze schema complexity and potential issues."""
           type_map = schema.type_map
           
           # Count types
           object_types = [t for t in type_map.values() if hasattr(t, 'fields')]
           scalar_types = [t for t in type_map.values() if not hasattr(t, 'fields')]
           
           logger.info(f"Schema analysis: {len(object_types)} object types, {len(scalar_types)} scalar types")
           
           # Find deeply nested types
           for type_name, type_obj in type_map.items():
               if hasattr(type_obj, 'fields'):
                   self._analyze_type_depth(type_name, type_obj, max_depth=5)
       
       def _analyze_type_depth(self, type_name, type_obj, current_depth=0, max_depth=5):
           """Analyze the depth of type relationships."""
           if current_depth > max_depth:
               logger.warning(f"Deep nesting detected in type {type_name} (depth > {max_depth})")
               return
           
           # Analyze field types recursively
           for field_name, field in type_obj.fields.items():
               field_type = field.type
               # Continue analysis for object types
               if hasattr(field_type, 'fields'):
                   self._analyze_type_depth(f"{type_name}.{field_name}", field_type, current_depth + 1, max_depth)

Interactive Debugging Tools
---------------------------

GraphQL Playground Enhancement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Custom Playground Configuration:**

.. code-block:: python

   # django_graphql_auto/views.py
   from django.shortcuts import render
   from django.conf import settings
   from django.http import JsonResponse
   import json
   
   class EnhancedGraphQLPlayground:
       """Enhanced GraphQL Playground with debugging features."""
       
       def __init__(self):
           self.debug = settings.DEBUG
       
       def render_playground(self, request):
           """Render GraphQL Playground with debugging enhancements."""
           context = {
               'graphql_endpoint': '/graphql/',
               'debug_mode': self.debug,
               'introspection_enabled': self.debug,
               'query_examples': self._get_query_examples(),
               'schema_docs': self._get_schema_documentation(),
           }
           
           return render(request, 'graphql_playground.html', context)
       
       def _get_query_examples(self):
           """Get example queries for debugging."""
           return [
               {
                   'name': 'Get All Users',
                   'query': '''
                   query GetUsers {
                       users {
                           edges {
                               node {
                                   id
                                   username
                                   email
                               }
                           }
                       }
                   }
                   '''
               },
               {
                   'name': 'Get User with Posts',
                   'query': '''
                   query GetUserWithPosts($userId: ID!) {
                       user(id: $userId) {
                           username
                           posts {
                               edges {
                                   node {
                                       title
                                       createdAt
                                   }
                               }
                           }
                       }
                   }
                   ''',
                   'variables': {'userId': '1'}
               }
           ]
       
       def _get_schema_documentation(self):
           """Get schema documentation for debugging."""
           # This would typically introspect the schema
           return {
               'types': ['User', 'Post', 'Category'],
               'queries': ['user', 'users', 'post', 'posts'],
               'mutations': ['createUser', 'updateUser', 'deleteUser'],
           }

Django Debug Toolbar Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Custom Debug Panels:**

.. code-block:: python

   # django_graphql_auto/debug/panels.py
   from debug_toolbar.panels import Panel
   from django.template.loader import render_to_string
   from django.utils.translation import gettext_lazy as _
   
   class GraphQLPanel(Panel):
       """Debug toolbar panel for GraphQL queries."""
       
       title = _("GraphQL")
       template = 'debug_toolbar/panels/graphql.html'
       
       def __init__(self, *args, **kwargs):
           super().__init__(*args, **kwargs)
           self.queries = []
       
       def enable_instrumentation(self):
           """Enable instrumentation to collect GraphQL data."""
           # Hook into GraphQL execution to collect query data
           pass
       
       def disable_instrumentation(self):
           """Disable instrumentation."""
           pass
       
       def process_request(self, request):
           """Process the request to collect GraphQL data."""
           self.queries = []
       
       def generate_stats(self, request, response):
           """Generate statistics for the panel."""
           self.record_stats({
               'queries': self.queries,
               'num_queries': len(self.queries),
               'total_time': sum(q.get('execution_time', 0) for q in self.queries),
           })

Command-Line Debugging Tools
----------------------------

Management Commands
~~~~~~~~~~~~~~~~~~~

**Schema Inspection Command:**

.. code-block:: python

   # management/commands/debug_schema.py
   from django.core.management.base import BaseCommand
   from django.apps import apps
   from django_graphql_auto.schema import SchemaGenerator
   from graphql import print_schema
   
   class Command(BaseCommand):
       help = 'Debug GraphQL schema generation'
       
       def add_arguments(self, parser):
           parser.add_argument(
               '--app',
               type=str,
               help='Specific app to analyze'
           )
           parser.add_argument(
               '--model',
               type=str,
               help='Specific model to analyze'
           )
           parser.add_argument(
               '--output',
               type=str,
               choices=['schema', 'types', 'queries', 'mutations'],
               default='schema',
               help='Type of output to generate'
           )
       
       def handle(self, *args, **options):
           generator = SchemaGenerator()
           
           # Get models to analyze
           if options['app']:
               app_config = apps.get_app_config(options['app'])
               models = app_config.get_models()
           else:
               models = apps.get_models()
           
           if options['model']:
               models = [m for m in models if m.__name__ == options['model']]
           
           # Generate schema
           schema = generator.generate_schema(models)
           
           # Output based on option
           if options['output'] == 'schema':
               self.stdout.write(print_schema(schema))
           elif options['output'] == 'types':
               self._print_types(schema)
           elif options['output'] == 'queries':
               self._print_queries(schema)
           elif options['output'] == 'mutations':
               self._print_mutations(schema)
       
       def _print_types(self, schema):
           """Print all types in the schema."""
           for type_name, type_obj in schema.type_map.items():
               if not type_name.startswith('__'):
                   self.stdout.write(f"Type: {type_name}")
                   if hasattr(type_obj, 'fields'):
                       for field_name, field in type_obj.fields.items():
                           self.stdout.write(f"  {field_name}: {field.type}")
       
       def _print_queries(self, schema):
           """Print all queries in the schema."""
           query_type = schema.query_type
           if query_type:
               for field_name, field in query_type.fields.items():
                   self.stdout.write(f"Query: {field_name} -> {field.type}")
       
       def _print_mutations(self, schema):
           """Print all mutations in the schema."""
           mutation_type = schema.mutation_type
           if mutation_type:
               for field_name, field in mutation_type.fields.items():
                   self.stdout.write(f"Mutation: {field_name} -> {field.type}")

**Query Performance Command:**

.. code-block:: python

   # management/commands/analyze_queries.py
   from django.core.management.base import BaseCommand
   from django.db import connection
   import json
   
   class Command(BaseCommand):
       help = 'Analyze database query performance'
       
       def add_arguments(self, parser):
           parser.add_argument(
               '--threshold',
               type=float,
               default=0.1,
               help='Slow query threshold in seconds'
           )
           parser.add_argument(
               '--output',
               type=str,
               choices=['summary', 'detailed', 'json'],
               default='summary',
               help='Output format'
           )
       
       def handle(self, *args, **options):
           # Reset query log
           connection.queries_log.clear()
           
           # Run a sample GraphQL query to collect data
           self.stdout.write("Run your GraphQL queries now, then press Ctrl+C to analyze...")
           
           try:
               input()  # Wait for user input
           except KeyboardInterrupt:
               pass
           
           # Analyze queries
           queries = connection.queries
           slow_queries = [q for q in queries if float(q['time']) > options['threshold']]
           
           if options['output'] == 'json':
               self.stdout.write(json.dumps({
                   'total_queries': len(queries),
                   'slow_queries': len(slow_queries),
                   'queries': queries
               }, indent=2))
           elif options['output'] == 'detailed':
               self._print_detailed_analysis(queries, slow_queries)
           else:
               self._print_summary(queries, slow_queries)
       
       def _print_summary(self, queries, slow_queries):
           """Print summary analysis."""
           total_time = sum(float(q['time']) for q in queries)
           avg_time = total_time / len(queries) if queries else 0
           
           self.stdout.write(f"Query Analysis Summary:")
           self.stdout.write(f"  Total queries: {len(queries)}")
           self.stdout.write(f"  Slow queries: {len(slow_queries)}")
           self.stdout.write(f"  Total time: {total_time:.3f}s")
           self.stdout.write(f"  Average time: {avg_time:.3f}s")
       
       def _print_detailed_analysis(self, queries, slow_queries):
           """Print detailed analysis."""
           self._print_summary(queries, slow_queries)
           
           if slow_queries:
               self.stdout.write("\nSlow Queries:")
               for i, query in enumerate(slow_queries, 1):
                   self.stdout.write(f"{i}. Time: {query['time']}s")
                   self.stdout.write(f"   SQL: {query['sql'][:200]}...")

Testing and Debugging Integration
----------------------------------

Test Debugging Strategies
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Debug Test Failures:**

.. code-block:: python

   # tests/debug_helpers.py
   import logging
   from django.test import TestCase
   from django.db import connection
   
   logger = logging.getLogger(__name__)
   
   class DebugTestCase(TestCase):
       """Enhanced TestCase with debugging capabilities."""
       
       def setUp(self):
           super().setUp()
           self.debug_queries = []
           self.start_query_count = len(connection.queries)
       
       def tearDown(self):
           # Log query information
           end_query_count = len(connection.queries)
           queries_executed = end_query_count - self.start_query_count
           
           if queries_executed > 10:  # Threshold for too many queries
               logger.warning(f"Test executed {queries_executed} database queries")
               
           super().tearDown()
       
       def debug_graphql_query(self, query, variables=None):
           """Execute GraphQL query with debugging information."""
           from django.test import Client
           import json
           
           client = Client()
           response = client.post(
               '/graphql/',
               json.dumps({'query': query, 'variables': variables or {}}),
               content_type='application/json'
           )
           
           result = response.json()
           
           # Log query and response for debugging
           logger.debug(f"GraphQL Query: {query}")
           logger.debug(f"Variables: {variables}")
           logger.debug(f"Response: {result}")
           
           if 'errors' in result:
               logger.error(f"GraphQL Errors: {result['errors']}")
           
           return result
       
       def assert_no_graphql_errors(self, result):
           """Assert that GraphQL result contains no errors."""
           if 'errors' in result:
               error_messages = [error['message'] for error in result['errors']]
               self.fail(f"GraphQL errors occurred: {error_messages}")

**Debugging Test Data:**

.. code-block:: python

   # tests/debug_factories.py
   import factory
   from factory.django import DjangoModelFactory
   from tests.models import User, Post
   
   class DebugUserFactory(DjangoModelFactory):
       """User factory with debugging information."""
       
       class Meta:
           model = User
       
       username = factory.Sequence(lambda n: f"debug_user_{n}")
       email = factory.LazyAttribute(lambda obj: f"{obj.username}@debug.com")
       
       @classmethod
       def _create(cls, model_class, *args, **kwargs):
           """Override create to add debugging."""
           instance = super()._create(model_class, *args, **kwargs)
           print(f"Created debug user: {instance.username} (ID: {instance.id})")
           return instance

Performance Debugging
----------------------

Query Optimization
~~~~~~~~~~~~~~~~~~

**Query Analysis Tools:**

.. code-block:: python

   # django_graphql_auto/debug/performance.py
   import time
   import logging
   from django.db import connection
   from contextlib import contextmanager
   
   logger = logging.getLogger(__name__)
   
   @contextmanager
   def query_debugger(operation_name="Unknown"):
       """Context manager to debug database queries."""
       start_queries = len(connection.queries)
       start_time = time.time()
       
       yield
       
       end_queries = len(connection.queries)
       end_time = time.time()
       
       queries_executed = end_queries - start_queries
       execution_time = (end_time - start_time) * 1000
       
       logger.info(f"{operation_name}: {queries_executed} queries in {execution_time:.2f}ms")
       
       if queries_executed > 5:  # Threshold for too many queries
           logger.warning(f"High query count detected in {operation_name}")
           
           # Log recent queries
           recent_queries = connection.queries[start_queries:end_queries]
           for i, query in enumerate(recent_queries, 1):
               logger.debug(f"Query {i}: {query['sql'][:100]}... ({query['time']}s)")

**Memory Profiling:**

.. code-block:: python

   # django_graphql_auto/debug/memory.py
   import psutil
   import os
   import logging
   from functools import wraps
   
   logger = logging.getLogger(__name__)
   
   def memory_profiler(func):
       """Decorator to profile memory usage of functions."""
       @wraps(func)
       def wrapper(*args, **kwargs):
           process = psutil.Process(os.getpid())
           
           # Get initial memory usage
           initial_memory = process.memory_info().rss / 1024 / 1024  # MB
           
           # Execute function
           result = func(*args, **kwargs)
           
           # Get final memory usage
           final_memory = process.memory_info().rss / 1024 / 1024  # MB
           memory_diff = final_memory - initial_memory
           
           logger.info(f"{func.__name__}: Memory usage {initial_memory:.1f}MB -> {final_memory:.1f}MB (Δ{memory_diff:+.1f}MB)")
           
           if memory_diff > 50:  # Threshold for high memory usage
               logger.warning(f"High memory usage detected in {func.__name__}: {memory_diff:.1f}MB")
           
           return result
       
       return wrapper

Common Debugging Scenarios
---------------------------

Resolver Issues
~~~~~~~~~~~~~~~

**Debugging Resolver Problems:**

.. code-block:: python

   # Common resolver debugging patterns
   
   def debug_resolver(resolver_func):
       """Decorator to debug resolver execution."""
       @wraps(resolver_func)
       def wrapper(self, info, **kwargs):
           logger.debug(f"Executing resolver: {resolver_func.__name__}")
           logger.debug(f"Arguments: {kwargs}")
           logger.debug(f"User: {getattr(info.context, 'user', 'Anonymous')}")
           
           try:
               result = resolver_func(self, info, **kwargs)
               logger.debug(f"Resolver result type: {type(result)}")
               return result
           except Exception as error:
               logger.exception(f"Resolver error in {resolver_func.__name__}: {error}")
               raise
       
       return wrapper
   
   # Usage example
   class UserResolver:
       @debug_resolver
       def resolve_user(self, info, id):
           return User.objects.get(id=id)

Schema Generation Issues
~~~~~~~~~~~~~~~~~~~~~~~~

**Debugging Schema Problems:**

.. code-block:: python

   # Debug schema generation step by step
   
   def debug_schema_generation():
       """Debug schema generation process."""
       from django_graphql_auto.schema import SchemaGenerator
       from django.apps import apps
       
       generator = SchemaGenerator()
       models = apps.get_models()
       
       logger.info(f"Generating schema for {len(models)} models")
       
       for model in models:
           try:
               logger.debug(f"Processing model: {model.__name__}")
               # Generate type for individual model
               model_type = generator.generate_type_for_model(model)
               logger.debug(f"Generated type: {model_type}")
           except Exception as error:
               logger.error(f"Failed to generate type for {model.__name__}: {error}")

Production Debugging
--------------------

Safe Production Debugging
~~~~~~~~~~~~~~~~~~~~~~~~~

**Production-Safe Debug Tools:**

.. code-block:: python

   # django_graphql_auto/debug/production.py
   import logging
   from django.conf import settings
   from django.core.cache import cache
   
   logger = logging.getLogger(__name__)
   
   class ProductionDebugger:
       """Safe debugging tools for production environments."""
       
       def __init__(self):
           self.enabled = getattr(settings, 'PRODUCTION_DEBUG_ENABLED', False)
           self.debug_key = getattr(settings, 'PRODUCTION_DEBUG_KEY', None)
       
       def is_debug_enabled(self, request):
           """Check if debug mode is enabled for this request."""
           if not self.enabled:
               return False
           
           # Check for debug key in headers
           debug_key = request.META.get('HTTP_X_DEBUG_KEY')
           return debug_key == self.debug_key
       
       def log_query_performance(self, query, execution_time, user=None):
           """Log query performance in production."""
           if execution_time > 1000:  # Log slow queries only
               logger.warning(f"Slow query detected: {execution_time}ms", extra={
                   'query_hash': hash(query),  # Don't log full query in production
                   'execution_time': execution_time,
                   'user_id': getattr(user, 'id', None) if user else None,
               })
       
       def capture_error_context(self, error, request):
           """Capture error context for production debugging."""
           context = {
               'error_type': type(error).__name__,
               'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
               'path': request.path,
               'method': request.method,
               'timestamp': time.time(),
           }
           
           # Store in cache for later analysis
           cache_key = f"error_context:{hash(str(error))}"
           cache.set(cache_key, context, timeout=3600)  # 1 hour
           
           return context

---

*This debugging guide provides comprehensive tools and techniques for debugging Django GraphQL Auto applications. Use these tools systematically to identify and resolve issues efficiently.*