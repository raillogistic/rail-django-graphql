#!/usr/bin/env python
"""
Test script to verify that the client query can handle LocalClient instances
using the resolve_type method approach.
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
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'polymorphic',
            'test_app',
        ],
        USE_TZ=True,
        SECRET_KEY='test-secret-key',
    )

# Setup Django
django.setup()

# Create tables
from django.core.management import execute_from_command_line
execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])

from django_graphql_auto.core.schema import SchemaBuilder
from test_app.models import Client, LocalClient

def test_client_polymorphic_query():
    """Test that client query can handle LocalClient instances with resolve_type"""
    
    # Create test data
    local_client = LocalClient.objects.create(
        raison="Test Local Client",
        test="Test Value"
    )
    
    # Create ClientInformation for the local_client
    from test_app.models import ClientInformation
    client_info = ClientInformation.objects.create(
        client=local_client,
        adresse="123 Test Street",
        ville="Test City",
        code_postal="12345",
        pays="Test Country",
        paysx="Test Country X"
    )
    
    print(f"Created LocalClient with ID: {local_client.id}")
    print(f"LocalClient type: {type(local_client)}")
    print(f"Created ClientInformation with ID: {client_info.id}")
    
    # Build schema
    schema_builder = SchemaBuilder()
    schema_builder.register_app('test_app')
    
    print("Building schema...")
    schema = schema_builder.get_schema()
    
    # GraphQL query using union type fragments
    query = """
    query {
        client(id: "1") {
            ... on ClientType {
                id
                raison
            }
            ... on LocalClientType {
                id
                raison
                test
                info {
                    adresse
                    ville
                }
            }
        }
    }
    """
    
    print(f"Executing query: {query}")
    
    # Execute query
    result = schema.execute(query)
    
    if result.errors:
        print("GraphQL Errors:")
        for error in result.errors:
            print(f"  - {error}")
        return False
    
    print("Query Result:")
    print(result.data)
    
    # Verify the result
    if result.data and result.data.get('client'):
        client_data = result.data['client']
        print(f"Successfully retrieved client data: {client_data}")
        
        # Check if we got the LocalClient specific fields
        if 'test' in client_data and 'info' in client_data:
            print("✓ LocalClient specific fields retrieved successfully")
            return True
        else:
            print("✗ LocalClient specific fields not found")
            return False
    else:
        print("✗ No client data returned")
        return False

if __name__ == "__main__":
    success = test_client_polymorphic_query()
    if success:
        print("\n✓ Test passed: client query successfully handles LocalClient instances")
    else:
        print("\n✗ Test failed: client query could not handle LocalClient instances")
    
    sys.exit(0 if success else 1)