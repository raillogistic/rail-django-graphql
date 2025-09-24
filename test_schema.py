#!/usr/bin/env python
"""
Test script to verify the GraphQL schema fixes.
Tests both the empty Q() filter fix and the direct model access for reverse relationships.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment
from django_graphql_auto.schema import schema
from graphene.test import Client

def create_test_data():
    """Create test data for testing."""
    print("Creating test data...")
    
    # Import Category model
    from test_app.models import Category
    
    # Clear existing data to avoid unique constraint issues
    User.objects.all().delete()
    Post.objects.all().delete()
    Comment.objects.all().delete()
    Category.objects.all().delete()
    
    # Create users
    user1 = User.objects.create_user(username='user1', email='user1@test.com')
    user2 = User.objects.create_user(username='user2', email='user2@test.com')
    user3 = User.objects.create_user(username='user3', email='user3@test.com')
    
    # Create category (required for posts)
    category = Category.objects.create(name='Test Category', slug='test-category')
    
    # Create posts
    post1 = Post.objects.create(title='Post 1', slug='post-1', content='Content 1', author=user1, category=category)
    post2 = Post.objects.create(title='Post 2', slug='post-2', content='Content 2', author=user1, category=category)
    post3 = Post.objects.create(title='Post 3', slug='post-3', content='Content 3', author=user2, category=category)
    
    # Create comments
    Comment.objects.create(content='Comment 1', post=post1, author=user1)
    Comment.objects.create(content='Comment 2', post=post1, author=user2)
    Comment.objects.create(content='Comment 3', post=post2, author=user3)
    
    print(f"Created {User.objects.count()} users, {Post.objects.count()} posts, {Comment.objects.count()} comments")
    return user1, user2, user3

def test_user_query_without_args():
    """Test that user query without arguments returns None instead of error."""
    print("\n=== Testing user query without arguments ===")
    
    client = Client(schema)
    query = """
    query {
        user {
            id
            username
        }
    }
    """
    
    result = client.execute(query)
    print(f"Query result: {result}")
    
    if 'errors' in result:
        print("❌ FAILED: Query returned errors")
        for error in result['errors']:
            print(f"   Error: {error['message']}")
        return False
    else:
        print("✅ PASSED: Query executed without errors")
        print(f"   Result: {result['data']['user']}")
        return True

def test_user_with_posts_direct_access():
    """Test that user.posts returns direct list of Post objects."""
    print("\n=== Testing user.posts direct access ===")
    
    # First, let's check what users exist and get their actual IDs
    users = User.objects.all()
    print(f"Available users: {[(u.id, u.username) for u in users]}")
    
    if not users:
        print("❌ FAILED: No users found in database")
        return False
    
    # Use the first user's actual ID
    user_id = users[0].id
    
    query = f"""
    query {{
        user(id: "{user_id}") {{
            username
            posts {{
                title
                content
            }}
        }}
    }}
    """
    
    try:
        result = schema.execute(query)
        print(f"Query result: {result.data}")
        
        if result.errors:
            print(f"❌ FAILED: Query returned errors")
            for error in result.errors:
                print(f"   Error: {error.message}")
            return False
        
        user_data = result.data.get('user')
        if not user_data:
            print("❌ FAILED: No user data returned")
            return False
        
        posts = user_data.get('posts')
        if posts is None:
            print("❌ FAILED: posts field is None")
            return False
        
        # Check if posts is a direct list (not a relay connection)
        if isinstance(posts, list):
            print(f"✅ PASSED: posts is a direct list with {len(posts)} items")
            for i, post in enumerate(posts):
                print(f"   Post {i+1}: {post.get('title', 'No title')}")
            return True
        else:
            print(f"❌ FAILED: posts is not a direct list, got: {type(posts)}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: test_user_with_posts_direct_access raised exception: {e}")
        return False

def test_schema_introspection():
    """Test schema introspection to see available types and fields."""
    print("\n=== Testing schema introspection ===")
    
    client = Client(schema)
    query = """
    query {
        __schema {
            types {
                name
                fields {
                    name
                    type {
                        name
                    }
                }
            }
        }
    }
    """
    
    result = client.execute(query)
    if 'errors' in result:
        print("❌ FAILED: Schema introspection failed")
        for error in result['errors']:
            print(f"   Error: {error['message']}")
        return False
    
    # Find UserType
    user_type = None
    for type_info in result['data']['__schema']['types']:
        if type_info['name'] == 'UserType':
            user_type = type_info
            break
    
    if user_type:
        print("✅ PASSED: Found UserType in schema")
        print("   UserType fields:")
        for field in user_type['fields'] or []:
            print(f"     - {field['name']}: {field['type']['name'] if field['type'] else 'Unknown'}")
        
        # Check if posts field exists
        posts_field = next((f for f in user_type['fields'] or [] if f['name'] == 'posts'), None)
        if posts_field:
            print("✅ PASSED: posts field found in UserType")
            return True
        else:
            print("❌ FAILED: posts field not found in UserType")
            return False
    else:
        print("❌ FAILED: UserType not found in schema")
        return False

def main():
    """Run all tests."""
    print("Starting GraphQL schema tests...")
    
    # Create test data before running tests
    create_test_data()
    
    tests = [
        test_user_query_without_args,
        test_user_with_posts_direct_access,
        test_schema_introspection,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ FAILED: {test.__name__} raised exception: {e}")
            failed += 1
    
    print(f"\n=== Test Results ===")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n💥 {failed} test(s) failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())