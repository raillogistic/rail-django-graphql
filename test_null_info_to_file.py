#!/usr/bin/env python
"""
Test for null info handling that writes output to a file
"""

import os
import sys
import django
import traceback

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from rail_django_graphql.core.schema import get_schema_builder
from test_app.models import LocalClient, ClientInformation


def test_null_info():
    output_file = "test_null_info_output.txt"

    with open(output_file, "w") as f:
        f.write("=== Testing Null Info Handling ===\n")

        try:
            # Create a LocalClient without ClientInformation
            local_client = LocalClient.objects.create(
                raison="Test Client Without Info", test="Test Value"
            )
            f.write(
                f"Created LocalClient {local_client.id} without ClientInformation\n"
            )

            # Get the schema
            schema_builder = get_schema_builder()
            schema = schema_builder.get_schema()
            f.write("Schema obtained successfully\n")

            # Test simple query
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

            f.write("Executing GraphQL query...\n")
            result = schema.execute(query)

            if result.errors:
                f.write("ERRORS occurred:\n")
                for error in result.errors:
                    f.write(f"  - {error}\n")
                    if hasattr(error, "original_error"):
                        f.write(f"  - Original error: {error.original_error}\n")
                        f.write(f"  - Error type: {type(error.original_error)}\n")
            else:
                f.write("Query executed successfully!\n")
                data = result.data
                if data and data.get("localclients"):
                    f.write(f"Found {len(data['localclients'])} LocalClients:\n")
                    for client_data in data["localclients"]:
                        f.write(f"  LocalClient ID: {client_data['id']}\n")
                        f.write(f"  Raison: {client_data['raison']}\n")
                        f.write(f"  Test: {client_data['test']}\n")
                        f.write(f"  Info: {client_data['info']}\n")

                        if client_data["id"] == str(local_client.id):
                            if client_data["info"] is None:
                                f.write(
                                    "  SUCCESS: Info field correctly returns null!\n"
                                )
                            else:
                                f.write(
                                    f"  ERROR: Info field should be null but returned: {client_data['info']}\n"
                                )
                        f.write("  ---\n")
                else:
                    f.write("ERROR: No LocalClient data returned\n")

            # Clean up
            local_client.delete()
            f.write(f"\nCleaned up test LocalClient {local_client.id}\n")

        except Exception as e:
            f.write(f"Exception occurred: {e}\n")
            f.write(f"Traceback: {traceback.format_exc()}\n")

    print(f"Test completed. Output written to {output_file}")


if __name__ == "__main__":
    test_null_info()
