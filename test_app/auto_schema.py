"""
Auto-generated GraphQL schema for test_app using the Django GraphQL Auto-Generation system.
"""

from rail_django_graphql.core.schema import SchemaBuilder
from rail_django_graphql.core.settings import SchemaSettings, MutationGeneratorSettings

# Configure the auto-generation settings
mutation_settings = MutationGeneratorSettings(
    generate_create=True,
    generate_update=True,
    generate_delete=True,
    enable_nested_relations=True,  # Enable automatic dual field generation
    enable_method_mutations=True,  # Enable method-to-mutation conversion
)

schema_settings = SchemaSettings(
    auto_refresh_on_model_change=True,
    excluded_apps=["admin", "auth", "contenttypes", "sessions"],
)

# Build the auto-generated schema
schema_builder = SchemaBuilder(schema_settings)
schema_builder.mutation_generator.settings = mutation_settings

# Get the auto-generated schema
auto_schema = schema_builder.get_schema()
