"""
Model Introspection System for Django GraphQL Auto-Generation

This module provides the ModelIntrospector class, which is responsible for analyzing
Django models and extracting metadata required for generating GraphQL schemas.
"""

import inspect
from typing import Any, Dict, List, Type, Union, get_origin, get_args

from django.db import models
from django.db.models.fields.related import (ForeignKey, ManyToManyField,
                                              OneToOneField)
from django.utils.functional import cached_property

# Data structures for introspection results

class FieldInfo:
    """Stores metadata about a Django model field."""
    def __init__(self, field_type: Any, is_required: bool, default_value: Any, help_text: str, 
                 has_auto_now: bool = False, has_auto_now_add: bool = False, blank: bool = True, 
                 has_default: bool = False):
        self.field_type = field_type
        self.is_required = is_required
        self.default_value = default_value
        self.help_text = help_text
        self.has_auto_now = has_auto_now
        self.has_auto_now_add = has_auto_now_add
        self.blank = blank
        self.has_default = has_default

class RelationshipInfo:
    """Stores metadata about a model relationship."""
    def __init__(self, related_model: Type[models.Model], relationship_type: str, to_field: str, from_field: str):
        self.related_model = related_model
        self.relationship_type = relationship_type
        self.to_field = to_field
        self.from_field = from_field

class MethodInfo:
    """Stores metadata about a model method."""
    def __init__(self, arguments: Dict[str, Any], return_type: Any, is_async: bool):
        self.arguments = arguments
        self.return_type = return_type
        self.is_async = is_async

class PropertyInfo:
    """Stores metadata about a model property."""
    def __init__(self, return_type: Any):
        self.return_type = return_type

class InheritanceInfo:
    """Stores metadata about model inheritance."""
    def __init__(self, base_classes: List[Type[models.Model]], is_abstract: bool):
        self.base_classes = base_classes
        self.is_abstract = is_abstract

class ModelIntrospector:
    """
    Analyzes Django models to extract metadata for GraphQL schema generation.
    Caches results to avoid redundant introspection.
    """
    def __init__(self, model: Type[models.Model]):
        self.model = model
        self._meta = getattr(model, '_meta', None)

    @cached_property
    def fields(self) -> Dict[str, FieldInfo]:
        """Extracts model fields with their types and constraints."""
        if not self._meta:
            return {}
        
        field_info = {}
        for field in self._meta.get_fields():
            # Skip relationship fields and reverse relationship fields
            if isinstance(field, (ForeignKey, OneToOneField, ManyToManyField)):
                continue
            
            # Skip reverse relationship fields (they don't have null or default attributes)
            if not hasattr(field, 'null') or not hasattr(field, 'default'):
                continue
            
            # Check for auto_now and auto_now_add fields
            has_auto_now = getattr(field, 'auto_now', False)
            has_auto_now_add = getattr(field, 'auto_now_add', False)
            
            # Check if field has a default value
            has_default = field.default is not models.NOT_PROVIDED
            
            # Get blank attribute (defaults to False for most fields)
            blank = getattr(field, 'blank', False)
            
            field_info[field.name] = FieldInfo(
                field_type=type(field),
                is_required=not field.null,
                default_value=field.default if has_default else None,
                help_text=str(field.help_text),
                has_auto_now=has_auto_now,
                has_auto_now_add=has_auto_now_add,
                blank=blank,
                has_default=has_default
            )
        return field_info

    @cached_property
    def relationships(self) -> Dict[str, RelationshipInfo]:
        """Identifies model relationships (ForeignKey, ManyToMany, OneToOne)."""
        if not self._meta:
            return {}

        relationship_info = {}
        for field in self._meta.get_fields():
            if isinstance(field, (ForeignKey, OneToOneField, ManyToManyField)):
                relationship_info[field.name] = RelationshipInfo(
                    related_model=field.related_model,
                    relationship_type=type(field).__name__,
                    to_field=field.remote_field.name if field.remote_field else None,
                    from_field=field.name
                )
        return relationship_info

    @cached_property
    def methods(self) -> Dict[str, MethodInfo]:
        """Discovers model methods, their arguments, and return types."""
        method_info = {}
        for name, member in inspect.getmembers(self.model, predicate=inspect.isfunction):
            if name.startswith('_'):
                continue

            sig = inspect.signature(member)
            arguments = {p.name: p.annotation for p in sig.parameters.values() if p.name != 'self'}
            return_type = sig.return_annotation

            method_info[name] = MethodInfo(
                arguments=arguments,
                return_type=return_type,
                is_async=inspect.iscoroutinefunction(member)
            )
        return method_info

    @cached_property
    def properties(self) -> Dict[str, PropertyInfo]:
        """Discovers model properties and their return types."""
        property_info = {}
        for name, member in inspect.getmembers(self.model, predicate=lambda x: isinstance(x, property)):
            if name.startswith('_'):
                continue

            # Infer return type from property's fget method if available
            return_type = Any
            if member.fget:
                sig = inspect.signature(member.fget)
                return_type = sig.return_annotation

            property_info[name] = PropertyInfo(return_type=return_type)
        return property_info

    @cached_property
    def inheritance(self) -> InheritanceInfo:
        """Analyzes the model's inheritance hierarchy."""
        if not self._meta:
            return InheritanceInfo(base_classes=[], is_abstract=False)

        return InheritanceInfo(
            base_classes=[b for b in self.model.__bases__ if isinstance(b, type(models.Model))],
            is_abstract=self._meta.abstract
        )

    def get_model_fields(self) -> Dict[str, FieldInfo]:
        return self.fields

    def get_model_relationships(self) -> Dict[str, RelationshipInfo]:
        return self.relationships

    def get_model_methods(self) -> Dict[str, MethodInfo]:
        return self.methods

    def get_model_properties(self) -> Dict[str, PropertyInfo]:
        return self.properties

    def analyze_inheritance(self) -> InheritanceInfo:
        return self.inheritance

    def get_reverse_relations(self) -> Dict[str, Type[models.Model]]:
        """
        Get reverse relationships for the model (e.g., comments for Post).
        
        Returns:
            Dict mapping field names to related models
        """
        reverse_relations = {}
        
        if not self._meta:
            return reverse_relations
        
        # For modern Django versions, use related_objects
        if hasattr(self._meta, 'related_objects'):
            for rel in self._meta.related_objects:
                # Get the accessor name (e.g., 'comments' for Comment.post -> Post)
                accessor_name = rel.get_accessor_name()
                reverse_relations[accessor_name] = rel.related_model
        else:
            # Fallback for older Django versions
            try:
                for rel in self._meta.get_all_related_objects():
                    if hasattr(rel, 'get_accessor_name'):
                        accessor_name = rel.get_accessor_name()
                    else:
                        accessor_name = rel.name
                    
                    reverse_relations[accessor_name] = rel.related_model
            except AttributeError:
                # If get_all_related_objects doesn't exist, skip reverse relations
                pass
        
        return reverse_relations