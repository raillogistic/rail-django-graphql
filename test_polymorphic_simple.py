#!/usr/bin/env python3
"""
Simple test to verify polymorphic_type field works with existing database setup.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

if not settings.configured:
    django.setup()

from test_app.models import Client
from rail_django_graphql.core.schema import SchemaBuilder


def test_polymorphic_type_field():
    """Test that polymorphic_type field works for client queries."""

    try:
        # Clean up any existing data
        Client.objects.all().delete()

        # Create test data - just base Client for now
        client = Client.objects.create(raison="Test Client Base")

        print(f"Created Client ID: {client.id}")

        # Build schema
        schema_builder = SchemaBuilder()
        schema = schema_builder.build()

        # Test 1: List query with polymorphic_type field
        list_query = """
        query {
            clients {
                id
                raison
                uppercaseRaison
                polymorphicType
            }
        }
        """

        print("\n=== Testing List Query ===")
        result = schema.execute(list_query)

        if result.errors:
            print(f"GraphQL Errors: {result.errors}")
            return False

        clients_data = result.data["clients"]
        print(f"Retrieved {len(clients_data)} clients from list query")

        for client_data in clients_data:
            print(
                f"Client ID: {client_data['id']}, Type: {client_data['polymorphicType']}, Raison: {client_data['raison']}"
            )

        # Test 2: Single client query by ID
        single_query = f"""
        query {{
            client(id: {client.id}) {{
                id
                raison
                uppercaseRaison
                polymorphicType
            }}
        }}
        """

        print(f"\n=== Testing Single Client Query (ID: {client.id}) ===")
        result = schema.execute(single_query)

        if result.errors:
            print(f"GraphQL Errors: {result.errors}")
            return False

        client_data = result.data["client"]
        if client_data:
            print(
                f"Single Client - ID: {client_data['id']}, Type: {client_data['polymorphicType']}, Raison: {client_data['raison']}"
            )

            if client_data["polymorphicType"] != "Client":
                print(
                    f"ERROR: Expected 'Client' type, got: {client_data['polymorphicType']}"
                )
                return False
        else:
            print("ERROR: No client data returned")
            return False

        print("\n✅ SUCCESS: polymorphic_type field works!")
        print("- List query returns polymorphic_type field")
        print("- Single client query returns correct polymorphic_type")
        print("- Both queries use ClientType and include polymorphic_type field")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Clean up
        Client.objects.all().delete()


if __name__ == "__main__":
    success = test_polymorphic_type_field()
    sys.exit(0 if success else 1)
