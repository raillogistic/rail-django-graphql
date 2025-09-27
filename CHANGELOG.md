# Changelog

All notable changes to the Django GraphQL Auto-Generation Library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Phase 6: File Uploads & Media Management System**
  - Complete file upload system with GraphQL integration
  - Multi-file upload support with progress tracking
  - Comprehensive security features including virus scanning
  - Image processing and thumbnail generation
  - Multiple storage backend support (Local, AWS S3, Google Cloud, Azure)
  - File validation and content type detection
  - Quarantine system for suspicious files
  - Performance monitoring and optimization
  
- **File Upload GraphQL Operations**
  - `uploadFile` mutation for single file uploads
  - `uploadMultipleFiles` mutation for batch uploads
  - `fileProcessingStatus` query for upload status tracking
  - `listFiles` query with filtering and pagination
  - `deleteFile` mutation with security validation
  
- **Security Features**
  - ClamAV virus scanner integration
  - File type validation and MIME type checking
  - Content-based file validation
  - Quarantine system for infected files
  - Security monitoring and audit logging
  - Configurable file size and type restrictions
  
- **Media Processing**
  - Automatic thumbnail generation for images
  - Image optimization and format conversion
  - Configurable processing pipelines
  - Async processing with status tracking
  
- **Storage Backends**
  - Local filesystem storage with configurable paths
  - AWS S3 integration with IAM support
  - Google Cloud Storage integration
  - Azure Blob Storage support
  - Configurable storage policies and retention

### Enhanced
- **Documentation System**: Complete file upload documentation
  - Comprehensive API reference for file operations
  - Security documentation with best practices
  - Feature documentation with examples
  - Installation guide with system dependencies
  - Practical examples for all file operations
  
- **Configuration System**: Extended settings for file uploads
  - `FILE_UPLOADS` configuration section
  - Virus scanning configuration
  - Storage backend selection and settings
  - Performance and security tuning options

### Added
- Comprehensive API reference documentation
- Enhanced feature documentation for filtering, method mutations, and bulk operations
- French verbose name support throughout the documentation

### Changed
- Updated all documentation to reflect current feature set
- Improved code examples with French verbose names
- Enhanced quick-start guide with new features

## [1.3.5] - 2024-01-15 - Phase 3.5: Method Mutations & Bulk Operations

### Added
- **Method Mutations System**: Execute custom Django model methods as GraphQL mutations
  - `@graphql_mutation` decorator for marking methods as GraphQL mutations
  - Automatic parameter detection and GraphQL schema generation
  - Support for method parameters with type hints
  - Return value handling for complex method responses
  - Error handling and validation for method execution
  
- **Bulk Operations System**: Efficient batch processing for large datasets
  - `bulkCreate<Model>` mutations for creating multiple objects
  - `bulkUpdate<Model>` mutations for updating multiple objects with different values
  - `bulkDelete<Model>` mutations for deleting multiple objects by ID
  - Configurable batch sizes and transaction management
  - Partial success support with detailed error reporting
  - Performance optimization with memory management
  
- **Enhanced Configuration System**: Extended settings for new features
  - `enable_method_mutations`: Toggle method mutation generation
  - `enable_bulk_operations`: Toggle bulk operation generation
  - `bulk_batch_size`: Configure batch processing size
  - `bulk_max_objects`: Set maximum objects per bulk operation
  - `bulk_transaction_timeout`: Configure transaction timeout

### Enhanced
- **Django Built-in Filtering**: Comprehensive filter support
  - String operators: `exact`, `iexact`, `contains`, `icontains`, `startswith`, `endswith`, `regex`
  - Numeric operators: `gt`, `gte`, `lt`, `lte`, `range`, `in`
  - Date/time operators: Range filtering and comparison operators
  - Relationship filtering: Deep filtering across foreign keys and many-to-many fields
  - Logical operators: `AND`, `OR`, `NOT` for complex filter combinations
  
- **Nested Operations**: Improved relationship handling
  - Enhanced nested object creation and updates
  - Better validation for nested relationships
  - Improved error handling for complex nested structures

### Fixed
- Improved quote handling in GraphQL input sanitization
- Enhanced error messages for validation failures
- Better memory management for large bulk operations
- Optimized database queries for relationship filtering

### Documentation
- Added comprehensive method mutations documentation (`docs/features/method-mutations.md`)
- Added detailed bulk operations guide (`docs/features/bulk-operations.md`)
- Created complete API reference (`docs/api-reference.md`)
- Updated quick-start guide with new features
- Enhanced examples with method mutations and bulk operations
- Added French verbose name examples throughout documentation

### Performance
- Optimized bulk operations with batch processing
- Improved query performance for filtered results
- Enhanced memory usage for large dataset operations
- Better database connection management

## [1.3.0] - 2024-01-01 - Phase 3: Advanced Features

### Added
- **Advanced Filtering System**: Comprehensive filtering capabilities
  - Field-level filtering with multiple operators
  - Relationship filtering across models
  - Date and time range filtering
  - Custom filter implementations
  
- **Nested Operations**: Create and update related objects
  - Nested object creation in mutations
  - Relationship management in single operations
  - Configurable nesting depth and permissions
  
