#!/usr/bin/env python
"""
Test GraphQL queries with @property methods.
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
django.setup()

import graphene
from test_app.models import Client, Category
from django_graphql_auto.core.schema import SchemaBuilder

def test_graphql_property_queries():
    """Test GraphQL queries that include @property fields."""
    print("=== Testing GraphQL Property Queries ===")
    
    try:
        # Create test data
        category = Category.objects.create(
            name="Technology",
            description="Technology related posts"
        )
        
        client = Client.objects.create(
            raison="Acme Corporation"
        )
        
        # Generate GraphQL schema
        schema_builder = SchemaBuilder()
        schema = schema_builder.get_schema()
        
        # Test Client query with property
        client_query = """
        query {
            clients {
                id
                raison
                uppercaseRaison
            }
        }
        """
        
        print("Executing Client query with property...")
        client_result = schema.execute(client_query)
        if client_result.errors:
            print(f"Client query errors: {client_result.errors}")
        else:
            print(f"Client query result: {client_result.data}")
        
        # Test Category query with properties
        category_query = """
        query {
            categories {
                id
                name
                uppercaseName
                postCount
            }
        }
        """
        
        print("\nExecuting Category query with properties...")
        category_result = schema.execute(category_query)
        if category_result.errors:
            print(f"Category query errors: {category_result.errors}")
        else:
            print(f"Category query result: {category_result.data}")
        
        # Clean up
        client.delete()
        category.delete()
        
        print("\n✅ GraphQL property queries test complete!")
        
    except Exception as e:
        print(f"❌ Error testing GraphQL property queries: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_graphql_property_queries()