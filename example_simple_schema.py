"""
Simple Example: Exposing Auto-Generated Schema for Apps and Models

This example demonstrates how to create and expose a GraphQL schema that automatically
generates types, queries, and mutations from your Django models using the 
rail_django_graphql library.
"""

from django.apps import apps
from rail_django_graphql.core.schema import SchemaBuilder
from rail_django_graphql.core.settings import (
    SchemaSettings, 
    MutationGeneratorSettings, 
    QueryGeneratorSettings,
    TypeGeneratorSettings
)
from rail_django_graphql.core.registry import get_schema_registry
from rail_django_graphql.decorators import register_schema


# =============================================================================
# EXAMPLE 1: Basic Auto-Generated Schema
# =============================================================================

def create_basic_schema():
    """
    Create a basic auto-generated schema that includes all models from specified apps.
    """
    # Configure schema settings
    schema_settings = SchemaSettings(
        # Exclude Django's built-in apps
        excluded_apps=["admin", "auth", "contenttypes", "sessions", "messages"],
        # Enable introspection for development
        enable_introspection=True,
        # Enable GraphiQL interface
        enable_graphiql=True,
        # Auto-refresh when models change (useful for development)
        auto_refresh_on_model_change=True,
    )
    
    # Configure mutation generation
    mutation_settings = MutationGeneratorSettings(
        generate_create=True,
        generate_update=True,
        generate_delete=True,
        enable_bulk_operations=True,
        enable_nested_relations=True,
        enable_method_mutations=True,  # Convert model methods to mutations
    )
    
    # Configure query generation
    query_settings = QueryGeneratorSettings(
        enable_single_queries=True,
        enable_list_queries=True,
        enable_pagination=True,
        enable_filtering=True,
        enable_ordering=True,
    )
    
    # Configure type generation
    type_settings = TypeGeneratorSettings(
        include_pk_field=True,
        include_computed_fields=True,  # Include @property methods
        auto_camelcase_fields=False,   # Keep snake_case field names
    )
    
    # Create schema builder
    schema_builder = SchemaBuilder(
        schema_settings=schema_settings,
        mutation_settings=mutation_settings,
        query_settings=query_settings,
        type_settings=type_settings
    )
    
    # Build and return the schema
    return schema_builder.get_schema()


# =============================================================================
# EXAMPLE 2: App-Specific Schema
# =============================================================================

def create_app_specific_schema(app_names=None):
    """
    Create a schema that only includes models from specific Django apps.
    
    Args:
        app_names (list): List of app names to include. If None, includes 'test_app'
    """
    if app_names is None:
        app_names = ['test_app']
    
    # Get all models from specified apps
    included_models = []
    for app_name in app_names:
        try:
            app_config = apps.get_app_config(app_name)
            app_models = [f"{app_name}.{model._meta.model_name}" for model in app_config.get_models()]
            included_models.extend(app_models)
        except LookupError:
            print(f"Warning: App '{app_name}' not found")
    
    schema_settings = SchemaSettings(
        # Only include specified apps
        excluded_apps=["admin", "auth", "contenttypes", "sessions"],
        enable_introspection=True,
        enable_graphiql=True,
    )
    
    mutation_settings = MutationGeneratorSettings(
        generate_create=True,
        generate_update=True,
        generate_delete=True,
        enable_method_mutations=True,
    )
    
    schema_builder = SchemaBuilder(schema_settings)
    schema_builder.mutation_generator.settings = mutation_settings
    
    return schema_builder.get_schema()


# =============================================================================
# EXAMPLE 3: Model-Specific Schema with Custom Configuration
# =============================================================================

def create_model_specific_schema():
    """
    Create a schema that only exposes specific models with custom configuration.
    """
    schema_settings = SchemaSettings(
        # Exclude all apps except our target app
        excluded_apps=["admin", "auth", "contenttypes", "sessions"],
        # Exclude specific models we don't want to expose
        excluded_models=["LogEntry", "Session"],
        enable_introspection=True,
        enable_graphiql=True,
    )
    
    # Only generate mutations for specific operations
    mutation_settings = MutationGeneratorSettings(
        generate_create=True,
        generate_update=True,
        generate_delete=False,  # Disable delete mutations for safety
        enable_bulk_operations=False,  # Disable bulk operations
        enable_method_mutations=True,  # Enable custom model methods as mutations
    )
    
    # Configure queries with filtering
    query_settings = QueryGeneratorSettings(
        enable_single_queries=True,
        enable_list_queries=True,
        enable_pagination=True,
        enable_filtering=True,
        enable_ordering=True,
        default_page_size=20,
        max_page_size=100,
    )
    
    schema_builder = SchemaBuilder(
        schema_settings=schema_settings,
        mutation_settings=mutation_settings,
        query_settings=query_settings
    )
    
    return schema_builder.get_schema()


# =============================================================================
# EXAMPLE 4: Registered Schema with Schema Registry
# =============================================================================

