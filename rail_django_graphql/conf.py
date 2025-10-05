"""Configuration management for Rail Django GraphQL.

This module provides a hierarchical settings system that allows for:
1. Schema-specific settings
2. Global Django settings
3. Library defaults

Settings are resolved in the following order:
1. Schema-specific settings (highest priority)
2. Global Django RAIL_DJANGO_GRAPHQL settings
3. Library defaults (lowest priority)
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .core.settings import QueryGeneratorSettings, MutationGeneratorSettings, TypeGeneratorSettings
from .defaults import LIBRARY_DEFAULTS, get_merged_settings

logger = logging.getLogger(__name__)


class SettingsProxy:
    """
    A proxy for accessing Rail Django GraphQL settings with hierarchical resolution.

    This class provides a unified interface for accessing settings from multiple sources:
    - Schema-specific settings
    - Global Django settings
    - Library defaults
    """

    def __init__(self, schema_name: Optional[str] = None):
        """
        Initialize the settings proxy.

        Args:
            schema_name: Optional schema name for schema-specific settings
        """
        self.schema_name = schema_name
        self._cache = {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value with hierarchical resolution.

        Args:
            key: Setting key (supports dot notation for nested keys)
            default: Default value if key is not found

        Returns:
            Setting value
        """
        # Check cache first
        cache_key = f"{self.schema_name}:{key}" if self.schema_name else key
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try schema-specific settings first
        if self.schema_name:
            schema_value = self._get_schema_setting(key)
            if schema_value is not None:
                self._cache[cache_key] = schema_value
                return schema_value

        # Try global Django settings
        django_value = self._get_django_setting(key)
        if django_value is not None:
            self._cache[cache_key] = django_value
            return django_value

        # Try library defaults
        library_value = self._get_library_default(key)
        if library_value is not None:
            self._cache[cache_key] = library_value
            return library_value

        # Return default if nothing found
        self._cache[cache_key] = default
        return default

    def _get_schema_setting(self, key: str) -> Any:
        """Get setting from schema-specific configuration."""
        if not self.schema_name:
            return None

        schema_settings = getattr(settings, "RAIL_DJANGO_GRAPHQL_SCHEMAS", {})
        if self.schema_name not in schema_settings:
            return None

        return self._get_nested_value(schema_settings[self.schema_name], key)

    def _get_django_setting(self, key: str) -> Any:
        """Get setting from global Django RAIL_DJANGO_GRAPHQL settings."""
        django_settings = getattr(settings, "RAIL_DJANGO_GRAPHQL", {})
        return self._get_nested_value(django_settings, key)

    def _get_library_default(self, key: str) -> Any:
        """Get setting from library defaults."""
        return self._get_nested_value(LIBRARY_DEFAULTS, key)

    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """
        Get a nested value using dot notation.

        Args:
            data: Dictionary to search in
            key: Key with dot notation (e.g., 'QUERY_SETTINGS.MAX_DEPTH')

        Returns:
            Value if found, None otherwise
        """
        if not isinstance(data, dict):
            return None

        keys = key.split(".")
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None

        return current

    def set(self, key: str, value: Any, schema_specific: bool = False) -> None:
        """
        Set a setting value.

        Args:
            key: Setting key
            value: Setting value
            schema_specific: Whether to set as schema-specific setting
        """
        cache_key = f"{self.schema_name}:{key}" if self.schema_name else key
        self._cache[cache_key] = value

        if schema_specific and self.schema_name:
            # Set schema-specific setting
            if not hasattr(settings, "RAIL_DJANGO_GRAPHQL_SCHEMAS"):
                settings.RAIL_DJANGO_GRAPHQL_SCHEMAS = {}

            if self.schema_name not in settings.RAIL_DJANGO_GRAPHQL_SCHEMAS:
                settings.RAIL_DJANGO_GRAPHQL_SCHEMAS[self.schema_name] = {}

            self._set_nested_value(
                settings.RAIL_DJANGO_GRAPHQL_SCHEMAS[self.schema_name], key, value
            )
        else:
            # Set global setting
            if not hasattr(settings, "RAIL_DJANGO_GRAPHQL"):
                settings.RAIL_DJANGO_GRAPHQL = {}

            self._set_nested_value(settings.RAIL_DJANGO_GRAPHQL, key, value)

    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """Set a nested value using dot notation."""
        keys = key.split(".")
        current = data

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def clear_cache(self) -> None:
        """Clear the settings cache."""
        self._cache.clear()

    def validate(self) -> Dict[str, str]:
        """
        Validate current settings configuration.

        Returns:
            Dictionary of validation errors (empty if valid)
        """
        errors = {}

        # Validate required settings based on new structure
        required_settings = [
            "CORE_SCHEMA_SETTINGS.ENABLE_GRAPHIQL",
            "CORE_SCHEMA_SETTINGS.ENABLE_INTROSPECTION",
            "QUERY_SETTINGS.MAX_DEPTH",
            "MUTATION_SETTINGS.ENABLE_MUTATIONS",
        ]

        for setting in required_settings:
            value = self.get(setting)
            if value is None:
                errors[setting] = f"Required setting '{setting}' is not configured"

        # Validate data types based on new structure
        type_validations = {
            "QUERY_SETTINGS.MAX_DEPTH": int,
            "QUERY_SETTINGS.MAX_COMPLEXITY": int,
            "CORE_SCHEMA_SETTINGS.ENABLE_GRAPHIQL": bool,
            "CORE_SCHEMA_SETTINGS.ENABLE_INTROSPECTION": bool,
            "MUTATION_SETTINGS.ENABLE_MUTATIONS": bool,
            "PERFORMANCE_SETTINGS.ENABLE_QUERY_TIMEOUT": bool,
            "PERFORMANCE_SETTINGS.QUERY_TIMEOUT_SECONDS": int,
            "SECURITY_SETTINGS.ENABLE_RATE_LIMITING": bool,
            "SECURITY_SETTINGS.RATE_LIMIT_PER_MINUTE": int,
            "ERROR_SETTINGS.ENABLE_DETAILED_ERRORS": bool,
            "FILE_UPLOAD_SETTINGS.ENABLE_FILE_UPLOADS": bool,
            "FILE_UPLOAD_SETTINGS.MAX_FILE_SIZE": int,
            "MONITORING_SETTINGS.ENABLE_METRICS": bool,
            "DEVELOPMENT_SETTINGS.ENABLE_DEBUG_MODE": bool,
            "MIDDLEWARE_SETTINGS.ENABLE_PERFORMANCE_MIDDLEWARE": bool,
            "I18N_SETTINGS.ENABLE_I18N": bool,
            "TESTING_SETTINGS.ENABLE_TEST_MODE": bool,
        }

        for setting, expected_type in type_validations.items():
            value = self.get(setting)
            if value is not None and not isinstance(value, expected_type):
                errors[setting] = (
                    f"Setting '{setting}' must be of type {expected_type.__name__}"
                )

        # Validate list settings
        list_validations = {
            "TYPE_GENERATION_SETTINGS.EXCLUDED_MODELS": list,
            "TYPE_GENERATION_SETTINGS.INCLUDED_MODELS": list,
            "SECURITY_SETTINGS.QUERY_WHITELIST": list,
            "SECURITY_SETTINGS.QUERY_BLACKLIST": list,
            "SECURITY_SETTINGS.IP_WHITELIST": list,
            "SECURITY_SETTINGS.CORS_ALLOWED_ORIGINS": list,
            "FILE_UPLOAD_SETTINGS.ALLOWED_EXTENSIONS": list,
            "I18N_SETTINGS.SUPPORTED_LANGUAGES": list,
        }

        for setting, expected_type in list_validations.items():
            value = self.get(setting)
            if value is not None and not isinstance(value, expected_type):
                errors[setting] = (
                    f"Setting '{setting}' must be of type {expected_type.__name__}"
                )

        # Validate specific value constraints
        max_depth = self.get("QUERY_SETTINGS.MAX_DEPTH")
        if max_depth is not None and (max_depth < 1 or max_depth > 50):
            errors["QUERY_SETTINGS.MAX_DEPTH"] = "MAX_DEPTH must be between 1 and 50"

        max_complexity = self.get("QUERY_SETTINGS.MAX_COMPLEXITY")
        if max_complexity is not None and max_complexity < 1:
            errors["QUERY_SETTINGS.MAX_COMPLEXITY"] = (
                "MAX_COMPLEXITY must be greater than 0"
            )

        rate_limit = self.get("SECURITY_SETTINGS.RATE_LIMIT_PER_MINUTE")
        if rate_limit is not None and rate_limit < 1:
            errors["SECURITY_SETTINGS.RATE_LIMIT_PER_MINUTE"] = (
                "RATE_LIMIT_PER_MINUTE must be greater than 0"
            )

        return errors


