"""
Schema Builder System for Django GraphQL Auto-Generation

This module provides the SchemaBuilder class, which is responsible for assembling
the unified GraphQL schema from all registered Django apps and models.
"""

from typing import Dict, List, Optional, Set, Type, Union
import importlib
import inspect
import logging
import threading
from pathlib import Path

import graphene
from django.apps import apps
from django.db import models
from django.db.models.signals import post_migrate, post_save, post_delete
from django.dispatch import receiver
from graphene_django.debug import DjangoDebug

from .settings import SchemaSettings
from ..generators.introspector import ModelIntrospector
from ..generators.types import TypeGenerator
from ..generators.queries import QueryGenerator
from ..generators.mutations import MutationGenerator

logger = logging.getLogger(__name__)

class SchemaBuilder:
    """
    Builds and manages the unified GraphQL schema, combining queries and mutations
    from all registered Django apps and models.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, settings: Optional[SchemaSettings] = None):
        if not hasattr(self, '_initialized'):
            self.settings = settings or SchemaSettings()
            self.type_generator = TypeGenerator()
            self.query_generator = QueryGenerator(self.type_generator)
            # Load mutation settings from Django configuration
            from .config_loader import load_mutation_settings
            mutation_settings = load_mutation_settings()
            self.mutation_generator = MutationGenerator(self.type_generator, mutation_settings)
            
            self._schema = None
            self._query_fields: Dict[str, Union[graphene.Field, graphene.List]] = {}
            self._mutation_fields: Dict[str, Type[graphene.Mutation]] = {}
            self._registered_models: Set[Type[models.Model]] = set()
            self._schema_version = 0
            
            self._initialized = True
            self._connect_signals()

    def _connect_signals(self) -> None:
        """
        Connects Django signals for schema updates.
        """
        post_migrate.connect(self._handle_post_migrate)
        if self.settings.auto_refresh_on_model_change:
            post_save.connect(self._handle_model_change)
            post_delete.connect(self._handle_model_change)

    def _handle_post_migrate(self, sender, **kwargs) -> None:
        """
        Handles post-migrate signal to rebuild schema after migrations.
        """
        logger.info("Rebuilding schema after database migration")
        self.rebuild_schema()

    def _handle_model_change(self, sender, **kwargs) -> None:
        """
        Handles model change signals to update schema when necessary.
        """
        if sender in self._registered_models:
            logger.info(f"Model {sender.__name__} changed, updating schema")
            self.rebuild_schema()

    def _is_valid_model(self, model: Type[models.Model]) -> bool:
        """
        Checks if a model should be included in the schema.
        """
        if model._meta.abstract:
            return False

        app_label = model._meta.app_label
        model_name = model.__name__

        # Check app exclusions
        if app_label in self.settings.excluded_apps:
            return False

        # Check model exclusions
        if model_name in self.settings.excluded_models:
            return False

        # Check app.model exclusions
        if f"{app_label}.{model_name}" in self.settings.excluded_models:
            return False

        return True

    def _discover_models(self) -> List[Type[models.Model]]:
        """
        Discovers all valid Django models for schema generation.
        """
        discovered_models = []
        
        for app_config in apps.get_app_configs():
            if app_config.name in self.settings.excluded_apps:
                continue

            for model in app_config.get_models():
                if self._is_valid_model(model):
                    discovered_models.append(model)

        return discovered_models

    def _generate_query_fields(self, models: List[Type[models.Model]]) -> None:
        """
        Generates query fields for all discovered models.
        """
        self._query_fields = {}

        for model in models:
            model_name = model.__name__.lower()

            # Single object query
            single_query = self.query_generator.generate_single_query(model)
            self._query_fields[model_name] = single_query

            # List query
            list_query = self.query_generator.generate_list_query(model)
            self._query_fields[f'{model_name}s'] = list_query

            # Paginated query
            if self.settings.enable_pagination:
                paginated_query = self.query_generator.generate_paginated_query(model)
                self._query_fields[f'{model_name}_pages'] = paginated_query

    def _generate_mutation_fields(self, models: List[Type[models.Model]]) -> None:
        """
        Generates mutation fields for all discovered models.
        """
        self._mutation_fields = {}

        for model in models:
            mutations = self.mutation_generator.generate_all_mutations(model)
            logger.debug(f"Generated {len(mutations)} mutations for model {model.__name__}: {list(mutations.keys())}")
            self._mutation_fields.update(mutations)
        
        logger.info(f"Total mutations generated: {len(self._mutation_fields)}")
        logger.debug(f"Mutation fields: {list(self._mutation_fields.keys())}")

    def rebuild_schema(self) -> None:
        """
        Rebuilds the entire GraphQL schema.
        """
        with self._lock:
            try:
                # Clear existing schema
                self._schema = None
                self._query_fields = {}
                self._mutation_fields = {}

                # Discover models
                models = self._discover_models()
                self._registered_models = set(models)
                logger.info(f"Discovered {len(models)} models: {[m.__name__ for m in models]}")

                # Generate queries
                self._generate_query_fields(models)

                # Generate mutations
                self._generate_mutation_fields(models)
                
                logger.info(f"After generation - Query fields: {len(self._query_fields)}, Mutation fields: {len(self._mutation_fields)}")

                # Create Query type with security extensions
                query_attrs = {
                    'debug': graphene.Field(DjangoDebug, name='_debug')
                }
                query_attrs.update(self._query_fields)
                
                # Add security-related queries
                try:
                    from ..extensions.auth import MeQuery
                    from ..extensions.permissions import PermissionQuery
                    from ..extensions.validation import ValidationQuery
                    from ..extensions.rate_limiting import SecurityQuery
                    
                    # Merge security queries
                    for query_class in [MeQuery, PermissionQuery, ValidationQuery, SecurityQuery]:
                        for field_name, field in query_class._meta.fields.items():
                            query_attrs[field_name] = field
                    
                    logger.info("Security extensions integrated into schema")
                except ImportError as e:
                    logger.warning(f"Could not import security extensions: {e}")
                
                query_type = type('Query', (graphene.ObjectType,), query_attrs)

                # Create Mutation type if there are mutations
                mutation_type = None
                logger.info(f"Checking mutation fields: {len(self._mutation_fields)} mutations found")
                
                # Add security-related mutations
                security_mutations = {}
                try:
                    from ..extensions.auth import LoginMutation, RegisterMutation, RefreshTokenMutation, LogoutMutation
                    
                    security_mutations.update({
                        'login': LoginMutation.Field(),
                        'register': RegisterMutation.Field(),
                        'refresh_token': RefreshTokenMutation.Field(),
                        'logout': LogoutMutation.Field(),
                    })
                    logger.info("Security mutations integrated into schema")
                except ImportError as e:
                    logger.warning(f"Could not import security mutations: {e}")
                
                # Combine all mutations
                all_mutations = {**self._mutation_fields, **security_mutations}
                
                if all_mutations:
                    logger.info(f"Creating Mutation type with fields: {list(all_mutations.keys())}")
                    mutation_type = type('Mutation', (graphene.ObjectType,), all_mutations)
                else:
                    logger.info("No mutations found, creating dummy mutation")
                    # Create dummy mutation to avoid GraphQL error
                    class DummyMutation(graphene.Mutation):
                        class Arguments:
                            pass
                        
                        success = graphene.Boolean()
                        
                        def mutate(self, info):
                            return DummyMutation(success=True)
                    
                    mutation_attrs = {
                        'dummy': DummyMutation.Field(description="Placeholder mutation field")
                    }
                    mutation_type = type('Mutation', (graphene.ObjectType,), mutation_attrs)

                # Create Schema with security middleware
                middleware = []
                try:
                    from ..extensions.rate_limiting import GraphQLSecurityMiddleware
                    middleware.append(GraphQLSecurityMiddleware())
                    logger.info("Security middleware integrated into schema")
                except ImportError as e:
                    logger.warning(f"Could not import security middleware: {e}")
                
                # Note: Graphene Schema doesn't support middleware parameter directly
                # Middleware should be applied at the GraphQL execution level
                self._schema = graphene.Schema(
                    query=query_type,
                    mutation=mutation_type,
                    auto_camelcase=self.settings.auto_camelcase
                )
                
                # Store middleware for later use in execution
                self._middleware = middleware

                # Increment schema version
                self._schema_version += 1

                logger.info(
                    f"Schema rebuilt successfully (version {self._schema_version})"
                    f"\n - Models: {len(models)}"
                    f"\n - Queries: {len(self._query_fields)}"
                    f"\n - Mutations: {len(self._mutation_fields)}"
                )

            except Exception as e:
                logger.error(f"Failed to rebuild schema: {str(e)}", exc_info=True)
                raise

    def get_schema(self) -> graphene.Schema:
        """
        Returns the current GraphQL schema, rebuilding if necessary.
        """
        if self._schema is None:
            self.rebuild_schema()
        return self._schema

    def get_schema_version(self) -> int:
        """
        Returns the current schema version number.
        """
        return self._schema_version

    def clear_schema(self) -> None:
        """
        Clears the current schema, forcing a rebuild on next access.
        """
        with self._lock:
            self._schema = None
            self._query_fields.clear()
            self._mutation_fields.clear()
            self._registered_models.clear()
            logger.info("Schema cleared")

    def register_app(self, app_label: str) -> None:
        """
        Registers a Django app for schema generation.
        """
        if app_label in self.settings.excluded_apps:
            self.settings.excluded_apps.remove(app_label)
            self.rebuild_schema()
            logger.info(f"App '{app_label}' registered for schema generation")

    def unregister_app(self, app_label: str) -> None:
        """
        Unregisters a Django app from schema generation.
        """
        if app_label not in self.settings.excluded_apps:
            self.settings.excluded_apps.add(app_label)
            self.rebuild_schema()
            logger.info(f"App '{app_label}' unregistered from schema generation")

    def register_model(self, model: Union[Type[models.Model], str]) -> None:
        """
        Registers a model for schema generation.
        """
        model_identifier = model.__name__ if isinstance(model, type) else model
        if model_identifier in self.settings.excluded_models:
            self.settings.excluded_models.remove(model_identifier)
            self.rebuild_schema()
            logger.info(f"Model '{model_identifier}' registered for schema generation")

    def unregister_model(self, model: Union[Type[models.Model], str]) -> None:
        """
        Unregisters a model from schema generation.
        """
        model_identifier = model.__name__ if isinstance(model, type) else model
        if model_identifier not in self.settings.excluded_models:
            self.settings.excluded_models.add(model_identifier)
            self.rebuild_schema()
            logger.info(f"Model '{model_identifier}' unregistered from schema generation")

    def reload_app_schema(self, app_label: str) -> None:
        """
        Reloads schema for a specific app.
        """
        try:
            app_config = apps.get_app_config(app_label)
            models = [
                model for model in app_config.get_models()
                if self._is_valid_model(model)
            ]
            
            with self._lock:
                # Remove existing app-related fields
                for model in models:
                    model_name = model.__name__.lower()
                    # Remove queries
                    self._query_fields.pop(model_name, None)
                    self._query_fields.pop(f'{model_name}s', None)
                    self._query_fields.pop(f'{model_name}_pages', None)
                    
                    # Remove mutations
                    mutations = self.mutation_generator.generate_all_mutations(model)
                    for mutation_name in mutations:
                        self._mutation_fields.pop(mutation_name, None)

                # Regenerate app schema
                self._generate_query_fields(models)
                self._generate_mutation_fields(models)
                
                # Update registered models
                self._registered_models.update(models)
                
                # Rebuild schema
                self.rebuild_schema()
                
            logger.info(f"Schema reloaded for app '{app_label}'")
            
        except Exception as e:
            logger.error(f"Failed to reload schema for app '{app_label}': {str(e)}", exc_info=True)
            raise

# Create a global schema instance
schema_builder = SchemaBuilder()
schema = schema_builder.get_schema()