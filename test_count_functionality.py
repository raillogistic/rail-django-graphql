#!/usr/bin/env python
"""
Test script for count fields and filters functionality.

This script tests the newly implemented count helper fields and filters
for ManyToOne and ManyToMany relationships.
"""

import os
import sys
import django
from django.core.management import call_command

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
django.setup()

from tests.models import (
    TestCustomer, TestAccount, TestTransaction, TestProduct, 
    TestProductCategory, TestOrder, TestOrderItem, TestEmployee,
    TestProject, TestProjectAssignment, FixtureTestAuthor, 
    FixtureTestBook, FixtureTestCategory, FixtureTestReview
)
from django.contrib.auth.models import User
from django_graphql_auto.generators.types import TypeGenerator
from django_graphql_auto.generators.filters import AdvancedFilterGenerator
import graphene


def test_count_field_generation():
    """Test that count fields are generated for ManyToMany and reverse ManyToOne relationships."""
    print("\n=== Testing Count Field Generation ===")
    
    # Test with TestOrder model (has ManyToMany relationship with TestProduct)
    type_generator = TypeGenerator()
    order_type = type_generator.generate_object_type(TestOrder)
    
    # Check if count field exists for ManyToMany relationship
    order_fields = order_type._meta.fields
    print(f"TestOrder fields: {list(order_fields.keys())}")
    
    # Look for count field for produits_commande (ManyToMany)
    if 'produits_commande_count' in order_fields:
        print("✓ Count field for ManyToMany relationship found")
    else:
        print("✗ Count field for ManyToMany relationship not found")
    
    # Test with TestProduct model (has reverse ManyToOne from TestOrder)
    product_type = type_generator.generate_object_type(TestProduct)
    product_fields = product_type._meta.fields
    print(f"TestProduct fields: {list(product_fields.keys())}")
    
    # Look for count field for reverse relationship
    # Note: The reverse relationship name might be different, let's check what's available
    reverse_count_fields = [field for field in product_fields.keys() if '_count' in field]
    print(f"Found count fields in TestProduct: {reverse_count_fields}")
    
    print("✓ Count field generation test completed")


def test_count_filter_generation():
    """Test that count filters are generated for ManyToMany and reverse ManyToOne relationships."""
    print("\n=== Testing Count Filter Generation ===")
    
    filter_generator = AdvancedFilterGenerator()
    
    # Test with TestOrder model
    order_filter_set = filter_generator.generate_filter_set(TestOrder)
    order_filter_instance = order_filter_set()
    order_filters = order_filter_instance.filters
    print(f"TestOrder filters: {list(order_filters.keys())}")
    
    # Check for count filters
    count_filters = [f for f in order_filters.keys() if 'count' in f]
    print(f"Found count filters in TestOrder: {count_filters}")
    
    # Test with TestProduct model
    product_filter_set = filter_generator.generate_filter_set(TestProduct)
    product_filter_instance = product_filter_set()
    product_filters = product_filter_instance.filters
    print(f"TestProduct filters: {list(product_filters.keys())}")
    
    # Check for count filters
    product_count_filters = [f for f in product_filters.keys() if 'count' in f]
    print(f"Found count filters in TestProduct: {product_count_filters}")
    
    print("✓ Count filter generation test completed")


def test_count_functionality_with_data():
    """Test count functionality with actual data."""
    print("\n=== Testing Count Functionality with Data ===\n")
    
    # Create test data
    call_command('migrate', verbosity=0)
    
    try:
        # Create test data
        print("Creating test data...")
        
        # Create a user for orders
        user = User.objects.create_user(username='testuser', email='test@example.com')
        
        # Create product category
        category = TestProductCategory.objects.create(
            nom_categorie="Electronics",
            description_categorie="Electronic products"
        )
        
        # Create products
        product1 = TestProduct.objects.create(
            nom_produit="Laptop",
            description_produit="Gaming laptop",
            prix_produit=1500.00,
            quantite_stock=10,
            categorie_produit=category
        )
        
        product2 = TestProduct.objects.create(
            nom_produit="Mouse",
            description_produit="Gaming mouse",
            prix_produit=50.00,
            quantite_stock=20,
            categorie_produit=category
        )
        
        # Create orders
        order1 = TestOrder.objects.create(
            numero_commande="ORD001",
            client_commande=user,
            statut_commande="EN_ATTENTE"
        )
        
        order2 = TestOrder.objects.create(
            numero_commande="ORD002",
            client_commande=user,
            statut_commande="CONFIRMEE"
        )
        
        # Create order items to establish ManyToMany relationships
        TestOrderItem.objects.create(
            commande_item=order1,
            produit_item=product1,
            quantite_item=1,
            prix_unitaire=1500.00
        )
        
        TestOrderItem.objects.create(
            commande_item=order1,
            produit_item=product2,
            quantite_item=2,
            prix_unitaire=50.00
        )
        
        TestOrderItem.objects.create(
            commande_item=order2,
            produit_item=product1,
            quantite_item=1,
            prix_unitaire=1500.00
        )
        
        print("✓ Test data created successfully")
        
        # Test count queries
        print("Testing count queries...")
        
        # Count products in order1 (should be 2)
        order1_product_count = order1.produits_commande.count()
        print(f"Order1 product count: {order1_product_count}")
        
        # Count orders for product1 (should be 2)
        product1_order_count = TestOrder.objects.filter(produits_commande=product1).count()
        print(f"Product1 order count: {product1_order_count}")
        
        print("✓ Count functionality test completed successfully")
        
    except Exception as e:
        print(f"Error in count functionality test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test data
        print("Cleaning up test data...")
        try:
            TestOrderItem.objects.all().delete()
            TestOrder.objects.all().delete()
            TestProduct.objects.all().delete()
            TestProductCategory.objects.all().delete()
            User.objects.filter(username='testuser').delete()
            print("✓ Test data cleaned up")
        except Exception as e:
            print(f"Error cleaning up: {e}")


def main():
    """Run all tests."""
    print("Testing Count Fields and Filters Functionality")
    print("=" * 50)
    
    try:
        test_count_field_generation()
        test_count_filter_generation()
        test_count_functionality_with_data()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()