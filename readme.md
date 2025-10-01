# Rail Django GraphQL

A powerful, Django-agnostic GraphQL library that provides automatic schema generation, advanced permissions, and performance optimizations.

## Features

- 🚀 **Automatic Schema Generation**: Generate GraphQL schemas from your models with minimal configuration
- 🔐 **Advanced Permission System**: Fine-grained access control with role-based permissions
- ⚡ **Performance Optimized**: Built-in N+1 query optimization and caching
- 📁 **File Upload Support**: Handle file uploads with GraphQL mutations
- 📊 **Monitoring & Metrics**: Built-in performance monitoring and metrics collection
- 🔧 **Django Integration**: Seamless integration with Django projects
- 🎯 **Framework Agnostic Core**: Core library can be used with any Python web framework

## Installation

```bash
pip install rail-django-graphql
```

### Optional Dependencies

For specific features, install optional dependencies:

```bash
# Authentication and permissions
pip install rail-django-graphql[auth]

# Performance monitoring and caching
pip install rail-django-graphql[performance]

# File upload support
pip install rail-django-graphql[media]

# Monitoring and metrics
pip install rail-django-graphql[monitoring]

# Development tools
pip install rail-django-graphql[dev]

# All features
pip install rail-django-graphql[all]
```

## Quick Start

### 1. Add to Django Settings

```python
# settings.py
INSTALLED_APPS = [
    # ... your apps
    'rail_django_graphql',
    'graphene_django',
]

# GraphQL Configuration
GRAPHENE = {
    'SCHEMA': 'rail_django_graphql.schema.schema',
    'MIDDLEWARE': [
        'rail_django_graphql.middleware.AuthenticationMiddleware',
        'rail_django_graphql.middleware.PermissionMiddleware',
        'rail_django_graphql.middleware.PerformanceMiddleware',
    ],
}

# Rail Django GraphQL Settings
RAIL_DJANGO_GRAPHQL = {
    'AUTO_GENERATE_SCHEMA': True,
    'ENABLE_PERMISSIONS': True,
    'ENABLE_CACHING': True,
    'CACHE_TIMEOUT': 300,
    'MAX_QUERY_DEPTH': 10,
    'ENABLE_MONITORING': True,
}
```

### 2. Configure URLs

```python
# urls.py
from django.urls import path
from rail_django_graphql.views import GraphQLView

urlpatterns = [
    path('graphql/', GraphQLView.as_view(graphiql=True)),
]
```

### 3. Define Your Models

```python
# models.py
from django.db import models
from rail_django_graphql.decorators import graphql_model

@graphql_model
class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField()
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    is_active = models.BooleanField(default=True)

@graphql_model
class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 4. Run Migrations and Start

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Visit `http://localhost:8000/graphql/` to access GraphiQL interface.

## Configuration

### Core Settings

```python
RAIL_DJANGO_GRAPHQL = {
    # Schema Generation
    'AUTO_GENERATE_SCHEMA': True,
    'SCHEMA_OUTPUT_PATH': 'schema.graphql',
    
    # Performance
    'ENABLE_CACHING': True,
    'CACHE_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'rail_graphql',
    'MAX_QUERY_DEPTH': 10,
    'MAX_QUERY_COMPLEXITY': 1000,
    
    # Security
    'ENABLE_PERMISSIONS': True,
    'REQUIRE_AUTHENTICATION': False,
    'ALLOWED_HOSTS': ['*'],
    
    # Monitoring
    'ENABLE_MONITORING': True,
    'METRICS_BACKEND': 'prometheus',
    
    # File Uploads
    'ENABLE_FILE_UPLOADS': True,
    'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
    'ALLOWED_FILE_TYPES': ['image/*', 'application/pdf'],
}
```

## Advanced Usage

### Custom Permissions

```python
from rail_django_graphql.permissions import BasePermission

class IsOwnerOrReadOnly(BasePermission):
    def has_permission(self, info, obj=None):
        if info.context.method == 'GET':
            return True
        return obj.author == info.context.user

# Apply to model
@graphql_model(permissions=[IsOwnerOrReadOnly])
class Post(models.Model):
    # ... model fields
```

### Custom Resolvers

```python
from rail_django_graphql.resolvers import BaseResolver

class PostResolver(BaseResolver):
    def resolve_posts(self, info, **kwargs):
        # Custom logic here
        return Post.objects.filter(is_published=True)

# Register resolver
from rail_django_graphql.registry import resolver_registry
resolver_registry.register('Post', PostResolver)
```

### Performance Monitoring

```python
from rail_django_graphql.monitoring import monitor_query

@monitor_query
def resolve_complex_data(self, info, **kwargs):
    # This resolver will be monitored for performance
    return expensive_operation()
```

## Framework Agnostic Usage

The core library can be used without Django:

```python
from rail_django_graphql.core import GraphQLSchema
from rail_django_graphql.core.types import ObjectType
from rail_django_graphql.core.fields import Field

class UserType(ObjectType):
    id = Field(int)
    name = Field(str)
    email = Field(str)

schema = GraphQLSchema()
schema.add_type(UserType)
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/your-org/rail-django-graphql.git
cd rail-django-graphql
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Linting
flake8 rail_django_graphql/
black rail_django_graphql/
isort rail_django_graphql/

# Type checking
mypy rail_django_graphql/

# Security
bandit -r rail_django_graphql/
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## Support

- 📖 [Documentation](https://rail-django-graphql.readthedocs.io/)
- 🐛 [Issue Tracker](https://github.com/your-org/rail-django-graphql/issues)
- 💬 [Discussions](https://github.com/your-org/rail-django-graphql/discussions)
- 📧 [Email Support](mailto:support@rail-graphql.com)

## Acknowledgments

- Built on top of [Graphene](https://graphene-python.org/)
- Inspired by [Django REST Framework](https://www.django-rest-framework.org/)
- Thanks to all contributors and the open-source community