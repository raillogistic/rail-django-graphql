"""
Configuration loader for Django GraphQL Auto-Generation.

This module provides utilities to load configuration from Django settings
and apply them to the various settings classes.
"""

from typing import Dict, Any, Optional
from django.conf import settings
from .settings import MutationGeneratorSettings, TypeGeneratorSettings, SchemaSettings


class ConfigLoader:
    """
    Configuration loader class for Django GraphQL Auto-Generation.

    This class provides methods to load and validate configuration from Django settings.
    """

    @staticmethod
    def get_rail_django_graphql_settings() -> Dict[str, Any]:
        """
        Get rail_django_graphql settings from Django settings.

        Returns:
            Dictionary containing the configuration, or empty dict if not found.
        """
        return get_rail_django_graphql_settings()

    @staticmethod
    def load_mutation_settings() -> MutationGeneratorSettings:
        """
        Load MutationGeneratorSettings from Django settings.

        Returns:
            MutationGeneratorSettings instance with configuration from Django settings.
        """
        return load_mutation_settings()

    @staticmethod
    def load_type_settings() -> TypeGeneratorSettings:
        """
        Load TypeGeneratorSettings from Django settings.

        Returns:
            TypeGeneratorSettings instance with configuration from Django settings.
        """
        return load_type_settings()

    @staticmethod
    def load_schema_settings() -> SchemaSettings:
        """
        Load SchemaSettings from Django settings.

        Returns:
            SchemaSettings instance with configuration from Django settings.
        """
        return load_schema_settings()

    @staticmethod
    def validate_configuration() -> bool:
        """
        Validate the rail_django_graphql configuration.

        Returns:
            True if configuration is valid, False otherwise.
        """
        return validate_configuration()

    @staticmethod
    def debug_configuration() -> None:
        """
        Print debug information about the current configuration.
        """
        debug_configuration()


def get_rail_django_graphql_settings() -> Dict[str, Any]:
    """
    Get rail_django_graphql settings from Django settings.

    Returns:
        Dictionary containing the configuration, or empty dict if not found.
    """
    return getattr(settings, "rail_django_graphql", {})


def load_mutation_settings() -> MutationGeneratorSettings:
    """
    Load MutationGeneratorSettings from Django settings.

    Returns:
        MutationGeneratorSettings instance with configuration from Django settings.
    """
    config = get_rail_django_graphql_settings()
    mutation_config = config.get("MUTATION_SETTINGS", {})

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


def load_type_settings() -> TypeGeneratorSettings:
    """
    Load TypeGeneratorSettings from Django settings.

    Returns:
        TypeGeneratorSettings instance with configuration from Django settings.
    """
    config = get_rail_django_graphql_settings()
    type_config = config.get("TYPE_SETTINGS", {})

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


def load_schema_settings() -> SchemaSettings:
    """
    Load SchemaSettings from Django settings.

    Returns:
        SchemaSettings instance with configuration from Django settings.
    """
    config = get_rail_django_graphql_settings()

    # Create settings instance with loaded configuration
    schema_settings = SchemaSettings(
        auto_generate_schema=config.get("AUTO_GENERATE_SCHEMA", True),
        auto_refresh_on_model_change=config.get("AUTO_REFRESH_ON_MODEL_CHANGE", True),
        schema_output_dir=config.get("SCHEMA_OUTPUT_DIR", "generated_schema/"),
        apps_to_include=config.get("APPS_TO_INCLUDE", []),
        apps_to_exclude=config.get(
            "APPS_TO_EXCLUDE", ["admin", "auth", "contenttypes"]
        ),
        models_to_exclude=config.get("MODELS_TO_EXCLUDE", []),
        enable_mutations=config.get("ENABLE_MUTATIONS", True),
        enable_subscriptions=config.get("ENABLE_SUBSCRIPTIONS", False),
        pagination_size=config.get("PAGINATION_SIZE", 20),
        max_query_depth=config.get("MAX_QUERY_DEPTH", 10),
        enable_filters=config.get("ENABLE_FILTERS", True),
        enable_nested_operations=config.get("ENABLE_NESTED_OPERATIONS", True),
        enable_file_uploads=config.get("ENABLE_FILE_UPLOADS", True),
        enable_custom_scalars=config.get("ENABLE_CUSTOM_SCALARS", True),
        enable_inheritance=config.get("ENABLE_INHERITANCE", True),
    )

    return schema_settings


def validate_configuration(config: dict) -> dict:
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


def debug_configuration() -> None:
    """
    Print debug information about the current configuration.
    """
    config = get_rail_django_graphql_settings()
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