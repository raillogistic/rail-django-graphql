# Schema Management API

The Schema Management API provides comprehensive REST endpoints for managing GraphQL schemas, including CRUD operations, health monitoring, and performance metrics.

## 🎯 Overview

The API provides the following capabilities:
- **Schema CRUD Operations**: Create, read, update, and delete schemas
- **Schema Management**: Enable/disable schemas, bulk operations
- **Auto-Discovery**: Trigger and monitor schema discovery
- **Health Monitoring**: Check system health and schema status
- **Performance Metrics**: Detailed performance and usage statistics

## 🔗 Base URL

All API endpoints are available under:
```
/api/schemas/
```

## 🔐 Authentication

API endpoints respect the global authentication settings. Configure authentication in your Django settings:

```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    "API_AUTHENTICATION_REQUIRED": True,  # Require auth for API endpoints
    "API_CORS_ENABLED": True,            # Enable CORS headers
}
```

## 📋 Schema Operations

### List Schemas

**Endpoint:** `GET /api/schemas/`

**Description:** Retrieve a list of all registered schemas with optional filtering.

**Query Parameters:**
- `enabled` (boolean): Filter by enabled status (`true`/`false`)
- `app` (string): Filter by app name
- `format` (string): Response format (`summary`/`detailed`)

**Example Request:**
```bash
GET /api/schemas/?enabled=true&format=detailed
```

**Example Response:**
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "success",
    "data": {
        "schemas": [
            {
                "name": "public_api",
                "description": "Public API for customers",
                "version": "1.0.0",
                "apps": ["customers", "products"],
                "models": ["Customer", "Product"],
                "exclude_models": [],
                "enabled": true,
                "auto_discover": true,
                "settings": {
                    "enable_graphiql": true,
                    "authentication_required": false
                },
                "created_at": "2024-01-15T09:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z"
            }
        ],
        "total_count": 1,
        "enabled_count": 1,
        "disabled_count": 0
    }
}
```

### Create Schema

**Endpoint:** `POST /api/schemas/`

**Description:** Register a new GraphQL schema.

**Request Body:**
```json
{
    "name": "new_api",
    "description": "New API schema",
    "version": "1.0.0",
    "apps": ["myapp"],
    "models": ["MyModel"],
    "exclude_models": [],
    "enabled": true,
    "auto_discover": true,
    "settings": {
        "enable_graphiql": true,
        "authentication_required": false,
        "max_query_depth": 10
    }
}
```

**Example Response:**
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "success",
    "data": {
        "message": "Schema 'new_api' registered successfully",
        "schema": {
            "name": "new_api",
            "description": "New API schema",
            "version": "1.0.0",
            "enabled": true
        }
    }
}
```

### Get Schema Details

**Endpoint:** `GET /api/schemas/{schema_name}/`

**Description:** Retrieve detailed information about a specific schema.

**Example Request:**
```bash
GET /api/schemas/public_api/
```

**Example Response:**
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "success",
    "data": {
        "schema": {
            "name": "public_api",
            "description": "Public API for customers",
            "version": "1.0.0",
            "apps": ["customers", "products"],
            "models": ["Customer", "Product"],
            "exclude_models": [],
            "enabled": true,
            "auto_discover": true,
            "settings": {
                "enable_graphiql": true,
                "authentication_required": false
            },
            "builder": {
                "has_builder": true,
                "builder_type": "AutoSchemaBuilder"
            },
            "created_at": "2024-01-15T09:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }
    }
}
```

### Update Schema

**Endpoint:** `PUT /api/schemas/{schema_name}/`

**Description:** Update an existing schema configuration.

**Request Body:**
```json
{
    "description": "Updated API description",
    "enabled": false,
    "settings": {
        "enable_graphiql": false,
        "authentication_required": true
    }
}
```

**Example Response:**
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "success",
    "data": {
        "message": "Schema 'public_api' updated successfully",
        "schema": {
            "name": "public_api",
            "description": "Updated API description",
            "version": "1.0.0",
            "enabled": false
        }
    }
}
```

