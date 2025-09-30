#!/usr/bin/env python
"""
Test script to reproduce the polymorphic type mismatch issue.
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
    
    # Create a LocalClient instance
    local_client = LocalClient.objects.create(
        raison="Test Local Client",
        test="Test Value"
    )
    
    # Create associated ClientInformation
    client_info = ClientInformation.objects.create(
        client=local_client,
        adresse="123 Test Street"
    )
    
    print(f"Created LocalClient with ID: {local_client.id}")
    print(f"LocalClient type: {type(local_client)}")
    print(f"LocalClient is instance of Client: {isinstance(local_client, Client)}")
    
    # Test the GraphQL query
    query = f'''
    {{
        client(id:"{local_client.id}") {{
            id
            raison
            info {{
                adresse
            }}
        }}
    }}
    '''
    
    print(f"\nExecuting GraphQL query:")
    print(query)
    
    try:
        result = schema.execute(query)
        
        print(f"\nGraphQL execution completed")
        print(f"Has errors: {bool(result.errors)}")
        
        if result.errors:
            print("\nGraphQL Errors:")
            for error in result.errors:
                print(f"  - {error}")
                print(f"    Type: {type(error)}")
                if hasattr(error, 'original_error'):
                    print(f"    Original: {error.original_error}")
        else:
            print("\nGraphQL Result:")
            print(json.dumps(result.data, indent=2))
            
    except Exception as e:
        print(f"\nException during query execution: {e}")
        import traceback
        traceback.print_exc()
    
    # Clean up
    client_info.delete()
    local_client.delete()
    print(f"\nCleaned up LocalClient {local_client.id}")

if __name__ == "__main__":
    test_polymorphic_client_query()