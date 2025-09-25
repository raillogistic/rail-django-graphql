#!/usr/bin/env python
"""
Test script to verify the fix for nested comment duplication bug.
This script tests that creating a post with one nested comment creates exactly one comment.
"""

import os
import sys
import django

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from django_graphql_auto.generators.nested_operations import NestedOperationHandler
from django_graphql_auto.core.config_loader import load_mutation_settings
from django.db import transaction
import time

def test_nested_comment_duplication_fix():
    """Test that creating a post with one nested comment creates exactly one comment."""
    print("=== Testing Nested Comment Duplication Fix ===")
    
    # Clean up any existing test data
    Comment.objects.filter(content__contains="Test comment for duplication fix").delete()
    Post.objects.filter(title__contains="Test Post for Duplication Fix").delete()
    
    # Create test user and category
    user, _ = User.objects.get_or_create(
        username='testuser_dup_fix',
        defaults={'email': 'testuser@example.com'}
    )
    
    category, _ = Category.objects.get_or_create(
        name='Test Category Dup Fix',
        defaults={'slug': 'test-category-dup-fix', 'description': 'Test category'}
    )
    
    # Initialize nested operation handler
    settings = load_mutation_settings()
    nested_handler = NestedOperationHandler(settings)
    
    # Create unique identifiers
    unique_id = int(time.time())
    
    # Test data with ONE nested comment
    test_data = {
        'title': f'Test Post for Duplication Fix {unique_id}',
        'content': 'This post tests the nested comment duplication fix',
        'slug': f'test-post-dup-fix-{unique_id}',
        'status': 'published',
        'is_featured': False,
        'author': user.id,
        'category': category.id,
        'comments': [  # Using comments field (the correct reverse relationship name)
            {
                'content': f'Test comment for duplication fix {unique_id}',
                'author': user.id,
                'is_approved': True
            }
        ]
    }
    
    print(f"Creating post with 1 nested comment...")
    print(f"Input data: {test_data}")
    
    try:
        with transaction.atomic():
            # Create post with nested comment
            post = nested_handler.handle_nested_create(Post, test_data)
            
            # Count comments created
            comments_count = Comment.objects.filter(post=post).count()
            
            print(f"✓ Post created: {post.title}")
            print(f"✓ Comments created: {comments_count}")
            
            # Verify exactly one comment was created
            if comments_count == 1:
                print("✅ SUCCESS: Exactly 1 comment created for 1 nested comment input")
                
                # Get the comment and verify its content
                comment = Comment.objects.get(post=post)
                print(f"✓ Comment content: {comment.content}")
                print(f"✓ Comment author: {comment.author.username}")
                
                return True
            else:
                print(f"❌ FAIL: Expected 1 comment, but got {comments_count}")
                
                # List all comments for debugging
                comments = Comment.objects.filter(post=post)
                for i, comment in enumerate(comments, 1):
                    print(f"   Comment {i}: {comment.content}")
                
                return False
                
    except Exception as e:
        print(f"❌ ERROR: Failed to create post with nested comment: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_nested_comments():
    """Test that creating a post with multiple nested comments works correctly."""
    print("\n=== Testing Multiple Nested Comments ===")
    
    # Clean up any existing test data
    Comment.objects.filter(content__contains="Multiple comment test").delete()
    Post.objects.filter(title__contains="Multiple Comments Test").delete()
    
    # Create test user and category
    user, _ = User.objects.get_or_create(
        username='testuser_multiple',
        defaults={'email': 'testuser2@example.com'}
    )
    
    category, _ = Category.objects.get_or_create(
        name='Test Category Multiple',
        defaults={'slug': 'test-category-multiple', 'description': 'Test category'}
    )
    
    # Initialize nested operation handler
    settings = load_mutation_settings()
    nested_handler = NestedOperationHandler(settings)
    
    # Create unique identifiers
    unique_id = int(time.time())
    
    # Test data with THREE nested comments
    test_data = {
        'title': f'Multiple Comments Test {unique_id}',
        'content': 'This post tests multiple nested comments',
        'slug': f'multiple-comments-test-{unique_id}',
        'status': 'published',
        'is_featured': False,
        'author': user.id,
        'category': category.id,
        'comments': [
            {
                'content': f'Multiple comment test 1 - {unique_id}',
                'author': user.id,
                'is_approved': True
            },
            {
                'content': f'Multiple comment test 2 - {unique_id}',
                'author': user.id,
                'is_approved': True
            },
            {
                'content': f'Multiple comment test 3 - {unique_id}',
                'author': user.id,
                'is_approved': True
            }
        ]
    }
    
    print(f"Creating post with 3 nested comments...")
    
    try:
        with transaction.atomic():
            # Create post with nested comments
            post = nested_handler.handle_nested_create(Post, test_data)
            
            # Count comments created
            comments_count = Comment.objects.filter(post=post).count()
            
            print(f"✓ Post created: {post.title}")
            print(f"✓ Comments created: {comments_count}")
            
            # Verify exactly three comments were created
            if comments_count == 3:
                print("✅ SUCCESS: Exactly 3 comments created for 3 nested comment inputs")
                
                # List all comments
                comments = Comment.objects.filter(post=post).order_by('id')
                for i, comment in enumerate(comments, 1):
                    print(f"   Comment {i}: {comment.content}")
                
                return True
            else:
                print(f"❌ FAIL: Expected 3 comments, but got {comments_count}")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: Failed to create post with multiple nested comments: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Testing nested comment duplication fix...\n")
    
    # Test single nested comment
    single_test_passed = test_nested_comment_duplication_fix()
    
    # Test multiple nested comments
    multiple_test_passed = test_multiple_nested_comments()
    
    print(f"\n=== Test Results ===")
    print(f"Single nested comment test: {'PASSED' if single_test_passed else 'FAILED'}")
    print(f"Multiple nested comments test: {'PASSED' if multiple_test_passed else 'FAILED'}")
    
    if single_test_passed and multiple_test_passed:
        print("✅ All tests PASSED - Nested comment duplication fix is working!")
    else:
        print("❌ Some tests FAILED - Need to investigate further")