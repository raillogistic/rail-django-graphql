# Django GraphQL Auto

A comprehensive Django library for automatic GraphQL schema generation, multi-schema management, and advanced GraphQL features including validation, introspection, debugging, and performance monitoring.

## 🚀 Overview

Django GraphQL Auto transforms your Django models into powerful GraphQL APIs with minimal configuration. Whether you're building microservices, multi-tenant applications, or complex APIs with different access levels, this library provides enterprise-grade tools for GraphQL schema management.

### ✨ Key Benefits

- **🔧 Zero Configuration**: Works out of the box with sensible defaults
- **🏗️ Multi-Schema Architecture**: Manage multiple GraphQL schemas in a single Django application  
- **🚀 Production Ready**: Thread-safe operations with comprehensive error handling
- **👨‍💻 Developer Friendly**: Rich debugging tools and comprehensive documentation
- **🔌 Extensible**: Plugin architecture for custom functionality
- **📊 Performance Monitoring**: Built-in metrics and performance tracking
- **🔍 Schema Validation**: Comprehensive validation and introspection capabilities

## 📋 Features

### Core Features
- 🚀 **Multi-Schema Support**: Register and manage multiple GraphQL schemas independently
- 🔍 **Dynamic Schema Discovery**: Automatic schema detection from Django apps and models
- 📋 **Schema Registry**: Centralized schema management with metadata and versioning
- 🌐 **REST API**: Complete REST API for schema management and monitoring
- 💚 **Health Checks**: Built-in health monitoring and performance metrics
- 🔒 **Thread Safety**: Production-ready thread-safe operations

### Advanced Features
- 🪝 **Discovery Hooks**: Pre/post registration hooks for custom logic
- 📈 **Schema Versioning**: Version management for schema evolution
- 📊 **Performance Monitoring**: Built-in metrics and performance tracking
- 🌍 **CORS Support**: Cross-origin resource sharing for API endpoints
- 🎯 **Decorator-based Registration**: Simple decorators for schema registration
- 🔧 **Hierarchical Settings**: Three-tier configuration system (schema > global > defaults)
- ✅ **Schema Validation**: Comprehensive validation with detailed error reporting
- 🔍 **Schema Introspection**: Advanced introspection with documentation generation
- 🐛 **Debugging Tools**: Comprehensive debugging hooks and query analysis
- 📁 **Schema Management**: Migration, backup, and lifecycle management utilities

## 📦 Installation

### From PyPI (Recommended)

```bash
pip install rail-django-graphql
```

### From GitHub (Latest)

```bash
pip install git+https://github.com/raillogistic/rail-django-graphql.git@main
```

### Development Installation

```bash
git clone https://github.com/raillogistic/rail-django-graphql.git
cd rail-django-graphql
pip install -e .
```

### Optional Dependencies

Install additional features as needed:

```bash
# Authentication and permissions
pip install rail-django-graphql[auth]

# Performance monitoring and caching
pip install rail-django-graphql[performance]

# File upload support
pip install rail-django-graphql[media]

# Documentation generation
pip install rail-django-graphql[docs]

# All features
pip install rail-django-graphql[all]
```

## ⚡ Quick Start

### 1. Add to Django Settings

```python
# settings.py
INSTALLED_APPS = [
    # ... your existing apps
    'django_graphql_auto',
]

# Basic configuration
DJANGO_GRAPHQL_AUTO = {
    'DEFAULT_SCHEMA': 'main',
    'ENABLE_GRAPHIQL': True,
    'AUTO_DISCOVER_SCHEMAS': True,
    'SCHEMAS': {
        'main': {
            'description': 'Main GraphQL API',
            'apps': ['myapp'],
        }
    }
}
```

### 2. Add URL Configuration

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ... your existing patterns
    path('graphql/', include('django_graphql_auto.urls')),
]
```

### 3. Create Your Models

```python
# myapp/models.py
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    isbn = models.CharField(max_length=13, unique=True)
    published_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
```

### 4. Register Schema (Optional)

```python
# myapp/schema.py
import graphene
from django_graphql_auto import register_schema
from django_graphql_auto.types import DjangoObjectType
from .models import Author, Book

class AuthorType(DjangoObjectType):
    class Meta:
        model = Author
        fields = '__all__'

class BookType(DjangoObjectType):
    class Meta:
        model = Book
        fields = '__all__'

