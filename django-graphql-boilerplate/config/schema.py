"""
Main GraphQL schema for django-graphql-boilerplate project.
"""

import graphene
from rail_django_graphql import get_schema_builder

# Get the schema builder
SchemaBuilder = get_schema_builder()

# Build the auto-generated schema
schema_builder = SchemaBuilder('default')
auto_schema = schema_builder.build()


class Query(auto_schema.Query):
    """
    Main GraphQL Query combining auto-generated queries with custom ones.
    """
    # Custom query example
    hello = graphene.String(default_value="Hello World!")
    
    def resolve_hello(self, info):
        return "Hello from Django GraphQL Boilerplate!"


class Mutation(auto_schema.Mutation):
    """
    Main GraphQL Mutation combining auto-generated mutations with custom ones.
    """
    pass


# Create the final schema
schema = graphene.Schema(
    query=Query,
    mutation=Mutation
)