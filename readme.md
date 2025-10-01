# Django GraphQL Multi-Schema System

A comprehensive Django package for managing multiple GraphQL schemas with advanced features including schema discovery, plugin architecture, and REST API management.

## Features

### Core Features
- 🚀 **Multi-Schema Support**: Register and manage multiple GraphQL schemas
- 🔍 **Dynamic Schema Discovery**: Automatic schema detection from Django apps
- 📋 **Schema Registry**: Centralized schema management with metadata
- 🔌 **Plugin Architecture**: Extensible plugin system for custom functionality
- 🌐 **REST API**: Complete REST API for schema management and monitoring
- 💚 **Health Checks**: Built-in health monitoring and metrics
- 🔒 **Thread Safety**: Thread-safe operations for production environments

### Advanced Features
- 🪝 **Discovery Hooks**: Pre/post registration hooks for custom logic
- 📈 **Schema Versioning**: Version management for schema evolution
- 📊 **Performance Monitoring**: Built-in metrics and performance tracking
- 🌍 **CORS Support**: Cross-origin resource sharing for API endpoints
- 🎯 **Decorator-based Registration**: Simple decorators for schema registration
- 🔎 **Auto-discovery**: Automatic schema detection from Django apps

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
```bash
pip install django-graphql-multi-schema
```

Add to your Django `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... your apps
    'rail_django_graphql',
]
```

Add URL patterns to your main `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... your patterns
    path('graphql/', include('rail_django_graphql.urls')),
]
```

## Quick Start

### 1. Basic Schema Registration

```python
# myapp/schema.py
import graphene
from rail_django_graphql.core.registry import schema_registry

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello World!")

schema = graphene.Schema(query=Query)

# Register the schema
schema_registry.register_schema(
    name='myapp_schema',
    description='My application GraphQL schema',
    version='1.0.0',
    apps=['myapp'],
    models=['MyModel'],
    schema=schema
)
```

### 2. Using Decorators

```python
# myapp/schema.py
from rail_django_graphql.decorators import register_schema
import graphene

@register_schema(
    name='decorated_schema',
    description='Schema registered with decorator',
    version='1.0.0'
)
class MySchema:
    def get_schema(self):
        return graphene.Schema(query=Query)
```

### 3. Auto-Discovery

Create a `graphql_schema.py` file in your Django app:

```python
# myapp/graphql_schema.py
import graphene
from rail_django_graphql.core.registry import register_schema

class Query(graphene.ObjectType):
    hello = graphene.String(default_value="Hello from auto-discovery!")

# This will be automatically discovered
register_schema(
    name='auto_discovered_schema',
    description='Automatically discovered schema',
    schema=graphene.Schema(query=Query)
)
```

## Schema Registration

### Manual Registration

```python
from rail_django_graphql.core.registry import schema_registry

schema_info = schema_registry.register_schema(
    name='my_schema',
    description='My GraphQL schema',
    version='1.0.0',
    apps=['app1', 'app2'],
    models=['Model1', 'Model2'],
    exclude_models=['ExcludedModel'],
    settings={'custom_setting': 'value'},
    auto_discover=True,
    enabled=True,
    schema=my_graphene_schema
)
```

### Schema Builder Pattern

```python
from rail_django_graphql.core.registry import schema_registry

def build_my_schema():
    # Custom schema building logic
    return graphene.Schema(query=MyQuery)

schema_registry.register_schema(
    name='builder_schema',
    builder=build_my_schema
)
```

### Decorator Registration

```python
from rail_django_graphql.decorators import register_schema

@register_schema(
    name='user_schema',
    description='User management schema',
    apps=['users'],
    models=['User', 'Profile']
)
class UserSchema:
    def get_schema(self):
        return graphene.Schema(query=UserQuery)
```

## Multi-Schema Routing

The system provides multiple GraphQL endpoints:

### Schema-Specific Endpoints

```
/graphql/<schema_name>/          # GraphQL endpoint for specific schema
/graphql/<schema_name>/playground/  # GraphiQL playground for specific schema
```

### Multi-Schema Endpoints

```
/graphql/                        # Default GraphQL endpoint
/playground/                     # GraphiQL playground with schema selector
/graphql/schemas/               # List all available schemas
```

### URL Configuration

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path('graphql/', include('rail_django_graphql.urls')),
]
```

## REST API

The system provides a comprehensive REST API for schema management:

### Schema Management

```bash
# List all schemas
GET /api/v1/schemas/

# Get specific schema
GET /api/v1/schemas/{schema_name}/

