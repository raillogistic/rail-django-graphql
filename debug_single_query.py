#!/usr/bin/env python
"""
Debug script to investigate why single object queries by ID are returning null.
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from test_app.models import Client, LocalClient, Post
from django_graphql_auto.core.schema import SchemaBuilder
import graphene

def debug_single_queries():
    """Debug single object queries to understand why they return null"""
    print("Debugging single object queries...")
    
    # Check existing data
    print("\n1. Checking existing data:")
    clients = Client.objects.all()
    posts = Post.objects.all()
    
    print(f"   Total clients: {clients.count()}")
    for client in clients[:5]:  # Show first 5
        print(f"     - Client ID: {client.id}, Raison: {client.raison}, Type: {type(client).__name__}")
    
    print(f"   Total posts: {posts.count()}")
    for post in posts[:5]:  # Show first 5
        print(f"     - Post ID: {post.id}, Title: {post.title}")
    
    # Build schema
    print("\n2. Building schema...")
    schema_builder = SchemaBuilder()
    schema_builder.register_app('test_app')
    schema = schema_builder.get_schema()
    
    # Test single client query with existing ID
    if clients.exists():
        client_id = clients.first().id
        print(f"\n3. Testing single client query with ID: {client_id}")
        
        single_client_query = """
        query GetClient($id: ID!) {
            client(id: $id) {
                id
                raison
                polymorphic_type
            }
        }
        """
        
        result = schema.execute(single_client_query, variables={"id": str(client_id)})
        
        if result.errors:
            print(f"   ❌ Errors: {result.errors}")
        else:
            print(f"   ✅ Result: {result.data}")
            if result.data.get('client') is None:
                print("   ⚠️  Client is null - investigating resolver...")
    
    # Test single post query with existing ID
    if posts.exists():
        post_id = posts.first().id
        print(f"\n4. Testing single post query with ID: {post_id}")
        
        single_post_query = """
        query GetPost($id: ID!) {
            post(id: $id) {
                id
                title
                content
            }
        }
        """
        
        result = schema.execute(single_post_query, variables={"id": str(post_id)})
        
        if result.errors:
            print(f"   ❌ Errors: {result.errors}")
        else:
            print(f"   ✅ Result: {result.data}")
            if result.data.get('post') is None:
                print("   ⚠️  Post is null - investigating resolver...")
    
    # Test list queries to ensure they work
    print("\n5. Testing list queries for comparison:")
    
    list_clients_query = """
    query GetAllClients {
        allClients {
            id
            raison
            polymorphic_type
        }
    }
    """
    
    result = schema.execute(list_clients_query)
    if result.errors:
        print(f"   ❌ List clients errors: {result.errors}")
    else:
        clients_data = result.data.get('allClients', [])
        print(f"   ✅ List clients returned {len(clients_data)} items")
        if clients_data:
            print(f"       First client: {clients_data[0]}")
    
    list_posts_query = """
    query GetAllPosts {
        allPosts {
            id
            title
        }
    }
    """
    
    result = schema.execute(list_posts_query)
    if result.errors:
        print(f"   ❌ List posts errors: {result.errors}")
    else:
        posts_data = result.data.get('allPosts', [])
        print(f"   ✅ List posts returned {len(posts_data)} items")
        if posts_data:
            print(f"       First post: {posts_data[0]}")

if __name__ == "__main__":
    try:
        debug_single_queries()
    except Exception as e:
        print(f"❌ Debug failed with exception: {e}")
        import traceback
        traceback.print_exc()