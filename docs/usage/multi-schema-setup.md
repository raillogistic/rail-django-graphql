# Multi-Schema Setup Guide

This guide walks you through setting up and using multiple GraphQL schemas in your Django application using the `rail_django_graphql` package.

## 🎯 Overview

Multi-schema support allows you to:
- **Separate APIs by purpose**: Public API, Admin API, Partner API
- **Organize by domain**: User management, Product catalog, Order processing
- **Control access**: Different authentication and permission levels
- **Version APIs**: Maintain multiple API versions simultaneously

## 🚀 Quick Start

### 1. Basic Multi-Schema Setup

First, ensure you have the package installed and configured:

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'graphene_django',
    'rail_django_graphql',  # Add this
    'myapp',  # Your Django apps
]

# Basic configuration
RAIL_DJANGO_GRAPHQL = {
    "MULTI_SCHEMA_ENABLED": True,
    "AUTO_DISCOVER_SCHEMAS": True,
}
```

### 2. Register Your First Schema

Create a schema configuration in your app:

```python
# myapp/schema_config.py
from rail_django_graphql.core.registry import schema_registry

# Register a public API schema
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
        "max_query_depth": 10,
    }
)

# Register an admin API schema
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
        "max_query_depth": 15,
    }
)
```

### 3. Configure URLs

Add multi-schema URLs to your project:

```python
# urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', include('rail_django_graphql.urls')),  # Multi-schema URLs
]
```

This automatically provides:
- `/graphql/public_api/` - Public API endpoint
- `/graphql/admin_api/` - Admin API endpoint
- `/graphql/public_api/graphiql/` - Public API GraphiQL interface
- `/graphql/admin_api/graphiql/` - Admin API GraphiQL interface

### 4. Test Your Setup

Start your development server and visit:
- `http://localhost:8000/graphql/public_api/graphiql/` - Public API playground
- `http://localhost:8000/graphql/admin_api/graphiql/` - Admin API playground

## 📋 Schema Configuration Options

### Complete Schema Configuration

```python
from rail_django_graphql.core.registry import schema_registry

schema_registry.register_schema(
    # Basic Information
    name="my_api",                    # Unique schema identifier
    description="My API description", # Human-readable description
    version="1.0.0",                 # API version
    
    # Model Selection
    apps=["app1", "app2"],           # Django apps to include
    models=["Model1", "Model2"],     # Specific models to include
    exclude_models=["SensitiveModel"], # Models to exclude
    
    # Schema Behavior
    enabled=True,                    # Enable/disable schema
    auto_discover=True,              # Auto-discover models from apps
    
    # Schema Settings
    settings={
        # GraphiQL Configuration
        "enable_graphiql": True,
        "graphiql_template": "custom_graphiql.html",
        
        # Authentication & Security
        "authentication_required": False,
        "permission_classes": ["myapp.permissions.CustomPermission"],
        
        # Query Limits
        "max_query_depth": 10,
        "max_query_complexity": 1000,
        "query_timeout": 30,
        
        # Caching
        "enable_query_caching": True,
        "cache_timeout": 300,
        
        # Custom Middleware
        "middleware": ["myapp.middleware.CustomMiddleware"],
        
        # CORS Settings
        "cors_enabled": True,
        "cors_origins": ["http://localhost:3000"],
    }
)
```

### Settings Hierarchy

Settings are applied in this order (later overrides earlier):
1. Global defaults from `RAIL_DJANGO_GRAPHQL`
2. Schema-specific settings
3. Runtime overrides

```python
# settings.py - Global defaults
RAIL_DJANGO_GRAPHQL = {
    "DEFAULT_SCHEMA_SETTINGS": {
        "enable_graphiql": True,
        "authentication_required": False,
        "max_query_depth": 10,
    }
}

# Schema-specific override
schema_registry.register_schema(
    name="secure_api",
    settings={
        "authentication_required": True,  # Overrides global default
        "max_query_depth": 5,            # Overrides global default
        # enable_graphiql inherits global default (True)
    }
)
```

## 🔐 Authentication & Security

### Per-Schema Authentication

```python
# Public API - No authentication
schema_registry.register_schema(
    name="public_api",
    settings={
        "authentication_required": False,
    }
)

# Admin API - Requires authentication
schema_registry.register_schema(
    name="admin_api",
    settings={
        "authentication_required": True,
        "permission_classes": ["django.contrib.auth.permissions.IsAuthenticated"],
    }
)

# Partner API - Custom authentication
schema_registry.register_schema(
    name="partner_api",
    settings={
        "authentication_required": True,
        "permission_classes": ["myapp.permissions.IsPartner"],
    }
)
```

### Custom Permission Classes

```python
# myapp/permissions.py
from django.contrib.auth.models import Permission
from graphql import GraphQLError

class IsPartner:
    def has_permission(self, info):
        user = info.context.user
        if not user.is_authenticated:
            raise GraphQLError("Authentication required")
        
        if not user.groups.filter(name="Partners").exists():
            raise GraphQLError("Partner access required")
        
        return True

# Register schema with custom permission
schema_registry.register_schema(
    name="partner_api",
    settings={
        "authentication_required": True,
        "permission_classes": ["myapp.permissions.IsPartner"],
    }
)
```

