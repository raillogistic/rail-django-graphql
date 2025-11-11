"""SModel metadata schema for Django GraphQL Auto-Generation.

This module provides comprehensive metadata exposure for Django models to support
rich frontend interfaces including advanced filtering, CRUD operations, and
complex forms with nested fields.
"""

import hashlib
import logging
import threading
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Dict, List, Optional, Type, Union

import graphene
from django.apps import apps
from django.db import models
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver
from graphql import GraphQLError
from rail_django_graphql.plugins import base

from ..conf import get_core_schema_settings
from ..core.settings import SchemaSettings
from ..generators.introspector import ModelIntrospector
# Caching removed: no cache imports

# Remove imports that cause AppRegistryNotReady error
# from ..core.security import AuthorizationManager
# from ..extensions.permissions import PermissionLevel, OperationType

logger = logging.getLogger(__name__)

## Metadata cache configuration removed: caching is not supported.

# Lightweight, targeted cache for model_table metadata only
_table_cache_lock = threading.RLock()
_table_cache: Dict[str, Dict[str, Any]] = {}
_table_cache_stats = {
    "hits": 0,
    "misses": 0,
    "sets": 0,
    "deletes": 0,
    "invalidations": 0,
}


def _get_table_cache_timeout() -> int:
    """
    Purpose: Resolve TTL for model_table metadata cache from Django settings.
    Args: None
    Returns: int: Timeout in seconds; defaults to 600 (10 minutes) if not set
    Raises: None
    Example:
        >>> _get_table_cache_timeout()
        600
    """
    try:
        from django.conf import settings as django_settings

        config = getattr(django_settings, "RAIL_DJANGO_GRAPHQL", {}) or {}
        metadata_cfg = config.get("METADATA", {}) or {}
        timeout_val = int(metadata_cfg.get("table_cache_timeout_seconds", 600))
        return timeout_val if timeout_val > 0 else 600
    except Exception:
        return 600


def _make_table_cache_key(
    schema_name: str,
    app_name: str,
    model_name: str,
    counts: bool,
) -> str:
    """
    Purpose: Build a stable cache key for model_table metadata.
    Args:
        schema_name: str schema identifier
        app_name: str Django app label
        model_name: str Django model name
        counts: bool include reverse relationship counts
    Returns: str: cache key
    Raises: None
    Example:
        >>> _make_table_cache_key('default','app','Model',False)
        'model-table:default:app:Model:counts=0'
    """
    return (
        f"model-table:{schema_name}:{app_name}:{model_name}:counts={1 if counts else 0}"
    )