class SchemaSettingsManager:
    """
    Manager for schema-specific settings.

    This class provides methods to manage settings for multiple GraphQL schemas.
    """

    def __init__(self):
        """Initialize the schema settings manager."""
        self._schema_proxies = {}

    def get_schema_proxy(self, schema_name: str) -> SettingsProxy:
        """
        Get a settings proxy for a specific schema.

        Args:
            schema_name: Name of the schema

        Returns:
            SettingsProxy instance for the schema
        """
        if schema_name not in self._schema_proxies:
            self._schema_proxies[schema_name] = SettingsProxy(schema_name)

        return self._schema_proxies[schema_name]

    def get_all_schemas(self) -> Dict[str, SettingsProxy]:
        """
        Get all registered schema proxies.

        Returns:
            Dictionary of schema name to SettingsProxy
        """
        return self._schema_proxies.copy()

    def register_schema(self, schema_name: str, settings_dict: Dict[str, Any]) -> None:
        """
        Register a new schema with its settings.

        Args:
            schema_name: Name of the schema
            settings_dict: Schema-specific settings
        """
        # Ensure Django settings structure exists
        if not hasattr(settings, "RAIL_DJANGO_GRAPHQL_SCHEMAS"):
            settings.RAIL_DJANGO_GRAPHQL_SCHEMAS = {}

        settings.RAIL_DJANGO_GRAPHQL_SCHEMAS[schema_name] = settings_dict

        # Create or update proxy
        self._schema_proxies[schema_name] = SettingsProxy(schema_name)

    def unregister_schema(self, schema_name: str) -> None:
        """
        Unregister a schema and its settings.

        Args:
            schema_name: Name of the schema to unregister
        """
        # Remove from Django settings
        if hasattr(settings, "RAIL_DJANGO_GRAPHQL_SCHEMAS"):
            settings.RAIL_DJANGO_GRAPHQL_SCHEMAS.pop(schema_name, None)

        # Remove proxy
        self._schema_proxies.pop(schema_name, None)

    def validate_all_schemas(self) -> Dict[str, Dict[str, str]]:
        """
        Validate settings for all registered schemas.

        Returns:
            Dictionary of schema name to validation errors
        """
        validation_results = {}

        for schema_name, proxy in self._schema_proxies.items():
            errors = proxy.validate()
            if errors:
                validation_results[schema_name] = errors

        return validation_results

    def get_merged_schema_settings(
        self, schema_name: str, environment: str = "development"
    ) -> Dict[str, Any]:
        """
        Get merged settings for a specific schema and environment.

        Args:
            schema_name: Name of the schema
            environment: Environment name (development, testing, production)

        Returns:
            Merged settings dictionary
        """
        return get_merged_settings(schema_name, environment)


