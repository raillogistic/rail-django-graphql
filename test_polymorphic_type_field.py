#!/usr/bin/env python3
"""
Test script to verify polymorphic_type field works for both list and single client queries.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')

if not settings.configured:
    django.setup()

from test_app.models import Client, LocalClient
from django_graphql_auto.core.schema import SchemaBuilder

def test_polymorphic_type_field():
    """Test that polymorphic_type field works for both list and single queries."""
    
    # Clean up any existing data
    LocalClient.objects.all().delete()
    Client.objects.all().delete()
    
    try:
        # Create test data
        client = Client.objects.create(raison="Test Client Base")
        local_client = LocalClient.objects.create(raison="Test Local Client", test="Test Value")
        
        print(f"Created Client ID: {client.id}")
        print(f"Created LocalClient ID: {local_client.id}")
        
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
        
        clients_data = result.data['clients']
        print(f"Retrieved {len(clients_data)} clients from list query")
        
        for client_data in clients_data:
            print(f"Client ID: {client_data['id']}, Type: {client_data['polymorphicType']}, Raison: {client_data['raison']}")
        
        # Verify we have both types
        types_found = [c['polymorphicType'] for c in clients_data]
        if 'Client' not in types_found or 'LocalClient' not in types_found:
            print(f"ERROR: Expected both 'Client' and 'LocalClient' types, got: {types_found}")
            return False
        
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
        
        client_data = result.data['client']
        if client_data:
            print(f"Single Client - ID: {client_data['id']}, Type: {client_data['polymorphicType']}, Raison: {client_data['raison']}")
            
            if client_data['polymorphicType'] != 'Client':
                print(f"ERROR: Expected 'Client' type, got: {client_data['polymorphicType']}")
                return False
        else:
            print("ERROR: No client data returned")
            return False
        
        # Test 3: Single LocalClient query by ID
        local_single_query = f"""
        query {{
            client(id: {local_client.id}) {{
                id
                raison
                uppercaseRaison
                polymorphicType
            }}
        }}
        """
        
        print(f"\n=== Testing Single LocalClient Query (ID: {local_client.id}) ===")
        result = schema.execute(local_single_query)
        
        if result.errors:
            print(f"GraphQL Errors: {result.errors}")
            return False
        
        local_client_data = result.data['client']
        if local_client_data:
            print(f"Single LocalClient - ID: {local_client_data['id']}, Type: {local_client_data['polymorphicType']}, Raison: {local_client_data['raison']}")
            
            if local_client_data['polymorphicType'] != 'LocalClient':
                print(f"ERROR: Expected 'LocalClient' type, got: {local_client_data['polymorphicType']}")
                return False
        else:
            print("ERROR: No local client data returned")
            return False
        
        print("\n✅ SUCCESS: All polymorphic_type field tests passed!")
        print("- List query returns polymorphic_type for all instances")
        print("- Single client query returns correct polymorphic_type for base Client")
        print("- Single client query returns correct polymorphic_type for LocalClient")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        LocalClient.objects.all().delete()
        Client.objects.all().delete()

if __name__ == "__main__":
    success = test_polymorphic_type_field()
    sys.exit(0 if success else 1)