# API Reference

This document provides detailed API reference for the Django GraphQL Multi-Schema System.

## Table of Contents

- [Schema Registry](#schema-registry)
- [Schema Info](#schema-info)
- [Decorators](#decorators)
- [Plugin System](#plugin-system)
- [Hook Registry](#hook-registry)
- [REST API Endpoints](#rest-api-endpoints)
- [Views](#views)
- [Serializers](#serializers)
- [Exceptions](#exceptions)

## Schema Registry

The `SchemaRegistry` class is the central component for managing GraphQL schemas.

### Class: `SchemaRegistry`

Located in: `rail_django_graphql.core.registry`

#### Methods

##### `register_schema(name: str, **kwargs) -> SchemaInfo`

Register a new GraphQL schema.

**Parameters:**
- `name` (str): Unique name for the schema
- `description` (str, optional): Schema description
- `version` (str, optional): Schema version
- `apps` (List[str], optional): Associated Django apps
- `models` (List[str], optional): Included models
- `exclude_models` (List[str], optional): Excluded models
- `settings` (Dict, optional): Custom settings
- `auto_discover` (bool, optional): Enable auto-discovery (default: True)
- `enabled` (bool, optional): Enable schema (default: True)
- `schema` (graphene.Schema, optional): GraphQL schema instance
- `builder` (Callable, optional): Schema builder function

**Returns:**
- `SchemaInfo`: Registered schema information

**Raises:**
- `ValueError`: If schema name already exists or invalid parameters
- `TypeError`: If schema or builder is invalid

**Example:**
```python
from rail_django_graphql.core.registry import schema_registry

schema_info = schema_registry.register_schema(
    name='my_schema',
    description='My GraphQL schema',
    version='1.0.0',
    apps=['myapp'],
    schema=my_graphene_schema
)
```

##### `unregister_schema(name: str) -> bool`

Remove a schema from the registry.

**Parameters:**
- `name` (str): Schema name to remove

**Returns:**
- `bool`: True if schema was removed, False if not found

**Example:**
```python
success = schema_registry.unregister_schema('my_schema')
```

##### `get_schema(name: str) -> Optional[SchemaInfo]`

Retrieve schema information by name.

**Parameters:**
- `name` (str): Schema name

**Returns:**
- `SchemaInfo` or `None`: Schema information if found

**Example:**
```python
schema_info = schema_registry.get_schema('my_schema')
if schema_info:
    print(f"Schema version: {schema_info.version}")
```

##### `list_schemas() -> List[SchemaInfo]`

Get all registered schemas.

**Returns:**
- `List[SchemaInfo]`: List of all schema information objects

**Example:**
```python
all_schemas = schema_registry.list_schemas()
for schema in all_schemas:
    print(f"{schema.name}: {schema.description}")
```

##### `schema_exists(name: str) -> bool`

Check if a schema exists in the registry.

**Parameters:**
- `name` (str): Schema name to check

**Returns:**
- `bool`: True if schema exists

**Example:**
```python
if schema_registry.schema_exists('my_schema'):
    print("Schema exists")
```

##### `enable_schema(name: str) -> bool`

Enable a schema.

**Parameters:**
- `name` (str): Schema name to enable

**Returns:**
- `bool`: True if schema was enabled

**Example:**
```python
schema_registry.enable_schema('my_schema')
```

##### `disable_schema(name: str) -> bool`

Disable a schema.

**Parameters:**
- `name` (str): Schema name to disable

**Returns:**
- `bool`: True if schema was disabled

**Example:**
```python
schema_registry.disable_schema('my_schema')
```

##### `clear() -> None`

Remove all schemas from the registry.

**Example:**
```python
schema_registry.clear()
```

##### `auto_discover_schemas() -> int`

Automatically discover and register schemas from Django apps.

**Returns:**
- `int`: Number of newly discovered schemas

**Example:**
```python
count = schema_registry.auto_discover_schemas()
print(f"Discovered {count} new schemas")
```

##### `get_schema_builder(name: str) -> Optional[Callable]`

Get the schema builder function for a schema.

**Parameters:**
- `name` (str): Schema name

**Returns:**
- `Callable` or `None`: Schema builder function if available

##### `discover_schemas() -> List[str]`

Discover available schemas without registering them.

**Returns:**
- `List[str]`: List of discovered schema names

##### Hook Management Methods

##### `add_discovery_hook(hook: Callable) -> None`

Add a discovery hook function.

**Parameters:**
- `hook` (Callable): Hook function to add

##### `add_pre_registration_hook(hook: Callable) -> None`

Add a pre-registration hook function.

**Parameters:**
- `hook` (Callable): Hook function that modifies registration arguments

##### `add_post_registration_hook(hook: Callable) -> None`

Add a post-registration hook function.

**Parameters:**
- `hook` (Callable): Hook function called after registration

##### `remove_discovery_hook(hook: Callable) -> bool`

Remove a discovery hook function.

**Parameters:**
- `hook` (Callable): Hook function to remove

**Returns:**
- `bool`: True if hook was removed

##### `clear_discovery_hooks() -> None`

Remove all discovery hooks.

##### `get_discovery_hooks() -> List[Callable]`

Get all registered discovery hooks.

**Returns:**
- `List[Callable]`: List of discovery hook functions

## Schema Info

The `SchemaInfo` class contains metadata about a registered schema.

### Class: `SchemaInfo`

Located in: `rail_django_graphql.core.registry`

#### Properties

- `name` (str): Schema name
- `description` (str): Schema description
- `version` (str): Schema version
- `apps` (List[str]): Associated Django apps
- `models` (List[str]): Included models
- `exclude_models` (List[str]): Excluded models
- `enabled` (bool): Whether schema is enabled
- `auto_discover` (bool): Whether schema supports auto-discovery
- `settings` (Dict): Custom settings dictionary
- `schema` (graphene.Schema): GraphQL schema instance
- `builder` (Callable): Schema builder function
- `registered_at` (datetime): Registration timestamp

#### Methods

##### `get_graphql_schema() -> graphene.Schema`

Get the GraphQL schema instance, building it if necessary.

**Returns:**
- `graphene.Schema`: The GraphQL schema

**Raises:**
- `ValueError`: If neither schema nor builder is available

**Example:**
```python
schema_info = schema_registry.get_schema('my_schema')
graphql_schema = schema_info.get_graphql_schema()
```

##### `to_dict() -> Dict`

Convert schema info to dictionary representation.

**Returns:**
- `Dict`: Dictionary representation of schema info

**Example:**
```python
schema_dict = schema_info.to_dict()
print(json.dumps(schema_dict, indent=2))
```

## Decorators

### `@register_schema(**kwargs)`

Decorator for registering classes or functions as schema providers.

Located in: `rail_django_graphql.decorators`

**Parameters:**
- Same as `SchemaRegistry.register_schema()` except `name` is required

**Usage with Classes:**
```python
from rail_django_graphql.decorators import register_schema

@register_schema(
    name='user_schema',
    description='User management schema',
    version='1.0.0'
)
class UserSchema:
    def get_schema(self):
        return graphene.Schema(query=UserQuery)
```

**Usage with Functions:**
```python
@register_schema(
    name='product_schema',
    description='Product schema'
)
def create_product_schema():
    return graphene.Schema(query=ProductQuery)
```

## Plugin System

### Class: `BasePlugin`

Located in: `rail_django_graphql.plugins.base`

Base class for creating plugins.

#### Properties

- `name` (str): Plugin name
- `version` (str): Plugin version
- `enabled` (bool): Whether plugin is enabled

#### Methods

##### `on_pre_registration(schema_name: str, **kwargs) -> Dict`

Called before schema registration.

**Parameters:**
- `schema_name` (str): Name of schema being registered
- `**kwargs`: Registration arguments

**Returns:**
- `Dict`: Modified registration arguments

##### `on_post_registration(schema_name: str, schema_info: SchemaInfo) -> None`

Called after schema registration.

**Parameters:**
- `schema_name` (str): Name of registered schema
- `schema_info` (SchemaInfo): Registered schema information

##### `on_schema_discovery(discovered_schemas: List[str]) -> None`

Called after schema discovery.

**Parameters:**
- `discovered_schemas` (List[str]): List of discovered schema names

##### `validate_schema(schema_info: SchemaInfo) -> bool`

Validate schema configuration.

**Parameters:**
- `schema_info` (SchemaInfo): Schema to validate

**Returns:**
- `bool`: True if schema is valid

**Raises:**
- `ValueError`: If schema is invalid

### Class: `PluginManager`

Located in: `rail_django_graphql.plugins.base`

Manages plugin loading and execution.

#### Methods

##### `load_plugins() -> None`

Load plugins from Django settings.

##### `get_plugins() -> List[BasePlugin]`

Get all loaded plugins.

**Returns:**
- `List[BasePlugin]`: List of plugin instances

##### `get_enabled_plugins() -> List[BasePlugin]`

Get enabled plugins only.

**Returns:**
- `List[BasePlugin]`: List of enabled plugin instances

##### `run_pre_registration_hooks(schema_name: str, **kwargs) -> Dict`

Run pre-registration hooks from all enabled plugins.

**Parameters:**
- `schema_name` (str): Schema name
- `**kwargs`: Registration arguments

**Returns:**
- `Dict`: Modified registration arguments

##### `run_post_registration_hooks(schema_name: str, schema_info: SchemaInfo) -> None`

Run post-registration hooks from all enabled plugins.

**Parameters:**
- `schema_name` (str): Schema name
- `schema_info` (SchemaInfo): Schema information

## Hook Registry

### Class: `HookRegistry`

Located in: `rail_django_graphql.plugins.hooks`

Independent hook management system.

#### Methods

##### `register_hook(hook_type: str, hook_func: Callable, name: str = None) -> None`

Register a hook function.

**Parameters:**
- `hook_type` (str): Type of hook ('pre_registration', 'post_registration', etc.)
- `hook_func` (Callable): Hook function
- `name` (str, optional): Hook name for identification

##### `unregister_hook(hook_type: str, hook_func: Callable = None, name: str = None) -> bool`

Unregister a hook function.

**Parameters:**
- `hook_type` (str): Type of hook
- `hook_func` (Callable, optional): Hook function to remove
- `name` (str, optional): Hook name to remove

**Returns:**
- `bool`: True if hook was removed

##### `get_hooks(hook_type: str) -> List[Callable]`

Get all hooks of a specific type.

**Parameters:**
- `hook_type` (str): Type of hook

**Returns:**
- `List[Callable]`: List of hook functions

##### `execute_hooks(hook_type: str, *args, **kwargs) -> None`

Execute all hooks of a specific type.

**Parameters:**
- `hook_type` (str): Type of hook
- `*args`: Arguments to pass to hooks
- `**kwargs`: Keyword arguments to pass to hooks

##### `execute_hooks_with_data(hook_type: str, data: Dict, *args, **kwargs) -> Dict`

Execute hooks that can modify data.

**Parameters:**
- `hook_type` (str): Type of hook
- `data` (Dict): Data to be modified by hooks
- `*args`: Additional arguments
- `**kwargs`: Additional keyword arguments

**Returns:**
- `Dict`: Modified data

##### `clear_hooks(hook_type: str = None) -> None`

Clear hooks.

**Parameters:**
- `hook_type` (str, optional): Specific hook type to clear, or None for all

##### `list_hooks() -> Dict[str, List[str]]`

List all registered hooks.

**Returns:**
- `Dict[str, List[str]]`: Dictionary mapping hook types to hook names

## REST API Endpoints

### Schema Management

#### `GET /api/v1/schemas/`

List all registered schemas.

**Response:**
```json
{
    "status": "success",
    "data": {
        "schemas": [
            {
                "name": "my_schema",
                "description": "My schema",
                "version": "1.0.0",
                "enabled": true,
                "apps": ["myapp"],
                "models": ["MyModel"]
            }
        ],
        "count": 1
    }
}
```

#### `GET /api/v1/schemas/{schema_name}/`

Get specific schema details.

**Response:**
```json
{
    "status": "success",
    "data": {
        "name": "my_schema",
        "description": "My schema",
        "version": "1.0.0",
        "enabled": true,
        "apps": ["myapp"],
        "models": ["MyModel"],
        "settings": {},
        "registered_at": "2024-01-01T00:00:00Z"
    }
}
```

#### `POST /api/v1/schemas/`

Create a new schema.

**Request Body:**
```json
{
    "name": "new_schema",
    "description": "New schema",
    "version": "1.0.0",
    "apps": ["myapp"],
    "enabled": true
}
```

**Response:**
```json
{
    "status": "success",
    "data": {
        "name": "new_schema",
        "description": "New schema",
        "version": "1.0.0",
        "enabled": true
    },
    "message": "Schema created successfully"
}
```

#### `PUT /api/v1/schemas/{schema_name}/`

Update an existing schema.

**Request Body:**
```json
{
    "description": "Updated description",
    "enabled": false
}
```

#### `DELETE /api/v1/schemas/{schema_name}/`

Delete a schema.

**Response:**
```json
{
    "status": "success",
    "message": "Schema deleted successfully"
}
```

### Management Operations

#### `POST /api/v1/management/`

Perform management operations.

**Enable Schema:**
```json
{
    "action": "enable",
    "schema_name": "my_schema"
}
```

**Disable Schema:**
```json
{
    "action": "disable",
    "schema_name": "my_schema"
}
```

**Clear All Schemas:**
```json
{
    "action": "clear_all"
}
```

### Discovery

#### `GET /api/v1/discovery/`

Get discovery status.

**Response:**
```json
{
    "status": "success",
    "data": {
        "auto_discovery_enabled": true,
        "last_discovery": "2024-01-01T00:00:00Z",
        "discovered_schemas": ["schema1", "schema2"]
    }
}
```

#### `POST /api/v1/discovery/`

Trigger schema discovery.

**Response:**
```json
{
    "status": "success",
    "data": {
        "discovered_count": 2,
        "new_schemas": ["new_schema1", "new_schema2"]
    },
    "message": "Discovery completed successfully"
}
```

### Health Check

#### `GET /api/v1/health/`

Get system health status.

**Response:**
```json
{
    "status": "success",
    "data": {
        "status": "healthy",
        "registry_status": "operational",
        "schema_count": 5,
        "enabled_schemas": 4,
        "plugin_count": 2,
        "last_check": "2024-01-01T00:00:00Z"
    }
}
```

### Metrics

#### `GET /api/v1/metrics/`

Get system metrics.

**Response:**
```json
{
    "status": "success",
    "data": {
        "schema_metrics": {
            "total_schemas": 5,
            "enabled_schemas": 4,
            "disabled_schemas": 1
        },
        "model_metrics": {
            "total_models": 20,
            "models_per_app": {
                "app1": 10,
                "app2": 10
            }
        },
        "app_metrics": {
            "total_apps": 2,
            "apps_with_schemas": ["app1", "app2"]
        },
        "plugin_metrics": {
            "total_plugins": 2,
            "enabled_plugins": 2
        }
    }
}
```

## Views

### Class: `MultiSchemaGraphQLView`

Located in: `rail_django_graphql.views`

GraphQL view that supports multiple schemas.

#### Methods

##### `get_schema(schema_name: str) -> graphene.Schema`

Get GraphQL schema by name.

##### `dispatch(request, *args, **kwargs)`

Handle HTTP requests and route to appropriate schema.

### Class: `SchemaListView`

Located in: `rail_django_graphql.views`

View for listing available schemas.

### Class: `GraphQLPlaygroundView`

Located in: `rail_django_graphql.views`

GraphiQL playground view with schema selection.

## Serializers

### Class: `SchemaSerializer`

Located in: `rail_django_graphql.api.serializers`

Serializer for schema data validation and serialization.

#### Fields

- `name` (CharField): Schema name
- `description` (CharField): Schema description
- `version` (CharField): Schema version
- `apps` (ListField): Associated apps
- `models` (ListField): Included models
- `exclude_models` (ListField): Excluded models
- `enabled` (BooleanField): Whether schema is enabled
- `settings` (JSONField): Custom settings

### Class: `ManagementActionSerializer`

Located in: `rail_django_graphql.api.serializers`

Serializer for management actions.

#### Fields

- `action` (ChoiceField): Action type ('enable', 'disable', 'clear_all')
- `schema_name` (CharField): Target schema name (optional)

### Class: `HealthSerializer`

Located in: `rail_django_graphql.api.serializers`

Serializer for health status data.

### Class: `MetricsSerializer`

Located in: `rail_django_graphql.api.serializers`

Serializer for metrics data.

### Class: `DiscoverySerializer`

Located in: `rail_django_graphql.api.serializers`

Serializer for discovery status and results.

## Exceptions

### Class: `SchemaRegistryError`

Located in: `rail_django_graphql.exceptions`

Base exception for schema registry errors.

### Class: `SchemaNotFoundError`

Located in: `rail_django_graphql.exceptions`

Raised when a requested schema is not found.

### Class: `SchemaAlreadyExistsError`

Located in: `rail_django_graphql.exceptions`

Raised when attempting to register a schema that already exists.

### Class: `InvalidSchemaError`

Located in: `rail_django_graphql.exceptions`

Raised when a schema is invalid or malformed.

### Class: `PluginError`

Located in: `rail_django_graphql.exceptions`

Base exception for plugin-related errors.

### Class: `HookExecutionError`

Located in: `rail_django_graphql.exceptions`

Raised when a hook execution fails.

## Global Registry Instance

A global registry instance is available for convenience:

```python
from rail_django_graphql.core.registry import schema_registry

# Use the global instance
schema_registry.register_schema(name='my_schema', ...)
```

## Global Hook Registry Instance

A global hook registry instance is available:

```python
from rail_django_graphql.plugins.hooks import hook_registry

# Use the global instance
hook_registry.register_hook('pre_registration', my_hook)
```

## Type Hints

The library provides comprehensive type hints for better IDE support:

```python
from typing import Optional, List, Dict, Callable
from rail_django_graphql.core.registry import SchemaInfo, SchemaRegistry

def my_function(registry: SchemaRegistry) -> Optional[SchemaInfo]:
    return registry.get_schema('my_schema')
```