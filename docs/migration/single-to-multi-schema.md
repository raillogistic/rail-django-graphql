# Migration Guide: Single-Schema to Multi-Schema

This guide helps you migrate from a single GraphQL schema setup to the new multi-schema architecture in `rail_django_graphql`.

## 🎯 Overview

The multi-schema feature allows you to:
- **Maintain backward compatibility** with existing single-schema setups
- **Gradually migrate** to multi-schema architecture
- **Organize APIs** by purpose, domain, or access level
- **Improve security** with schema-specific authentication

## 📋 Migration Checklist

- [ ] Review current schema configuration
- [ ] Plan schema organization strategy
- [ ] Update Django settings
- [ ] Migrate URL patterns
- [ ] Test existing functionality
- [ ] Update client applications
- [ ] Deploy and monitor

## 🔍 Pre-Migration Assessment

### 1. Analyze Current Setup

First, understand your current configuration:

```python
# Current single-schema setup (settings.py)
RAIL_DJANGO_GRAPHQL = {
    'MUTATION_SETTINGS': {
        'enable_create_mutations': True,
        'enable_update_mutations': True,
        'enable_delete_mutations': True,
        'max_nested_depth': 3,
    },
    'TYPE_SETTINGS': {
        'enable_filtering': True,
        'enable_ordering': True,
        'enable_pagination': True,
        'default_page_size': 20,
    },
    'SCHEMA_SETTINGS': {
        'enable_introspection': True,
        'enable_playground': True,
        'schema_name': 'My API',
    },
    'SECURITY_SETTINGS': {
        'authentication_required': False,
        'max_query_depth': 10,
    }
}
```

### 2. Identify Migration Strategy

Choose your migration approach:

#### Option A: Gradual Migration (Recommended)
- Keep existing single schema as default
- Add new schemas incrementally
- Migrate clients gradually

#### Option B: Complete Migration
- Convert single schema to named schema
- Update all URLs and clients immediately

#### Option C: Hybrid Approach
- Maintain single schema for backward compatibility
- Add multi-schema for new features

## 🚀 Migration Steps

### Step 1: Enable Multi-Schema Support

Update your Django settings to enable multi-schema support while maintaining backward compatibility:

```python
# settings.py - Updated configuration
RAIL_DJANGO_GRAPHQL = {
    # Enable multi-schema support
    'MULTI_SCHEMA_ENABLED': True,
    'AUTO_DISCOVER_SCHEMAS': False,  # Manual control during migration
    
    # Backward compatibility - convert existing config to default schema
    'DEFAULT_SCHEMA_NAME': 'default',  # Name for your existing schema
    'MAINTAIN_LEGACY_URLS': True,      # Keep /graphql/ working
    
    # Default settings for all schemas (from your existing config)
    'DEFAULT_SCHEMA_SETTINGS': {
        'enable_graphiql': True,
        'authentication_required': False,
        'max_query_depth': 10,
        'enable_filtering': True,
        'enable_ordering': True,
        'enable_pagination': True,
        'default_page_size': 20,
        'enable_create_mutations': True,
        'enable_update_mutations': True,
        'enable_delete_mutations': True,
        'max_nested_depth': 3,
    },
    
    # Legacy settings (still supported)
    'MUTATION_SETTINGS': {
        'enable_create_mutations': True,
        'enable_update_mutations': True,
        'enable_delete_mutations': True,
        'max_nested_depth': 3,
    },
    'TYPE_SETTINGS': {
        'enable_filtering': True,
        'enable_ordering': True,
        'enable_pagination': True,
        'default_page_size': 20,
    },
    'SCHEMA_SETTINGS': {
        'enable_introspection': True,
        'enable_playground': True,
        'schema_name': 'My API',
    },
    'SECURITY_SETTINGS': {
        'authentication_required': False,
        'max_query_depth': 10,
    }
}
```

### Step 2: Register Your Default Schema

Create a schema registration for your existing setup:

```python
# myapp/schema_config.py
from rail_django_graphql.core.registry import schema_registry
from django.apps import apps

def register_default_schema():
    """Register the default schema with existing configuration"""
    
    # Get all your current apps and models
    all_apps = [app.label for app in apps.get_app_configs() 
                if app.label not in ['admin', 'auth', 'contenttypes', 'sessions']]
    
    schema_registry.register_schema(
        name="default",
        description="Default API (migrated from single schema)",
        version="1.0.0",
        apps=all_apps,  # Include all your existing apps
        enabled=True,
        settings={
            # Use your existing settings
            'enable_graphiql': True,
            'authentication_required': False,
            'max_query_depth': 10,
            'enable_filtering': True,
            'enable_ordering': True,
            'enable_pagination': True,
            'default_page_size': 20,
        }
    )

# Call this in your app's ready() method or at startup
register_default_schema()
```

