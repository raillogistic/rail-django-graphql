# Settings Propagation Analysis

## Overview
This document analyzes how settings are propagated from `schema_registry.register_schema` to all generators and the schema builder in the Rail Django GraphQL library.

## Settings Flow Architecture

### 1. Schema Registration (`registry.py`)
```python
def register_schema(self, schema_name: str, **settings):
    # Settings are stored in Django settings under RAIL_DJANGO_GRAPHQL_SCHEMAS
    configure_schema_settings(schema_name, **settings)
```

### 2. Schema Builder Initialization (`schema.py`)
```python
def get_schema_builder(schema_name: str = "default") -> SchemaBuilder:
    # Gets settings from hierarchical system
    settings = get_schema_settings(schema_name)
    raw_settings = get_merged_settings(schema_name)
    
    return SchemaBuilder(
        settings=settings,
        schema_name=schema_name,
        raw_settings=raw_settings
    )
```

### 3. Generator Initialization
All generators use the hierarchical settings system through `conf.py`:

#### TypeGenerator (`generators/types.py`)
```python
def __init__(self, schema_name: str = "default"):
    self.schema_name = schema_name
    # Uses hierarchical settings
    self.settings = get_type_generator_settings(schema_name)
    self.mutation_settings = get_mutation_generator_settings(schema_name)
```

#### QueryGenerator (`generators/queries.py`)
```python
def __init__(self, type_generator: TypeGenerator, schema_name: str = "default"):
    self.schema_name = schema_name
    # Uses hierarchical settings
    self.settings = get_query_generator_settings(schema_name)
```

#### MutationGenerator (`generators/mutations.py`)
```python
def __init__(self, type_generator: TypeGenerator, schema_name: str = "default"):
    self.schema_name = schema_name
    # Uses hierarchical settings
    self.settings = get_mutation_generator_settings(schema_name)
```

## Hierarchical Settings System (`conf.py`)

### Settings Resolution Order
1. **Schema-specific settings** (highest priority)
   - Stored in `settings.RAIL_DJANGO_GRAPHQL_SCHEMAS[schema_name]`
   - Set via `schema_registry.register_schema()`

2. **Global Django settings**
   - Stored in `settings.RAIL_DJANGO_GRAPHQL`
   - Set in Django settings.py

3. **Library defaults** (lowest priority)
   - Defined in `defaults.py` as `LIBRARY_DEFAULTS`

### Settings Proxy Implementation
```python
class SettingsProxy:
    def get(self, key: str, default: Any = None) -> Any:
        # 1. Check schema-specific settings
        if self.schema_name:
            schema_value = self._get_schema_setting(key)
            if schema_value is not None:
                return schema_value
        
        # 2. Check global Django settings
        django_value = self._get_django_setting(key)
        if django_value is not None:
            return django_value
        
        # 3. Check library defaults
        library_value = self._get_library_default(key)
        if library_value is not None:
            return library_value
        
        return default
```

### Generator Settings Functions
```python
def get_type_generator_settings(schema_name: Optional[str] = None) -> TypeGeneratorSettings:
    settings_dict = get_setting("TYPE_GENERATION_SETTINGS", {}, schema_name)
    # Filters and creates dataclass instance
    return TypeGeneratorSettings(**filtered_settings)

def get_query_generator_settings(schema_name: Optional[str] = None) -> QueryGeneratorSettings:
    settings_dict = get_setting("QUERY_SETTINGS", {}, schema_name)
    # Filters and creates dataclass instance
    return QueryGeneratorSettings(**filtered_settings)

def get_mutation_generator_settings(schema_name: Optional[str] = None) -> MutationGeneratorSettings:
    settings_dict = get_setting("MUTATION_SETTINGS", {}, schema_name)
    # Filters and creates dataclass instance
    return MutationGeneratorSettings(**filtered_settings)
```

## Verification of Settings Propagation

### ✅ Confirmed Working Components

1. **Registry to Django Settings**
   - `schema_registry.register_schema()` correctly stores settings in `RAIL_DJANGO_GRAPHQL_SCHEMAS`
   - Settings are properly normalized and stored

2. **Hierarchical Resolution**
   - `SettingsProxy` correctly implements 3-tier hierarchy
   - Schema-specific settings override global and default settings
   - Proper fallback mechanism in place

3. **Generator Access**
   - All generators use `get_*_generator_settings(schema_name)` functions
   - Functions properly retrieve settings using hierarchical system
   - Settings are converted to appropriate dataclass instances

4. **Schema Builder Integration**
   - `SchemaBuilder` receives settings from registry
   - Generators are initialized with correct `schema_name`
   - Each generator independently accesses hierarchical settings

### Settings Propagation Flow

```
schema_registry.register_schema(schema_name, **settings)
    ↓
Django settings.RAIL_DJANGO_GRAPHQL_SCHEMAS[schema_name] = settings
    ↓
get_schema_builder(schema_name)
    ↓
SchemaBuilder(schema_name=schema_name)
    ↓
Generators initialized with schema_name:
    - TypeGenerator(schema_name=schema_name)
    - QueryGenerator(schema_name=schema_name)  
    - MutationGenerator(schema_name=schema_name)
    ↓
Each generator calls get_*_generator_settings(schema_name)
    ↓
Hierarchical settings resolution:
    1. RAIL_DJANGO_GRAPHQL_SCHEMAS[schema_name]
    2. RAIL_DJANGO_GRAPHQL (global)
    3. LIBRARY_DEFAULTS
```

## Conclusion

**✅ SETTINGS PROPAGATION IS WORKING CORRECTLY**

The analysis confirms that:

1. Settings passed to `schema_registry.register_schema()` are properly stored in Django settings
2. The hierarchical settings system correctly resolves schema-specific settings
3. All generators access settings through the hierarchical system using their `schema_name`
4. Settings are properly converted to dataclass instances with validation
5. The complete chain from registry → Django settings → hierarchical resolution → generators is functioning as designed

The architecture ensures that schema-specific settings registered via `schema_registry.register_schema()` are correctly propagated to all generators and components throughout the system.