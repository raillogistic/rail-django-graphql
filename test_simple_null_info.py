#!/usr/bin/env python
"""
Simple test for null info handling without complex filters
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


def test_simple_null_info():
    print("=== Testing Simple Null Info Handling ===")

    # First, create a LocalClient without ClientInformation
    local_client = LocalClient.objects.create(
        raison="Test Client Without Info", test="Test Value"
    )
    print(f"Created LocalClient {local_client.id} without ClientInformation")

    # Get the schema
    schema_builder = get_schema_builder()
    schema = schema_builder.get_schema()

    # Test simple query without filters
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

    print("Testing simple GraphQL query:")
    print(query)

    result = schema.execute(query)

    if result.errors:
        print("❌ Errors occurred:")
        for error in result.errors:
            print(f"  - {error}")
    else:
        print("✅ Query executed successfully!")
        data = result.data
        if data and data.get("localclients"):
            for client_data in data["localclients"]:
                print(f"LocalClient ID: {client_data['id']}")
                print(f"Raison: {client_data['raison']}")
                print(f"Test: {client_data['test']}")
                print(f"Info: {client_data['info']}")

                if client_data["id"] == str(local_client.id):
                    if client_data["info"] is None:
                        print("✅ Info field correctly returns null for test client!")
                    else:
                        print(
                            "❌ Info field should be null but returned:",
                            client_data["info"],
                        )
                print("---")
        else:
            print("❌ No LocalClient data returned")

    # Clean up - delete the test LocalClient
    local_client.delete()
    print(f"\nCleaned up test LocalClient {local_client.id}")


if __name__ == "__main__":
    test_simple_null_info()
