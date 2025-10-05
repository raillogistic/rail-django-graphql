"""
Configuration loader for rail-django-graphql library.

This module provides utilities to load configuration from Django settings
and apply them to the various settings classes. It integrates with the new
hierarchical configuration system.
"""

from typing import Dict, Any, Optional, Type, TypeVar
from django.conf import settings as django_settings
import logging

logger = logging.getLogger(__name__)

# Import the new configuration system
try:
    from ..conf import (
        settings as conf_settings,
        get_schema_settings as conf_get_schema_settings,
        validate_configuration as conf_validate_configuration,
    )
    NEW_CONFIG_AVAILABLE = True
except ImportError:
    # Fallback for development
    logger.warning("New configuration system not available, using legacy loader")
    conf_settings = None
    conf_get_schema_settings = None
    conf_validate_configuration = None
    NEW_CONFIG_AVAILABLE = False

# Legacy imports for backward compatibility
try:
    from .settings import MutationGeneratorSettings, TypeGeneratorSettings, SchemaSettings
except ImportError:
    logger.warning("Legacy settings classes not available")
    MutationGeneratorSettings = None
    TypeGeneratorSettings = None
    SchemaSettings = None

T = TypeVar('T')


class ConfigLoader:
    """
    Configuration loader class for rail-django-graphql library.

    This class provides methods to load and validate configuration from Django settings
    using the new hierarchical configuration system.
    """

    @staticmethod
    def get_rail_django_graphql_settings() -> Dict[str, Any]:
        """
        Get rail_django_graphql settings from Django settings.

        Returns:
            Dictionary containing the configuration, or empty dict if not found.
        """
        if NEW_CONFIG_AVAILABLE and conf_settings:
            return conf_settings.get_all_settings()
        return get_rail_django_graphql_settings_legacy()

    @staticmethod
    def get_schema_specific_settings(schema_name: str) -> Dict[str, Any]:
        """
        Get schema-specific settings.

        Args:
            schema_name: Name of the schema

        Returns:
            Dictionary containing schema-specific configuration
        """
        if NEW_CONFIG_AVAILABLE and conf_get_schema_settings:
            return conf_get_schema_settings(schema_name).get_all_settings()
        return {}

    @staticmethod
    def load_mutation_settings(schema_name: Optional[str] = None) -> 'MutationGeneratorSettings':
        """
        Load MutationGeneratorSettings from Django settings.

        Args:
            schema_name: Optional schema name for schema-specific settings

        Returns:
            MutationGeneratorSettings instance with configuration from Django settings.
        """
        if NEW_CONFIG_AVAILABLE and schema_name and conf_get_schema_settings:
            config = conf_get_schema_settings(schema_name).get_all_settings()
            mutation_config = config.get("MUTATION_SETTINGS", {})
        else:
            mutation_config = ConfigLoader.get_rail_django_graphql_settings().get("MUTATION_SETTINGS", {})
        
        return load_mutation_settings_from_config(mutation_config)

    @staticmethod
    def load_type_settings(schema_name: Optional[str] = None) -> 'TypeGeneratorSettings':
        """
        Load TypeGeneratorSettings from Django settings.

        Args:
            schema_name: Optional schema name for schema-specific settings

        Returns:
            TypeGeneratorSettings instance with configuration from Django settings.
        """
        if NEW_CONFIG_AVAILABLE and schema_name and conf_get_schema_settings:
            config = conf_get_schema_settings(schema_name).get_all_settings()
            type_config = config.get("TYPE_SETTINGS", {})
        else:
            type_config = ConfigLoader.get_rail_django_graphql_settings().get("TYPE_SETTINGS", {})
        
        return load_type_settings_from_config(type_config)

    @staticmethod
    def load_schema_settings(schema_name: Optional[str] = None) -> 'SchemaSettings':
        """
        Load SchemaSettings from Django settings.

        Args:
            schema_name: Optional schema name for schema-specific settings

        Returns:
            SchemaSettings instance with configuration from Django settings.
        """
        if NEW_CONFIG_AVAILABLE and schema_name and conf_get_schema_settings:
            config = conf_get_schema_settings(schema_name).get_all_settings()
        else:
            config = ConfigLoader.get_rail_django_graphql_settings()
        
        return load_schema_settings_from_config(config)

    @staticmethod
    def validate_configuration() -> bool:
        """
        Validate the rail_django_graphql configuration.

        Returns:
            True if configuration is valid, False otherwise.
        """
        try:
            if NEW_CONFIG_AVAILABLE and conf_validate_configuration:
                try:
                    conf_validate_configuration()
                    return True
                except Exception as e:
                    logger.error(f"New configuration validation failed: {e}")
                    return False
            else:
                return validate_configuration_legacy()
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    @staticmethod
    def debug_configuration_new() -> None:
        """
        Print debug information about the current configuration.
        """
        if NEW_CONFIG_AVAILABLE:
            debug_configuration_new()
        else:
            debug_configuration_legacy()

    @staticmethod
    def get_setting(key: str, default: Any = None, schema_name: Optional[str] = None) -> Any:
        """
        Get a specific setting value with hierarchical lookup.

        Args:
            key: Setting key (supports dot notation like 'MUTATION_SETTINGS.enable_create')
            default: Default value if setting not found
            schema_name: Optional schema name for schema-specific settings

        Returns:
            Setting value or default
        """
        try:
            if NEW_CONFIG_AVAILABLE and conf_settings:
                proxy = (
                    conf_get_schema_settings(schema_name)
                    if (schema_name and conf_get_schema_settings)
                    else conf_settings
                )
                # Support dot notation for nested dict
                if "." in key:
                    keys = key.split(".")
                    root = keys[0]
                    value = proxy.get(root, default)
                    for k in keys[1:]:
                        if isinstance(value, dict) and k in value:
                            value = value[k]
                        else:
                            return default
                    return value
                else:
                    return proxy.get(key, default)
            else:
                # Legacy fallback
                config = get_rail_django_graphql_settings_legacy()
                keys = key.split('.')
                value = config
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        return default
                return value
        except Exception as e:
            logger.warning(f"Error getting setting '{key}': {e}")
            return default


