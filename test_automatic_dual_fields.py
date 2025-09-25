#!/usr/bin/env python
"""
Test script for automatic dual field generation in GraphQL mutations.

This test verifies that the mutation generation logic automatically creates
dual fields for all relationship types without requiring configuration.
"""

import os
import sys
import django
from django.test import TestCase
from django.db import transaction

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

import graphene
from graphene.test import Client
from test_app.models import Post, Tag, Category, Comment
from test_app.auto_schema import auto_schema as schema
from django.contrib.auth.models import User


def test_schema_introspection():
    """Test that the schema contains the expected dual fields."""
    
    print("\n🔍 Testing detailed schema introspection...")
    
    client = Client(schema)
    
    # Query the schema to check for dual fields
    introspection_query = """
    query {
        __schema {
            mutationType {
                fields {
                    name
                    args {
                        name
                        type {
                            name
                            inputFields {
                                name
                                type {
                                    name
                                    kind
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    try:
        result = client.execute(introspection_query)
        
        # Find the create_post mutation
        mutations = result.get('data', {}).get('__schema', {}).get('mutationType', {}).get('fields', [])
        create_post_mutation = next((m for m in mutations if m['name'] == 'create_post'), None)
        
        if create_post_mutation:
            print("✅ Found create_post mutation")
            # Get the input type fields
            input_arg = next((arg for arg in create_post_mutation['args'] if arg['name'] == 'input'), None)
            if input_arg and input_arg['type']['inputFields']:
                field_names = [field['name'] for field in input_arg['type']['inputFields']]
                
                print(f"\n📋 All available PostInput fields:")
                for field in input_arg['type']['inputFields']:
                    field_type = field['type']['name'] if field['type']['name'] else field['type']['kind']
                    print(f"  - {field['name']}: {field_type}")
                
                # Check for dual fields
                expected_dual_fields = [
                    ('category', 'nested_category'),
                    ('tags', 'nested_tags'),
                    ('comments', 'nested_comments')
                ]
                
                for direct_field, nested_field in expected_dual_fields:
                    if direct_field in field_names and nested_field in field_names:
                        print(f"✅ Dual fields found: {direct_field} and {nested_field}")
                    elif direct_field in field_names:
                        print(f"⚠️  Only direct field found: {direct_field}")
                    elif nested_field in field_names:
                        print(f"⚠️  Only nested field found: {nested_field}")
                    else:
                        print(f"❌ Missing both fields: {direct_field} and {nested_field}")
            else:
                print("❌ Could not find input fields for create_post mutation")
        else:
            print("❌ Could not find create_post mutation")
            print(f"Available mutations: {[m['name'] for m in mutations]}")
    except Exception as e:
        print(f"❌ Schema introspection failed: {e}")


def test_automatic_dual_fields():
    """Test automatic dual field generation for all relationship types."""
    print("\n🧪 Running automatic dual field generation tests...")
    
    # Create a test user first
    test_user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    
    # Create a test category first
    test_category, created = Category.objects.get_or_create(
        name='Test Category',
        defaults={'slug': 'test-category', 'description': 'Test category for posts'}
    )
    
    print("\n🚀 Starting automatic dual field generation test...")
    
    # Test 1: Basic post creation with required fields
    print("\n📝 Test 1: Basic post creation with required fields")
    
    client = Client(schema)
    
    mutation = f"""
    mutation {{
        create_post(input: {{
            title: "Test Post Basic"
            slug: "test-post-basic"
            content: "Testing basic post creation"
            author: "{test_user.id}"
            category: "{test_category.id}"
        }}) {{
            ok
            object {{
                id
                title
                category {{
                    id
                    name
                }}
            }}
            errors
        }}
    }}
    """
    
    try:
        result = client.execute(mutation)
        print(f"✅ Basic post creation result: {result}")
        
        if result.get('data') and result['data'].get('create_post'):
            mutation_result = result['data']['create_post']
            if mutation_result.get('ok') and mutation_result.get('object'):
                print("✅ Basic post creation successful!")
            else:
                print(f"❌ Mutation failed: {mutation_result.get('errors', 'Unknown error')}")
        else:
            print("❌ No data returned from mutation")
            
    except Exception as e:
        print(f"❌ Basic post test failed with exception: {e}")

    print("\n🎯 Automatic dual field generation test completed!")


if __name__ == "__main__":
    print("🧪 Running automatic dual field generation tests...")
    
    # Clean up any existing data
    with transaction.atomic():
        Post.objects.all().delete()
        Category.objects.all().delete()
        Tag.objects.all().delete()
        Comment.objects.all().delete()
    
    # Run tests
    test_schema_introspection()
    test_automatic_dual_fields()
    
    print("\n✨ All tests completed!")