#!/usr/bin/env python
"""
Test script to reproduce the polymorphic type mismatch issue and write output to file.
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from test_app.models import Client, LocalClient, ClientInformation
from django_graphql_auto.schema import schema
import json

def test_polymorphic_client_query():
    """Test querying a client that is actually a LocalClient instance."""
    
    output_file = "test_polymorphic_output.txt"
    
    with open(output_file, "w") as f:
        # Create a LocalClient instance
        local_client = LocalClient.objects.create(
            raison="Test Local Client",
            test="Test Value"
        )
        
        # Create associated ClientInformation
        client_info = ClientInformation.objects.create(
            client=local_client,
            adresse="123 Test Street",
            ville="Test City",
            code_postal="12345",
            pays="Test Country",
            paysx="Test Country X"
        )
        
        f.write(f"Created LocalClient with ID: {local_client.id}\n")
        f.write(f"LocalClient type: {type(local_client)}\n")
        f.write(f"LocalClient is instance of Client: {isinstance(local_client, Client)}\n")
        
        # Test GraphQL query using localclient instead of client
        query = f'''
        {{
            localclient(id:"{local_client.id}") {{
                id
                raison
                test
                info {{
                    adresse
                }}
            }}
        }}
        '''
        
        f.write(f"\nExecuting GraphQL query:\n")
        f.write(query)
        f.write("\n")
        
        try:
            result = schema.execute(query)
            
            f.write(f"\nGraphQL execution completed\n")
            f.write(f"Has errors: {bool(result.errors)}\n")
            
            if result.errors:
                f.write("\nGraphQL Errors:\n")
                for error in result.errors:
                    f.write(f"  - {error}\n")
                    f.write(f"    Type: {type(error)}\n")
                    if hasattr(error, 'original_error'):
                        f.write(f"    Original: {error.original_error}\n")
            else:
                f.write("\nGraphQL Result:\n")
                f.write(json.dumps(result.data, indent=2))
                f.write("\n")
                
        except Exception as e:
            f.write(f"\nException during query execution: {e}\n")
            import traceback
            f.write(traceback.format_exc())
        
        # Clean up
        client_info.delete()
        local_client.delete()
        f.write(f"\nCleaned up LocalClient {local_client.id}\n")
    
    print(f"Test output written to {output_file}")

if __name__ == "__main__":
    test_polymorphic_client_query()