# Create new schema
POST /api/v1/schemas/
{
    "name": "new_schema",
    "description": "New schema",
    "version": "1.0.0",
    "apps": ["myapp"],
    "enabled": true
}

# Update schema
PUT /api/v1/schemas/{schema_name}/
{
    "description": "Updated description",
    "enabled": false
}

# Delete schema
DELETE /api/v1/schemas/{schema_name}/
```

### Management Operations

```bash
# Enable schema
POST /api/v1/management/
{
    "action": "enable",
    "schema_name": "my_schema"
}

# Disable schema
POST /api/v1/management/
{
    "action": "disable",
    "schema_name": "my_schema"
}

# Clear all schemas
POST /api/v1/management/
{
    "action": "clear_all"
}
```

### Discovery and Health

```bash
# Trigger schema discovery
POST /api/v1/discovery/

# Get discovery status
GET /api/v1/discovery/

# Health check
GET /api/v1/health/

# Get metrics
GET /api/v1/metrics/
```

## Plugin System

### Creating a Plugin

```python
# myplugin.py
from rail_django_graphql.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    name = 'my_plugin'
    version = '1.0.0'
    
    def on_pre_registration(self, schema_name, **kwargs):
        """Called before schema registration."""
        print(f"Registering schema: {schema_name}")
        return kwargs  # Can modify registration arguments
    
    def on_post_registration(self, schema_name, schema_info):
        """Called after schema registration."""
        print(f"Schema {schema_name} registered successfully")
    
    def on_schema_discovery(self, discovered_schemas):
        """Called after schema discovery."""
        print(f"Discovered {len(discovered_schemas)} schemas")
    
    def validate_schema(self, schema_info):
        """Validate schema configuration."""
        if not schema_info.description:
            raise ValueError("Schema must have a description")
        return True
```

### Plugin Configuration

```python
# settings.py
GRAPHQL_SCHEMA_PLUGINS = [
    'myapp.plugins.MyPlugin',
    'another_app.plugins.AnotherPlugin',
]

GRAPHQL_SCHEMA_PLUGIN_SETTINGS = {
    'my_plugin': {
        'enabled': True,
        'config': {'setting': 'value'}
    }
}
```

## Discovery Hooks

### Adding Hooks

```python
from rail_django_graphql.core.registry import schema_registry

def my_pre_hook(schema_name, **kwargs):
    """Modify schema registration arguments."""
    kwargs['description'] = f"Enhanced: {kwargs.get('description', '')}"
    return kwargs

def my_post_hook(schema_name, schema_info):
    """Perform actions after registration."""
    print(f"Schema {schema_name} registered with version {schema_info.version}")

# Add hooks
schema_registry.add_pre_registration_hook(my_pre_hook)
schema_registry.add_post_registration_hook(my_post_hook)
```

### Hook Registry

```python
from rail_django_graphql.plugins.hooks import hook_registry

# Register hooks independently
hook_registry.register_hook('pre_registration', my_pre_hook, 'my_hook')
hook_registry.register_hook('post_registration', my_post_hook, 'my_post_hook')

# Execute hooks
modified_kwargs = hook_registry.execute_hooks_with_data('pre_registration', kwargs)
hook_registry.execute_hooks('post_registration', schema_name, schema_info)
```

## Configuration

### Django Settings

```python
# settings.py

# Enable/disable auto-discovery
GRAPHQL_SCHEMA_AUTO_DISCOVERY = True

# Discovery paths
GRAPHQL_SCHEMA_DISCOVERY_PATHS = [
    'graphql_schema.py',
    'schema.py',
    'graphql/schema.py'
]

# Plugin configuration
GRAPHQL_SCHEMA_PLUGINS = [
    'myapp.plugins.MyPlugin',
]

# API settings
GRAPHQL_SCHEMA_API_CORS_ENABLED = True
GRAPHQL_SCHEMA_API_AUTH_REQUIRED = False

# Performance settings
GRAPHQL_SCHEMA_CACHE_ENABLED = True
GRAPHQL_SCHEMA_CACHE_TIMEOUT = 3600

# Logging
LOGGING = {
    'loggers': {
        'rail_django_graphql': {
            'level': 'INFO',
            'handlers': ['console'],
        }
    }
}
```

### Schema Configuration

```python
# In your schema files
SCHEMA_CONFIG = {
    'name': 'my_schema',
    'description': 'My application schema',
    'version': '1.0.0',
    'apps': ['myapp'],
    'models': ['MyModel'],
    'settings': {
        'enable_subscriptions': True,
        'max_query_depth': 10
    }
}
```
## Testing

### Unit Tests

```python
# test_schemas.py
from django.test import TestCase
from rail_django_graphql.core.registry import schema_registry

