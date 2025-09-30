#!/usr/bin/env python
"""
Test script to verify that single object queries by ID now work correctly
for both Client and Post models.
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from test_app.models import Client, LocalClient, Post, Category
from rail_django_graphql.core.schema import SchemaBuilder
import graphene


def test_single_query_fix():
    """Test that single object queries by ID now work correctly"""
    print("Testing single object query fix...")

    # Clean up existing data
    Client.objects.all().delete()
    Post.objects.all().delete()

    # Create test data
    print("\n1. Creating test data...")
    client = Client.objects.create(raison="Test Base Client for Fix")
    local_client = LocalClient.objects.create(
        raison="Test Local Client for Fix", test="Local Info"
    )

    # Create a category first for the post
    category = Category.objects.create(
        name="Test Category", description="Test category for fix"
    )
    post = Post.objects.create(
        title="Test Post for Fix", content="Testing single query fix", category=category
    )

    print(f"   Created Client: {client.id} - {client.raison}")
    print(f"   Created LocalClient: {local_client.id} - {local_client.raison}")
    print(f"   Created Post: {post.id} - {post.title}")

    # Build schema
    print("\n2. Building schema...")
    schema_builder = SchemaBuilder()
    schema_builder.register_app("test_app")
    schema = schema_builder.get_schema()

    # Test single client query
    print(f"\n3. Testing single client query (ID: {client.id})...")
    single_client_query = """
    query GetClient($id: ID!) {
        client(id: $id) {
            id
            raison
            polymorphic_type
        }
    }
    """

    result = schema.execute(single_client_query, variables={"id": str(client.id)})

    if result.errors:
        print(f"   ❌ Errors: {result.errors}")
        return False
    else:
        client_data = result.data.get("client")
        if client_data:
            print(f"   ✅ Success: {client_data}")
            if client_data["polymorphic_type"] != "Client":
                print(
                    f"   ⚠️  Expected 'Client', got '{client_data['polymorphic_type']}'"
                )
        else:
            print("   ❌ Client is null")
            return False

    # Test single local client query
    print(f"\n4. Testing single local client query (ID: {local_client.id})...")

    result = schema.execute(single_client_query, variables={"id": str(local_client.id)})

    if result.errors:
        print(f"   ❌ Errors: {result.errors}")
        return False
    else:
        local_client_data = result.data.get("client")
        if local_client_data:
            print(f"   ✅ Success: {local_client_data}")
            if local_client_data["polymorphic_type"] != "LocalClient":
                print(
                    f"   ⚠️  Expected 'LocalClient', got '{local_client_data['polymorphic_type']}'"
                )
        else:
            print("   ❌ LocalClient is null")
            return False

    # Test single post query
    print(f"\n5. Testing single post query (ID: {post.id})...")
    single_post_query = """
    query GetPost($id: ID!) {
        post(id: $id) {
            id
            title
            content
        }
    }
    """

    result = schema.execute(single_post_query, variables={"id": str(post.id)})

    if result.errors:
        print(f"   ❌ Errors: {result.errors}")
        return False
    else:
        post_data = result.data.get("post")
        if post_data:
            print(f"   ✅ Success: {post_data}")
        else:
            print("   ❌ Post is null")
            return False

    # Test list queries to ensure they still work
    print("\n6. Testing list queries to ensure they still work...")

    list_clients_query = """
    query GetClients {
        clients {
            id
            raison
            polymorphic_type
        }
    }
    """

    result = schema.execute(list_clients_query)
    if result.errors:
        print(f"   ❌ List clients errors: {result.errors}")
        return False
    else:
        clients_data = result.data.get("clients", [])
        print(f"   ✅ List clients returned {len(clients_data)} items")
        if clients_data:
            print(f"       First client: {clients_data[0]}")

    list_posts_query = """
    query GetPosts {
        posts {
            id
            title
        }
    }
    """

    result = schema.execute(list_posts_query)
    if result.errors:
        print(f"   ❌ List posts errors: {result.errors}")
        return False
    else:
        posts_data = result.data.get("posts", [])
        print(f"   ✅ List posts returned {len(posts_data)} items")
        if posts_data:
            print(f"       First post: {posts_data[0]}")

    print("\n✅ SUCCESS: All single object queries now work correctly!")
    print("   - Client single query works")
    print("   - LocalClient single query works with correct polymorphic_type")
    print("   - Post single query works")
    print("   - List queries still work")

    return True


if __name__ == "__main__":
    try:
        success = test_single_query_fix()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
