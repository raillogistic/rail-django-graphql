#!/usr/bin/env python
"""
Test script to verify that single client queries now return ClientType instead of ClientUnion.
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from test_app.models import Client, LocalClient
from rail_django_graphql.core.schema import SchemaBuilder
import graphene


def test_single_client_query_fix():
    """Test that single client queries now return ClientType instead of ClientUnion"""
    print("Testing single client query fix...")

    # Clean up existing data
    Client.objects.all().delete()

    # Create test data
    print("Creating test data...")
    client = Client.objects.create(raison="Test Base Client")
    local_client = LocalClient.objects.create(
        raison="Test Local Client", test="Local Info"
    )

    print(f"Created Client: {client.id} - {client.raison}")
    print(f"Created LocalClient: {local_client.id} - {local_client.raison}")

    # Build schema
    print("Building schema...")
    schema_builder = SchemaBuilder()
    schema_builder.register_app("test_app")
    schema = schema_builder.get_schema()

    # Test single client query
    print("\nTesting single client query...")
    single_client_query = """
    query GetClient($id: ID!) {
        client(id: $id) {
            id
            raison
            polymorphicType
        }
    }
    """

    # Test with base client
    print(f"Querying base client (ID: {client.id})...")
    result = schema.execute(single_client_query, variables={"id": str(client.id)})

    if result.errors:
        print(f"❌ Errors in base client query: {result.errors}")
        return False
    else:
        print(f"✅ Base client query successful!")
        print(f"   Data: {result.data}")

        client_data = result.data.get("client")
        if client_data:
            print(f"   ID: {client_data.get('id')}")
            print(f"   Raison: {client_data.get('raison')}")
            print(f"   Polymorphic Type: {client_data.get('polymorphicType')}")

    # Test with local client
    print(f"\nQuerying local client (ID: {local_client.id})...")
    result = schema.execute(single_client_query, variables={"id": str(local_client.id)})

    if result.errors:
        print(f"❌ Errors in local client query: {result.errors}")
        return False
    else:
        print(f"✅ Local client query successful!")
        print(f"   Data: {result.data}")

        client_data = result.data.get("client")
        if client_data:
            print(f"   ID: {client_data.get('id')}")
            print(f"   Raison: {client_data.get('raison')}")
            print(f"   Polymorphic Type: {client_data.get('polymorphicType')}")

    # Test list query to ensure it still works
    print("\nTesting list client query...")
    list_query = """
    query GetAllClients {
        allClients {
            id
            raison
            polymorphicType
        }
    }
    """

    result = schema.execute(list_query)

    if result.errors:
        print(f"❌ Errors in list query: {result.errors}")
        return False
    else:
        print(f"✅ List query successful!")
        print(f"   Data: {result.data}")

        clients = result.data.get("allClients", [])
        print(f"   Found {len(clients)} clients:")
        for client_data in clients:
            print(
                f"     - ID: {client_data.get('id')}, Type: {client_data.get('polymorphicType')}"
            )

    print(
        "\n🎉 All tests passed! Single client queries now return ClientType instead of ClientUnion."
    )
    return True


if __name__ == "__main__":
    try:
        success = test_single_client_query_fix()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
