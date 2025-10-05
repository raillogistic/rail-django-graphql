"""
Configuration loader for rail-django-graphql library.

This module provides a hierarchical settings system that merges:
1. Library defaults (lowest priority)
2. Global Django settings overrides (medium priority)
3. Schema-specific overrides (highest priority)

Usage:
    from rail_django_graphql.conf import settings

    # Access settings with automatic hierarchy resolution
    enable_graphiql = settings.ENABLE_GRAPHIQL
    query_settings = settings.QUERY_SETTINGS
"""

import logging
from typing import Any, Dict, Optional, Union

from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured

from .defaults import LIBRARY_DEFAULTS

logger = logging.getLogger(__name__)


class SettingsProxy:
    """
    Proxy object that provides access to library settings with hierarchical resolution.

    Settings are resolved in this priority order:
    1. Schema-specific overrides (highest priority)
    2. Global Django settings overrides (RAIL_DJANGO_GRAPHQL setting)
    3. Library defaults (lowest priority)
    """

    def __init__(self):
        self._cache = {}
        self._schema_overrides = {}

    def __getattr__(self, name: str) -> Any:
        """Get setting value with hierarchical resolution."""
        if name.startswith("_"):
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

        # Check cache first
        cache_key = f"{name}_{id(self._schema_overrides)}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Resolve setting value
        value = self._resolve_setting(name)
        self._cache[cache_key] = value
        return value

    def get(self, name: str, default: Any = None) -> Any:
        """Get setting value with optional default."""
        try:
            return self._resolve_setting(name)
        except AttributeError:
            return default

    def _resolve_setting(self, name: str) -> Any:
        """Resolve setting value using hierarchical priority."""
        # 1. Schema-specific overrides (highest priority)
        if name in self._schema_overrides:
            logger.debug(f"Using schema override for {name}")
            return self._schema_overrides[name]

        # 2. Global Django settings overrides
        django_config = getattr(django_settings, "RAIL_DJANGO_GRAPHQL", {})
        if name in django_config:
            logger.debug(f"Using global Django setting for {name}")
            return django_config[name]

        # 3. Library defaults (lowest priority)
        if name in LIBRARY_DEFAULTS:
            logger.debug(f"Using library default for {name}")
            return LIBRARY_DEFAULTS[name]
        # 4. Nested SCHEMA_SETTINGS lookup for dataclass-style keys
        nested_schema: Optional[Dict[str, Any]] = None
        if "SCHEMA_SETTINGS" in self._schema_overrides and isinstance(self._schema_overrides["SCHEMA_SETTINGS"], dict):
            nested_schema = self._schema_overrides["SCHEMA_SETTINGS"]
        elif "SCHEMA_SETTINGS" in django_config and isinstance(django_config["SCHEMA_SETTINGS"], dict):
            nested_schema = django_config["SCHEMA_SETTINGS"]
        elif "SCHEMA_SETTINGS" in LIBRARY_DEFAULTS and isinstance(LIBRARY_DEFAULTS["SCHEMA_SETTINGS"], dict):
            nested_schema = LIBRARY_DEFAULTS["SCHEMA_SETTINGS"]
        if nested_schema and name in nested_schema:
            logger.debug(f"Using nested SCHEMA_SETTINGS for {name}")
            return nested_schema[name]
        # Setting not found
        raise AttributeError(f"Setting '{name}' not found in library configuration")

    def set_schema_overrides(self, overrides: Dict[str, Any]) -> None:
        """Set schema-specific setting overrides."""
        self._schema_overrides = overrides.copy()
        self._cache.clear()  # Clear cache when overrides change
        logger.debug(f"Set schema overrides: {list(overrides.keys())}")

    def clear_schema_overrides(self) -> None:
        """Clear all schema-specific overrides."""
        self._schema_overrides.clear()
        self._cache.clear()
        logger.debug("Cleared schema overrides")

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all resolved settings as a dictionary."""
        result = {}

        # Start with library defaults
        result.update(LIBRARY_DEFAULTS)

        # Apply global Django settings
        django_config = getattr(django_settings, "RAIL_DJANGO_GRAPHQL", {})
        result.update(django_config)

        # Apply schema overrides
        result.update(self._schema_overrides)

        return result

    def validate_settings(self) -> None:
        """Validate current settings configuration."""
        all_settings = self.get_all_settings()

        # Validate required settings
        required_settings = ["DEFAULT_SCHEMA", "ENABLE_GRAPHIQL"]
        for setting in required_settings:
            if setting not in all_settings:
                raise ImproperlyConfigured(f"Required setting '{setting}' is missing")

        # Validate setting types
        type_validations = {
            "ENABLE_GRAPHIQL": bool,
            "AUTHENTICATION_REQUIRED": bool,
            "MAX_QUERY_DEPTH": int,
            "MAX_QUERY_COMPLEXITY": int,
            "ENABLE_CACHING": bool,
            "CACHE_TIMEOUT": int,
        }

        for setting, expected_type in type_validations.items():
            if setting in all_settings:
                value = all_settings[setting]
                if not isinstance(value, expected_type):
                    raise ImproperlyConfigured(
                        f"Setting '{setting}' must be of type {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )

        logger.info("Settings validation passed")


class SchemaSettingsManager:
    """
    Manager for schema-specific settings.

    Allows different GraphQL schemas to have different configurations
    while maintaining the hierarchical settings resolution.
    """

    def __init__(self):
        self._schema_settings = {}

    def get_settings_for_schema(self, schema_name: str) -> SettingsProxy:
        """Get settings proxy for a specific schema."""
        if schema_name not in self._schema_settings:
            proxy = SettingsProxy()

            # Apply schema-specific overrides from Django settings
            django_config = getattr(django_settings, "RAIL_DJANGO_GRAPHQL", {})
            schema_overrides = django_config.get("SCHEMA_OVERRIDES", {}).get(
                schema_name, {}
            )

            if schema_overrides:
                proxy.set_schema_overrides(schema_overrides)

            self._schema_settings[schema_name] = proxy

        return self._schema_settings[schema_name]

    def register_schema_overrides(
        self, schema_name: str, overrides: Dict[str, Any]
    ) -> None:
        """Register overrides for a specific schema."""
        proxy = self.get_settings_for_schema(schema_name)

        # Merge with existing overrides
        existing_overrides = proxy._schema_overrides.copy()
        existing_overrides.update(overrides)
        proxy.set_schema_overrides(existing_overrides)

        logger.info(
            f"Registered overrides for schema '{schema_name}': {list(overrides.keys())}"
        )

    def clear_schema_overrides(self, schema_name: str) -> None:
        """Clear overrides for a specific schema."""
        if schema_name in self._schema_settings:
            self._schema_settings[schema_name].clear_schema_overrides()
            logger.info(f"Cleared overrides for schema '{schema_name}'")


# Global instances
settings = SettingsProxy()
schema_manager = SchemaSettingsManager()


def get_settings_for_schema(schema_name: str) -> SettingsProxy:
    """
    Get settings proxy for a specific schema.

    Args:
        schema_name: Name of the GraphQL schema

    Returns:
        SettingsProxy configured for the specified schema
    """
    return schema_manager.get_settings_for_schema(schema_name)


def get_schema_settings(schema_name: str) -> SettingsProxy:
    """
    Get settings for a specific schema (alias for get_settings_for_schema).

    Args:
        schema_name: Name of the GraphQL schema

    Returns:
        SettingsProxy configured for the specified schema
    """
    return get_settings_for_schema(schema_name)


def configure_schema_settings(schema_name: str, **overrides) -> None:
    """
    Configure settings for a specific schema.

    Args:
        schema_name: Name of the GraphQL schema
        **overrides: Setting overrides to apply
    """
    schema_manager.register_schema_overrides(schema_name, overrides)


def validate_configuration() -> None:
    """Validate the current library configuration."""
    try:
        settings.validate_settings()
        logger.info("Library configuration validation passed")
    except Exception as e:
        logger.error(f"Library configuration validation failed: {e}")
        raise


# Auto-validate configuration on import (in development)
if django_settings.DEBUG:
    try:
        validate_configuration()
    except Exception as e:
        logger.warning(f"Configuration validation warning: {e}")