# Legacy functions for backward compatibility
def get_rail_django_graphql_settings_legacy() -> Dict[str, Any]:
    """
    Legacy function to get rail_django_graphql settings from Django settings.

    Returns:
        Dictionary containing the configuration, or empty dict if not found.
    """
    return getattr(django_settings, "RAIL_DJANGO_GRAPHQL", {})


def load_mutation_settings_from_config(mutation_config: Dict[str, Any]) -> 'MutationGeneratorSettings':
    """
    Load MutationGeneratorSettings from configuration dictionary.

    Args:
        mutation_config: Configuration dictionary for mutations

    Returns:
        MutationGeneratorSettings instance with configuration.
    """
    if not MutationGeneratorSettings:
        raise ImportError("MutationGeneratorSettings not available")
    
    # Create settings instance with loaded configuration
    mutation_settings = MutationGeneratorSettings(
        enable_nested_relations=mutation_config.get("enable_nested_relations", False),
        nested_relations_config=mutation_config.get("nested_relations_config", {}),
        nested_field_config=mutation_config.get("nested_field_config", {}),
        # Keep other default values
        generate_create=mutation_config.get("generate_create", True),
        generate_update=mutation_config.get("generate_update", True),
        generate_delete=mutation_config.get("generate_delete", True),
        generate_bulk=mutation_config.get("generate_bulk", False),
        enable_create=mutation_config.get("enable_create", True),
        enable_update=mutation_config.get("enable_update", True),
        enable_delete=mutation_config.get("enable_delete", True),
        enable_bulk_operations=mutation_config.get("enable_bulk_operations", False),
        enable_method_mutations=mutation_config.get("enable_method_mutations", False),
        bulk_batch_size=mutation_config.get("bulk_batch_size", 100),
        required_update_fields=mutation_config.get("required_update_fields", {}),
    )

    return mutation_settings


