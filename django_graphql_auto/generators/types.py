"""
Type Generation System for Django GraphQL Auto-Generation

This module provides the TypeGenerator class, which is responsible for converting
Django model fields and relationships into GraphQL types.
"""

from typing import Any, Dict, List, Optional, Type, Union

import graphene
from django.db import models
from django.db.models.fields import Field
from django.db.models.fields.related import (
    ForeignKey,
    ManyToManyField,
    OneToOneField
)
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.utils import DJANGO_FILTER_INSTALLED

if DJANGO_FILTER_INSTALLED:
    from django_filters import CharFilter

from ..core.settings import TypeGeneratorSettings
from .introspector import ModelIntrospector, FieldInfo

class TypeGenerator:
    """
    Generates GraphQL types from Django models, including object types,
    input types, and filter types.
    """

    # Mapping of Django field types to GraphQL scalar types
    FIELD_TYPE_MAP = {
        models.AutoField: graphene.ID,
        models.BigAutoField: graphene.ID,
        models.BigIntegerField: graphene.Int,
        models.BooleanField: graphene.Boolean,
        models.CharField: graphene.String,
        models.DateField: graphene.Date,
        models.DateTimeField: graphene.DateTime,
        models.DecimalField: graphene.Decimal,
        models.EmailField: graphene.String,
        models.FileField: graphene.String,
        models.FloatField: graphene.Float,
        models.ImageField: graphene.String,
        models.IntegerField: graphene.Int,
        models.JSONField: graphene.JSONString,
        models.PositiveIntegerField: graphene.Int,
        models.PositiveSmallIntegerField: graphene.Int,
        models.SlugField: graphene.String,
        models.SmallIntegerField: graphene.Int,
        models.TextField: graphene.String,
        models.TimeField: graphene.Time,
        models.URLField: graphene.String,
        models.UUIDField: graphene.UUID,
    }

    def __init__(self, settings: Optional[TypeGeneratorSettings] = None):
        self.settings = settings or TypeGeneratorSettings()
        self._type_registry: Dict[Type[models.Model], Type[DjangoObjectType]] = {}
        self._input_type_registry: Dict[Type[models.Model], Type[graphene.InputObjectType]] = {}
        self._filter_type_registry: Dict[Type[models.Model], Type] = {}

    def _get_excluded_fields(self, model: Type[models.Model]) -> List[str]:
        """Get excluded fields for a specific model."""
        model_name = model.__name__
        excluded = set()
        
        # Check both exclude_fields and excluded_fields (alias)
        excluded.update(self.settings.exclude_fields.get(model_name, []))
        excluded.update(self.settings.excluded_fields.get(model_name, []))
        
        return list(excluded)

    def _get_included_fields(self, model: Type[models.Model]) -> Optional[List[str]]:
        """Get included fields for a specific model."""
        if self.settings.include_fields is None:
            return None
        return self.settings.include_fields.get(model.__name__, None)

    def _should_field_be_required_for_create(self, field_info: 'FieldInfo') -> bool:
        """
        Determine if a field should be required for create mutations based on:
        - auto_now and auto_now_add fields are not required
        - fields with defaults are not required  
        - only blank=False fields are required
        - id fields are not required for create
        """
        # auto_now and auto_now_add fields are automatically set
        if field_info.has_auto_now or field_info.has_auto_now_add:
            return False
            
        # Fields with defaults don't need to be provided
        if field_info.has_default:
            return False
            
        # Only require fields that have blank=False
        return not field_info.blank
    def _should_field_be_required_for_update(self, field_name: str, field_info: Any) -> bool:
        """
        Determine if a field should be required for update mutations.
        Only id is required for updates.
        """
        return field_name == 'id'

    def _should_include_field(self, model: Type[models.Model], field_name: str) -> bool:
        """Determine if a field should be included in the schema."""
        excluded_fields = self._get_excluded_fields(model)
        if field_name in excluded_fields:
            return False

        included_fields = self._get_included_fields(model)
        if included_fields is not None:
            return field_name in included_fields

        return True

    def generate_object_type(self, model: Type[models.Model]) -> Type[DjangoObjectType]:
        """
        Generates a GraphQL object type for a Django model.
        Handles relationships and custom field mappings.
        """
        if model in self._type_registry:
            return self._type_registry[model]

        introspector = ModelIntrospector(model)
        fields = introspector.get_model_fields()
        relationships = introspector.get_model_relationships()

        # Get excluded fields for this model
        exclude_fields = self._get_excluded_fields(model)
        
        # Create the Meta class for the DjangoObjectType
        meta_attrs = {
            'model': model,
            'exclude_fields': exclude_fields,
            'interfaces': (graphene.relay.Node,) if self.settings.generate_filters else (),
        }
        meta_class = type('Meta', (), meta_attrs)

        # Create the object type class
        class_name = f"{model.__name__}Type"
        type_attrs = {
            'Meta': meta_class,
            '__doc__': f"GraphQL type for the {model.__name__} model."
        }

        # Add custom field resolvers
        for field_name, field_info in fields.items():
            if not self._should_include_field(model, field_name):
                continue
            resolver_name = f'resolve_{field_name}'
            if hasattr(self, resolver_name):
                type_attrs[resolver_name] = getattr(self, resolver_name)

        # Create the type class
        model_type = type(
            class_name,
            (DjangoObjectType,),
            type_attrs
        )

        self._type_registry[model] = model_type
        return model_type

    def generate_input_type(self, model: Type[models.Model], partial: bool = False, 
                           mutation_type: str = 'create') -> Type[graphene.InputObjectType]:
        """
        Generates a GraphQL input type for mutations.
        Handles nested inputs and validation.
        
        Args:
            model: The Django model to generate input type for
            partial: Whether this is a partial input (for updates)
            mutation_type: Type of mutation ('create' or 'update') to determine field requirements
        """
        # Check if we already have this input type to prevent infinite recursion
        cache_key = (model, partial, mutation_type)
        if model in self._input_type_registry:
            return self._input_type_registry[model]

        introspector = ModelIntrospector(model)
        fields = introspector.get_model_fields()
        relationships = introspector.get_model_relationships()

        # Create input fields
        input_fields = {}
        for field_name, field_info in fields.items():
            if not self._should_include_field(model, field_name):
                continue

            # Skip id field for create mutations
            if mutation_type == 'create' and field_name == 'id':
                continue

            field_type = self._get_input_field_type(field_info.field_type)
            if field_type:
                # Determine if field should be required based on mutation type
                if mutation_type == 'create':
                    is_required = self._should_field_be_required_for_create(field_info) and not partial
                else:  # update
                    is_required = self._should_field_be_required_for_update(field_name, field_info) and not partial
                
                input_fields[field_name] = field_type(
                    required=is_required,
                    description=field_info.help_text
                )

        # Add relationship fields (simplified to avoid recursion)
        for field_name, rel_info in relationships.items():
            if not self._should_include_field(model, field_name):
                continue

            # Use ID references instead of nested input types to avoid recursion
            if rel_info.relationship_type in ('ForeignKey', 'OneToOneField'):
                input_fields[field_name] = graphene.ID(required=False)
            elif rel_info.relationship_type == 'ManyToManyField':
                input_fields[field_name] = graphene.List(graphene.ID, required=False)

        # Create the input type class
        class_name = f"{model.__name__}Input"
        input_type = type(
            class_name,
            (graphene.InputObjectType,),
            {
                '__doc__': f"Input type for creating/updating {model.__name__} instances.",
                **input_fields
            }
        )

        self._input_type_registry[model] = input_type
        return input_type

    def generate_filter_type(self, model: Type[models.Model]) -> Type:
        """
        Generates a filter type for the model if Django-filter is installed.
        Configures available filter operations based on field types.
        """
        if not DJANGO_FILTER_INSTALLED or not self.settings.generate_filters:
            return None

        if model in self._filter_type_registry:
            return self._filter_type_registry[model]

        from django_filters import FilterSet

        introspector = ModelIntrospector(model)
        fields = introspector.get_model_fields()

        # Define filter fields
        filter_fields = {}
        for field_name, field_info in fields.items():
            if not self._should_include_field(model, field_name):
                continue

            filter_type = self._get_filter_field_type(field_info.field_type)
            if filter_type:
                filter_fields[field_name] = filter_type

        # Create the filter set class
        class_name = f"{model.__name__}Filter"
        
        # Add filter overrides for file fields
        filter_overrides = {
            models.FileField: {
                'filter_class': CharFilter,
                'extra': lambda f: {'lookup_expr': 'exact'},
            },
            models.ImageField: {
                'filter_class': CharFilter, 
                'extra': lambda f: {'lookup_expr': 'exact'},
            },
        }
        
        meta_class = type('Meta', (), {
            'model': model,
            'fields': filter_fields,
            'filter_overrides': filter_overrides
        })

        filter_class = type(
            class_name,
            (FilterSet,),
            {
                'Meta': meta_class,
                '__doc__': f"Filter set for {model.__name__} queries."
            }
        )

        self._filter_type_registry[model] = filter_class
        return filter_class

    def _get_input_field_type(self, django_field_type: Type[Field]) -> Optional[Type[graphene.Scalar]]:
        """Maps Django field types to GraphQL input field types."""
        return self.FIELD_TYPE_MAP.get(django_field_type)

    def _get_filter_field_type(self, django_field_type: Type[Field]) -> List[str]:
        """Determines available filter operations for a field type."""
        base_filters = ['exact', 'in', 'isnull']
        text_filters = ['contains', 'icontains', 'startswith', 'istartswith', 'endswith', 'iendswith']
        number_filters = ['gt', 'gte', 'lt', 'lte', 'range']
        
        if issubclass(django_field_type, (models.CharField, models.TextField)):
            return base_filters + text_filters
        elif issubclass(django_field_type, (models.IntegerField, models.FloatField, models.DecimalField)):
            return base_filters + number_filters
        elif issubclass(django_field_type, (models.DateField, models.DateTimeField)):
            return base_filters + number_filters + ['year', 'month', 'day']
        else:
            return base_filters

    def _get_filterable_fields(self, model: Type[models.Model]) -> Dict[str, List[str]]:
        """
        Determines which fields should be filterable and what operations are available.
        """
        introspector = ModelIntrospector(model)
        fields = introspector.get_model_fields()
        
        filterable_fields = {}
        for field_name, field_info in fields.items():
            if self._should_include_field(model, field_name):
                filter_ops = self._get_filter_field_type(field_info.field_type)
                if filter_ops:
                    filterable_fields[field_name] = filter_ops
                    
        return filterable_fields

    def handle_custom_fields(self, field: Field) -> graphene.Scalar:
        """
        Handles custom field types by attempting to map them to appropriate GraphQL types.
        Falls back to String if no specific mapping is found.
        """
        # Check if there's a custom mapping defined in settings
        if self.settings.custom_field_mappings:
            field_type = type(field)
            if field_type in self.settings.custom_field_mappings:
                return self.settings.custom_field_mappings[field_type]

        # Default to String for unknown field types
        return graphene.String