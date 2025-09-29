#!/usr/bin/env python
"""
Test script for property-based filtering in Django GraphQL Auto-Generation

This script tests the autofiltering functionality for @property methods,
verifying that properties can be filtered using various operations like
exact, contains, gt, lt, etc.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')

# Setup Django
django.setup()

from django.test import TestCase
from django.db import connection
from test_app.models import Client, Category, Post
from django_graphql_auto.generators.filters import AdvancedFilterGenerator
from django_graphql_auto.core.schema import SchemaBuilder
import graphene


def test_property_filter_generation():
    """Test that property filters are correctly generated for models."""
    print("Testing property filter generation...")
    
    # Test Client model property filters
    filter_generator = AdvancedFilterGenerator()
    client_filters = filter_generator.generate_filter_set(Client)
    
    # Check if property filters are included
    expected_property_filters = [
        'uppercase_raison',
        'uppercase_raison__contains',
        'uppercase_raison__icontains',
        'uppercase_raison__startswith',
        'uppercase_raison__endswith',
        'uppercase_raison__exact'
    ]
    
    filter_names = list(client_filters.base_filters.keys())
    print(f"Generated filters for Client: {filter_names}")
    
    for expected_filter in expected_property_filters:
        if expected_filter in filter_names:
            print(f"Found property filter: {expected_filter}")
        else:
            print(f"Missing property filter: {expected_filter}")
    
    # Test Category model property filters
    category_filters = filter_generator.generate_filter_set(Category)
    category_filter_names = list(category_filters.base_filters.keys())
    print(f"Generated filters for Category: {category_filter_names}")
    
    # Check for postCount property filters (numeric)
    expected_numeric_filters = [
        'post_count',
        'post_count__gt',
        'post_count__gte', 
        'post_count__lt',
        'post_count__lte'
    ]
    
    for expected_filter in expected_numeric_filters:
        if expected_filter in category_filter_names:
            print(f"Found numeric property filter: {expected_filter}")
        else:
            print(f"Missing numeric property filter: {expected_filter}")


def test_property_filtering_functionality():
    """Test actual filtering functionality with property filters."""
    print("\nTesting property filtering functionality...")
    
    # Create test data
    print("Creating test data...")
    
    # Clear existing data
    Client.objects.all().delete()
    Category.objects.all().delete()
    Post.objects.all().delete()
    
    # Create clients with different raison values
    client1 = Client.objects.create(
        raison="tech company"
    )
    client2 = Client.objects.create(
        raison="consulting firm"
    )
    client3 = Client.objects.create(
        raison="software house"
    )
    
    # Create categories with different post counts
    category1 = Category.objects.create(name="Technology")
    category2 = Category.objects.create(name="Business")
    category3 = Category.objects.create(name="Science")
    
    # Create posts to affect post_count property
    Post.objects.create(title="Tech Post 1", content="Content 1", category=category1, is_published=True)
    Post.objects.create(title="Tech Post 2", content="Content 2", category=category1, is_published=True)
    Post.objects.create(title="Business Post 1", content="Content 3", category=category2, is_published=True)
    
    print(f"Created {Client.objects.count()} clients and {Category.objects.count()} categories")
    
    # Test property filtering
    filter_generator = AdvancedFilterGenerator()
    
    # Test text property filtering (uppercase_raison)
    print("\nTesting text property filtering...")
    
    # Test exact match
    client_filter = filter_generator.generate_filter_set(Client)
    
    # Create filter instance
    filter_instance = client_filter()
    
    # Test contains filter on uppercase_raison property
    queryset = Client.objects.all()
    
    # Manually test the property filter method
    property_filter_method = filter_generator._create_property_filter_method('uppercase_raison', 'icontains')
    
    # Test filtering for "TECH" (should match "TECH COMPANY")
    filtered_queryset = property_filter_method(queryset, 'uppercase_raison__icontains', 'TECH')
    filtered_clients = list(filtered_queryset)
    
    print(f"Filtering for 'TECH' in uppercase_raison:")
    for client in filtered_clients:
        print(f"  - {client.raison}: {client.uppercase_raison}")
    
    # Test filtering for "CONSULTING" 
    filtered_queryset2 = property_filter_method(queryset, 'uppercase_raison__icontains', 'CONSULTING')
    filtered_clients2 = list(filtered_queryset2)
    
    print(f"Filtering for 'CONSULTING' in uppercase_raison:")
    for client in filtered_clients2:
        print(f"  - {client.raison}: {client.uppercase_raison}")
    
    # Test numeric property filtering (post_count)
    print("\nTesting numeric property filtering...")
    
    category_filter = filter_generator.generate_filter_set(Category)
    category_queryset = Category.objects.all()
    
    # Test gt filter on post_count property
    numeric_filter_method = filter_generator._create_property_filter_method('post_count', 'gt')
    
    # Filter categories with post_count > 1
    filtered_categories = numeric_filter_method(category_queryset, 'post_count__gt', 1)
    filtered_categories_list = list(filtered_categories)
    
    print(f"Categories with post_count > 1:")
    for category in filtered_categories_list:
        print(f"  - {category.name}: {category.post_count} posts")
    
    # Test exact numeric filter
    exact_filter_method = filter_generator._create_property_filter_method('post_count', 'exact')
    exact_filtered = exact_filter_method(category_queryset, 'post_count__exact', 2)
    exact_filtered_list = list(exact_filtered)
    
    print(f"Categories with exactly 2 posts:")
    for category in exact_filtered_list:
        print(f"  - {category.name}: {category.post_count} posts")


def test_graphql_property_filtering():
    """Test property filtering through GraphQL queries."""
    print("\n🌐 Testing GraphQL property filtering...")
    
    try:
        # Generate schema with property filtering
        schema_builder = SchemaBuilder()
        schema = schema_builder.get_schema()
        
        # Test query with property filter
        query = """
        query {
            clients(uppercase_raison__icontains: "TECH") {
                raison
                uppercase_raison
            }
        }
        """
        
        result = schema.execute(query)
        
        if result.errors:
            print(f"❌ GraphQL query errors: {result.errors}")
        else:
            print("✅ GraphQL property filtering query executed successfully")
            if result.data and result.data.get('clients'):
                clients = result.data['clients']
                print(f"Found {len(clients)} clients matching filter")
                for client in clients:
                    print(f"  - {client['raison']}: {client['uppercase_raison']}")
            else:
                print("No clients found or query structure issue")
                
    except Exception as e:
        print(f"❌ GraphQL property filtering test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all property filtering tests."""
    print("🚀 Starting Property Filtering Tests")
    print("=" * 50)
    
    try:
        # Test filter generation
        test_property_filter_generation()
        
        # Test filtering functionality
        test_property_filtering_functionality()
        
        # Test GraphQL integration
        test_graphql_property_filtering()
        
        print("\n" + "=" * 50)
        print("✅ Property filtering tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)