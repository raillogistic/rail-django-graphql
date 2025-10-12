"""
Schema Builder System for rail-django-graphql library

This module provides the SchemaBuilder class, which is responsible for assembling
the unified GraphQL schema from all registered Django apps and models.
"""

import importlib
import inspect
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, Union

import graphene
from django.apps import apps
from django.db import models
from django.db.models.signals import post_delete, post_migrate, post_save
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

    _instances: Dict[str, "SchemaBuilder"] = {}
    _lock = threading.Lock()

    def __new__(
        cls,
        settings: Optional[Any] = None,
        schema_name: str = "default",
        *args,
        **kwargs,
    ):
        """Create or return existing SchemaBuilder instance for the given schema name."""
        with cls._lock:
            if schema_name not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[schema_name] = instance
            return cls._instances[schema_name]

    def __init__(
        self,
        settings: Optional[Any] = None,
        schema_name: str = "default",
        raw_settings: Optional[dict] = None,
        registry=None,
    ):
        """
        Initialize the SchemaBuilder.

        Args:
            settings: Schema settings instance or None for defaults
            schema_name: Name of the schema (for multi-schema support)
            raw_settings: Raw settings dictionary containing schema_settings
            registry: Schema registry instance for model discovery
        """
        # Avoid re-initialization
        if hasattr(self, "_initialized") and self._initialized:
            return
        self.schema_name = schema_name
        self.registry = registry

        # Store the raw settings dictionary for schema_settings extraction
        self._raw_settings = raw_settings or {}

        # Load settings using the new configuration system
        if settings is None:
            try:
                from ..conf import get_core_schema_settings
                from .settings import SchemaSettings

                # Get schema-specific settings
                settings_dict = get_core_schema_settings(schema_name)
                if settings_dict:
                    # Convert dictionary to SchemaSettings dataclass
                    self.settings = SchemaSettings(**settings_dict)
                else:
                    # Use default settings if empty
                    self.settings = SchemaSettings()

                # If no raw_settings provided, use the settings_dict
                if not self._raw_settings:
                    self._raw_settings = settings_dict or {}
            except ImportError:
                # Fallback to legacy settings
                from .settings import SchemaSettings

                self.settings = SchemaSettings()
        else:
            self.settings = settings
            # If raw_settings is provided, use it; otherwise, initialize empty
            if not self._raw_settings:
                self._raw_settings = {}

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

            self._type_generator = TypeGenerator(schema_name=self.schema_name)
        return self._type_generator

    @property
    def query_generator(self):
        """Lazy-loaded query generator."""
        if self._query_generator is None:
            from ..generators.queries import QueryGenerator

            self._query_generator = QueryGenerator(
                self.type_generator,
                schema_name=self.schema_name,
            )
        return self._query_generator

    @property
    def mutation_generator(self):
        """Lazy-loaded mutation generator."""
        if self._mutation_generator is None:
            from ..conf import get_mutation_generator_settings
            from ..generators.mutations import MutationGenerator

            mutation_settings = get_mutation_generator_settings(self.schema_name)
            self._mutation_generator = MutationGenerator(
                self.type_generator,
                settings=mutation_settings,
                schema_name=self.schema_name,
            )
        return self._mutation_generator

    def _get_schema_setting(self, key: str, default: Any = None) -> Any:
        """
        Extract a setting from the settings object or raw settings.

        Args:
            key: Setting key to extract
            default: Default value if key is not found

        Returns:
            Setting value or default
        """
        # First try to get from the settings object
        if hasattr(self.settings, key):
            return getattr(self.settings, key)

        # Fallback to raw settings for backward compatibility
        return self._raw_settings.get(key, default)

    def _connect_signals(self) -> None:
        """
        Connects Django signals for automatic schema rebuilding.
        """
        post_migrate.connect(self._handle_post_migrate)
        if self._get_schema_setting("auto_refresh_on_model_change", True):
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
            logger.info(
                f"Model {sender.__name__} changed, updating schema '{self.schema_name}'"
            )
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

        # Check app exclusions from schema_settings
        excluded_apps = self._get_schema_setting("excluded_apps", [])

        if app_label in excluded_apps:
            logger.debug(
                f"Excluding model {model_name} from app {app_label} (app excluded)"
            )
            return False

        # Check model exclusions from schema_settings
        excluded_models = self._get_schema_setting("excluded_models", [])

        # Check model name exclusions
        if model_name in excluded_models:
            logger.debug(f"Excluding model {model_name} (model name excluded)")
            return False

        # Check app.model exclusions
        full_model_name = f"{app_label}.{model_name}"
        if full_model_name in excluded_models:
            logger.debug(
                f"Excluding model {full_model_name} (full model name excluded)"
            )
            return False

        return True

    def _discover_models(self) -> List[Type[models.Model]]:
        """
        Discovers all Django models that should be included in the schema.

        Returns:
            List[Type[models.Model]]: List of valid Django models
        """
        # If registry is available and schema is registered, use registry's model discovery
        if self.registry and self.schema_name != "default":
            try:
                registry_models = self.registry.get_models_for_schema(self.schema_name)
                if registry_models:
                    logger.debug(
                        f"Using registry model discovery for schema '{self.schema_name}': {[m.__name__ for m in registry_models]}"
                    )
                    return registry_models
            except Exception as e:
                logger.warning(
                    f"Failed to get models from registry for schema '{self.schema_name}': {e}"
                )

        # Fallback to default model discovery
        models = []
        excluded_apps = self._get_schema_setting("excluded_apps", [])

        for app_config in apps.get_app_configs():
            # Skip excluded apps at the app level for efficiency
            if app_config.label in excluded_apps:
                logger.debug(
                    f"Skipping entire app {app_config.label} (excluded in schema_settings)"
                )
                continue

            for model in app_config.get_models():
                if self._is_valid_model(model):
                    models.append(model)

        return models

    def _generate_query_fields(self, models: List[Type[models.Model]]) -> None:
        """
        Generates query fields for all discovered models.
        Now supports multiple managers per model with custom naming conventions.

        Args:
            models: List of Django models to generate queries for
        """
        self._query_fields = {}

        for model in models:
            model_name = model.__name__.lower()

            # Get model managers using introspector
            from ..generators.introspector import ModelIntrospector

            introspector = ModelIntrospector(model)
            managers = introspector.get_model_managers()

            # Generate queries for each manager
            for manager_name, manager_info in managers.items():
                if manager_info.is_default:
                    # Default manager keeps standard naming
                    # Single object query
                    single_query = self.query_generator.generate_single_query(
                        model, manager_name
                    )
                    self._query_fields[model_name] = single_query

                    # List query
                    list_query = self.query_generator.generate_list_query(
                        model, manager_name
                    )
                    self._query_fields[f"{model_name}s"] = list_query

                    # Paginated query
                    if self.settings.enable_pagination:
                        paginated_query = self.query_generator.generate_paginated_query(
                            model, manager_name
                        )
                        self._query_fields[f"{model_name}s_pages"] = paginated_query
                else:
                    # Custom managers use new naming convention
                    # Single object query: modelname__custommanager
                    single_query = self.query_generator.generate_single_query(
                        model, manager_name
                    )
                    self._query_fields[f"{model_name}__{manager_name}"] = single_query

                    # List query: modelname__custommanager (plural form)
                    list_query = self.query_generator.generate_list_query(
                        model, manager_name
                    )
                    self._query_fields[f"{model_name}s__{manager_name}"] = list_query

                    # Paginated query: modelname_pages_custommanager
                    if self.settings.enable_pagination:
                        paginated_query = self.query_generator.generate_paginated_query(
                            model, manager_name
                        )
                        self._query_fields[f"{model_name}s_pages_{manager_name}"] = (
                            paginated_query
                        )

    def _generate_mutation_fields(self, models: List[Type[models.Model]]) -> None:
        """
        Generates mutation fields for all discovered models.

        Args:
            models: List of Django models to generate mutations for
        """
        self._mutation_fields = {}

        for model in models:
            mutations = self.mutation_generator.generate_all_mutations(model)
            logger.debug(
                f"Generated {len(mutations)} mutations for model {model.__name__}: {list(mutations.keys())}"
            )
            self._mutation_fields.update(mutations)

        logger.info(
            f"Total mutations generated for schema '{self.schema_name}': {len(self._mutation_fields)}"
        )
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
                logger.info(
                    f"Discovered {len(models)} models for schema '{self.schema_name}': {[m.__name__ for m in models]}"
                )

                # Generate queries
                self._generate_query_fields(models)

                # Generate mutations
                self._generate_mutation_fields(models)

                logger.info(
                    f"Schema '{self.schema_name}' generation - Query fields: {len(self._query_fields)}, Mutation fields: {len(self._mutation_fields)}"
                )

                # Create Query type with security extensions
                query_attrs = {"debug": graphene.Field(DjangoDebug, name="_debug")}
                query_attrs.update(self._query_fields)

                # Add security-related queries
                try:
                    from ..extensions.auth import MeQuery
                    from ..extensions.permissions import PermissionQuery
                    from ..extensions.rate_limiting import SecurityQuery
                    from ..extensions.validation import ValidationQuery

                    # Merge security queries
                    for query_class in [
                        MeQuery,
                        PermissionQuery,
                        ValidationQuery,
                        SecurityQuery,
                    ]:
                        for field_name, field in query_class._meta.fields.items():
                            query_attrs[field_name] = field

                    logger.info(
                        f"Security extensions integrated into schema '{self.schema_name}'"
                    )
                except ImportError as e:
                    logger.warning(
                        f"Could not import security extensions for schema '{self.schema_name}': {e}"
                    )

                # Add health monitoring queries
                try:
                    from ..extensions.health import HealthQuery

                    # Create an instance of HealthQuery to get bound methods
                    health_query_instance = HealthQuery()

                    # Merge health queries with proper resolver binding
                    for field_name, field in HealthQuery._meta.fields.items():
                        # Get the resolver method from the instance
                        resolver_method_name = f"resolve_{field_name}"
                        if hasattr(health_query_instance, resolver_method_name):
                            resolver_method = getattr(
                                health_query_instance, resolver_method_name
                            )

                            # Create a wrapper that handles the root parameter
                            def create_resolver_wrapper(method):
                                def wrapper(root, info, **kwargs):
                                    return method(info, **kwargs)

                                return wrapper

                            # Create a new field with the wrapped resolver
                            query_attrs[field_name] = graphene.Field(
                                field.type,
                                description=field.description,
                                resolver=create_resolver_wrapper(resolver_method),
                                **field.args,
                            )
                        else:
                            query_attrs[field_name] = field

                    logger.info(
                        f"Health monitoring queries integrated into schema '{self.schema_name}'"
                    )
                except ImportError as e:
                    logger.warning(
                        f"Could not import health queries for schema '{self.schema_name}': {e}"
                    )

                # Add model metadata queries
                if self.settings.show_metadata:
                    try:
                        from ..extensions.metadata import ModelMetadataQuery

                        # Create an instance of ModelMetadataQuery to get bound methods
                        metadata_query_instance = ModelMetadataQuery()
                        # Merge metadata queries with proper resolver binding
                        for (
                            field_name,
                            field,
                        ) in ModelMetadataQuery._meta.fields.items():
                            # Get the resolver method from the instance
                            resolver_method_name = f"resolve_{field_name}"
                            if hasattr(metadata_query_instance, resolver_method_name):
                                resolver_method = getattr(
                                    metadata_query_instance, resolver_method_name
                                )

                                # Create a wrapper that handles the root parameter
                                def create_resolver_wrapper(method):
                                    def wrapper(root, info, **kwargs):
                                        return method(info, **kwargs)

                                    return wrapper

                                # Create a new field with the wrapped resolver
                                query_attrs[field_name] = graphene.Field(
                                    field.type,
                                    description=field.description,
                                    resolver=create_resolver_wrapper(resolver_method),
                                    **field.args,
                                )
                            else:
                                query_attrs[field_name] = field

                        logger.info(
                            f"Model metadata queries integrated into schema '{self.schema_name}'"
                        )
                    except ImportError as e:
                        logger.warning(
                            f"Could not import metadata queries for schema '{self.schema_name}': {e}"
                        )

                query_type = type("Query", (graphene.ObjectType,), query_attrs)

                # Create Mutation type if there are mutations
                mutation_type = None
                logger.info(
                    f"Checking mutation fields for schema '{self.schema_name}': {len(self._mutation_fields)} mutations found"
                )
                #
                # Add security-related mutations
                security_mutations = {}
                try:
                    # Use hierarchical settings system to get disable_security_mutations
                    from ..conf import get_setting
                    from ..extensions.auth import (
                        LoginMutation,
                        LogoutMutation,
                        RefreshTokenMutation,
                        RegisterMutation,
                    )

                    disable_security = self.settings.disable_security_mutations
                    # get_setting(
                    # "disable_security_mutations", False, self.schema_name
                    # )

                    if not disable_security:
                        security_mutations.update(
                            {
                                "login": LoginMutation.Field(),
                                "register": RegisterMutation.Field(),
                                "refresh_token": RefreshTokenMutation.Field(),
                                "logout": LogoutMutation.Field(),
                            }
                        )
                        logger.info(
                            f"Security mutations integrated into schema '{self.schema_name}'"
                        )
                except ImportError as e:
                    logger.warning(
                        f"Could not import security mutations for schema '{self.schema_name}': {e}"
                    )

                # Combine all mutations
                all_mutations = {**self._mutation_fields, **security_mutations}

                if all_mutations:
                    # logger.info(
                    #     f"Creating Mutation type for schema '{self.schema_name}' with fields: {list(all_mutations.keys())}"
                    # )
                    mutation_type = type(
                        "Mutation", (graphene.ObjectType,), all_mutations
                    )
                else:
                    logger.info(
                        f"No mutations found for schema '{self.schema_name}', creating dummy mutation"
                    )

                    # Create dummy mutation to avoid GraphQL error
                    class DummyMutation(graphene.Mutation):
                        class Arguments:
                            pass

                        success = graphene.Boolean()

                        def mutate(self, info):
                            return DummyMutation(success=True)

                    mutation_attrs = {
                        "dummy": DummyMutation.Field(
                            description="Placeholder mutation field"
                        )
                    }
                    mutation_type = type(
                        "Mutation", (graphene.ObjectType,), mutation_attrs
                    )

                # Create Schema with security middleware
                middleware = []
                try:
                    from ..extensions.rate_limiting import GraphQLSecurityMiddleware

                    middleware.append(GraphQLSecurityMiddleware())
                    logger.info(
                        f"Security middleware integrated into schema '{self.schema_name}'"
                    )
                except ImportError as e:
                    logger.warning(
                        f"Could not import security middleware for schema '{self.schema_name}': {e}"
                    )

                # Note: Graphene Schema doesn't support middleware parameter directly
                # Middleware should be applied at the GraphQL execution level

                self._schema = graphene.Schema(
                    query=query_type,
                    mutation=mutation_type,
                    auto_camelcase=self.settings.auto_camelcase,
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
                        description=f"Auto-generated GraphQL schema for {self.schema_name}",
                        version=str(self._schema_version),
                        models=list(self._registered_models),
                    )
                    logger.info(
                        f"Schema '{self.schema_name}' registered in schema registry"
                    )
                except ImportError as e:
                    logger.warning(
                        f"Could not register schema '{self.schema_name}' in registry: {e}"
                    )

                logger.info(
                    f"Schema '{self.schema_name}' rebuilt successfully (version {self._schema_version})"
                    f"\n - Models: {len(models)}"
                    f"\n - Queries: {len(self._query_fields)}"
                    f"\n - Mutations: {len(self._mutation_fields)}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to rebuild schema '{self.schema_name}': {str(e)}",
                    exc_info=True,
                )
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
        return getattr(self, "_middleware", [])

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
            logger.info(
                f"App '{app_label}' registered for schema '{self.schema_name}' generation"
            )

    def unregister_app(self, app_label: str) -> None:
        """
        Unregisters a Django app from schema generation.

        Args:
            app_label: Django app label to unregister
        """
        if app_label not in self.settings.excluded_apps:
            self.settings.excluded_apps.append(app_label)
            self.rebuild_schema()
            logger.info(
                f"App '{app_label}' unregistered from schema '{self.schema_name}' generation"
            )

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
            logger.info(
                f"Model '{model_identifier}' registered for schema '{self.schema_name}' generation"
            )

    def unregister_model(self, model: Union[Type[models.Model], str]) -> None:
        """
        Unregisters a model from schema generation.

        Args:
            model: Django model class or model name to unregister
        """
        model_identifier = model.__name__ if isinstance(model, type) else model
        if model_identifier not in self.settings.excluded_models:
            self.settings.excluded_models.append(model_identifier)
            self.rebuild_schema()
            logger.info(
                f"Model '{model_identifier}' unregistered from schema '{self.schema_name}' generation"
            )

    def reload_app_schema(self, app_label: str) -> None:
        """
        Reloads schema for a specific app.

        Args:
            app_label: Django app label to reload
        """
        try:
            app_config = apps.get_app_config(app_label)
            models = [
                model
                for model in app_config.get_models()
                if self._is_valid_model(model)
            ]

            with self._lock:
                # Remove existing app-related fields
                for model in models:
                    model_name = model.__name__.lower()
                    # Remove queries
                    self._query_fields.pop(model_name, None)
                    self._query_fields.pop(f"{model_name}s", None)
                    self._query_fields.pop(f"{model_name}_pages", None)

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

            logger.info(
                f"Schema reloaded for app '{app_label}' in schema '{self.schema_name}'"
            )

        except Exception as e:
            logger.error(
                f"Failed to reload schema for app '{app_label}' in schema '{self.schema_name}': {str(e)}",
                exc_info=True,
            )
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

    def get_settings(self) -> Any:
        """
        Returns the schema settings for this schema.

        Returns:
            Any: Schema settings instance
        """
        return self.settings


# Global schema management functions
def get_schema_builder(schema_name: str = "default") -> SchemaBuilder:
    """
    Get or create a schema builder instance for the given schema name.

    Args:
        schema_name: Name of the schema (defaults to "default")

    Returns:
        SchemaBuilder: Schema builder instance
    """
    from .registry import schema_registry

    return SchemaBuilder(schema_name=schema_name, registry=schema_registry)


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