class Query(graphene.ObjectType):
    authors = graphene.List(AuthorType)
    books = graphene.List(BookType)
    
    def resolve_authors(self, info):
        return Author.objects.all()
    
    def resolve_books(self, info):
        return Book.objects.all()

# Register schema using decorator
@register_schema('main')
class MainSchema(graphene.Schema):
    query = Query
```

### 5. Access Your GraphQL API

Once configured, your GraphQL endpoints will be available at:

- **GraphQL Endpoint**: `http://localhost:8000/graphql/main/`
- **GraphiQL Interface**: `http://localhost:8000/graphql/main/graphiql/`
- **Schema Management API**: `http://localhost:8000/graphql/api/schemas/`
- **Health Check**: `http://localhost:8000/graphql/api/health/`

## 📖 Usage Examples

### Schema Registration Methods

#### 1. Decorator-based Registration

```python
from django_graphql_auto import register_schema
import graphene

@register_schema('api_v1', description='API Version 1', version='1.0.0')
class APIv1Schema(graphene.Schema):
    query = Query
    mutation = Mutation
```

#### 2. Manual Registration

```python
from django_graphql_auto.registry import schema_registry
import graphene

schema = graphene.Schema(query=Query, mutation=Mutation)
schema_registry.register(
    name='api_v2',
    schema=schema,
    description='API Version 2',
    version='2.0.0'
)
```

#### 3. Auto-discovery from Apps

```python
# settings.py
DJANGO_GRAPHQL_AUTO = {
    'AUTO_DISCOVER_SCHEMAS': True,
    'DISCOVERY_APPS': ['myapp', 'otherapp'],
    'SCHEMA_FILE_PATTERNS': ['schema.py', 'graphql_schema.py'],
}
```

#### 4. Builder Pattern

```python
from django_graphql_auto.builders import SchemaBuilder

schema = (SchemaBuilder('ecommerce')
    .with_query(Query)
    .with_mutation(Mutation)
    .with_subscription(Subscription)
    .with_description('E-commerce GraphQL API')
    .with_version('1.0.0')
    .build())
```

### Multi-Schema Setup

```python
# settings.py
DJANGO_GRAPHQL_AUTO = {
    'SCHEMAS': {
        'public': {
            'description': 'Public API',
            'apps': ['blog', 'products'],
            'authentication_required': False,
        },
        'admin': {
            'description': 'Admin API',
            'apps': ['users', 'orders'],
            'authentication_required': True,
            'permission_classes': ['IsAdminUser'],
        },
        'mobile': {
            'description': 'Mobile API',
            'apps': ['mobile'],
            'max_query_depth': 5,
            'enable_caching': True,
        }
    }
}
```

### Schema Validation and Introspection

```python
from django_graphql_auto.validation import SchemaValidator
from django_graphql_auto.introspection import SchemaIntrospector

# Validate schema
validator = SchemaValidator()
result = validator.validate_schema(schema)
if not result.is_valid:
    print(f"Validation errors: {result.errors}")

# Introspect schema
introspector = SchemaIntrospector()
introspection_result = introspector.introspect_schema(schema)
print(f"Schema has {len(introspection_result.types)} types")
```

### Performance Monitoring

```python
from django_graphql_auto.debugging import PerformanceMonitor

# Monitor query performance
monitor = PerformanceMonitor()
monitor.start_operation('user_query', {'query': 'query { users { name } }'})
# ... execute query
monitor.end_operation('user_query')

# Get performance metrics
metrics = monitor.get_metrics()
print(f"Average execution time: {metrics.average_execution_time}ms")
```

## ⚙️ Configuration

### Global Configuration

