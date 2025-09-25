#!/usr/bin/env python
"""
Test script to verify ManyToMany field handling with nested configuration.
This tests that when nested=False, ManyToMany fields still work with ID-based operations.
"""

import os
import sys
import django
from django.core.exceptions import ValidationError

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django_graphql_auto.core.settings import MutationGeneratorSettings
from django_graphql_auto.generators.types import TypeGenerator
from django_graphql_auto.generators.mutations import MutationGenerator
from django_graphql_auto.generators.nested_operations import NestedOperationHandler
from test_app.models import Post, Tag, Category
from django.contrib.auth.models import User


def test_m2m_with_nested_enabled():
    """Test ManyToMany fields with nested operations enabled."""
    print("=== Testing ManyToMany with nested=True ===")
    
    # Configuration with nested relations enabled for tags
    mutation_settings = MutationGeneratorSettings(
        enable_nested_relations=True,
        nested_field_config={
            'Post': {
                'tags': True  # Enable nested operations for tags
            }
        }
    )
    
    nested_handler = NestedOperationHandler(mutation_settings)
    
    # Test data with nested tag creation
    test_data = {
        'title': 'Test Post with Nested Tags',
        'content': 'Content with nested tag creation',
        'slug': 'test-post-nested-tags',
        'status': 'published',
        'is_featured': False,
        'author': 1,  # Use ID instead of author_id
        'category': 1,  # Use ID instead of category_id
        'tags': [
            {'name': 'New Tag 1', 'slug': 'new-tag-1'},  # Create new tag
            {'name': 'New Tag 2', 'slug': 'new-tag-2'},  # Create new tag
            1,  # Reference existing tag by ID
            2   # Reference existing tag by ID
        ]
    }
    
    try:
        # This should work - nested operations are enabled
        post = nested_handler.handle_nested_create(Post, test_data)
        print(f"✓ Created post with nested tags: {post.title}")
        print(f"  Tags count: {post.tags.count()}")
        return True
    except Exception as e:
        print(f"✗ Failed to create post with nested tags: {e}")
        return False


def test_m2m_with_nested_disabled():
    """Test ManyToMany fields with nested operations disabled."""
    print("\n=== Testing ManyToMany with nested=False ===")
    
    # Configuration with nested relations disabled for tags
    mutation_settings = MutationGeneratorSettings(
        enable_nested_relations=True,  # Global enabled
        nested_field_config={
            'Post': {
                'tags': False  # Disable nested operations for tags
            }
        }
    )
    
    nested_handler = NestedOperationHandler(mutation_settings)
    
    # Test 1: ID-based operations should work
    print("\n1. Testing ID-based operations (should work)...")
    test_data_ids = {
        'title': 'Test Post with ID Tags',
        'content': 'Content with ID-based tag references',
        'slug': 'test-post-id-tags',
        'status': 'published',
        'is_featured': False,
        'author': 1,  # Use ID instead of author_id
        'category': 1,  # Use ID instead of category_id
        'tags': [1, 2, 3]  # Only ID references
    }
    
    try:
        post = nested_handler.handle_nested_create(Post, test_data_ids)
        print(f"✓ Created post with ID-based tags: {post.title}")
        print(f"  Tags count: {post.tags.count()}")
        id_test_passed = True
    except Exception as e:
        print(f"✗ Failed to create post with ID-based tags: {e}")
        id_test_passed = False
    
    # Test 2: Nested object creation should fail
    print("\n2. Testing nested object creation (should fail)...")
    test_data_nested = {
        'title': 'Test Post with Nested Tags',
        'content': 'Content with nested tag creation',
        'slug': 'test-post-nested-tags-fail',
        'status': 'published',
        'is_featured': False,
        'author': 1,  # Use ID instead of author_id
        'category': 1,  # Use ID instead of category_id
        'tags': [
            {'name': 'Should Fail Tag', 'slug': 'should-fail-tag'},  # This should fail
            1, 2  # These should work
        ]
    }
    
    try:
        post = nested_handler.handle_nested_create(Post, test_data_nested)
        print(f"✗ Unexpectedly created post with nested tags: {post.title}")
        nested_test_passed = False
    except ValidationError as e:
        if "Nested operations are disabled" in str(e):
            print(f"✓ Correctly rejected nested tag creation: {e}")
            nested_test_passed = True
        else:
            print(f"✗ Wrong error for nested tag creation: {e}")
            nested_test_passed = False
    except Exception as e:
        print(f"✗ Unexpected error for nested tag creation: {e}")
        nested_test_passed = False
    
    return id_test_passed and nested_test_passed


def test_m2m_dict_operations_disabled():
    """Test ManyToMany dict operations when nested is disabled."""
    print("\n=== Testing ManyToMany dict operations with nested=False ===")
    
    # Configuration with nested relations disabled for tags
    mutation_settings = MutationGeneratorSettings(
        enable_nested_relations=True,
        nested_field_config={
            'Post': {
                'tags': False  # Disable nested operations for tags
            }
        }
    )
    
    nested_handler = NestedOperationHandler(mutation_settings)
    
    # Test dict-based operations (should fail when nested is disabled)
    test_data_dict = {
        'title': 'Test Post with Dict Tags',
        'content': 'Content with dict-based tag operations',
        'slug': 'test-post-dict-tags',
        'status': 'published',
        'is_featured': False,
        'author': 1,  # Use ID instead of author_id
        'category': 1,  # Use ID instead of category_id
        'tags': {
            'connect': [1, 2],  # This should fail when nested=False
            'create': [{'name': 'New Tag', 'slug': 'new-tag'}]
        }
    }
    
    try:
        post = nested_handler.handle_nested_create(Post, test_data_dict)
        print(f"✗ Unexpectedly created post with dict tags: {post.title}")
        return False
    except ValidationError as e:
        if "Nested operations are disabled" in str(e):
            print(f"✓ Correctly rejected dict-based tag operations: {e}")
            return True
        else:
            print(f"✗ Wrong error for dict-based tag operations: {e}")
            return False
    except Exception as e:
        print(f"✗ Unexpected error for dict-based tag operations: {e}")
        return False


def main():
    """Run all ManyToMany nested configuration tests."""
    print("Testing ManyToMany field handling with nested configuration...")
    
    # Ensure we have test data
    try:
        # Create test author and category if they don't exist
        author, _ = User.objects.get_or_create(
            id=1,
            defaults={'username': 'testauthor', 'email': 'test@example.com'}
        )
        category, _ = Category.objects.get_or_create(
            id=1,
            defaults={'name': 'Test Category', 'slug': 'test-category', 'description': 'Test category description'}
        )
        
        # Create test tags if they don't exist
        for i in range(1, 4):
            Tag.objects.get_or_create(
                id=i,
                defaults={'name': f'Test Tag {i}', 'slug': f'test-tag-{i}'}
            )
        
        print("✓ Test data prepared")
    except Exception as e:
        print(f"✗ Failed to prepare test data: {e}")
        return False
    
    # Run tests
    test1_passed = test_m2m_with_nested_enabled()
    test2_passed = test_m2m_with_nested_disabled()
    test3_passed = test_m2m_dict_operations_disabled()
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY:")
    print(f"✓ ManyToMany with nested=True: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"✓ ManyToMany with nested=False (ID operations): {'PASSED' if test2_passed else 'FAILED'}")
    print(f"✓ ManyToMany dict operations disabled: {'PASSED' if test3_passed else 'FAILED'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    print(f"\nOverall result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)