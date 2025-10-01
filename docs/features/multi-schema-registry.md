# Multi-Schema Registry

The Multi-Schema Registry is a powerful feature that allows you to manage multiple GraphQL schemas within a single Django application. Each schema can have independent configurations, authentication requirements, and GraphiQL settings.

## 🎯 Overview

The schema registry provides:
- **Multiple GraphQL Schemas**: Register and manage multiple schemas independently
- **Per-Schema Configuration**: Each schema can have its own settings and authentication
- **Dynamic Schema Routing**: Route requests to different schemas based on URL patterns
- **Schema Discovery**: Automatic discovery of schemas from installed Django apps
- **Management API**: REST API for schema CRUD operations and monitoring

## 🚀 Quick Start

### Basic Schema Registration

```python
from rail_django_graphql.core.registry import schema_registry

# Register a simple schema
schema_registry.register_schema(
    name="public_api",
    description="Public API for customer access",
    apps=["customers", "products"],
    enabled=True,
    settings={
        "enable_graphiql": True,
        "authentication_required": False
    }
)

# Register a protected admin schema
schema_registry.register_schema(
    name="admin_api", 
    description="Admin API with authentication",
    apps=["admin", "users", "orders"],
    enabled=True,
    settings={
        "enable_graphiql": True,
        "authentication_required": True
    }
)
```

### URL Configuration

```python
# urls.py
from django.urls import path, include
from rail_django_graphql.views import MultiSchemaGraphQLView

urlpatterns = [
    # Multi-schema GraphQL endpoint
    path('graphql/<str:schema_name>/', MultiSchemaGraphQLView.as_view(), name='graphql-schema'),
    
    # Schema management API
    path('api/schemas/', include('rail_django_graphql.api.urls')),
]
```

## 📋 Schema Configuration

### Schema Registration Parameters

```python
schema_registry.register_schema(
    name="my_schema",                    # Unique schema identifier
    description="Schema description",     # Human-readable description
    version="1.0.0",                     # Schema version
    apps=["app1", "app2"],              # Django apps to include
    models=["Model1", "Model2"],        # Specific models to include
    exclude_models=["SensitiveModel"],   # Models to exclude
    enabled=True,                        # Enable/disable schema
    auto_discover=True,                  # Auto-discover models from apps
    settings={                           # Schema-specific settings
        "enable_graphiql": True,
        "authentication_required": False,
        "max_query_depth": 10,
        "enable_subscriptions": False
    }
)
```

### Settings Hierarchy

The system uses a three-tier settings hierarchy:

1. **Schema-level settings** (highest priority)
2. **Global Django settings** (`RAIL_DJANGO_GRAPHQL`)
3. **Library defaults** (lowest priority)

```python
# Django settings.py
RAIL_DJANGO_GRAPHQL = {
    "DEFAULT_SCHEMA": "main",
    "ENABLE_GRAPHIQL": False,  # Global default
    "AUTHENTICATION_REQUIRED": True,
}

# Schema-specific override
schema_registry.register_schema(
    name="public_api",
    settings={
        "enable_graphiql": True,  # Overrides global setting
        "authentication_required": False  # Overrides global setting
    }
)
```

## 🔐 Authentication & Security

### Per-Schema Authentication

```python
# Public schema - no authentication required
schema_registry.register_schema(
    name="public_api",
    settings={
        "authentication_required": False,
        "enable_graphiql": True
    }
)

# Protected schema - authentication required
schema_registry.register_schema(
    name="admin_api",
    settings={
        "authentication_required": True,
        "enable_graphiql": True  # GraphiQL will require authentication
    }
)
```

### Custom Authentication

```python
# In your Django settings
RAIL_DJANGO_GRAPHQL = {
    "AUTHENTICATION_BACKENDS": [
        "django.contrib.auth.backends.ModelBackend",
        "your_app.auth.CustomAuthBackend"
    ],
    "JWT_AUTHENTICATION": {
        "enabled": True,
        "secret_key": "your-secret-key",
        "algorithm": "HS256"
    }
}
```

## 🛠️ Schema Management

### Programmatic Management

```python
from rail_django_graphql.core.registry import schema_registry

# List all schemas
schemas = schema_registry.list_schemas()

# Get specific schema
schema_info = schema_registry.get_schema("my_schema")

# Enable/disable schema
schema_registry.enable_schema("my_schema")
schema_registry.disable_schema("my_schema")

# Check if schema exists
exists = schema_registry.schema_exists("my_schema")

# Remove schema
schema_registry.unregister_schema("my_schema")

# Auto-discover schemas from apps
discovered_count = schema_registry.auto_discover_schemas()
```

### Using Decorators

```python
from rail_django_graphql.decorators import register_schema

@register_schema(
    name="products_api",
    description="Products and inventory management",
    apps=["products", "inventory"]
)
class ProductsSchema:
    pass
```

## 🌐 REST API Management

The system provides a comprehensive REST API for schema management:

### List Schemas
```bash
GET /api/schemas/
GET /api/schemas/?enabled=true&app=products&format=detailed
```

