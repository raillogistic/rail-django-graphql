"""
Comprehensive test cases for nested field filtering functionality.

This module tests the AdvancedFilterGenerator's nested filtering capabilities,
including depth control, performance optimizations, and edge cases.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.db import models
from django_filters import FilterSet
from django_graphql_auto.generators.filters import AdvancedFilterGenerator
from django_graphql_auto.core.schema import SchemaBuilder
from django_graphql_auto.generators.types import TypeGenerator
from django_graphql_auto.generators.mutations import MutationGenerator
from django_graphql_auto.generators.queries import QueryGenerator
from django_graphql_auto.generators.introspector import ModelIntrospector
from test_app.models import Category, Tag, Product, Brand, Country


# Test Models for Nested Filtering - Additional models not in test_app


class Customer(models.Model):
    """Test model representing a customer."""
    username = models.CharField(max_length=50, unique=True, verbose_name="Nom d'utilisateur")
    email = models.EmailField(verbose_name="Email")
    first_name = models.CharField(max_length=50, verbose_name="Prénom")
    last_name = models.CharField(max_length=50, verbose_name="Nom de famille")
    
    class Meta:
        app_label = 'test_app'


class Order(models.Model):
    """Test model representing an order."""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, verbose_name="Client")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant total")
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Date de commande")
    is_completed = models.BooleanField(default=False, verbose_name="Terminé")
    
    class Meta:
        app_label = 'test_app'


class OrderItem(models.Model):
    """Test model representing an order item."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="Commande")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Produit")
    quantity = models.IntegerField(verbose_name="Quantité")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire")
    
    class Meta:
        app_label = 'test_app'