# Global instances
settings_proxy = SettingsProxy()
schema_manager = SchemaSettingsManager()


def get_setting(
    key: str, default: Any = None, schema_name: Optional[str] = None
) -> Any:
    """
    Get a setting value with hierarchical resolution.

    Args:
        key: Setting key (supports dot notation)
        default: Default value if key is not found
        schema_name: Optional schema name for schema-specific settings

    Returns:
        Setting value
    """
    if schema_name:
        proxy = schema_manager.get_schema_proxy(schema_name)
        return proxy.get(key, default)
    else:
        return settings_proxy.get(key, default)


def set_setting(key: str, value: Any, schema_name: Optional[str] = None) -> None:
    """
    Set a setting value.

    Args:
        key: Setting key
        value: Setting value
        schema_name: Optional schema name for schema-specific settings
    """
    if schema_name:
        proxy = schema_manager.get_schema_proxy(schema_name)
        proxy.set(key, value, schema_specific=True)
    else:
        settings_proxy.set(key, value)


def validate_settings(schema_name: Optional[str] = None) -> Dict[str, str]:
    """
    Validate settings configuration.

    Args:
        schema_name: Optional schema name to validate specific schema

    Returns:
        Dictionary of validation errors
    """
    if schema_name:
        proxy = schema_manager.get_schema_proxy(schema_name)
        return proxy.validate()
    else:
        return settings_proxy.validate()


def clear_settings_cache() -> None:
    """Clear all settings caches."""
    settings_proxy.clear_cache()
    for proxy in schema_manager.get_all_schemas().values():
        proxy.clear_cache()


