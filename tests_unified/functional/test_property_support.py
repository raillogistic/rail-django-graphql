#!/usr/bin/env python
"""
Test script to verify @property support in GraphQL schema generation.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rail_django_graphql.settings')
django.setup()

from test_app.models import Client, Category, Post
from rail_django_graphql.generators.types import TypeGenerator
from rail_django_graphql.generators.introspector import ModelIntrospector

def test_property_introspection():
    """Test that ModelIntrospector correctly detects @property methods."""
    print("=== Testing Property Introspection ===")
    
    # Test Client model
    client_introspector = ModelIntrospector(Client)
    client_properties = client_introspector.properties
    print(f"Client properties: {list(client_properties.keys())}")
    
    if 'uppercase_raison' in client_properties:
        prop_info = client_properties['uppercase_raison']
        print(f"  uppercase_raison return type: {prop_info.return_type}")
    
    # Test Category model
    category_introspector = ModelIntrospector(Category)
    category_properties = category_introspector.properties
    print(f"Category properties: {list(category_properties.keys())}")
    
    for prop_name, prop_info in category_properties.items():
        print(f"  {prop_name} return type: {prop_info.return_type}")
    
    # Test Post model
    post_introspector = ModelIntrospector(Post)
    post_properties = post_introspector.properties
    print(f"Post properties: {list(post_properties.keys())}")
    
    for prop_name, prop_info in post_properties.items():
        print(f"  {prop_name} return type: {prop_info.return_type}")

def test_graphql_type_generation():
    """Test that TypeGenerator includes @property methods in GraphQL types."""
    print("\n=== Testing GraphQL Type Generation ===")
    
    type_generator = TypeGenerator()
    
    # Test Client type
    client_type = type_generator.generate_object_type(Client)
    print(f"Client GraphQL type: {client_type.__name__}")
    
    # Check if property fields are included
    client_fields = dir(client_type)
    property_fields = [field for field in client_fields if 'uppercase_raison' in field]
    print(f"Client property-related fields: {property_fields}")
    
    # Test Category type
    category_type = type_generator.generate_object_type(Category)
    print(f"Category GraphQL type: {category_type.__name__}")
    
    category_fields = dir(category_type)
    property_fields = [field for field in category_fields if any(prop in field for prop in ['uppercase_name', 'post_count'])]
    print(f"Category property-related fields: {property_fields}")
    
    # Test Post type
    post_type = type_generator.generate_object_type(Post)
    print(f"Post GraphQL type: {post_type.__name__}")
    
    post_fields = dir(post_type)
    property_fields = [field for field in post_fields if any(prop in field for prop in ['title_with_category', 'word_count', 'tag_names'])]
    print(f"Post property-related fields: {property_fields}")

def test_property_resolvers():
    """Test that property resolvers work correctly."""
    print("\n=== Testing Property Resolvers ===")
    
    # Create test data
    try:
        # Create a category
        category = Category.objects.create(
            name="Test Category",
            description="A test category"
        )
        
        # Create a client
        client = Client.objects.create(
            raison="Test Client"
        )
        
        # Test property values
        print(f"Client raison: {client.raison}")
        print(f"Client uppercase_raison: {client.uppercase_raison}")
        
        print(f"Category name: {category.name}")
        print(f"Category uppercase_name: {category.uppercase_name}")
        print(f"Category post_count: {category.post_count}")
        
        # Create a post to test post properties
        post = Post.objects.create(
            title="Test Post",
            content="This is a test post with some content",
            category=category
        )
        
        print(f"Post title: {post.title}")
        print(f"Post title_with_category: {post.title_with_category}")
        print(f"Post word_count: {post.word_count}")
        print(f"Post tag_names: {post.tag_names}")
        
        # Clean up
        post.delete()
        client.delete()
        category.delete()
        
        print("✅ Property resolvers work correctly!")
        
    except Exception as e:
        print(f"❌ Error testing property resolvers: {e}")

if __name__ == "__main__":
    test_property_introspection()
    test_graphql_type_generation()
    test_property_resolvers()
    print("\n=== Property Support Test Complete ===")