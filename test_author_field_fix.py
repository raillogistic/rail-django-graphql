#!/usr/bin/env python3
"""
Simple test to verify if the author field is present in CommentNestedCreateInput.
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

def test_author_field_in_schema():
    """Test if author field is present in CommentNestedCreateInput in schema.graphql."""
    print("=== Testing Author Field in CommentNestedCreateInput ===")
    
    # Read the current schema.graphql file
    schema_file = os.path.join(os.path.dirname(__file__), 'schema.graphql')
    
    if not os.path.exists(schema_file):
        print("❌ ERROR: schema.graphql file not found")
        return False
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_content = f.read()
    
    # Find CommentNestedCreateInput definition
    lines = schema_content.split('\n')
    in_comment_nested = False
    comment_nested_fields = []
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('input CommentNestedCreateInput'):
            in_comment_nested = True
            print(f"✓ Found CommentNestedCreateInput definition")
            continue
        
        if in_comment_nested:
            if line.startswith('}'):
                break
            elif line and not line.startswith('"""') and ':' in line:
                field_name = line.split(':')[0].strip()
                if field_name:
                    comment_nested_fields.append(field_name)
    
    print(f"Fields in CommentNestedCreateInput: {comment_nested_fields}")
    
    # Check for specific fields
    has_author = 'author' in comment_nested_fields
    has_post = 'post' in comment_nested_fields
    has_content = 'content' in comment_nested_fields
    
    print(f"Has 'author' field: {has_author}")
    print(f"Has 'post' field: {has_post}")
    print(f"Has 'content' field: {has_content}")
    
    if has_author:
        print("✅ SUCCESS: Author field is present in CommentNestedCreateInput!")
        return True
    else:
        print("❌ PROBLEM: Author field is missing from CommentNestedCreateInput")
        return False

def test_direct_generation():
    """Test direct generation of CommentNestedCreateInput."""
    print("\n=== Testing Direct Generation ===")
    
    from test_app.models import Post, Comment
    from django_graphql_auto.generators.types import TypeGenerator
    from django_graphql_auto.core.settings import TypeGeneratorSettings
    
    # Initialize components
    settings = TypeGeneratorSettings()
    type_generator = TypeGenerator(settings)
    
    # Generate CommentNestedCreateInput directly
    nested_input_type = type_generator._get_or_create_nested_input_type(
        model=Comment,
        mutation_type='create',
        exclude_parent_field=Post
    )
    
    # Check fields
    if hasattr(nested_input_type, '_meta') and hasattr(nested_input_type._meta, 'fields'):
        fields = nested_input_type._meta.fields
        field_names = list(fields.keys())
        print(f"Direct generation fields: {field_names}")
        
        has_author = 'author' in field_names
        has_post = 'post' in field_names
        
        print(f"Direct generation - Has 'author': {has_author}")
        print(f"Direct generation - Has 'post': {has_post}")
        
        return has_author
    else:
        print("❌ ERROR: Cannot access fields in directly generated type")
        return False

if __name__ == "__main__":
    try:
        schema_test_passed = test_author_field_in_schema()
        direct_test_passed = test_direct_generation()
        
        print(f"\n=== SUMMARY ===")
        print(f"Schema file test: {'PASSED' if schema_test_passed else 'FAILED'}")
        print(f"Direct generation test: {'PASSED' if direct_test_passed else 'FAILED'}")
        
        if direct_test_passed and not schema_test_passed:
            print("\n🔍 DIAGNOSIS: Direct generation works but schema file is outdated")
            print("   Try regenerating the schema with: python manage.py graphql_schema")
        elif schema_test_passed:
            print("\n✅ CONCLUSION: The issue appears to be resolved!")
        else:
            print("\n❌ CONCLUSION: The issue persists in both direct generation and schema file")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()