def get_core_schema_settings(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Get core schema settings."""
    return get_setting("SCHEMA_SETTINGS", {}, schema_name)


def get_query_settings(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Get query settings."""
    return get_setting("QUERY_SETTINGS", {}, schema_name)


def get_query_generator_settings(schema_name: Optional[str] = None) -> QueryGeneratorSettings:
    """
    Get query generator settings as QueryGeneratorSettings dataclass instance.
    
    Args:
        schema_name: Optional schema name for schema-specific settings
        
    Returns:
        QueryGeneratorSettings: Configured query generator settings
    """
    settings_dict = get_setting("QUERY_SETTINGS", {}, schema_name)
    
    # Create QueryGeneratorSettings instance from dictionary
    # Filter only the fields that exist in the dataclass
    valid_fields = {
        field.name for field in QueryGeneratorSettings.__dataclass_fields__.values()
    }
    
    filtered_settings = {
        key: value for key, value in settings_dict.items() 
        if key in valid_fields
    }
    
    return QueryGeneratorSettings(**filtered_settings)


def get_mutation_generator_settings(schema_name: Optional[str] = None) -> MutationGeneratorSettings:
    """
    Get mutation generator settings as MutationGeneratorSettings dataclass instance.
    
    Args:
        schema_name: Optional schema name for schema-specific settings
        
    Returns:
        MutationGeneratorSettings: Configured mutation generator settings
    """
    settings_dict = get_setting("MUTATION_SETTINGS", {}, schema_name)
    
    # Create MutationGeneratorSettings instance from dictionary
    # Filter only the fields that exist in the dataclass
    valid_fields = {
        field.name for field in MutationGeneratorSettings.__dataclass_fields__.values()
    }
    
    filtered_settings = {
        key: value for key, value in settings_dict.items() 
        if key in valid_fields
    }
    
    return MutationGeneratorSettings(**filtered_settings)


def get_type_generator_settings(schema_name: Optional[str] = None) -> TypeGeneratorSettings:
    """
    Get type generator settings as TypeGeneratorSettings dataclass instance.
    
    Args:
        schema_name: Optional schema name for schema-specific settings
        
    Returns:
        TypeGeneratorSettings: Configured type generator settings
    """
    settings_dict = get_setting("TYPE_GENERATION_SETTINGS", {}, schema_name)
    
    # Create TypeGeneratorSettings instance from dictionary
    # Filter only the fields that exist in the dataclass
    valid_fields = {
        field.name for field in TypeGeneratorSettings.__dataclass_fields__.values()
    }
    
    filtered_settings = {
        key: value for key, value in settings_dict.items() 
        if key in valid_fields
    }
    
    return TypeGeneratorSettings(**filtered_settings)


def get_mutation_settings(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Get mutation settings."""
    return get_setting("MUTATION_SETTINGS", {}, schema_name)


def get_type_generation_settings(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Get type generation settings."""
    return get_setting("TYPE_GENERATION_SETTINGS", {}, schema_name)


def get_performance_settings(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Get performance settings."""
    return get_setting("PERFORMANCE_SETTINGS", {}, schema_name)


def get_security_settings(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Get security settings."""
    return get_setting("SECURITY_SETTINGS", {}, schema_name)


def get_error_settings(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Get error handling settings."""
    return get_setting("ERROR_SETTINGS", {}, schema_name)


def get_caching_settings(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Get caching settings."""
    return get_setting("CACHING_SETTINGS", {}, schema_name)


def get_file_upload_settings(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Get file upload settings."""
    return get_setting("FILE_UPLOAD_SETTINGS", {}, schema_name)


def get_monitoring_settings(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Get monitoring settings."""
    return get_setting("MONITORING_SETTINGS", {}, schema_name)


def get_development_settings(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Get development settings."""
    return get_setting("DEVELOPMENT_SETTINGS", {}, schema_name)


def get_middleware_settings(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Get middleware settings."""
    return get_setting("MIDDLEWARE_SETTINGS", {}, schema_name)


def get_i18n_settings(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Get internationalization settings."""
    return get_setting("I18N_SETTINGS", {}, schema_name)


def get_testing_settings(schema_name: Optional[str] = None) -> Dict[str, Any]:
    """Get testing settings."""
    return get_setting("TESTING_SETTINGS", {}, schema_name)


# Backward compatibility aliases
settings = settings_proxy


def get_settings_for_schema(schema_name: str) -> SettingsProxy:
    """Get settings proxy for a specific schema (backward compatibility)."""
    return schema_manager.get_schema_proxy(schema_name)


def get_schema_settings(schema_name: str) -> SettingsProxy:
    """Get settings for a specific schema (backward compatibility)."""
    return get_settings_for_schema(schema_name)


def configure_schema_settings(schema_name: str, **overrides) -> None:
    """Configure settings for a specific schema (backward compatibility)."""
    schema_manager.register_schema(schema_name, overrides)


def validate_configuration() -> None:
    """Validate the current library configuration (backward compatibility)."""
    errors = validate_settings()
    if errors:
        error_msg = "; ".join([f"{k}: {v}" for k, v in errors.items()])
        raise ImproperlyConfigured(f"Configuration validation failed: {error_msg}")
    logger.info("Library configuration validation passed")


# Auto-validate configuration on import (in development)
if getattr(settings, "DEBUG", False):
    try:
        validate_configuration()
    except Exception as e:
        logger.warning(f"Configuration validation warning: {e}")
