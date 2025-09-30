#!/usr/bin/env python
"""
Test LocalClient info field in GraphQL
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from rail_django_graphql.core.schema import get_schema_builder
from test_app.models import LocalClient, ClientInformation


def test_localclient_graphql():
    print("=== Testing LocalClient GraphQL Schema ===")

    # Get the schema
    schema_builder = get_schema_builder()
    schema = schema_builder.get_schema()

    # Test the query
    query = """
    {
        localclients {
            id
            raison
            test
            info {
                id
                adresse
                ville
            }
        }
    }
    """

    print("Executing query:")
    print(query)

    try:
        result = schema.execute(query)

        if result.errors:
            print("\nErrors:")
            for error in result.errors:
                print(f"  - {error}")

        if result.data:
            print("\nData:")
            print(result.data)

    except Exception as e:
        print(f"Exception: {e}")

    # Let's also check the schema introspection for LocalClient type
    print("\n=== Schema Introspection ===")
    introspection_query = """
    {
        __type(name: "LocalClientType") {
            name
            fields {
                name
                type {
                    name
                    kind
                }
            }
        }
    }
    """

    try:
        result = schema.execute(introspection_query)

        if result.errors:
            print("Introspection Errors:")
            for error in result.errors:
                print(f"  - {error}")

        if result.data:
            print("LocalClientType fields:")
            if result.data.get("__type") and result.data["__type"].get("fields"):
                for field in result.data["__type"]["fields"]:
                    field_name = field["name"]
                    field_type = (
                        field["type"]["name"]
                        if field["type"]["name"]
                        else field["type"]["kind"]
                    )
                    print(f"  - {field_name}: {field_type}")
            else:
                print("  No fields found or type not found")

    except Exception as e:
        print(f"Introspection Exception: {e}")


if __name__ == "__main__":
    test_localclient_graphql()
