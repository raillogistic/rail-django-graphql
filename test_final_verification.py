#!/usr/bin/env python
"""
Final verification script to confirm the author field fix is working correctly.
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from test_app.models import Post, Comment, User
from django_graphql_auto.generators.types import TypeGenerator
from django_graphql_auto.core.settings import TypeGeneratorSettings


def test_final_verification():
    """Final verification that the author field fix is working correctly."""
    print("=== Final Verification of Author Field Fix ===")
    
    # Initialize type generator
    settings = TypeGeneratorSettings()
    type_generator = TypeGenerator(settings)
    
    print("\n1. Testing CommentNestedCreateInput generation for Post model:")
    
    # Generate nested input type for Comment when used in Post context
    comment_nested_input = type_generator._get_or_create_nested_input_type(
        Comment, 
        mutation_type='create',
        exclude_parent_field=Post  # This should exclude 'post' field but include 'author'
    )
    
    print(f"   Generated type: {comment_nested_input.__name__}")
    print(f"   Available fields: {list(comment_nested_input._meta.fields.keys())}")
    
    # Check for author field
    has_author = 'author' in comment_nested_input._meta.fields
    has_post = 'post' in comment_nested_input._meta.fields
    
    print(f"   ✓ Has 'author' field: {has_author}")
    print(f"   ✓ Has 'post' field: {has_post} (should be False)")
    
    print("\n2. Testing CommentNestedCreateInput generation for User model:")
    
    # Generate nested input type for Comment when used in User context
    comment_nested_input_user = type_generator._get_or_create_nested_input_type(
        Comment, 
        mutation_type='create',
        exclude_parent_field=User  # This should exclude 'author' field but include 'post'
    )
    
    print(f"   Generated type: {comment_nested_input_user.__name__}")
    print(f"   Available fields: {list(comment_nested_input_user._meta.fields.keys())}")
    
    # Check for fields
    has_author_user = 'author' in comment_nested_input_user._meta.fields
    has_post_user = 'post' in comment_nested_input_user._meta.fields
    
    print(f"   ✓ Has 'author' field: {has_author_user} (should be False)")
    print(f"   ✓ Has 'post' field: {has_post_user}")
    
    print("\n3. Verifying schema.graphql content:")
    
    # Read schema file
    with open('schema.graphql', 'r') as f:
        schema_content = f.read()
    
    # Check for the correct input types
    has_exclude_post = 'CommentNestedCreateInput_exclude_Post' in schema_content
    has_exclude_user = 'CommentNestedCreateInput_exclude_User' in schema_content
    
    print(f"   ✓ Schema contains CommentNestedCreateInput_exclude_Post: {has_exclude_post}")
    print(f"   ✓ Schema contains CommentNestedCreateInput_exclude_User: {has_exclude_user}")
    
    # Check PostInput uses the correct variant
    post_input_section = schema_content[schema_content.find('input PostInput'):schema_content.find('input PostInput') + 1000]
    uses_correct_variant = 'CommentNestedCreateInput_exclude_Post' in post_input_section
    
    print(f"   ✓ PostInput uses CommentNestedCreateInput_exclude_Post: {uses_correct_variant}")
    
    print("\n=== SUMMARY ===")
    
    if has_author and not has_post and not has_author_user and has_post_user and uses_correct_variant:
        print("🎉 SUCCESS: The author field fix is working correctly!")
        print("   - CommentNestedCreateInput_exclude_Post includes 'author' field (✓)")
        print("   - CommentNestedCreateInput_exclude_Post excludes 'post' field (✓)")
        print("   - CommentNestedCreateInput_exclude_User excludes 'author' field (✓)")
        print("   - CommentNestedCreateInput_exclude_User includes 'post' field (✓)")
        print("   - PostInput correctly uses CommentNestedCreateInput_exclude_Post (✓)")
        return True
    else:
        print("❌ ISSUE: The fix is not working as expected.")
        print(f"   - Author in Post context: {has_author} (should be True)")
        print(f"   - Post excluded in Post context: {not has_post} (should be True)")
        print(f"   - Author excluded in User context: {not has_author_user} (should be True)")
        print(f"   - Post in User context: {has_post_user} (should be True)")
        print(f"   - Correct variant in PostInput: {uses_correct_variant} (should be True)")
        return False


if __name__ == "__main__":
    test_final_verification()