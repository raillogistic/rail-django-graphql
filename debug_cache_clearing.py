#!/usr/bin/env python3
"""
Debug script to clear caches and force regeneration of CommentNestedCreateInput.
This will help identify if caching is causing the author field to be missing.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from test_app.models import Post, Comment, User
from django_graphql_auto.generators.types import TypeGenerator
from django_graphql_auto.generators.introspector import ModelIntrospector
from django_graphql_auto.core.settings import TypeGeneratorSettings

def debug_cache_clearing():
    """Debug cache clearing and regeneration of CommentNestedCreateInput."""
    print("=== Debugging Cache Clearing for CommentNestedCreateInput ===")
    
    # Initialize components
    settings = TypeGeneratorSettings()
    type_generator = TypeGenerator(settings)
    
    print(f"1. Initial cache state:")
    print(f"   Input type registry size: {len(type_generator._input_type_registry)}")
    print(f"   Registry keys: {list(type_generator._input_type_registry.keys())}")
    
    # Clear the cache
    print("\n2. Clearing input type registry cache...")
    type_generator._input_type_registry.clear()
    print(f"   Cache cleared. Registry size: {len(type_generator._input_type_registry)}")
    
    # Generate CommentNestedCreateInput fresh
    print("\n3. Generating fresh CommentNestedCreateInput...")
    nested_input_type = type_generator._get_or_create_nested_input_type(
        model=Comment,
        mutation_type='create',
        exclude_parent_field=Post
    )
    
    print(f"   Generated type: {nested_input_type}")
    print(f"   Type name: {nested_input_type.__name__}")
    print(f"   Cache size after generation: {len(type_generator._input_type_registry)}")
    
    # Check fields in the generated type
    if hasattr(nested_input_type, '_meta') and hasattr(nested_input_type._meta, 'fields'):
        fields = nested_input_type._meta.fields
        print(f"   Fields in generated type: {list(fields.keys())}")
        
        # Check specifically for author and post fields
        has_author = 'author' in fields
        has_post = 'post' in fields
        print(f"   Has 'author' field: {has_author}")
        print(f"   Has 'post' field: {has_post}")
        
        if has_author:
            author_field = fields['author']
            print(f"   Author field type: {type(author_field)}")
            print(f"   Author field: {author_field}")
        else:
            print("   ❌ PROBLEM: 'author' field is missing after cache clear!")
            
        if not has_post:
            print("   ✓ CORRECT: 'post' field is excluded (prevents circular reference)")
        else:
            print("   ❌ UNEXPECTED: 'post' field is present")
    else:
        print("   ❌ ERROR: Cannot access fields in generated type")
    
    # Now test the full schema generation process
    print("\n4. Testing full schema generation process...")
    try:
        from django_graphql_auto.core.schema import SchemaBuilder
        
        # Create a fresh schema instance
        schema_builder = SchemaBuilder()
        
        # Generate the schema
        schema = schema_builder.get_schema()
        
        print(f"   Schema generated successfully")
        print(f"   Schema types: {len(schema.type_map)} types")
        
        # Check if CommentNestedCreateInput is in the schema
        if 'CommentNestedCreateInput' in schema.type_map:
            comment_nested_type = schema.type_map['CommentNestedCreateInput']
            print(f"   CommentNestedCreateInput found in schema")
            print(f"   Fields: {list(comment_nested_type.fields.keys())}")
            
            has_author_in_schema = 'author' in comment_nested_type.fields
            has_post_in_schema = 'post' in comment_nested_type.fields
            print(f"   Has 'author' field in schema: {has_author_in_schema}")
            print(f"   Has 'post' field in schema: {has_post_in_schema}")
        else:
            print("   ❌ ERROR: CommentNestedCreateInput not found in schema")
            
    except Exception as e:
        print(f"   ❌ ERROR in schema generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        debug_cache_clearing()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()