class SchemaRegistryTest(TestCase):
    def setUp(self):
        schema_registry.clear()
    
    def test_schema_registration(self):
        schema_info = schema_registry.register_schema(
            name='test_schema',
            description='Test schema'
        )
        
        self.assertEqual(schema_info.name, 'test_schema')
        self.assertTrue(schema_registry.schema_exists('test_schema'))
    
    def test_schema_retrieval(self):
        schema_registry.register_schema(name='test_schema')
        schema_info = schema_registry.get_schema('test_schema')
        
        self.assertIsNotNone(schema_info)
        self.assertEqual(schema_info.name, 'test_schema')
```

### Integration Tests

```python
# test_api.py
from django.test import TestCase, Client
import json

class SchemaAPITest(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_list_schemas(self):
        response = self.client.get('/api/v1/schemas/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('schemas', data['data'])
    
    def test_create_schema(self):
        schema_data = {
            'name': 'test_schema',
            'description': 'Test schema',
            'version': '1.0.0'
        }
        
        response = self.client.post(
            '/api/v1/schemas/',
            data=json.dumps(schema_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
```

### Running Tests

```bash
# Run all tests
python manage.py test rail_django_graphql

# Run specific test modules
python manage.py test rail_django_graphql.tests.unit
python manage.py test rail_django_graphql.tests.integration

# Run with coverage
coverage run --source='.' manage.py test rail_django_graphql
coverage report
```

## API Reference

### Schema Registry

#### Methods

- `register_schema(name, **kwargs)` - Register a new schema
- `unregister_schema(name)` - Remove a schema
- `get_schema(name)` - Get schema information
- `list_schemas()` - List all registered schemas
- `schema_exists(name)` - Check if schema exists
- `enable_schema(name)` - Enable a schema
- `disable_schema(name)` - Disable a schema
- `clear()` - Remove all schemas
- `auto_discover_schemas()` - Trigger auto-discovery

#### Schema Info Properties

- `name` - Schema name
- `description` - Schema description
- `version` - Schema version
- `apps` - Associated Django apps
- `models` - Included models
- `exclude_models` - Excluded models
- `enabled` - Whether schema is enabled
- `auto_discover` - Whether schema supports auto-discovery
- `settings` - Custom settings dictionary
- `schema` - GraphQL schema instance
- `builder` - Schema builder function

### Decorators

#### `@register_schema(**kwargs)`

Register a class or function as a schema provider.

```python
@register_schema(name='my_schema', version='1.0.0')
class MySchema:
    def get_schema(self):
        return graphene.Schema(query=MyQuery)
```

### Plugin Base Classes

#### `BasePlugin`

Base class for creating plugins.

**Methods:**
- `on_pre_registration(schema_name, **kwargs)` - Pre-registration hook
- `on_post_registration(schema_name, schema_info)` - Post-registration hook
- `on_schema_discovery(discovered_schemas)` - Discovery hook
- `validate_schema(schema_info)` - Schema validation

#### `PluginManager`

Manages plugin loading and execution.

**Methods:**
- `load_plugins()` - Load plugins from settings
- `get_plugins()` - Get all loaded plugins
- `get_enabled_plugins()` - Get enabled plugins
- `run_pre_registration_hooks(schema_name, **kwargs)` - Run pre-registration hooks
- `run_post_registration_hooks(schema_name, schema_info)` - Run post-registration hooks

## Examples

### Complete Example: E-commerce Schema

```python
# ecommerce/graphql_schema.py
import graphene
from graphene_django import DjangoObjectType
from rail_django_graphql.decorators import register_schema
from .models import Product, Category, Order

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = '__all__'

class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = '__all__'

class Query(graphene.ObjectType):
    products = graphene.List(ProductType)
    categories = graphene.List(CategoryType)
    
    def resolve_products(self, info):
        return Product.objects.all()
    
    def resolve_categories(self, info):
        return Category.objects.all()

class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Decimal(required=True)
        category_id = graphene.ID(required=True)
    
    product = graphene.Field(ProductType)
    
    def mutate(self, info, name, price, category_id):
        product = Product.objects.create(
            name=name,
            price=price,
            category_id=category_id
        )
        return CreateProduct(product=product)

class Mutation(graphene.ObjectType):
    create_product = CreateProduct.Field()

@register_schema(
    name='ecommerce_schema',
    description='E-commerce GraphQL schema',
    version='1.0.0',
    apps=['ecommerce'],
    models=['Product', 'Category', 'Order'],
    settings={
        'enable_subscriptions': True,
        'max_query_depth': 5
    }
)
class EcommerceSchema:
    def get_schema(self):
        return graphene.Schema(
            query=Query,
            mutation=Mutation
        )
```

### Custom Plugin Example

```python
# myapp/plugins.py
from rail_django_graphql.plugins.base import BasePlugin
import logging

logger = logging.getLogger(__name__)

class AuditPlugin(BasePlugin):
    name = 'audit_plugin'
    version = '1.0.0'
    
    def on_pre_registration(self, schema_name, **kwargs):
        """Log schema registration attempts."""
        logger.info(f"Attempting to register schema: {schema_name}")
        
        # Add audit metadata
        kwargs.setdefault('settings', {})
        kwargs['settings']['registered_by'] = 'audit_plugin'
        kwargs['settings']['registration_time'] = timezone.now().isoformat()
        
        return kwargs
    
    def on_post_registration(self, schema_name, schema_info):
        """Log successful registrations."""
        logger.info(f"Successfully registered schema: {schema_name} v{schema_info.version}")
        
        # Could send to external audit system
        self.send_audit_event('schema_registered', {
            'schema_name': schema_name,
            'version': schema_info.version,
            'apps': schema_info.apps
        })
    
    def validate_schema(self, schema_info):
        """Validate schema meets audit requirements."""
        if not schema_info.description:
            raise ValueError(f"Schema {schema_info.name} must have a description for audit compliance")
        
        if not schema_info.version:
            raise ValueError(f"Schema {schema_info.name} must have a version for audit compliance")
        
        return True
    
    def send_audit_event(self, event_type, data):
        """Send audit event to external system."""
        # Implementation would depend on your audit system
        pass
```

### Advanced Discovery Hook

```python
# myapp/hooks.py
from rail_django_graphql.core.registry import schema_registry
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def environment_aware_hook(schema_name, **kwargs):
    """Modify schema registration based on environment."""
    
    # Add environment-specific settings
    env = getattr(settings, 'ENVIRONMENT', 'development')
    
    kwargs.setdefault('settings', {})
    kwargs['settings']['environment'] = env
    
    # Disable certain schemas in production
    if env == 'production' and schema_name.endswith('_test'):
        kwargs['enabled'] = False
        logger.warning(f"Disabled test schema {schema_name} in production")
    
    # Add debug information in development
    if env == 'development':
        kwargs['settings']['debug'] = True
        kwargs['description'] = f"[DEV] {kwargs.get('description', '')}"
    
    return kwargs

def schema_validation_hook(schema_name, schema_info):
    """Validate schema after registration."""
    
    # Check for required models
    required_models = getattr(settings, 'REQUIRED_MODELS', [])
    missing_models = set(required_models) - set(schema_info.models)
    
    if missing_models:
        logger.warning(f"Schema {schema_name} missing required models: {missing_models}")
    
    # Log schema statistics
    logger.info(f"Schema {schema_name} registered with {len(schema_info.models)} models")

# Register hooks
schema_registry.add_pre_registration_hook(environment_aware_hook)
schema_registry.add_post_registration_hook(schema_validation_hook)
```

## Contributing

### Development Setup

```bash
# Clone the repository
git clone https://github.com/your-org/django-graphql-multi-schema.git
cd django-graphql-multi-schema

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
python manage.py test

# Run linting
flake8 rail_django_graphql/
black rail_django_graphql/
isort rail_django_graphql/
```

### Code Style

- Follow PEP 8
- Use type hints where appropriate
- Write comprehensive docstrings
- Add unit tests for new features
- Update documentation for API changes

### Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### Version 1.0.0
- Initial release
- Multi-schema support
- Schema registry
- Plugin architecture
- REST API
- Auto-discovery
- Discovery hooks
- Comprehensive test suite

## Support

- **Documentation**: [Full documentation](https://django-graphql-multi-schema.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/your-org/django-graphql-multi-schema/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/django-graphql-multi-schema/discussions)
- **Email**: support@your-org.com

## Acknowledgments

- Built on top of [Graphene-Django](https://github.com/graphql-python/graphene-django)
- Inspired by Django's app registry system
- Thanks to all contributors and the GraphQL community
- Inspired by [Django REST Framework](https://www.django-rest-framework.org/)
- Thanks to all contributors and the open-source community