# Using rail-django-graphql as a Third-Party Library

This guide explains how to use `rail-django-graphql` as a third-party library in your Django projects.

## 📦 Installation

### Option 1: Install from PyPI (Recommended for Production)

```bash
# Basic installation
pip install rail-django-graphql

# With optional dependencies
pip install rail-django-graphql[all]  # All features
pip install rail-django-graphql[auth,performance]  # Specific features
```

### Option 2: Install from Source (Development)

```bash
# Clone the repository
git clone https://github.com/raillogistic/rail-django-graphql.git
cd rail-django-graphql

# Install in development mode
pip install -e .

# Or install with all dependencies
pip install -e .[all]
```

### Option 3: Install from Local Path

```bash
# If you have the source code locally
pip install /path/to/rail-django-graphql

# Or in development mode
pip install -e /path/to/rail-django-graphql
```

## 🚀 Quick Setup in Your Django Project

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

    # Third-party apps
    'graphene_django',
    'corsheaders',  # Optional: for CORS support
    'rail_django_graphql',  # Add this line

    # Your apps
    'your_app',
]

# GraphQL Configuration
GRAPHENE = {
    'SCHEMA': 'your_project.schema.schema',  # Your main schema
    'MIDDLEWARE': [
        'rail_django_graphql.middleware.AuthenticationMiddleware',
        'rail_django_graphql.middleware.PermissionMiddleware',
    ],
}

# Rail Django GraphQL Configuration
RAIL_DJANGO_GRAPHQL = {
    'SCHEMAS': {
        'default': {
            'MODELS': [
                'your_app.models.YourModel',
                'your_app.models.AnotherModel',
            ],
            'ENABLE_MUTATIONS': True,
            'ENABLE_FILTERS': True,
            'ENABLE_PAGINATION': True,
            'ENABLE_SUBSCRIPTIONS': False,
            'MAX_PAGE_SIZE': 100,
            'DEFAULT_PAGE_SIZE': 20,
        }
    },
    'SECURITY': {
        'ENABLE_INTROSPECTION': True,  # Set to False in production
        'ENABLE_GRAPHIQL': True,       # Set to False in production
        'MAX_QUERY_DEPTH': 10,
        'MAX_QUERY_COMPLEXITY': 1000,
    },
    'PERFORMANCE': {
        'ENABLE_CACHING': True,
        'CACHE_TIMEOUT': 300,
        'ENABLE_DATALOADER': True,
    }
}
```

### 2. Create Your Schema

```python
# your_project/schema.py
import graphene
from rail_django_graphql import get_schema_builder

# Get the schema builder
SchemaBuilder = get_schema_builder()

# Build your schema
schema_builder = SchemaBuilder('default')
auto_schema = schema_builder.build()

class Query(auto_schema.Query):
    """Extend the auto-generated query with custom fields."""
    hello = graphene.String(default_value="Hello World!")
    
    def resolve_hello(self, info):
        return "Hello from your custom resolver!"

class Mutation(auto_schema.Mutation):
    """Extend the auto-generated mutations with custom mutations."""
    pass

# Create the final schema
schema = graphene.Schema(
    query=Query,
    mutation=Mutation
)
```

### 3. Add URL Configuration

```python
# your_project/urls.py
from django.contrib import admin
from django.urls import path, include
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    
    # Optional: Include health check endpoints
    path('health/', include('rail_django_graphql.health_urls')),
    
    # Optional: Include API management endpoints
    path('api/', include('rail_django_graphql.api.urls')),
]
```

## 🏗️ Advanced Usage Examples

### Custom Model Configuration

```python
# your_app/models.py
from django.db import models
from rail_django_graphql.decorators import graphql_model

@graphql_model(
    enable_mutations=['create', 'update', 'delete'],
    enable_filters=['name', 'created_at'],
    permissions=['view', 'add', 'change', 'delete']
)
class Product(models.Model):
    name = models.CharField("Nom du produit", max_length=200)
    description = models.TextField("Description", blank=True)
    price = models.DecimalField("Prix", max_digits=10, decimal_places=2)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    
    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
```

### Multiple Schema Configuration

```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    'SCHEMAS': {
        'public': {
            'MODELS': [
                'blog.models.Post',
                'blog.models.Category',
            ],
            'ENABLE_MUTATIONS': False,  # Read-only public API
            'PERMISSIONS': {
                'REQUIRE_AUTHENTICATION': False,
            }
        },
        'admin': {
            'MODELS': [
                'blog.models.Post',
                'blog.models.Category',
                'auth.models.User',
            ],
            'ENABLE_MUTATIONS': True,
            'PERMISSIONS': {
                'REQUIRE_AUTHENTICATION': True,
                'REQUIRE_STAFF': True,
            }
        }
    }
}
```

### Custom Resolvers and Mutations

```python
# your_app/graphql.py
import graphene
from rail_django_graphql import get_query_generator, get_mutation_generator
from .models import Product