### Step 3: Update URL Configuration

Update your URLs to support both legacy and multi-schema patterns:

```python
# urls.py - Migration-friendly URL configuration
from django.contrib import admin
from django.urls import path, include
from rail_django_graphql.views import MultiSchemaGraphQLView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Multi-schema URLs (new)
    path('graphql/', include('rail_django_graphql.urls')),
    
    # Legacy URL support (maintains backward compatibility)
    path('graphql/', MultiSchemaGraphQLView.as_view(
        schema_name="default",
        legacy_mode=True
    )),
    path('graphiql/', MultiSchemaGraphQLView.as_view(
        schema_name="default",
        graphiql=True,
        legacy_mode=True
    )),
]
```

This configuration provides:
- `/graphql/` - Legacy endpoint (uses default schema)
- `/graphiql/` - Legacy GraphiQL interface
- `/graphql/default/` - New multi-schema endpoint
- `/graphql/default/graphiql/` - New GraphiQL interface

### Step 4: Test Backward Compatibility

Verify that your existing setup still works:

```bash
# Test legacy endpoints
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { types { name } } }"}'

# Test new multi-schema endpoints
curl -X POST http://localhost:8000/graphql/default/ \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { types { name } } }"}'

# Visit GraphiQL interfaces
# http://localhost:8000/graphiql/ (legacy)
# http://localhost:8000/graphql/default/graphiql/ (new)
```

### Step 5: Add New Schemas

Now you can add additional schemas for different purposes:

```python
# myapp/schema_config.py - Add new schemas
def register_additional_schemas():
    # Public API for customers
    schema_registry.register_schema(
        name="public_api",
        description="Public API for customer applications",
        version="1.0.0",
        apps=["products", "categories", "reviews"],
        models=["Product", "Category", "Review"],
        exclude_models=["ProductCost", "InternalNotes"],
        settings={
            "enable_graphiql": True,
            "authentication_required": False,
            "max_query_depth": 8,
            "cors_enabled": True,
            "cors_origins": ["https://mystore.com"],
        }
    )
    
    # Admin API for internal tools
    schema_registry.register_schema(
        name="admin_api",
        description="Admin API for internal management",
        version="1.0.0",
        apps=["products", "orders", "customers", "analytics"],
        settings={
            "enable_graphiql": True,
            "authentication_required": True,
            "permission_classes": ["django.contrib.auth.permissions.IsStaff"],
            "max_query_depth": 15,
        }
    )
    
    # Partner API for external integrations
    schema_registry.register_schema(
        name="partner_api",
        description="Partner API for external integrations",
        version="1.0.0",
        apps=["products", "inventory"],
        models=["Product", "Inventory", "PartnerInfo"],
        settings={
            "authentication_required": True,
            "permission_classes": ["myapp.permissions.IsPartner"],
            "max_query_depth": 10,
            "enable_graphiql": False,  # Disable for external API
        }
    )

register_additional_schemas()
```

### Step 6: Update Client Applications

#### Gradual Client Migration

For existing clients, you can maintain the legacy endpoints while gradually migrating:

```javascript
// Option 1: Keep using legacy endpoint
const GRAPHQL_ENDPOINT = '/graphql/';

// Option 2: Migrate to specific schema endpoint
const GRAPHQL_ENDPOINT = '/graphql/default/';

// Option 3: Use different schemas for different purposes
const PUBLIC_API = '/graphql/public_api/';
const ADMIN_API = '/graphql/admin_api/';
```

#### Client Configuration Examples

```javascript
// React Apollo Client
import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client';

// Legacy setup (no changes needed)
const legacyClient = new ApolloClient({
  link: createHttpLink({ uri: '/graphql/' }),
  cache: new InMemoryCache(),
});

// Multi-schema setup
const publicClient = new ApolloClient({
  link: createHttpLink({ uri: '/graphql/public_api/' }),
  cache: new InMemoryCache(),
});

const adminClient = new ApolloClient({
  link: createHttpLink({ 
    uri: '/graphql/admin_api/',
    headers: {
      authorization: `Bearer ${getAuthToken()}`,
    }
  }),
  cache: new InMemoryCache(),
});
```