### Create Schema
```bash
POST /api/schemas/
Content-Type: application/json

{
    "name": "new_schema",
    "description": "New schema description",
    "apps": ["app1", "app2"],
    "enabled": true,
    "settings": {
        "enable_graphiql": true,
        "authentication_required": false
    }
}
```

### Get Schema Details
```bash
GET /api/schemas/my_schema/
```

### Update Schema
```bash
PUT /api/schemas/my_schema/
Content-Type: application/json

{
    "description": "Updated description",
    "enabled": false
}
```

### Delete Schema
```bash
DELETE /api/schemas/my_schema/
```

### Management Operations
```bash
# Enable schema
POST /api/schemas/manage/
{
    "action": "enable",
    "schema_name": "my_schema"
}

# Disable schema
POST /api/schemas/manage/
{
    "action": "disable", 
    "schema_name": "my_schema"
}

# Clear all schemas
POST /api/schemas/manage/
{
    "action": "clear_all"
}
```

### Schema Discovery
```bash
# Trigger auto-discovery
POST /api/schemas/discover/

# Get discovery status
GET /api/schemas/discover/
```

### Health & Metrics
```bash
# Health check
GET /api/schemas/health/

# Detailed metrics
GET /api/schemas/metrics/
```

## 🔍 Schema Introspection

### GraphQL Introspection

```graphql
# Get schema information
query {
  __schema {
    types {
      name
      description
    }
    queryType {
      name
    }
    mutationType {
      name
    }
  }
}
```

### Python Introspection

```python
from rail_django_graphql.core.registry import schema_registry

# Get schema builder
builder = schema_registry.get_schema_builder("my_schema")

# Get GraphQL schema object
graphql_schema = builder.build_schema()

# Introspect schema
from graphql import build_client_schema, get_introspection_query
introspection = graphql_schema.execute(get_introspection_query())
```

## 🎨 GraphiQL Configuration

### Per-Schema GraphiQL

Each schema can have independent GraphiQL configuration:

```python
schema_registry.register_schema(
    name="development_api",
    settings={
        "enable_graphiql": True,
        "graphiql_settings": {
            "title": "Development API Explorer",
            "default_query": '''
                query {
                  users {
                    id
                    username
                  }
                }
            ''',
            "headers": {
                "Authorization": "Bearer your-token"
            }
        }
    }
)
```

### Accessing GraphiQL

```bash
# Access GraphiQL for specific schema
http://localhost:8000/graphql/my_schema/

# GraphiQL will be available if:
# 1. Schema has enable_graphiql: True
# 2. Authentication passes (if required)
# 3. Schema is enabled
```

## 🚀 Advanced Usage

### Custom Schema Builders

```python
from rail_django_graphql.core.schema import BaseSchemaBuilder

class CustomSchemaBuilder(BaseSchemaBuilder):
    def build_schema(self):
        # Custom schema building logic
        schema = super().build_schema()
        # Add custom types, resolvers, etc.
        return schema

# Register with custom builder
schema_registry.register_schema(
    name="custom_schema",
    builder_class=CustomSchemaBuilder,
    apps=["myapp"]
)
```

### Schema Hooks

```python
from rail_django_graphql.plugins.hooks import schema_hooks

@schema_hooks.pre_register
def before_schema_register(schema_info):
    print(f"Registering schema: {schema_info.name}")

@schema_hooks.post_register  
def after_schema_register(schema_info):
    print(f"Schema registered: {schema_info.name}")

@schema_hooks.pre_build
def before_schema_build(schema_name, builder):
    print(f"Building schema: {schema_name}")
```

### Performance Optimization

```python
# Enable schema caching
RAIL_DJANGO_GRAPHQL = {
    "SCHEMA_CACHE": {
        "enabled": True,
        "timeout": 3600,  # 1 hour
        "key_prefix": "graphql_schema"
    },
    "QUERY_CACHE": {
        "enabled": True,
        "timeout": 300,   # 5 minutes
        "max_size": 1000
    }
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Schema Not Found**
   ```python
   # Check if schema is registered and enabled
   if not schema_registry.schema_exists("my_schema"):
       print("Schema not registered")
   
   schema_info = schema_registry.get_schema("my_schema")
   if not schema_info.enabled:
       print("Schema is disabled")
   ```

2. **Authentication Issues**
   ```python
   # Check authentication settings
   schema_info = schema_registry.get_schema("my_schema")
   auth_required = schema_info.settings.get("authentication_required", False)
   print(f"Authentication required: {auth_required}")
   ```

3. **GraphiQL Not Loading**
   ```python
   # Verify GraphiQL settings
   schema_info = schema_registry.get_schema("my_schema")
   graphiql_enabled = schema_info.settings.get("enable_graphiql", False)
   print(f"GraphiQL enabled: {graphiql_enabled}")
   ```

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger('rail_django_graphql').setLevel(logging.DEBUG)

# Check registry status
from rail_django_graphql.core.registry import schema_registry
print(f"Registered schemas: {[s.name for s in schema_registry.list_schemas()]}")
```

## 📚 Related Documentation

- [Schema Management API](../api/schema-management-api.md)
- [Multi-Schema Setup Guide](../usage/multi-schema-setup.md)
- [Configuration Guide](../configuration-guide.md)
- [Security Configuration](../setup/security-configuration.md)