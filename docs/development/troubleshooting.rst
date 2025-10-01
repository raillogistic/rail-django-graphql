Development Troubleshooting
==========================

This guide helps developers troubleshoot common issues when working with Django GraphQL Auto.

.. contents:: Table of Contents
   :local:
   :depth: 2

Troubleshooting Philosophy
-------------------------

Our troubleshooting approach follows these principles:

* **Systematic Investigation**: Follow a structured approach to identify root causes
* **Documentation First**: Document solutions for future reference
* **Community Support**: Share knowledge and help others
* **Continuous Improvement**: Learn from issues to prevent recurrence

Common Development Issues
------------------------

Schema Generation Problems
~~~~~~~~~~~~~~~~~~~~~~~~~

**Issue**: Schema not generating correctly

.. code-block:: python

   # Check model registration
   from rail_django_graphql.registry import registry
   print(registry.get_registered_models())

   # Verify model configuration
   class MyModel(models.Model):
       class Meta:
           graphql_auto = True  # Ensure this is set

**Issue**: Missing fields in schema

.. code-block:: python

   # Check field exclusions
   class MyModel(models.Model):
       sensitive_field = models.CharField(max_length=100)
       
       class Meta:
           graphql_auto = True
           graphql_exclude_fields = ['sensitive_field']

**Issue**: Relationship fields not working

.. code-block:: python

   # Ensure related models are registered
   class Author(models.Model):
       name = models.CharField(max_length=100)
       
       class Meta:
           graphql_auto = True

   class Book(models.Model):
       title = models.CharField(max_length=200)
       author = models.ForeignKey(Author, on_delete=models.CASCADE)
       
       class Meta:
           graphql_auto = True

Query and Mutation Issues
~~~~~~~~~~~~~~~~~~~~~~~~~

**Issue**: Queries returning unexpected results

.. code-block:: python

   # Debug query execution
   import logging
   logging.basicConfig(level=logging.DEBUG)
   
   # Enable SQL logging
   LOGGING = {
       'version': 1,
       'handlers': {
           'console': {
               'class': 'logging.StreamHandler',
           },
       },
       'loggers': {
           'django.db.backends': {
               'handlers': ['console'],
               'level': 'DEBUG',
           },
       },
   }

**Issue**: Mutations not working

.. code-block:: python

   # Check permissions
   class MyModel(models.Model):
       class Meta:
           graphql_auto = True
           graphql_permissions = {
               'create': ['auth.add_mymodel'],
               'update': ['auth.change_mymodel'],
               'delete': ['auth.delete_mymodel'],
           }

**Issue**: N+1 query problems

.. code-block:: python

   # Use select_related and prefetch_related
   from rail_django_graphql.decorators import graphql_query
   
   @graphql_query
   def optimized_books(info):
       return Book.objects.select_related('author').prefetch_related('tags')

Performance Issues
~~~~~~~~~~~~~~~~~

**Issue**: Slow query performance

.. code-block:: python

   # Enable query analysis
   GRAPHQL_AUTO = {
       'ENABLE_QUERY_ANALYSIS': True,
       'MAX_QUERY_COMPLEXITY': 1000,
       'MAX_QUERY_DEPTH': 10,
   }

**Issue**: Memory usage problems

.. code-block:: python

   # Implement pagination
   from rail_django_graphql.pagination import CursorPagination
   
   class BookConnection(CursorPagination):
       class Meta:
           model = Book
           page_size = 20

**Issue**: Database connection issues

.. code-block:: python

   # Check connection settings
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'CONN_MAX_AGE': 600,
           'OPTIONS': {
               'MAX_CONNS': 20,
           }
       }
   }

Authentication and Authorization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Issue**: Authentication not working

.. code-block:: python

   # Check middleware configuration
   MIDDLEWARE = [
       'django.middleware.security.SecurityMiddleware',
       'django.contrib.sessions.middleware.SessionMiddleware',
       'django.contrib.auth.middleware.AuthenticationMiddleware',
       'rail_django_graphql.middleware.GraphQLAuthMiddleware',
   ]

