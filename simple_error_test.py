#!/usr/bin/env python
"""
Simple test to debug field extraction from database constraint errors.
"""

import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from test_app.models import Tag
from django_graphql_auto.schema import schema

def test_unique_constraint():
    """Test unique constraint error field extraction."""
    
    print("Creating first tag...")
    # Create first tag
    tag1 = Tag.objects.create(name="test_unique")
    print(f"Created: {tag1.name}")
    
    print("\nTesting GraphQL mutation with duplicate name...")
    
    # Test GraphQL mutation
    mutation = """
    mutation {
        create_tag(input: {name: "test_unique"}) {
            ok
            errors {
                field
                message
            }
        }
    }
    """
    
    result = schema.execute(mutation)
    
    print(f"GraphQL execution result:")
    print(f"Data: {result.data}")
    
    if result.errors:
        print(f"GraphQL Errors: {result.errors}")
    
    if result.data and result.data.get('create_tag'):
        create_result = result.data['create_tag']
        print(f"OK: {create_result.get('ok')}")
        
        errors = create_result.get('errors', [])
        print(f"Number of errors: {len(errors)}")
        
        for i, error in enumerate(errors):
            print(f"Error {i+1}:")
            print(f"  Field: {error.get('field')}")
            print(f"  Message: {error.get('message')}")
            
            if error.get('field') == 'name':
                print("  ✅ SUCCESS: Field extraction working!")
            else:
                print("  ❌ ISSUE: Field is not 'name'")
    
    # Clean up
    Tag.objects.filter(name="test_unique").delete()
    print("\nCleanup completed.")

if __name__ == "__main__":
    test_unique_constraint()