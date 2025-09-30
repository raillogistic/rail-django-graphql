#!/usr/bin/env python
"""
Test script to verify cascading polymorphic type resolution.
When querying "clients", both Client and LocalClient objects should be returned
with proper type resolution based on their actual instance types.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

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

# Create tables
from django.core.management import execute_from_command_line

execute_from_command_line(["manage.py", "migrate", "--run-syncdb"])

from rail_django_graphql.core.schema import SchemaBuilder
from test_app.models import Client, LocalClient, ClientInformation
import json


def test_cascading_polymorphic_resolution():
    """Test that clients query returns both Client and LocalClient with proper type resolution."""

    print("=== Testing Cascading Polymorphic Type Resolution ===")

    # Create test data
    print("\n1. Creating test data...")

    # Create a regular Client
    regular_client = Client.objects.create(raison="Regular Client Corp")
    print(f"Created regular Client: {regular_client.id} - {regular_client.raison}")

    # Create a LocalClient (inherits from Client)
    local_client = LocalClient.objects.create(
        raison="Local Client Ltd", test="Local test value"
    )
    print(
        f"Created LocalClient: {local_client.id} - {local_client.raison} - {local_client.test}"
    )

    # Create ClientInformation for both
    regular_info = ClientInformation.objects.create(
        client=regular_client,
        adresse="123 Regular St",
        ville="Regular City",
        code_postal="12345",
        pays="Regular Country",
        paysx="Regular CountryX",
    )

    local_info = ClientInformation.objects.create(
        client=local_client,
        adresse="456 Local Ave",
        ville="Local Town",
        code_postal="67890",
        pays="Local Country",
        paysx="Local CountryX",
    )

    print(f"Created ClientInformation for both clients")

    # Build schema
    print("\n2. Building GraphQL schema...")
    builder = SchemaBuilder()
    schema = builder.get_schema()

    # Debug: Check what queries are available
    print("\n3. Available queries:")
    try:
        query_type = schema.type_map.get("Query")
        if query_type and hasattr(query_type, "fields"):
            for field_name, field in query_type.fields.items():
                print(f"  - {field_name}: {field.type}")
        else:
            print("  No Query type found in schema")
    except Exception as e:
        print(f"  Error accessing schema: {e}")

    # Debug: Check if clients query exists
    print("\n4. Checking for clients query...")
    try:
        if (
            query_type
            and hasattr(query_type, "fields")
            and "clients" in query_type.fields
        ):
            print("  clients query found")
        else:
            print("  clients query NOT found")
    except Exception as e:
        print(f"  Error checking clients query: {e}")

    # Test query that should return both types
    print("\n5. Testing clients list query...")

    # Query for all clients - should return both Client and LocalClient instances
    query = """
    query {
        clients {
            __typename
            ... on ClientType {
                id
                raison
                uppercase_raison
                info {
                    adresse
                    ville
                }
            }
            ... on LocalClientType {
                id
                raison
                uppercase_raison
                test
                info {
                    adresse
                    ville
                }
            }
        }
    }
    """

    try:
        result = schema.execute(query)

        if result.errors:
            print(f"GraphQL Errors: {[str(error) for error in result.errors]}")
            return False

        print("Query executed successfully!")
        print("Result:")
        print(json.dumps(result.data, indent=2))

        # Verify results
        clients_data = result.data.get("clients", [])
        print(f"\nFound {len(clients_data)} clients")

        # Check if we have both types
        has_regular_client = False
        has_local_client = False

        for client_data in clients_data:
            print(f"\nClient ID {client_data['id']}:")
            print(f"  - raison: {client_data['raison']}")
            print(f"  - uppercase_raison: {client_data['uppercase_raison']}")

            if "test" in client_data:
                print(f"  - test: {client_data['test']} (LocalClient)")
                has_local_client = True
            else:
                print(f"  - No 'test' field (Regular Client)")
                has_regular_client = True

            if client_data.get("info"):
                print(f"  - info.adresse: {client_data['info']['adresse']}")

        success = has_regular_client and has_local_client

        if success:
            print(
                f"\n✓ Success: Found both Client and LocalClient instances with proper type resolution"
            )
        else:
            print(
                f"\n✗ Failed: Missing client types - Regular: {has_regular_client}, Local: {has_local_client}"
            )

        return success

    except Exception as e:
        print(f"\nException during query execution: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Clean up
        print(f"\n5. Cleaning up...")
        regular_info.delete()
        local_info.delete()
        regular_client.delete()
        local_client.delete()
        print("Cleanup completed")


if __name__ == "__main__":
    success = test_cascading_polymorphic_resolution()
    if success:
        print("\n✓ Test passed: Cascading polymorphic type resolution works correctly")
    else:
        print("\n✗ Test failed: Cascading polymorphic type resolution needs fixing")

    sys.exit(0 if success else 1)
