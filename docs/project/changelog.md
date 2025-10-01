# Changelog

All notable changes to Django GraphQL Auto will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation system with Sphinx
- Health monitoring and alerting system
- Performance metrics collection and analysis
- Multi-schema support with advanced routing
- Custom scalar type support
- File upload and media handling
- Advanced filtering and pagination
- Query complexity analysis and limits
- Caching middleware with Redis support
- Security enhancements and validation
- Developer debugging tools
- Integration testing framework

### Changed
- Improved schema generation performance
- Enhanced error handling and reporting
- Better type inference for Django models
- Optimized query execution pipeline

### Fixed
- Memory leaks in schema caching
- Race conditions in multi-schema environments
- Type resolution issues with complex relationships

## [2.1.0] - 2024-01-15

### Added
- **Multi-Schema Support**: Full support for multiple GraphQL schemas in a single Django application
- **Advanced Routing**: Schema-based URL routing with namespace support
- **Performance Monitoring**: Built-in metrics collection and performance analysis
- **Health Checks**: Comprehensive health monitoring system
- **Custom Scalars**: Support for custom scalar types (DateTime, JSON, Upload, etc.)
- **File Uploads**: GraphQL multipart request specification support
- **Query Complexity**: Analysis and limiting of query complexity
- **Caching Layer**: Redis-based caching for improved performance
- **Security Features**: Query depth limiting, rate limiting, and validation

### Changed
- **Breaking**: Refactored schema registration API for better multi-schema support
- **Breaking**: Updated configuration structure for enhanced flexibility
- Improved error messages with more context and suggestions
- Enhanced type inference for Django model relationships
- Better handling of nullable fields and default values

### Fixed
- Fixed memory leaks in schema caching mechanism
- Resolved race conditions in concurrent schema access
- Fixed type resolution issues with generic foreign keys
- Corrected pagination cursor encoding/decoding

### Security
- Added query depth limiting to prevent DoS attacks
- Implemented rate limiting for GraphQL endpoints
- Enhanced input validation and sanitization

## [2.0.0] - 2023-12-01

### Added
- **Auto Schema Generation**: Automatic GraphQL schema generation from Django models
- **Decorator-based Registration**: Simple `@graphql_schema` decorator for model registration
- **Manual Schema Building**: Programmatic schema construction API
- **Schema Discovery**: Automatic discovery of models with GraphQL configurations
- **Builder Pattern**: Fluent API for complex schema construction
- **Introspection Support**: Full GraphQL introspection capabilities
- **Django Integration**: Seamless integration with Django ORM and admin
- **Type Safety**: Strong typing with proper GraphQL type mapping

### Changed
- **Breaking**: Complete rewrite of the core architecture
- **Breaking**: New configuration format and API
- Migrated from class-based to function-based resolvers
- Improved performance with optimized query execution
- Enhanced error handling with detailed error messages

### Removed
- **Breaking**: Removed legacy schema definition format
- **Breaking**: Dropped support for Django < 3.2
- Removed deprecated configuration options

## [1.5.2] - 2023-10-15

### Fixed
- Fixed compatibility issues with Django 4.2
- Resolved circular import problems in complex model hierarchies
- Fixed memory usage in large schema generation

### Security
- Updated dependencies to address security vulnerabilities
- Improved input validation for GraphQL queries

## [1.5.1] - 2023-09-20

### Fixed
- Fixed schema caching issues in production environments
- Resolved type conflicts with multiple inheritance
- Fixed pagination issues with filtered querysets

### Changed
- Improved error messages for schema generation failures
- Enhanced logging for debugging purposes

## [1.5.0] - 2023-08-10

### Added
- Support for Django 4.1 and 4.2
- Enhanced filtering capabilities with complex lookups
- Pagination support with cursor-based pagination
- Basic caching for frequently accessed schemas
- Improved documentation and examples

### Changed
- Optimized schema generation performance
- Better handling of model relationships
- Enhanced type inference for model fields

### Fixed
- Fixed issues with abstract model inheritance
- Resolved problems with custom model managers
- Fixed timezone handling in DateTime fields

## [1.4.0] - 2023-06-15

### Added
- Support for custom field resolvers
- Basic authentication and permission handling
- Schema validation and error reporting
- Development server integration
- Basic testing utilities

### Changed
- Improved schema generation algorithm
- Better error handling and reporting
- Enhanced documentation

### Fixed
- Fixed issues with model field mapping
- Resolved problems with nullable fields
- Fixed schema generation for models with custom primary keys

## [1.3.0] - 2023-04-20

### Added
- Support for model relationships (ForeignKey, ManyToMany)
- Basic mutation support for CRUD operations
- Schema introspection capabilities
- Configuration management system
- Basic logging and debugging features

### Changed
- Refactored core schema generation logic
- Improved type mapping for Django fields
- Enhanced error messages

### Fixed
- Fixed issues with model inheritance
- Resolved circular dependency problems
- Fixed schema generation for proxy models

## [1.2.0] - 2023-02-10

### Added
- Support for Django 3.2 and 4.0
- Basic schema generation from Django models
- Simple query resolution
- Configuration through Django settings
- Basic documentation

### Changed
- Improved code organization and structure
- Better separation of concerns
- Enhanced type safety

### Fixed
- Fixed compatibility issues with different Django versions
- Resolved import problems
- Fixed basic schema generation bugs

## [1.1.0] - 2023-01-05

### Added
- Initial GraphQL schema generation
- Basic Django model integration
- Simple configuration system
- Basic error handling

### Changed
- Improved project structure
- Better code organization

### Fixed
- Fixed initial setup issues
- Resolved basic functionality bugs

## [1.0.0] - 2022-12-01

### Added
- Initial release of Django GraphQL Auto
- Basic GraphQL schema generation from Django models
- Simple configuration and setup
- Basic documentation and examples
- MIT license

### Features
- Automatic schema generation
- Django model integration
- Basic query support
- Simple configuration

---

## Migration Guides

### Migrating from 1.x to 2.0

The 2.0 release includes breaking changes. See our [Migration Guide](migration-guide.md) for detailed instructions.

### Migrating from 2.0 to 2.1

The 2.1 release introduces multi-schema support with some breaking changes in configuration. See the [2.1 Migration Guide](migration-guide.md#migrating-to-21) for details.

## Support

- **Documentation**: [https://rail-django-graphql.readthedocs.io/](https://rail-django-graphql.readthedocs.io/)
- **Issues**: [https://github.com/rail-logistic/rail-django-graphql/issues](https://github.com/rail-logistic/rail-django-graphql/issues)
- **Discussions**: [https://github.com/rail-logistic/rail-django-graphql/discussions](https://github.com/rail-logistic/rail-django-graphql/discussions)

## Contributing

We welcome contributions! Please see our [Contributing Guide](../CONTRIBUTING.md) for details on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.