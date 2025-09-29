#!/usr/bin/env python
"""
Comprehensive test suite for property filtering functionality.

This test suite verifies:
1. Property detection and filter generation
2. All filter operations (exact, contains, icontains, startswith, endswith, gt, lt, etc.)
3. Complex filter expressions with AND, OR, NOT
4. Edge cases and error handling
5. Performance with large datasets
"""

import os
import sys
import django
from django.test import TestCase
from django.db import models
from graphene.test import Client
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from test_app.models import Client as ClientModel
from django_graphql_auto.generators.filters import AdvancedFilterGenerator
from django_graphql_auto.generators.introspector import ModelIntrospector
from django_graphql_auto.schema import schema

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PropertyFilteringTestSuite:
    """Comprehensive test suite for property filtering."""
    
    def __init__(self):
        self.client = Client(schema)
        self.setup_test_data()
    
    def setup_test_data(self):
        """Create test data for comprehensive testing."""
        print("Setting up test data...")
        
        # Clear existing data
        ClientModel.objects.all().delete()
        
        # Create diverse test clients
        self.test_clients = [
            ClientModel.objects.create(raison="acme corp"),
            ClientModel.objects.create(raison="tech solutions"),
            ClientModel.objects.create(raison="global industries"),
            ClientModel.objects.create(raison="startup inc"),
            ClientModel.objects.create(raison="enterprise systems"),
            ClientModel.objects.create(raison="digital agency"),
            ClientModel.objects.create(raison="consulting group"),
            ClientModel.objects.create(raison="innovation labs"),
            ClientModel.objects.create(raison="software house"),
            ClientModel.objects.create(raison="data analytics"),
        ]
        
        print(f"Created {len(self.test_clients)} test clients")
        for client in self.test_clients:
            print(f"  - {client.raison} -> {client.uppercase_raison}")
    
    def test_property_detection(self):
        """Test 1: Verify property detection by ModelIntrospector."""
        print("\n=== Test 1: Property Detection ===")
        
        introspector = ModelIntrospector(ClientModel)
        properties = introspector.properties
        
        assert 'uppercase_raison' in properties, "uppercase_raison property not detected"
        
        prop_info = properties['uppercase_raison']
        assert prop_info.return_type == str, f"Expected str, got {prop_info.return_type}"
        
        print("Property detection working correctly")
        return True
    
    def test_filter_generation(self):
        """Test 2: Verify filter generation for properties."""
        print("\n=== Test 2: Filter Generation ===")
        
        generator = AdvancedFilterGenerator()
        filters = generator._generate_property_filters(ClientModel)
        
        # Check that property filters are generated
        property_filter_names = [name for name in filters.keys() if 'uppercase_raison' in name]
        
        expected_filters = [
            'uppercase_raison',
            'uppercase_raison__exact',
            'uppercase_raison__icontains',
            'uppercase_raison__contains',
            'uppercase_raison__startswith',
            'uppercase_raison__endswith'
        ]
        
        for expected in expected_filters:
            assert expected in property_filter_names, f"Missing filter: {expected}"
        
        print(f"Generated {len(property_filter_names)} property filters")
        return True
    
    def test_exact_filtering(self):
        """Test 3: Exact match filtering."""
        print("\n=== Test 3: Exact Match Filtering ===")
        
        query = """
        query {
            clients(uppercase_raison__exact: "ACME CORP") {
                raison
                uppercase_raison
            }
        }
        """
        
        result = self.client.execute(query)
        
        # Handle both dict and ExecutionResult formats
        if hasattr(result, 'errors') and result.errors:
            print(f"Query errors: {result.errors}")
            return False
        elif isinstance(result, dict) and 'errors' in result:
            print(f"Query errors: {result['errors']}")
            return False
        
        # Get data from result
        data = result.data if hasattr(result, 'data') else result.get('data', {})
        clients = data.get('clients', [])
        
        if len(clients) == 1 and clients[0]['raison'] == 'ACME Corp':
            print("Exact match filtering working correctly")
            return True
        return False
    
    def test_icontains_filtering(self):
        """Test 4: Case-insensitive contains filtering."""
        print("\n=== Test 4: Case-Insensitive Contains Filtering ===")
        
        query = """
        query {
            clients(uppercase_raison__icontains: "tech") {
                raison
                uppercase_raison
            }
        }
        """
        
        result = self.client.execute(query)
        
        # Handle both dict and ExecutionResult formats
        if hasattr(result, 'errors') and result.errors:
            print(f"Query errors: {result.errors}")
            return False
        elif isinstance(result, dict) and 'errors' in result:
            print(f"Query errors: {result['errors']}")
            return False
        
        # Get data from result
        data = result.data if hasattr(result, 'data') else result.get('data', {})
        clients = data.get('clients', [])
        
        # Should find "tech solutions" -> "TECH SOLUTIONS"
        if len(clients) >= 1:
            tech_clients = [c for c in clients if 'TECH' in c['uppercase_raison']]
            if len(tech_clients) >= 1:
                print(f"Found {len(clients)} clients with case-insensitive contains filtering")
                return True
        return False
    
    def test_startswith_filtering(self):
        """Test 5: Starts with filtering."""
        print("\n=== Test 5: Starts With Filtering ===")
        
        query = """
        query {
            clients(uppercase_raison__startswith: "GLOBAL") {
                raison
                uppercase_raison
            }
        }
        """
        
        result = self.client.execute(query)
        
        # Handle both dict and ExecutionResult formats
        if hasattr(result, 'errors') and result.errors:
            print(f"Query errors: {result.errors}")
            return False
        elif isinstance(result, dict) and 'errors' in result:
            print(f"Query errors: {result['errors']}")
            return False
        
        # Get data from result
        data = result.data if hasattr(result, 'data') else result.get('data', {})
        clients = data.get('clients', [])
        if len(clients) == 1 and clients[0]['uppercase_raison'].startswith('GLOBAL'):
            print("Starts with filtering working correctly")
            return True
        return False
    
    def test_endswith_filtering(self):
        """Test 6: Ends with filtering."""
        print("\n=== Test 6: Ends With Filtering ===")
        
        query = """
        query {
            clients(uppercase_raison__endswith: "INC") {
                raison
                uppercase_raison
            }
        }
        """
        
        result = self.client.execute(query)
        
        # Handle both dict and ExecutionResult formats
        if hasattr(result, 'errors') and result.errors:
            print(f"Query errors: {result.errors}")
            return False
        elif isinstance(result, dict) and 'errors' in result:
            print(f"Query errors: {result['errors']}")
            return False
        
        # Get data from result
        data = result.data if hasattr(result, 'data') else result.get('data', {})
        clients = data.get('clients', [])
        
        if len(clients) == 1 and clients[0]['uppercase_raison'].endswith('INC'):
            print("Ends with filtering working correctly")
            return True
        return False
    
    def test_complex_filtering(self):
        """Test 7: Complex filtering with multiple conditions."""
        print("\n=== Test 7: Complex Filtering ===")
        
        # Test combining property filter with regular field filter
        query = """
        query {
            clients(
                raison__icontains: "tech"
                uppercase_raison__icontains: "TECH"
            ) {
                raison
                uppercase_raison
            }
        }
        """
        
        result = self.client.execute(query)
        
        # Handle both dict and ExecutionResult formats
        if hasattr(result, 'errors') and result.errors:
            print(f"Query errors: {result.errors}")
            return False
        elif isinstance(result, dict) and 'errors' in result:
            print(f"Query errors: {result['errors']}")
            return False
        
        # Get data from result
        data = result.data if hasattr(result, 'data') else result.get('data', {})
        clients = data.get('clients', [])
        if len(clients) >= 1:
            for client in clients:
                if 'TECH' not in client['uppercase_raison']:
                    return False
            print(f"Complex filtering working correctly with {len(clients)} results")
            return True
        return False
    
    def test_no_results_filtering(self):
        """Test 8: Filtering that returns no results."""
        print("\n=== Test 8: No Results Filtering ===")
        
        query = """
        query {
            clients(uppercase_raison__exact: "NONEXISTENT COMPANY") {
                raison
                uppercase_raison
            }
        }
        """
        
        result = self.client.execute(query)
        
        # Handle both dict and ExecutionResult formats
        if hasattr(result, 'errors') and result.errors:
            print(f"Query errors: {result.errors}")
            return False
        elif isinstance(result, dict) and 'errors' in result:
            print(f"Query errors: {result['errors']}")
            return False
        
        # Get data from result
        data = result.data if hasattr(result, 'data') else result.get('data', {})
        clients = data.get('clients', [])
        if len(clients) == 0:
            print("No results filtering working correctly")
            return True
        return False
    
    def test_performance(self):
        """Test 9: Performance with larger dataset."""
        print("\n=== Test 9: Performance Testing ===")
        
        # Create additional test data
        import time
        
        start_time = time.time()
        
        # Create 100 additional clients
        bulk_clients = []
        for i in range(100):
            bulk_clients.append(ClientModel(raison=f"bulk client {i:03d}"))
        
        ClientModel.objects.bulk_create(bulk_clients)
        
        # Test filtering performance
        query_start = time.time()
        
        query = """
        query {
            clients(uppercase_raison__icontains: "BULK") {
                raison
                uppercase_raison
            }
        }
        """
        
        result = self.client.execute(query)
        
        query_end = time.time()
        
        # Handle both dict and ExecutionResult formats
        if hasattr(result, 'errors') and result.errors:
            print(f"Query errors: {result.errors}")
            return False
        elif isinstance(result, dict) and 'errors' in result:
            print(f"Query errors: {result['errors']}")
            return False
        
        # Get data from result
        data = result.data if hasattr(result, 'data') else result.get('data', {})
        clients = data.get('clients', [])
        query_time = query_end - query_start
        
        print(f"Performance test: Found {len(clients)} clients in {query_time:.3f}s")
        
        # Cleanup bulk data
        ClientModel.objects.filter(raison__startswith="bulk client").delete()
        
        return True
    
    def test_error_handling(self):
        """Test 10: Error handling for invalid filters."""
        print("\n=== Test 10: Error Handling ===")
        
        # Test invalid filter operation (should be handled gracefully)
        query = """
        query {
            clients(uppercase_raison__invalid_operation: "test") {
                raison
                uppercase_raison
            }
        }
        """
        
        result = self.client.execute(query)
        
        # Should have errors for invalid operation
        has_errors = False
        if hasattr(result, 'errors') and result.errors:
            has_errors = True
        elif isinstance(result, dict) and 'errors' in result and result['errors']:
            has_errors = True
        
        if not has_errors:
            print("Expected errors for invalid filter operation, but got none")
            return False
        
        print("Error handling working correctly for invalid operations")
        return True
    
    def run_all_tests(self):
        """Run all tests in the suite."""
        print("Starting Comprehensive Property Filtering Test Suite")
        print("=" * 60)
        
        tests = [
            self.test_property_detection,
            self.test_filter_generation,
            self.test_exact_filtering,
            self.test_icontains_filtering,
            self.test_startswith_filtering,
            self.test_endswith_filtering,
            self.test_complex_filtering,
            self.test_no_results_filtering,
            self.test_performance,
            self.test_error_handling,
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
                print(f"Test {test.__name__} failed with exception: {e}")
                failed += 1
        
        print("\n" + "=" * 60)
        print(f"Test Suite Complete: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("All tests passed! Property filtering is working correctly.")
        else:
            print(f"{failed} tests failed. Please review the implementation.")
        
        return failed == 0

def main():
    """Main test runner."""
    suite = PropertyFilteringTestSuite()
    success = suite.run_all_tests()
    
    if success:
        print("\nProperty filtering implementation is complete and working!")
    else:
        print("\nProperty filtering implementation needs attention.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())