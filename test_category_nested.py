#!/usr/bin/env python
"""
Test script to verify category nested operations behavior.
This tests ForeignKey nested operations which should allow creating/updating related Category objects.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django_graphql_auto.core.config_loader import load_mutation_settings
from django_graphql_auto.generators.types import TypeGenerator
from test_app.models import Post, Category

def test_category_nested_operations():
    """Test that category nested operations work when configured as True."""
    print("=== Testing Category Nested Operations ===\n")
    
    # Load settings from Django configuration
    settings = load_mutation_settings()
    print(f"Global enable_nested_relations: {settings.enable_nested_relations}")
    print(f"Nested field config: {settings.nested_field_config}")
    
    # Check if Post.category is configured
    if 'Post' in settings.nested_field_config:
        post_config = settings.nested_field_config['Post']
        category_config = post_config.get('category', 'not configured')
        print(f"Post.category configuration: {category_config}")
    else:
        print("Post model not found in nested_field_config")
    
    print("\n1. Testing Post input type generation...")
    type_generator = TypeGenerator(mutation_settings=settings)
    input_type = type_generator.generate_input_type(Post, mutation_type='create')
    
    # Check if category field exists and its type
    if hasattr(input_type, '_meta') and hasattr(input_type._meta, 'fields'):
        fields = input_type._meta.fields
        print(f"Available input fields: {list(fields.keys())}")
        
        if 'category' in fields:
            field = fields['category']
            field_type = getattr(field, 'type', None)
            print(f"✓ Category field found: {field}")
            print(f"✓ Field type: {field_type}")
            
            # Check if it's nested input type (should contain "CategoryNestedCreateInput")
            field_type_str = str(field_type)
            if "CategoryNestedCreateInput" in field_type_str:
                print("✓ SUCCESS: Category field appears as nested input type")
                return True
            else:
                print(f"✗ FAIL: Expected nested input type, got: {field_type_str}")
                return False
        else:
            print("✗ FAIL: Category field not found in input type")
            return False
    else:
        print("✗ FAIL: Input type has no fields")
        return False

def test_category_input_type_generation():
    """Test that CategoryNestedCreateInput type is properly generated."""
    print("\n2. Testing Category input type generation...")
    
    settings = load_mutation_settings()
    type_generator = TypeGenerator(mutation_settings=settings)
    
    try:
        category_input_type = type_generator.generate_input_type(Category, mutation_type='create')
        print(f"✓ Category input type generated: {category_input_type}")
        
        if hasattr(category_input_type, '_meta') and hasattr(category_input_type._meta, 'fields'):
            fields = category_input_type._meta.fields
            print(f"✓ Category input fields: {list(fields.keys())}")
            
            # Check for expected fields
            expected_fields = ['name', 'slug', 'description', 'is_active', 'order']
            missing_fields = [f for f in expected_fields if f not in fields]
            if missing_fields:
                print(f"⚠ Missing expected fields: {missing_fields}")
            else:
                print("✓ All expected fields present")
            
            return True
        else:
            print("✗ FAIL: Category input type has no fields")
            return False
    except Exception as e:
        print(f"✗ FAIL: Error generating Category input type: {e}")
        return False

def test_nested_operation_handler():
    """Test the nested operation handler for category operations."""
    print("\n3. Testing nested operation handler...")
    
    from django_graphql_auto.generators.nested_operations import NestedOperationHandler
    from django.contrib.auth.models import User
    
    settings = load_mutation_settings()
    nested_handler = NestedOperationHandler(settings)
    
    # Create or get a test user
    author, created = User.objects.get_or_create(
        username='testauthor',
        defaults={'email': 'test@example.com'}
    )
    
    # Use unique names to avoid constraint errors
    import time
    unique_id = int(time.time())
    unique_slug = f"test-category-{unique_id}"
    unique_name = f"Test Category {unique_id}"
    
    # Test data with nested category creation
    test_data = {
        'title': 'Test Post with Nested Category',
        'content': 'Test content',
        'slug': f'test-post-{unique_id}',
        'status': 'published',
        'is_featured': False,
        'author': author.id,
        'category': {
            'name': unique_name,
            'slug': unique_slug,
            'description': 'Test category description',
            'is_active': True,
            'order': 1
        }
    }
    
    try:
        print("✓ Testing nested category creation...")
        # This should create both the post and the nested category
        post = nested_handler.handle_nested_create(Post, test_data)
        print(f"✓ Post created: {post.title}")
        print(f"✓ Category created: {post.category.name}")
        return True
    except Exception as e:
        print(f"✗ FAIL: Error in nested operation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing category nested operations functionality...\n")
    
    test1_passed = test_category_nested_operations()
    test2_passed = test_category_input_type_generation()
    test3_passed = test_nested_operation_handler()
    
    print(f"\n=== Test Results ===")
    print(f"Post input type test: {'PASS' if test1_passed else 'FAIL'}")
    print(f"Category input type test: {'PASS' if test2_passed else 'FAIL'}")
    print(f"Nested operation test: {'PASS' if test3_passed else 'FAIL'}")
    
    if all([test1_passed, test2_passed, test3_passed]):
        print("\n✓ All tests passed - Category nested operations are working!")
    else:
        print("\n✗ Some tests failed - Category nested operations need investigation")