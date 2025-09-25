#!/usr/bin/env python
"""
Debug script to investigate why author field is missing from CommentNestedCreateInput.
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from test_app.models import Comment, Post, User
from django_graphql_auto.generators.types import TypeGenerator
from django_graphql_auto.generators.introspector import ModelIntrospector
from django_graphql_auto.core.settings import MutationGeneratorSettings
import graphene

def debug_comment_nested_input():
    """Debug the CommentNestedCreateInput generation."""
    print("=== Debugging CommentNestedCreateInput Generation ===")
    
    # Initialize components
    type_generator = TypeGenerator()
    introspector = ModelIntrospector(Comment)
    
    print(f"1. Comment model: {Comment}")
    print(f"   Fields: {[f.name for f in Comment._meta.get_fields()]}")
    
    # Get field information
    field_info = introspector.fields
    print(f"\n2. Comment field info:")
    for field_name, info in field_info.items():
        print(f"   {field_name}: {info}")
    
    # Get relationship information
    relationships = introspector.relationships
    print(f"\n3. Comment relationships:")
    for rel_name, rel_info in relationships.items():
        print(f"   {rel_name}: {rel_info}")
        print(f"      related_model: {rel_info.related_model}")
        print(f"      relationship_type: {rel_info.relationship_type}")
    
    # Check field inclusion for author
    should_include_author = type_generator._should_include_field(Comment, 'author')
    print(f"\n4. Should include 'author' field: {should_include_author}")
    
    # Check field inclusion for post
    should_include_post = type_generator._should_include_field(Comment, 'post')
    print(f"   Should include 'post' field: {should_include_post}")
    
    # Get excluded fields
    excluded_fields = type_generator._get_excluded_fields(Comment)
    print(f"\n5. Excluded fields for Comment: {excluded_fields}")
    
    # Get included fields
    included_fields = type_generator._get_included_fields(Comment)
    print(f"   Included fields for Comment: {included_fields}")
    
    # Now let's try to generate CommentNestedCreateInput with exclude_parent_field
    print(f"\n6. Generating CommentNestedCreateInput with exclude_parent_field=Post...")
    
    # Generate the nested input type directly using the internal method
    try:
        nested_input_type = type_generator._get_or_create_nested_input_type(
            Comment, 
            mutation_type='create',
            exclude_parent_field=Post
        )
        print(f"   Generated type: {nested_input_type}")
        print(f"   Type name: {nested_input_type.__name__}")
        
        # Get the fields from the generated type
        if hasattr(nested_input_type, '_meta') and hasattr(nested_input_type._meta, 'fields'):
            fields = nested_input_type._meta.fields
            print(f"   Fields in generated type: {list(fields.keys())}")
            
            # Check if author field is present
            if 'author' in fields:
                print(f"   ✓ Author field is present: {fields['author']}")
            else:
                print(f"   ✗ Author field is missing!")
                
            # Check if post field is present
            if 'post' in fields:
                print(f"   ✓ Post field is present: {fields['post']}")
            else:
                print(f"   ✗ Post field is missing (expected to be excluded)")
        else:
            print(f"   Could not access fields from generated type")
            
    except Exception as e:
        print(f"   Error generating nested input type: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n7. Testing author field relationship info:")
    author_rel = relationships.get('author')
    if author_rel:
        print(f"   Author related_model: {author_rel.related_model}")
        print(f"   Post model: {Post}")
        print(f"   Are they equal? {author_rel.related_model == Post}")
        print(f"   Author related_model name: {author_rel.related_model.__name__}")
        print(f"   Post model name: {Post.__name__}")
    
    print(f"\n8. Testing post field relationship info:")
    post_rel = relationships.get('post')
    if post_rel:
        print(f"   Post related_model: {post_rel.related_model}")
        print(f"   Post model: {Post}")
        print(f"   Are they equal? {post_rel.related_model == Post}")
        print(f"   Post related_model name: {post_rel.related_model.__name__}")
        print(f"   Post model name: {Post.__name__}")

if __name__ == "__main__":
    debug_comment_nested_input()