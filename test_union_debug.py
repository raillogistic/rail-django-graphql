#!/usr/bin/env python
"""
Test script to debug union type creation for polymorphic models.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath("."))

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "polymorphic",
            "test_app",
        ],
        USE_TZ=True,
        SECRET_KEY="test-secret-key",
    )

# Setup Django
django.setup()

# Create database tables
from django.db import connection
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from test_app.models import Client, LocalClient, ClientInformation

# Create tables manually
with connection.schema_editor() as schema_editor:
    # Create Django's built-in tables first
    schema_editor.create_model(ContentType)
    schema_editor.create_model(User)

    # Create our app tables
    schema_editor.create_model(ClientInformation)
    schema_editor.create_model(Client)
    schema_editor.create_model(LocalClient)
from rail_django_graphql.core.schema import SchemaBuilder
from rail_django_graphql.generators.queries import QueryGenerator
from rail_django_graphql.generators.inheritance import inheritance_handler


def test_union_creation():
    """Test union type creation for Client model"""
    print("Testing union type creation for Client model...")

    # Create test data - first create the LocalClient, then the ClientInformation
    local_client = LocalClient.objects.create(
        raison="Test Local Client", test="Test Info"
    )

    client_info = ClientInformation.objects.create(
        client=local_client,  # Link to the client
        adresse="123 Test St",
        ville="Test City",
        code_postal="12345",
        pays="Test Country",
        paysx="Test Country X",
    )

    print(f"Created LocalClient: {local_client}")
    print(f"LocalClient type: {type(local_client)}")
    print(
        f"LocalClient polymorphic_ctype: {getattr(local_client, 'polymorphic_ctype', 'None')}"
    )
    print(f"Created ClientInformation: {client_info}")

    # Test inheritance analysis
    analysis = inheritance_handler.analyze_model_inheritance(Client)
    print(f"\nInheritance analysis for Client:")
    print(f"  - Analysis keys: {list(analysis.keys())}")
    print(f"  - Child models: {[m.__name__ for m in analysis['child_models']]}")
    print(f"  - Parent models: {[m.__name__ for m in analysis['parent_models']]}")

    # Create schema builder and test union creation
    schema_builder = SchemaBuilder()
    schema_builder.register_app("test_app")

    # Get type generator
    type_generator = schema_builder.type_generator

    # Test union creation
    union_type = inheritance_handler.create_union_for_inheritance_tree(
        Client, type_generator
    )
    print(f"\nUnion type created: {union_type}")

    if union_type:
        print(f"Union name: {union_type.__name__}")
        print(f"Union types: {[t.__name__ for t in union_type._meta.types]}")

        # Test resolve_type
        resolved_type = union_type.resolve_type(local_client, None)
        print(f"Resolved type for LocalClient: {resolved_type}")

        # Test the query generator directly
        query_generator = QueryGenerator(type_generator)

        # Debug the polymorphic check
        print(f"\nDebugging polymorphic check for Client model:")
        print(f"Has _meta: {hasattr(Client, '_meta')}")
        if hasattr(Client, "_meta"):
            print(
                f"Has polymorphic_ctype: {hasattr(Client._meta, 'polymorphic_ctype')}"
            )
            if hasattr(Client._meta, "polymorphic_ctype"):
                print(f"polymorphic_ctype value: {Client._meta.polymorphic_ctype}")

        # Test inheritance analysis
        analysis = inheritance_handler.analyze_model_inheritance(Client)
        print(f"Inheritance analysis: {analysis}")

        client_query_field = query_generator.generate_single_query(Client)
        print(f"\nQuery generator field type: {client_query_field.type}")
        print(
            f"Query generator field type name: {getattr(client_query_field.type, '__name__', 'No name')}"
        )

        # Build schema to see if union is properly registered
        schema = schema_builder.get_schema()
        print(f"\nSchema built successfully")

        # Check what type the client query actually returns
        query_type = schema.query
        if hasattr(query_type, "_meta") and hasattr(query_type._meta, "fields"):
            client_field = query_type._meta.fields.get("client")
            if client_field:
                print(f"Client query field type: {client_field.type}")
                print(
                    f"Client query field type name: {getattr(client_field.type, '__name__', 'No name')}"
                )
            else:
                print("No client query field found")
                print(f"Available query fields: {list(query_type._meta.fields.keys())}")
        else:
            print("Could not access query fields")

        # Test query
        query = """
        query {
            client(id: "1") {
                ... on ClientType {
                    id
                    raison
                }
                ... on LocalClientType {
                    id
                    raison
                    test
                }
            }
        }
        """

        print(f"\nExecuting query: {query}")
        result = schema.execute(query)

        if result.errors:
            print("GraphQL Errors:")
            for error in result.errors:
                print(f"  - {error}")
        else:
            print(f"Query result: {result.data}")
    else:
        print("No union type created")


if __name__ == "__main__":
    test_union_creation()