```python
# Python client
import requests

# Legacy endpoint
legacy_response = requests.post('/graphql/', json={
    'query': '{ products { id name } }'
})

# Multi-schema endpoints
public_response = requests.post('/graphql/public_api/', json={
    'query': '{ products { id name price } }'
})

admin_response = requests.post('/graphql/admin_api/', 
    json={'query': '{ products { id name cost profit } }'},
    headers={'Authorization': f'Bearer {token}'}
)
```

## 🔄 Migration Strategies

### Strategy 1: Feature-Based Migration

Migrate by adding new features to new schemas:

```python
# Phase 1: Keep existing functionality on default schema
# Phase 2: Add new features to specialized schemas
# Phase 3: Gradually move existing features

# Week 1: Add public API for new mobile app
schema_registry.register_schema(
    name="mobile_api",
    description="API for mobile applications",
    apps=["products", "users"],
    settings={"max_query_depth": 6}
)

# Week 2: Add admin API for new dashboard
schema_registry.register_schema(
    name="dashboard_api", 
    description="API for admin dashboard",
    apps=["analytics", "reports"],
    settings={"authentication_required": True}
)

# Week 3: Migrate existing web app to public_api
# Update web app to use /graphql/public_api/
```

### Strategy 2: Domain-Based Migration

Organize schemas by business domain:

```python
# User management schema
schema_registry.register_schema(
    name="users_api",
    apps=["users", "profiles", "authentication"],
    settings={"authentication_required": True}
)

# Product catalog schema  
schema_registry.register_schema(
    name="catalog_api",
    apps=["products", "categories", "inventory"],
    settings={"authentication_required": False}
)

# Order processing schema
schema_registry.register_schema(
    name="orders_api", 
    apps=["orders", "payments", "shipping"],
    settings={"authentication_required": True}
)
```

### Strategy 3: Access-Level Migration

Organize by access requirements:

```python
# Public access - no authentication
schema_registry.register_schema(
    name="public",
    models=["Product", "Category"],
    settings={"authentication_required": False}
)

# User access - basic authentication
schema_registry.register_schema(
    name="user",
    models=["Product", "Order", "Profile"],
    settings={"authentication_required": True}
)

# Admin access - staff only
schema_registry.register_schema(
    name="admin",
    apps=["all"],
    settings={
        "authentication_required": True,
        "permission_classes": ["django.contrib.auth.permissions.IsStaff"]
    }
)
```

## 🧪 Testing Migration

### Automated Testing

```python
# tests/test_migration.py
from django.test import TestCase, Client
from rail_django_graphql.core.registry import schema_registry
import json

class MigrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_legacy_endpoint_works(self):
        """Test that legacy /graphql/ endpoint still works"""
        response = self.client.post('/graphql/', {
            'query': '{ __schema { types { name } } }'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('data', data)
    
    def test_multi_schema_endpoints_work(self):
        """Test that new multi-schema endpoints work"""
        schemas = schema_registry.list_schemas()
        
        for schema in schemas:
            if schema.enabled:
                response = self.client.post(f'/graphql/{schema.name}/', {
                    'query': '{ __schema { types { name } } }'
                }, content_type='application/json')
                
                self.assertEqual(response.status_code, 200)
    
    def test_schema_isolation(self):
        """Test that schemas are properly isolated"""
        # Test that public API doesn't expose admin fields
        public_response = self.client.post('/graphql/public_api/', {
            'query': '{ __type(name: "User") { fields { name } } }'
        }, content_type='application/json')
        
        admin_response = self.client.post('/graphql/admin_api/', {
            'query': '{ __type(name: "User") { fields { name } } }'
        }, content_type='application/json')
        
        # Verify different field sets
        public_data = json.loads(public_response.content)
        admin_data = json.loads(admin_response.content)
        
        # Admin should have more fields than public
        if public_data['data']['__type'] and admin_data['data']['__type']:
            public_fields = len(public_data['data']['__type']['fields'])
            admin_fields = len(admin_data['data']['__type']['fields'])
            self.assertGreater(admin_fields, public_fields)
```

### Manual Testing Checklist

