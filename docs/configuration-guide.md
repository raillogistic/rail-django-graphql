# Django GraphQL Auto-Generation Configuration Guide

This guide details all available configuration options for Django GraphQL Auto-Generation, with practical examples and best practices.

## Table of Contents

1. [Base Configuration](#base-configuration)
2. [Mutation Settings](#mutation-settings)
3. [Type Settings](#type-settings)
4. [Schema Settings](#schema-settings)
5. [Security Settings](#security-settings)
6. [Performance Settings](#performance-settings)
7. [Feature Flags](#feature-flags)
8. [Runtime Configuration](#runtime-configuration)
9. [Complete Examples](#complete-examples)
10. [Troubleshooting](#troubleshooting)

## Base Configuration

The main configuration is done in your Django project's `settings.py` file:

```python
# settings.py
rail_django_graphql = {
    'MUTATION_SETTINGS': {
        # Mutation configuration
    },
    'TYPE_SETTINGS': {
        # GraphQL type configuration
    },
    'SCHEMA_SETTINGS': {
        # Schema configuration
    },
    'SECURITY_SETTINGS': {
        # Security configuration
    },
    'PERFORMANCE_SETTINGS': {
        # Performance configuration
    }
}
```

## Mutation Settings

### Complete Configuration

```python
rail_django_graphql = {
    'MUTATION_SETTINGS': {
        # Nested relations by model
        'nested_relations_config': {
            'User': True,
            'Order': True,
            'Product': False,
        },

        # Nested fields by model
        'nested_field_config': {
            'User': {
                'profile': True,
                'orders': False,
            },
            'Order': {
                'items': True,
                'customer': True,
            }
        },

        # Mutation type control
        'enable_create_mutations': True,
        'enable_update_mutations': True,
        'enable_delete_mutations': True,

        # Security limits
        'max_nested_depth': 3,
        'batch_size_limit': 100,
    }
}
```

### Detailed Options

| Option                    | Type   | Default | Description                               |
| ------------------------- | ------ | ------- | ----------------------------------------- |
| `nested_relations_config` | `dict` | `{}`    | Enable/disable nested relations by model  |
| `nested_field_config`     | `dict` | `{}`    | Enable/disable specific nested fields     |
| `enable_create_mutations` | `bool` | `True`  | Enable creation mutations                 |
| `enable_update_mutations` | `bool` | `True`  | Enable update mutations                   |
| `enable_delete_mutations` | `bool` | `True`  | Enable deletion mutations                 |
| `max_nested_depth`        | `int`  | `3`     | Maximum depth for nested relations (1-10) |
| `batch_size_limit`        | `int`  | `100`   | Limit for batch operations (1-1000)       |

### Usage Examples

#### Disable Delete Mutations

```python
'MUTATION_SETTINGS': {
    'enable_delete_mutations': False,
}
```

#### Selective Relation Configuration

```python
'MUTATION_SETTINGS': {
    'nested_relations_config': {
        # Models with complex relations
        'User': True,
        'Company': True,

        # Simple models without nested relations
        'Category': False,
        'Tag': False,
    }
}
```

## Type Settings

### Complete Configuration

```python
rail_django_graphql = {
    'TYPE_SETTINGS': {
        # GraphQL features
        'enable_relay_connections': False,
        'enable_filtering': True,
        'enable_ordering': True,
        'enable_pagination': True,

        # Pagination settings
        'default_page_size': 20,
        'max_page_size': 100,
    }
}
```

### Detailed Options

| Option                     | Type   | Default | Description                             |
| -------------------------- | ------ | ------- | --------------------------------------- |
| `enable_relay_connections` | `bool` | `False` | Enable Relay connections for pagination |
| `enable_filtering`         | `bool` | `True`  | Enable query filtering                  |
| `enable_ordering`          | `bool` | `True`  | Enable result ordering                  |
| `enable_pagination`        | `bool` | `True`  | Enable pagination                       |
| `default_page_size`        | `int`  | `20`    | Default page size (1-1000)              |
| `max_page_size`            | `int`  | `100`   | Maximum page size (1-10000)             |

### Usage Examples

#### Configuration for Public API

```python
'TYPE_SETTINGS': {
    'enable_filtering': True,
    'enable_ordering': True,
    'enable_pagination': True,
    'default_page_size': 10,
    'max_page_size': 50,  # Limit to avoid overload
}
```

#### Configuration for Internal API

```python
'TYPE_SETTINGS': {
    'enable_relay_connections': True,
    'default_page_size': 50,
    'max_page_size': 500,  # More permissive for internal tools
}
```

## Schema Settings

### Complete Configuration

```python
rail_django_graphql = {
    'SCHEMA_SETTINGS': {
        'enable_introspection': True,
        'enable_playground': True,
        'schema_name': 'My GraphQL API',
        'schema_description': 'Automatically generated GraphQL API for my application',
    }
}
```

### Detailed Options

| Option                 | Type   | Default                                    | Description                 |
| ---------------------- | ------ | ------------------------------------------ | --------------------------- |
| `enable_introspection` | `bool` | `True`                                     | Enable schema introspection |
| `enable_playground`    | `bool` | `True`                                     | Enable GraphQL Playground   |
| `schema_name`          | `str`  | `'Auto Generated Schema'`                  | GraphQL schema name         |
| `schema_description`   | `str`  | `'Automatically generated GraphQL schema'` | Schema description          |

### Environment-based Configuration

```python
# settings/development.py
rail_django_graphql = {
    'SCHEMA_SETTINGS': {
        'enable_introspection': True,
        'enable_playground': True,
    }
}

# settings/production.py
rail_django_graphql = {
    'SCHEMA_SETTINGS': {
        'enable_introspection': False,  # Security in production
        'enable_playground': False,     # No public interface
    }
}
```

## Security Settings

### Complete Configuration

```python
rail_django_graphql = {
    'SECURITY_SETTINGS': {
        # Depth analysis
        'enable_query_depth_analysis': True,
        'max_query_depth': 10,

        # Complexity analysis
        'enable_query_complexity_analysis': True,
        'max_query_complexity': 1000,

        # Rate limiting
        'enable_rate_limiting': True,
        'rate_limit_per_minute': 60,
    }
}
```

### Detailed Options

| Option                             | Type   | Default | Description                        |
| ---------------------------------- | ------ | ------- | ---------------------------------- |
| `enable_query_depth_analysis`      | `bool` | `True`  | Enable query depth analysis        |
| `max_query_depth`                  | `int`  | `10`    | Maximum query depth (1-50)         |
| `enable_query_complexity_analysis` | `bool` | `True`  | Enable complexity analysis         |
| `max_query_complexity`             | `int`  | `1000`  | Maximum query complexity (1-10000) |
| `enable_rate_limiting`             | `bool` | `False` | Enable rate limiting               |
| `rate_limit_per_minute`            | `int`  | `60`    | Request limit per minute (1-10000) |

### Security Configuration Examples

#### Strict Configuration (Production)

```python
'SECURITY_SETTINGS': {
    'enable_query_depth_analysis': True,
    'max_query_depth': 5,  # Very restrictive
    'enable_query_complexity_analysis': True,
    'max_query_complexity': 500,  # Low limit
    'enable_rate_limiting': True,
    'rate_limit_per_minute': 30,  # Strict limit
}
```

#### Permissive Configuration (Development)

```python
'SECURITY_SETTINGS': {
    'enable_query_depth_analysis': False,
    'enable_query_complexity_analysis': False,
    'enable_rate_limiting': False,
}
```

## Performance Settings

### Complete Configuration

```python
rail_django_graphql = {
    'PERFORMANCE_SETTINGS': {
        # Query caching
        'enable_query_caching': True,
        'cache_timeout': 300,  # 5 minutes

        # Optimizations
        'enable_dataloader': True,
        'enable_query_optimization': True,
    }
}
```

### Detailed Options

| Option                      | Type   | Default | Description                              |
| --------------------------- | ------ | ------- | ---------------------------------------- |
| `enable_query_caching`      | `bool` | `False` | Enable query caching                     |
| `cache_timeout`             | `int`  | `300`   | Cache timeout in seconds (1-86400)       |
| `enable_dataloader`         | `bool` | `True`  | Enable DataLoader for query optimization |
| `enable_query_optimization` | `bool` | `True`  | Enable automatic query optimization      |

### Load-based Configuration

#### High Performance Configuration

```python
'PERFORMANCE_SETTINGS': {
    'enable_query_caching': True,
    'cache_timeout': 600,  # 10 minutes
    'enable_dataloader': True,
    'enable_query_optimization': True,
}
```

#### Development Configuration

```python
'PERFORMANCE_SETTINGS': {
    'enable_query_caching': False,  # No cache in dev
    'enable_dataloader': True,
    'enable_query_optimization': False,  # Easier debugging
}
```

## Feature Flags

### Feature Flags Configuration

```python
# settings.py
FEATURE_FLAGS = {
    # Simple configuration (boolean)
    'enable_advanced_filtering': True,
    'enable_bulk_operations': False,

    # Advanced configuration
    'new_mutation_system': {
        'description': 'New mutation system with advanced validation',
        'type': 'boolean',
        'default_value': False,
        'enabled': True,
        'environments': ['development', 'staging'],
        'percentage_rollout': 50,  # Progressive rollout
        'dependencies': ['enable_advanced_filtering'],
        'metadata': {
            'version': '2.0',
            'team': 'backend'
        }
    }
}
```

### Using Feature Flags

```python
from rail_django_graphql.core.feature_flags import is_feature_enabled, get_feature_value

# In your views or resolvers
def my_resolver(self, info):
    if is_feature_enabled('enable_advanced_filtering', info.context.user):
        # Logic with advanced filtering
        return advanced_filter_logic()
    else:
        # Standard logic
        return standard_logic()

# Decorator for views
from rail_django_graphql.core.feature_flags import feature_flag_required

@feature_flag_required('enable_bulk_operations')
def bulk_update_view(request):
    # This view is only accessible if the feature flag is enabled
    pass
```

## Runtime Configuration

### Configuration Updates Without Restart

```python
from rail_django_graphql.core.runtime_config import set_runtime_config, get_runtime_config

# Update a configuration
set_runtime_config(
    'SECURITY_SETTINGS.max_query_depth',
    15,
    user='admin',
    reason='Temporary increase for testing'
)

# Get a configuration
max_depth = get_runtime_config('SECURITY_SETTINGS.max_query_depth', default=10)
```

### Change Callbacks

```python
from rail_django_graphql.core.runtime_config import runtime_config

def on_security_change(key, old_value, new_value):
    print(f"Security setting changed: {key} = {new_value}")
    # Notification or logging logic

# Register the callback
runtime_config.register_change_callback('SECURITY_SETTINGS.max_query_depth', on_security_change)
```

## Complete Examples

### E-commerce Configuration

```python
rail_django_graphql = {
    'MUTATION_SETTINGS': {
        'nested_relations_config': {
            'User': True,
            'Order': True,
            'Product': True,
            'Category': False,
        },
        'enable_delete_mutations': False,  # Soft delete only
        'max_nested_depth': 2,
        'batch_size_limit': 50,
    },
    'TYPE_SETTINGS': {
        'enable_filtering': True,
        'enable_ordering': True,
        'enable_pagination': True,
        'default_page_size': 12,  # Product grid
        'max_page_size': 100,
    },
    'SECURITY_SETTINGS': {
        'enable_query_depth_analysis': True,
        'max_query_depth': 8,
        'enable_rate_limiting': True,
        'rate_limit_per_minute': 120,
    },
    'PERFORMANCE_SETTINGS': {
        'enable_query_caching': True,
        'cache_timeout': 600,
        'enable_dataloader': True,
    }
}
```

### Internal API Configuration

```python
rail_django_graphql = {
    'MUTATION_SETTINGS': {
        'nested_relations_config': {
            # All relations enabled for flexibility
            'User': True,
            'Department': True,
            'Project': True,
        },
        'max_nested_depth': 5,
        'batch_size_limit': 500,
    },
    'TYPE_SETTINGS': {
        'enable_relay_connections': True,
        'default_page_size': 50,
        'max_page_size': 1000,
    },
    'SECURITY_SETTINGS': {
        'enable_query_depth_analysis': False,  # Internal trust
        'enable_rate_limiting': False,
    },
    'PERFORMANCE_SETTINGS': {
        'enable_query_caching': True,
        'cache_timeout': 1800,  # 30 minutes
    }
}
```

### Microservice Configuration

```python
rail_django_graphql = {
    'MUTATION_SETTINGS': {
        'enable_create_mutations': True,
        'enable_update_mutations': True,
        'enable_delete_mutations': False,  # Handled by another service
        'max_nested_depth': 1,  # Simple relations
    },
    'TYPE_SETTINGS': {
        'enable_pagination': True,
        'default_page_size': 25,
        'max_page_size': 200,
    },
    'SECURITY_SETTINGS': {
        'enable_query_depth_analysis': True,
        'max_query_depth': 3,
        'max_query_complexity': 200,
    }
}
```

## Troubleshooting

### Common Issues

#### 1. Configuration Validation Error

```
ImproperlyConfigured: MUTATION_SETTINGS.max_nested_depth must be >= 1
```

**Solution:** Check that numeric values respect the defined limits.

#### 2. Performance Degradation

**Symptoms:** Slow queries, timeouts

**Solutions:**

- Enable `enable_query_caching`
- Reduce `max_page_size`
- Enable `enable_dataloader`
- Limit `max_nested_depth`

#### 3. Security Errors

```
Query depth limit exceeded: 15 > 10
```

**Solutions:**

- Increase `max_query_depth` if legitimate
- Optimize query structure
- Use pagination

### Configuration Validation

```python
from rail_django_graphql.core.config_loader import validate_configuration

# Validate current configuration
try:
    config = validate_configuration(settings.rail_django_graphql)
    print("Configuration is valid")
except ImproperlyConfigured as e:
    print(f"Configuration errors: {e}")
```

### Configuration Debugging

```python
from rail_django_graphql.core.config_loader import debug_configuration

# Display current configuration
debug_configuration()
```

### Feature Flags Monitoring

```python
from rail_django_graphql.core.feature_flags import feature_flags

# Get all flags
all_flags = feature_flags.get_all_flags()
for name, flag in all_flags.items():
    print(f"{name}: {'✓' if flag.enabled else '✗'}")

# Change history
from rail_django_graphql.core.runtime_config import runtime_config
history = runtime_config.get_change_history(limit=10)
for change in history:
    print(f"{change.timestamp}: {change.key} = {change.new_value}")
```

## Best Practices

### 1. Environment-based Configuration

Use separate settings files:

```python
# settings/base.py
rail_django_graphql = {
    'MUTATION_SETTINGS': {
        'max_nested_depth': 3,
    }
}

# settings/production.py
from .base import *

rail_django_graphql.update({
    'SECURITY_SETTINGS': {
        'enable_rate_limiting': True,
        'rate_limit_per_minute': 30,
    }
})
```

### 2. Monitoring and Alerts

```python
# Callback for monitoring
def monitor_config_changes(key, old_value, new_value):
    if 'SECURITY_SETTINGS' in key:
        # Alert for security changes
        send_security_alert(key, old_value, new_value)

runtime_config.register_change_callback('SECURITY_SETTINGS.*', monitor_config_changes)
```

### 3. Configuration Testing

```python
# tests/test_config.py
from django.test import TestCase
from rail_django_graphql.core.config_loader import validate_configuration

class ConfigurationTest(TestCase):
    def test_valid_configuration(self):
        config = {
            'MUTATION_SETTINGS': {
                'max_nested_depth': 5,
            }
        }
        validated = validate_configuration(config)
        self.assertEqual(validated['MUTATION_SETTINGS']['max_nested_depth'], 5)

    def test_invalid_configuration(self):
        config = {
            'MUTATION_SETTINGS': {
                'max_nested_depth': 0,  # Invalid
            }
        }
        with self.assertRaises(ImproperlyConfigured):
            validate_configuration(config)
```

This documentation covers all aspects of Django GraphQL Auto-Generation system configuration. Refer to the relevant sections according to your specific needs.
