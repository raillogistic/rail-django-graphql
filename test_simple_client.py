#!/usr/bin/env python3
"""
Simple test to verify client type resolution without Django logging noise.
"""
import os
import sys
import django
import logging

# Disable Django logging for cleaner output
logging.disable(logging.CRITICAL)

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from test_app.models import Client, LocalClient, ClientInformation
from django_graphql_auto.core.schema import SchemaBuilder

def test_client_type():
    """Simple test for client type resolution."""
    print("Testing client type resolution...")
    
    # Clean up
    ClientInformation.objects.all().delete()
    LocalClient.objects.all().delete()
    Client.objects.all().delete()
    
    # Create test data
    client = Client.objects.create(raison="Test Client")
    local_client = LocalClient.objects.create(raison="Test Local Client", test="Test Value")
    
    # Create info
    ClientInformation.objects.create(
        client=client,
        code_postal="12345",
        pays="France",
        paysx="FranceX"
    )
    
    ClientInformation.objects.create(
        client=local_client,
        code_postal="67890",
        pays="Germany",
        paysx="GermanyX"
    )
    
    # Build schema
    builder = SchemaBuilder()
    schema = builder.get_schema()
    
    # Test query
    query = """
    query {
        clients {
            id
            raison
            uppercase_raison
        }
    }
    """
    
    result = schema.execute(query)
    
    if result.errors:
        print(f"❌ GraphQL errors: {result.errors}")
        return False
    
    clients_data = result.data['clients']
    print(f"✅ Retrieved {len(clients_data)} clients successfully")
    
    # Cleanup
    ClientInformation.objects.all().delete()
    LocalClient.objects.all().delete()
    Client.objects.all().delete()
    
    return True

if __name__ == "__main__":
    success = test_client_type()
    print("✅ SUCCESS: Client type resolution works!" if success else "❌ FAILED")
    sys.exit(0 if success else 1)