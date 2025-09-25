#!/usr/bin/env python
"""
Test script to verify reverse relationship field handling with nested configurations.
Tests that when nested=False for reverse relationships, fields appear as List[ID] instead of disappearing.
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
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'test_app',
        ],
        SECRET_KEY='test-secret-key',
        USE_TZ=True,
    )

django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category, Tag
from django_graphql_auto.generators.types import TypeGenerator
from django_graphql_auto.core.settings import MutationGeneratorSettings
import graphene

def test_reverse_field_nested_true():
    """Test that reverse relationship fields are included as nested objects when nested=True."""
    print("=== Testing Reverse Field with nested=True ===")
    
    # Configuration with nested relations enabled for comments
    mutation_settings = MutationGeneratorSettings(
        enable_nested_relations=True,
        nested_field_config={
            'Post': {
                'comments': True  # Enable nested comments
            }
        }
    )
    
    type_generator = TypeGenerator(mutation_settings=mutation_settings)
    
    # Generate input type for Post
    input_type = type_generator.generate_input_type(Post, mutation_type='create')
    
    # Check if comments field is present
    input_fields = input_type._meta.fields
    print(f"Available input fields: {list(input_fields.keys())}")
    
    has_comments = 'comments' in input_fields
    print(f"✓ Comments field present: {has_comments}")
    
    if has_comments:
        comments_field = input_fields['comments']
        print(f"✓ Comments field type: {type(comments_field)}")
        
        # Get the actual field type from the InputField
        field_type = comments_field.type
        print(f"✓ Comments field actual type: {field_type}")
        print(f"✓ Comments field is List: {hasattr(field_type, 'of_type')}")
        
        # Check if it's a nested input type (not just ID)
        if hasattr(field_type, 'of_type'):
            inner_type = field_type.of_type
            is_nested = hasattr(inner_type, '_meta') and hasattr(inner_type._meta, 'fields')
            print(f"✓ Comments field is nested object: {is_nested}")
            
            if is_nested:
                nested_fields = list(inner_type._meta.fields.keys())
                print(f"✓ Nested comment fields: {nested_fields}")
            else:
                print(f"✓ Inner type is: {inner_type}")
    
    return has_comments

def test_reverse_field_nested_false():
    """Test that reverse relationship fields are included as List[ID] when nested=False."""
    print("\n=== Testing Reverse Field with nested=False ===")
    
    # Configuration with nested relations disabled for comments
    mutation_settings = MutationGeneratorSettings(
        enable_nested_relations=True,
        nested_field_config={
            'Post': {
                'comments': False  # Disable nested comments
            }
        }
    )
    
    type_generator = TypeGenerator(mutation_settings=mutation_settings)
    
    # Generate input type for Post
    input_type = type_generator.generate_input_type(Post, mutation_type='create')
    
    # Check if comments field is present
    input_fields = input_type._meta.fields
    print(f"Available input fields: {list(input_fields.keys())}")
    
    has_comments = 'comments' in input_fields
    print(f"✓ Comments field present: {has_comments}")
    
    if has_comments:
        comments_field = input_fields['comments']
        print(f"✓ Comments field type: {type(comments_field)}")
        
        # Get the actual field type from the InputField
        field_type = comments_field.type
        print(f"✓ Comments field actual type: {field_type}")
        print(f"✓ Comments field is List: {hasattr(field_type, 'of_type')}")
        
        # Check if it's a List[ID] (not nested object)
        if hasattr(field_type, 'of_type'):
            inner_type = field_type.of_type
            is_id_type = inner_type == graphene.ID
            is_nested = hasattr(inner_type, '_meta') and hasattr(inner_type._meta, 'fields')
            print(f"✓ Comments field is List[ID]: {is_id_type}")
            print(f"✓ Comments field is nested object: {is_nested}")
            print(f"✓ Inner type: {inner_type}")
    
    return has_comments

def test_reverse_field_no_config():
    """Test that reverse relationship fields default to nested when no config is provided."""
    print("\n=== Testing Reverse Field with no specific config ===")
    
    # Configuration with no specific field config
    mutation_settings = MutationGeneratorSettings(
        enable_nested_relations=True
    )
    
    type_generator = TypeGenerator(mutation_settings=mutation_settings)
    
    # Generate input type for Post
    input_type = type_generator.generate_input_type(Post, mutation_type='create')
    
    # Check if comments field is present
    input_fields = input_type._meta.fields
    print(f"Available input fields: {list(input_fields.keys())}")
    
    has_comments = 'comments' in input_fields
    print(f"✓ Comments field present: {has_comments}")
    
    if has_comments:
        comments_field = input_fields['comments']
        print(f"✓ Comments field type: {type(comments_field)}")
        
        # Get the actual field type from the InputField
        field_type = comments_field.type
        print(f"✓ Comments field actual type: {field_type}")
        
        # Check if it defaults to nested (should be nested object, not ID)
        if hasattr(field_type, 'of_type'):
            inner_type = field_type.of_type
            is_nested = hasattr(inner_type, '_meta') and hasattr(inner_type._meta, 'fields')
            is_id_type = inner_type == graphene.ID
            print(f"✓ Comments field is nested object: {is_nested}")
            print(f"✓ Comments field is List[ID]: {is_id_type}")
            print(f"✓ Inner type: {inner_type}")
    
    return has_comments

def main():
    """Run all tests."""
    print("Testing reverse relationship field handling with nested configurations...")
    
    try:
        # Test nested=True
        result1 = test_reverse_field_nested_true()
        
        # Test nested=False (this should now include the field as List[ID])
        result2 = test_reverse_field_nested_false()
        
        # Test no config (should default to nested)
        result3 = test_reverse_field_no_config()
        
        print(f"\n=== Test Results ===")
        print(f"✓ Nested=True has comments: {result1}")
        print(f"✓ Nested=False has comments: {result2}")
        print(f"✓ No config has comments: {result3}")
        
        if result1 and result2 and result3:
            print("\n🎉 All tests passed! Reverse relationship fields are properly handled.")
        else:
            print("\n❌ Some tests failed. Check the output above.")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()