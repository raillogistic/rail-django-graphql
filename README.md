# Rail Django GraphQL

[![CI](https://github.com/yourusername/rail-django-graphql/workflows/CI/badge.svg)](https://github.com/yourusername/rail-django-graphql/actions)
[![PyPI version](https://badge.fury.io/py/rail-django-graphql.svg)](https://badge.fury.io/py/rail-django-graphql)
[![Python versions](https://img.shields.io/pypi/pyversions/rail-django-graphql.svg)](https://pypi.org/project/rail-django-graphql/)
[![Django versions](https://img.shields.io/pypi/djversions/rail-django-graphql.svg)](https://pypi.org/project/rail-django-graphql/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A powerful Django library for automatic GraphQL schema generation with advanced features including type generation, query optimization, permissions, and comprehensive debugging tools.

## Features

- 🚀 **Automatic Schema Generation**: Generate GraphQL schemas from Django models with zero configuration
- 🔧 **Type Generators**: Automatic GraphQL type creation with customizable field mappings
- 🔍 **Query Optimization**: Built-in query optimization and N+1 problem prevention
- 🛡️ **Advanced Permissions**: Flexible permission system with field-level access control
- 🐛 **Debugging Tools**: Comprehensive debugging and introspection capabilities
- 📊 **Performance Monitoring**: Built-in performance metrics and query analysis
- 🔌 **Plugin System**: Extensible architecture with custom plugins
- 🎨 **GraphiQL Integration**: Enhanced GraphiQL interface with custom tools
- 📝 **Auto Documentation**: Automatic API documentation generation
- 🔒 **Security Features**: Built-in security measures and validation

## Installation

### From PyPI (Recommended)

```bash
pip install rail-django-graphql
```

### From GitHub (Development Version)

```bash
# Install directly from GitHub
pip install git+https://github.com/yourusername/rail-django-graphql.git

# Or clone and install locally
git clone https://github.com/yourusername/rail-django-graphql.git
cd rail-django-graphql
pip install -e .
```

### Optional Dependencies

Install additional features:

```bash
# Authentication support
pip install rail-django-graphql[auth]

# Performance optimizations
pip install rail-django-graphql[performance]

# Media handling
pip install rail-django-graphql[media]

# Monitoring and metrics
pip install rail-django-graphql[monitoring]

# All optional features
pip install rail-django-graphql[all]
```

## Quick Start

### 1. Add to Django Settings

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # GraphQL dependencies
    'graphene_django',
    'django_filters',
    'corsheaders',
    
    # Rail Django GraphQL
    'rail_django_graphql',
    
    # Your apps
    'your_app',
]

# GraphQL Configuration
GRAPHENE = {
    'SCHEMA': 'your_project.schema.schema',
    'MIDDLEWARE': [
        'rail_django_graphql.middleware.QueryOptimizationMiddleware',
        'rail_django_graphql.middleware.PermissionMiddleware',
        'rail_django_graphql.middleware.DebuggingMiddleware',
    ],
}

# Rail Django GraphQL Settings
RAIL_GRAPHQL = {
    'AUTO_GENERATE_SCHEMA': True,
    'ENABLE_DEBUGGING': True,
    'ENABLE_INTROSPECTION': True,
    'MAX_QUERY_DEPTH': 10,
    'ENABLE_QUERY_OPTIMIZATION': True,
}
```

### 2. Create Your Schema

```python
# schema.py
import graphene
from rail_django_graphql import (
    TypeGenerator,
    QueryGenerator,
    MutationGenerator,
    SchemaBuilder
)
from your_app.models import User, Post, Comment

# Generate types automatically
UserType = TypeGenerator.from_model(User)
PostType = TypeGenerator.from_model(Post)
CommentType = TypeGenerator.from_model(Comment)

# Generate queries
class Query(graphene.ObjectType):
    # Auto-generated queries
    users = QueryGenerator.list_field(User)
    user = QueryGenerator.detail_field(User)
    posts = QueryGenerator.list_field(Post)
    post = QueryGenerator.detail_field(Post)
    
    # Custom queries
    my_posts = graphene.List(PostType)
    
    def resolve_my_posts(self, info):
        return Post.objects.filter(author=info.context.user)

# Generate mutations
class Mutation(graphene.ObjectType):
    create_post = MutationGenerator.create_mutation(Post)
    update_post = MutationGenerator.update_mutation(Post)
    delete_post = MutationGenerator.delete_mutation(Post)

# Build schema
schema = SchemaBuilder.build(
    query=Query,
    mutation=Mutation,
    auto_discover=True  # Automatically discover and include all models
)
```

### 3. Add URLs

```python
# urls.py
from django.contrib import admin
from django.urls import path, include
from graphene_django.views import GraphQLView
from rail_django_graphql.views.graphql_views import (
    MultiSchemaGraphQLView,
    SchemaListView,
    GraphQLPlaygroundView,
)
from rail_django_graphql.health_urls import health_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    # Single schema endpoint (backward compatible)
    path('graphql/', GraphQLView.as_view(graphiql=True)),
    # Multi-schema endpoints
    path('graphql/<str:schema_name>/', MultiSchemaGraphQLView.as_view(), name='graphql-by-schema'),
    path('schemas/', SchemaListView.as_view(), name='graphql-schemas'),
    path('playground/<str:schema_name>/', GraphQLPlaygroundView.as_view(), name='graphql-playground'),
    # Health endpoints
    path('health/', include(health_urlpatterns)),
]
```

### 4. Run Migrations and Start Server

```bash
python manage.py migrate
python manage.py runserver
```

Visit `http://localhost:8000/graphql/` to access the GraphiQL interface.

## Advanced Usage
### Multi-Schema Setup

The library supports multiple schemas with per-schema settings, endpoints, and GraphiQL control.

1) Enable multi-schema in settings and register schemas via the registry:

```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    "MULTI_SCHEMA_ENABLED": True,
}

# myapp/schema_config.py
from rail_django_graphql.core.registry import schema_registry

schema_registry.register_schema(
    name="public_api",
    description="Public API for customers",
    version="1.0.0",
    apps=["customers", "products"],
    models=["Customer", "Product"],
    enabled=True,
    settings={
        "enable_graphiql": True,
        "authentication_required": False,
    },
)

schema_registry.register_schema(
    name="admin_api",
    description="Admin API for internal use",
    version="1.0.0",
    apps=["customers", "products", "orders"],
    models=["Customer", "Product", "Order", "User"],
    enabled=True,
    settings={
        "enable_graphiql": True,
        "authentication_required": True,
    },
)
```

2) Configure URLs to expose per-schema endpoints:

```python
from django.urls import path
from rail_django_graphql.views.graphql_views import MultiSchemaGraphQLView, SchemaListView, GraphQLPlaygroundView

urlpatterns = [
    path('graphql/<str:schema_name>/', MultiSchemaGraphQLView.as_view(), name='graphql-by-schema'),
    path('schemas/', SchemaListView.as_view(), name='graphql-schemas'),
    path('playground/<str:schema_name>/', GraphQLPlaygroundView.as_view(), name='graphql-playground'),
]
```

Endpoints provided:
- `GET/POST /graphql/<schema_name>/` — Execute queries against the specified schema
- `GET /schemas/` — List registered schemas and their metadata
- `GET /playground/<schema_name>/` — Open a schema-specific GraphQL Playground

3) Control per-schema authentication and GraphiQL:

```python
schema_registry.register_schema(
    name="secure_api",
    enabled=True,
    settings={
        "authentication_required": True,
        "permission_classes": ["django.contrib.auth.permissions.IsAuthenticated"],
        "enable_graphiql": False,  # Disable GraphiQL for production
    },
)
```

See more details in `rail_django_graphql/views/graphql_views.py` and the integration tests in `rail_django_graphql/tests/integration/test_multi_schema.py`.

### Custom Type Generation

```python
from rail_django_graphql import TypeGenerator
from your_app.models import User

# Basic type generation
UserType = TypeGenerator.from_model(User)

# Advanced type generation with custom fields
UserType = TypeGenerator.from_model(
    User,
    fields=['id', 'username', 'email', 'first_name', 'last_name'],
    exclude_fields=['password'],
    custom_fields={
        'full_name': graphene.String(),
        'post_count': graphene.Int(),
    },
    custom_resolvers={
        'full_name': lambda user, info: f"{user.first_name} {user.last_name}",
        'post_count': lambda user, info: user.posts.count(),
    }
)
```

### Permission System

```python
from rail_django_graphql.permissions import BasePermission

class IsOwnerOrReadOnly(BasePermission):
    def has_permission(self, info, obj=None):
        if info.context.method == 'GET':
            return True
        return obj and obj.owner == info.context.user

# Apply to queries
posts = QueryGenerator.list_field(
    Post,
    permission_classes=[IsOwnerOrReadOnly]
)
```

### Query Optimization

```python
# Automatic optimization is enabled by default
# Manual optimization for complex queries
from rail_django_graphql.optimization import QueryOptimizer

class Query(graphene.ObjectType):
    posts = graphene.List(PostType)
    
    @QueryOptimizer.optimize(['author', 'comments__user'])
    def resolve_posts(self, info):
        return Post.objects.all()
```

## Configuration

### Settings Reference

```python
RAIL_GRAPHQL = {
    # Schema Generation
    'AUTO_GENERATE_SCHEMA': True,
    'AUTO_DISCOVER_MODELS': True,
    'SCHEMA_OUTPUT_PATH': 'schema.json',
    
    # Security
    'ENABLE_INTROSPECTION': True,  # Disable in production
    'MAX_QUERY_DEPTH': 10,
    'MAX_QUERY_COMPLEXITY': 1000,
    'ENABLE_QUERY_WHITELIST': False,
    
    # Performance
    'ENABLE_QUERY_OPTIMIZATION': True,
    'ENABLE_DATALOADER': True,
    'CACHE_TIMEOUT': 300,
    
    # Debugging
    'ENABLE_DEBUGGING': True,  # Disable in production
    'LOG_QUERIES': True,
    'LOG_SLOW_QUERIES': True,
    'SLOW_QUERY_THRESHOLD': 1.0,  # seconds
    
    # Permissions
    'DEFAULT_PERMISSION_CLASSES': [
        'rail_django_graphql.permissions.IsAuthenticated',
    ],
    'ENABLE_FIELD_PERMISSIONS': True,
    
    # Extensions
    'ENABLE_EXTENSIONS': True,
    'EXTENSION_CLASSES': [
        'rail_django_graphql.extensions.QueryComplexityExtension',
        'rail_django_graphql.extensions.PerformanceExtension',
    ],
}
```

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/rail-django-graphql.git
cd rail-django-graphql

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e .

# Run tests
python -m pytest

# Run linting
black rail_django_graphql
isort rail_django_graphql
flake8 rail_django_graphql
mypy rail_django_graphql
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=rail_django_graphql --cov-report=html

# Run specific test file
python -m pytest rail_django_graphql/tests/test_generators.py

# Run with verbose output
python -m pytest -v
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Run the test suite (`python -m pytest`)
6. Run linting (`black . && isort . && flake8`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## Documentation

- [Full Documentation](https://rail-django-graphql.readthedocs.io/)
- [API Reference](https://rail-django-graphql.readthedocs.io/en/latest/api/)
- [Examples](examples/)
- [Changelog](CHANGELOG.md)

## Requirements

- Python 3.8+
- Django 4.2+
- graphene-django 3.0+

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- [GitHub Issues](https://github.com/yourusername/rail-django-graphql/issues)
- [Discussions](https://github.com/yourusername/rail-django-graphql/discussions)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/rail-django-graphql)

## Acknowledgments

- Built on top of [Graphene-Django](https://github.com/graphql-python/graphene-django)
- Inspired by Django REST Framework's design patterns
- Thanks to all contributors and the Django/GraphQL community