## 🎨 Custom Schema Builders

### Using Custom Schema Builder

```python
# myapp/builders.py
from rail_django_graphql.core.builders import BaseSchemaBuilder
import graphene

class CustomSchemaBuilder(BaseSchemaBuilder):
    def build_query(self):
        """Build custom query with additional fields"""
        base_query = super().build_query()
        
        class CustomQuery(base_query):
            # Add custom fields
            api_version = graphene.String()
            server_time = graphene.DateTime()
            
            def resolve_api_version(self, info):
                return "1.0.0"
            
            def resolve_server_time(self, info):
                from datetime import datetime
                return datetime.now()
        
        return CustomQuery
    
    def build_mutation(self):
        """Build custom mutations"""
        base_mutation = super().build_mutation()
        
        class CustomMutation(base_mutation):
            # Add custom mutations
            ping = graphene.String()
            
            def resolve_ping(self, info):
                return "pong"
        
        return CustomMutation

# Register schema with custom builder
from rail_django_graphql.core.registry import schema_registry

schema_registry.register_schema(
    name="custom_api",
    apps=["myapp"],
    builder_class="myapp.builders.CustomSchemaBuilder",
)
```

### Schema Hooks

```python
# myapp/hooks.py
from rail_django_graphql.core.hooks import SchemaHook

class LoggingHook(SchemaHook):
    def before_schema_build(self, schema_config):
        """Called before schema is built"""
        print(f"Building schema: {schema_config.name}")
    
    def after_schema_build(self, schema_config, schema):
        """Called after schema is built"""
        print(f"Schema built: {schema_config.name}")
    
    def before_query_execution(self, schema_config, query, variables):
        """Called before each query execution"""
        print(f"Executing query on {schema_config.name}")
    
    def after_query_execution(self, schema_config, result):
        """Called after each query execution"""
        print(f"Query completed on {schema_config.name}")

# Register hook
from rail_django_graphql.core.registry import schema_registry

schema_registry.register_hook("logging", LoggingHook())

# Apply hook to schema
schema_registry.register_schema(
    name="logged_api",
    apps=["myapp"],
    settings={
        "hooks": ["logging"],
    }
)
```

## 🌐 Advanced URL Configuration

### Custom URL Patterns

```python
# urls.py
from django.urls import path, include
from rail_django_graphql.views import MultiSchemaGraphQLView

urlpatterns = [
    # Default multi-schema URLs
    path('graphql/', include('rail_django_graphql.urls')),
    
    # Custom schema endpoints
    path('api/v1/', MultiSchemaGraphQLView.as_view(schema_name="public_api_v1")),
    path('api/v2/', MultiSchemaGraphQLView.as_view(schema_name="public_api_v2")),
    path('admin/graphql/', MultiSchemaGraphQLView.as_view(schema_name="admin_api")),
    
    # Custom GraphiQL endpoints
    path('playground/', MultiSchemaGraphQLView.as_view(
        schema_name="public_api",
        graphiql=True,
        graphiql_template="custom_playground.html"
    )),
]
```

### Subdomain-Based Routing

```python
# urls.py
from django.urls import path
from rail_django_graphql.views import MultiSchemaGraphQLView

# Configure different schemas for different subdomains
urlpatterns = [
    # api.example.com
    path('graphql/', MultiSchemaGraphQLView.as_view(schema_name="public_api")),
    
    # admin.example.com  
    path('graphql/', MultiSchemaGraphQLView.as_view(schema_name="admin_api")),
    
    # partners.example.com
    path('graphql/', MultiSchemaGraphQLView.as_view(schema_name="partner_api")),
]

# Middleware to route based on subdomain
class SubdomainSchemaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        host = request.get_host().split(':')[0]  # Remove port
        subdomain = host.split('.')[0]
        
        # Map subdomain to schema
        schema_mapping = {
            'api': 'public_api',
            'admin': 'admin_api', 
            'partners': 'partner_api',
        }
        
        if subdomain in schema_mapping:
            request.schema_name = schema_mapping[subdomain]
        
        return self.get_response(request)
```

## 📊 Monitoring & Management

### Using the Management API

```python
# Check schema health
import requests

response = requests.get('http://localhost:8000/api/schemas/health/')
health_data = response.json()

print(f"System status: {health_data['data']['status']}")
print(f"Total schemas: {health_data['data']['total_schemas']}")
print(f"Enabled schemas: {health_data['data']['enabled_schemas']}")
```

### Programmatic Schema Management

```python
# In your Django code
from rail_django_graphql.core.registry import schema_registry

# List all schemas
schemas = schema_registry.list_schemas()
for schema in schemas:
    print(f"Schema: {schema.name}, Enabled: {schema.enabled}")

# Enable/disable schemas
schema_registry.enable_schema("public_api")
schema_registry.disable_schema("admin_api")

# Get schema details
schema = schema_registry.get_schema("public_api")
if schema:
    print(f"Apps: {schema.apps}")
    print(f"Models: {schema.models}")
    print(f"Settings: {schema.settings}")

# Update schema settings
schema_registry.update_schema("public_api", {
    "settings": {
        "max_query_depth": 15,
        "enable_graphiql": False,
    }
})
```