### Delete Schema

**Endpoint:** `DELETE /api/schemas/{schema_name}/`

**Description:** Remove a schema registration.

**Example Request:**
```bash
DELETE /api/schemas/old_api/
```

**Example Response:**
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "success",
    "data": {
        "message": "Schema 'old_api' deleted successfully"
    }
}
```

## 🛠️ Schema Management Operations

### Management Actions

**Endpoint:** `POST /api/schemas/manage/`

**Description:** Execute management actions on schemas.

#### Enable Schema

**Request Body:**
```json
{
    "action": "enable",
    "schema_name": "my_schema"
}
```

**Response:**
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "success",
    "data": {
        "message": "Schema 'my_schema' enabled successfully"
    }
}
```

#### Disable Schema

**Request Body:**
```json
{
    "action": "disable",
    "schema_name": "my_schema"
}
```

#### Clear All Schemas

**Request Body:**
```json
{
    "action": "clear_all"
}
```

**Response:**
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "success",
    "data": {
        "message": "All schemas cleared successfully"
    }
}
```

## 🔍 Schema Discovery

### Trigger Auto-Discovery

**Endpoint:** `POST /api/schemas/discover/`

**Description:** Trigger automatic schema discovery from installed Django apps.

**Example Response:**
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "success",
    "data": {
        "discovered_schemas": 3,
        "message": "Schema discovery completed",
        "details": {
            "new_schemas": ["app1_schema", "app2_schema"],
            "updated_schemas": ["existing_schema"],
            "skipped_schemas": []
        }
    }
}
```

### Get Discovery Status

**Endpoint:** `GET /api/schemas/discover/`

**Description:** Get current discovery configuration and status.

**Example Response:**
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "success",
    "data": {
        "discovery_enabled": true,
        "total_schemas": 5,
        "auto_discover_schemas": 3,
        "last_discovery": "2024-01-15T09:00:00Z",
        "discovery_interval": 3600
    }
}
```

## 🏥 Health Monitoring

### Health Check

**Endpoint:** `GET /api/schemas/health/`

**Description:** Get overall system health status.

**Example Response:**
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "success",
    "data": {
        "status": "healthy",
        "total_schemas": 5,
        "enabled_schemas": 4,
        "disabled_schemas": 1,
        "registry_initialized": true,
        "plugin_count": 3,
        "issues": [],
        "timestamp": "2024-01-15T10:30:00Z"
    }
}
```

**Health Status Values:**
- `healthy`: All systems operational
- `warning`: Minor issues detected
- `unhealthy`: Critical issues present

**Common Issues:**
- No enabled schemas found
- Large number of schemas (performance warning)
- Registry initialization failures

## 📊 Performance Metrics

### Get Metrics

**Endpoint:** `GET /api/schemas/metrics/`

**Description:** Retrieve detailed performance and usage metrics.

