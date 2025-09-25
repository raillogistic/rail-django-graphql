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

from ..core.settings import TypeGeneratorSettings, MutationGeneratorSettings
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

    def __init__(self, settings: Optional[TypeGeneratorSettings] = None, mutation_settings: Optional[MutationGeneratorSettings] = None):
        self.settings = settings or TypeGeneratorSettings()
        self.mutation_settings = mutation_settings or MutationGeneratorSettings()
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

    def _should_field_be_required_for_create(self, field_info: 'FieldInfo', field_name: str = None) -> bool:

        """
        Determine if a field should be required for create mutations based on:
        - auto_now and auto_now_add fields are not required (automatically set)
        - fields with defaults are not required (Django will use the default)
        - fields with blank=True are not required (can be empty)
        - fields with blank=False AND no default ARE required
        - id/primary key fields are not required for create (auto-generated)
        """
        # Primary key fields (id, pk) are not required for create
        if field_name and field_name in ('id', 'pk'):
            return False
            
        # auto_now and auto_now_add fields are automatically set
        if field_info.has_auto_now or field_info.has_auto_now_add:
            return False
            
        # Fields with defaults don't need to be provided
        if field_info.has_default:
            return False
            
        # Fields with blank=True can be left empty, so not required
        if field_info.blank:
            return False
            
        # Fields with blank=False (default) and no default value are required
        return True
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

        # Add pk field that resolves to the model's primary key
        type_attrs['pk'] = graphene.ID(description="Primary key of the model")
        type_attrs['resolve_pk'] = lambda self, info: getattr(self, self._meta.pk.name)

        # Add custom field resolvers
        for field_name, field_info in fields.items():
            if not self._should_include_field(model, field_name):
                continue
            resolver_name = f'resolve_{field_name}'
            if hasattr(self, resolver_name):
                type_attrs[resolver_name] = getattr(self, resolver_name)

        # Add custom resolvers for reverse relationships to return direct model lists
        # instead of relay connections
        for field in model._meta.get_fields():
            if hasattr(field, 'related_name') and field.related_name:
                related_name = field.related_name
                if not self._should_include_field(model, related_name):
                    continue
                
                # Get the related model
                related_model = field.related_model
                
                # Use proper lazy type resolution to avoid recursion
                # Create a closure that captures the related_model
                def make_lazy_type(model_ref):
                    def lazy_type():
                        # Check if type already exists to avoid infinite recursion
                        if model_ref in self._type_registry:
                            return self._type_registry[model_ref]
                        return self.generate_object_type(model_ref)
                    return lazy_type
                
                # Add the field as a direct list with proper lazy type resolution
                type_attrs[related_name] = graphene.List(
                    make_lazy_type(related_model),
                    description=f"Related {related_model.__name__} objects"
                )
                
                # Add resolver that returns direct queryset
                def make_resolver(related_name):
                    def resolver(self, info):
                        return getattr(self, related_name).all()
                    return resolver
                
                type_attrs[f'resolve_{related_name}'] = make_resolver(related_name)

        # Create the type class
        model_type = type(
            class_name,
            (DjangoObjectType,),
            type_attrs
        )

        self._type_registry[model] = model_type
        return model_type
    
    def generate_input_type(self, model: Type[models.Model], partial: bool = False, 
                           mutation_type: str = 'create', include_reverse_relations: bool = True) -> Type[graphene.InputObjectType]:
        """
        Generates a GraphQL input type for mutations.
        Handles nested inputs, validation, and reverse relationships.
        
        Args:
            model: The Django model to generate input type for
            partial: Whether this is a partial input (for updates)
            mutation_type: Type of mutation ('create' or 'update') to determine field requirements
            include_reverse_relations: Whether to include reverse relationship fields for nested creation
        """
        # Check if we already have this input type to prevent infinite recursion
        cache_key = (model, partial, mutation_type, include_reverse_relations)
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

            # Get field type, fallback to handle_custom_fields if not in mapping
            field_type = self._get_input_field_type(field_info.field_type)
            if not field_type:
                # Handle custom fields that aren't in FIELD_TYPE_MAP
                field_type = self.handle_custom_fields(field_info.field_type)
            
            # Determine if field should be required based on mutation type
            if mutation_type == 'create':
                is_required = self._should_field_be_required_for_create(field_info, field_name) and not partial
            else:  # update
                is_required = self._should_field_be_required_for_update(field_name, field_info) and not partial
            
            input_fields[field_name] = field_type(
                required=is_required,
                description=field_info.help_text
            )

        # Add forward relationship fields (ForeignKey, OneToOne, ManyToMany)
        for field_name, rel_info in relationships.items():
            if not self._should_include_field(model, field_name):
                continue

            # Get the actual Django field to check its requirements
            django_field = model._meta.get_field(field_name)
            
            # Create a FieldInfo object for the relationship field to check requirements
            from .introspector import FieldInfo
            rel_field_info = FieldInfo(
                field_type=type(django_field),
                is_required=not django_field.null,
                default_value=django_field.default if django_field.default is not models.NOT_PROVIDED else None,
                help_text=str(django_field.help_text),
                has_auto_now=getattr(django_field, 'auto_now', False),
                has_auto_now_add=getattr(django_field, 'auto_now_add', False),
                blank=getattr(django_field, 'blank', False),
                has_default=django_field.default is not models.NOT_PROVIDED
            )
            
            # Apply field requirement logic to relationship fields
            # For ManyToMany fields, use blank attribute instead of null
            if rel_info.relationship_type == 'ManyToManyField':
                is_required = not django_field.blank
            else:
                is_required = self._should_field_be_required_for_create(rel_field_info, field_name) if mutation_type == 'create' else self._should_field_be_required_for_update(field_name, rel_field_info)

            # Support both ID references and nested object creation
            if rel_info.relationship_type in ('ForeignKey', 'OneToOneField'):
                # For ForeignKey/OneToOne, use ID field instead of Union to avoid GraphQL complexity
                # Users can provide either the ID directly or use nested mutations separately
                if is_required:
                    input_fields[field_name] = graphene.NonNull(graphene.ID)
                else:
                    input_fields[field_name] = graphene.ID()
            elif rel_info.relationship_type == 'ManyToManyField':
                # For ManyToMany, use List of IDs
                list_type = graphene.List(graphene.ID)
                if is_required:
                    input_fields[field_name] = graphene.NonNull(list_type)
                else:
                    input_fields[field_name] = list_type

        # Add reverse relationship fields for nested creation (e.g., comments for Post)
        if include_reverse_relations and mutation_type == 'create' and self._should_include_nested_relations(model):
            reverse_relations = self._get_reverse_relations(model)
            for field_name, related_model in reverse_relations.items():
                if not self._should_include_field(model, field_name):
                    continue
                
                # Check if this specific field should be nested
                if not self._should_include_nested_field(model, field_name):
                    continue
                
                # Create nested input type for reverse relations
                nested_input_type = self._get_or_create_nested_input_type(related_model, 'create', exclude_parent_field=model)
                input_fields[field_name] = graphene.List(nested_input_type)

        # Create the input type class
        class_name = f"{model.__name__}Input"
        input_type = type(
            class_name,
            (graphene.InputObjectType,),
            {
                '__doc__': f"Input type for creating/updating {model.__name__} instances with nested relationships.",
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

    def handle_custom_fields(self, field: Field) -> Type[graphene.Scalar]:
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

    def _get_reverse_relations(self, model: Type[models.Model]) -> Dict[str, Type[models.Model]]:
        """
        Get reverse relationships for a model (e.g., comments for Post).
        
        Returns:
            Dict mapping field names to related models
        """
        reverse_relations = {}
        
        # For modern Django versions, use related_objects
        if hasattr(model._meta, 'related_objects'):
            for rel in model._meta.related_objects:
                # Get the accessor name (e.g., 'comments' for Comment.post -> Post)
                accessor_name = rel.get_accessor_name()
                
                # Skip if accessor name is in excluded fields
                if not self._should_include_field(model, accessor_name):
                    continue
                    
                reverse_relations[accessor_name] = rel.related_model
        else:
            # Fallback for older Django versions
            try:
                for rel in model._meta.get_all_related_objects():
                    if hasattr(rel, 'get_accessor_name'):
                        accessor_name = rel.get_accessor_name()
                    else:
                        accessor_name = rel.name
                    
                    if self._should_include_field(model, accessor_name):
                        reverse_relations[accessor_name] = rel.related_model
            except AttributeError:
                # If get_all_related_objects doesn't exist, skip reverse relations
                pass
        
        return reverse_relations

    def _get_or_create_nested_input_type(
        self, 
        model: Type[models.Model], 
        mutation_type: str = 'create',
        exclude_parent_field: Optional[Type[models.Model]] = None
    ) -> Type[graphene.InputObjectType]:
        """
        Get or create a nested input type for a model, avoiding circular references.
        
        Args:
            model: The model to create input type for
            mutation_type: Type of mutation ('create' or 'update')
            exclude_parent_field: Parent model to exclude from nested input to prevent circular refs
            
        Returns:
            GraphQL input type for the model
        """
        # Create a simplified input type to avoid infinite recursion
        cache_key = f"{model.__name__}Nested{mutation_type.title()}Input"
        
        if cache_key in self._input_type_registry:
            return self._input_type_registry[cache_key]
        
        introspector = ModelIntrospector(model)
        fields = introspector.get_model_fields()
        relationships = introspector.get_model_relationships()
        
        input_fields = {}
        
        # Add regular fields
        for field_name, field_info in fields.items():
            if not self._should_include_field(model, field_name):
                continue
                
            # Skip id field for create mutations
            if mutation_type == 'create' and field_name == 'id':
                continue
                
            field_type = self._get_input_field_type(field_info.field_type)
            if not field_type:
                field_type = self.handle_custom_fields(field_info.field_type)
            
            # For nested inputs, make most fields optional to allow partial data
            is_required = False
            if mutation_type == 'create':
                is_required = self._should_field_be_required_for_create(field_info, field_name)
            
            input_fields[field_name] = field_type(
                required=is_required,
                description=field_info.help_text
            )
        
        # Add only essential relationship fields (avoid deep nesting)
        for field_name, rel_info in relationships.items():
            if not self._should_include_field(model, field_name):
                continue
                
            # Skip the parent field to prevent circular references
            if exclude_parent_field and rel_info.related_model == exclude_parent_field:
                continue
            
            # For nested inputs, use only ID references for relationships
            if rel_info.relationship_type in ('ForeignKey', 'OneToOneField'):
                input_fields[field_name] = graphene.ID(required=False)
            elif rel_info.relationship_type == 'ManyToManyField':
                input_fields[field_name] = graphene.List(graphene.ID)
        
        # Create the nested input type
        nested_input_type = type(
            cache_key,
            (graphene.InputObjectType,),
            {
                '__doc__': f"Nested input type for {model.__name__} in {mutation_type} operations.",
                **input_fields
            }
        )
        
        self._input_type_registry[cache_key] = nested_input_type
        return nested_input_type

    def _should_include_nested_relations(self, model: Type[models.Model]) -> bool:
        """
        Check if nested relations should be included for this model.
        
        Args:
            model: The Django model to check
            
        Returns:
            bool: True if nested relations should be included
        """
        model_name = model.__name__
        
        # Check global setting first
        if not self.mutation_settings.enable_nested_relations:
            return False
        
        # Check per-model configuration
        if model_name in self.mutation_settings.nested_relations_config:
            return self.mutation_settings.nested_relations_config[model_name]
        
        # Default to enabled if no specific configuration
        return True

    def _should_include_nested_field(self, model: Type[models.Model], field_name: str) -> bool:
        """
        Check if a specific nested field should be included for this model.
        
        Args:
            model: The Django model
            field_name: The field name to check
            
        Returns:
            bool: True if the nested field should be included
        """
        model_name = model.__name__
        
        # Check per-field configuration
        if model_name in self.mutation_settings.nested_field_config:
            field_config = self.mutation_settings.nested_field_config[model_name]
            if field_name in field_config:
                return field_config[field_name]
        
        # Default to enabled if no specific configuration
        return True