**Issue**: Permission denied errors

.. code-block:: python

   # Debug permissions
   def check_user_permissions(user, model, action):
       required_perm = f"{model._meta.app_label}.{action}_{model._meta.model_name}"
       has_perm = user.has_perm(required_perm)
       print(f"User {user} has permission {required_perm}: {has_perm}")
       return has_perm

Testing Issues
~~~~~~~~~~~~~

**Issue**: Tests failing unexpectedly

.. code-block:: python

   # Use proper test database settings
   if 'test' in sys.argv:
       DATABASES['default'] = {
           'ENGINE': 'django.db.backends.sqlite3',
           'NAME': ':memory:'
       }

**Issue**: GraphQL client setup in tests

.. code-block:: python

   from graphene.test import Client
   from rail_django_graphql.schema import schema
   
   def test_query():
       client = Client(schema)
       result = client.execute('''
           query {
               allBooks {
                   edges {
                       node {
                           title
                       }
                   }
               }
           }
       ''')
       assert not result.errors

Configuration Issues
~~~~~~~~~~~~~~~~~~~

**Issue**: Settings not being applied

.. code-block:: python

   # Check settings loading
   from django.conf import settings
   print(settings.GRAPHQL_AUTO)
   
   # Ensure proper app ordering
   INSTALLED_APPS = [
       'django.contrib.auth',
       'django.contrib.contenttypes',
       'rail_django_graphql',  # Should be after Django apps
       'your_app',
   ]

**Issue**: URL configuration problems

.. code-block:: python

   # Check URL patterns
   from django.urls import path, include
   
   urlpatterns = [
       path('admin/', admin.site.urls),
       path('graphql/', include('rail_django_graphql.urls')),
   ]

Debugging Tools and Techniques
-----------------------------

Django Debug Toolbar
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Install and configure
   pip install django-debug-toolbar
   
   INSTALLED_APPS = [
       'debug_toolbar',
       # ... other apps
   ]
   
   MIDDLEWARE = [
       'debug_toolbar.middleware.DebugToolbarMiddleware',
       # ... other middleware
   ]

GraphQL Playground
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Enable in development
   GRAPHQL_AUTO = {
       'ENABLE_GRAPHIQL': True,
       'ENABLE_PLAYGROUND': True,
   }

Logging Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'formatters': {
           'verbose': {
               'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
               'style': '{',
           },
       },
       'handlers': {
           'file': {
               'level': 'DEBUG',
               'class': 'logging.FileHandler',
               'filename': 'debug.log',
               'formatter': 'verbose',
           },
       },
       'loggers': {
           'rail_django_graphql': {
               'handlers': ['file'],
               'level': 'DEBUG',
               'propagate': True,
           },
       },
   }

Error Analysis
-------------

Common Error Messages
~~~~~~~~~~~~~~~~~~~

**"Model not registered"**

.. code-block:: python

   # Solution: Register the model
   from rail_django_graphql.registry import registry
   registry.register(MyModel)

**"Permission denied"**

.. code-block:: python

   # Solution: Check user permissions
   user.user_permissions.add(
       Permission.objects.get(codename='add_mymodel')
   )

**"Field does not exist"**

.. code-block:: python

   # Solution: Check field name and model
   class MyModel(models.Model):
       correct_field_name = models.CharField(max_length=100)

**"Circular import"**

.. code-block:: python

   # Solution: Use string references
   class MyModel(models.Model):
       related = models.ForeignKey('app.OtherModel', on_delete=models.CASCADE)

Stack Trace Analysis
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import traceback
   
   try:
       # Your code here
       pass
   except Exception as e:
       print(f"Error: {e}")
       traceback.print_exc()

Performance Debugging
--------------------

Query Analysis
~~~~~~~~~~~~~

