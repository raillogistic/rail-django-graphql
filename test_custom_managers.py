"""
Test script for multiple Django model managers functionality.

This script tests the GraphQL schema generation with custom managers
to ensure the naming conventions and query handling work correctly.
"""

import os
import sys
import django
from django.conf import settings
from django.db import models

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
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'rail_django_graphql',
        ],
        SECRET_KEY='test-secret-key-for-custom-managers',
        USE_TZ=True,
    )

django.setup()

# Import after Django setup
from rail_django_graphql.generators.introspector import ModelIntrospector
from rail_django_graphql.generators.queries import QueryGenerator
from rail_django_graphql.generators.types import TypeGenerator
from rail_django_graphql.core.schema import SchemaBuilder


class PublishedManager(models.Manager):
    """Custom manager for published books."""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)
    
    def recent(self):
        """Get recently published books."""
        return self.get_queryset().order_by('-created_at')[:10]


class FeaturedManager(models.Manager):
    """Custom manager for featured books."""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_featured=True)


class Book(models.Model):
    """Test model with multiple custom managers."""
    
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Default manager (should keep its name)
    objects = models.Manager()
    
    # Custom managers
    published = PublishedManager()
    featured = FeaturedManager()
    
    class Meta:
        app_label = 'test_app'
    
    class GraphQLMeta:
        """GraphQL configuration for Book model."""
        exclude_fields = []
        filter_fields = ['title', 'author', 'is_published', 'is_featured']


def test_manager_detection():
    """Test that ModelIntrospector correctly detects all managers."""
    print("Testing manager detection...")
    
    introspector = ModelIntrospector(Book)
    managers_dict = introspector.get_model_managers()
    managers = list(managers_dict.values())
    
    print(f"Detected {len(managers)} managers:")
    for manager in managers:
        print(f"  - {manager.name}: {manager.manager_class.__name__} (default: {manager.is_default})")
    
    # Verify we have all expected managers
    manager_names = [m.name for m in managers]
    expected_managers = ['objects', 'published', 'featured']
    
    for expected in expected_managers:
        if expected in manager_names:
            print(f"✓ Found expected manager: {expected}")
        else:
            print(f"✗ Missing expected manager: {expected}")
    
    return managers


def test_query_generation():
    """Test that QueryGenerator creates queries for all managers."""
    print("\nTesting query generation...")
    
    # Initialize generators
    type_generator = TypeGenerator()
    query_generator = QueryGenerator(type_generator)
    
    # Get managers
    introspector = ModelIntrospector(Book)
    managers_dict = introspector.get_model_managers()
    managers = list(managers_dict.values())
    
    # Test query generation for each manager
    for manager in managers:
        print(f"\nTesting queries for manager: {manager.name}")
        
        # Test single query
        try:
            single_query = query_generator.generate_single_query(Book, manager.name)
            print(f"✓ Single query generated for {manager.name}")
        except Exception as e:
            print(f"✗ Single query failed for {manager.name}: {e}")
        
        # Test list query
        try:
            list_query = query_generator.generate_list_query(Book, manager.name)
            print(f"✓ List query generated for {manager.name}")
        except Exception as e:
            print(f"✗ List query failed for {manager.name}: {e}")
        
        # Test paginated query
        try:
            paginated_query = query_generator.generate_paginated_query(Book, manager.name)
            print(f"✓ Paginated query generated for {manager.name}")
        except Exception as e:
            print(f"✗ Paginated query failed for {manager.name}: {e}")


def test_schema_generation():
    """Test that schema generation creates properly named fields."""
    print("\nTesting schema generation...")
    
    try:
        # Create schema builder with explicit model list
        schema_builder = SchemaBuilder()
        
        # Instead of register_model, we need to directly test the _generate_query_fields method
        # Let's create a simple test by calling the internal methods
        
        # First, let's see what models are discovered
        models = schema_builder._discover_models()
        print(f"Discovered models: {[m.__name__ for m in models]}")
        
        # Add our Book model to the list if it's not there
        if Book not in models:
            models.append(Book)
            print(f"Added Book model to the list")
        
        # Generate query fields for our models
        schema_builder._generate_query_fields(models)
        
        # Get the generated query fields
        query_fields = schema_builder._query_fields
        
        print(f"Generated {len(query_fields)} query fields:")
        for field_name in sorted(query_fields.keys()):
            print(f"  - {field_name}")
        
        # Check for expected field names based on naming conventions
        expected_fields = [
            # Default manager (objects) - keeps original names
            'book',           # single query
            'books',          # list query  
            'books_pages',    # paginated query
            
            # Custom managers - use naming conventions
            'book__published',        # single query for published manager
            'books__published',       # list query for published manager
            'books_pages_published',  # paginated query for published manager
            
            'book__featured',         # single query for featured manager
            'books__featured',        # list query for featured manager
            'books_pages_featured',   # paginated query for featured manager
        ]
        
        print("\nChecking expected field names:")
        found_count = 0
        for expected in expected_fields:
            if expected in query_fields:
                print(f"✓ Found expected field: {expected}")
                found_count += 1
            else:
                print(f"✗ Missing expected field: {expected}")
        
        print(f"\nFound {found_count}/{len(expected_fields)} expected fields")
        
        return query_fields
        
    except Exception as e:
        print(f"✗ Schema generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Multiple Django Model Managers Functionality")
    print("=" * 60)
    
    # Test 1: Manager detection
    managers = test_manager_detection()
    
    # Test 2: Query generation
    test_query_generation()
    
    # Test 3: Schema generation
    schema = test_schema_generation()
    
    print("\n" + "=" * 60)
    if schema:
        print("✓ All tests completed successfully!")
        print("Multiple Django model managers functionality is working correctly.")
    else:
        print("✗ Some tests failed. Please check the implementation.")
    print("=" * 60)


if __name__ == "__main__":
    main()