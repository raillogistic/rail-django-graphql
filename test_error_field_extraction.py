#!/usr/bin/env python
"""
Test script to verify field extraction from database constraint errors.
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.test import TestCase
from django.db import transaction
from test_app.models import Tag  # Changed from tests.models to test_app.models
import graphene
from django_graphql_auto.schema import schema


def test_unique_constraint_error():
    """Test that unique constraint errors extract field names correctly."""
    
    # First, create a tag to establish the constraint violation
    tag1 = Tag.objects.create(name="test_tag")
    print(f"Created first tag: {tag1.name}")
    
    # Test the GraphQL mutation that should trigger a unique constraint error
    mutation = """
    mutation createTag {
        create_tag(input: {
            name: "test_tag"
        }) {
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
    """
    
    try:
        result = schema.execute(mutation)
        print("GraphQL Result:")
        print(f"Data: {result.data}")
        if result.errors:
            print(f"Errors: {result.errors}")
        
        # Check if we got the expected error structure
        if result.data and result.data.get('create_tag'):
            create_result = result.data['create_tag']
            if create_result.get('errors'):
                for error in create_result['errors']:
                    print(f"Error field: {error.get('field')}")
                    print(f"Error message: {error.get('message')}")
                    
                    # This should now show field="name" instead of field=null
                    if error.get('field') == 'name':
                        print("✅ SUCCESS: Field extraction working correctly!")
                    else:
                        print("❌ ISSUE: Field is still null or incorrect")
            else:
                print("No errors returned - this might indicate the constraint isn't being triggered")
        
    except Exception as e:
        print(f"Exception during GraphQL execution: {e}")
        import traceback
        traceback.print_exc()
    
    # Clean up
    Tag.objects.filter(name="test_tag").delete()


def test_direct_database_error():
    """Test the database error parsing directly."""
    
    # Simulate the error message format we expect from SQLite
    error_messages = [
        "UNIQUE constraint failed: tests_tag.name",
        "NOT NULL constraint failed: tests_tag.name", 
        "FOREIGN KEY constraint failed",
        "Some other database error"
    ]
    
    import re
    
    for error_msg in error_messages:
        print(f"\nTesting error: {error_msg}")
        
        field_name = None
        
        # Handle UNIQUE constraint failures
        if "UNIQUE constraint failed" in error_msg:
            match = re.search(r'UNIQUE constraint failed: \w+\.(\w+)', error_msg)
            if match:
                field_name = match.group(1)
                print(f"  Extracted field: {field_name}")
            else:
                print("  No field extracted from UNIQUE constraint")
        
        # Handle NOT NULL constraint failures  
        elif "NOT NULL constraint failed" in error_msg:
            match = re.search(r'NOT NULL constraint failed: \w+\.(\w+)', error_msg)
            if match:
                field_name = match.group(1)
                print(f"  Extracted field: {field_name}")
            else:
                print("  No field extracted from NOT NULL constraint")
        
        else:
            print(f"  No field extraction for: {error_msg}")


if __name__ == "__main__":
    print("Testing database error field extraction...")
    print("=" * 50)
    
    print("\n1. Testing direct regex parsing:")
    test_direct_database_error()
    
    print("\n2. Testing GraphQL mutation with unique constraint:")
    test_unique_constraint_error()
    
    print("\nTest completed!")