def load_type_settings_from_config(type_config: Dict[str, Any]) -> 'TypeGeneratorSettings':
    """
    Load TypeGeneratorSettings from configuration dictionary.

    Args:
        type_config: Configuration dictionary for types

    Returns:
        TypeGeneratorSettings instance with configuration.
    """
    if not TypeGeneratorSettings:
        raise ImportError("TypeGeneratorSettings not available")
    
    # Create settings instance with loaded configuration
    type_settings = TypeGeneratorSettings(
        naming_convention=type_config.get("naming_convention", "snake_case"),
        enable_relationships=type_config.get("enable_relationships", True),
        enable_reverse_relationships=type_config.get(
            "enable_reverse_relationships", True
        ),
        max_relationship_depth=type_config.get("max_relationship_depth", 3),
        enable_custom_scalars=type_config.get("enable_custom_scalars", True),
        custom_scalar_mapping=type_config.get("custom_scalar_mapping", {}),
        field_converters=type_config.get("field_converters", {}),
        exclude_fields=type_config.get("exclude_fields", []),
        include_fields=type_config.get("include_fields", []),
        enable_inheritance=type_config.get("enable_inheritance", True),
    )

    return type_settings


def load_schema_settings_from_config(config: Dict[str, Any]) -> 'SchemaSettings':
    """
    Load SchemaSettings from configuration dictionary.

    Args:
        config: Configuration dictionary

    Returns:
        SchemaSettings instance with configuration.
    """
    if not SchemaSettings:
       raise ImportError("SchemaSettings not available")
   
    # Map lowercase to uppercase keys for backward compatibility
    key_mapping = {
        "excluded_apps": "APPS_TO_EXCLUDE",
        "excluded_models": "MODELS_TO_EXCLUDE", 
        "enable_introspection": "ENABLE_INTROSPECTION",
        "enable_graphiql": "ENABLE_GRAPHIQL",
        "auto_refresh_on_model_change": "AUTO_REFRESH_ON_MODEL_CHANGE",
        "enable_pagination": "ENABLE_PAGINATION",
        "auto_camelcase": "AUTO_CAMELCASE",
    }
    
    # Helper function to get value with fallback mapping
    def get_config_value(lowercase_key: str, default: Any) -> Any:
        sentinel = object()
        uppercase_key = key_mapping.get(lowercase_key)

        # Prefer attribute-style access via .get if available (SettingsProxy or dict)
        if hasattr(config, "get"):
            # Try lowercase direct
            value = config.get(lowercase_key, sentinel)
            if value is not sentinel:
                return value
            # Try uppercase direct
            if uppercase_key:
                value = config.get(uppercase_key, sentinel)
                if value is not sentinel:
                    return value
            # Try nested SCHEMA_SETTINGS
            nested = config.get("SCHEMA_SETTINGS", {})
            if hasattr(nested, "get"):
                value = nested.get(lowercase_key, sentinel)
                if value is not sentinel:
                    return value
        else:
            # Fallback plain dict-like access
            try:
                if lowercase_key in config:
                    return config[lowercase_key]
                if uppercase_key and uppercase_key in config:
                    return config[uppercase_key]
                nested = config.get("SCHEMA_SETTINGS", {})
                if isinstance(nested, dict) and lowercase_key in nested:
                    return nested[lowercase_key]
            except Exception:
                pass
        return default
    
    # Create settings instance with loaded configuration
    schema_settings = SchemaSettings(
        excluded_apps=get_config_value("excluded_apps", ["admin", "auth", "contenttypes", "sessions"]),
        excluded_models=get_config_value("excluded_models", []),
        enable_introspection=get_config_value("enable_introspection", True),
        enable_graphiql=get_config_value("enable_graphiql", True),
        auto_refresh_on_model_change=get_config_value("auto_refresh_on_model_change", True),
        enable_pagination=get_config_value("enable_pagination", True),
        auto_camelcase=get_config_value("auto_camelcase", False),
    )

    return schema_settings


# Legacy functions
def load_mutation_settings_legacy() -> 'MutationGeneratorSettings':
    """
    Legacy function to load MutationGeneratorSettings from Django settings.

    Returns:
        MutationGeneratorSettings instance with configuration from Django settings.
    """
    config = get_rail_django_graphql_settings_legacy()
    mutation_config = config.get("MUTATION_SETTINGS", {})
    return load_mutation_settings_from_config(mutation_config)


def load_type_settings_legacy() -> 'TypeGeneratorSettings':
    """
    Legacy function to load TypeGeneratorSettings from Django settings.

    Returns:
        TypeGeneratorSettings instance with configuration from Django settings.
    """
    config = get_rail_django_graphql_settings_legacy()
    type_config = config.get("TYPE_SETTINGS", {})
    return load_type_settings_from_config(type_config)


