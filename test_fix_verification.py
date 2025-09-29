# -*- coding: utf-8 -*-
"""
Test script to verify the NOT NULL constraint fix works for various nested operations
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category, Tag
from django_graphql_auto.schema import schema

def test_nested_comment_creation():
    """Test creating new comments in nested updates"""
    print("=== Testing Nested Comment Creation ===")
    
    # Clean up
    Comment.objects.filter(content__contains="test_nested").delete()
    Post.objects.filter(title__contains="Test Nested").delete()
    User.objects.filter(username="test_nested_user").delete()
    Category.objects.filter(name="Test Nested Category").delete()
    
    # Create test data
    user = User.objects.create_user(username='test_nested_user', email='test_nested@test.com')
    category = Category.objects.create(name='Test Nested Category')
    post = Post.objects.create(title='Test Nested Post', content='Test content', category=category)
    
    # Test creating new comment with author as ID
    mutation = f'''
    mutation {{
        update_post(id:"{post.id}",input:{{ 
            nested_comments:[ 
                {{content:"test_nested_comment_1",author:"{user.id}"}}, 
            ], 
            title:"Test Nested Updated", 
        }}){{ 
            ok 
            errors 
            object {{
                comments {{
                    pk
                    content
                    author {{
                        pk
                        username
                    }}
                }}
            }}
        }} 
    }}
    '''
    
    result = schema.execute(mutation)
    if result.data['update_post']['ok']:
        print("✓ Nested comment creation with author ID: SUCCESS")
    else:
        print(f"✗ Nested comment creation with author ID: FAILED - {result.data['update_post']['errors']}")
    
    return result.data['update_post']['ok']

def test_nested_comment_with_multiple_fields():
    """Test creating comments with multiple foreign key fields"""
    print("\n=== Testing Multiple Foreign Key Fields ===")
    
    # Clean up
    Comment.objects.filter(content__contains="test_multi").delete()
    Post.objects.filter(title__contains="Test Multi").delete()
    User.objects.filter(username="test_multi_user").delete()
    Category.objects.filter(name="Test Multi Category").delete()
    
    # Create test data
    user = User.objects.create_user(username='test_multi_user', email='test_multi@test.com')
    category = Category.objects.create(name='Test Multi Category')
    post = Post.objects.create(title='Test Multi Post', content='Test content', category=category)
    
    # Test creating comment with both author and post references
    mutation = f'''
    mutation {{
        update_post(id:"{post.id}",input:{{ 
            nested_comments:[ 
                {{
                    content:"test_multi_comment",
                    author:"{user.id}",
                    is_approved:true
                }}, 
            ], 
        }}){{ 
            ok 
            errors 
        }} 
    }}
    '''
    
    result = schema.execute(mutation)
    if result.data['update_post']['ok']:
        print("✓ Multiple foreign key fields: SUCCESS")
    else:
        print(f"✗ Multiple foreign key fields: FAILED - {result.data['update_post']['errors']}")
    
    return result.data['update_post']['ok']

def test_create_comment_directly():
    """Test creating comments directly (not nested)"""
    print("\n=== Testing Direct Comment Creation ===")
    
    # Clean up
    Comment.objects.filter(content__contains="test_direct").delete()
    Post.objects.filter(title__contains="Test Direct").delete()
    User.objects.filter(username="test_direct_user").delete()
    Category.objects.filter(name="Test Direct Category").delete()
    
    # Create test data
    user = User.objects.create_user(username='test_direct_user', email='test_direct@test.com')
    category = Category.objects.create(name='Test Direct Category')
    post = Post.objects.create(title='Test Direct Post', content='Test content', category=category)
    
    # Test creating comment directly
    mutation = f'''
    mutation {{
        create_comment(input:{{ 
            content:"test_direct_comment",
            author:"{user.id}",
            post:"{post.id}",
            is_approved:true
        }}){{ 
            ok 
            errors 
            object {{
                pk
                content
                author {{
                    username
                }}
                post {{
                    title
                }}
            }}
        }} 
    }}
    '''
    
    result = schema.execute(mutation)
    if result.data['create_comment']['ok']:
        print("✓ Direct comment creation: SUCCESS")
    else:
        print(f"✗ Direct comment creation: FAILED - {result.data['create_comment']['errors']}")
    
    return result.data['create_comment']['ok']

def test_nested_post_creation():
    """Test creating posts with nested comments"""
    print("\n=== Testing Nested Post Creation ===")
    
    # Clean up
    Comment.objects.filter(content__contains="test_post_nested").delete()
    Post.objects.filter(title__contains="Test Post Nested").delete()
    User.objects.filter(username="test_post_nested_user").delete()
    Category.objects.filter(name="Test Post Nested Category").delete()
    
    # Create test data
    user = User.objects.create_user(username='test_post_nested_user', email='test_post_nested@test.com')
    category = Category.objects.create(name='Test Post Nested Category')
    
    # Test creating post with nested comments
    mutation = f'''
    mutation {{
        create_post(input:{{ 
            title:"Test Post Nested Creation",
            content:"Test content",
            category:"{category.id}",
            nested_comments:[ 
                {{
                    content:"test_post_nested_comment",
                    author:"{user.id}",
                    is_approved:true
                }}, 
            ]
        }}){{ 
            ok 
            errors 
            object {{
                pk
                title
                comments {{
                    pk
                    content
                    author {{
                        username
                    }}
                }}
            }}
        }} 
    }}
    '''
    
    result = schema.execute(mutation)
    if result.data['create_post']['ok']:
        print("✓ Nested post creation with comments: SUCCESS")
    else:
        print(f"✗ Nested post creation with comments: FAILED - {result.data['create_post']['errors']}")
    
    return result.data['create_post']['ok']

def main():
    print("=== COMPREHENSIVE FIX VERIFICATION ===")
    
    tests = [
        test_nested_comment_creation,
        test_nested_comment_with_multiple_fields,
        test_create_comment_directly,
        test_nested_post_creation
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print(f"\n=== SUMMARY ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ ALL TESTS PASSED - Fix is working correctly!")
    else:
        print("✗ Some tests failed - Fix may need additional work")
    
    print("=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    main()