```python
# settings.py
DJANGO_GRAPHQL_AUTO = {
    # Core settings
    'DEFAULT_SCHEMA': 'main',
    'ENABLE_GRAPHIQL': True,
    'AUTHENTICATION_REQUIRED': False,
    
    # Auto-discovery
    'AUTO_DISCOVER_SCHEMAS': True,
    'DISCOVERY_APPS': ['myapp'],
    'SCHEMA_FILE_PATTERNS': ['schema.py', 'graphql_schema.py'],
    
    # Performance
    'ENABLE_CACHING': True,
    'CACHE_TIMEOUT': 300,
    'MAX_QUERY_DEPTH': 10,
    'QUERY_TIMEOUT': 30,
    
    # Security
    'CORS_ENABLED': True,
    'CORS_ALLOW_ALL_ORIGINS': False,
    'CORS_ALLOWED_ORIGINS': ['http://localhost:3000'],
    'ENABLE_INTROSPECTION': True,
    
    # Monitoring and Debugging
    'ENABLE_METRICS': True,
    'ENABLE_DEBUG_HOOKS': True,
    'PERFORMANCE_MONITORING': True,
    'LOG_QUERIES': True,
    
    # Validation
    'STRICT_VALIDATION': True,
    'VALIDATE_ON_STARTUP': True,
    'VALIDATION_RULES': ['default', 'security', 'performance'],
    
    # Schema Management
    'ENABLE_SCHEMA_MANAGEMENT': True,
    'AUTO_BACKUP_SCHEMAS': True,
    'BACKUP_RETENTION_DAYS': 30,
    
    # Schema-specific settings
    'SCHEMAS': {
        'main': {
            'description': 'Main API',
            'version': '1.0.0',
            'apps': ['myapp'],
            'enable_graphiql': True,
            'authentication_required': False,
        },
        'admin': {
            'description': 'Admin API',
            'authentication_required': True,
            'permission_classes': ['IsAdminUser'],
            'max_query_depth': 15,
        }
    }
}
```

### Per-Schema Configuration

```python
from django_graphql_auto import register_schema

@register_schema(
    name='secure_api',
    description='Secure API with authentication',
    version='1.0.0',
    authentication_required=True,
    permission_classes=['IsAuthenticated'],
    enable_graphiql=False,
    cors_enabled=False,
    max_query_depth=5,
    enable_caching=True,
    cache_timeout=600
)
class SecureSchema(graphene.Schema):
    query = Query
```

## 🔧 Advanced Features

### Schema Validation

```python
from django_graphql_auto.validation import SchemaValidator, ValidationRule

# Custom validation rule
class CustomValidationRule(ValidationRule):
    def validate(self, schema_definition):
        # Custom validation logic
        if 'deprecated' in schema_definition.description.lower():
            return ValidationResult(
                is_valid=False,
                errors=['Schema should not be deprecated']
            )
        return ValidationResult(is_valid=True)

# Use validator with custom rules
validator = SchemaValidator()
validator.add_rule(CustomValidationRule())
result = validator.validate_schema(schema)
```

### Schema Introspection and Documentation

```python
from django_graphql_auto.introspection import SchemaIntrospector
from django_graphql_auto.documentation import DocumentationGenerator

# Introspect schema
introspector = SchemaIntrospector()
introspection = introspector.introspect_schema(schema)

# Generate documentation
doc_generator = DocumentationGenerator()
html_docs = doc_generator.generate_html_documentation(introspection)
markdown_docs = doc_generator.generate_markdown_documentation(introspection)
```

### Debugging and Performance Monitoring

```python
from django_graphql_auto.debugging import DebugHooks, PerformanceMonitor, QueryAnalyzer

# Set up debugging
debug_hooks = DebugHooks()
debug_hooks.register_pre_execution_hook(lambda query, variables: print(f"Executing: {query}"))

# Performance monitoring
monitor = PerformanceMonitor()
monitor.set_threshold('execution_time', 1000)  # 1 second threshold

# Query analysis
analyzer = QueryAnalyzer()
analysis = analyzer.analyze_query(query_string)
if analysis.complexity_score > 100:
    print("Query is too complex!")
```

### Schema Management

```python
from django_graphql_auto.management import SchemaManager, MigrationManager, BackupManager

# Schema lifecycle management
schema_manager = SchemaManager()
schema_manager.register_schema('new_api', schema, metadata={'version': '1.0.0'})

# Schema migration
migration_manager = MigrationManager()
migration_plan = migration_manager.create_migration(old_schema, new_schema)
migration_manager.execute_migration(migration_plan)

# Schema backup
backup_manager = BackupManager()
backup = backup_manager.create_backup('main_schema')
backup_manager.restore_backup(backup.backup_id)
```

## 🔄 Migration Guide

### From Standalone Project to Library

If you're migrating from a standalone GraphQL implementation:

#### 1. Update Dependencies

```bash
# Remove old dependencies
pip uninstall graphene-django

# Install rail-django-graphql
pip install rail-django-graphql
```

#### 2. Update Settings

