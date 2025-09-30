#!/usr/bin/env python
"""
Test foreign key error field extraction.
"""

import os
import sys
import django
import json

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from test_app.models import Post, Category
from django.test import RequestFactory
from graphene.test import Client
from rail_django_graphql.core.schema import SchemaBuilder


def test_foreign_key_error_extraction():
    """Test field extraction for foreign key errors."""

    print("Setting up GraphQL schema...")

    # Create schema
    schema_builder = SchemaBuilder()
    schema = schema_builder.get_schema()
    client = Client(schema)

    # Test creating post with invalid category ID
    print("\nTesting post creation with invalid category ID...")

    mutation = """
    mutation {
        create_post(input: {
            title: "Test Post",
            content: "Test Content", 
            category: "999"
        }) {
            ok
            object {
                id
                title
            }
            errors {
                field
                message
            }
        }
    }
    """

    result = client.execute(mutation)
    print(f"GraphQL result: {json.dumps(result, indent=2)}")

    # Check if we have errors with field information
    if "data" in result and result["data"] and result["data"]["create_post"]["errors"]:
        errors = result["data"]["create_post"]["errors"]
        for error in errors:
            print(f"Error field: {error['field']}")
            print(f"Error message: {error['message']}")

            # Verify field extraction worked
            if error["field"] == "category":
                print("✅ Foreign key field extraction successful!")
            else:
                print("❌ Foreign key field extraction failed!")
    else:
        print("No errors found in response")

    print("\nTest completed.")


if __name__ == "__main__":
    test_foreign_key_error_extraction()