# Get generators
QueryGenerator = get_query_generator()
MutationGenerator = get_mutation_generator()

class CustomProductQuery(graphene.ObjectType):
    """Custom queries for Product model."""
    
    featured_products = graphene.List(
        QueryGenerator.get_type_for_model(Product)
    )
    
    def resolve_featured_products(self, info):
        return Product.objects.filter(featured=True)

class CustomProductMutation(graphene.ObjectType):
    """Custom mutations for Product model."""
    
    mark_as_featured = graphene.Field(
        QueryGenerator.get_type_for_model(Product),
        id=graphene.ID(required=True)
    )
    
    def resolve_mark_as_featured(self, info, id):
        product = Product.objects.get(pk=id)
        product.featured = True
        product.save()
        return product
```

## 🔧 Configuration Options

### Security Settings

```python
RAIL_DJANGO_GRAPHQL = {
    'SECURITY': {
        'ENABLE_INTROSPECTION': False,  # Disable in production
        'ENABLE_GRAPHIQL': False,       # Disable in production
        'MAX_QUERY_DEPTH': 10,
        'MAX_QUERY_COMPLEXITY': 1000,
        'ENABLE_QUERY_WHITELIST': True,
        'ALLOWED_HOSTS': ['yourdomain.com'],
    }
}
```

### Performance Settings

```python
RAIL_DJANGO_GRAPHQL = {
    'PERFORMANCE': {
        'ENABLE_CACHING': True,
        'CACHE_BACKEND': 'redis',
        'CACHE_TIMEOUT': 300,
        'ENABLE_DATALOADER': True,
        'BATCH_SIZE': 100,
        'ENABLE_QUERY_OPTIMIZATION': True,
    }
}
```

### Authentication & Permissions

```python
RAIL_DJANGO_GRAPHQL = {
    'AUTHENTICATION': {
        'BACKEND': 'django.contrib.auth.backends.ModelBackend',
        'JWT_ENABLED': True,
        'JWT_SECRET_KEY': 'your-secret-key',
        'JWT_EXPIRATION_DELTA': 3600,  # 1 hour
    },
    'PERMISSIONS': {
        'DEFAULT_PERMISSION_CLASSES': [
            'rail_django_graphql.permissions.IsAuthenticated',
        ],
        'REQUIRE_AUTHENTICATION': True,
        'REQUIRE_STAFF': False,
    }
}
```

## 📚 Available Features

### Core Features
- ✅ Automatic schema generation from Django models
- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Advanced filtering and searching
- ✅ Pagination support
- ✅ Nested relationships
- ✅ Custom field resolvers

### Security Features
- ✅ Authentication middleware
- ✅ Permission-based access control
- ✅ Query depth limiting
- ✅ Query complexity analysis
- ✅ Rate limiting
- ✅ CORS support

### Performance Features
- ✅ DataLoader integration
- ✅ Query optimization
- ✅ Caching support
- ✅ Batch operations
- ✅ Connection pooling

### Monitoring Features
- ✅ Health check endpoints
- ✅ Metrics collection
- ✅ Performance monitoring
- ✅ Error tracking
- ✅ Logging integration

## 🧪 Testing Your Integration

```python
# tests/test_graphql.py
import pytest
from django.test import TestCase
from graphene.test import Client
from your_project.schema import schema

class GraphQLTestCase(TestCase):
    def setUp(self):
        self.client = Client(schema)
    
    def test_query_products(self):
        query = '''
            query {
                products {
                    edges {
                        node {
                            id
                            name
                            price
                        }
                    }
                }
            }
        '''
        result = self.client.execute(query)
        self.assertIsNone(result.errors)
        self.assertIn('products', result.data)
```

## 🚀 Production Deployment

### Environment Variables

```bash
# .env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
GRAPHQL_INTROSPECTION=False
GRAPHQL_GRAPHIQL=False
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

### Docker Integration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["gunicorn", "your_project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 📖 Additional Resources

- **Documentation**: [Full Documentation](./docs/)
- **Examples**: [Example Projects](./examples/)
- **API Reference**: [API Documentation](./docs/api/)
- **Contributing**: [Contributing Guide](./CONTRIBUTING.md)
- **Changelog**: [Release Notes](./CHANGELOG.md)

## 🆘 Troubleshooting

### Common Issues

1. **Import Error**: Make sure `rail_django_graphql` is in `INSTALLED_APPS`
2. **Schema Not Found**: Check your `GRAPHENE['SCHEMA']` setting
3. **Permission Denied**: Verify your authentication and permission settings
4. **Performance Issues**: Enable caching and DataLoader

### Getting Help

- 📧 Email: contact@raillogistic.com
- 🐛 Issues: [GitHub Issues](https://github.com/raillogistic/rail-django-graphql/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/raillogistic/rail-django-graphql/discussions)

---

**Happy GraphQL Development! 🚀**