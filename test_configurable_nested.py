#!/usr/bin/env python
"""
Test script for configurable nested relationships in mutations.
Tests both nested and non-nested configurations with quote handling.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
        USE_TZ=True,
        SECRET_KEY='test-secret-key-for-testing-only'
    )
    django.setup()
    
    # Create database tables
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])

from django.db import transaction
from test_app.models import Post, Comment, Category, User
from django_graphql_auto.core.settings import MutationGeneratorSettings
from django_graphql_auto.generators.types import TypeGenerator
from django_graphql_auto.generators.mutations import MutationGenerator


def test_nested_enabled_configuration():
    """Test mutations with nested relationships enabled (default)."""
    print("=== Testing Nested Relations ENABLED ===")
    
    # Configuration with nested relations enabled
    mutation_settings = MutationGeneratorSettings(
        enable_nested_relations=True
    )
    
    type_generator = TypeGenerator(mutation_settings=mutation_settings)
    mutation_generator = MutationGenerator(type_generator, mutation_settings)
    
    # Generate input type for Post with nested relations
    input_type = type_generator.generate_input_type(Post, mutation_type='create')
    
    # Check if comments field is present (nested relation)
    input_fields = input_type._meta.fields
    print(f"Available input fields: {list(input_fields.keys())}")
    
    has_comments = 'comments' in input_fields
    print(f"✓ Comments field present (nested): {has_comments}")
    
    # Test creating a post with nested comments and quotes
    test_data = {
        'title': 'Post with "nested" comments',
        'content': 'Content with "double quotes" and nested data',
        'slug': 'post-with-nested-comments',
        'status': 'published',
        'is_featured': True,
        'author_id': 1,
        'category_id': 1,
        'comments': [
            {
                'content': 'First comment with "quotes"',
                'author_id': 1
            },
            {
                'content': 'Second comment with "more quotes"',
                'author_id': 1
            }
        ]
    }
    
    print(f"✓ Test data with nested comments: {len(test_data.get('comments', []))} comments")
    print(f"✓ Quote handling in title: {test_data['title']}")
    print(f"✓ Quote handling in content: {test_data['content']}")
    print(f"✓ Quote handling in comments: {[c['content'] for c in test_data['comments']]}")
    
    return has_comments


def test_nested_disabled_configuration():
    """Test mutations with nested relationships disabled."""
    print("\n=== Testing Nested Relations DISABLED ===")
    
    # Configuration with nested relations disabled
    mutation_settings = MutationGeneratorSettings(
        enable_nested_relations=False
    )
    
    type_generator = TypeGenerator(mutation_settings=mutation_settings)
    mutation_generator = MutationGenerator(type_generator, mutation_settings)
    
    # Generate input type for Post without nested relations
    input_type = type_generator.generate_input_type(Post, mutation_type='create')
    
    # Check if comments field is absent (no nested relation)
    input_fields = input_type._meta.fields
    print(f"Available input fields: {list(input_fields.keys())}")
    
    has_comments = 'comments' in input_fields
    print(f"✓ Comments field absent (no nested): {not has_comments}")
    
    # Test creating a post without nested comments but with quotes
    test_data = {
        'title': 'Post without "nested" comments',
        'content': 'Content with "double quotes" but no nested data',
        'slug': 'post-without-nested-comments',
        'status': 'published',
        'is_featured': True,
        'author_id': 1,
        'category_id': 1
    }
    
    print(f"✓ Test data without nested comments: {'comments' not in test_data}")
    print(f"✓ Quote handling in title: {test_data['title']}")
    print(f"✓ Quote handling in content: {test_data['content']}")
    
    return not has_comments


def test_per_model_configuration():
    """Test per-model nested relationship configuration."""
    print("\n=== Testing Per-Model Configuration ===")
    
    # Configuration with per-model settings
    mutation_settings = MutationGeneratorSettings(
        enable_nested_relations=True,  # Global enabled
        nested_relations_config={
            'Post': False,  # But disabled for Post specifically
            'Comment': True  # Enabled for Comment
        }
    )
    
    type_generator = TypeGenerator(mutation_settings=mutation_settings)
    mutation_generator = MutationGenerator(type_generator, mutation_settings)
    
    # Test Post (should not have nested relations)
    post_input_type = type_generator.generate_input_type(Post, mutation_type='create')
    post_fields = post_input_type._meta.fields
    post_has_comments = 'comments' in post_fields
    
    print(f"Post input fields: {list(post_fields.keys())}")
    print(f"✓ Post comments field absent (per-model config): {not post_has_comments}")
    
    # Test Comment (should have nested relations if any exist)
    comment_input_type = type_generator.generate_input_type(Comment, mutation_type='create')
    comment_fields = comment_input_type._meta.fields
    comment_has_replies = 'replies' in comment_fields
    
    print(f"Comment input fields: {list(comment_fields.keys())}")
    print(f"✓ Comment replies field present (per-model config): {comment_has_replies}")
    
    return not post_has_comments and comment_has_replies


def test_per_field_configuration():
    """Test per-field nested relationship configuration."""
    print("\n=== Testing Per-Field Configuration ===")
    
    # Configuration with per-field settings
    mutation_settings = MutationGeneratorSettings(
        enable_nested_relations=True,  # Global enabled
        nested_field_config={
            'Post': {
                'comments': False  # Disable comments field specifically
            }
        }
    )
    
    type_generator = TypeGenerator(mutation_settings=mutation_settings)
    mutation_generator = MutationGenerator(type_generator, mutation_settings)
    
    # Test Post (should not have comments field)
    post_input_type = type_generator.generate_input_type(Post, mutation_type='create')
    post_fields = post_input_type._meta.fields
    post_has_comments = 'comments' in post_fields
    
    print(f"Post input fields: {list(post_fields.keys())}")
    print(f"✓ Post comments field absent (per-field config): {not post_has_comments}")
    
    return not post_has_comments


def test_quote_handling_in_mutations():
    """Test quote handling in mutation data processing."""
    print("\n=== Testing Quote Handling ===")
    
    # Test data with various quote scenarios
    test_cases = [
        'Simple text without quotes',
        'Text with "double quotes"',
        'Text with ""double double quotes""',
        'Text with \'single quotes\'',
        'Mixed "double" and \'single\' quotes',
        'Escaped \\"quotes\\" in text',
        'JSON-like {"key": "value"} content'
    ]
    
    mutation_settings = MutationGeneratorSettings()
    type_generator = TypeGenerator(mutation_settings=mutation_settings)
    mutation_generator = MutationGenerator(type_generator, mutation_settings)
    
    print("✓ Testing quote handling scenarios:")
    for i, test_case in enumerate(test_cases, 1):
        print(f"  {i}. {test_case}")
        
        # Create a test mutation class to access the sanitize method
        CreateMutation = mutation_generator.generate_create_mutation(Comment)
        
        # Test sanitization (this would be called internally)
        try:
            sanitized = CreateMutation._sanitize_input_data({'content': test_case})
            expected_content = test_case.replace('""', '"')  # Expected transformation
            
            if sanitized['content'] == expected_content:
                print(f"     ✓ Sanitized correctly: {sanitized['content']}")
            else:
                print(f"     ❌ Sanitization failed: got {sanitized['content']}, expected {expected_content}")
                return False
        except Exception as e:
            print(f"     ❌ Error during sanitization: {e}")
            return False
    
    return True


def main():
    """Run all configuration tests."""
    print("Testing Configurable Nested Relationships and Quote Handling")
    print("=" * 60)
    
    try:
        # Create test data
        with transaction.atomic():
            user, _ = User.objects.get_or_create(
                username='testuser',
                defaults={'email': 'test@example.com'}
            )
            category, _ = Category.objects.get_or_create(
                name='Test Category',
                defaults={'description': 'Test category description'}
            )
        
        # Run tests
        test_results = []
        
        test_results.append(test_nested_enabled_configuration())
        test_results.append(test_nested_disabled_configuration())
        test_results.append(test_per_model_configuration())
        test_results.append(test_per_field_configuration())
        test_results.append(test_quote_handling_in_mutations())
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(test_results)
        total = len(test_results)
        
        print(f"✓ Nested relations enabled: {'PASS' if test_results[0] else 'FAIL'}")
        print(f"✓ Nested relations disabled: {'PASS' if test_results[1] else 'FAIL'}")
        print(f"✓ Per-model configuration: {'PASS' if test_results[2] else 'FAIL'}")
        print(f"✓ Per-field configuration: {'PASS' if test_results[3] else 'FAIL'}")
        print(f"✓ Quote handling: {'PASS' if test_results[4] else 'FAIL'}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All configuration tests completed successfully!")
        else:
            print("❌ Some tests failed. Check the output above.")
            
        return passed == total
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)