.. code-block:: python

   from django.db import connection
   from django.test.utils import override_settings
   
   @override_settings(DEBUG=True)
   def analyze_queries():
       connection.queries_log.clear()
       # Execute your GraphQL query
       print(f"Number of queries: {len(connection.queries)}")
       for query in connection.queries:
           print(f"Query: {query['sql']}")
           print(f"Time: {query['time']}")

Memory Profiling
~~~~~~~~~~~~~~~

.. code-block:: python

   import tracemalloc
   
   tracemalloc.start()
   
   # Your code here
   
   current, peak = tracemalloc.get_traced_memory()
   print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
   print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
   tracemalloc.stop()

Environment-Specific Issues
--------------------------

Development Environment
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Common development settings
   DEBUG = True
   ALLOWED_HOSTS = ['localhost', '127.0.0.1']
   
   # Database for development
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.sqlite3',
           'NAME': BASE_DIR / 'db.sqlite3',
       }
   }

Production Environment
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Production checklist
   DEBUG = False
   ALLOWED_HOSTS = ['your-domain.com']
   
   # Security settings
   SECURE_SSL_REDIRECT = True
   SECURE_HSTS_SECONDS = 31536000
   
   # Database connection pooling
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'CONN_MAX_AGE': 600,
       }
   }

Docker Environment
~~~~~~~~~~~~~~~~~

.. code-block:: dockerfile

   # Common Docker issues
   FROM python:3.9
   
   # Install system dependencies
   RUN apt-get update && apt-get install -y \
       postgresql-client \
       && rm -rf /var/lib/apt/lists/*
   
   # Set environment variables
   ENV PYTHONUNBUFFERED=1
   ENV DJANGO_SETTINGS_MODULE=myproject.settings.production

Getting Help
-----------

Community Resources
~~~~~~~~~~~~~~~~~~

* **GitHub Issues**: Report bugs and request features
* **Stack Overflow**: Ask questions with the ``django-graphql-auto`` tag
* **Discord/Slack**: Join our community chat
* **Documentation**: Check the latest docs at readthedocs.io

Professional Support
~~~~~~~~~~~~~~~~~~~

* **Consulting Services**: Available for complex implementations
* **Priority Support**: Faster response times for critical issues
* **Custom Development**: Tailored solutions for specific needs

Reporting Issues
~~~~~~~~~~~~~~~

When reporting issues, include:

1. **Environment Information**:
   - Python version
   - Django version
   - Package version
   - Operating system

2. **Minimal Reproducible Example**:
   - Simplified code that demonstrates the issue
   - Sample data if relevant
   - Expected vs actual behavior

3. **Error Messages**:
   - Full stack traces
   - Log output
   - Console errors

4. **Configuration**:
   - Relevant settings
   - Model definitions
   - URL patterns

Best Practices for Troubleshooting
----------------------------------

Systematic Approach
~~~~~~~~~~~~~~~~~~

1. **Reproduce the Issue**: Create a minimal test case
2. **Isolate the Problem**: Remove unnecessary complexity
3. **Check Documentation**: Review relevant guides and examples
4. **Search Existing Issues**: Look for similar problems
5. **Test Solutions**: Verify fixes work as expected
6. **Document the Solution**: Help others with similar issues

Prevention Strategies
~~~~~~~~~~~~~~~~~~~

* **Code Reviews**: Catch issues before they reach production
* **Automated Testing**: Comprehensive test coverage
* **Monitoring**: Track application health and performance
* **Documentation**: Keep implementation details up to date
* **Version Control**: Use proper branching and tagging strategies

Continuous Improvement
~~~~~~~~~~~~~~~~~~~~~

* **Post-Mortem Analysis**: Learn from production issues
* **Knowledge Sharing**: Document solutions and patterns
* **Tool Enhancement**: Improve debugging and monitoring tools
* **Team Training**: Keep skills and knowledge current