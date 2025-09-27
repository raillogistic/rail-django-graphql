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
    def get_django_graphql_auto_settings() -> Dict[str, Any]:
        """
        Get DJANGO_GRAPHQL_AUTO settings from Django settings.
        
        Returns:
            Dictionary containing the configuration, or empty dict if not found.
        """
        return get_django_graphql_auto_settings()
    
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
        Validate the DJANGO_GRAPHQL_AUTO configuration.
        
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


def get_django_graphql_auto_settings() -> Dict[str, Any]:
    """
    Get DJANGO_GRAPHQL_AUTO settings from Django settings.
    
    Returns:
        Dictionary containing the configuration, or empty dict if not found.
    """
    return getattr(settings, 'DJANGO_GRAPHQL_AUTO', {})


def load_mutation_settings() -> MutationGeneratorSettings:
    """
    Load MutationGeneratorSettings from Django settings.
    
    Returns:
        MutationGeneratorSettings instance with configuration from Django settings.
    """
    config = get_django_graphql_auto_settings()
    mutation_config = config.get('MUTATION_SETTINGS', {})
    
    # Create settings instance with loaded configuration
    mutation_settings = MutationGeneratorSettings(
        enable_nested_relations=mutation_config.get('enable_nested_relations', False),
        nested_relations_config=mutation_config.get('nested_relations_config', {}),
        nested_field_config=mutation_config.get('nested_field_config', {}),
        # Keep other default values
        generate_create=mutation_config.get('generate_create', True),
        generate_update=mutation_config.get('generate_update', True),
        generate_delete=mutation_config.get('generate_delete', True),
        generate_bulk=mutation_config.get('generate_bulk', False),
        enable_create=mutation_config.get('enable_create', True),
        enable_update=mutation_config.get('enable_update', True),
        enable_delete=mutation_config.get('enable_delete', True),
        enable_bulk_operations=mutation_config.get('enable_bulk_operations', False),
        enable_method_mutations=mutation_config.get('enable_method_mutations', False),
        bulk_batch_size=mutation_config.get('bulk_batch_size', 100),
        required_update_fields=mutation_config.get('required_update_fields', {}),
    )
    
    return mutation_settings


def load_type_settings() -> TypeGeneratorSettings:
    """
    Load TypeGeneratorSettings from Django settings.
    
    Returns:
        TypeGeneratorSettings instance with configuration from Django settings.
    """
    config = get_django_graphql_auto_settings()
    type_config = config.get('TYPE_SETTINGS', {})
    
    # Create settings instance with loaded configuration
    type_settings = TypeGeneratorSettings(
        naming_convention=type_config.get('naming_convention', 'snake_case'),
        enable_relationships=type_config.get('enable_relationships', True),
        enable_reverse_relationships=type_config.get('enable_reverse_relationships', True),
        max_relationship_depth=type_config.get('max_relationship_depth', 3),
        enable_custom_scalars=type_config.get('enable_custom_scalars', True),
        custom_scalar_mapping=type_config.get('custom_scalar_mapping', {}),
        field_converters=type_config.get('field_converters', {}),
        exclude_fields=type_config.get('exclude_fields', []),
        include_fields=type_config.get('include_fields', []),
        enable_inheritance=type_config.get('enable_inheritance', True),
    )
    
    return type_settings


def load_schema_settings() -> SchemaSettings:
    """
    Load SchemaSettings from Django settings.
    
    Returns:
        SchemaSettings instance with configuration from Django settings.
    """
    config = get_django_graphql_auto_settings()
    
    # Create settings instance with loaded configuration
    schema_settings = SchemaSettings(
        auto_generate_schema=config.get('AUTO_GENERATE_SCHEMA', True),
        auto_refresh_on_model_change=config.get('AUTO_REFRESH_ON_MODEL_CHANGE', True),
        schema_output_dir=config.get('SCHEMA_OUTPUT_DIR', 'generated_schema/'),
        apps_to_include=config.get('APPS_TO_INCLUDE', []),
        apps_to_exclude=config.get('APPS_TO_EXCLUDE', ['admin', 'auth', 'contenttypes']),
        models_to_exclude=config.get('MODELS_TO_EXCLUDE', []),
        enable_mutations=config.get('ENABLE_MUTATIONS', True),
        enable_subscriptions=config.get('ENABLE_SUBSCRIPTIONS', False),
        pagination_size=config.get('PAGINATION_SIZE', 20),
        max_query_depth=config.get('MAX_QUERY_DEPTH', 10),
        enable_filters=config.get('ENABLE_FILTERS', True),
        enable_nested_operations=config.get('ENABLE_NESTED_OPERATIONS', True),
        enable_file_uploads=config.get('ENABLE_FILE_UPLOADS', True),
        enable_custom_scalars=config.get('ENABLE_CUSTOM_SCALARS', True),
        enable_inheritance=config.get('ENABLE_INHERITANCE', True),
    )
    
    return schema_settings


def validate_configuration() -> bool:
    """
    Validate the DJANGO_GRAPHQL_AUTO configuration.
    
    Returns:
        True if configuration is valid, False otherwise.
    """
    try:
        config = get_django_graphql_auto_settings()
        
        # Check if MUTATION_SETTINGS exists and has valid structure
        if 'MUTATION_SETTINGS' in config:
            mutation_settings = config['MUTATION_SETTINGS']
            
            # Validate nested_relations_config
            if 'nested_relations_config' in mutation_settings:
                nested_config = mutation_settings['nested_relations_config']
                if not isinstance(nested_config, dict):
                    print("Warning: nested_relations_config should be a dictionary")
                    return False
                    
                for model_name, enabled in nested_config.items():
                    if not isinstance(enabled, bool):
                        print(f"Warning: nested_relations_config['{model_name}'] should be a boolean")
                        return False
            
            # Validate nested_field_config
            if 'nested_field_config' in mutation_settings:
                field_config = mutation_settings['nested_field_config']
                if not isinstance(field_config, dict):
                    print("Warning: nested_field_config should be a dictionary")
                    return False
                    
                for model_name, fields in field_config.items():
                    if not isinstance(fields, dict):
                        print(f"Warning: nested_field_config['{model_name}'] should be a dictionary")
                        return False
                        
                    for field_name, enabled in fields.items():
                        if not isinstance(enabled, bool):
                            print(f"Warning: nested_field_config['{model_name}']['{field_name}'] should be a boolean")
                            return False
        
        return True
        
    except Exception as e:
        print(f"Configuration validation error: {e}")
        return False


def debug_configuration() -> None:
    """
    Print debug information about the current configuration.
    """
    config = get_django_graphql_auto_settings()
    print("=== DJANGO_GRAPHQL_AUTO Configuration Debug ===")
    print(f"Full config: {config}")
    
    if 'MUTATION_SETTINGS' in config:
        mutation_settings = config['MUTATION_SETTINGS']
        print(f"MUTATION_SETTINGS found: {mutation_settings}")
        
        print(f"enable_nested_relations: {mutation_settings.get('enable_nested_relations', 'NOT SET')}")
        print(f"nested_relations_config: {mutation_settings.get('nested_relations_config', 'NOT SET')}")
        print(f"nested_field_config: {mutation_settings.get('nested_field_config', 'NOT SET')}")
    else:
        print("MUTATION_SETTINGS not found in configuration")
    
    print("=== End Configuration Debug ===")