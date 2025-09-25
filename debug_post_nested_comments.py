#!/usr/bin/env python3
"""
Debug script to trace CommentNestedCreateInput generation in PostInput context.
This will help understand why the author field is missing.
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

def debug_post_nested_comments():
    """Debug how CommentNestedCreateInput is generated for PostInput."""
    print("=== Debugging CommentNestedCreateInput generation for PostInput ===")
    
    # Initialize components
    settings = TypeGeneratorSettings()
    type_generator = TypeGenerator(settings)
    
    print(f"1. Post model: {Post}")
    print(f"2. Comment model: {Comment}")
    
    # Get Post model introspection
    post_introspector = ModelIntrospector(Post)
    print(f"3. Post fields: {list(post_introspector.fields.keys())}")
    print(f"4. Post relationships: {list(post_introspector.relationships.keys())}")
    
    # Get reverse relations for Post
    reverse_relations = type_generator._get_reverse_relations(Post)
    print(f"5. Post reverse relations: {reverse_relations}")
    
    # Check if comments is in reverse relations
    if 'comments' in reverse_relations:
        related_model = reverse_relations['comments']
        print(f"6. Comments reverse relation points to: {related_model}")
        
        # This is where CommentNestedCreateInput gets generated
        print("\n7. Generating CommentNestedCreateInput for Post's nested_comments field...")
        print(f"   - Related model: {related_model}")
        print(f"   - Mutation type: create")
        print(f"   - exclude_parent_field: {Post}")
        
        # Generate the nested input type (this is what happens in PostInput generation)
        nested_input_type = type_generator._get_or_create_nested_input_type(
            model=related_model,  # Comment
            mutation_type='create',
            exclude_parent_field=Post  # This should exclude 'post' field, not 'author'
        )
        
        print(f"   Generated type: {nested_input_type}")
        print(f"   Type name: {nested_input_type.__name__}")
        
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
                print("   ❌ PROBLEM: 'author' field is missing!")
                
            if not has_post:
                print("   ✓ CORRECT: 'post' field is excluded (prevents circular reference)")
            else:
                print("   ❌ UNEXPECTED: 'post' field is present")
        else:
            print("   ❌ ERROR: Cannot access fields in generated type")
    else:
        print("6. ❌ ERROR: 'comments' not found in reverse relations")

if __name__ == "__main__":
    try:
        debug_post_nested_comments()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()