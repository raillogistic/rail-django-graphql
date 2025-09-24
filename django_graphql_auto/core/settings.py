"""
Settings module for Django GraphQL Auto-Generation.

This module defines the configuration classes used to customize the behavior
of the GraphQL schema generation process.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type, Union

import graphene
from django.db.models import Field


@dataclass
class TypeGeneratorSettings:
    """Settings for controlling GraphQL type generation."""
    
    # Fields to exclude from types, per model
    exclude_fields: Dict[str, List[str]] = field(default_factory=dict)
    excluded_fields: Dict[str, List[str]] = field(default_factory=dict)  # Alias for exclude_fields
    
    # Fields to include in types, per model (if None, include all non-excluded fields)
    include_fields: Optional[Dict[str, List[str]]] = None
    
    # Custom field type mappings
    custom_field_mappings: Dict[Type[Field], Type[graphene.Scalar]] = field(default_factory=dict)
    
    # Enable filter generation for types
    generate_filters: bool = True
    
    # Enable filtering support (alias for generate_filters)
    enable_filtering: bool = True
    
    # Enable auto-camelcase for field names
    auto_camelcase: bool = False
    
    # Enable field descriptions
    generate_descriptions: bool = True


@dataclass
class QueryGeneratorSettings:
    """Settings for controlling GraphQL query generation."""
    
    # Enable filtering support
    generate_filters: bool = True
    
    # Enable ordering support
    generate_ordering: bool = True
    
    # Enable pagination support
    generate_pagination: bool = True
    
    # Enable pagination support (alias for generate_pagination)
    enable_pagination: bool = True
    
    # Enable ordering support (alias for generate_ordering)
    enable_ordering: bool = True
    
    # Enable Relay-style pagination
    use_relay: bool = False
    
    # Default page size for paginated queries
    default_page_size: int = 20
    
    # Maximum allowed page size
    max_page_size: int = 100
    
    # Additional fields to use for lookups (e.g., slug, uuid)
    additional_lookup_fields: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class MutationGeneratorSettings:
    """Settings for controlling GraphQL mutation generation."""
    
    # Enable create mutations
    generate_create: bool = True
    
    # Enable update mutations
    generate_update: bool = True
    
    # Enable delete mutations
    generate_delete: bool = True
    
    # Enable bulk mutations
    generate_bulk: bool = False
    
    # Enable create mutations (alias for generate_create)
    enable_create: bool = True
    
    # Enable update mutations (alias for generate_update)
    enable_update: bool = True
    
    # Enable delete mutations (alias for generate_delete)
    enable_delete: bool = True
    
    # Enable bulk operations
    enable_bulk_operations: bool = False
    
    # Enable method mutations
    enable_method_mutations: bool = False
    
    # Maximum number of items in bulk operations
    bulk_batch_size: int = 100
    
    # Fields required for update operations
    required_update_fields: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class SchemaSettings:
    """Settings for controlling overall schema behavior."""
    
    # Apps to exclude from schema generation
    excluded_apps: List[str] = field(default_factory=list)
    
    # Models to exclude from schema generation
    excluded_models: List[str] = field(default_factory=list)
    
    # Enable schema introspection
    enable_introspection: bool = True
    
    # Enable GraphiQL interface
    enable_graphiql: bool = True
    
    # Auto-refresh schema when models change
    auto_refresh_on_model_change: bool = True
    
    # Enable pagination support
    enable_pagination: bool = True
    
    # Enable auto-camelcase for GraphQL schema
    auto_camelcase: bool = False


class GraphQLAutoConfig:
    """
    Configuration class for managing model-specific GraphQL auto-generation settings.
    """
    
    def __init__(
        self,
        type_settings: Optional[TypeGeneratorSettings] = None,
        query_settings: Optional[QueryGeneratorSettings] = None,
        mutation_settings: Optional[MutationGeneratorSettings] = None,
        schema_settings: Optional[SchemaSettings] = None
    ):
        self.type_settings = type_settings or TypeGeneratorSettings()
        self.query_settings = query_settings or QueryGeneratorSettings()
        self.mutation_settings = mutation_settings or MutationGeneratorSettings()
        self.schema_settings = schema_settings or SchemaSettings()

    def should_include_model(self, model_name: str) -> bool:
        """
        Determine if a model should be included in the schema.
        
        Args:
            model_name: The name of the model to check
            
        Returns:
            bool: True if the model should be included, False otherwise
        """
        return (
            model_name not in self.schema_settings.excluded_models and
            model_name not in self.schema_settings.excluded_apps
        )

    def should_include_field(self, model_name: str, field_name: str) -> bool:
        """
        Determine if a field should be included in the schema.
        
        Args:
            model_name: The name of the model containing the field
            field_name: The name of the field to check
            
        Returns:
            bool: True if the field should be included, False otherwise
        """
        # Check excluded fields
        excluded = set()
        excluded.update(self.type_settings.exclude_fields.get(model_name, []))
        excluded.update(self.type_settings.excluded_fields.get(model_name, []))
        if field_name in excluded:
            return False

        # Check included fields
        if self.type_settings.include_fields is not None:
            included = self.type_settings.include_fields.get(model_name, [])
            return field_name in included

        return True

    def get_additional_lookup_fields(self, model_name: str) -> List[str]:
        """
        Get additional lookup fields for a model.
        
        Args:
            model_name: The name of the model
            
        Returns:
            List[str]: List of additional lookup field names
        """
        return self.query_settings.additional_lookup_fields.get(model_name, [])