# Note: legacy load_schema_settings is redundant because ConfigLoader.load_schema_settings covers both


def validate_configuration_dict(config: dict) -> dict:
    """
    Valide la configuration rail_django_graphql avec validation complète du schéma.

    Args:
        config: Configuration à valider

    Returns:
        Configuration validée avec les valeurs par défaut

    Raises:
        ImproperlyConfigured: Si la configuration est invalide
    """
    from django.core.exceptions import ImproperlyConfigured
    import logging

    logger = logging.getLogger("rail_django_graphql.config")
    validated_config = config.copy()
    validation_errors = []

    # Schéma de validation complet
    validation_schema = {
        "MUTATION_SETTINGS": {
            "type": dict,
            "required": False,
            "schema": {
                "nested_relations_config": {
                    "type": dict,
                    "required": False,
                    "value_type": bool,
                    "description": "Configuration des relations imbriquées par modèle",
                },
                "nested_field_config": {
                    "type": dict,
                    "required": False,
                    "value_type": bool,
                    "description": "Configuration des champs imbriqués",
                },
                "enable_create_mutations": {
                    "type": bool,
                    "required": False,
                    "default": True,
                    "description": "Activer les mutations de création",
                },
                "enable_update_mutations": {
                    "type": bool,
                    "required": False,
                    "default": True,
                    "description": "Activer les mutations de mise à jour",
                },
                "enable_delete_mutations": {
                    "type": bool,
                    "required": False,
                    "default": True,
                    "description": "Activer les mutations de suppression",
                },
                "max_nested_depth": {
                    "type": int,
                    "required": False,
                    "default": 3,
                    "min_value": 1,
                    "max_value": 10,
                    "description": "Profondeur maximale des relations imbriquées",
                },
                "batch_size_limit": {
                    "type": int,
                    "required": False,
                    "default": 100,
                    "min_value": 1,
                    "max_value": 1000,
                    "description": "Limite de taille pour les opérations par lot",
                },
            },
        },
        "TYPE_SETTINGS": {
            "type": dict,
            "required": False,
            "schema": {
                "enable_relay_connections": {
                    "type": bool,
                    "required": False,
                    "default": False,
                    "description": "Activer les connexions Relay",
                },
                "enable_filtering": {
                    "type": bool,
                    "required": False,
                    "default": True,
                    "description": "Activer le filtrage des requêtes",
                },
                "enable_ordering": {
                    "type": bool,
                    "required": False,
                    "default": True,
                    "description": "Activer le tri des requêtes",
                },
                "enable_pagination": {
                    "type": bool,
                    "required": False,
                    "default": True,
                    "description": "Activer la pagination",
                },
                "default_page_size": {
                    "type": int,
                    "required": False,
                    "default": 20,
                    "min_value": 1,
                    "max_value": 1000,
                    "description": "Taille de page par défaut",
                },
                "max_page_size": {
                    "type": int,
                    "required": False,
                    "default": 100,
                    "min_value": 1,
                    "max_value": 10000,
                    "description": "Taille de page maximale",
                },
            },
        },
        "SCHEMA_SETTINGS": {
            "type": dict,
            "required": False,
            "schema": {
                "enable_introspection": {
                    "type": bool,
                    "required": False,
                    "default": True,
                    "description": "Activer l'introspection du schéma",
                },
                "enable_playground": {
                    "type": bool,
                    "required": False,
                    "default": True,
                    "description": "Activer GraphQL Playground",
                },
                "schema_name": {
                    "type": str,
                    "required": False,
                    "default": "Auto Generated Schema",
                    "description": "Nom du schéma GraphQL",
                },
                "schema_description": {
                    "type": str,
                    "required": False,
                    "default": "Automatically generated GraphQL schema",
                    "description": "Description du schéma GraphQL",
                },
            },
        },
        "SECURITY_SETTINGS": {
            "type": dict,
            "required": False,
            "schema": {
                "enable_query_depth_analysis": {
                    "type": bool,
                    "required": False,
                    "default": True,
                    "description": "Activer l'analyse de profondeur des requêtes",
                },
                "max_query_depth": {
                    "type": int,
                    "required": False,
                    "default": 10,
                    "min_value": 1,
                    "max_value": 50,
                    "description": "Profondeur maximale des requêtes",
                },
                "enable_query_complexity_analysis": {
                    "type": bool,
                    "required": False,
                    "default": True,
                    "description": "Activer l'analyse de complexité des requêtes",
                },
                "max_query_complexity": {
                    "type": int,
                    "required": False,
                    "default": 1000,
                    "min_value": 1,
                    "max_value": 10000,
                    "description": "Complexité maximale des requêtes",
                },
                "enable_rate_limiting": {
                    "type": bool,
                    "required": False,
                    "default": False,
                    "description": "Activer la limitation de débit",
                },
                "rate_limit_per_minute": {
                    "type": int,
                    "required": False,
                    "default": 60,
                    "min_value": 1,
                    "max_value": 10000,
                    "description": "Limite de requêtes par minute",
                },
            },
        },
        "PERFORMANCE_SETTINGS": {
            "type": dict,
            "required": False,
            "schema": {
                "enable_query_caching": {
                    "type": bool,
                    "required": False,
                    "default": False,
                    "description": "Activer la mise en cache des requêtes",
                },
                "cache_timeout": {
                    "type": int,
                    "required": False,
                    "default": 300,
                    "min_value": 1,
                    "max_value": 86400,
                    "description": "Timeout du cache en secondes",
                },
                "enable_dataloader": {
                    "type": bool,
                    "required": False,
                    "default": True,
                    "description": "Activer DataLoader pour optimiser les requêtes",
                },
                "enable_query_optimization": {
                    "type": bool,
                    "required": False,
                    "default": True,
                    "description": "Activer l'optimisation automatique des requêtes",
                },
            },
        },
    }

    # Validation récursive
    def validate_section(
        section_name: str, section_config: dict, section_schema: dict
    ) -> dict:
        validated_section = {}

        for key, schema_def in section_schema.items():
            value = section_config.get(key)

            # Vérifier si le champ est requis
            if schema_def.get("required", False) and value is None:
                validation_errors.append(f"{section_name}.{key} est requis")
                continue

            # Appliquer la valeur par défaut si nécessaire
            if value is None and "default" in schema_def:
                value = schema_def["default"]

            if value is not None:
                # Validation du type
                expected_type = schema_def["type"]
                if not isinstance(value, expected_type):
                    validation_errors.append(
                        f"{section_name}.{key} doit être de type {expected_type.__name__}, "
                        f"reçu {type(value).__name__}"
                    )
                    continue

                # Validation des valeurs numériques
                if expected_type in (int, float):
                    if "min_value" in schema_def and value < schema_def["min_value"]:
                        validation_errors.append(
                            f"{section_name}.{key} doit être >= {schema_def['min_value']}"
                        )
                        continue

                    if "max_value" in schema_def and value > schema_def["max_value"]:
                        validation_errors.append(
                            f"{section_name}.{key} doit être <= {schema_def['max_value']}"
                        )
                        continue

                # Validation des dictionnaires avec type de valeur spécifique
                if expected_type == dict and "value_type" in schema_def:
                    value_type = schema_def["value_type"]
                    for dict_key, dict_value in value.items():
                        if not isinstance(dict_value, value_type):
                            validation_errors.append(
                                f"{section_name}.{key}.{dict_key} doit être de type {value_type.__name__}"
                            )

                # Validation des sous-schémas
                if expected_type == dict and "schema" in schema_def:
                    validated_subsection = validate_section(
                        f"{section_name}.{key}", value, schema_def["schema"]
                    )
                    validated_section[key] = validated_subsection
                else:
                    validated_section[key] = value

        return validated_section

    # Valider chaque section principale
    for section_name, section_schema in validation_schema.items():
        if section_name in validated_config:
            section_config = validated_config[section_name]
            if not isinstance(section_config, dict):
                validation_errors.append(f"{section_name} doit être un dictionnaire")
                continue

            validated_section = validate_section(
                section_name, section_config, section_schema["schema"]
            )
            validated_config[section_name] = validated_section
        else:
            # Appliquer les valeurs par défaut pour les sections manquantes
            default_section = {}
            for key, schema_def in section_schema["schema"].items():
                if "default" in schema_def:
                    default_section[key] = schema_def["default"]

            if default_section:
                validated_config[section_name] = default_section

    # Validation des dépendances inter-sections
    _validate_cross_section_dependencies(validated_config, validation_errors)

    # Lever une exception si des erreurs ont été trouvées
    if validation_errors:
        error_message = "Erreurs de validation de configuration:\n" + "\n".join(
            f"  - {error}" for error in validation_errors
        )
        raise ImproperlyConfigured(error_message)

    return validated_config


