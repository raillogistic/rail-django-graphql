#!/usr/bin/env python
"""
Test GraphQL mutation to see debug logs.
"""

import os
import sys
import django
import logging

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

# Set up logging to see debug messages
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(name)s - %(message)s")

from test_app.models import Tag
from rail_django_graphql.schema import schema


def test_graphql_unique_error():
    """Test GraphQL mutation with unique constraint error."""

    print("Creating first tag...")
    # Create first tag
    tag1 = Tag.objects.create(name="test_graphql_unique")
    print(f"Created: {tag1.name}")

    print("\nTesting GraphQL mutation with duplicate name...")

    # Test GraphQL mutation
    mutation = """
    mutation {
        create_tag(input: {name: "test_graphql_unique"}) {
            ok
            errors {
                field
                message
            }
        }
    }
    """

    result = schema.execute(mutation)

    print(f"\nGraphQL execution result:")
    print(f"Data: {result.data}")

    if result.errors:
        print(f"GraphQL Errors: {result.errors}")

    if result.data and result.data.get("create_tag"):
        create_result = result.data["create_tag"]
        print(f"OK: {create_result.get('ok')}")

        errors = create_result.get("errors", [])
        print(f"Number of errors: {len(errors)}")

        for i, error in enumerate(errors):
            print(f"Error {i+1}:")
            print(f"  Field: {error.get('field')}")
            print(f"  Message: {error.get('message')}")

    # Clean up
    Tag.objects.filter(name="test_graphql_unique").delete()
    print("\nCleanup completed.")


if __name__ == "__main__":
    test_graphql_unique_error()