**Example Response:**
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "success",
    "data": {
        "metrics": {
            "schema_statistics": {
                "total_schemas": 5,
                "enabled_schemas": 4,
                "disabled_schemas": 1,
                "schemas_with_auth": 2,
                "schemas_with_graphiql": 4
            },
            "app_distribution": {
                "customers": 2,
                "products": 3,
                "orders": 1
            },
            "model_statistics": {
                "total_models": 25,
                "average_models_per_schema": 5,
                "most_used_models": ["User", "Product", "Order"]
            },
            "performance_metrics": {
                "average_build_time": 150,
                "cache_hit_rate": 0.85,
                "memory_usage": "45MB"
            },
            "plugin_metrics": {
                "enabled_plugins": 3,
                "plugin_execution_time": 25
            },
            "system_info": {
                "django_version": "4.2.0",
                "graphene_version": "3.4.0",
                "python_version": "3.11.0"
            }
        }
    }
}
```

## 🚨 Error Handling

### Error Response Format

All API endpoints return consistent error responses:

```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "error",
    "data": {
        "message": "Schema 'nonexistent' not found",
        "details": {
            "error_code": "SCHEMA_NOT_FOUND",
            "available_schemas": ["public_api", "admin_api"]
        }
    }
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_JSON` | Request body contains invalid JSON |
| 400 | `VALIDATION_ERROR` | Request data validation failed |
| 401 | `AUTHENTICATION_REQUIRED` | Authentication required but not provided |
| 403 | `PERMISSION_DENIED` | Insufficient permissions |
| 404 | `SCHEMA_NOT_FOUND` | Requested schema does not exist |
| 409 | `SCHEMA_EXISTS` | Schema with same name already exists |
| 500 | `INTERNAL_ERROR` | Internal server error |

### Validation Errors

```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "status": "error",
    "data": {
        "message": "Validation failed",
        "details": {
            "name": ["Schema name is required"],
            "apps": ["At least one app must be specified"],
            "settings.max_query_depth": ["Must be a positive integer"]
        }
    }
}
```

## 🔧 Configuration

### API Settings

Configure the API behavior in your Django settings:

```python
# settings.py
RAIL_DJANGO_GRAPHQL = {
    # API Configuration
    "API_AUTHENTICATION_REQUIRED": True,
    "API_CORS_ENABLED": True,
    "API_RATE_LIMITING": {
        "enabled": True,
        "requests_per_minute": 60
    },
    
    # Response Configuration
    "API_PAGINATION": {
        "enabled": True,
        "page_size": 20,
        "max_page_size": 100
    },
    
    # Caching
    "API_CACHE": {
        "enabled": True,
        "timeout": 300,  # 5 minutes
        "key_prefix": "schema_api"
    }
}
```

### CORS Configuration

```python
# For development
RAIL_DJANGO_GRAPHQL = {
    "API_CORS_ENABLED": True,
    "API_CORS_ORIGINS": ["http://localhost:3000", "http://127.0.0.1:3000"],
    "API_CORS_ALLOW_CREDENTIALS": True
}

# For production
RAIL_DJANGO_GRAPHQL = {
    "API_CORS_ENABLED": True,
    "API_CORS_ORIGINS": ["https://yourdomain.com"],
    "API_CORS_ALLOW_CREDENTIALS": False
}
```

## 🧪 Testing the API

### Using curl

```bash
# List schemas
curl -X GET "http://localhost:8000/api/schemas/" \
     -H "Content-Type: application/json"

# Create schema
curl -X POST "http://localhost:8000/api/schemas/" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "test_api",
       "description": "Test API",
       "apps": ["myapp"],
       "enabled": true
     }'

# Get schema details
curl -X GET "http://localhost:8000/api/schemas/test_api/" \
     -H "Content-Type: application/json"

# Health check
curl -X GET "http://localhost:8000/api/schemas/health/" \
     -H "Content-Type: application/json"
```

### Using Python requests

```python
import requests

base_url = "http://localhost:8000/api/schemas"

# List schemas
response = requests.get(f"{base_url}/")
schemas = response.json()

# Create schema
schema_data = {
    "name": "python_api",
    "description": "API created via Python",
    "apps": ["myapp"],
    "enabled": True,
    "settings": {
        "enable_graphiql": True,
        "authentication_required": False
    }
}
response = requests.post(f"{base_url}/", json=schema_data)

# Get metrics
response = requests.get(f"{base_url}/metrics/")
metrics = response.json()
```

### Using JavaScript/Fetch

```javascript
// List schemas
const response = await fetch('/api/schemas/');
const data = await response.json();

// Create schema
const schemaData = {
    name: 'js_api',
    description: 'API created via JavaScript',
    apps: ['myapp'],
    enabled: true,
    settings: {
        enable_graphiql: true,
        authentication_required: false
    }
};

const createResponse = await fetch('/api/schemas/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(schemaData)
});
```

## 📚 Related Documentation

- [Multi-Schema Registry](../features/multi-schema-registry.md)
- [Multi-Schema Setup Guide](../usage/multi-schema-setup.md)
- [Configuration Guide](../configuration-guide.md)
- [Security Configuration](../setup/security-configuration.md)