def _validate_cross_section_dependencies(config: dict, errors: list) -> None:
    """
    Valide les dépendances entre différentes sections de configuration.

    Args:
        config: Configuration validée
        errors: Liste des erreurs à compléter
    """
    import logging

    logger = logging.getLogger(__name__)

    # Vérifier que max_page_size >= default_page_size
    type_settings = config.get("TYPE_SETTINGS", {})
    if type_settings:
        default_page_size = type_settings.get("default_page_size", 20)
        max_page_size = type_settings.get("max_page_size", 100)

        if default_page_size > max_page_size:
            errors.append(
                "TYPE_SETTINGS.default_page_size ne peut pas être supérieur à max_page_size"
            )

    # Vérifier que max_nested_depth est cohérent avec max_query_depth
    mutation_settings = config.get("MUTATION_SETTINGS", {})
    security_settings = config.get("SECURITY_SETTINGS", {})

    if mutation_settings and security_settings:
        max_nested_depth = mutation_settings.get("max_nested_depth", 3)
        max_query_depth = security_settings.get("max_query_depth", 10)

        if max_nested_depth > max_query_depth:
            errors.append(
                "MUTATION_SETTINGS.max_nested_depth ne peut pas être supérieur à "
                "SECURITY_SETTINGS.max_query_depth"
            )

    # Vérifier que le cache est activé si DataLoader est activé
    performance_settings = config.get("PERFORMANCE_SETTINGS", {})
    if performance_settings:
        enable_dataloader = performance_settings.get("enable_dataloader", True)
        enable_query_caching = performance_settings.get("enable_query_caching", False)

        if enable_dataloader and not enable_query_caching:
            # Avertissement plutôt qu'erreur
            logger.warning(
                "DataLoader est activé mais pas la mise en cache des requêtes. "
                "Considérez activer PERFORMANCE_SETTINGS.enable_query_caching pour de meilleures performances."
            )


