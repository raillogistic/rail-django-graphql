"""
Schema Builder System for rail-django-graphql library

This module provides the SchemaBuilder class, which is responsible for assembling
the unified GraphQL schema from all registered Django apps and models.
"""

from typing import Dict, List, Optional, Set, Type, Union, Any
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

logger = logging.getLogger(__name__)


class SchemaBuilder:
    """
    Builds and manages the unified GraphQL schema, combining queries and mutations
    from all registered Django apps and models.
    
    This class supports:
    - Multiple schema configurations
    - Schema-specific settings
    - Automatic model discovery
    - Dynamic schema rebuilding
    - Integration with the schema registry
    """

    _instances: Dict[str, 'SchemaBuilder'] = {}
    _lock = threading.Lock()

    def __new__(cls, settings: Optional[Any] = None, schema_name: str = "default", *args, **kwargs):
        """Create or return existing SchemaBuilder instance for the given schema name."""
        with cls._lock:
            if schema_name not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[schema_name] = instance
            return cls._instances[schema_name]

    def __init__(self, settings: Optional[Any] = None, schema_name: str = "default"):
        """
        Initialize the SchemaBuilder.
        
        Args:
            settings: Schema settings instance or None for defaults
            schema_name: Name of the schema (for multi-schema support)
        """
        # Avoid re-initialization
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.schema_name = schema_name
        
        # Load settings using the new configuration system
        if settings is None:
            try:
                from ..conf import get_schema_settings
                from .settings import SchemaSettings
                
                # Get schema-specific settings
                config = get_schema_settings(schema_name)
                self.settings = SchemaSettings(**config.get('SCHEMA_SETTINGS', {}))
            except ImportError:
                # Fallback to legacy settings
                from .settings import SchemaSettings
                self.settings = SchemaSettings()
        else:
            self.settings = settings
        
        # Initialize generators with lazy imports to avoid circular dependencies
        self._type_generator = None
        self._query_generator = None
        self._mutation_generator = None
        
        # Schema state
        self._schema = None
        self._query_fields: Dict[str, Union[graphene.Field, graphene.List]] = {}
        self._mutation_fields: Dict[str, Type[graphene.Mutation]] = {}
        self._registered_models: Set[Type[models.Model]] = set()
        self._schema_version = 0
        
        self._initialized = True
        self._connect_signals()

    @property
    def type_generator(self):
        """Lazy-loaded type generator."""
        if self._type_generator is None:
            from ..generators.types import TypeGenerator
            from ..core.settings import TypeGeneratorSettings
            try:
                from ..conf import get_schema_settings
                type_config = get_schema_settings(self.schema_name).get('TYPE_SETTINGS', {})
                # Convert dict to TypeGeneratorSettings object, filtering valid parameters
                valid_params = {}
                if type_config:
                    # Map config keys to TypeGeneratorSettings field names
                    field_mapping = {
                        'EXCLUDE_FIELDS': 'exclude_fields',
                        'EXCLUDED_FIELDS': 'excluded_fields',
                        'INCLUDE_FIELDS': 'include_fields',
                        'CUSTOM_FIELD_MAPPINGS': 'custom_field_mappings',
                        'GENERATE_FILTERS': 'generate_filters',
                        'ENABLE_FILTERING': 'enable_filtering',
                        'AUTO_CAMELCASE': 'auto_camelcase',
                        'ENABLE_AUTO_CAMEL_CASE': 'auto_camelcase',  # Alias
                        'GENERATE_DESCRIPTIONS': 'generate_descriptions',
                    }
                    for config_key, value in type_config.items():
                        if config_key in field_mapping:
                            valid_params[field_mapping[config_key]] = value
                
                type_settings = TypeGeneratorSettings(**valid_params)
                self._type_generator = TypeGenerator(settings=type_settings, schema_name=self.schema_name)
            except ImportError:
                self._type_generator = TypeGenerator(settings=TypeGeneratorSettings())
        return self._type_generator

    @property
    def query_generator(self):
        """Lazy-loaded query generator."""
        if self._query_generator is None:
            from ..generators.queries import QueryGenerator
            from ..core.settings import QueryGeneratorSettings
            try:
                from ..conf import get_schema_settings
                query_config = get_schema_settings(self.schema_name).get('QUERY_SETTINGS', {})
                
                # Convert dictionary to QueryGeneratorSettings object
                if isinstance(query_config, dict):
                    # Map configuration keys to QueryGeneratorSettings fields
                    settings_kwargs = {}
                    for key, value in query_config.items():
                        if key == 'GENERATE_FILTERS':
                            settings_kwargs['generate_filters'] = value
                        elif key == 'GENERATE_ORDERING':
                            settings_kwargs['generate_ordering'] = value
                        elif key == 'GENERATE_PAGINATION':
                            settings_kwargs['generate_pagination'] = value
                        elif key == 'USE_RELAY':
                            settings_kwargs['use_relay'] = value
                        elif key == 'DEFAULT_PAGE_SIZE':
                            settings_kwargs['default_page_size'] = value
                        elif key == 'MAX_PAGE_SIZE':
                            settings_kwargs['max_page_size'] = value
                        elif key == 'ENABLE_PAGINATION':
                            settings_kwargs['enable_pagination'] = value
                        elif key == 'ENABLE_ORDERING':
                            settings_kwargs['enable_ordering'] = value
                        elif key == 'ADDITIONAL_LOOKUP_FIELDS':
                            settings_kwargs['additional_lookup_fields'] = value
                    
                    query_settings = QueryGeneratorSettings(**settings_kwargs)
                else:
                    query_settings = query_config
                
                self._query_generator = QueryGenerator(
                    self.type_generator, 
                    settings=query_settings,
                    schema_name=self.schema_name
                )
            except ImportError:
                self._query_generator = QueryGenerator(self.type_generator)
        return self._query_generator

    @property
    def mutation_generator(self):
        """Lazy-loaded mutation generator."""
        if self._mutation_generator is None:
            from ..generators.mutations import MutationGenerator
            try:
                from ..conf import get_schema_settings
                from .config_loader import ConfigLoader
                
                # Load mutation settings for this schema
                mutation_settings = ConfigLoader.load_mutation_settings(self.schema_name)
                self._mutation_generator = MutationGenerator(
                    self.type_generator, 
                    mutation_settings,
                    schema_name=self.schema_name
                )
            except ImportError:
                # Fallback to legacy loading
                from .config_loader import load_mutation_settings
                mutation_settings = load_mutation_settings()
                from ..generators.mutations import MutationGenerator
                self._mutation_generator = MutationGenerator(self.type_generator, mutation_settings)
        return self._mutation_generator

    def _connect_signals(self) -> None:
        """
        Connects Django signals for automatic schema rebuilding.
        """
        post_migrate.connect(self._handle_post_migrate)
        if self.settings.auto_refresh_on_model_change:
            post_save.connect(self._handle_model_change)
            post_delete.connect(self._handle_model_change)

    def _handle_post_migrate(self, sender, **kwargs) -> None:
        """
        Handles post-migrate signal to rebuild schema after migrations.
        """
        logger.info(f"Rebuilding schema '{self.schema_name}' after database migration")
        self.rebuild_schema()

    def _handle_model_change(self, sender, **kwargs) -> None:
        """
        Handles model change signals to update schema when necessary.
        """
        if sender in self._registered_models:
            logger.info(f"Model {sender.__name__} changed, updating schema '{self.schema_name}'")
            self.rebuild_schema()

    def _is_valid_model(self, model: Type[models.Model]) -> bool:
        """
        Checks if a model should be included in the schema.
        
        Args:
            model: Django model class to validate
            
        Returns:
            bool: True if model should be included in schema
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
        
        Returns:
            List[Type[models.Model]]: List of valid Django models
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
        
        Args:
            models: List of Django models to generate queries for
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
        
        Args:
            models: List of Django models to generate mutations for
        """
        self._mutation_fields = {}

        for model in models:
            mutations = self.mutation_generator.generate_all_mutations(model)
            logger.debug(f"Generated {len(mutations)} mutations for model {model.__name__}: {list(mutations.keys())}")
            self._mutation_fields.update(mutations)
        
        logger.info(f"Total mutations generated for schema '{self.schema_name}': {len(self._mutation_fields)}")
        logger.debug(f"Mutation fields: {list(self._mutation_fields.keys())}")

    def rebuild_schema(self) -> None:
        """
        Rebuilds the entire GraphQL schema.
        
        This method:
        1. Discovers all valid Django models
        2. Generates query and mutation fields
        3. Integrates security extensions
        4. Creates the final GraphQL schema
        5. Registers the schema in the registry
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
                logger.info(f"Discovered {len(models)} models for schema '{self.schema_name}': {[m.__name__ for m in models]}")

                # Generate queries
                self._generate_query_fields(models)

                # Generate mutations
                self._generate_mutation_fields(models)
                
                logger.info(f"Schema '{self.schema_name}' generation - Query fields: {len(self._query_fields)}, Mutation fields: {len(self._mutation_fields)}")

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
                    
                    logger.info(f"Security extensions integrated into schema '{self.schema_name}'")
                except ImportError as e:
                    logger.warning(f"Could not import security extensions for schema '{self.schema_name}': {e}")
                
                # Add health monitoring queries
                try:
                    from ..extensions.health import HealthQuery
                    
                    # Create an instance of HealthQuery to get bound methods
                    health_query_instance = HealthQuery()
                    
                    # Merge health queries with proper resolver binding
                    for field_name, field in HealthQuery._meta.fields.items():
                        # Get the resolver method from the instance
                        resolver_method_name = f'resolve_{field_name}'
                        if hasattr(health_query_instance, resolver_method_name):
                            resolver_method = getattr(health_query_instance, resolver_method_name)
                            # Create a wrapper that handles the root parameter
                            def create_resolver_wrapper(method):
                                def wrapper(root, info, **kwargs):
                                    return method(info, **kwargs)
                                return wrapper
                            
                            # Create a new field with the wrapped resolver
                            query_attrs[field_name] = graphene.Field(
                                field.type,
                                description=field.description,
                                resolver=create_resolver_wrapper(resolver_method)
                            )
                        else:
                            query_attrs[field_name] = field
                    
                    logger.info(f"Health monitoring queries integrated into schema '{self.schema_name}'")
                except ImportError as e:
                    logger.warning(f"Could not import health queries for schema '{self.schema_name}': {e}")
                
                query_type = type('Query', (graphene.ObjectType,), query_attrs)

                # Create Mutation type if there are mutations
                mutation_type = None
                logger.info(f"Checking mutation fields for schema '{self.schema_name}': {len(self._mutation_fields)} mutations found")
                
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
                    logger.info(f"Security mutations integrated into schema '{self.schema_name}'")
                except ImportError as e:
                    logger.warning(f"Could not import security mutations for schema '{self.schema_name}': {e}")
                
                # Combine all mutations
                all_mutations = {**self._mutation_fields, **security_mutations}
                
                if all_mutations:
                    logger.info(f"Creating Mutation type for schema '{self.schema_name}' with fields: {list(all_mutations.keys())}")
                    mutation_type = type('Mutation', (graphene.ObjectType,), all_mutations)
                else:
                    logger.info(f"No mutations found for schema '{self.schema_name}', creating dummy mutation")
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
                    logger.info(f"Security middleware integrated into schema '{self.schema_name}'")
                except ImportError as e:
                    logger.warning(f"Could not import security middleware for schema '{self.schema_name}': {e}")
                
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

                # Register schema in the registry
                try:
                    from .registry import register_schema
                    register_schema(
                        name=self.schema_name,
                        schema=self._schema,
                        description=f"Auto-generated GraphQL schema for {self.schema_name}",
                        version=str(self._schema_version),
                        models=list(self._registered_models)
                    )
                    logger.info(f"Schema '{self.schema_name}' registered in schema registry")
                except ImportError as e:
                    logger.warning(f"Could not register schema '{self.schema_name}' in registry: {e}")

                logger.info(
                    f"Schema '{self.schema_name}' rebuilt successfully (version {self._schema_version})"
                    f"\n - Models: {len(models)}"
                    f"\n - Queries: {len(self._query_fields)}"
                    f"\n - Mutations: {len(self._mutation_fields)}"
                )

            except Exception as e:
                logger.error(f"Failed to rebuild schema '{self.schema_name}': {str(e)}", exc_info=True)
                raise

    def get_schema(self) -> graphene.Schema:
        """
        Returns the current GraphQL schema, rebuilding if necessary.
        
        Returns:
            graphene.Schema: The current GraphQL schema
        """
        if self._schema is None:
            self.rebuild_schema()
        return self._schema

    def get_schema_version(self) -> int:
        """
        Returns the current schema version number.
        
        Returns:
            int: Current schema version
        """
        return self._schema_version

    def get_middleware(self) -> List:
        """
        Returns the middleware list for this schema.
        
        Returns:
            List: List of middleware instances
        """
        return getattr(self, '_middleware', [])

    def clear_schema(self) -> None:
        """
        Clears the current schema, forcing a rebuild on next access.
        """
        with self._lock:
            self._schema = None
            self._query_fields.clear()
            self._mutation_fields.clear()
            self._registered_models.clear()
            logger.info(f"Schema '{self.schema_name}' cleared")

    def register_app(self, app_label: str) -> None:
        """
        Registers a Django app for schema generation.
        
        Args:
            app_label: Django app label to register
        """
        if app_label in self.settings.excluded_apps:
            self.settings.excluded_apps.remove(app_label)
            self.rebuild_schema()
            logger.info(f"App '{app_label}' registered for schema '{self.schema_name}' generation")

    def unregister_app(self, app_label: str) -> None:
        """
        Unregisters a Django app from schema generation.
        
        Args:
            app_label: Django app label to unregister
        """
        if app_label not in self.settings.excluded_apps:
            self.settings.excluded_apps.add(app_label)
            self.rebuild_schema()
            logger.info(f"App '{app_label}' unregistered from schema '{self.schema_name}' generation")

    def register_model(self, model: Union[Type[models.Model], str]) -> None:
        """
        Registers a model for schema generation.
        
        Args:
            model: Django model class or model name to register
        """
        model_identifier = model.__name__ if isinstance(model, type) else model
        if model_identifier in self.settings.excluded_models:
            self.settings.excluded_models.remove(model_identifier)
            self.rebuild_schema()
            logger.info(f"Model '{model_identifier}' registered for schema '{self.schema_name}' generation")

    def unregister_model(self, model: Union[Type[models.Model], str]) -> None:
        """
        Unregisters a model from schema generation.
        
        Args:
            model: Django model class or model name to unregister
        """
        model_identifier = model.__name__ if isinstance(model, type) else model
        if model_identifier not in self.settings.excluded_models:
            self.settings.excluded_models.add(model_identifier)
            self.rebuild_schema()
            logger.info(f"Model '{model_identifier}' unregistered from schema '{self.schema_name}' generation")

    def reload_app_schema(self, app_label: str) -> None:
        """
        Reloads schema for a specific app.
        
        Args:
            app_label: Django app label to reload
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
                
            logger.info(f"Schema reloaded for app '{app_label}' in schema '{self.schema_name}'")
            
        except Exception as e:
            logger.error(f"Failed to reload schema for app '{app_label}' in schema '{self.schema_name}': {str(e)}", exc_info=True)
            raise

    def get_registered_models(self) -> Set[Type[models.Model]]:
        """
        Returns the set of registered models for this schema.
        
        Returns:
            Set[Type[models.Model]]: Set of registered Django models
        """
        return self._registered_models.copy()

    def get_query_fields(self) -> Dict[str, Union[graphene.Field, graphene.List]]:
        """
        Returns the current query fields for this schema.
        
        Returns:
            Dict[str, Union[graphene.Field, graphene.List]]: Query fields dictionary
        """
        return self._query_fields.copy()

    def get_mutation_fields(self) -> Dict[str, Type[graphene.Mutation]]:
        """
        Returns the current mutation fields for this schema.
        
        Returns:
            Dict[str, Type[graphene.Mutation]]: Mutation fields dictionary
        """
        return self._mutation_fields.copy()


# Global schema management functions
def get_schema_builder(schema_name: str = "default") -> SchemaBuilder:
    """
    Get or create a schema builder instance for the given schema name.
    
    Args:
        schema_name: Name of the schema (defaults to "default")
        
    Returns:
        SchemaBuilder: Schema builder instance
    """
    return SchemaBuilder(schema_name=schema_name)


def get_schema(schema_name: str = "default") -> graphene.Schema:
    """
    Get the GraphQL schema for the given schema name.
    
    Args:
        schema_name: Name of the schema (defaults to "default")
        
    Returns:
        graphene.Schema: The GraphQL schema
    """
    return get_schema_builder(schema_name).get_schema()


def clear_all_schemas() -> None:
    """
    Clear all schema builder instances.
    """
    with SchemaBuilder._lock:
        for schema_name, builder in SchemaBuilder._instances.items():
            builder.clear_schema()
        SchemaBuilder._instances.clear()
        logger.info("All schemas cleared")


def get_all_schema_names() -> List[str]:
    """
    Get all registered schema names.
    
    Returns:
        List[str]: List of schema names
    """
    return list(SchemaBuilder._instances.keys())