class TestNestedFieldFiltering(TestCase):
    """Test cases for nested field filtering functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = AdvancedFilterGenerator(
            max_nested_depth=3,
            enable_nested_filters=True
        )
    
    def test_generator_initialization(self):
        """Test AdvancedFilterGenerator initialization with nested filtering parameters."""
        # Test default initialization
        default_generator = AdvancedFilterGenerator()
        self.assertEqual(default_generator.max_nested_depth, 3)
        self.assertTrue(default_generator.enable_nested_filters)
        self.assertEqual(default_generator._visited_models, set())
        
        # Test custom initialization
        custom_generator = AdvancedFilterGenerator(
            max_nested_depth=2,
            enable_nested_filters=False
        )
        self.assertEqual(custom_generator.max_nested_depth, 2)
        self.assertFalse(custom_generator.enable_nested_filters)
    
    def test_depth_validation(self):
        """Test depth validation in generator initialization."""
        # Test valid depth
        generator = AdvancedFilterGenerator(max_nested_depth=3)
        self.assertEqual(generator.max_nested_depth, 3)
        
        # Test maximum allowed depth
        generator = AdvancedFilterGenerator(max_nested_depth=5)
        self.assertEqual(generator.max_nested_depth, 5)
        
        # Test depth exceeding maximum (should be clamped)
        generator = AdvancedFilterGenerator(max_nested_depth=10)
        self.assertEqual(generator.max_nested_depth, 5)  # Should be clamped to MAX_ALLOWED_NESTED_DEPTH
    
    @patch('django_graphql_auto.generators.filters.logger')
    def test_generate_filter_set_basic(self, mock_logger):
        """Test basic filter set generation without nested filtering."""
        filter_set = self.generator.generate_filter_set(Product)
        
        # Verify FilterSet is created
        self.assertTrue(issubclass(filter_set, FilterSet))
        
        # Verify basic filters are present
        filter_instance = filter_set()
        self.assertIn('name', filter_instance.filters)
        self.assertIn('price', filter_instance.filters)
        self.assertIn('is_active', filter_instance.filters)
        
        # Verify logging
        mock_logger.debug.assert_called()
    
    @patch('django_graphql_auto.generators.filters.logger')
    def test_generate_filter_set_with_nested_filters(self, mock_logger):
        """Test filter set generation with nested filtering enabled."""
        filter_set = self.generator.generate_filter_set(Product, current_depth=0)
        
        # Verify FilterSet is created
        self.assertTrue(issubclass(filter_set, FilterSet))
        
        # Create filter instance to check available filters
        filter_instance = filter_set()
        
        # Verify nested filters are present
        nested_filters = [f for f in filter_instance.filters.keys() if '__' in f]
        self.assertTrue(len(nested_filters) > 0)
        
        # Check for specific nested filters
        expected_nested_filters = [
            'category__name',
            'category__description',
            'brand__name',
            'brand__country__name',
            'brand__country__code'
        ]
        
        for expected_filter in expected_nested_filters:
            self.assertIn(expected_filter, filter_instance.filters)
    
    def test_depth_control_mechanism(self):
        """Test that depth control prevents infinite recursion."""
        # Test with depth 1 - should only include direct relationships
        generator_depth_1 = AdvancedFilterGenerator(max_nested_depth=1)
        filter_set = generator_depth_1.generate_filter_set(Product, current_depth=0)
        filter_instance = filter_set()
        
        # Should have category and brand filters but not nested ones
        self.assertIn('category__name', filter_instance.filters)
        self.assertIn('brand__name', filter_instance.filters)
        
        # Should NOT have deeply nested filters
        self.assertNotIn('brand__country__name', filter_instance.filters)
        
        # Test with depth 2 - should include one level of nesting
        generator_depth_2 = AdvancedFilterGenerator(max_nested_depth=2)
        filter_set = generator_depth_2.generate_filter_set(Product, current_depth=0)
        filter_instance = filter_set()
        
        # Should have nested filters
        self.assertIn('brand__country__name', filter_instance.filters)
    
    def test_circular_reference_prevention(self):
        """Test prevention of circular references in nested filtering."""
        # Create a mock model with circular reference
        with patch.object(self.generator, '_visited_models', set()) as mock_visited:
            # Simulate circular reference detection
            mock_visited.add(Product)
            
            # This should not cause infinite recursion
            filter_set = self.generator.generate_filter_set(Product, current_depth=0)
            self.assertTrue(issubclass(filter_set, FilterSet))
    
    def test_nested_text_filters(self):
        """Test generation of nested text filters."""
        filters = self.generator._generate_nested_text_filters('category__name', 'category')
        
        # Verify text filter types are generated
        expected_filters = [
            'category__name__exact',
            'category__name__icontains',
            'category__name__istartswith',
            'category__name__iendswith'
        ]
        
        for expected_filter in expected_filters:
            self.assertIn(expected_filter, filters)
    
    def test_nested_numeric_filters(self):
        """Test generation of nested numeric filters."""
        filters = self.generator._generate_nested_numeric_filters('brand__founded_year', 'brand')
        
        # Verify numeric filter types are generated
        expected_filters = [
            'brand__founded_year__exact',
            'brand__founded_year__gt',
            'brand__founded_year__gte',
            'brand__founded_year__lt',
            'brand__founded_year__lte',
            'brand__founded_year__range'
        ]
        
        for expected_filter in expected_filters:
            self.assertIn(expected_filter, filters)
    
    def test_nested_date_filters(self):
        """Test generation of nested date filters."""
        filters = self.generator._generate_nested_date_filters('created_at', 'product')
        
        # Verify date filter types are generated
        expected_filters = [
            'created_at__exact',
            'created_at__gt',
            'created_at__gte',
            'created_at__lt',
            'created_at__lte',
            'created_at__date',
            'created_at__year',
            'created_at__month',
            'created_at__day'
        ]
        
        for expected_filter in expected_filters:
            self.assertIn(expected_filter, filters)
    
    def test_nested_boolean_filters(self):
        """Test generation of nested boolean filters."""
        filters = self.generator._generate_nested_boolean_filters('is_active', 'product')
        
        # Verify boolean filter is generated
        self.assertIn('is_active__exact', filters)
    
    def test_performance_analysis(self):
        """Test query performance analysis functionality."""
        test_filters = {
            'name__icontains': 'test',
            'category__name__exact': 'Electronics',
            'brand__country__name__icontains': 'USA',
            'brand__founded_year__gte': 2000,
            'is_active': True
        }
        
        analysis = self.generator.analyze_query_performance(Product, test_filters)
        
        # Verify analysis structure
        self.assertIn('model', analysis)
        self.assertIn('total_filters', analysis)
        self.assertIn('nested_filters', analysis)
        self.assertIn('max_depth', analysis)
        self.assertIn('select_related_suggestions', analysis)
        self.assertIn('prefetch_related_suggestions', analysis)
        self.assertIn('performance_score', analysis)
        self.assertIn('recommendations', analysis)
        
        # Verify analysis results
        self.assertEqual(analysis['model'], 'Product')
        self.assertEqual(analysis['total_filters'], 5)
        self.assertEqual(analysis['nested_filters'], 3)
        self.assertEqual(analysis['max_depth'], 2)
        
        # Verify optimization suggestions
        self.assertIn('category', analysis['select_related_suggestions'])
        self.assertIn('brand__country', analysis['select_related_suggestions'])
    
    def test_optimized_queryset_generation(self):
        """Test generation of optimized querysets."""
        test_filters = {
            'category__name__exact': 'Electronics',
            'brand__country__name__icontains': 'USA'
        }
        
        # Mock QuerySet for testing
        mock_queryset = Mock()
        mock_queryset.select_related.return_value = mock_queryset
        mock_queryset.prefetch_related.return_value = mock_queryset
        
        with patch.object(Product.objects, 'all', return_value=mock_queryset):
            optimized_qs = self.generator.get_optimized_queryset(Product, test_filters)
            
            # Verify select_related was called with appropriate fields
            mock_queryset.select_related.assert_called()
    
    def test_disabled_nested_filtering(self):
        """Test behavior when nested filtering is disabled."""
        generator = AdvancedFilterGenerator(enable_nested_filters=False)
        filter_set = generator.generate_filter_set(Product)
        filter_instance = filter_set()
        
        # Should not have nested relationship filters (filters that cross model boundaries)
        # Basic field filters with lookup expressions (like name__icontains) are still allowed
        nested_relationship_filters = [
            f for f in filter_instance.filters.keys() 
            if '__' in f and any(rel in f for rel in ['category__', 'brand__'])
        ]
        self.assertEqual(len(nested_relationship_filters), 0)
    
    def test_cache_functionality(self):
        """Test filter set caching functionality."""
        # Generate filter set twice for the same model and depth
        filter_set_1 = self.generator.generate_filter_set(Product, current_depth=0)
        filter_set_2 = self.generator.generate_filter_set(Product, current_depth=0)
        
        # Should return the same cached FilterSet class
        self.assertEqual(filter_set_1, filter_set_2)
    
    @patch('django_graphql_auto.generators.filters.logger')
    def test_error_handling(self, mock_logger):
        """Test error handling in nested filter generation."""
        # Test with invalid model
        with self.assertRaises(AttributeError):
            self.generator.generate_filter_set(None)
        
        # Test with model that has no fields
        class EmptyModel(models.Model):
            class Meta:
                app_label = 'test_app'
        
        # Should handle gracefully
        filter_set = self.generator.generate_filter_set(EmptyModel)
        self.assertTrue(issubclass(filter_set, FilterSet))
    
    def test_complex_nested_relationships(self):
        """Test filtering with complex nested relationships."""
        # Test OrderItem -> Order -> Customer -> nested filtering
        filter_set = self.generator.generate_filter_set(OrderItem, current_depth=0)
        filter_instance = filter_set()
        
        # Verify complex nested filters are available
        expected_complex_filters = [
            'order__customer__username',
            'order__customer__email',
            'product__category__name',
            'product__brand__country__name'
        ]
        
        for expected_filter in expected_complex_filters:
            self.assertIn(expected_filter, filter_instance.filters)
    
    def test_performance_score_calculation(self):
        """Test performance score calculation logic."""
        # Test good performance score
        simple_filters = {'name__icontains': 'test'}
        analysis = self.generator.analyze_query_performance(Product, simple_filters)
        self.assertEqual(analysis['performance_score'], 'good')
        
        # Test moderate performance score
        moderate_filters = {f'field_{i}__nested__value': 'test' for i in range(6)}
        analysis = self.generator.analyze_query_performance(Product, moderate_filters)
        self.assertEqual(analysis['performance_score'], 'moderate')
        
        # Test poor performance score
        complex_filters = {f'field_{i}__very__deeply__nested__value': 'test' for i in range(15)}
        analysis = self.generator.analyze_query_performance(Product, complex_filters)
        self.assertEqual(analysis['performance_score'], 'poor')


class TestNestedFilteringIntegration(TestCase):
    """Integration tests for nested field filtering with real Django models."""
    
    def setUp(self):
        """Set up test data."""
        self.generator = AdvancedFilterGenerator(max_nested_depth=3)
        
        # Create test data
        self.country = Country.objects.create(name="États-Unis", code="USA")
        self.category = Category.objects.create(
            name="Électronique", 
            description="Appareils électroniques"
        )
        self.brand = Brand.objects.create(
            name="TechCorp", 
            country=self.country, 
            founded_year=1995
        )
        self.product = Product.objects.create(
            name="Smartphone Pro",
            price=999.99,
            category=self.category,
            brand=self.brand,
            is_active=True
        )
    
    def test_real_model_filter_generation(self):
        """Test filter generation with real Django models."""
        filter_set = self.generator.generate_filter_set(Product)
        filter_instance = filter_set()
        
        # Debug: Print available filters
        print(f"Available filters: {list(filter_instance.filters.keys())}")
        
        # Test that filters work with real data
        self.assertIn('brand__country__name__icontains', filter_instance.filters)
        self.assertIn('category__name__exact', filter_instance.filters)
        
        # Debug: Check if data exists
        print(f"Product count: {Product.objects.count()}")
        print(f"Brand count: {Brand.objects.count()}")
        print(f"Country count: {Country.objects.count()}")
        
        # Test filter application with a simpler filter first
        simple_filter_data = {
            'name__icontains': 'Smartphone'
        }
        simple_filtered_instance = filter_set(data=simple_filter_data, queryset=Product.objects.all())
        simple_filtered_data = simple_filtered_instance.qs
        print(f"Simple filter result count: {simple_filtered_data.count()}")
        
        # Test filter application
        filter_data = {
            'brand__country__name__icontains': 'États'
        }
        filtered_instance = filter_set(data=filter_data, queryset=Product.objects.all())
        filtered_data = filtered_instance.qs
        
        self.assertEqual(filtered_data.count(), 1)
        self.assertEqual(filtered_data.first(), self.product)
    
    def test_performance_optimization_with_real_data(self):
        """Test performance optimization suggestions with real data."""
        test_filters = {
            'brand__country__name__icontains': 'États',
            'category__name__exact': 'Électronique'
        }
        
        analysis = self.generator.analyze_query_performance(Product, test_filters)
        
        # Verify optimization suggestions are practical
        self.assertIn('brand__country', analysis['select_related_suggestions'])
        self.assertIn('category', analysis['select_related_suggestions'])
        
        # Test optimized queryset
        optimized_qs = self.generator.get_optimized_queryset(Product, test_filters)
        
        # Verify queryset is optimized (would need database query analysis in real scenario)
        self.assertIsNotNone(optimized_qs)


if __name__ == '__main__':
    pytest.main([__file__])