def debug_configuration_new() -> None:
    """
    Print debug information about the current configuration.
    """
    config = ConfigLoader.get_rail_django_graphql_settings()
    print("=== rail_django_graphql Configuration Debug ===")
    print(f"Full config: {config}")

    if "MUTATION_SETTINGS" in config:
        mutation_settings = config["MUTATION_SETTINGS"]
        print(f"MUTATION_SETTINGS found: {mutation_settings}")

        print(
            f"enable_nested_relations: {mutation_settings.get('enable_nested_relations', 'NOT SET')}"
        )
        print(
            f"nested_relations_config: {mutation_settings.get('nested_relations_config', 'NOT SET')}"
        )
        print(
            f"nested_field_config: {mutation_settings.get('nested_field_config', 'NOT SET')}"
        )
    else:
        print("MUTATION_SETTINGS not found in configuration")

    print("=== End Configuration Debug ===")


def debug_configuration_legacy() -> None:
    """Legacy debug function to print current configuration from Django settings."""
    config = get_rail_django_graphql_settings_legacy()
    print("=== Legacy rail_django_graphql Configuration Debug ===")
    print(f"Full legacy config: {config}")
    if "MUTATION_SETTINGS" in config:
        mutation_settings = config["MUTATION_SETTINGS"]
        print(f"MUTATION_SETTINGS found: {mutation_settings}")
    else:
        print("MUTATION_SETTINGS not found in legacy configuration")
    print("=== End Legacy Configuration Debug ===")


def validate_configuration_legacy() -> bool:
    """
    Legacy wrapper to validate configuration using legacy schema.

    Returns:
        True if legacy configuration is valid, False otherwise.
    """
    try:
        config = get_rail_django_graphql_settings_legacy()
        validate_configuration_dict(config)
        return True
    except Exception as e:
        logger.error(f"Legacy configuration validation failed: {e}")
        return False