@register_schema(
    name="blog_schema",
    description="Auto-generated GraphQL schema for blog functionality",
    version="1.0.0"
)
class BlogSchema:
    """
    Example of using the @register_schema decorator to automatically register
    a schema in the schema registry.
    """
    
    @classmethod
    def get_schema(cls):
        """Return the auto-generated schema for blog models."""
        schema_settings = SchemaSettings(
            excluded_apps=["admin", "auth", "contenttypes", "sessions"],
            enable_introspection=True,
            enable_graphiql=True,
        )
        
        mutation_settings = MutationGeneratorSettings(
            generate_create=True,
            generate_update=True,
            generate_delete=True,
            enable_method_mutations=True,
        )
        
        schema_builder = SchemaBuilder(schema_settings)
        schema_builder.mutation_generator.settings = mutation_settings
        
        return schema_builder.get_schema()


# =============================================================================
# EXAMPLE 5: Multiple Schemas with Registry
# =============================================================================

def setup_multiple_schemas():
    """
    Example of setting up multiple schemas for different purposes using the registry.
    """
    registry = get_schema_registry()
    
    # Public API Schema - Read-only
    public_schema_settings = SchemaSettings(
        excluded_apps=["admin", "auth", "contenttypes", "sessions"],
        enable_introspection=False,  # Disable introspection for security
        enable_graphiql=False,       # Disable GraphiQL for production
    )
    
    public_mutation_settings = MutationGeneratorSettings(
        generate_create=False,       # No create operations
        generate_update=False,       # No update operations  
        generate_delete=False,       # No delete operations
        enable_method_mutations=False, # No custom mutations
    )
    
    public_schema_builder = SchemaBuilder(
        schema_settings=public_schema_settings,
        mutation_settings=public_mutation_settings
    )
    
    # Register public schema
    registry.register_schema(
        name="public_api",
        description="Public read-only GraphQL API",
        version="1.0.0",
        schema=public_schema_builder.get_schema(),
        settings={
            'authentication_required': False,
            'enable_graphiql': False,
        }
    )
    
    # Admin Schema - Full CRUD
    admin_schema_settings = SchemaSettings(
        excluded_apps=["contenttypes", "sessions"],  # Include auth for admin
        enable_introspection=True,
        enable_graphiql=True,
    )
    
    admin_mutation_settings = MutationGeneratorSettings(
        generate_create=True,
        generate_update=True,
        generate_delete=True,
        enable_bulk_operations=True,
        enable_method_mutations=True,
    )
    
    admin_schema_builder = SchemaBuilder(
        schema_settings=admin_schema_settings,
        mutation_settings=admin_mutation_settings
    )
    
    # Register admin schema
    registry.register_schema(
        name="admin_api",
        description="Full-featured admin GraphQL API",
        version="1.0.0",
        schema=admin_schema_builder.get_schema(),
        settings={
            'authentication_required': True,
            'permission_classes': ['IsAdminUser'],
            'enable_graphiql': True,
        }
    )
    
    return registry


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

if __name__ == "__main__":
    # Example 1: Create basic schema
    print("Creating basic auto-generated schema...")
    basic_schema = create_basic_schema()
    print(f"Basic schema created with {len(basic_schema.type_map)} types")
    
    # Example 2: Create app-specific schema
    print("\nCreating app-specific schema...")
    app_schema = create_app_specific_schema(['test_app'])
    print(f"App-specific schema created")
    
    # Example 3: Create model-specific schema
    print("\nCreating model-specific schema...")
    model_schema = create_model_specific_schema()
    print(f"Model-specific schema created")
    
    # Example 4: Register schema using decorator
    print("\nRegistering schema using decorator...")
    blog_schema = BlogSchema.get_schema()
    print(f"Blog schema registered")
    
    # Example 5: Setup multiple schemas
    print("\nSetting up multiple schemas...")
    registry = setup_multiple_schemas()
    print(f"Registry contains {len(registry.get_all_schemas())} schemas")
    
    # List all registered schemas
    print("\nRegistered schemas:")
    for schema_name, schema_info in registry.get_all_schemas().items():
        print(f"  - {schema_name}: {schema_info.description}")


# =============================================================================
# DJANGO SETTINGS INTEGRATION
# =============================================================================

"""
To use these schemas in your Django project, add this to your settings.py:

# settings.py
GRAPHQL_AUTO_GEN = {
    'SCHEMA_CONFIG': {
        # Use one of the example schemas
        'schema_factory': 'example_simple_schema.create_basic_schema',
        
        # Or use the registry
        'use_schema_registry': True,
        'default_schema': 'blog_schema',
    },
    
    # Global settings
    'ENABLE_INTROSPECTION': True,
    'ENABLE_GRAPHIQL': True,
    'APPS_TO_EXCLUDE': ['admin', 'auth', 'contenttypes', 'sessions'],
}

# urls.py
from django.urls import path, include
from rail_django_graphql.urls import urlpatterns as graphql_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', include(graphql_urls)),
]
"""