"""
Main GraphQL schema for django-graphql-boilerplate project.
"""

from rail_django_graphql.core.schema import get_schema as get_auto_schema

# Return the auto-generated GraphQL schema managed by the library
schema = get_auto_schema(schema_name="default")