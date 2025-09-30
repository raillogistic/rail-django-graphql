#!/usr/bin/env python
"""
Test polymorphic_type field for both list and single client queries.
This test verifies that the polymorphic_type field correctly identifies
the class name for both Client and LocalClient instances.
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
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
    django.setup()

from django.test import TestCase
from django.db import transaction
from graphene.test import Client as GraphQLClient
from django_graphql_auto.core.schema import SchemaBuilder
from test_app.models import Client, LocalClient


def test_polymorphic_type_field():
    """Test polymorphic_type field for both list and single queries."""
    print("=== Testing polymorphic_type field ===")
    
    try:
        # Build the schema
        schema_builder = SchemaBuilder()
        schema = schema_builder.get_schema()
        
        # Create GraphQL client
        client = GraphQLClient(schema)
        
        # Clean up existing data
        with transaction.atomic():
            LocalClient.objects.all().delete()
            Client.objects.all().delete()
        
        # Create test data
        with transaction.atomic():
            # Create a base Client
            base_client = Client.objects.create(raison="Base Client Company")
            print(f"Created base client: {base_client.raison} (ID: {base_client.id})")
            
            # Create a LocalClient
            local_client = LocalClient.objects.create(
                raison="Local Client Company",
                test="Local specific test data"
            )
            print(f"Created local client: {local_client.raison} (ID: {local_client.id})")
        
        # Test 1: List query with polymorphic_type
        print("\n--- Test 1: List query with polymorphic_type ---")
        list_query = """
        query {
            clients {
                id
                raison
                polymorphic_type
            }
        }
        """
        
        result = client.execute(list_query)
        print(f"List query result: {result}")
        
        if result.get('errors'):
            print(f"❌ List query failed with errors: {result['errors']}")
            return False
        
        clients_data = result.get('data', {}).get('clients', [])
        if not clients_data:
            print("❌ No clients returned from list query")
            return False
        
        print(f"✅ Retrieved {len(clients_data)} clients from list query")
        for client_data in clients_data:
            print(f"   - ID: {client_data['id']}, Raison: {client_data['raison']}, Type: {client_data['polymorphic_type']}")
        
        # Test 2: Single client query by ID with polymorphic_type
        print("\n--- Test 2: Single client queries by ID ---")
        
        # Query base client by ID
        base_client_query = f"""
        query {{
            client(id: "{base_client.id}") {{
                id
                raison
                polymorphic_type
            }}
        }}
        """
        
        result = client.execute(base_client_query)
        print(f"Base client query result: {result}")
        
        if result.get('errors'):
            print(f"❌ Base client query failed with errors: {result['errors']}")
            return False
        
        base_client_data = result.get('data', {}).get('client')
        if not base_client_data:
            print("❌ No base client returned from single query")
            return False
        
        print(f"✅ Base client query successful:")
        print(f"   - ID: {base_client_data['id']}, Raison: {base_client_data['raison']}, Type: {base_client_data['polymorphic_type']}")
        
        # Query local client by ID
        local_client_query = f"""
        query {{
            client(id: "{local_client.id}") {{
                id
                raison
                polymorphic_type
            }}
        }}
        """
        
        result = client.execute(local_client_query)
        print(f"Local client query result: {result}")
        
        if result.get('errors'):
            print(f"❌ Local client query failed with errors: {result['errors']}")
            return False
        
        local_client_data = result.get('data', {}).get('client')
        if not local_client_data:
            print("❌ No local client returned from single query")
            return False
        
        print(f"✅ Local client query successful:")
        print(f"   - ID: {local_client_data['id']}, Raison: {local_client_data['raison']}, Type: {local_client_data['polymorphic_type']}")
        
        # Verify polymorphic_type values
        print("\n--- Verification ---")
        
        # Find the base client in list results
        base_in_list = next((c for c in clients_data if c['id'] == str(base_client.id)), None)
        local_in_list = next((c for c in clients_data if c['id'] == str(local_client.id)), None)
        
        if base_in_list and base_in_list['polymorphic_type'] == 'Client':
            print("✅ Base client has correct polymorphic_type 'Client' in list query")
        else:
            print(f"❌ Base client has incorrect polymorphic_type: {base_in_list['polymorphic_type'] if base_in_list else 'Not found'}")
            return False
        
        if local_in_list and local_in_list['polymorphic_type'] == 'LocalClient':
            print("✅ Local client has correct polymorphic_type 'LocalClient' in list query")
        else:
            print(f"❌ Local client has incorrect polymorphic_type: {local_in_list['polymorphic_type'] if local_in_list else 'Not found'}")
            return False
        
        if base_client_data['polymorphic_type'] == 'Client':
            print("✅ Base client has correct polymorphic_type 'Client' in single query")
        else:
            print(f"❌ Base client has incorrect polymorphic_type in single query: {base_client_data['polymorphic_type']}")
            return False
        
        if local_client_data['polymorphic_type'] == 'LocalClient':
            print("✅ Local client has correct polymorphic_type 'LocalClient' in single query")
        else:
            print(f"❌ Local client has incorrect polymorphic_type in single query: {local_client_data['polymorphic_type']}")
            return False
        
        print("\n✅ SUCCESS: All polymorphic_type tests passed!")
        print("   - List queries correctly show polymorphic_type")
        print("   - Single queries by ID correctly show polymorphic_type")
        print("   - Both Client and LocalClient instances are properly identified")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_polymorphic_type_field()
    sys.exit(0 if success else 1)