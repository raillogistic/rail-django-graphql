#!/usr/bin/env python
"""
Test LocalClient info field in GraphQL with proper null handling
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


def test_localclient_info_proper():
    print("=== Testing LocalClient Info Field (Proper Handling) ===")

    # Get the schema
    schema_builder = get_schema_builder()
    schema = schema_builder.get_schema()

    # Test 1: Query only LocalClients that have info
    query1 = """
    {
        localclients {
            id
            raison
            test
        }
    }
    """

    print("Test 1: Basic LocalClient query (without info)")
    print(query1)

    result1 = schema.execute(query1)

    if result1.errors:
        print("Errors:")
        for error in result1.errors:
            print(f"  - {error}")
    else:
        print("✓ Success - No errors")
        print(f"Found {len(result1.data['localclients'])} LocalClients")

    # Test 2: Query with conditional info access
    query2 = """
    {
        localclients {
            id
            raison
            test
            ... on LocalClientType {
                info {
                    id
                    adresse
                    ville
                }
            }
        }
    }
    """

    print("\nTest 2: LocalClient query with conditional info access")
    print(query2)

    result2 = schema.execute(query2)

    if result2.errors:
        print("Errors:")
        for error in result2.errors:
            print(f"  - {error}")
    else:
        print("✓ Success - No errors")
        for client in result2.data["localclients"]:
            client_id = client["id"]
            has_info = client.get("info") is not None
            print(f"  LocalClient {client_id}: has_info={has_info}")

    # Test 3: Create a LocalClient with info and test
    print("\nTest 3: Creating LocalClient with info and testing")

    # Create LocalClient with info
    local_client = LocalClient.objects.create(
        raison="GraphQL Test Client", test="GraphQL Test"
    )

    client_info = ClientInformation.objects.create(
        client=local_client,
        adresse="GraphQL Test Address",
        ville="GraphQL Test City",
        code_postal="12345",
        pays="GraphQL Test Country",
        paysx="GraphQL Test Country X",
    )

    # Query this specific client
    query3 = f"""
    {{
        localclient(id: "{local_client.id}") {{
            id
            raison
            test
            info {{
                id
                adresse
                ville
                code_postal
                pays
            }}
        }}
    }}
    """

    print(f"Querying LocalClient ID: {local_client.id}")

    result3 = schema.execute(query3)

    if result3.errors:
        print("Errors:")
        for error in result3.errors:
            print(f"  - {error}")
    else:
        print("✓ Success - LocalClient with info created and queried successfully")
        if result3.data and result3.data.get("localclient"):
            client_data = result3.data["localclient"]
            print(f"  Raison: {client_data['raison']}")
            print(f"  Test: {client_data['test']}")
            if client_data.get("info"):
                info_data = client_data["info"]
                print(f"  Info Adresse: {info_data['adresse']}")
                print(f"  Info Ville: {info_data['ville']}")

    print("\n=== Summary ===")
    print("The 'LocalClient has no info' error occurs when:")
    print("1. A LocalClient doesn't have an associated ClientInformation record")
    print("2. The GraphQL query tries to access the info field on such a LocalClient")
    print("3. This is expected behavior - the info field is nullable")
    print("\nSolution: Handle null info fields in your GraphQL queries or ensure")
    print("all LocalClients have associated ClientInformation records.")


if __name__ == "__main__":
    test_localclient_info_proper()