### Django Management Commands

```bash
# List all registered schemas
python manage.py list_schemas

# Enable/disable schemas
python manage.py enable_schema public_api
python manage.py disable_schema admin_api

# Discover schemas automatically
python manage.py discover_schemas

# Validate schema configurations
python manage.py validate_schemas

# Export schema configurations
python manage.py export_schemas --format json --output schemas.json

# Import schema configurations  
python manage.py import_schemas --input schemas.json
```

## 🔧 Configuration Examples

### E-commerce Platform

```python
# E-commerce multi-schema setup
from rail_django_graphql.core.registry import schema_registry

# Customer-facing API
schema_registry.register_schema(
    name="storefront_api",
    description="Customer-facing storefront API",
    version="1.0.0",
    apps=["products", "categories", "reviews"],
    models=["Product", "Category", "Review"],
    exclude_models=["ProductCost", "SupplierInfo"],
    settings={
        "enable_graphiql": True,
        "authentication_required": False,
        "max_query_depth": 8,
        "cors_enabled": True,
        "cors_origins": ["https://mystore.com"],
    }
)

# Admin management API
schema_registry.register_schema(
    name="admin_api",
    description="Admin management interface",
    version="1.0.0",
    apps=["products", "categories", "orders", "customers"],
    settings={
        "enable_graphiql": True,
        "authentication_required": True,
        "permission_classes": ["django.contrib.auth.permissions.IsStaff"],
        "max_query_depth": 15,
    }
)

# Partner/supplier API
schema_registry.register_schema(
    name="partner_api", 
    description="Partner and supplier API",
    version="1.0.0",
    apps=["products", "inventory"],
    models=["Product", "Inventory", "SupplierInfo"],
    settings={
        "authentication_required": True,
        "permission_classes": ["myapp.permissions.IsPartner"],
        "max_query_depth": 10,
    }
)
```

### Multi-tenant SaaS

```python
# Multi-tenant schema setup
def register_tenant_schema(tenant_name, tenant_apps):
    schema_registry.register_schema(
        name=f"tenant_{tenant_name}",
        description=f"API for {tenant_name}",
        version="1.0.0",
        apps=tenant_apps,
        settings={
            "authentication_required": True,
            "permission_classes": [f"tenants.permissions.IsTenant{tenant_name.title()}"],
            "middleware": [f"tenants.middleware.Tenant{tenant_name.title()}Middleware"],
        }
    )

# Register schemas for different tenants
register_tenant_schema("acme", ["acme_products", "acme_orders"])
register_tenant_schema("globex", ["globex_products", "globex_orders"])
register_tenant_schema("initech", ["initech_products", "initech_orders"])
```

## 🚨 Troubleshooting

### Common Issues

#### Schema Not Found
```python
# Error: Schema 'my_api' not found
# Solution: Check schema registration
from rail_django_graphql.core.registry import schema_registry

# List registered schemas
schemas = schema_registry.list_schemas()
print([s.name for s in schemas])

# Re-register if missing
schema_registry.register_schema(
    name="my_api",
    apps=["myapp"],
)
```

#### Authentication Errors
```python
# Error: Authentication required
# Solution: Check authentication settings
schema = schema_registry.get_schema("my_api")
print(f"Auth required: {schema.settings.get('authentication_required')}")

# Update authentication settings
schema_registry.update_schema("my_api", {
    "settings": {
        "authentication_required": False,  # or True
    }
})
```

#### GraphiQL Not Loading
```python
# Check GraphiQL settings
schema = schema_registry.get_schema("my_api")
print(f"GraphiQL enabled: {schema.settings.get('enable_graphiql')}")

# Enable GraphiQL
schema_registry.update_schema("my_api", {
    "settings": {
        "enable_graphiql": True,
    }
})
```

### Debug Mode

```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    "DEBUG": True,  # Enable debug logging
    "LOG_LEVEL": "DEBUG",
    "LOG_QUERIES": True,  # Log all GraphQL queries
}
```

### Health Checks

```python
# Check system health
from rail_django_graphql.core.registry import schema_registry

# Validate all schemas
issues = schema_registry.validate_schemas()
if issues:
    for issue in issues:
        print(f"Issue: {issue}")
else:
    print("All schemas are valid")

# Check individual schema
schema = schema_registry.get_schema("my_api")
if schema and schema.enabled:
    print(f"Schema {schema.name} is healthy")
else:
    print(f"Schema issues detected")
```

## 📚 Next Steps

- [Schema Management API](../api/schema-management-api.md) - REST API for managing schemas
- [Configuration Guide](../configuration-guide.md) - Detailed configuration options
- [Security Configuration](../setup/security-configuration.md) - Security best practices
- [Performance Optimization](../performance/optimization-guide.md) - Performance tuning