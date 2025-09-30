#!/usr/bin/env python
"""
Simple test for null info handling with plain text output
"""
import os
import sys
import django
import traceback

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django_graphql_auto.core.schema import get_schema_builder
from test_app.models import LocalClient, ClientInformation

def test_simple_null_info():
    print("=== Testing Simple Null Info Handling ===")
    
    try:
        # First, create a LocalClient without ClientInformation
        local_client = LocalClient.objects.create(
            raison="Test Client Without Info",
            test="Test Value"
        )
        print(f"Created LocalClient {local_client.id} without ClientInformation")
        
        # Get the schema
        print("Getting schema...")
        schema_builder = get_schema_builder()
        schema = schema_builder.get_schema()
        print("Schema obtained successfully")
        
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
        
        print("Executing query...")
        result = schema.execute(query)
        
        if result.errors:
            print("ERRORS occurred:")
            for error in result.errors:
                print(f"  - {error}")
                if hasattr(error, 'original_error'):
                    print(f"  - Original error: {error.original_error}")
                    print(f"  - Traceback: {traceback.format_exception(type(error.original_error), error.original_error, error.original_error.__traceback__)}")
        else:
            print("Query executed successfully!")
            data = result.data
            if data and data.get('localclients'):
                print(f"Found {len(data['localclients'])} LocalClients:")
                for client_data in data['localclients']:
                    print(f"  LocalClient ID: {client_data['id']}")
                    print(f"  Raison: {client_data['raison']}")
                    print(f"  Test: {client_data['test']}")
                    print(f"  Info: {client_data['info']}")
                    
                    if client_data['id'] == str(local_client.id):
                        if client_data['info'] is None:
                            print("  SUCCESS: Info field correctly returns null for test client!")
                        else:
                            print("  ERROR: Info field should be null but returned:", client_data['info'])
                    print("  ---")
            else:
                print("ERROR: No LocalClient data returned")
        
        # Clean up - delete the test LocalClient
        local_client.delete()
        print(f"\nCleaned up test LocalClient {local_client.id}")
        
    except Exception as e:
        print(f"Exception occurred: {e}")
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_simple_null_info()