- [ ] Legacy `/graphql/` endpoint responds correctly
- [ ] Legacy `/graphiql/` interface loads and works
- [ ] New schema endpoints `/graphql/{schema_name}/` work
- [ ] New GraphiQL interfaces load correctly
- [ ] Authentication works as expected for each schema
- [ ] Schema isolation is maintained (no data leakage)
- [ ] Performance is acceptable
- [ ] Error handling works correctly

## 🚨 Common Issues and Solutions

### Issue 1: Legacy URLs Not Working

**Problem:** Legacy `/graphql/` endpoint returns 404

**Solution:** Ensure URL configuration includes legacy support:

```python
# urls.py
urlpatterns = [
    # Add this BEFORE the include
    path('graphql/', MultiSchemaGraphQLView.as_view(
        schema_name="default",
        legacy_mode=True
    )),
    
    # Then include multi-schema URLs
    path('graphql/', include('rail_django_graphql.urls')),
]
```

### Issue 2: Schema Not Found

**Problem:** `Schema 'default' not found` error

**Solution:** Ensure schema is registered before URL resolution:

```python
# myapp/apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    
    def ready(self):
        # Register schemas when app is ready
        from .schema_config import register_default_schema
        register_default_schema()
```

### Issue 3: Authentication Issues

**Problem:** Authentication not working after migration

**Solution:** Check authentication settings in schema configuration:

```python
# Verify authentication settings
schema = schema_registry.get_schema("my_schema")
print(f"Auth required: {schema.settings.get('authentication_required')}")

# Update if needed
schema_registry.update_schema("my_schema", {
    "settings": {
        "authentication_required": True,
        "permission_classes": ["django.contrib.auth.permissions.IsAuthenticated"]
    }
})
```

### Issue 4: Performance Degradation

**Problem:** Slower response times after migration

**Solution:** Enable caching and optimize schema configuration:

```python
RAIL_DJANGO_GRAPHQL = {
    'DEFAULT_SCHEMA_SETTINGS': {
        'enable_query_caching': True,
        'cache_timeout': 300,
    },
    'SCHEMA_REGISTRY': {
        'cache_enabled': True,
        'cache_timeout': 3600,
    }
}
```

## 📊 Monitoring Migration

### Health Checks

```python
# Check migration health
from rail_django_graphql.core.registry import schema_registry

def check_migration_health():
    schemas = schema_registry.list_schemas()
    
    print(f"Total schemas: {len(schemas)}")
    print(f"Enabled schemas: {len([s for s in schemas if s.enabled])}")
    
    for schema in schemas:
        print(f"Schema: {schema.name}")
        print(f"  Enabled: {schema.enabled}")
        print(f"  Apps: {schema.apps}")
        print(f"  Auth required: {schema.settings.get('authentication_required')}")
```

### Performance Monitoring

```python
# Add logging to monitor performance
import logging
import time

logger = logging.getLogger(__name__)

class MigrationMonitoringMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/graphql/'):
            start_time = time.time()
            response = self.get_response(request)
            duration = time.time() - start_time
            
            logger.info(f"GraphQL request to {request.path} took {duration:.2f}s")
            return response
        
        return self.get_response(request)
```

## 🎉 Post-Migration Steps

### 1. Clean Up Legacy Configuration

Once migration is complete and stable:

```python
# settings.py - Clean configuration
RAIL_DJANGO_GRAPHQL = {
    'MULTI_SCHEMA_ENABLED': True,
    'AUTO_DISCOVER_SCHEMAS': True,
    
    'DEFAULT_SCHEMA_SETTINGS': {
        'enable_graphiql': True,
        'authentication_required': False,
        'max_query_depth': 10,
    },
    
    # Remove legacy settings
    # 'MUTATION_SETTINGS': {...},  # No longer needed
    # 'TYPE_SETTINGS': {...},      # No longer needed
    # 'SCHEMA_SETTINGS': {...},    # No longer needed
}
```

### 2. Update Documentation

- Update API documentation with new endpoints
- Create schema-specific documentation
- Update client integration guides

### 3. Monitor and Optimize

- Monitor performance metrics
- Optimize schema configurations
- Consider schema consolidation if needed

## 📚 Related Documentation

- [Multi-Schema Setup Guide](../usage/multi-schema-setup.md)
- [Schema Management API](../api/schema-management-api.md)
- [Configuration Guide](../configuration-guide.md)
- [Security Configuration](../setup/security-configuration.md)