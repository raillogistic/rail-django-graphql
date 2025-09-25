#!/usr/bin/env python
"""
Test script to verify that reverse relationship fields default to [ID] when not mentioned in nested_field_config.
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

from django_graphql_auto.core.settings import MutationGeneratorSettings
from django_graphql_auto.core.config_loader import load_mutation_settings
from django_graphql_auto.generators.types import TypeGenerator
from test_app.models import Post, Comment

def test_default_reverse_field_behavior():
    """Test that reverse fields default to [ID] when not mentioned in config."""
    print("=== Testing Default Reverse Field Behavior ===\n")
    
    # Test 1: No nested_field_config at all - should use global default from settings.py
    print("1. Testing with no nested_field_config...")
    settings = load_mutation_settings()  # Load from Django settings
    
    type_generator = TypeGenerator(mutation_settings=settings)
    input_type = type_generator.generate_input_type(Post, mutation_type='create')
    
    # Check if comments field exists
    if hasattr(input_type, '_meta') and hasattr(input_type._meta, 'fields'):
        fields = input_type._meta.fields
        if 'comments' in fields:
            field = fields['comments']
            field_type = getattr(field, 'type', None)
            print(f"   ✓ Comments field found: {field}")
            print(f"   ✓ Field type: {field_type}")
            
            # Check if it's List[ID]
            if hasattr(field_type, 'of_type'):
                inner_type = field_type.of_type
                print(f"   ✓ Inner type: {inner_type}")
                if str(inner_type) == 'ID':
                    print("   ✓ SUCCESS: Comments field defaults to [ID]")
                else:
                    print(f"   ✗ FAIL: Expected [ID], got [{inner_type}]")
            else:
                print(f"   ✗ FAIL: Field type is not a List: {field_type}")
        else:
            print("   ✗ FAIL: Comments field not found in input type")
    else:
        print("   ✗ FAIL: Could not access input type fields")
    
    print()
    
    # Test 2: Global nested relations disabled
    print("2. Testing with global nested_relations disabled...")
    settings = MutationGeneratorSettings(
        enable_nested_relations=False,  # Global setting disabled
        nested_relations_config={},
        nested_field_config={}  # No specific config for comments
    )
    
    type_generator = TypeGenerator(mutation_settings=settings)
    input_type = type_generator.generate_input_type(Post, mutation_type='create')
    
    # Check if comments field exists
    if hasattr(input_type, '_meta') and hasattr(input_type._meta, 'fields'):
        fields = input_type._meta.fields
        if 'comments' in fields:
            field = fields['comments']
            field_type = getattr(field, 'type', None)
            print(f"   ✓ Comments field found: {field}")
            print(f"   ✓ Field type: {field_type}")
            
            # Check if it's List[ID]
            if hasattr(field_type, 'of_type'):
                inner_type = field_type.of_type
                print(f"   ✓ Inner type: {inner_type}")
                if str(inner_type) == 'ID':
                    print("   ✓ SUCCESS: Comments field appears as [ID] when global nested disabled")
                else:
                    print(f"   ✗ FAIL: Expected [ID], got [{inner_type}]")
            else:
                print(f"   ✗ FAIL: Field type is not a List: {field_type}")
        else:
            print("   ✗ FAIL: Comments field not found in input type")
    else:
        print("   ✗ FAIL: Could not access input type fields")
    
    print()
    
    # Test 3: Other fields configured but comments not mentioned - should use global default
    print("3. Testing with other field configs but comments not mentioned...")
    settings = MutationGeneratorSettings(
        enable_nested_relations=False,  # Global default from settings.py
        nested_field_config={
            'Post': {
                'tags': True,  # Enable tags but don't mention comments
                'category': True
            }
        }
    )
    
    type_generator = TypeGenerator(mutation_settings=settings)
    input_type = type_generator.generate_input_type(Post, mutation_type='create')
    
    # Check if comments field exists
    if hasattr(input_type, '_meta') and hasattr(input_type._meta, 'fields'):
        fields = input_type._meta.fields
        if 'comments' in fields:
            field = fields['comments']
            field_type = getattr(field, 'type', None)
            print(f"   ✓ Comments field found: {field}")
            print(f"   ✓ Field type: {field_type}")
            
            # Check if it's List[ID]
            if hasattr(field_type, 'of_type'):
                inner_type = field_type.of_type
                print(f"   ✓ Inner type: {inner_type}")
                if str(inner_type) == 'ID':
                    print("   ✓ SUCCESS: Comments field defaults to [ID] when not mentioned in field config")
                else:
                    print(f"   ✗ FAIL: Expected [ID], got [{inner_type}]")
            else:
                print(f"   ✗ FAIL: Field type is not a List: {field_type}")
        else:
            print("   ✗ FAIL: Comments field not found in input type")
    else:
        print("   ✗ FAIL: Could not access input type fields")

if __name__ == '__main__':
    test_default_reverse_field_behavior()