"""Configuration loader for rail_django_graphql.

This module provides utilities to load and validate configuration settings
for the rail_django_graphql library, supporting the new hierarchical
configuration structure defined in settings.md.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from ..defaults import LIBRARY_DEFAULTS, get_merged_settings

logger = logging.getLogger(__name__)

# Import the new configuration system
try:
    from ..defaults import LIBRARY_DEFAULTS, get_merged_settings
    NEW_CONFIG_AVAILABLE = True
except ImportError:
    # Fallback for development
    logger.warning("New configuration system not available, using legacy loader")
    LIBRARY_DEFAULTS = {}
    get_merged_settings = None
    NEW_CONFIG_AVAILABLE = False

# Legacy imports for backward compatibility
try:
    from .settings import (
        MutationGeneratorSettings,
        SchemaSettings,
        TypeGeneratorSettings,
    )
except ImportError:
    logger.warning("Legacy settings classes not available")
    MutationGeneratorSettings = None
    TypeGeneratorSettings = None
    SchemaSettings = None


class ConfigLoader:
    """
    Configuration loader for rail_django_graphql settings.

    Supports the new hierarchical configuration structure with schema-specific
    and environment-specific overrides as defined in settings.md.
    """

    @staticmethod
    def get_rail_django_graphql_settings() -> Dict[str, Any]:
        """
        Get rail_django_graphql settings from Django settings with defaults.

        Returns:
            Dictionary containing merged rail_django_graphql configuration
        """
        user_settings = getattr(settings, "RAIL_DJANGO_GRAPHQL", {})
        
        # Get environment from Django settings or default to 'development'
        environment = getattr(settings, 'ENVIRONMENT', 'development')
        
        # Merge with defaults using the new hierarchical structure
        return get_merged_settings(user_settings, environment=environment)

    @staticmethod
    def get_schema_specific_settings(schema_name: str, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get schema-specific settings for a given schema.

        Args:
            schema_name: Name of the schema
            environment: Environment name (defaults to Django ENVIRONMENT setting)

        Returns:
            Dictionary containing schema-specific settings
        """
        if environment is None:
            environment = getattr(settings, 'ENVIRONMENT', 'development')
            
        user_settings = getattr(settings, "RAIL_DJANGO_GRAPHQL", {})
        return get_merged_settings(user_settings, schema_name=schema_name, environment=environment)

    @staticmethod
    def get_global_settings(environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get global rail_django_graphql settings (non-schema-specific).

        Args:
            environment: Environment name (defaults to Django ENVIRONMENT setting)

        Returns:
            Dictionary containing global settings
        """
        if environment is None:
            environment = getattr(settings, 'ENVIRONMENT', 'development')
            
        user_settings = getattr(settings, "RAIL_DJANGO_GRAPHQL", {})
        return get_merged_settings(user_settings, environment=environment)

    @staticmethod
    def get_core_schema_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get core schema settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing core schema settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("CORE_SCHEMA_SETTINGS", {})

    @staticmethod
    def get_query_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get query settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing query settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("QUERY_SETTINGS", {})

    @staticmethod
    def get_mutation_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get mutation settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing mutation settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("MUTATION_SETTINGS", {})

    @staticmethod
    def get_type_generation_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get type generation settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing type generation settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("TYPE_GENERATION_SETTINGS", {})

    @staticmethod
    def get_performance_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing performance settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("PERFORMANCE_SETTINGS", {})

    @staticmethod
    def get_security_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get security settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing security settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("SECURITY_SETTINGS", {})

    @staticmethod
    def get_error_handling_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get error handling settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing error handling settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("ERROR_HANDLING_SETTINGS", {})

    @staticmethod
    def get_caching_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get caching settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing caching settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("CACHING_SETTINGS", {})

    @staticmethod
    def get_file_upload_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get file upload settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing file upload settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("FILE_UPLOAD_SETTINGS", {})

    @staticmethod
    def get_monitoring_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get monitoring settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing monitoring settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("MONITORING_SETTINGS", {})

    @staticmethod
    def get_development_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get development settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing development settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("DEVELOPMENT_SETTINGS", {})

    @staticmethod
    def get_schema_registry_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get schema registry settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing schema registry settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("SCHEMA_REGISTRY_SETTINGS", {})

    @staticmethod
    def get_middleware_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get middleware settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing middleware settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("MIDDLEWARE_SETTINGS", {})

    @staticmethod
    def get_extension_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get extension settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing extension settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("EXTENSION_SETTINGS", {})

    @staticmethod
    def get_internationalization_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get internationalization settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing internationalization settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("INTERNATIONALIZATION_SETTINGS", {})

    @staticmethod
    def get_testing_settings(schema_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get testing settings.

        Args:
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            Dictionary containing testing settings
        """
        config = ConfigLoader.get_schema_specific_settings(schema_name, environment) if schema_name else ConfigLoader.get_global_settings(environment)
        return config.get("TESTING_SETTINGS", {})

    @staticmethod
    def validate_configuration(
        config: Optional[Dict[str, Any]] = None, 
        schema_name: Optional[str] = None,
        environment: Optional[str] = None
    ) -> bool:
        """
        Validate configuration settings using the new validation system.

        Args:
            config: Optional configuration dictionary
            schema_name: Optional schema name for schema-specific settings
            environment: Environment name

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            if config is None:
                if schema_name:
                    config = ConfigLoader.get_schema_specific_settings(schema_name, environment)
                else:
                    config = ConfigLoader.get_rail_django_graphql_settings()

            # Use the new validation system from defaults.py
            from ..defaults import validate_settings
            validate_settings(config)
            return True
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    @staticmethod
    def debug_configuration(schema_name: Optional[str] = None, environment: Optional[str] = None) -> None:
        """
        Print debug information about the current configuration.

        Args:
            schema_name: Optional schema name for schema-specific debug info
            environment: Environment name
        """
        if schema_name:
            config = ConfigLoader.get_schema_specific_settings(schema_name, environment)
            print(f"=== Schema '{schema_name}' Configuration Debug ===")
        else:
            config = ConfigLoader.get_rail_django_graphql_settings()
            print("=== Global rail_django_graphql Configuration Debug ===")

        print(f"Environment: {environment or getattr(settings, 'ENVIRONMENT', 'development')}")
        print(f"Full config keys: {list(config.keys())}")

        # Debug all new settings sections
        sections = [
            "CORE_SCHEMA_SETTINGS", "QUERY_SETTINGS", "MUTATION_SETTINGS", 
            "TYPE_GENERATION_SETTINGS", "PERFORMANCE_SETTINGS", "SECURITY_SETTINGS",
            "ERROR_HANDLING_SETTINGS", "CACHING_SETTINGS", "FILE_UPLOAD_SETTINGS",
            "MONITORING_SETTINGS", "DEVELOPMENT_SETTINGS", "SCHEMA_REGISTRY_SETTINGS",
            "MIDDLEWARE_SETTINGS", "EXTENSION_SETTINGS", "INTERNATIONALIZATION_SETTINGS",
            "TESTING_SETTINGS"
        ]
        
        for section in sections:
            if section in config:
                print(f"{section}: {len(config[section])} settings")
            else:
                print(f"{section}: not found")

        print("=== End Configuration Debug ===")


# Legacy support functions for backward compatibility
def get_rail_django_graphql_settings_legacy() -> Dict[str, Any]:
    """
    Legacy function to get rail_django_graphql settings.
    Maintained for backward compatibility.

    Returns:
        Dictionary containing rail_django_graphql configuration
    """
    return ConfigLoader.get_rail_django_graphql_settings()


# Helper functions for loading specific settings types
def load_mutation_settings_from_config(config: Dict[str, Any]) -> "MutationGeneratorSettings":
    """
    Load MutationGeneratorSettings from configuration dictionary.

    Args:
        config: Configuration dictionary

    Returns:
        MutationGeneratorSettings instance
    """
    # Import here to avoid circular imports
    try:
        from .settings import MutationGeneratorSettings
        return MutationGeneratorSettings.from_dict(config)
    except ImportError:
        logger.warning("MutationGeneratorSettings not available")
        return None


def load_type_settings_from_config(config: Dict[str, Any]) -> "TypeGeneratorSettings":
    """
    Load TypeGeneratorSettings from configuration dictionary.

    Args:
        config: Configuration dictionary

    Returns:
        TypeGeneratorSettings instance
    """
    # Import here to avoid circular imports
    try:
        from .settings import TypeGeneratorSettings
        return TypeGeneratorSettings.from_dict(config)
    except ImportError:
        logger.warning("TypeGeneratorSettings not available")
        return None


def load_schema_settings_from_config(config: Dict[str, Any]) -> "SchemaSettings":
    """
    Load SchemaSettings from configuration dictionary.

    Args:
        config: Configuration dictionary

    Returns:
        SchemaSettings instance
    """
    # Import here to avoid circular imports
    try:
        from .settings import SchemaSettings
        return SchemaSettings.from_dict(config)
    except ImportError:
        logger.warning("SchemaSettings not available")
        return None


def validate_configuration_legacy() -> bool:
    """
    Legacy wrapper to validate configuration using legacy schema.

    Returns:
        True if legacy configuration is valid, False otherwise.
    """
    try:
        config = get_rail_django_graphql_settings_legacy()
        # Basic validation for legacy config
        return isinstance(config, dict)
    except Exception as e:
        logger.error(f"Legacy configuration validation failed: {e}")
        return False


def debug_configuration_legacy() -> None:
    """Legacy debug function to print current configuration from Django settings."""
    config = get_rail_django_graphql_settings_legacy()
    print("=== Legacy rail_django_graphql Configuration Debug ===")
    print(f"Full legacy config: {config}")
    
    # Debug legacy sections
    legacy_sections = ["MUTATION_SETTINGS", "TYPE_SETTINGS", "SCHEMA_SETTINGS"]
    for section in legacy_sections:
        if section in config:
            print(f"{section} found: {config[section]}")
        else:
            print(f"{section} not found in legacy configuration")
    
    print("=== End Legacy Configuration Debug ===")


# Additional helper functions for the new configuration structure
def get_setting_value(key: str, default: Any = None, schema_name: Optional[str] = None, environment: Optional[str] = None) -> Any:
    """
    Get a specific setting value with hierarchical lookup.

    Args:
        key: Setting key (supports dot notation like 'MUTATION_SETTINGS.enable_create')
        default: Default value if setting not found
        schema_name: Optional schema name for schema-specific settings
        environment: Environment name

    Returns:
        Setting value or default
    """
    try:
        if schema_name:
            config = ConfigLoader.get_schema_specific_settings(schema_name, environment)
        else:
            config = ConfigLoader.get_rail_django_graphql_settings()
        
        # Support dot notation for nested dict
        if "." in key:
            keys = key.split(".")
            value = config
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        else:
            return config.get(key, default)
    except Exception as e:
        logger.warning(f"Error getting setting '{key}': {e}")
        return default
