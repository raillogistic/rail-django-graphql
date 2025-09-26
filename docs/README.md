# Django GraphQL Auto-Generation Library Documentation

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Django Version](https://img.shields.io/badge/django-3.2%2B-green.svg)](https://djangoproject.com)
[![GraphQL](https://img.shields.io/badge/graphql-enabled-e10098.svg)](https://graphql.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🚀 Overview

The Django GraphQL Auto-Generation Library is a powerful system that automatically generates comprehensive GraphQL schemas (queries, mutations, subscriptions) for all Django apps based on models and relationships. It features live schema updates, advanced filtering, nested operations, and follows GraphQL best practices with snake_case naming conventions.

## ✨ Key Features

- **🔄 Automatic Schema Generation**: Zero-configuration GraphQL schema generation from Django models
- **🔍 Advanced Filtering**: Complex filter combinations with AND, OR, NOT operations
- **🔗 Nested Operations**: Full control over nested create/update operations with granular configuration
- **🎯 Smart Field Requirements**: Intelligent field requirement detection based on Django constraints
- **🏗️ Inheritance Support**: Complete support for Django model inheritance patterns
- **📊 Custom Scalars**: Built-in support for JSON, DateTime, Decimal, UUID, and Duration types
- **⚙️ Method Mutations**: Automatic conversion of Django model methods to GraphQL mutations
- **📦 Bulk Operations**: High-performance bulk create, update, and delete operations
- **🛡️ Django Built-in Filtering**: Intelligent filtering of Django framework methods from mutations
- **⚙️ Flexible Configuration**: Global, per-model, and per-field control over schema generation
- **🔒 Security Ready**: Built-in authentication and permission systems (Phase 4)
- **⚡ Performance Optimized**: N+1 query prevention and intelligent caching (Phase 5)
- **📁 File Upload Support**: Automatic file upload mutations (Phase 6)

## 📚 Documentation

For comprehensive documentation, examples, and guides, visit our documentation:

- **[📖 Documentation Index](index.md)** - Complete documentation overview and navigation
- **[🚀 Installation Guide](setup/installation.md)** - Complete setup instructions
- **[📝 Basic Usage](usage/basic-usage.md)** - Getting started with the library
- **[⚡ Advanced Features](advanced/)** - Custom scalars, inheritance, nested operations
- **[📋 API Reference](api/core-classes.md)** - Detailed API documentation
- **[💡 Examples](examples/)** - Practical usage examples
- **[🔧 Performance Guide](development/performance.md)** - Optimization strategies
- **[🛠️ Troubleshooting](development/troubleshooting.md)** - Common issues and solutions
- **[📈 Changelog](CHANGELOG.md)** - Version history and release notes

### Documentation Structure

### Getting Started
- [Installation & Setup](setup/installation.md) - Quick start guide and configuration
- [Basic Usage](usage/basic-usage.md) - Your first GraphQL schema
- [Configuration](setup/configuration.md) - Advanced configuration options

### Core Features
- [Schema Generation](features/schema-generation.md) - How automatic schema generation works
- [Queries](features/queries.md) - Single, list, and paginated queries
- [Mutations](features/mutations.md) - CRUD operations and custom mutations
- [Filtering](features/filtering.md) - Advanced filtering capabilities
- [Nested Operations](features/nested-operations.md) - Complex nested create/update operations

### Advanced Features
- [Custom Scalars](advanced/custom-scalars.md) - Working with complex data types
- [Inheritance Support](advanced/inheritance.md) - Django model inheritance in GraphQL
- [Method Conversion](advanced/method-conversion.md) - Converting Django methods to GraphQL
- [File Uploads](advanced/file-uploads.md) - Handling file uploads in GraphQL

### API Reference
- [Core Classes](api/core-classes.md) - ModelIntrospector, TypeGenerator, QueryGenerator
- [Generators](api/generators.md) - MutationGenerator, FilterGenerator, SchemaBuilder
- [Extensions](api/extensions.md) - Authentication, permissions, caching
- [Utilities](api/utilities.md) - Helper functions and utilities

### Examples
- [Basic Examples](examples/basic-examples.md) - Simple use cases and patterns
- [Advanced Examples](examples/advanced-examples.md) - Complex scenarios and integrations
- [Real-world Projects](examples/real-world.md) - Production-ready implementations

### Development
- [Contributing](development/contributing.md) - How to contribute to the project
- [Architecture](development/architecture.md) - System design and architecture
- [Testing](development/testing.md) - Testing strategies and guidelines
- [Troubleshooting](development/troubleshooting.md) - Common issues and solutions

## 🎯 Quick Start

```bash
# Install the library
pip install django-graphql-auto

# Add to Django settings
INSTALLED_APPS = [
    'django_graphql_auto',
    # ... your apps
]

# Configure Django settings
DJANGO_GRAPHQL_AUTO = {
    'MUTATION_SETTINGS': {
        'enable_nested_relations': True,  # Global control
        'enable_method_mutations': True,  # Enable method mutations
        'enable_bulk_operations': True,   # Enable bulk operations
        'bulk_batch_size': 100,          # Batch size for bulk operations
        'nested_relations_config': {
            'Post': True,     # Enable nested relations for Post model
            'Comment': False  # Disable nested relations for Comment model
        },
        'nested_field_config': {
            'Post': {
                'comments': False,      # Disable nested comments in Post mutations
                'related_posts': True  # Enable nested related_posts
            }
        }
    }
}

# Generate schema
python manage.py generate_graphql_schema

# Start using GraphQL
# Your schema is automatically available at /graphql/
```

## 📊 Current Status

### ✅ Completed Phases
- **Phase 1**: Foundation & Setup
- **Phase 2**: Auto-Generation Engine
- **Phase 3**: Advanced Features (Filtering, Nested Operations, Custom Scalars, Inheritance)
- **Phase 3.5**: Method Mutations & Bulk Operations

### 🔄 In Progress
- **Phase 4**: Security Implementation (Authentication, Permissions)

### ⏳ Planned
- **Phase 5**: Performance Optimization
- **Phase 6**: File Uploads & Media
- **Phase 7**: Comprehensive Testing
- **Phase 8**: Deployment & Monitoring

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- 🐛 **Bug Reports** - Help us identify and fix issues
- 💡 **Feature Requests** - Suggest new features and improvements  
- 🔧 **Code Contributions** - Submit pull requests with improvements
- 📚 **Documentation** - Help improve our guides and examples
- 🧪 **Testing** - Add test cases and improve coverage
- 💬 **Community** - Join discussions and help other users

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🙏 Acknowledgments

- Django community for the excellent framework
- Graphene-Django team for GraphQL integration
- All contributors and users providing feedback
- Open source community for inspiration and support

---

**Ready to get started?** Check out our [Installation Guide](setup/installation.md) and [Basic Usage](usage/basic-usage.md) to begin using the Django GraphQL Auto-Generation Library!