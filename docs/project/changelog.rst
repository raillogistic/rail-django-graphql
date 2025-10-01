Changelog
=========

All notable changes to Django GraphQL Auto will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

Unreleased
----------

Added
~~~~~
- Advanced query optimization with intelligent caching strategies
- Real-time subscription support with WebSocket integration
- Enhanced security features with field-level permissions
- Comprehensive monitoring and alerting system
- Performance profiling and bottleneck detection tools

Changed
~~~~~~~
- Improved schema generation performance by 40%
- Enhanced error handling with detailed debugging information
- Updated documentation with interactive examples
- Refactored core engine for better extensibility

Fixed
~~~~~
- Resolved memory leaks in long-running processes
- Fixed edge cases in nested relationship handling
- Corrected timezone handling in datetime fields
- Improved compatibility with Django 4.2+

Security
~~~~~~~~
- Enhanced input validation and sanitization
- Improved authentication and authorization mechanisms
- Added rate limiting and DDoS protection features

[2.1.0] - 2024-01-15
---------------------

Added
~~~~~
- **GraphQL Subscriptions**: Real-time data updates via WebSocket
- **Advanced Caching**: Multi-level caching with Redis integration
- **Query Complexity Analysis**: Automatic query complexity scoring and limits
- **Field-Level Permissions**: Granular access control for individual fields
- **Batch Operations**: Efficient bulk create, update, and delete operations
- **Custom Scalar Types**: Support for custom data types and validation
- **API Versioning**: Built-in versioning support for schema evolution
- **Monitoring Dashboard**: Real-time performance and health monitoring
- **Auto-Documentation**: Automatic API documentation generation
- **Plugin System**: Extensible architecture for custom functionality

Changed
~~~~~~~
- Enhanced schema introspection with better type information
- Improved error messages with detailed context and suggestions
- Updated dependency requirements for better security
- Optimized database query generation for complex relationships
- Refactored middleware system for better performance

Fixed
~~~~~
- Resolved circular dependency issues in complex schemas
- Fixed pagination edge cases with filtered queries
- Corrected handling of null values in nested objects
- Improved memory usage in large dataset operations
- Fixed timezone-aware datetime serialization

Deprecated
~~~~~~~~~~
- ``legacy_auth_backend`` - Use new ``AuthenticationBackend`` instead
- ``old_cache_config`` - Migrate to new caching configuration format

Removed
~~~~~~~
- Support for Django versions below 3.2
- Deprecated ``SimpleGraphQLView`` class
- Legacy configuration format (pre-2.0)

Security
~~~~~~~~
- Enhanced SQL injection prevention in dynamic queries
- Improved CSRF protection for GraphQL mutations
- Added request rate limiting and throttling
- Enhanced input validation for all scalar types

[2.0.0] - 2023-11-20
---------------------

Added
~~~~~
- **Complete Schema Auto-Generation**: Automatic GraphQL schema from Django models
- **Intelligent Relationship Mapping**: Automatic detection and mapping of model relationships
- **Dynamic Query Optimization**: Runtime query optimization based on usage patterns
- **Advanced Filtering System**: Comprehensive filtering with operators and conditions
- **Pagination Support**: Cursor-based and offset-based pagination
- **Mutation Auto-Generation**: Automatic CRUD mutations for all models
- **Permission Integration**: Seamless integration with Django's permission system
- **Custom Field Resolvers**: Support for custom business logic in field resolution
- **Schema Validation**: Comprehensive validation of generated schemas
- **Performance Monitoring**: Built-in performance tracking and optimization suggestions

Changed
~~~~~~~
- **Breaking**: Completely rewritten core engine for better performance
- **Breaking**: New configuration format (see migration guide below)
- **Breaking**: Updated API endpoints and naming conventions
- Improved error handling with structured error responses
- Enhanced logging with detailed operation tracking
- Updated documentation with comprehensive examples

Fixed
~~~~~
- Resolved performance issues with large datasets
- Fixed edge cases in relationship traversal
- Corrected handling of abstract model inheritance
- Improved compatibility with custom Django fields