```python
# Old settings.py
INSTALLED_APPS = [
    'graphene_django',
]

GRAPHENE = {
    'SCHEMA': 'myapp.schema.schema'
}

# New settings.py
INSTALLED_APPS = [
    'django_graphql_auto',
]

DJANGO_GRAPHQL_AUTO = {
    'DEFAULT_SCHEMA': 'main',
    'SCHEMAS': {
        'main': {
            'apps': ['myapp'],
        }
    }
}
```

#### 3. Update Schema Registration

```python
# Old schema.py
import graphene
from graphene_django import DjangoObjectType

schema = graphene.Schema(query=Query)

# New schema.py
import graphene
from django_graphql_auto import register_schema
from django_graphql_auto.types import DjangoObjectType

@register_schema('main')
class MainSchema(graphene.Schema):
    query = Query
```

#### 4. Update URLs

```python
# Old urls.py
from graphene_django.views import GraphQLView

urlpatterns = [
    path('graphql/', GraphQLView.as_view(graphiql=True)),
]

# New urls.py
from django.urls import include

urlpatterns = [
    path('graphql/', include('django_graphql_auto.urls')),
]
```

### From Single Schema to Multi-Schema

#### 1. Reorganize Schemas

```python
# Before: Single schema
class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderType)

# After: Multiple schemas
@register_schema('users')
class UserSchema(graphene.Schema):
    query = UserQuery

@register_schema('products')  
class ProductSchema(graphene.Schema):
    query = ProductQuery

@register_schema('orders')
class OrderSchema(graphene.Schema):
    query = OrderQuery
```

#### 2. Update Client Code

```javascript
// Before: Single endpoint
const client = new ApolloClient({
  uri: '/graphql/',
});

// After: Multiple endpoints
const userClient = new ApolloClient({
  uri: '/graphql/users/',
});

const productClient = new ApolloClient({
  uri: '/graphql/products/',
});
```

## 📚 Documentation

### Full Documentation

- **[Quick Start Guide](docs/quick-start.md)** - Get up and running in minutes
- **[Configuration Guide](docs/configuration-guide.md)** - Comprehensive configuration options
- **[API Reference](docs/api-reference.md)** - Complete API documentation
- **[Advanced Usage](docs/usage/advanced-usage.md)** - Advanced features and patterns
- **[Migration Guide](docs/migration/single-to-multi-schema.md)** - Migration strategies
- **[Performance Guide](docs/development/performance.md)** - Performance optimization
- **[Security Guide](docs/features/security.md)** - Security best practices
- **[Troubleshooting](docs/development/troubleshooting.md)** - Common issues and solutions

### Examples

- **[Basic Examples](docs/examples/basic-examples.md)** - Simple usage examples
- **[Advanced Examples](docs/examples/advanced-examples.md)** - Complex scenarios
- **[Authentication Examples](docs/examples/authentication-examples.md)** - Auth patterns
- **[Performance Examples](docs/examples/performance-examples.md)** - Performance optimization

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/raillogistic/rail-django-graphql.git
cd rail-django-graphql
pip install -e ".[dev]"
pre-commit install
```

### Running Tests

```bash
pytest
pytest --cov=django_graphql_auto
```

### Code Quality

```bash
black .
isort .
flake8
mypy django_graphql_auto
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [https://rail-django-graphql.readthedocs.io/](https://rail-django-graphql.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/raillogistic/rail-django-graphql/issues)
- **Discussions**: [GitHub Discussions](https://github.com/raillogistic/rail-django-graphql/discussions)
- **Email**: support@raillogistic.com

## 🗺️ Roadmap

- [ ] GraphQL Federation support
- [ ] Real-time subscriptions with WebSockets
- [ ] Advanced caching strategies
- [ ] GraphQL Code Generator integration
- [ ] Automated testing utilities
- [ ] Performance benchmarking tools
- [ ] Schema stitching capabilities
- [ ] Advanced security features

## 📊 Stats

![GitHub stars](https://img.shields.io/github/stars/raillogistic/rail-django-graphql)
![GitHub forks](https://img.shields.io/github/forks/raillogistic/rail-django-graphql)
![GitHub issues](https://img.shields.io/github/issues/raillogistic/rail-django-graphql)
![PyPI version](https://img.shields.io/pypi/v/rail-django-graphql)
![Python versions](https://img.shields.io/pypi/pyversions/rail-django-graphql)
![Django versions](https://img.shields.io/badge/django-3.2%2B-blue)

---

Made with ❤️ by [Rail Logistic](https://raillogistic.com)