- **Enhanced Quote Handling**: Robust input sanitization
  - Automatic quote normalization in GraphQL inputs
  - JSON content support with proper escaping
  - Special character protection and validation

### Enhanced
- **Schema Generation**: Improved type generation and validation
- **Error Handling**: More detailed error messages and validation
- **Performance**: Optimized query generation and execution

### Fixed
- Quote handling in complex nested inputs
- Validation errors for relationship fields
- Memory usage optimization for large schemas

## [1.2.0] - 2023-12-01 - Phase 2: Core Mutations

### Added
- **CRUD Mutations**: Complete create, read, update, delete operations
  - `create<Model>` mutations with comprehensive input validation
  - `update<Model>` mutations with partial update support
  - `delete<Model>` mutations with cascade handling
  
- **Input Validation**: Robust validation system
  - Django model validation integration
  - Custom validation rules support
  - Detailed error reporting and field-level errors
  
- **Relationship Handling**: Foreign key and many-to-many support
  - Automatic relationship field generation
  - ID-based relationship assignment
  - Validation for relationship constraints

### Enhanced
- **Type System**: Improved GraphQL type generation from Django models
- **Error Handling**: Standardized error response format
- **Documentation**: Comprehensive mutation examples and usage guides

### Fixed
- Type resolution for complex Django field types
- Validation handling for optional fields
- Relationship field naming consistency

## [1.1.0] - 2023-11-01 - Phase 1: Foundation & Queries

### Added
- **Automatic Schema Generation**: Generate GraphQL schemas from Django models
  - Model introspection and metadata extraction
  - Automatic type generation for all Django field types
  - Relationship mapping and type resolution
  
- **Query System**: Comprehensive query capabilities
  - Single object queries by ID
  - List queries with filtering support
  - Paginated queries with Relay-style connections
  
- **Configuration System**: Flexible configuration options
  - App-based model selection
  - Field inclusion/exclusion controls
  - Custom naming conventions
  
- **Basic Filtering**: Initial filtering implementation
  - Field-level exact match filtering
  - Basic relationship filtering
  - Simple query optimization

### Technical Foundation
- **Model Introspection**: Advanced Django model analysis
- **Type Generation**: Robust GraphQL type creation
- **Schema Assembly**: Modular schema building system
- **Error Handling**: Basic error reporting and validation

## [1.0.0] - 2023-10-01 - Initial Release

### Added
- **Project Foundation**: Initial project structure and core architecture
- **Basic Schema Generation**: Minimal GraphQL schema from Django models
- **Simple Queries**: Basic object retrieval functionality
- **Documentation**: Initial documentation and setup guides
- **Configuration**: Basic configuration system

### Technical Features
- Django integration and model discovery
- GraphQL schema generation pipeline
- Basic type mapping for Django fields
- Simple query resolution
- Error handling framework

---

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version when making incompatible API changes
- **MINOR** version when adding functionality in a backwards compatible manner
- **PATCH** version when making backwards compatible bug fixes

## Release Process

1. **Development**: Features developed in feature branches
2. **Testing**: Comprehensive testing including unit, integration, and performance tests
3. **Documentation**: Update documentation for new features
4. **Release**: Tag release and update changelog
5. **Deployment**: Deploy to package repositories

## Migration Guides

### Upgrading to 1.3.5

#### Method Mutations
To use the new method mutations feature:

1. Add the `@graphql_mutation` decorator to your model methods:
```python
from django_graphql_auto.decorators import graphql_mutation

class MyModel(models.Model):
    @graphql_mutation
    def my_method(self):
        # Your method logic
        return result
```

2. Enable method mutations in settings:
```python
DJANGO_GRAPHQL_AUTO = {
    'MUTATION_SETTINGS': {
        'enable_method_mutations': True,
    }
}
```

#### Bulk Operations
To use bulk operations:

1. Enable in settings:
```python
DJANGO_GRAPHQL_AUTO = {
    'MUTATION_SETTINGS': {
        'enable_bulk_operations': True,
        'bulk_batch_size': 100,
    }
}
```

2. Use the generated bulk mutations in your GraphQL queries:
```graphql
mutation {
  bulkCreateMyModel(input: { objects: [...] }) {
    ok
    objects { id }
    errors
  }
}
```

### Upgrading to 1.3.0

#### Advanced Filtering
The new filtering system is automatically available. Update your queries to use the enhanced filter operators:

```graphql
query {
  posts(filters: {
    title__icontains: "django"
    createdAt__gte: "2024-01-01T00:00:00Z"
    author__username: "john"
  }) {
    id
    title
  }
}
```

#### Nested Operations
Enable nested operations in your configuration:

```python
DJANGO_GRAPHQL_AUTO = {
    'MUTATION_SETTINGS': {
        'enable_nested_relations': True,
        'nested_depth_limit': 3,
    }
}
```

## Support and Contributing

- **Issues**: Report bugs and request features on GitHub
- **Documentation**: Comprehensive guides in the `docs/` directory
- **Contributing**: See `CONTRIBUTING.md` for development guidelines
- **Community**: Join our discussions and get help from the community

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.