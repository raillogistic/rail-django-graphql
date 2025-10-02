"""
Schema Registry System for rail-django-graphql library.

This module provides a centralized registry for managing multiple GraphQL schemas,
their configurations, and automatic discovery mechanisms.
"""

from typing import Dict, List, Optional, Set, Type, Any, Callable
import logging
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from django.apps import apps
from django.db import models
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


@dataclass
class SchemaInfo:
    """Information about a registered schema."""
    name: str
    description: str = ""
    version: str = "1.0.0"
    apps: List[str] = field(default_factory=list)
    models: List[str] = field(default_factory=list)
    exclude_models: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    schema_class: Optional[Type] = None
    auto_discover: bool = True
    enabled: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SchemaRegistry:
    """
    Central registry for managing multiple GraphQL schemas.
    
    This registry allows for:
    - Multiple schema registration and management
    - Automatic schema discovery
    - Schema-specific configuration
    - Dynamic schema loading and unloading
    """
    
    def __init__(self):
        self._schemas: Dict[str, SchemaInfo] = {}
        self._schema_builders: Dict[str, Any] = {}
        self._discovery_hooks: List[Callable] = []
        self._lock = threading.Lock()
        self._initialized = False
    
    def register_schema(
        self,
        name: str,
        description: str = "",
        version: str = "1.0.0",
        apps: Optional[List[str]] = None,
        models: Optional[List[str]] = None,
        exclude_models: Optional[List[str]] = None,
        settings: Optional[Dict[str, Any]] = None,
        schema_class: Optional[Type] = None,
        auto_discover: bool = True,
        enabled: bool = True
    ) -> SchemaInfo:
        """
        Register a new GraphQL schema.
        
        Args:
            name: Unique schema name
            description: Schema description
            version: Schema version
            apps: List of Django apps to include
            models: List of specific models to include
            exclude_models: List of models to exclude
            settings: Schema-specific settings
            schema_class: Custom schema class
            auto_discover: Enable automatic discovery
            enabled: Whether schema is enabled
            
        Returns:
            SchemaInfo instance
        """
        # Run pre-registration hooks
        kwargs = {
            'description': description,
            'version': version,
            'apps': apps,
            'models': models,
            'exclude_models': exclude_models,
            'settings': settings,
            'schema_class': schema_class,
            'auto_discover': auto_discover,
            'enabled': enabled
        }
        modified_kwargs = self._run_pre_registration_hooks(name, **kwargs)
        
        with self._lock:
            if name in self._schemas:
                logger.warning(f"Schema '{name}' already registered, updating...")
            
            schema_info = SchemaInfo(
                name=name,
                description=modified_kwargs.get('description', description),
                version=modified_kwargs.get('version', version),
                apps=modified_kwargs.get('apps', apps) or [],
                models=modified_kwargs.get('models', models) or [],
                exclude_models=modified_kwargs.get('exclude_models', exclude_models) or [],
                settings=modified_kwargs.get('settings', settings) or {},
                schema_class=modified_kwargs.get('schema_class', schema_class),
                auto_discover=modified_kwargs.get('auto_discover', auto_discover),
                enabled=modified_kwargs.get('enabled', enabled)
            )
            
            self._schemas[name] = schema_info
            logger.info(f"Registered schema: {name}")
            
            # Run post-registration hooks
            self._run_post_registration_hooks(schema_info)
            
            return schema_info
    
    def unregister_schema(self, name: str) -> bool:
        """
        Unregister a schema.
        
        Args:
            name: Schema name to unregister
            
        Returns:
            True if schema was unregistered, False if not found
        """
        with self._lock:
            if name in self._schemas:
                del self._schemas[name]
                if name in self._schema_builders:
                    del self._schema_builders[name]
                logger.info(f"Unregistered schema: {name}")
                return True
            return False
    
    def get_schema(self, name: str) -> Optional[SchemaInfo]:
        """
        Get schema information by name.
        
        Args:
            name: Schema name
            
        Returns:
            SchemaInfo instance or None if not found
        """
        return self._schemas.get(name)
    
    def list_schemas(self, enabled_only: bool = False) -> List[SchemaInfo]:
        """
        List all registered schemas.
        
        Args:
            enabled_only: Only return enabled schemas
            
        Returns:
            List of SchemaInfo instances
        """
        schemas = list(self._schemas.values())
        if enabled_only:
            schemas = [s for s in schemas if s.enabled]
        return schemas
    
    def get_schema_names(self, enabled_only: bool = False) -> List[str]:
        """
        Get list of schema names.
        
        Args:
            enabled_only: Only return enabled schema names
            
        Returns:
            List of schema names
        """
        return [s.name for s in self.list_schemas(enabled_only)]
    
    def enable_schema(self, name: str) -> bool:
        """
        Enable a schema.
        
        Args:
            name: Schema name
            
        Returns:
            True if schema was enabled, False if not found
        """
        schema = self.get_schema(name)
        if schema:
            schema.enabled = True
            logger.info(f"Enabled schema: {name}")
            return True
        return False
    
    def disable_schema(self, name: str) -> bool:
        """
        Disable a schema.
        
        Args:
            name: Schema name
            
        Returns:
            True if schema was disabled, False if not found
        """
        schema = self.get_schema(name)
        if schema:
            schema.enabled = False
            logger.info(f"Disabled schema: {name}")
            return True
        return False
    
    def get_schema_builder(self, name: str):
        """
        Get or create a schema builder for the given schema.
        
        Args:
            name: Schema name
            
        Returns:
            Schema builder instance
        """
        if name not in self._schema_builders:
            schema_info = self.get_schema(name)
            if not schema_info:
                raise ValueError(f"Schema '{name}' not found")
            
            if not schema_info.enabled:
                raise ValueError(f"Schema '{name}' is disabled")
            
            # Import SchemaBuilder to avoid circular imports
            try:
                from .schema import SchemaBuilder
                from ..conf import get_schema_settings
                
                # Get schema-specific settings
                settings = get_schema_settings(name)
                
                # Create schema builder with schema-specific settings
                builder = SchemaBuilder(settings=settings, schema_name=name)
                self._schema_builders[name] = builder
                
            except ImportError as e:
                logger.error(f"Could not import SchemaBuilder: {e}")
                raise
        
        return self._schema_builders[name]
    
    def discover_schemas(self) -> None:
        """
        Automatically discover schemas from Django apps.
        """
        if self._initialized:
            return
        
        logger.info("Starting schema discovery...")
        
        # Look for schema configurations in Django apps
        for app_config in apps.get_app_configs():
            self._discover_app_schemas(app_config)
        
        # Run discovery hooks
        for hook in self._discovery_hooks:
            try:
                hook(self)
            except Exception as e:
                logger.error(f"Error running discovery hook: {e}")
        
        self._initialized = True
        logger.info(f"Schema discovery completed. Found {len(self._schemas)} schemas.")
    
    def auto_discover_schemas(self) -> int:
        """
        Automatically discover and register schemas from Django apps.
        
        Returns:
            Number of schemas discovered and registered
        """
        initial_count = len(self._schemas)
        
        logger.info("Starting automatic schema discovery...")
        
        # Look for schema configurations in Django apps
        for app_config in apps.get_app_configs():
            self._discover_app_schemas(app_config)
        
        discovered_count = len(self._schemas) - initial_count
        logger.info(f"Auto-discovery completed. Discovered {discovered_count} new schemas.")
        
        return discovered_count
    
    def _discover_app_schemas(self, app_config) -> None:
        """
        Discover schemas in a specific Django app.
        
        Args:
            app_config: Django app configuration
        """
        app_name = app_config.name
        
        # Look for graphql_schema.py or schema.py in the app
        schema_modules = [
            f"{app_name}.graphql_schema",
            f"{app_name}.schema",
            f"{app_name}.graphql.schema"
        ]
        
        for module_path in schema_modules:
            try:
                module = import_string(module_path)
                
                # Look for SCHEMA_CONFIG or schema configuration
                if hasattr(module, 'SCHEMA_CONFIG'):
                    config = module.SCHEMA_CONFIG
                    self._register_from_config(app_name, config)
                
                # Look for register_schema function
                if hasattr(module, 'register_schema'):
                    module.register_schema(self)
                
                logger.debug(f"Discovered schema configuration in {module_path}")
                break
                
            except (ImportError, AttributeError):
                continue
    
    def _register_from_config(self, app_name: str, config: Dict[str, Any]) -> None:
        """
        Register schema from configuration dictionary.
        
        Args:
            app_name: Django app name
            config: Schema configuration
        """
        schema_name = config.get('name', f"{app_name}_schema")
        
        self.register_schema(
            name=schema_name,
            description=config.get('description', f"Auto-discovered schema for {app_name}"),
            version=config.get('version', '1.0.0'),
            apps=config.get('apps', [app_name]),
            models=config.get('models', []),
            exclude_models=config.get('exclude_models', []),
            settings=config.get('settings', {}),
            auto_discover=config.get('auto_discover', True),
            enabled=config.get('enabled', True)
        )
    
    def add_discovery_hook(self, hook: Callable) -> None:
        """
        Add a discovery hook function.
        
        Args:
            hook: Function that takes the registry as argument
        """
        self._discovery_hooks.append(hook)
    
    def add_pre_registration_hook(self, hook: Callable) -> None:
        """
        Add a pre-registration hook function.
        
        Args:
            hook: Function called before schema registration with (registry, schema_name, **kwargs)
        """
        if not hasattr(self, '_pre_registration_hooks'):
            self._pre_registration_hooks = []
        self._pre_registration_hooks.append(hook)
    
    def add_post_registration_hook(self, hook: Callable) -> None:
        """
        Add a post-registration hook function.
        
        Args:
            hook: Function called after schema registration with (registry, schema_info)
        """
        if not hasattr(self, '_post_registration_hooks'):
            self._post_registration_hooks = []
        self._post_registration_hooks.append(hook)
    
    def remove_discovery_hook(self, hook: Callable) -> bool:
        """
        Remove a discovery hook function.
        
        Args:
            hook: Hook function to remove
            
        Returns:
            True if hook was removed, False if not found
        """
        try:
            self._discovery_hooks.remove(hook)
            return True
        except ValueError:
            return False
    
    def clear_discovery_hooks(self) -> None:
        """Clear all discovery hooks."""
        self._discovery_hooks.clear()
        if hasattr(self, '_pre_registration_hooks'):
            self._pre_registration_hooks.clear()
        if hasattr(self, '_post_registration_hooks'):
            self._post_registration_hooks.clear()
    
    def get_discovery_hooks(self) -> List[Callable]:
        """Get list of all discovery hooks."""
        return self._discovery_hooks.copy()
    
    def _run_pre_registration_hooks(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Run pre-registration hooks and collect modifications.
        
        Args:
            name: Schema name
            **kwargs: Registration parameters
            
        Returns:
            Modified registration parameters
        """
        if not hasattr(self, '_pre_registration_hooks'):
            return kwargs
        
        modified_kwargs = kwargs.copy()
        
        for hook in self._pre_registration_hooks:
            try:
                result = hook(self, name, **modified_kwargs)
                if isinstance(result, dict):
                    modified_kwargs.update(result)
                logger.debug(f"Pre-registration hook executed for schema: {name}")
            except Exception as e:
                logger.error(f"Error in pre-registration hook for schema '{name}': {e}")
        
        return modified_kwargs
    
    def _run_post_registration_hooks(self, schema_info: SchemaInfo) -> None:
        """
        Run post-registration hooks.
        
        Args:
            schema_info: Registered schema information
        """
        if not hasattr(self, '_post_registration_hooks'):
            return
        
        for hook in self._post_registration_hooks:
            try:
                hook(self, schema_info)
                logger.debug(f"Post-registration hook executed for schema: {schema_info.name}")
            except Exception as e:
                logger.error(f"Error in post-registration hook for schema '{schema_info.name}': {e}")
    
    def clear_schemas(self) -> None:
        """Clear all registered schemas."""
        with self._lock:
            self._schemas.clear()
            self._schema_builders.clear()
            logger.info("Cleared all schemas")
    
    def get_models_for_schema(self, name: str) -> List[Type[models.Model]]:
        """
        Get Django models for a specific schema.
        
        Args:
            name: Schema name
            
        Returns:
            List of Django model classes
        """
        schema_info = self.get_schema(name)
        if not schema_info:
            return []
        
        models_list = []
        
        # Get models from specified apps
        for app_name in schema_info.apps:
            try:
                app_models = apps.get_app_config(app_name).get_models()
                models_list.extend(app_models)
            except LookupError:
                logger.warning(f"App '{app_name}' not found for schema '{name}'")
        
        # Filter by specific models if specified
        if schema_info.models:
            model_names = set(schema_info.models)
            models_list = [m for m in models_list if m.__name__ in model_names]
        
        # Exclude models if specified
        if schema_info.exclude_models:
            exclude_names = set(schema_info.exclude_models)
            models_list = [m for m in models_list if m.__name__ not in exclude_names]
        
        return models_list
    
    def validate_schema(self, name: str) -> Dict[str, Any]:
        """
        Validate a schema configuration.
        
        Args:
            name: Schema name
            
        Returns:
            Validation results dictionary
        """
        schema_info = self.get_schema(name)
        if not schema_info:
            return {"valid": False, "errors": [f"Schema '{name}' not found"]}
        
        errors = []
        warnings = []
        
        # Validate apps exist
        for app_name in schema_info.apps:
            try:
                apps.get_app_config(app_name)
            except LookupError:
                errors.append(f"App '{app_name}' not found")
        
        # Validate models exist
        models_list = self.get_models_for_schema(name)
        if not models_list and schema_info.apps:
            warnings.append(f"No models found for schema '{name}'")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "model_count": len(models_list)
        }
    
    def schema_exists(self, name: str) -> bool:
        """
        Check if a schema exists in the registry.
        
        Args:
            name: Schema name to check
            
        Returns:
            True if schema exists, False otherwise
        """
        return name in self._schemas
    
    def clear(self) -> None:
        """
        Clear all schemas from the registry.
        
        This method removes all registered schemas and builders.
        Useful for testing and cleanup operations.
        """
        with self._lock:
            self._schemas.clear()
            self._schema_builders.clear()
            logger.info("Cleared all schemas from registry")


# Global schema registry instance
schema_registry = SchemaRegistry()


# Convenience functions
def register_schema(*args, **kwargs) -> SchemaInfo:
    """Register a schema using the global registry."""
    return schema_registry.register_schema(*args, **kwargs)


def get_schema(name: str) -> Optional[SchemaInfo]:
    """Get schema info using the global registry."""
    return schema_registry.get_schema(name)


def get_schema_builder(name: str):
    """Get schema builder using the global registry."""
    return schema_registry.get_schema_builder(name)


def list_schemas(enabled_only: bool = False) -> List[SchemaInfo]:
    """List schemas using the global registry."""
    return schema_registry.list_schemas(enabled_only)