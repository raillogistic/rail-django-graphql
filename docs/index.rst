Django GraphQL Auto Documentation
===================================

.. image:: https://img.shields.io/pypi/v/rail-django-graphql
   :target: https://pypi.org/project/rail-django-graphql/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/rail-django-graphql
   :target: https://pypi.org/project/rail-django-graphql/
   :alt: Python versions

.. image:: https://img.shields.io/badge/django-3.2%2B-blue
   :target: https://www.djangoproject.com/
   :alt: Django versions

.. image:: https://img.shields.io/github/license/raillogistic/rail-django-graphql
   :target: https://github.com/raillogistic/rail-django-graphql/blob/main/LICENSE
   :alt: License

A comprehensive Django library for automatic GraphQL schema generation, multi-schema management, and advanced GraphQL features including validation, introspection, debugging, and performance monitoring.

🚀 Overview
-----------

Django GraphQL Auto transforms your Django models into powerful GraphQL APIs with minimal configuration. Whether you're building microservices, multi-tenant applications, or complex APIs with different access levels, this library provides enterprise-grade tools for GraphQL schema management.

✨ Key Benefits
---------------

- **🔧 Zero Configuration**: Works out of the box with sensible defaults
- **🏗️ Multi-Schema Architecture**: Manage multiple GraphQL schemas in a single Django application  
- **🚀 Production Ready**: Thread-safe operations with comprehensive error handling
- **👨‍💻 Developer Friendly**: Rich debugging tools and comprehensive documentation
- **🔌 Extensible**: Plugin architecture for custom functionality
- **📊 Performance Monitoring**: Built-in metrics and performance tracking
- **🔍 Schema Validation**: Comprehensive validation and introspection capabilities

📚 Documentation Contents
-------------------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   setup/installation
   setup/quick-start
   setup/configuration

.. toctree::
   :maxdepth: 2
   :caption: Core Features

   features/multi-schema
   features/schema-registry
   features/auto-discovery
   features/validation
   features/introspection
   features/debugging
   features/performance
   features/security

.. toctree::
   :maxdepth: 2
   :caption: Usage Guide

   usage/basic-usage
   usage/advanced-usage
   usage/schema-management
   usage/authentication
   usage/permissions
   usage/caching
   usage/monitoring

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/core
   api/registry
   api/validation
   api/introspection
   api/debugging
   api/management
   api/rest-api

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples/basic-examples
   examples/advanced-examples
   examples/authentication-examples
   examples/performance-examples
   examples/multi-tenant-examples

.. toctree::
   :maxdepth: 2
   :caption: Migration & Deployment

   migration/from-graphene-django
   migration/single-to-multi-schema
   migration/version-upgrades
   deployment/production
   deployment/docker
   deployment/kubernetes

.. toctree::
   :maxdepth: 2
   :caption: Development

   development/contributing
   development/testing
   development/debugging
   development/performance
   development/troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: Health & Monitoring

   health/health-checks
   health/metrics
   health/monitoring
   health/alerting

.. toctree::
   :maxdepth: 1
   :caption: Project Information

   project/changelog
   project/roadmap
   project/license
   project/support

Quick Installation
------------------

Install Django GraphQL Auto using pip:

.. code-block:: bash

   pip install rail-django-graphql

Add to your Django settings:

.. code-block:: python

   # settings.py
   INSTALLED_APPS = [
       # ... your existing apps
       'django_graphql_auto',
   ]

   DJANGO_GRAPHQL_AUTO = {
       'DEFAULT_SCHEMA': 'main',
       'ENABLE_GRAPHIQL': True,
       'AUTO_DISCOVER_SCHEMAS': True,
   }

Add URL configuration:

.. code-block:: python

   # urls.py
   from django.urls import path, include

   urlpatterns = [
       # ... your existing patterns
       path('graphql/', include('django_graphql_auto.urls')),
   ]

That's it! Your GraphQL API is now available at ``http://localhost:8000/graphql/main/``

Community & Support
-------------------

- **Documentation**: https://rail-django-graphql.readthedocs.io/
- **GitHub**: https://github.com/raillogistic/rail-django-graphql
- **Issues**: https://github.com/raillogistic/rail-django-graphql/issues
- **Discussions**: https://github.com/raillogistic/rail-django-graphql/discussions
- **Email**: support@raillogistic.com

License
-------

This project is licensed under the MIT License - see the :doc:`project/license` for details.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`