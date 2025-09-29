#!/usr/bin/env python
"""
Final test to verify field extraction works with GraphQL mutations.
"""

import os
import sys
import django
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from test_app.models import Tag
from django.test import RequestFactory
from graphene.test import Client
from django_graphql_auto.core.schema import SchemaBuilder

def test_graphql_field_extraction():
    """Test field extraction in GraphQL mutations."""
    
    print("Setting up GraphQL schema...")
    
    # Create schema
    schema_builder = SchemaBuilder()
    schema = schema_builder.get_schema()
    client = Client(schema)
    
    # Create first tag
    tag1 = Tag.objects.create(name="graphql_test_unique")
    print(f"Created first tag: {tag1.name}")
    
    # Test duplicate creation via GraphQL
    print("\nTesting duplicate creation via GraphQL...")
    
    mutation = '''
    mutation {
        create_tag(input: {name: "graphql_test_unique"}) {
            ok
            object {
                id
                name
            }
            errors {
                field
                message
            }
        }
    }
    '''
    
    result = client.execute(mutation)
    print(f"GraphQL result: {json.dumps(result, indent=2)}")
    
    # Check if we have errors with field information
    if 'data' in result and result['data'] and result['data']['create_tag']['errors']:
        errors = result['data']['create_tag']['errors']
        for error in errors:
            print(f"Error field: {error['field']}")
            print(f"Error message: {error['message']}")
            
            # Verify field extraction worked
            if error['field'] == 'name':
                print("✅ Field extraction successful!")
            else:
                print("❌ Field extraction failed!")
    
    # Clean up
    Tag.objects.filter(name="graphql_test_unique").delete()
    print("\nCleanup completed.")

if __name__ == "__main__":
    test_graphql_field_extraction()