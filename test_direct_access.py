"""
Test script to verify direct access for reverse relationships.
This tests that many-to-one relationships now use direct access instead of edges{node{}} structure.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from graphene.test import Client
from django_graphql_auto.schema import schema
from test_app.models import User, Post, Comment

def test_direct_access():
    """Test that reverse relationships use direct access instead of Connection types."""
    
    # Create test client
    client = Client(schema)
    
    # Test query with direct access to reverse relationships
    query = """
    query {
        users {
            pk
            username
            post_set {
                pk
                title
            }
            comment_set {
                pk
                content
            }
        }
    }
    """
    
    print("Testing direct access for reverse relationships...")
    print(f"Query: {query}")
    
    try:
        result = client.execute(query)
        print(f"Result: {result}")
        
        if result.get('errors'):
            print("❌ Errors found:")
            for error in result['errors']:
                print(f"  - {error}")
            return False
        
        # Check if we got data
        data = result.get('data', {})
        users = data.get('users', [])
        
        if not users:
            print("⚠️  No users found in result")
            return True
        
        # Check structure - should have direct access to post_set and comment_set
        first_user = users[0]
        print(f"First user structure: {first_user}")
        
        # Verify direct access (no edges/node structure)
        if 'post_set' in first_user and isinstance(first_user['post_set'], list):
            print("✅ post_set uses direct access (list)")
        else:
            print("❌ post_set does not use direct access")
            return False
            
        if 'comment_set' in first_user and isinstance(first_user['comment_set'], list):
            print("✅ comment_set uses direct access (list)")
        else:
            print("❌ comment_set does not use direct access")
            return False
        
        print("✅ All reverse relationships use direct access!")
        return True
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return False

def test_nested_direct_access():
    """Test nested queries with direct access."""
    
    client = Client(schema)
    
    query = """
    query {
        posts {
            pk
            title
            author {
                pk
                username
                post_set {
                    pk
                    title
                }
            }
            comments {
                pk
                content
                author {
                    pk
                    username
                }
            }
        }
    }
    """
    
    print("\nTesting nested direct access...")
    print(f"Query: {query}")
    
    try:
        result = client.execute(query)
        print(f"Result: {result}")
        
        if result.get('errors'):
            print("❌ Errors found:")
            for error in result['errors']:
                print(f"  - {error}")
            return False
        
        print("✅ Nested direct access works!")
        return True
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING DIRECT ACCESS FOR REVERSE RELATIONSHIPS")
    print("=" * 60)
    
    success1 = test_direct_access()
    success2 = test_nested_direct_access()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 ALL TESTS PASSED - Direct access is working!")
    else:
        print("❌ Some tests failed")
    print("=" * 60)