def cache_metadata(
    timeout: int = None,
    user_specific: bool = True,
    invalidate_on_model_change: bool = True,
):
    """
    Decorator retained for API compatibility. Caching is removed; this is a no-op
    that simply executes the wrapped function.

    Args:
        timeout: Ignored
        user_specific: Ignored
        invalidate_on_model_change: Ignored
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            return func(self, *args, **kwargs)

        return wrapper

    return decorator


def invalidate_metadata_cache(model_name: str = None, app_name: str = None):
    """
    Purpose: Invalidate cached metadata. Currently focuses on model_table cache.
    Args:
        model_name: Optional[str] model name to invalidate
        app_name: Optional[str] app label to scope invalidation
    Returns: None
    Raises: None
    Example:
        >>> invalidate_metadata_cache(model_name="Product", app_name="inventory")
    """
    global _table_cache
    with _table_cache_lock:
        if not _table_cache:
            return
        for schema_name, inner in _table_cache.items():
            keys_to_delete = []
            for k in list(inner.keys()):
                parts = k.split(":")
                # Format: model-table:schema:app:model:counts=X:depth=Y:cf=...
                cache_app = parts[3] if len(parts) > 3 else None
                cache_model = parts[4] if len(parts) > 4 else None
                if model_name or app_name:
                    if (not app_name or app_name == cache_app) and (
                        not model_name or model_name == cache_model
                    ):
                        keys_to_delete.append(k)
                else:
                    keys_to_delete.append(k)
            for k in keys_to_delete:
                inner.pop(k, None)
                _table_cache_stats["deletes"] += 1
        _table_cache_stats["invalidations"] += 1


def invalidate_cache_on_startup() -> None:
    """

    Purpose: Invalidate metadata cache when the Django application starts, controlled by settings.
    Args: None
    Returns: None
    Raises: None
    Example:
        >>> invalidate_cache_on_startup()
    """
    try:
        from django.conf import settings as django_settings

        config = getattr(django_settings, "RAIL_DJANGO_GRAPHQL", {}) or {}
        metadata_config = config.get("METADATA", {}) or {}
        clear_on_start = bool(metadata_config.get("clear_cache_on_start", False))
        debug_only = bool(metadata_config.get("clear_cache_on_start_debug_only", False))
        debug_mode = bool(getattr(django_settings, "DEBUG", False))
        if clear_on_start and (not debug_only or debug_mode):
            invalidate_metadata_cache()
            logger.info("Metadata cache invalidated on application startup")
    except Exception as e:
        logger.debug(f"Skipping startup cache invalidation: {e}")


# Use lazy import to avoid AppRegistryNotReady error
def get_user_model_lazy():
    from django.contrib.auth import get_user_model

    return get_user_model()


@dataclass
class InputFieldMetadata:
    """Metadata for mutation input fields."""

    name: str
    field_type: str
    required: bool
    default_value: Optional[Any] = None
    description: Optional[str] = None
    choices: Optional[List[Dict[str, Any]]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    widget_type: Optional[str] = None
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    related_model: Optional[str] = None
    multiple: bool = False


@dataclass
class MutationMetadata:
    """Metadata for GraphQL mutations."""

    name: str
    description: Optional[str] = None
    input_fields: List[InputFieldMetadata] = field(default_factory=list)
    return_type: Optional[str] = None
    requires_authentication: bool = True
    required_permissions: List[str] = field(default_factory=list)
    mutation_type: str = "custom"  # create, update, delete, custom
    model_name: Optional[str] = None
    form_config: Optional[Dict[str, Any]] = None
    validation_schema: Optional[Dict[str, Any]] = None
    success_message: Optional[str] = None
    error_messages: Optional[Dict[str, str]] = None


# ChoiceType : {"value":str,"label":str}    graphene class
class ChoiceType(graphene.ObjectType):
    value = graphene.String(required=True, description="Choice value")
    label = graphene.String(required=True, description="Choice label")


class FilterOptionType(graphene.ObjectType):
    """GraphQL type for individual filter options within a grouped filter."""

    name = graphene.String(
        required=True, description="Filter option name (e.g., 'slug__iexact')"
    )
    lookup_expr = graphene.String(
        required=True, description="Django lookup expression (e.g., 'iexact')"
    )
    help_text = graphene.String(
        required=True, description="Filter help text in French using field verbose_name"
    )
    filter_type = graphene.String(
        required=True, description="Filter class type (e.g., 'CharFilter')"
    )
    choices = graphene.List(
        ChoiceType,
        description="Available choices for the field (if any, typically for CharField)",
    )


class FilterFieldType(graphene.ObjectType):
    """GraphQL type for grouped filter field metadata."""

    field_name = graphene.String(required=True, description="Target model field name")
    is_nested = graphene.Boolean(
        required=True, description="Whether this is a nested filter"
    )
    related_model = graphene.String(description="Related model name for nested filters")
    is_custom = graphene.Boolean(
        required=True, description="Whether this includes custom filters"
    )
    field_label = graphene.String(
        required=True, description="Human-readable label for the field"
    )

    options = graphene.List(
        FilterOptionType,
        required=True,
        description="List of filter options for this field",
    )

    # Nested filter fields for related lookups (e.g., famille__code)
    nested = graphene.List(
        lambda: FilterFieldType,
        description="Nested filter fields for related model attributes",
    )


class InputFieldMetadataType(graphene.ObjectType):
    """GraphQL type for input field metadata."""

    name = graphene.String(required=True, description="Field name")
    field_type = graphene.String(required=True, description="Field data type")
    required = graphene.Boolean(required=True, description="Whether field is required")
    default_value = graphene.JSONString(description="Default value for the field")
    description = graphene.String(description="Field description")
    choices = graphene.List(
        graphene.JSONString, description="Available choices for the field"
    )
    validation_rules = graphene.JSONString(description="Validation rules as JSON")
    widget_type = graphene.String(description="Recommended UI widget type")
    placeholder = graphene.String(description="Placeholder text for input")
    help_text = graphene.String(description="Help text for the field")
    min_length = graphene.Int(description="Minimum length for string fields")
    max_length = graphene.Int(description="Maximum length for string fields")
    min_value = graphene.Float(description="Minimum value for numeric fields")
    max_value = graphene.Float(description="Maximum value for numeric fields")
    pattern = graphene.String(description="Regex pattern for validation")
    related_model = graphene.String(description="Related model name for foreign keys")
    multiple = graphene.Boolean(
        required=True, description="Whether field accepts multiple values"
    )


class MutationMetadataType(graphene.ObjectType):
    """GraphQL type for mutation metadata."""

    name = graphene.String(required=True, description="Mutation name")
    description = graphene.String(description="Mutation description")
    input_fields = graphene.List(
        InputFieldMetadataType,
        required=True,
        description="Input fields for the mutation",
    )
    return_type = graphene.String(description="Return type of the mutation")
    requires_authentication = graphene.Boolean(
        required=True, description="Whether mutation requires authentication"
    )
    required_permissions = graphene.List(
        graphene.String,
        required=True,
        description="Required permissions to execute mutation",
    )
    mutation_type = graphene.String(
        required=True, description="Type of mutation (create, update, delete, custom)"
    )
    model_name = graphene.String(description="Associated model name")
    form_config = graphene.JSONString(description="Frontend form configuration")
    validation_schema = graphene.JSONString(
        description="Validation schema for the mutation"
    )
    success_message = graphene.String(description="Success message template")
    error_messages = graphene.JSONString(description="Error message templates")


@dataclass
class FieldMetadata:
    """Metadata for a single model field."""

    name: str
    field_type: str
    is_required: bool
    is_nullable: bool
    null: bool
    default_value: Any
    help_text: str
    max_length: Optional[int]
    choices: Optional[List[Dict[str, str]]]
    is_primary_key: bool
    is_foreign_key: bool
    is_unique: bool
    is_indexed: bool
    has_auto_now: bool
    has_auto_now_add: bool
    blank: bool
    editable: bool
    verbose_name: str
    has_permission: bool


@dataclass
class RelationshipMetadata:
    """Metadata for model relationships."""

    name: str
    relationship_type: str
    # Embed full related model metadata (single-level depth by default)
    related_model: "ModelMetadata"
    related_app: str
    to_field: Optional[str]
    from_field: str
    is_reverse: bool
    is_required: bool
    many_to_many: bool
    one_to_one: bool
    foreign_key: bool
    on_delete: Optional[str]
    related_name: Optional[str]
    has_permission: bool
    verbose_name: str


@dataclass
class ModelMetadata:
    """Complete metadata for a Django model."""

    app_name: str
    model_name: str
    verbose_name: str
    verbose_name_plural: str
    table_name: str
    primary_key_field: str
    fields: List[FieldMetadata]
    relationships: List[RelationshipMetadata]
    permissions: List[str]
    ordering: List[str]
    unique_together: List[List[str]]
    indexes: List[Dict[str, Any]]
    abstract: bool
    proxy: bool
    managed: bool
    filters: List[Dict[str, Any]]
    mutations: List["MutationMetadata"]


@dataclass
class FormFieldMetadata:
    """Metadata for form fields with Django-specific attributes."""

    name: str
    field_type: str
    is_required: bool
    verbose_name: str
    help_text: str
    widget_type: str
    placeholder: Optional[str] = None
    default_value: Any = None
    choices: Optional[List[Dict[str, str]]] = None
    # Django CharField attributes
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    # Django DecimalField attributes
    decimal_places: Optional[int] = None
    max_digits: Optional[int] = None
    # Django IntegerField/FloatField attributes
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    # Django DateField/DateTimeField attributes
    auto_now: bool = False
    auto_now_add: bool = False
    # Common field attributes
    blank: bool = False
    null: bool = False
    unique: bool = False
    editable: bool = True
    # Validation attributes
    validators: Optional[List[str]] = None
    error_messages: Optional[Dict[str, str]] = None
    # Form-specific attributes
    disabled: bool = False
    readonly: bool = False
    css_classes: Optional[str] = None
    data_attributes: Optional[Dict[str, str]] = None
    has_permission: bool = True


@dataclass
class FormRelationshipMetadata:
    """Metadata for form relationship fields with nested model information."""

    name: str
    relationship_type: str
    verbose_name: str
    help_text: str
    widget_type: str
    is_required: bool
    # Related model information
    related_model: str
    related_app: str
    to_field: Optional[str] = None
    from_field: str = ""
    # Relationship characteristics
    many_to_many: bool = False
    one_to_one: bool = False
    foreign_key: bool = False
    is_reverse: bool = False
    # Form-specific attributes
    multiple: bool = False
    queryset_filters: Optional[Dict[str, Any]] = None
    empty_label: Optional[str] = None
    limit_choices_to: Optional[Dict[str, Any]] = None
    # UI attributes
    disabled: bool = False
    readonly: bool = False
    css_classes: Optional[str] = None
    data_attributes: Optional[Dict[str, str]] = None
    has_permission: bool = True


@dataclass
class ModelFormMetadata:
    """Complete metadata for Django model forms."""

    app_name: str
    model_name: str
    verbose_name: str
    verbose_name_plural: str
    form_title: str
    form_description: Optional[str]
    fields: List[FormFieldMetadata]
    relationships: List[FormRelationshipMetadata]
    nested: List["ModelFormMetadata"] = field(default_factory=list)
    # Form configuration
    field_order: Optional[List[str]] = None
    exclude_fields: List[str] = field(default_factory=list)
    readonly_fields: List[str] = field(default_factory=list)
    # Validation and permissions
    required_permissions: List[str] = field(default_factory=list)
    form_validation_rules: Optional[Dict[str, Any]] = None
    # UI configuration
    form_layout: Optional[Dict[str, Any]] = None
    css_classes: Optional[str] = None
    form_attributes: Optional[Dict[str, str]] = None


@dataclass
class TableFieldMetadata:
    """Metadata for a table field used in data grid displays."""

    name: str
    accessor: str
    display: str
    editable: bool
    field_type: str
    filterable: bool
    sortable: bool
    title: str
    helpText: str
    is_property: bool
    is_related: bool


@dataclass
class ModelTableMetadata:
    """Comprehensive table metadata for a Django model, including fields and filters."""

    app: str
    model: str
    verboseName: str
    verboseNamePlural: str
    tableName: str
    primaryKey: str
    ordering: List[str]
    defaultOrdering: List[str]
    get_latest_by: Optional[str]
    managers: List[str]
    managed: bool
    fields: List[TableFieldMetadata]
    filters: List[Dict[str, Any]]


class FieldMetadataType(graphene.ObjectType):
    """GraphQL type for field metadata."""

    name = graphene.String(required=True, description="Field name")
    field_type = graphene.String(required=True, description="Django field type")
    is_required = graphene.Boolean(
        required=True, description="Whether field is required"
    )
    is_nullable = graphene.Boolean(
        required=True, description="Whether field can be null"
    )
    null = graphene.Boolean(required=True, description="Whether field can be null")
    default_value = graphene.String(description="Default value as string")
    help_text = graphene.String(description="Field help text")
    max_length = graphene.Int(description="Maximum length for string fields")
    choices = graphene.List(ChoiceType, description="Field choices")
    is_primary_key = graphene.Boolean(
        required=True, description="Whether field is primary key"
    )
    is_foreign_key = graphene.Boolean(
        required=True, description="Whether field is foreign key"
    )
    is_unique = graphene.Boolean(
        required=True, description="Whether field has unique constraint"
    )
    is_indexed = graphene.Boolean(required=True, description="Whether field is indexed")
    has_auto_now = graphene.Boolean(
        required=True, description="Whether field has auto_now"
    )
    has_auto_now_add = graphene.Boolean(
        required=True, description="Whether field has auto_now_add"
    )
    blank = graphene.Boolean(required=True, description="Whether field can be blank")
    editable = graphene.Boolean(required=True, description="Whether field is editable")
    verbose_name = graphene.String(required=True, description="Field verbose name")
    has_permission = graphene.Boolean(
        required=True, description="Whether user has permission for this field"
    )


class RelationshipMetadataType(graphene.ObjectType):
    """GraphQL type for relationship metadata."""

    name = graphene.String(required=True, description="Relationship field name")
    relationship_type = graphene.String(
        required=True, description="Type of relationship"
    )
    related_model = graphene.Field(
        lambda: ModelMetadataType,
        required=True,
        description="Related model metadata",
    )
    related_app = graphene.String(required=True, description="Related model app")
    to_field = graphene.String(description="Target field name")
    from_field = graphene.String(required=True, description="Source field name")
    is_reverse = graphene.Boolean(
        required=True, description="Whether this is a reverse relationship"
    )
    is_required = graphene.Boolean(
        required=True, description="Whether this is a reverse relationship"
    )
    many_to_many = graphene.Boolean(
        required=True, description="Whether this is many-to-many"
    )
    one_to_one = graphene.Boolean(
        required=True, description="Whether this is one-to-one"
    )
    foreign_key = graphene.Boolean(
        required=True, description="Whether this is foreign key"
    )
    on_delete = graphene.String(description="On delete behavior")
    related_name = graphene.String(description="Related name for reverse lookups")
    has_permission = graphene.Boolean(
        required=True, description="Whether user has permission for this relationship"
    )
    verbose_name = graphene.String(required=True, description="Model verbose name")


class ModelMetadataType(graphene.ObjectType):
    """GraphQL type for complete model metadata."""

    app_name = graphene.String(required=True, description="Django app name")
    model_name = graphene.String(required=True, description="Model class name")
    verbose_name = graphene.String(required=True, description="Model verbose name")
    verbose_name_plural = graphene.String(
        required=True, description="Model verbose name plural"
    )
    table_name = graphene.String(required=True, description="Database table name")
    primary_key_field = graphene.String(
        required=True, description="Primary key field name"
    )
    fields = graphene.List(FieldMetadataType, required=True, description="Model fields")
    relationships = graphene.List(
        RelationshipMetadataType, required=True, description="Model relationships"
    )
    permissions = graphene.List(
        graphene.String, required=True, description="Available permissions"
    )
    ordering = graphene.List(
        graphene.String, required=True, description="Default ordering"
    )
    unique_together = graphene.List(
        graphene.List(graphene.String),
        required=True,
        description="Unique together constraints",
    )
    indexes = graphene.List(
        graphene.JSONString, required=True, description="Database indexes"
    )
    abstract = graphene.Boolean(required=True, description="Whether model is abstract")
    proxy = graphene.Boolean(required=True, description="Whether model is proxy")
    managed = graphene.Boolean(
        required=True, description="Whether model is managed by Django"
    )
    filters = graphene.List(
        FilterFieldType, required=True, description="Available filter fields"
    )
    mutations = graphene.List(
        MutationMetadataType,
        required=True,
        description="Available mutations for this model",
    )


class FormFieldMetadataType(graphene.ObjectType):
    """GraphQL type for form field metadata."""

    name = graphene.String(required=True, description="Field name")
    field_type = graphene.String(required=True, description="Django field type")
    is_required = graphene.Boolean(
        required=True, description="Whether field is required"
    )
    verbose_name = graphene.String(required=True, description="Field verbose name")
    help_text = graphene.String(description="Field help text")
    widget_type = graphene.String(
        required=True, description="Recommended UI widget type"
    )
    placeholder = graphene.String(description="Placeholder text for input")
    default_value = graphene.JSONString(description="Default value for the field")
    choices = graphene.List(ChoiceType, description="Field choices")
    # Django CharField attributes
    max_length = graphene.Int(description="Maximum length for string fields")
    min_length = graphene.Int(description="Minimum length for string fields")
    # Django DecimalField attributes
    decimal_places = graphene.Int(description="Number of decimal places")
    max_digits = graphene.Int(description="Maximum number of digits")
    # Django IntegerField/FloatField attributes
    min_value = graphene.Float(description="Minimum value for numeric fields")
    max_value = graphene.Float(description="Maximum value for numeric fields")
    # Django DateField/DateTimeField attributes
    auto_now = graphene.Boolean(required=True, description="Whether field has auto_now")
    auto_now_add = graphene.Boolean(
        required=True, description="Whether field has auto_now_add"
    )
    # Common field attributes
    blank = graphene.Boolean(required=True, description="Whether field can be blank")
    null = graphene.Boolean(required=True, description="Whether field can be null")
    unique = graphene.Boolean(
        required=True, description="Whether field has unique constraint"
    )
    editable = graphene.Boolean(required=True, description="Whether field is editable")
    # Validation attributes
    validators = graphene.List(graphene.String, description="Field validators")
    error_messages = graphene.JSONString(description="Custom error messages")
    # Form-specific attributes
    disabled = graphene.Boolean(
        required=True, description="Whether field is disabled in form"
    )
    readonly = graphene.Boolean(
        required=True, description="Whether field is readonly in form"
    )
    css_classes = graphene.String(description="CSS classes for form field")
    data_attributes = graphene.JSONString(description="Data attributes for form field")
    has_permission = graphene.Boolean(
        required=True, description="Whether user has permission to access this field"
    )
    has_permission = graphene.Boolean(
        required=True, description="Whether user has permission to access this field"
    )


class FormRelationshipMetadataType(graphene.ObjectType):
    """GraphQL type for form relationship metadata."""

    name = graphene.String(required=True, description="Relationship field name")
    relationship_type = graphene.String(
        required=True, description="Type of relationship"
    )
    verbose_name = graphene.String(required=True, description="Field verbose name")
    help_text = graphene.String(description="Field help text")
    widget_type = graphene.String(
        required=True, description="Recommended UI widget type"
    )
    is_required = graphene.Boolean(
        required=True, description="Whether field is required"
    )
    # Related model information
    related_model = graphene.String(
        required=True,
        description="Related model name",
    )
    related_app = graphene.String(required=True, description="Related model app")
    to_field = graphene.String(description="Target field name")
    from_field = graphene.String(required=True, description="Source field name")
    # Relationship characteristics
    many_to_many = graphene.Boolean(
        required=True, description="Whether this is many-to-many"
    )
    one_to_one = graphene.Boolean(
        required=True, description="Whether this is one-to-one"
    )
    foreign_key = graphene.Boolean(
        required=True, description="Whether this is foreign key"
    )
    is_reverse = graphene.Boolean(
        required=True, description="Whether this is a reverse relationship"
    )
    # Form-specific attributes
    multiple = graphene.Boolean(
        required=True, description="Whether field accepts multiple values"
    )
    queryset_filters = graphene.JSONString(description="Queryset filters for choices")
    empty_label = graphene.String(description="Empty choice label")
    limit_choices_to = graphene.JSONString(
        description="Limit choices to specific criteria"
    )
    # UI attributes
    disabled = graphene.Boolean(
        required=True, description="Whether field is disabled in form"
    )
    readonly = graphene.Boolean(
        required=True, description="Whether field is readonly in form"
    )
    css_classes = graphene.String(description="CSS classes for form field")
    data_attributes = graphene.JSONString(description="Data attributes for form field")


class ModelFormMetadataType(graphene.ObjectType):
    """GraphQL type for complete model form metadata."""

    app_name = graphene.String(required=True, description="Django app name")
    model_name = graphene.String(required=True, description="Model class name")
    verbose_name = graphene.String(required=True, description="Model verbose name")
    verbose_name_plural = graphene.String(
        required=True, description="Model verbose name plural"
    )
    form_title = graphene.String(required=True, description="Form title")
    form_description = graphene.String(description="Form description")
    fields = graphene.List(
        FormFieldMetadataType, required=True, description="Form fields"
    )
    relationships = graphene.List(
        FormRelationshipMetadataType, required=True, description="Form relationships"
    )
    nested = graphene.List(
        lambda: ModelFormMetadataType,
        required=True,
        description="Nested form metadata for specified fields",
    )
    # Form configuration
    field_order = graphene.List(graphene.String, description="Field display order")
    exclude_fields = graphene.List(
        graphene.String, required=True, description="Fields to exclude from form"
    )
    readonly_fields = graphene.List(
        graphene.String, required=True, description="Fields that are readonly"
    )
    # Validation and permissions
    required_permissions = graphene.List(
        graphene.String, required=True, description="Required permissions"
    )
    form_validation_rules = graphene.JSONString(description="Form validation rules")
    # UI configuration
    form_layout = graphene.JSONString(description="Form layout configuration")
    css_classes = graphene.String(description="CSS classes for form")
    form_attributes = graphene.JSONString(description="Form HTML attributes")


class TableFieldMetadataType(graphene.ObjectType):
    """GraphQL type for table field metadata used in data grid."""

    name = graphene.String(required=True, description="Field name")
    accessor = graphene.String(required=True, description="Field accessor")
    display = graphene.String(required=True, description="Field display accessor")
    editable = graphene.Boolean(required=True, description="Whether field is editable")
    field_type = graphene.String(required=True, description="Field data type")
    filterable = graphene.Boolean(
        required=True, description="Whether field is filterable"
    )
    sortable = graphene.Boolean(required=True, description="Whether field is sortable")
    title = graphene.String(required=True, description="Field title (verbose name)")
    helpText = graphene.String(required=True, description="Help text or description")
    is_property = graphene.Boolean(
        required=True, description="Whether field is a property"
    )
    is_related = graphene.Boolean(required=True, description="Whether field is related")


class ModelTableType(graphene.ObjectType):
    """GraphQL type for comprehensive table metadata for a Django model."""

    app = graphene.String(required=True, description="Application name")
    model = graphene.String(required=True, description="Model name")
    verboseName = graphene.String(required=True, description="Singular verbose name")
    verboseNamePlural = graphene.String(
        required=True, description="Plural verbose name"
    )
    tableName = graphene.String(required=True, description="Database table name")
    primaryKey = graphene.String(required=True, description="Primary key field name")
    ordering = graphene.List(
        graphene.String, required=True, description="Default ordering fields"
    )
    defaultOrdering = graphene.List(
        graphene.String, required=True, description="Fallback ordering fields"
    )
    get_latest_by = graphene.String(description="Field used by 'latest' manager")
    managers = graphene.List(
        graphene.String, required=True, description="Manager names"
    )
    managed = graphene.Boolean(
        required=True, description="Whether Django manages the table"
    )
    fields = graphene.List(
        TableFieldMetadataType, required=True, description="All field metadata"
    )
    filters = graphene.List(
        FilterFieldType,
        required=True,
        description="Available filters with field structure",
    )


class ModelMetadataExtractor:
    """Extracts comprehensive metadata from Django models."""

    def __init__(self, schema_name: str = "default", max_depth: int = 1):
        """
        Initialize the metadata extractor.

        Args:
            schema_name: Name of the schema configuration to use
            max_depth: Maximum depth for nested related model metadata
        """
        # Lazy import to avoid AppRegistryNotReady
        # from ..core.settings import get_schema_settings

        self.schema_name = schema_name
        self.max_depth = max_depth
        # self.settings = get_schema_settings(schema_name)

    @cache_metadata(
        timeout=0,
        user_specific=True,
        # timeout=1200, user_specific=True
    )  # 20 minutes cache for field metadata
    def _extract_field_metadata(self, field, user) -> Optional[FieldMetadata]:
        """
        Extract metadata for a single field with permission checking.

        Args:
            field: Django model field instance

        Returns:
            FieldMetadata if user has permission, None otherwise
        """
        # Lazy import to avoid AppRegistryNotReady
        from django.db import models

        # Get field choices
        choices = None
        if hasattr(field, "choices") and field.choices:
            choices = [
                {"value": choice[0], "label": choice[1]} for choice in field.choices
            ]

        # Get max length
        max_length = getattr(field, "max_length", None)

        # Get on_delete behavior for foreign keys (guard None)
        on_delete = None
        if getattr(field, "remote_field", None) is not None:
            remote_on_delete = getattr(field.remote_field, "on_delete", None)
            if remote_on_delete:
                on_delete = getattr(remote_on_delete, "__name__", None)

        # Simplified permission flag; adjust with actual permission checks if needed
        has_permission = True
        return FieldMetadata(
            name=field.name,
            field_type=field.__class__.__name__,
            is_required=not field.blank and field.default == models.NOT_PROVIDED,
            is_nullable=field.null,
            null=field.null,
            default_value=str(field.default)
            if field.default != models.NOT_PROVIDED
            else None,
            help_text=field.help_text or "",
            max_length=max_length,
            choices=choices,
            is_primary_key=getattr(field, "primary_key", None),
            is_foreign_key=isinstance(field, models.ForeignKey),
            is_unique=field.unique,
            is_indexed=field.db_index,
            has_auto_now=getattr(field, "auto_now", False),
            has_auto_now_add=getattr(field, "auto_now_add", False),
            blank=field.blank,
            editable=field.editable,
            verbose_name=str(field.verbose_name),
            has_permission=has_permission,
        )

    @cache_metadata(
        timeout=1200, user_specific=True
    )  # 20 minutes cache for relationship metadata
    def _extract_relationship_metadata(
        self, field, user, current_depth: int = 0
    ) -> Optional[RelationshipMetadata]:
        """
        Extract metadata for relationship fields.

        Args:
            field: Django relationship field instance

        Returns:
            RelationshipMetadata if user has permission, None otherwise
        """
        # Lazy import to avoid AppRegistryNotReady
        from django.db import models

        related_model = field.related_model
        on_delete = None

        if getattr(field, "remote_field", None) is not None:
            remote_on_delete = getattr(field.remote_field, "on_delete", None)
            if remote_on_delete:
                on_delete = getattr(remote_on_delete, "__name__", None)

        # Simplified permission flag; adjust with actual checks if needed
        has_permission = True

        # Build embedded related model metadata (guard depth to avoid recursion)
        if related_model is None or not hasattr(related_model, "_meta"):
            return None

        related_app_label = getattr(related_model._meta, "app_label", "")
        related_model_class_name = related_model.__name__

        # Include nested relationships only if within max depth
        include_nested = current_depth < self.max_depth
        embedded_related = self.extract_model_metadata(
            app_name=related_app_label,
            model_name=related_model_class_name,
            user=user,
            nested_fields=include_nested,
            permissions_included=True,
            current_depth=current_depth + 1,
        )
        if embedded_related is None:
            return None

        return RelationshipMetadata(
            name=field.name,
            relationship_type=field.__class__.__name__,
            related_model=embedded_related,
            is_required=not field.blank,
            related_app=related_app_label,
            to_field=field.remote_field.name
            if hasattr(field, "remote_field") and field.remote_field
            else None,
            from_field=field.name,
            is_reverse=False,
            many_to_many=isinstance(field, models.ManyToManyField),
            one_to_one=isinstance(field, models.OneToOneField),
            foreign_key=isinstance(field, models.ForeignKey),
            on_delete=on_delete,
            related_name=getattr(field, "related_name", None),
            has_permission=has_permission,
            verbose_name=field.verbose_name,
        )

    @cache_metadata(
        timeout=1800, user_specific=False
    )  # 30 minutes cache for complete model metadata
    def extract_model_metadata(
        self,
        app_name: str,
        model_name: str,
        user,
        nested_fields: bool = True,
        permissions_included: bool = True,
        current_depth: int = 0,
    ) -> Optional[ModelMetadata]:
        """
        Extract complete metadata for a Django model.

        Args:
            app_name: Django app label
            model_name: Model class name
            user: Current user for permission checking
            nested_fields: Whether to include relationship metadata
            permissions_included: Whether to include permission information

        Returns:
            ModelMetadata with filtered fields based on permissions, or None on error
        """
        # Resolve the model from app and model name
        try:
            model = apps.get_model(app_name, model_name)
        except Exception as e:
            logger.error(
                "Model '%s' not found in app '%s': %s", model_name, app_name, e
            )
            return None

        introspector = ModelIntrospector(model, self.schema_name)

        # Extract field metadata with permission filtering using concrete model fields
        fields = []
        for django_field in model._meta.get_fields():
            # Only include concrete fields (exclude relations and auto-created reverse accessors)
            if getattr(django_field, "is_relation", False):
                continue
            if getattr(django_field, "auto_created", False):
                continue
            field_metadata = self._extract_field_metadata(django_field, user)
            if field_metadata:
                fields.append(field_metadata)

        # Extract relationship metadata with permission filtering (declared relations only)
        relationships = []
        if nested_fields:
            for django_field in model._meta.get_fields():
                if not getattr(django_field, "is_relation", False):
                    continue
                # Skip polymorphic_ctype field
                if django_field.name == "polymorphic_ctype":
                    continue
                # Skip auto-created reverse relations; they will be added below
                if getattr(django_field, "auto_created", False):
                    continue
                rel_metadata = self._extract_relationship_metadata(
                    django_field, user, current_depth=current_depth
                )
                if rel_metadata:
                    relationships.append(rel_metadata)

        # Always include reverse relationships
        if nested_fields:
            reverse_relations = introspector.get_reverse_relations()
            for rel_name, related_model in reverse_relations.items():
                # Build embedded metadata for reverse-related model with depth guard
                include_nested = current_depth < self.max_depth
                embedded_related = self.extract_model_metadata(
                    app_name=related_model._meta.app_label,
                    model_name=related_model.__name__,
                    user=user,
                    nested_fields=include_nested,
                    permissions_included=True,
                    current_depth=current_depth + 1,
                )
                if embedded_related is None:
                    continue
                relationships.append(
                    RelationshipMetadata(
                        name=rel_name,
                        verbose_name=related_model._meta.verbose_name,
                        relationship_type="ReverseRelation",
                        related_model=embedded_related,
                        related_app=related_model._meta.app_label,
                        to_field=None,
                        is_required=False,
                        from_field=rel_name,
                        is_reverse=True,
                        many_to_many=False,
                        one_to_one=False,
                        foreign_key=False,
                        on_delete=None,
                        related_name=rel_name,
                        has_permission=True,
                    )
                )

        # Get model permissions for the user
        permissions = []
        if permissions_included and user:
            # Lazy import to avoid AppRegistryNotReady
            from django.contrib.auth.models import AnonymousUser

            if not isinstance(user, AnonymousUser):
                app_label = model._meta.app_label
                model_name_code = model._meta.model_name

                # Check standard Django permissions
                for action in ["add", "change", "delete", "view"]:
                    perm_code = f"{app_label}.{action}_{model_name_code}"
                    if user.has_perm(perm_code):
                        permissions.append(perm_code)

        # Get ordering
        ordering = list(model._meta.ordering) if model._meta.ordering else []

        # Get unique_together
        unique_together = []
        if hasattr(model._meta, "unique_together") and model._meta.unique_together:
            unique_together = [
                list(constraint) for constraint in model._meta.unique_together
            ]

        # Get indexes
        indexes = []
        if hasattr(model._meta, "indexes"):
            for index in model._meta.indexes:
                indexes.append(
                    {
                        "name": index.name,
                        "fields": list(index.fields),
                        "unique": getattr(index, "unique", False),
                    }
                )

        # Extract filter metadata
        filters = self._extract_filter_metadata(model)

        # Extract mutations metadata
        mutations = self.extract_mutations_metadata(
            model,
        )

        return ModelMetadata(
            app_name=model._meta.app_label,
            model_name=model.__name__,
            verbose_name=str(model._meta.verbose_name),
            verbose_name_plural=str(model._meta.verbose_name_plural),
            table_name=model._meta.db_table,
            primary_key_field=model._meta.pk.name,
            fields=fields,
            relationships=relationships,
            permissions=permissions,
            ordering=ordering,
            unique_together=unique_together,
            indexes=indexes,
            abstract=model._meta.abstract,
            proxy=model._meta.proxy,
            managed=model._meta.managed,
            filters=filters,
            mutations=mutations,
        )

    def _has_field_permission(self, user, model: type, field_name: str) -> bool:
        """
        Check if user has permission to access a specific field.

        Args:
            user: Django user instance
            model: Django model class
            field_name: Name of the field to check

        Returns:
            bool: True if user has permission to access the field
        """
        # Lazy import to avoid AppRegistryNotReady
        from django.contrib.auth.models import AnonymousUser

        if isinstance(user, AnonymousUser):
            return False

        # Check basic view permission for the model
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        view_permission = f"{app_label}.view_{model_name}"

        return user.has_perm(view_permission)

    @cache_metadata(
        timeout=1800, user_specific=False
    )  # 30 minutes cache for filter metadata (not user-specific)
    def _extract_filter_metadata(self, model) -> List[Dict[str, Any]]:
        """
        Extract comprehensive filter metadata for a Django model with enhanced features.

        Args:
            model: Django model class

        Returns:
            List of grouped filter field metadata dictionaries
        """
        try:
            # Import the enhanced filter generator
            from ..generators.filters import (
                AdvancedFilterGenerator,
                EnhancedFilterGenerator,
            )
            from ..utils.graphql_meta import get_model_graphql_meta

            # Use the instance's max_depth parameter
            max_depth = self.max_depth

            # Create enhanced filter generator instance with configurable depth
            enhanced_generator = EnhancedFilterGenerator(
                max_nested_depth=max_depth,
                enable_nested_filters=True,
                schema_name=self.schema_name,
            )

            # Get grouped filters for the model
            grouped_filters = enhanced_generator.get_grouped_filters(model)

            # Get GraphQL meta for custom filters
            graphql_meta = get_model_graphql_meta(model)

            # Create a dictionary to group filters by field name
            grouped_filter_dict = {}

            # Process enhanced filters
            for grouped_filter in grouped_filters:
                field_name = grouped_filter.field_name

                # Exclude the primary key 'id' field from filter metadata
                if field_name == "id" or "quick" in field_name:
                    continue

                # Get field verbose name for help text
                try:
                    field = model._meta.get_field(field_name)
                    verbose_name = str(field.verbose_name)
                except Exception:
                    # Ensure 'field' is defined to avoid UnboundLocalError later
                    field = None
                    verbose_name = field_name

                options = []
                for operation in grouped_filter.operations:
                    filter_name = (
                        f"{field_name}__{operation.lookup_expr}"
                        if operation.lookup_expr != "exact"
                        else field_name
                    )

                    # Translate help text to French using verbose_name
                    # Be defensive: some operations may not have description
                    help_text = self._translate_help_text_to_french(
                        operation.description or operation.lookup_expr, verbose_name
                    )

                    # Include choices if this is a CharField with declared choices (primarily for exact)
                    option_choices = None
                    if field is not None and isinstance(field, models.CharField):
                        raw_choices = getattr(field, "choices", None)
                        if raw_choices:
                            try:
                                option_choices = [
                                    {"value": str(val), "label": str(lbl)}
                                    for val, lbl in raw_choices
                                ]
                            except Exception:
                                option_choices = None

                    options.append(
                        {
                            "name": filter_name,
                            "lookup_expr": operation.lookup_expr,
                            "help_text": help_text,
                            "filter_type": operation.filter_type,
                            "choices": option_choices,
                        }
                    )
                # Safely resolve related model name even when 'field' lookup fails
                related_model_name = (
                    field.related_model.__name__
                    if (field is not None and getattr(field, "related_model", None))
                    else None
                )

                grouped_filter_dict[field_name] = {
                    "field_name": field_name,
                    "is_nested": False,
                    "related_model": related_model_name,
                    "is_custom": False,
                    "field_label": verbose_name,
                    "options": options,
                }

            # Add nested filters from traditional generator - RESTRUCTURED TO PARENT LEVEL
            try:
                filter_generator = AdvancedFilterGenerator(
                    max_nested_depth=max_depth,  # Use configurable depth
                    enable_nested_filters=True,
                    schema_name=self.schema_name,
                )

                filter_class = filter_generator.generate_filter_set(model)

                # Process nested filters and GROUP them under the base field name
                for filter_name, filter_instance in filter_class.base_filters.items():
                    if "quick" in filter_name:
                        continue

                    if "__" in filter_name and not filter_name.endswith("_count"):
                        field_parts = filter_name.split("__")
                        base_field_name = field_parts[0]
                        lookup_expr = "__".join(field_parts[1:])

                        # Optional depth control (kept if present elsewhere)
                        try:
                            if len(field_parts) - 1 > max_depth:  # type: ignore[name-defined]
                                continue
                        except Exception:
                            # If max_depth is not defined, proceed without depth restriction
                            pass

                        # Get related model info
                        related_model = None
                        try:
                            field = model._meta.get_field(base_field_name)
                            if hasattr(field, "related_model"):
                                related_model = field.related_model.__name__
                        except:
                            continue

                        # Get verbose name for nested field
                        try:
                            verbose_name = str(field.verbose_name)
                        except:
                            verbose_name = base_field_name

                        # GROUP: Add nested filter as an option under the base field
                        help_text = self._translate_help_text_to_french(
                            lookup_expr, verbose_name
                        )

                        if base_field_name not in grouped_filter_dict:
                            grouped_filter_dict[base_field_name] = {
                                "field_name": base_field_name,
                                "is_nested": True,
                                "related_model": related_model,
                                "is_custom": False,
                                "field_label": verbose_name,
                                "options": [],
                            }

                        grouped_filter_dict[base_field_name]["options"].append(
                            {
                                "name": filter_name,  # full path for execution
                                "lookup_expr": lookup_expr,
                                "help_text": help_text,
                                "filter_type": filter_instance.__class__.__name__,
                            }
                        )

                # Add property filters for @property-based fields
                try:
                    from ..generators.introspector import ModelIntrospector

                    introspector = ModelIntrospector(model, self.schema_name)
                    property_map = getattr(introspector, "properties", {}) or {}
                    property_names = set(property_map.keys())

                    # Iterate base filters and group property filters under property name
                    for fname, finstance in getattr(
                        filter_class, "base_filters", {}
                    ).items():
                        base_name = fname.split("__")[0]
                        if "quick" in base_name:
                            continue
                        if base_name in property_names:
                            lookup_expr = "__".join(fname.split("__")[1:]) or "exact"
                            prop_obj = property_map.get(base_name)
                            # Prefer fget.short_description when available for properties
                            verbose = (
                                getattr(
                                    getattr(prop_obj, "fget", None),
                                    "short_description",
                                    None,
                                )
                                or getattr(prop_obj, "verbose_name", None)
                                or base_name
                            )
                            original_help = (
                                getattr(finstance, "help_text", None)
                                or getattr(finstance, "label", "")
                                or f"Filter for {base_name}"
                            )
                            help_text = self._translate_help_text_to_french(
                                original_help, verbose
                            )

                            if base_name not in grouped_filter_dict:
                                grouped_filter_dict[base_name] = {
                                    "field_name": base_name,
                                    "is_nested": False,
                                    "related_model": None,
                                    "is_custom": False,
                                    "field_label": verbose,
                                    "options": [],
                                }

                            grouped_filter_dict[base_name]["options"].append(
                                {
                                    "name": fname,
                                    "lookup_expr": lookup_expr,
                                    "help_text": help_text,
                                    "filter_type": finstance.__class__.__name__,
                                }
                            )
                except Exception as e:
                    logger.warning(
                        f"Error processing property filters for {model.__name__}: {e}"
                    )

            except Exception as e:
                logger.warning(
                    f"Error processing nested filters for {model.__name__}: {e}"
                )

            # ENHANCED: Add custom filters from GraphQLMeta with better quick filter support
            if graphql_meta:
                # Add quick filters with comprehensive field support
                if (
                    hasattr(graphql_meta, "quick_filter_fields")
                    and graphql_meta.quick_filter_fields
                ):
                    quick_fields = graphql_meta.quick_filter_fields

                    # Create comprehensive quick filter entry
                    grouped_filter_dict["quick"] = {
                        "field_name": "quick",
                        "is_nested": False,
                        "related_model": None,
                        "is_custom": True,
                        "field_label": "Quick filter",
                        "options": [
                            {
                                "name": "quick",
                                "lookup_expr": "icontains",
                                "help_text": f"Recherche rapide dans les champs: {', '.join(quick_fields)}",
                                "filter_type": "CharFilter",
                            }
                        ],
                    }

                    # Also add individual quick filter options for each field
                    # for quick_field in quick_fields:
                    #     if "__" in quick_field:  # Handle nested quick fields
                    #         # Add nested quick field as separate filter
                    #         quick_filter_name = (
                    #             f"quick_{quick_field.replace('__', '_')}"
                    #         )
                    #         grouped_filter_dict[quick_filter_name] = {
                    #             "field_name": quick_filter_name,
                    #             "is_nested": True,
                    #             "related_model": self._get_related_model_name(
                    #                 model, quick_field
                    #             ),
                    #             "is_custom": True,
                    #             "field_label": quick_filter_name,
                    #             "options": [
                    #                 {
                    #                     "name": quick_filter_name,
                    #                     "lookup_expr": "icontains",
                    #                     "help_text": f"Recherche rapide dans {quick_field}",
                    #                     "filter_type": "CharFilter",
                    #                 }
                    #             ],
                    #         }

                # Add custom filters
                if (
                    hasattr(graphql_meta, "custom_filters")
                    and graphql_meta.custom_filters
                ):
                    for (
                        custom_name,
                        custom_method,
                    ) in graphql_meta.custom_filters.items():
                        if "quick" in custom_name:
                            continue
                        grouped_filter_dict[custom_name] = {
                            "field_name": custom_name,
                            "is_nested": False,
                            "related_model": None,
                            "is_custom": True,
                            "field_label": custom_name,
                            "options": [
                                {
                                    "name": custom_name,
                                    "lookup_expr": "custom",
                                    "help_text": f"Filtre personnalisé: {custom_name}",
                                    "filter_type": "CustomFilter",
                                }
                            ],
                        }

            # Convert to list format and sort for consistency
            # Fallback: if no filters were constructed, build a minimal set
            if not grouped_filter_dict:
                try:
                    for f in model._meta.get_fields():
                        if not hasattr(f, "name") or getattr(f, "auto_created", False):
                            continue

                        fname = f.name
                        if fname == "id":
                            # Exclude id from minimal filter construction as requested
                            continue
                        verbose = str(getattr(f, "verbose_name", fname))
                        options = []

                        # Minimal operation set per common field types
                        if isinstance(f, (models.CharField, models.TextField)):
                            for lookup in ("exact", "icontains"):
                                help_text = self._translate_help_text_to_french(
                                    lookup, verbose
                                )
                                option_choices = None
                                if lookup == "exact" and isinstance(
                                    f, models.CharField
                                ):
                                    raw_choices = getattr(f, "choices", None)
                                    if raw_choices:
                                        try:
                                            option_choices = [
                                                {"value": str(val), "label": str(lbl)}
                                                for val, lbl in raw_choices
                                            ]
                                        except Exception:
                                            option_choices = None
                                options.append(
                                    {
                                        "name": fname
                                        if lookup == "exact"
                                        else f"{fname}__{lookup}",
                                        "lookup_expr": lookup,
                                        "help_text": help_text,
                                        "filter_type": "CharFilter",
                                        "choices": option_choices,
                                    }
                                )
                        elif isinstance(
                            f,
                            (
                                models.IntegerField,
                                models.FloatField,
                                models.DecimalField,
                            ),
                        ):
                            for lookup in ("exact", "gt", "gte", "lt", "lte"):
                                help_text = self._translate_help_text_to_french(
                                    lookup, verbose
                                )
                                options.append(
                                    {
                                        "name": fname
                                        if lookup == "exact"
                                        else f"{fname}__{lookup}",
                                        "lookup_expr": lookup,
                                        "help_text": help_text,
                                        "filter_type": "NumberFilter",
                                    }
                                )
                        elif isinstance(f, (models.DateField, models.DateTimeField)):
                            for lookup in (
                                "exact",
                                "range",
                                "today",
                                "this_month",
                                "this_year",
                            ):
                                help_text = self._translate_help_text_to_french(
                                    lookup, verbose
                                )
                                options.append(
                                    {
                                        "name": fname
                                        if lookup == "exact"
                                        else f"{fname}__{lookup}",
                                        "lookup_expr": lookup,
                                        "help_text": help_text,
                                        "filter_type": "DateFilter",
                                    }
                                )
                        elif isinstance(f, models.BooleanField):
                            for lookup in ("exact", "isnull"):
                                help_text = self._translate_help_text_to_french(
                                    lookup, verbose
                                )
                                options.append(
                                    {
                                        "name": fname
                                        if lookup == "exact"
                                        else f"{fname}__{lookup}",
                                        "lookup_expr": lookup,
                                        "help_text": help_text,
                                        "filter_type": "BooleanFilter",
                                    }
                                )
                        elif isinstance(f, models.ForeignKey):
                            # Basic FK filter: exact by id
                            help_text = self._translate_help_text_to_french(
                                "exact", verbose
                            )
                            options.append(
                                {
                                    "name": fname,
                                    "lookup_expr": "exact",
                                    "help_text": help_text,
                                    "filter_type": "NumberFilter",
                                }
                            )
                        elif isinstance(f, models.ManyToManyField):
                            # Basic M2M filter: in
                            help_text = self._translate_help_text_to_french(
                                "in", verbose
                            )
                            options.append(
                                {
                                    "name": f"{fname}__in",
                                    "lookup_expr": "in",
                                    "help_text": help_text,
                                    "filter_type": "ModelMultipleChoiceFilter",
                                }
                            )

                        if options:
                            grouped_filter_dict[fname] = {
                                "field_name": fname,
                                "is_nested": False,
                                "related_model": getattr(
                                    getattr(f, "related_model", None), "__name__", None
                                ),
                                "is_custom": False,
                                "field_label": verbose,
                                "options": options,
                            }
                except Exception as e:
                    logger.warning(
                        f"Fallback filter construction failed for {model.__name__}: {e}"
                    )

            result = list(grouped_filter_dict.values())
            # Sort filters: regular fields first, then nested, then custom
            result.sort(key=lambda x: (x["is_custom"], x["is_nested"], x["field_name"]))
            return result

        except Exception as e:
            logger.error(f"Error extracting filter metadata for {model.__name__}: {e}")
            return []

    def _get_related_model_name(self, model, field_path: str) -> Optional[str]:
        """
        Get the related model name for a nested field path.

        Args:
            model: Base Django model
            field_path: Field path like 'author__username'

        Returns:
            Related model name or None
        """
        try:
            field_parts = field_path.split("__")
            current_model = model

            for field_name in field_parts[:-1]:  # Exclude the final field
                field = current_model._meta.get_field(field_name)
                if hasattr(field, "related_model"):
                    current_model = field.related_model
                else:
                    return None

            return current_model.__name__
        except:
            return None

    def _translate_help_text_to_french(
        self, original_text: str, verbose_name: str
    ) -> str:
        """
        Translate help text to French using field verbose_name.

        Args:
            original_text: Original English help text
            verbose_name: Field verbose name to use in translation

        Returns:
            French translated help text
        """
        # Basic translation mapping
        translations = {
            "exact": f"Correspondance exacte pour {verbose_name}",
            "iexact": f"Correspondance exacte insensible à la casse pour {verbose_name}",
            "contains": f"Contient le texte dans {verbose_name}",
            "icontains": f"Contient le texte (insensible à la casse) dans {verbose_name}",
            "startswith": f"Commence par le texte dans {verbose_name}",
            "istartswith": f"Commence par le texte (insensible à la casse) dans {verbose_name}",
            "endswith": f"Se termine par le texte dans {verbose_name}",
            "iendswith": f"Se termine par le texte (insensible à la casse) dans {verbose_name}",
            "in": f"Correspond à l'une des valeurs fournies pour {verbose_name}",
            "gt": f"Supérieur à la valeur pour {verbose_name}",
            "gte": f"Supérieur ou égal à la valeur pour {verbose_name}",
            "lt": f"Inférieur à la valeur pour {verbose_name}",
            "lte": f"Inférieur ou égal à la valeur pour {verbose_name}",
            "range": f"Valeur dans la plage pour {verbose_name}",
            "isnull": f"Vérifier si {verbose_name} est nul",
            "today": f"Filtrer pour la date d'aujourd'hui dans {verbose_name}",
            "yesterday": f"Filtrer pour la date d'hier dans {verbose_name}",
            "this_week": f"Filtrer pour les dates de cette semaine dans {verbose_name}",
            "this_month": f"Filtrer pour les dates de ce mois dans {verbose_name}",
            "this_year": f"Filtrer pour les dates de cette année dans {verbose_name}",
            "year": f"Filtrer par année pour {verbose_name}",
            "month": f"Filtrer par mois pour {verbose_name}",
            "day": f"Filtrer par jour pour {verbose_name}",
        }

        # Extract lookup expression from original text
        for lookup, french_text in translations.items():
            if lookup in original_text.lower():
                return french_text

        # Fallback: basic translation
        if "exact match" in original_text.lower():
            return f"Correspondance exacte pour {verbose_name}"
        elif "contains" in original_text.lower():
            return f"Contient le texte dans {verbose_name}"
        elif "greater than" in original_text.lower():
            return f"Supérieur à la valeur pour {verbose_name}"
        elif "less than" in original_text.lower():
            return f"Inférieur à la valeur pour {verbose_name}"
        else:
            return f"Filtre pour {verbose_name}"

    @cache_metadata(
        timeout=900, user_specific=False
    )  # 15 minutes cache for mutations metadata (not user-specific)
    def extract_mutations_metadata(
        self, model: Type[models.Model]
    ) -> List[MutationMetadata]:
        """
        Extract mutation metadata for a Django model.

        Args:
            model: Django model class

        Returns:
            List of MutationMetadata objects
        """
        try:
            from ..conf import get_mutation_generator_settings
            from ..generators.mutations import MutationGenerator
            from ..generators.types import TypeGenerator

            mutations = []
            model_name = model.__name__

            # Initialize mutation generator
            type_generator = TypeGenerator(schema_name=self.schema_name)
            mutation_settings = get_mutation_generator_settings(self.schema_name)
            mutation_generator = MutationGenerator(
                type_generator=type_generator,
                settings=mutation_settings,
                schema_name=self.schema_name,
            )

            # Generate CRUD mutations if enabled
            if mutation_settings.enable_create:
                create_mutation = self._extract_create_mutation_metadata(
                    model, mutation_generator
                )
                if create_mutation:
                    mutations.append(create_mutation)

            if mutation_settings.enable_update:
                update_mutation = self._extract_update_mutation_metadata(
                    model, mutation_generator
                )
                if update_mutation:
                    mutations.append(update_mutation)

            if mutation_settings.enable_delete:
                delete_mutation = self._extract_delete_mutation_metadata(
                    model, mutation_generator
                )
                if delete_mutation:
                    mutations.append(delete_mutation)

            # Generate bulk mutations if enabled
            if mutation_settings.enable_bulk_operations:
                bulk_mutations = self._extract_bulk_mutations_metadata(
                    model, mutation_generator
                )
                mutations.extend(bulk_mutations)

            # Generate method mutations if enabled
            if mutation_settings.enable_method_mutations:
                method_mutations = self._extract_method_mutations_metadata(
                    model, mutation_generator
                )
                mutations.extend(method_mutations)

            return mutations

        except Exception as e:
            logger.error(
                f"Error extracting mutations metadata for {model.__name__}: {e}"
            )
            return []

    def _extract_create_mutation_metadata(
        self, model: Type[models.Model], mutation_generator
    ) -> Optional[MutationMetadata]:
        """Extract metadata for create mutation."""
        try:
            model_name = model.__name__
            input_fields = self._extract_input_fields_from_model(model, "create")

            return MutationMetadata(
                name=f"create_{model_name.lower()}",
                description=f"Create a new {model_name} instance",
                input_fields=input_fields,
                return_type=f"{model_name}Type",
                requires_authentication=True,
                required_permissions=[
                    f"{model._meta.app_label}.add_{model._meta.model_name}"
                ],
                mutation_type="create",
                model_name=model_name,
                success_message=f"{model_name} created successfully",
                form_config={
                    "title": f"Create {model_name}",
                    "submit_text": "Create",
                    "cancel_text": "Cancel",
                },
            )
        except Exception as e:
            logger.error(f"Error extracting create mutation metadata: {e}")
            return None

    def _extract_update_mutation_metadata(
        self, model: Type[models.Model], mutation_generator
    ) -> Optional[MutationMetadata]:
        """Extract metadata for update mutation."""
        try:
            model_name = model.__name__
            input_fields = self._extract_input_fields_from_model(model, "update")

            # Add ID field for update
            id_field = InputFieldMetadata(
                name="id",
                field_type="ID",
                required=True,
                description=f"ID of the {model_name} to update",
                widget_type="hidden",
            )
            input_fields.insert(0, id_field)

            return MutationMetadata(
                name=f"update_{model_name.lower()}",
                description=f"Update an existing {model_name} instance",
                input_fields=input_fields,
                return_type=f"{model_name}Type",
                requires_authentication=True,
                required_permissions=[f"change_{model._meta.model_name}"],
                mutation_type="update",
                model_name=model_name,
                success_message=f"{model_name} updated successfully",
                form_config={
                    "title": f"Update {model_name}",
                    "submit_text": "Update",
                    "cancel_text": "Cancel",
                },
            )
        except Exception as e:
            logger.error(f"Error extracting update mutation metadata: {e}")
            return None

    def _extract_delete_mutation_metadata(
        self, model: Type[models.Model], mutation_generator
    ) -> Optional[MutationMetadata]:
        """Extract metadata for delete mutation."""
        try:
            model_name = model.__name__

            id_field = InputFieldMetadata(
                name="id",
                field_type="ID",
                required=True,
                description=f"ID of the {model_name} to delete",
                widget_type="hidden",
            )

            return MutationMetadata(
                name=f"delete_{model_name.lower()}",
                description=f"Delete a {model_name} instance",
                input_fields=[id_field],
                return_type="Boolean",
                requires_authentication=True,
                required_permissions=[f"delete_{model._meta.model_name}"],
                mutation_type="delete",
                model_name=model_name,
                success_message=f"{model_name} deleted successfully",
                form_config={
                    "title": f"Delete {model_name}",
                    "submit_text": "Delete",
                    "cancel_text": "Cancel",
                    "confirmation_required": True,
                    "confirmation_message": f"Are you sure you want to delete this {model_name}?",
                },
            )
        except Exception as e:
            logger.error(f"Error extracting delete mutation metadata: {e}")
            return None

    def _extract_bulk_mutations_metadata(
        self, model: Type[models.Model], mutation_generator
    ) -> List[MutationMetadata]:
        """Extract metadata for bulk mutations."""
        mutations = []
        model_name = model.__name__

        try:
            # Bulk create
            input_fields = self._extract_input_fields_from_model(model, "create")
            bulk_create = MutationMetadata(
                name=f"bulk_create_{model_name.lower()}",
                description=f"Create multiple {model_name} instances",
                input_fields=[
                    InputFieldMetadata(
                        name="objects",
                        field_type="List",
                        required=True,
                        description=f"List of {model_name} objects to create",
                        multiple=True,
                    )
                ],
                return_type=f"List[{model_name}Type]",
                requires_authentication=True,
                required_permissions=[f"add_{model._meta.model_name}"],
                mutation_type="bulk_create",
                model_name=model_name,
                success_message=f"Multiple {model_name} instances created successfully",
            )
            mutations.append(bulk_create)

            # Bulk update
            bulk_update = MutationMetadata(
                name=f"bulk_update_{model_name.lower()}",
                description=f"Update multiple {model_name} instances",
                input_fields=[
                    InputFieldMetadata(
                        name="objects",
                        field_type="List",
                        required=True,
                        description=f"List of {model_name} objects to update",
                        multiple=True,
                    )
                ],
                return_type=f"List[{model_name}Type]",
                requires_authentication=True,
                required_permissions=[f"change_{model._meta.model_name}"],
                mutation_type="bulk_update",
                model_name=model_name,
                success_message=f"Multiple {model_name} instances updated successfully",
            )
            mutations.append(bulk_update)

            # Bulk delete
            bulk_delete = MutationMetadata(
                name=f"bulk_delete_{model_name.lower()}",
                description=f"Delete multiple {model_name} instances",
                input_fields=[
                    InputFieldMetadata(
                        name="ids",
                        field_type="List[ID]",
                        required=True,
                        description=f"List of {model_name} IDs to delete",
                        multiple=True,
                    )
                ],
                return_type="Boolean",
                requires_authentication=True,
                required_permissions=[f"delete_{model._meta.model_name}"],
                mutation_type="bulk_delete",
                model_name=model_name,
                success_message=f"Multiple {model_name} instances deleted successfully",
            )
            mutations.append(bulk_delete)

        except Exception as e:
            logger.error(f"Error extracting bulk mutations metadata: {e}")

        return mutations

    def _extract_method_mutations_metadata(
        self, model: Type[models.Model], mutation_generator
    ) -> List[MutationMetadata]:
        """Extract metadata for method-based mutations."""
        mutations = []

        try:
            from ..generators.introspector import ModelIntrospector

            introspector = ModelIntrospector(model)
            model_methods = introspector.get_model_methods()

            for method_name, method_info in model_methods.items():
                if method_info.is_mutation and not method_info.is_private:
                    method_mutation = self._extract_method_mutation_metadata(
                        model, method_name, method_info
                    )
                    if method_mutation:
                        mutations.append(method_mutation)

        except Exception as e:
            logger.error(f"Error extracting method mutations metadata: {e}")

        return mutations

    def _extract_method_mutation_metadata(
        self, model: Type[models.Model], method_name: str, method_info
    ) -> Optional[MutationMetadata]:
        """Extract metadata for a specific method mutation."""
        try:
            model_name = model.__name__
            method = getattr(model, method_name)

            # Extract input fields from method signature
            input_fields = self._extract_input_fields_from_method(method)

            # Get custom attributes from decorators
            description = getattr(method, "_mutation_description", method.__doc__)
            custom_name = getattr(method, "_custom_mutation_name", None)
            requires_permission = getattr(method, "_requires_permission", None)

            mutation_name = custom_name or f"{model_name.lower()}_{method_name}"

            return MutationMetadata(
                name=mutation_name,
                description=description or f"Execute {method_name} on {model_name}",
                input_fields=input_fields,
                return_type="JSONString",
                requires_authentication=True,
                required_permissions=[requires_permission]
                if requires_permission
                else [],
                mutation_type="custom",
                model_name=model_name,
                success_message=f"{method_name} executed successfully",
            )

        except Exception as e:
            logger.error(f"Error extracting method mutation metadata: {e}")
            return None

    def _extract_input_fields_from_model(
        self, model: Type[models.Model], mutation_type: str
    ) -> List[InputFieldMetadata]:
        """Extract input fields from Django model fields."""
        input_fields = []

        for field in model._meta.fields:
            # Skip auto fields and primary keys for create mutations
            if getattr(field, "primary_key", None) and mutation_type == "create":
                continue

            # Skip auto-generated fields
            if hasattr(field, "auto_now") or hasattr(field, "auto_now_add"):
                continue

            input_field = self._convert_django_field_to_input_metadata(
                field, mutation_type
            )
            if input_field:
                input_fields.append(input_field)

        return input_fields

    def _convert_django_field_to_input_metadata(
        self, field, mutation_type: str
    ) -> Optional[InputFieldMetadata]:
        """Convert Django field to InputFieldMetadata."""
        try:
            from django.db import models

            field_name = field.name
            field_type = "String"  # Default
            required = (
                not field.null and not field.blank and not hasattr(field, "default")
            )

            # For update mutations, make fields optional
            if mutation_type == "update":
                required = False

            # Map Django field types to GraphQL types
            if isinstance(field, models.CharField):
                field_type = "String"
            elif isinstance(field, models.TextField):
                field_type = "String"
            elif isinstance(field, models.IntegerField):
                field_type = "Int"
            elif isinstance(field, models.FloatField):
                field_type = "Float"
            elif isinstance(field, models.BooleanField):
                field_type = "Boolean"
            elif isinstance(field, models.DateTimeField):
                field_type = "DateTime"
            elif isinstance(field, models.DateField):
                field_type = "Date"
            elif isinstance(field, models.EmailField):
                field_type = "String"
            elif isinstance(field, models.URLField):
                field_type = "String"
            elif isinstance(field, models.ForeignKey):
                field_type = "ID"
            elif isinstance(field, models.ManyToManyField):
                field_type = "List[ID]"

            # Get choices if available
            choices = None
            if hasattr(field, "choices") and field.choices:
                choices = [
                    {"value": choice[0], "label": choice[1]} for choice in field.choices
                ]

            # Determine widget type
            widget_type = self._get_widget_type_for_field(field)

            return InputFieldMetadata(
                name=field_name,
                field_type=field_type,
                required=required,
                description=str(field.verbose_name)
                if hasattr(field, "verbose_name")
                else None,
                choices=choices,
                widget_type=widget_type,
                help_text=str(field.help_text)
                if hasattr(field, "help_text") and field.help_text
                else None,
                max_length=getattr(field, "max_length", None),
                related_model=field.related_model.__name__
                if hasattr(field, "related_model") and field.related_model
                else None,
                multiple=isinstance(field, models.ManyToManyField),
            )

        except Exception as e:
            logger.error(f"Error converting field {field.name}: {e}")
            return None

    def _get_widget_type_for_field(self, field) -> str:
        """Determine the appropriate widget type for a Django field."""
        from django.db import models

        if isinstance(field, models.TextField):
            return "textarea"
        elif isinstance(field, models.EmailField):
            return "email"
        elif isinstance(field, models.URLField):
            return "url"
        elif isinstance(field, models.BooleanField):
            return "checkbox"
        elif isinstance(field, models.DateTimeField):
            return "datetime-local"
        elif isinstance(field, models.DateField):
            return "date"
        elif isinstance(field, models.IntegerField):
            return "number"
        elif isinstance(field, models.FloatField):
            return "number"
        elif isinstance(field, models.ForeignKey):
            return "select"
        elif isinstance(field, models.ManyToManyField):
            return "multiselect"
        elif hasattr(field, "choices") and field.choices:
            return "select"
        else:
            return "text"

    def _extract_input_fields_from_method(self, method) -> List[InputFieldMetadata]:
        """Extract input fields from method signature."""
        import inspect

        input_fields = []
        signature = inspect.signature(method)

        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue

            field_type = "String"  # Default
            required = param.default == inspect.Parameter.empty
            default_value = (
                param.default if param.default != inspect.Parameter.empty else None
            )

            # Try to infer type from annotation
            if param.annotation != inspect.Parameter.empty:
                annotation = param.annotation
                if annotation == int:
                    field_type = "Int"
                elif annotation == float:
                    field_type = "Float"
                elif annotation == bool:
                    field_type = "Boolean"
                elif hasattr(annotation, "__origin__"):
                    if annotation.__origin__ == list:
                        field_type = "List[String]"

            input_field = InputFieldMetadata(
                name=param_name,
                field_type=field_type,
                required=required,
                default_value=default_value,
                description=f"Parameter {param_name} for method execution",
            )
            input_fields.append(input_field)

        return input_fields


class ModelFormMetadataExtractor:
    """
    Extractor for Django model form metadata, providing all necessary information
    to construct forms on the frontend.
    """

    def __init__(self, schema_name: str = "default", max_depth: int = 1):
        """
        Initialize the form metadata extractor.

        Args:
            schema_name: Name of the schema configuration to use
            max_depth: Maximum depth for nested related model metadata
        """
        self.schema_name = schema_name
        self.max_depth = max_depth

    @cache_metadata(
        timeout=1200, user_specific=True
    )  # 20 minutes cache for form field metadata
    def _extract_form_field_metadata(self, field, user) -> Optional[FormFieldMetadata]:
        """
        Extract form-specific metadata for a single field with permission checking.

        Args:
            field: Django model field instance
            user: User instance for permission checking

        Returns:
            FormFieldMetadata if user has permission, None otherwise
        """
        from django.db import models

        # Get field choices
        choices = None
        if hasattr(field, "choices") and field.choices:
            choices = [
                {"value": choice[0], "label": choice[1]} for choice in field.choices
            ]

        # Determine widget type based on field type
        widget_type = self._get_form_widget_type(field)

        # Generate placeholder text
        placeholder = self._generate_placeholder(field)

        # Get validation attributes
        max_length = getattr(field, "max_length", None)
        min_length = (
            getattr(field, "min_length", None) if hasattr(field, "min_length") else None
        )
        max_value = (
            getattr(field, "max_value", None) if hasattr(field, "max_value") else None
        )
        min_value = (
            getattr(field, "min_value", None) if hasattr(field, "min_value") else None
        )

        # Handle decimal fields
        decimal_places = getattr(field, "decimal_places", None)
        max_digits = getattr(field, "max_digits", None)

        # Determine if field is required for forms (different from database nullable)
        is_required = not field.blank and field.default == models.NOT_PROVIDED

        # Get default value for forms
        default_value = None
        if field.default != models.NOT_PROVIDED:
            if callable(field.default):
                try:
                    default_value = field.default()
                except:
                    default_value = None
            else:
                default_value = field.default

        # Check field permissions using the model from the field
        model = field.model
        has_permission = self._has_field_permission(user, model, field.name)

        return FormFieldMetadata(
            name=field.name,
            field_type=field.__class__.__name__,
            is_required=is_required,
            verbose_name=str(field.verbose_name),
            help_text=field.help_text or "",
            widget_type=widget_type,
            placeholder=placeholder,
            default_value=default_value,
            choices=choices,
            max_length=max_length,
            min_length=min_length,
            decimal_places=decimal_places,
            max_digits=max_digits,
            min_value=min_value,
            max_value=max_value,
            auto_now=getattr(field, "auto_now", False),
            auto_now_add=getattr(field, "auto_now_add", False),
            blank=field.blank,
            null=field.null,
            unique=field.unique,
            editable=field.editable,
            validators=[],  # TODO: Extract validators
            error_messages={},  # TODO: Extract error messages
            has_permission=has_permission,
            disabled=not field.editable,
            readonly=not field.editable or getattr(field, "primary_key", None),
            css_classes=self._get_css_classes(field),
            data_attributes=self._get_data_attributes(field),
        )

    @cache_metadata(
        timeout=1200, user_specific=True
    )  # 20 minutes cache for form relationship metadata
    def _extract_form_relationship_metadata(
        self, field, user, current_depth: int = 0, visited_models: set = None
    ) -> Optional[FormRelationshipMetadata]:
        """
        Extract form-specific metadata for relationship fields.

        Args:
            field: Django relationship field instance
            user: User instance for permission checking
            current_depth: Current nesting depth

        Returns:
            FormRelationshipMetadata if user has permission, None otherwise
        """
        from django.db import models

        related_model = field.related_model

        if related_model is None or not hasattr(related_model, "_meta"):
            return None

        related_app_label = getattr(related_model._meta, "app_label", "")
        related_model_class_name = related_model.__name__

        # Check recursion depth to prevent infinite loops in circular relationships
        if current_depth >= self.max_depth:
            # Return basic relationship metadata without nested form data
            pass
        else:
            # Build embedded related model form metadata only if within depth limit
            embedded_related = self.extract_model_form_metadata(
                app_name=related_app_label,
                model_name=related_model_class_name,
                user=user,
                nested_fields=[],  # No nested fields for relationships by default
                current_depth=current_depth + 1,
                visited_models=visited_models,
            )

            if embedded_related is None:
                return None

        # Determine widget type for relationship
        widget_type = self._get_relationship_widget_type(field)

        # Check permission for relationship field
        model = field.model
        has_permission = self._has_field_permission(user, model, field.name)

        # Handle verbose_name for reverse relationships
        if hasattr(field, "verbose_name"):
            verbose_name = str(field.verbose_name)
        else:
            # For reverse relationships like ManyToOneRel, generate a readable name
            verbose_name = field.name.replace("_", " ").title()

        return FormRelationshipMetadata(
            name=field.name,
            relationship_type=field.__class__.__name__,
            verbose_name=verbose_name,
            help_text=getattr(field, "help_text", "") or "",
            widget_type=widget_type,
            is_required=not getattr(field, "blank", True),
            related_model=related_model_class_name,
            related_app=related_app_label,
            to_field=field.remote_field.name
            if hasattr(field, "remote_field") and field.remote_field
            else None,
            from_field=field.name,
            many_to_many=isinstance(field, models.ManyToManyField),
            one_to_one=isinstance(field, models.OneToOneField),
            foreign_key=isinstance(field, models.ForeignKey),
            is_reverse=False,
            multiple=isinstance(field, models.ManyToManyField),
            queryset_filters=self._get_queryset_filters(field),
            empty_label=self._get_empty_label(field),
            limit_choices_to=getattr(field, "limit_choices_to", None),
            has_permission=has_permission,
            disabled=not field.editable,
            readonly=not field.editable or getattr(field, "primary_key", None),
            css_classes=self._get_css_classes(field),
            data_attributes=self._get_data_attributes(field),
        )

    @cache_metadata(
        timeout=1800, user_specific=False
    )  # 30 minutes cache for complete model form metadata
    def extract_model_form_metadata(
        self,
        app_name: str,
        model_name: str,
        user,
        nested_fields: List[str] = None,
        current_depth: int = 0,
        visited_models: set = None,
    ) -> Optional[ModelFormMetadata]:
        """
        Extract comprehensive form metadata for a Django model.

        Args:
            app_name: Django app name
            model_name: Model class name
            user: User instance for permission checking
            nested_fields: List of field names to include nested metadata for
            current_depth: Current nesting depth
            visited_models: Set of already visited models to prevent circular references

        Returns:
            ModelFormMetadata with all form-specific information
        """
        # Initialize visited models set if not provided
        if visited_models is None:
            visited_models = set()

        # Create a unique identifier for this model
        model_key = f"{app_name}.{model_name}"

        # Check if we've already visited this model to prevent infinite recursion
        if model_key in visited_models:
            logger.warning(
                f"Circular reference detected for model {model_key}, skipping to prevent infinite recursion"
            )
            return None

        # Add current model to visited set
        visited_models.add(model_key)

        try:
            model = apps.get_model(app_name, model_name)
        except (LookupError, ValueError) as e:
            logger.error(f"Model {app_name}.{model_name} not found: {e}")
            visited_models.discard(model_key)  # Remove from visited set on error
            return None

        if not model or not hasattr(model, "_meta"):
            visited_models.discard(model_key)  # Remove from visited set on error
            return None

        meta = model._meta
        nested_fields = nested_fields or []

        # Extract form fields
        form_fields = []
        form_relationships = []

        for field in meta.get_fields():
            # Check if this is a relationship field
            if hasattr(field, "related_model") and field.related_model:
                # Always include relationship fields regardless of nested_fields
                relationship_metadata = self._extract_form_relationship_metadata(
                    field, user, current_depth, visited_models
                )
                if relationship_metadata:
                    form_relationships.append(relationship_metadata)
            else:
                # This is a regular field
                if not field.name.startswith("_") and field.concrete:
                    field_metadata = self._extract_form_field_metadata(field, user)
                    if field_metadata:
                        form_fields.append(field_metadata)

        # Get form configuration
        form_title = f"Form for {meta.verbose_name}"
        form_description = f"Create or edit {meta.verbose_name.lower()}"

        # Get field ordering
        field_order = list(getattr(meta, "field_order", []))
        if not field_order:
            field_order = [f.name for f in form_fields]

        # Get excluded fields (typically auto fields, computed fields)
        exclude_fields = []
        readonly_fields = []

        for field in meta.get_fields():
            if (
                field.auto_created
                or (hasattr(field, "auto_now") and field.auto_now)
                or (hasattr(field, "auto_now_add") and field.auto_now_add)
            ):
                exclude_fields.append(field.name)

            if getattr(field, "primary_key", None) or not field.editable:
                readonly_fields.append(field.name)

        # Required permissions (simplified)
        required_permissions = [
            f"{app_name}.add_{model_name.lower()}",
            f"{app_name}.change_{model_name.lower()}",
        ]

        # Extract nested metadata for specified fields
        nested_metadata = []
        if nested_fields and current_depth < self.max_depth:
            for field_name in nested_fields:
                try:
                    field = meta.get_field(field_name)
                    if hasattr(field, "related_model") and field.related_model:
                        related_model = field.related_model
                        related_meta = related_model._meta

                        # Extract nested form metadata for the related model
                        nested_form_metadata = self.extract_model_form_metadata(
                            app_name=related_meta.app_label,
                            model_name=related_model.__name__,
                            user=user,
                            nested_fields=[],  # Don't go deeper to avoid infinite recursion
                            current_depth=current_depth + 1,
                            visited_models=visited_models.copy(),  # Pass a copy to avoid affecting parent
                        )

                        if nested_form_metadata:
                            nested_metadata.append(nested_form_metadata)
                except Exception as e:
                    logger.warning(
                        f"Could not extract nested metadata for field {field_name}: {e}"
                    )

        # Remove current model from visited set before returning (cleanup)
        visited_models.discard(model_key)

        return ModelFormMetadata(
            app_name=app_name,
            model_name=model_name,
            verbose_name=str(meta.verbose_name),
            verbose_name_plural=str(meta.verbose_name_plural),
            form_title=form_title,
            form_description=form_description,
            fields=form_fields,
            relationships=form_relationships,
            nested=nested_metadata,
            field_order=field_order,
            exclude_fields=exclude_fields,
            readonly_fields=readonly_fields,
            required_permissions=required_permissions,
            form_validation_rules=self._get_form_validation_rules(model),
            form_layout=self._get_form_layout(model),
            css_classes=self._get_form_css_classes(model),
            form_attributes=self._get_form_attributes(model),
        )

    def _get_form_widget_type(self, field) -> str:
        """Get the recommended widget type for a form field."""
        from django.db import models

        widget_mapping = {
            models.CharField: "text",
            models.TextField: "textarea",
            models.EmailField: "email",
            models.URLField: "url",
            models.IntegerField: "number",
            models.FloatField: "number",
            models.DecimalField: "number",
            models.BooleanField: "checkbox",
            models.DateField: "date",
            models.DateTimeField: "datetime-local",
            models.TimeField: "time",
            models.FileField: "file",
            models.ImageField: "file",
            models.ForeignKey: "select",
            models.ManyToManyField: "select",
            models.OneToOneField: "select",
        }

        # Check for choices first
        if hasattr(field, "choices") and field.choices:
            return "select"

        return widget_mapping.get(field.__class__, "text")

    def _get_relationship_widget_type(self, field) -> str:
        """Get the recommended widget type for relationship fields."""
        from django.db import models

        if isinstance(field, models.ManyToManyField):
            return "multiselect"
        elif isinstance(field, (models.ForeignKey, models.OneToOneField)):
            return "select"

        return "select"

    def _generate_placeholder(self, field) -> Optional[str]:
        """Generate placeholder text for form fields."""
        if hasattr(field, "help_text") and field.help_text:
            return field.help_text

        return f"Enter {field.verbose_name.lower()}"

    def _get_queryset_filters(self, field) -> Optional[Dict[str, Any]]:
        """Get queryset filters for relationship fields."""
        if hasattr(field, "limit_choices_to") and field.limit_choices_to:
            return field.limit_choices_to
        return None

    def _get_empty_label(self, field) -> Optional[str]:
        """Get empty label for choice fields."""
        if hasattr(field, "choices") and field.choices:
            return f"Select {field.verbose_name.lower()}"
        return None

    def _get_css_classes(self, field) -> Optional[str]:
        """Get CSS classes for form fields."""
        from django.db import models

        classes = ["form-control"]

        if isinstance(field, models.TextField):
            classes.append("form-textarea")
        elif isinstance(
            field, (models.DateField, models.DateTimeField, models.TimeField)
        ):
            classes.append("form-date")
        elif isinstance(
            field, (models.IntegerField, models.FloatField, models.DecimalField)
        ):
            classes.append("form-number")
        elif isinstance(field, models.BooleanField):
            classes.append("form-checkbox")
        elif isinstance(field, (models.FileField, models.ImageField)):
            classes.append("form-file")

        if getattr(field, "primary_key", None):
            classes.append("form-readonly")

        return " ".join(classes)

    def _get_data_attributes(self, field) -> Optional[Dict[str, Any]]:
        """Get data attributes for form fields."""
        attributes = {}

        if hasattr(field, "max_length") and field.max_length:
            attributes["maxlength"] = field.max_length

        if hasattr(field, "min_length") and field.min_length:
            attributes["minlength"] = field.min_length

        return attributes if attributes else None

    def _get_form_validation_rules(self, model) -> Optional[Dict[str, Any]]:
        """Get form validation rules for the model."""
        return {
            "validate_on_blur": True,
            "validate_on_change": True,
            "show_errors_inline": True,
        }

    def _get_form_layout(self, model) -> Optional[Dict[str, Any]]:
        """Get form layout configuration."""
        return {
            "layout_type": "vertical",
            "field_spacing": "medium",
            "group_related_fields": True,
        }

    def _get_form_css_classes(self, model) -> Optional[str]:
        """Get CSS classes for the form."""
        return f"model-form {model._meta.app_label}-{model._meta.model_name}-form"

    def _get_form_attributes(self, model) -> Optional[Dict[str, Any]]:
        """Get form HTML attributes."""
        return {
            "novalidate": False,
            "autocomplete": "on",
            "data-model": f"{model._meta.app_label}.{model._meta.model_name}",
        }

    def _has_field_permission(self, user, model: type, field_name: str) -> bool:
        """
        Check if user has permission to access a specific field in forms.

        Args:
            user: The user to check permissions for
            model: The Django model class
            field_name: The name of the field to check

        Returns:
            bool: True if user has permission, False otherwise
        """
        # Anonymous users have no field permissions
        if not user or not user.is_authenticated:
            return False

        # Superusers have access to all fields
        if user.is_superuser:
            return True

        # Check if user has view permission for the model
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        view_permission = f"{app_label}.view_{model_name}"

        return user.has_perm(view_permission)


class ModelTableExtractor:
    """Extractor for comprehensive table metadata including fields and filters."""

    def __init__(self, schema_name: str = "default"):
        self.schema_name = schema_name

    def _get_model(self, app_name: str, model_name: str):
        try:
            return apps.get_model(app_name, model_name)
        except Exception as e:
            logger.error(
                "Model '%s' not found in app '%s': %s", model_name, app_name, e
            )
            return None

    def _build_table_field_from_django_field(self, field) -> TableFieldMetadata:
        from django.db import models

        field_type = field.__class__.__name__
        title = str(getattr(field, "verbose_name", field.name))
        help_text = str(getattr(field, "help_text", ""))
        is_related = isinstance(
            field, (models.ForeignKey, models.OneToOneField, models.ManyToManyField)
        )

        return TableFieldMetadata(
            name=field.name,
            accessor=field.name,
            display=f"{field.name}.desc" if is_related else field.name,
            editable=getattr(field, "editable", True),
            field_type=field_type,
            filterable=True,
            sortable=True,
            title=title,
            helpText=help_text,
            is_property=False,
            is_related=is_related,
        )

    def _build_table_field_for_property(
        self,
        prop_name: str,
        return_type,
        verbose_name: Optional[str] = None,
    ) -> TableFieldMetadata:
        import inspect
        from datetime import date, datetime, time
        from typing import Any, List, Union, get_args, get_origin

        def _to_graphql_str(py_type: Any) -> str:
            # Handle missing or Any annotations
            if py_type is Any or py_type is None or py_type is inspect._empty:
                return "String"

            # Base type mappings consistent with type generation
            base_map = {
                str: "String",
                int: "Int",
                float: "Float",
                bool: "Boolean",
                date: "Date",
                datetime: "DateTime",
                time: "Time",
            }

            # Dict and JSON-like types
            if py_type in (dict,):
                return "JSON"

            origin = get_origin(py_type)
            if origin is Union:
                # Optional/Union: pick first non-None type
                args = [arg for arg in get_args(py_type) if arg is not type(None)]
                return _to_graphql_str(args[0]) if args else "String"

            if origin in (list, List):
                args = get_args(py_type)
                inner = _to_graphql_str(args[0]) if args else "String"
                return f"List[{inner}]"

            if origin in (dict,):
                return "JSON"

            return base_map.get(py_type, "String")

        field_type_str = _to_graphql_str(return_type)
        return TableFieldMetadata(
            name=prop_name,
            accessor=prop_name,
            display=prop_name,
            editable=False,
            field_type=field_type_str,
            filterable=True,
            sortable=True,
            title=str(verbose_name or prop_name),
            helpText=f"Computed property ({field_type_str})",
            is_property=True,
            is_related=False,
        )

    def _build_table_field_for_reverse_count(
        self, introspector, model
    ) -> TableFieldMetadata:
        counts = []
        reverse_relations = introspector.get_manytoone_relations()
        for rel_name, related_model in reverse_relations.items():
            counts.append(
                TableFieldMetadata(
                    name=f"{rel_name}_count",
                    accessor=f"{rel_name}_count",
                    display=f"{rel_name}_count",
                    editable=False,
                    field_type="Count",
                    filterable=True,
                    sortable=True,
                    title=f"Related items count ({rel_name})",
                    helpText=f"Number of related reverse objects ({rel_name})",
                    is_property=False,
                    is_related=False,
                )
            )
        for field in model._meta.get_fields():
            if isinstance(field, models.ManyToManyField):
                counts.append(
                    TableFieldMetadata(
                        name=f"{field.name}_count",
                        accessor=f"{rel_name}_count",
                        display=f"{rel_name}_count",
                        editable=False,
                        field_type="Count",
                        filterable=True,
                        sortable=True,
                        title=f"Related items count ({field.verbose_name})",
                        helpText=f"Number of related reverse objects ({field.verbose_name})",
                        is_property=False,
                        is_related=False,
                    )
                )
        return counts

    def _translate_help_text_to_french(
        self, lookup_expr: str, verbose_name: str
    ) -> str:
        """
        Translate a lookup expression into French help text using the field verbose name.

        Purpose: Provide consistent help text for filter options in table metadata.
        Args:
            lookup_expr: Django lookup expression (e.g., 'exact', 'icontains')
            verbose_name: Human-readable field name to include in the message
        Returns:
            Translated help text string.
        """
        translations = {
            "exact": f"Correspondance exacte pour {verbose_name}",
            "iexact": f"Correspondance exacte insensible à la casse pour {verbose_name}",
            "contains": f"Contient le texte dans {verbose_name}",
            "icontains": f"Contient le texte (insensible à la casse) dans {verbose_name}",
            "startswith": f"Commence par le texte dans {verbose_name}",
            "istartswith": f"Commence par le texte (insensible à la casse) dans {verbose_name}",
            "endswith": f"Se termine par le texte dans {verbose_name}",
            "iendswith": f"Se termine par le texte (insensible à la casse) dans {verbose_name}",
            "in": f"Correspond à l'une des valeurs fournies pour {verbose_name}",
            "gt": f"Supérieur à la valeur pour {verbose_name}",
            "gte": f"Supérieur ou égal à la valeur pour {verbose_name}",
            "lt": f"Inférieur à la valeur pour {verbose_name}",
            "lte": f"Inférieur ou égal à la valeur pour {verbose_name}",
            "range": f"Valeur dans la plage pour {verbose_name}",
            "isnull": f"Vérifier si {verbose_name} est nul",
            "today": f"Filtrer pour la date d'aujourd'hui dans {verbose_name}",
            "yesterday": f"Filtrer pour la date d'hier dans {verbose_name}",
            "this_week": f"Filtrer pour les dates de cette semaine dans {verbose_name}",
            "this_month": f"Filtrer pour les dates de ce mois dans {verbose_name}",
            "this_year": f"Filtrer pour les dates de cette année dans {verbose_name}",
            "year": f"Filtrer par année pour {verbose_name}",
            "month": f"Filtrer par mois pour {verbose_name}",
            "day": f"Filtrer par jour pour {verbose_name}",
        }
        return translations.get(
            lookup_expr, f"Filtre '{lookup_expr}' pour {verbose_name}"
        )

    # Custom fields for table metadata are no longer supported and have been removed.

    @cache_metadata(timeout=1, user_specific=False)
    def extract_model_table_metadata(
        self,
        app_name: str,
        model_name: str,
        custom_fields: Optional[List[str]] = None,
        counts: bool = False,
        user=None,
    ) -> Optional[ModelTableMetadata]:
        # TTL cache lookup for model_table metadata
        try:
            cache_key = _make_table_cache_key(
                self.schema_name,
                app_name,
                model_name,
                counts,
            )
            now = time.time()
            with _table_cache_lock:
                entry = _table_cache.get(cache_key)
                if entry and entry.get("expires_at", 0) > now:
                    _table_cache_stats["hits"] += 1
                    cached = entry.get("value")
                    if cached is not None:
                        return cached
                _table_cache_stats["misses"] += 1
        except Exception:
            # Do not fail metadata resolution due to cache issues
            pass

        model = self._get_model(app_name, model_name)
        if not model:
            return None

        meta = model._meta
        introspector = ModelIntrospector(model, self.schema_name)

        # Detect polymorphic/multi-table inheritance and hide OneToOne relations
        # to avoid exposing parent/child or sibling pointers in table columns.
        # This is especially relevant for django-polymorphic where child models
        # include an auto-managed OneToOne link to the base model and projects
        # may define additional OneToOne links between siblings.
        try:
            from ..generators.inheritance import inheritance_handler

            inheritance_info = inheritance_handler.analyze_model_inheritance(model)
        except Exception:
            inheritance_info = {}

        # Basic heuristic: presence of polymorphic_ctype field, any parents, or any children
        is_polymorphic_model = False
        try:
            for _f in meta.get_fields():
                if getattr(_f, "name", None) == "polymorphic_ctype":
                    is_polymorphic_model = True
                    break
        except Exception:
            pass

        if getattr(meta, "parents", None):
            try:
                if len(meta.parents) > 0:
                    is_polymorphic_model = True
            except Exception:
                # Some Django versions expose parents as a dict-like
                is_polymorphic_model = True

        if inheritance_info and (
            inheritance_info.get("child_models")
            or inheritance_info.get("concrete_parents")
        ):
            is_polymorphic_model = True

        # Table-level metadata
        app_label = meta.app_label
        model_label = model.__name__
        verbose_name = str(meta.verbose_name)
        verbose_name_plural = str(meta.verbose_name_plural)
        table_name = str(meta.db_table)
        primary_key = meta.pk.name if meta.pk else "id"
        ordering = list(meta.ordering) if getattr(meta, "ordering", None) else []
        # Fallback ordering: latest_by or PK
        if not ordering:
            if getattr(meta, "get_latest_by", None):
                ordering = [f"-{meta.get_latest_by}"]
            else:
                ordering = [primary_key]
        default_ordering = ordering.copy()
        get_latest_by = getattr(meta, "get_latest_by", None)
        managers = [m.name for m in getattr(meta, "managers", [])] or [
            m.name for m in model._meta.managers
        ]
        managed = bool(getattr(meta, "managed", True))

        # Field metadata: include concrete fields
        table_fields: List[TableFieldMetadata] = []

        # For polymorphic models, we need to handle inheritance hierarchy properly
        # to ensure fields from all parent classes are included in child metadata
        if is_polymorphic_model and inheritance_info:
            # Get all fields including inherited ones with proper model attribution
            all_fields = meta.get_fields(include_parents=True)
        else:
            all_fields = meta.get_fields()

        for f in all_fields:
            # Skip auto-created reverse accessors
            if getattr(f, "auto_created", False) and getattr(f, "is_relation", False):
                continue
            # Only include concrete or forward relation fields

            if (
                f.name == "polymorphic_ctype"
                or f.name == "id"
                or f.name.endswith("_ptr")
            ):
                continue

            # In polymorphic/multi-table inheritance contexts, hide OneToOne relations
            # (parent_link or explicit) from table exposure to prevent confusing columns.
            # These links are implementation details rather than user-facing table fields.
            if is_polymorphic_model and isinstance(f, models.OneToOneField):
                continue

            if getattr(f, "concrete", False) or (
                getattr(f, "is_relation", False)
                and not getattr(f, "auto_created", False)
            ):
                try:
                    table_fields.append(self._build_table_field_from_django_field(f))
                except Exception as e:
                    logger.warning(f"Unable to build field metadata for {f.name}: {e}")
        # Properties from introspector should not surface polymorphic/internal links
        # In polymorphic/multi-table inheritance contexts, also hide properties that
        # correspond to OneToOne relations (parent_link or explicit), as they are
        # implementation details rather than user-facing table fields.
        try:
            properties_dict = getattr(introspector, "properties", {}) or {}
            # Build a set of OneToOne relation names and reverse accessor names
            # to filter property exposure in polymorphic contexts
            one_to_one_relation_names = set()
            reverse_relation_names = set()
            try:
                relationships_dict = getattr(introspector, "relationships", {}) or {}
                for rel_name, rel_info in relationships_dict.items():
                    if getattr(rel_info, "relationship_type", "") == "OneToOneField":
                        one_to_one_relation_names.add(rel_name)
            except Exception:
                # Be resilient if relationships are not available
                pass

            # Collect reverse relation accessor names (includes reverse OneToOne)
            try:
                if hasattr(introspector, "get_reverse_relations"):
                    reverse_relations = introspector.get_reverse_relations() or {}
                    for accessor_name in reverse_relations.keys():
                        reverse_relation_names.add(str(accessor_name))
            except Exception:
                pass

            existing_names = {getattr(tf, "name", None) for tf in table_fields}
            for prop_name, prop_info in properties_dict.items():
                # Skip internal/polymorphic properties and duplicates
                if (
                    prop_name == "pk"
                    or prop_name == "polymorphic_ctype"
                    or str(prop_name).endswith("_ptr")
                    or (
                        is_polymorphic_model
                        and (
                            prop_name in one_to_one_relation_names
                            or prop_name in reverse_relation_names
                        )
                    )
                ):
                    continue

                if prop_name in existing_names:
                    # Avoid duplicating a field already captured from Django model fields
                    continue

                verbose = getattr(prop_info, "verbose_name", prop_name)
                return_type = getattr(prop_info, "return_type", None)
                table_fields.append(
                    self._build_table_field_for_property(
                        prop_name, return_type, verbose
                    )
                )
        except Exception as E:
            # Properties may not be available; ignore quietly
            logger.debug(f"Properties extraction unavailable for {model.__name__}: {E}")
            pass

        # Reverse relationship count field if counts is True
        if counts:
            table_fields.extend(
                self._build_table_field_for_reverse_count(introspector, model)
            )
        # Filters: exclusively use AdvancedFilterGenerator for table filter extraction
        filters: List[Dict[str, Any]] = []
        try:
            from ..generators.filters import AdvancedFilterGenerator

            filter_generator = AdvancedFilterGenerator(
                enable_nested_filters=True, schema_name=self.schema_name
            )
            filter_class = filter_generator.generate_filter_set(model)

            # Collect property metadata to label property-based filters
            try:
                properties_dict = getattr(introspector, "properties", {}) or {}
            except Exception:
                properties_dict = {}

            grouped_filter_dict: Dict[str, Dict[str, Any]] = {}
            base_filters = getattr(filter_class, "base_filters", {}) or {}
            
            for fname, finstance in base_filters.items():
                # Skip quick filter
                if (
                    "quick" in fname
                    or "_ptr" in fname
                    or "polymorphic_ctype" in fname
                    or "_id" in fname
                    or fname == "pk"
                    or fname == "id"
                ):
                    continue

                parts = fname.split("__")
                base_name = parts[0]
                if (
                    base_name == "id"
                    or base_name == "pk"
                    or "report_rows" in base_name
                    or "_snapshots" in base_name
                    or "_policies" in base_name
                ):
                    continue
                # Determine lookup expression; if no explicit lookup, treat as exact
                lookup_expr = "__".join(parts[1:]) or "exact"
                # A filter is considered nested only when it references a deeper path
                # beyond the base field (e.g., famille__name__icontains). Direct
                # lookups on the base field (famille__in, famille__isnull, famille__exact)
                # must remain at the parent level.
                is_nested = (len(parts) > 2) and not fname.endswith("_count")

                # Parent group key
                group_key = base_name

                # Resolve field and labels
                field_obj = None
                verbose_name_val = group_key
                related_model_name = None
                try:
                    field_obj = model._meta.get_field(base_name)
                    # Prefer using the related model's verbose names for relation groups
                    if getattr(field_obj, "related_model", None):
                        related_model_name = field_obj.related_model.__name__
                        rel_meta = field_obj.related_model._meta
                        verbose_name_val = str(
                            getattr(rel_meta, "verbose_name_plural", None)
                            or getattr(rel_meta, "verbose_name", base_name)
                        )
                    else:
                        verbose_name_val = str(
                            getattr(field_obj, "verbose_name", base_name)
                        )
                except Exception:
                    # Property-based filters
                    prop_info = properties_dict.get(base_name)
                    if "_count" in base_name:
                        # remove "_count"
                        related_model = model._meta.get_field(
                            base_name.replace("_count", "")
                        ).related_model
                        label = base_name.replace("_count", "").upper()
                        if (
                            related_model._meta.verbose_name_plural
                            or related_model._meta.model_name
                        ):
                            label = (
                                related_model._meta.verbose_name_plural
                                or related_model._meta.model_name
                            ).lower()

                        verbose_name_val = f"Nombre total des {label} "

                    if prop_info is not None:
                        verbose_name_val = (
                            getattr(
                                getattr(prop_info, "fget", None),
                                "short_description",
                                None,
                            )
                            or getattr(prop_info, "verbose_name", None)
                            or "Nombre de "
                            or base_name
                        )

                    # Reverse relation filters: if base_name is an accessor/related_name,
                    # derive label from the related model's verbose name(s)
                    if field_obj is None and (prop_info is None):
                        try:
                            reverse_rel = None
                            for f in model._meta.get_fields():
                                # ManyToOneRel / ManyToManyRel have get_accessor_name
                                accessor = (
                                    getattr(f, "get_accessor_name", None)
                                )
                                if callable(accessor) and accessor() == base_name:
                                    reverse_rel = f
                                    break
                            if reverse_rel is not None:
                                rel_model = getattr(reverse_rel, "related_model", None)
                                if rel_model is not None:
                                    related_model_name = rel_model.__name__
                                    rel_meta = rel_model._meta
                                    # Prefer plural for reverse relations (manager-like)
                                    verbose_name_val = str(
                                        getattr(rel_meta, "verbose_name_plural", None)
                                        or getattr(rel_meta, "verbose_name", base_name)
                                    )
                        except Exception as e:
                            logger.debug(
                                f"Reverse relation label resolution failed for {model.__name__}.{base_name}: {e}"
                            )

                # Initialize group with nested container
                if group_key not in grouped_filter_dict:
                    grouped_filter_dict[group_key] = {
                        "field_name": group_key,
                        "is_nested": False,
                        "related_model": related_model_name,
                        "is_custom": False,
                        "field_label": verbose_name_val,
                        "options": [],
                        # Nested will be a list of FilterFieldType-like dicts
                        "nested": [],
                        # Internal: track seen parent lookups to avoid duplicates
                        "_seen_parent": set(),
                    }

                # Helper to build an option dict
                def _make_option(
                    name: str, lookup: str, label_for_help: str, choices_src: Any
                ) -> Dict[str, Any]:
                    return {
                        "name": name,
                        "lookup_expr": lookup,
                        "help_text": self._translate_help_text_to_french(
                            lookup, label_for_help
                        ),
                        "filter_type": finstance.__class__.__name__,
                        "choices": choices_src,
                    }

                # Compute choices for CharField choices on exact and in lookups
                option_choices = None
                try:
                    if field_obj is not None and isinstance(
                        field_obj, models.CharField
                    ):
                        raw_choices = getattr(field_obj, "choices", None)
                        if raw_choices and lookup_expr in ("exact", "in"):
                            option_choices = [
                                {"value": str(val), "label": str(lbl)}
                                for val, lbl in raw_choices
                            ]
                except Exception:
                    option_choices = None

                if not is_nested:
                    # Determine if this is a relation (ForeignKey/ManyToMany/etc.)
                    is_relation_field = bool(getattr(field_obj, "is_relation", False))

                    # For parent-level options, avoid duplicates (e.g., base and __exact)
                    seen_parent = grouped_filter_dict[group_key].setdefault(
                        "_seen_parent", set()
                    )

                    # Related fields: keep only exact, in, isnull at parent level
                    if is_relation_field:
                        if lookup_expr in ("exact", "in", "isnull"):
                            # Canonical name for exact is the base field without lookup
                            if lookup_expr == "exact":
                                if "exact" not in seen_parent:
                                    grouped_filter_dict[group_key]["options"].append(
                                        _make_option(
                                            base_name,
                                            lookup_expr,
                                            verbose_name_val,
                                            option_choices,
                                        )
                                    )
                                    seen_parent.add("exact")
                            else:
                                key = f"rel:{lookup_expr}"
                                if key not in seen_parent:
                                    grouped_filter_dict[group_key]["options"].append(
                                        _make_option(
                                            fname,
                                            lookup_expr,
                                            verbose_name_val,
                                            option_choices,
                                        )
                                    )
                                    seen_parent.add(key)
                        # Skip other lookups for relation parent field
                        continue

                    # Simple (non-relation) fields: include all available lookups
                    if lookup_expr == "exact":
                        if "exact" not in seen_parent:
                            grouped_filter_dict[group_key]["options"].append(
                                _make_option(
                                    base_name,
                                    lookup_expr,
                                    verbose_name_val,
                                    option_choices,
                                )
                            )
                            seen_parent.add("exact")
                    else:
                        key = f"simple:{lookup_expr}"
                        if key not in seen_parent:
                            grouped_filter_dict[group_key]["options"].append(
                                _make_option(
                                    fname,
                                    lookup_expr,
                                    verbose_name_val,
                                    option_choices,
                                )
                            )
                            seen_parent.add(key)
                    continue

                # Nested: group under 'nested' for the specific nested field path
                nested_path = fname.rsplit("__", 1)[0]

                # Determine nested field label by traversing the path
                nested_label = nested_path
                nested_option_choices = None
                try:
                    current_model = model
                    segments = nested_path.split("__")
                    final_field_obj = None
                    # Walk segments to find the final field verbose name
                    for i, seg in enumerate(segments):
                        fobj = current_model._meta.get_field(seg)
                        if i < len(segments) - 1:
                            # Relation hop
                            if getattr(fobj, "related_model", None) is not None:
                                current_model = fobj.related_model
                            else:
                                break
                        else:
                            final_field_obj = fobj
                            nested_label = str(getattr(fobj, "verbose_name", seg))
                    # If nested field has choices and lookup is exact or in, expose them
                    if final_field_obj is not None and isinstance(
                        final_field_obj, models.CharField
                    ):
                        raw_choices = getattr(final_field_obj, "choices", None)
                        if raw_choices and lookup_expr in ("exact", "in"):
                            nested_option_choices = [
                                {"value": str(val), "label": str(lbl)}
                                for val, lbl in raw_choices
                            ]
                except Exception:
                    nested_label = (
                        segments[-1]
                        if "segments" in locals() and segments
                        else nested_path
                    )

                # Find or create nested entry
                nested_groups = grouped_filter_dict[group_key].setdefault(
                    "_nested_groups", {}
                )
                if nested_path not in nested_groups:
                    nested_groups[nested_path] = {
                        "field_name": nested_path,
                        "is_nested": True,
                        "related_model": related_model_name,
                        "is_custom": False,
                        "field_label": nested_label,
                        "options": [],
                    }

                # For exact nested lookups, include both 'path' and full 'fname' entries
                if lookup_expr == "exact":
                    nested_groups[nested_path]["options"].append(
                        _make_option(
                            nested_path,
                            lookup_expr,
                            nested_label,
                            nested_option_choices,
                        )
                    )
                    nested_groups[nested_path]["options"].append(
                        _make_option(
                            fname, lookup_expr, nested_label, nested_option_choices
                        )
                    )
                else:
                    nested_groups[nested_path]["options"].append(
                        _make_option(
                            fname, lookup_expr, nested_label, nested_option_choices
                        )
                    )

            # Finalize nested lists
            filters = []
            for gval in grouped_filter_dict.values():
                nested_groups = gval.pop("_nested_groups", {})
                # Remove internal tracking key if present
                gval.pop("_seen_parent", None)
                gval["nested"] = list(nested_groups.values()) if nested_groups else []
                filters.append(gval)
        except Exception as e:
            logger.warning(f"Error extracting filters for {model_label}: {e}")
            filters = []
        # Assemble final metadata
        metadata = ModelTableMetadata(
            app=app_label,
            model=model_label,
            verboseName=verbose_name,
            verboseNamePlural=verbose_name_plural,
            tableName=table_name,
            primaryKey=primary_key,
            ordering=ordering,
            defaultOrdering=default_ordering,
            get_latest_by=get_latest_by,
            managers=managers,
            managed=managed,
            fields=table_fields,
            filters=filters,
        )
        # Store in TTL cache
        try:
            timeout = _get_table_cache_timeout()
            cache_key = _make_table_cache_key(
                self.schema_name,
                app_name,
                model_name,
                counts,
            )
            with _table_cache_lock:
                _table_cache[cache_key] = {
                    "value": metadata,
                    "expires_at": time.time() + timeout,
                }
                _table_cache_stats["sets"] += 1
        except Exception:
            # Do not prevent returning metadata due to cache issues
            pass
        return metadata


class ModelMetadataQuery(graphene.ObjectType):
    """GraphQL queries for model metadata."""

    model_metadata = graphene.Field(
        ModelMetadataType,
        app_name=graphene.String(required=True, description="Django app name"),
        model_name=graphene.String(required=True, description="Model class name"),
        nested_fields=graphene.Boolean(
            default_value=True, description="Include relationship metadata"
        ),
        permissions_included=graphene.Boolean(
            default_value=True, description="Include permission information"
        ),
        max_depth=graphene.Int(
            default_value=0,
            description="Maximum nesting depth for filters (default: 0)",
        ),
        description="Get comprehensive metadata for a Django model",
    )

    model_form_metadata = graphene.Field(
        ModelFormMetadataType,
        app_name=graphene.String(required=True, description="Django app name"),
        model_name=graphene.String(required=True, description="Model class name"),
        nested_fields=graphene.List(
            graphene.String,
            default_value=[],
            description="List of field names to include nested metadata for (depth 1)",
        ),
        description="Get comprehensive form metadata for a Django model",
    )

    model_table = graphene.Field(
        ModelTableType,
        app_name=graphene.String(required=True, description="Django app name"),
        model_name=graphene.String(required=True, description="Model class name"),
        counts=graphene.Boolean(
            default_value=False, description="Show reverse relationship count"
        ),
        description="Get comprehensive table metadata for a Django model",
    )

    def resolve_model_metadata(
        self,
        info,
        app_name: str,
        model_name: str,
        nested_fields: bool = True,
        permissions_included: bool = True,
        max_depth: int = 1,
    ) -> Optional[ModelMetadataType]:
        """
        Resolve model metadata with permission checking and settings validation.

        Args:
            info: GraphQL resolve info
            app_name: Django app name
            model_name: Model name
            nested_fields: Include nested relationship metadata
            permissions_included: Include permission-based field filtering
            max_depth: Maximum nesting depth for filters

        Returns:
            ModelMetadataType or None if not accessible
        """
        # Check core schema settings gating
        # Get user from context and require authentication
        user = getattr(info.context, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            permissions_included = False

        # Extract metadata via extractor which handles model lookup
        extractor = ModelMetadataExtractor(max_depth=max_depth)
        metadata = extractor.extract_model_metadata(
            app_name=app_name,
            model_name=model_name,
            user=user,
            nested_fields=nested_fields,
            permissions_included=permissions_included,
        )
        # Handle extraction error returning None
        if metadata is None:
            return None

        # Return dataclass directly for Graphene to resolve attributes
        return metadata

    def resolve_model_table(
        self,
        info,
        app_name: str,
        model_name: str,
        counts: bool = False,
    ) -> Optional[ModelTableType]:
        """Resolve comprehensive table metadata for a Django model."""
        user = getattr(info.context, "user", None)
        extractor = ModelTableExtractor()
        metadata = extractor.extract_model_table_metadata(
            app_name=app_name,
            model_name=model_name,
            counts=counts,
            user=user,
        )
        return metadata

    def resolve_model_form_metadata(
        self,
        info,
        app_name: str,
        model_name: str,
        nested_fields: List[str] = None,
    ) -> Optional[ModelFormMetadataType]:
        """
        Resolve model form metadata for frontend form construction.

        Args:
            info: GraphQL resolve info
            app_name: Django app name
            model_name: Model name
            nested_fields: List of field names to include nested metadata for (depth 1)

        Returns:
            ModelFormMetadataType or None if not accessible
        """
        # Get user from context
        user = getattr(info.context, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            user = None

        # Extract form metadata via extractor which handles model lookup
        extractor = ModelFormMetadataExtractor(max_depth=1)
        metadata = extractor.extract_model_form_metadata(
            app_name=app_name,
            model_name=model_name,
            user=user,
            nested_fields=nested_fields or [],
        )

        # Handle extraction error returning None
        if metadata is None:
            return None

        # Return dataclass directly for Graphene to resolve attributes
        return metadata


# Cache invalidation signals - only invalidate when models actually change
@receiver(post_save, sender=None)
def invalidate_model_metadata_cache_on_save(sender, instance, created, **kwargs):
    """
    Invalidate metadata cache only when model structure changes.

    This is triggered when:
    - New models are created (migrations)
    - Model fields are added/removed (migrations)
    - Model relationships change (migrations)

    Args:
        sender: The model class that was saved
        instance: The model instance
        created: Whether this is a new instance
        **kwargs: Signal arguments
    """
    # Only invalidate cache for model structure changes, not data changes
    # We check if this is likely a migration or model structure change
    if sender and hasattr(sender, "_meta"):
        # Skip cache invalidation for regular data operations
        # Only invalidate during migrations or when model structure changes
        if _is_model_structure_change(sender, instance, created, **kwargs):
            app_name = sender._meta.app_label
            model_name = sender.__name__

            # Invalidate cache for this specific model
            invalidate_metadata_cache(model_name=model_name, app_name=app_name)
            logger.info(
                f"Invalidated metadata cache for {app_name}.{model_name} due to model structure change"
            )


@receiver(post_delete, sender=None)
def invalidate_model_metadata_cache_on_delete(sender, instance, **kwargs):
    """
    Invalidate metadata cache when models are deleted.

    This is more conservative and only invalidates when it's likely
    a model structure change rather than regular data deletion.

    Args:
        sender: The model class that was deleted
        instance: The model instance
        **kwargs: Signal arguments
    """
    if sender and hasattr(sender, "_meta"):
        # Only invalidate for structural changes, not regular deletions
        if _is_model_structure_change(sender, instance, False, **kwargs):
            app_name = sender._meta.app_label
            model_name = sender.__name__

            # Invalidate cache for this specific model
            invalidate_metadata_cache(model_name=model_name, app_name=app_name)
            logger.info(
                f"Invalidated metadata cache for {app_name}.{model_name} due to model deletion"
            )


@receiver(m2m_changed)
def invalidate_m2m_metadata_cache(sender, action, **kwargs):
    """
    Invalidate metadata cache when many-to-many relationships change structurally.

    Only invalidates on structural changes, not data changes.

    Args:
        sender: The through model for the m2m field
        action: The type of m2m change
        **kwargs: Signal arguments
    """
    # Only invalidate on structural changes, not data operations
    if (
        action in ["post_add", "post_remove", "post_clear"]
        and sender
        and hasattr(sender, "_meta")
    ):
        # Check if this is a structural change vs data change
        if _is_m2m_structure_change(sender, action, **kwargs):
            app_name = sender._meta.app_label
            model_name = sender.__name__

            # Invalidate cache for this specific model
            invalidate_metadata_cache(model_name=model_name, app_name=app_name)
            logger.info(
                f"Invalidated m2m metadata cache for {app_name}.{model_name} due to relationship structure change"
            )


def _is_model_structure_change(sender, instance, created, **kwargs):
    """
    Determine if this is a model structure change vs regular data operation.

    Args:
        sender: The model class
        instance: The model instance
        created: Whether this is a new instance
        **kwargs: Signal arguments

    Returns:
        bool: True if this is likely a structure change
    """
    # Check if we're in a migration context
    if _is_in_migration_context():
        return True

    # Check if this is a Django internal model that affects schema
    if sender._meta.app_label in ["contenttypes", "auth", "admin"]:
        # These apps can affect GraphQL schema structure
        return True

    # Check if this model has custom metadata that might affect schema
    if hasattr(sender, "_graphql_metadata_affects_schema"):
        return getattr(sender, "_graphql_metadata_affects_schema", False)

    # For now, be conservative and don't invalidate on regular data operations
    return False


def _is_m2m_structure_change(sender, action, **kwargs):
    """
    Determine if this is an M2M structure change vs regular data operation.

    Args:
        sender: The through model
        action: The M2M action
        **kwargs: Signal arguments

    Returns:
        bool: True if this is likely a structure change
    """
    # Check if we're in a migration context
    if _is_in_migration_context():
        return True

    # For now, be conservative and don't invalidate on regular M2M operations
    return False


def _is_in_migration_context():
    """
    Check if we're currently in a Django migration context.

    Returns:
        bool: True if in migration context
    """
    import sys

    # Check if we're running migrations
    if "migrate" in sys.argv:
        return True

    # Check if we're in a migration module
    for frame_info in __import__("inspect").stack():
        if "migrations" in frame_info.filename:
            return True

    return False


def invalidate_cache_on_startup():
    """
    Invalidate metadata cache on application startup.

    This ensures that cache is fresh when the application starts,
    which is useful for deployments and development.
    """
    try:
        logger.info("Invalidating metadata cache on application startup")
        invalidate_metadata_cache()  # Invalidate all metadata cache
        logger.info("Metadata cache invalidated successfully on startup")
    except Exception as e:
        logger.warning(f"Failed to invalidate metadata cache on startup: {e}")
        # Don't raise exception to avoid breaking app startup


# Cache warming functions
def warm_metadata_cache(app_name: str = None, model_name: str = None, user=None):
    """
    Pre-warm metadata cache for specified models.

    Args:
        app_name: Specific app to warm cache for (optional)
        model_name: Specific model to warm cache for (optional)
        user: User context for permission-based caching
    """
    extractor = ModelMetadataExtractor()

    if app_name and model_name:
        # Warm cache for specific model
        try:
            extractor.extract_model_metadata(app_name, model_name, user)
            logger.info(f"Warmed metadata cache for {app_name}.{model_name}")
        except Exception as e:
            logger.error(f"Failed to warm cache for {app_name}.{model_name}: {e}")
    elif app_name:
        # Warm cache for all models in app
        try:
            app_config = apps.get_app_config(app_name)
            for model in app_config.get_models():
                extractor.extract_model_metadata(app_name, model.__name__, user)
            logger.info(f"Warmed metadata cache for app {app_name}")
        except Exception as e:
            logger.error(f"Failed to warm cache for app {app_name}: {e}")
    else:
        # Warm cache for all models
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                try:
                    extractor.extract_model_metadata(
                        app_config.label, model.__name__, user
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to warm cache for {app_config.label}.{model.__name__}: {e}"
                    )
        logger.info("Warmed metadata cache for all models")


def get_cache_stats() -> Dict[str, Any]:
    """
    Purpose: Return TTL cache statistics for model table metadata.

    Args:
        None

    Returns:
        Dict[str, Any]: Cache statistics including hits, misses, hit rate, sets,
        deletes, invalidations, default timeout, and current cache size.

    Raises:
        None

    Example:
        >>> stats = get_cache_stats()
        >>> stats["hits"]
        0
    """
    # Safely snapshot current stats and size under lock
    with _table_cache_lock:
        stats_snapshot = dict(_table_cache_stats)
        cache_size = len(_table_cache)

    total_requests = stats_snapshot.get("hits", 0) + stats_snapshot.get("misses", 0)
    hit_rate = (
        (stats_snapshot.get("hits", 0) / total_requests) if total_requests else 0.0
    )

    return {
        "hits": stats_snapshot.get("hits", 0),
        "misses": stats_snapshot.get("misses", 0),
        "hit_rate": hit_rate,
        "sets": stats_snapshot.get("sets", 0),
        "deletes": stats_snapshot.get("deletes", 0),
        "invalidations": stats_snapshot.get("invalidations", 0),
        "default_timeout": _get_table_cache_timeout(),
        "size": cache_size,
    }


# Use lazy import to avoid AppRegistryNotReady error
