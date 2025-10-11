"""
Model metadata schema for Django GraphQL Auto-Generation.

This module provides comprehensive metadata exposure for Django models to support
rich frontend interfaces including advanced filtering, CRUD operations, and
complex forms with nested fields.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, Union

import graphene
from django.apps import apps
from graphql import GraphQLError

from ..conf import get_core_schema_settings
from ..core.settings import SchemaSettings
from ..generators.introspector import ModelIntrospector

# Remove imports that cause AppRegistryNotReady error
# from ..core.security import AuthorizationManager
# from ..extensions.permissions import PermissionLevel, OperationType

logger = logging.getLogger(__name__)


# Use lazy import to avoid AppRegistryNotReady error
def get_user_model_lazy():
    from django.contrib.auth import get_user_model

    return get_user_model()


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
    choices: Optional[List[Dict[str, Any]]]
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
    choices = graphene.List(graphene.JSONString, description="Field choices")
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
            is_required=not field.null
            and not field.blank
            and field.default == models.NOT_PROVIDED,
            is_nullable=field.null,
            null=field.null,
            default_value=str(field.default)
            if field.default != models.NOT_PROVIDED
            else None,
            help_text=field.help_text or "",
            max_length=max_length,
            choices=choices,
            is_primary_key=field.primary_key,
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
                        is_required=True,
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
                        permissions.append(action)

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
        description="Get comprehensive metadata for a Django model",
    )

    def resolve_model_metadata(
        self,
        info,
        app_name: str,
        model_name: str,
        nested_fields: bool = True,
        permissions_included: bool = True,
    ) -> Optional[ModelMetadataType]:
        print("xxxxxxxxxxxxxxxx", getattr(info.context, "user", None))
        """
        Resolve model metadata with permission checking and settings validation.

        Args:
            info: GraphQL resolve info
            app_name: Django app name
            model_name: Model name
            include_nested: Include nested relationship metadata
            include_permissions: Include permission-based field filtering

        Returns:
            ModelMetadataType or None if not accessible
        """
        # Check core schema settings gating
        # Get user from context and require authentication
        user = getattr(info.context, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return None

        # Extract metadata via extractor which handles model lookup
        extractor = ModelMetadataExtractor()
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