Migration Guide (1.x to 2.0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Configuration Changes**:

.. code-block:: python

   # Old format (1.x)
   GRAPHQL_AUTO_CONFIG = {
       'auto_generate': True,
       'include_models': ['app.Model1', 'app.Model2']
   }
   
   # New format (2.0+)
   GRAPHQL_AUTO = {
       'SCHEMA': {
           'AUTO_GENERATE': True,
           'INCLUDE_MODELS': ['app.Model1', 'app.Model2']
       }
   }

**API Changes**:

.. code-block:: python

   # Old import (1.x)
   from django_graphql_auto.views import GraphQLAutoView
   
   # New import (2.0+)
   from django_graphql_auto.views import AutoGraphQLView

[1.5.2] - 2023-09-15
---------------------

Fixed
~~~~~
- Critical security fix for authentication bypass vulnerability
- Resolved memory leak in schema caching
- Fixed compatibility issues with Django 4.1
- Corrected handling of many-to-many relationships in mutations

Security
~~~~~~~~
- **CVE-2023-XXXX**: Fixed authentication bypass in custom resolvers
- Enhanced input sanitization for all user inputs
- Improved session management and token validation

[1.5.1] - 2023-08-10
---------------------

Fixed
~~~~~
- Resolved installation issues with Python 3.11
- Fixed deprecation warnings in Django 4.0+
- Corrected timezone handling in date/datetime fields
- Improved error messages for schema validation failures

Changed
~~~~~~~
- Updated dependencies to latest stable versions
- Enhanced compatibility testing across Python/Django versions
- Improved documentation with more examples

[1.5.0] - 2023-07-01
---------------------

Added
~~~~~
- Support for Django 4.2 LTS
- Enhanced filtering with JSON field support
- Custom authentication backends
- Improved schema introspection capabilities
- Basic monitoring and health check endpoints

Changed
~~~~~~~
- Optimized query generation for better performance
- Enhanced error handling with more descriptive messages
- Updated documentation structure and content
- Improved test coverage to 95%

Fixed
~~~~~
- Resolved issues with nested serializer handling
- Fixed edge cases in permission checking
- Corrected handling of custom model managers
- Improved compatibility with third-party Django packages

[1.4.0] - 2023-05-15
---------------------

Added
~~~~~
- Advanced query filtering with operators (gt, lt, contains, etc.)
- Support for custom scalar types
- Enhanced pagination with cursor-based navigation
- Basic caching mechanisms for improved performance
- Integration with Django's admin interface

Changed
~~~~~~~
- Improved schema generation performance
- Enhanced error reporting and debugging capabilities
- Updated API documentation with interactive examples
- Refactored internal architecture for better maintainability

Fixed
~~~~~
- Resolved circular import issues
- Fixed handling of nullable foreign key relationships
- Corrected serialization of decimal and date fields
- Improved validation of input parameters

[1.3.0] - 2023-03-20
---------------------

Added
~~~~~
- Support for nested mutations and complex operations
- Enhanced permission system with field-level controls
- Basic subscription support (experimental)
- Improved schema documentation generation
- Integration with popular Django packages (django-filter, etc.)

Changed
~~~~~~~
- Optimized database queries for relationship traversal
- Enhanced configuration options for schema customization
- Improved error handling and user feedback
- Updated dependencies and compatibility requirements

Fixed
~~~~~
- Resolved issues with model inheritance handling
- Fixed edge cases in relationship resolution
- Corrected handling of custom field types
- Improved stability under high load conditions

[1.2.0] - 2023-01-10
---------------------

Added
~~~~~
- Comprehensive mutation support for all CRUD operations
- Enhanced filtering capabilities with multiple operators
- Support for file uploads in GraphQL mutations
- Basic authentication and authorization integration
- Improved schema validation and error reporting

Changed
~~~~~~~
- Refactored core schema generation logic
- Enhanced performance for large model hierarchies
- Improved documentation with practical examples
- Updated testing framework and coverage

Fixed
~~~~~
- Resolved issues with many-to-many field handling
- Fixed edge cases in query optimization
- Corrected serialization of complex data types
- Improved error messages for better debugging

[1.1.0] - 2022-11-05
---------------------

Added
~~~~~
- Support for Django 4.0 and 4.1
- Enhanced relationship handling for complex models
- Basic pagination support for large datasets
- Improved configuration options and flexibility
- Integration with Django's built-in authentication

Changed
~~~~~~~
- Optimized schema generation for better performance
- Enhanced error handling and user experience
- Improved documentation and examples
- Updated project structure and organization

Fixed
~~~~~
- Resolved compatibility issues with newer Django versions
- Fixed edge cases in model field detection
- Corrected handling of abstract base classes
- Improved stability and reliability

[1.0.0] - 2022-09-01
---------------------

Added
~~~~~
- **Initial Release**: Core functionality for automatic GraphQL schema generation
- **Model Integration**: Seamless integration with Django ORM models
- **Basic Queries**: Automatic generation of query resolvers
- **Relationship Support**: Basic handling of foreign key relationships
- **Configuration System**: Flexible configuration for schema customization
- **Documentation**: Comprehensive documentation and examples
- **Testing Framework**: Full test suite with high coverage
- **Django Compatibility**: Support for Django 3.2+ and Python 3.8+

Features
~~~~~~~~
- Automatic schema generation from Django models
- Basic CRUD operations via GraphQL
- Simple relationship traversal
- Configurable field inclusion/exclusion
- Basic error handling and validation
- Integration with Django's ORM and admin

Support and Resources
---------------------

Getting Help
~~~~~~~~~~~~
- **Documentation**: https://django-graphql-auto.readthedocs.io/
- **GitHub Issues**: https://github.com/yourorg/django-graphql-auto/issues
- **Community Forum**: https://forum.django-graphql-auto.org/
- **Stack Overflow**: Tag your questions with ``django-graphql-auto``

Contributing
~~~~~~~~~~~~
We welcome contributions! Please see our `Contributing Guide <../development/contributing.html>`_ for details on:

- Code of Conduct
- Development setup
- Submission guidelines
- Testing requirements

Reporting Issues
~~~~~~~~~~~~~~~~
When reporting issues, please include:

- Django GraphQL Auto version
- Django version
- Python version
- Minimal reproduction case
- Error messages and stack traces

License
~~~~~~~
This project is licensed under the MIT License. See the `LICENSE <license.html>`_ file for details.

---

*For the complete version history and detailed release notes, visit our* `GitHub Releases <https://github.com/yourorg/django-graphql-auto/releases>`_ *page.*