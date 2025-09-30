#!/usr/bin/env python
"""
Final verification test for null info handling
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


def test_final_verification():
    print("=== Final Verification: Null Info Handling ===")

    # Create a LocalClient without ClientInformation
    test_client = LocalClient.objects.create(
        raison="Final Test Client", test="Final Test"
    )
    print(f"Created test LocalClient {test_client.id} without ClientInformation")

    # Get the schema
    schema_builder = get_schema_builder()
    schema = schema_builder.get_schema()

    # Test query that specifically targets our test client
    query = f"""
    {{
        localclient(id: "{test_client.id}") {{
            id
            raison
            test
            info {{
                id
                adresse
                ville
            }}
        }}
    }}
    """

    print("Executing GraphQL query for specific LocalClient...")
    result = schema.execute(query)

    success = True

    if result.errors:
        print("❌ ERRORS occurred:")
        for error in result.errors:
            print(f"  - {error}")
        success = False
    else:
        print("✅ Query executed successfully!")
        data = result.data
        if data and data.get("localclient"):
            client_data = data["localclient"]
            print(f"LocalClient ID: {client_data['id']}")
            print(f"Raison: {client_data['raison']}")
            print(f"Test: {client_data['test']}")
            print(f"Info: {client_data['info']}")

            if client_data["info"] is None:
                print("✅ SUCCESS: Info field correctly returns null!")
            else:
                print(
                    f"❌ ERROR: Info field should be null but returned: {client_data['info']}"
                )
                success = False
        else:
            print("❌ ERROR: No LocalClient data returned")
            success = False

    # Clean up
    test_client.delete()
    print(f"\nCleaned up test LocalClient {test_client.id}")

    if success:
        print("\n🎉 ALL TESTS PASSED: Null info handling is working correctly!")
        print("✅ OneToOne relationships now return null when no related object exists")
        print("✅ No more 'DoesNotExist' exceptions in GraphQL queries")
    else:
        print("\n❌ TESTS FAILED: There are still issues with null handling")

    return success


if __name__ == "__main__":
    test_final_verification()
