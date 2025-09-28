"""
Nested Field Filtering Examples for Django GraphQL Auto System

This module demonstrates practical implementations of nested field filtering
across various model relationships and use cases.
"""

from django.db import models
from django_graphql_auto.generators.filters import AdvancedFilterGenerator
import graphene
from graphene_django import DjangoObjectType
from django_filters import FilterSet


# Example Models for E-commerce System
class Country(models.Model):
    """Country model for geographic filtering"""
    name = models.CharField(max_length=100, verbose_name="Nom du pays")
    code = models.CharField(max_length=3, unique=True, verbose_name="Code pays")
    
    class Meta:
        verbose_name = "Pays"
        verbose_name_plural = "Pays"
    
    def __str__(self):
        return self.name


class Category(models.Model):
    """Product category with hierarchical structure"""
    name = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE,
        verbose_name="Catégorie parente"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
    
    def __str__(self):
        return self.name


class Brand(models.Model):
    """Brand model with country relationship"""
    name = models.CharField(max_length=100, verbose_name="Nom de la marque")
    country = models.ForeignKey(
        Country, 
        on_delete=models.CASCADE,
        verbose_name="Pays d'origine"
    )
    founded_year = models.IntegerField(null=True, blank=True, verbose_name="Année de fondation")
    is_active = models.BooleanField(default=True, verbose_name="Marque active")
    
    class Meta:
        verbose_name = "Marque"
        verbose_name_plural = "Marques"
    
    def __str__(self):
        return self.name


class Customer(models.Model):
    """Customer model with profile relationship"""
    email = models.EmailField(unique=True, verbose_name="Adresse email")
    first_name = models.CharField(max_length=50, verbose_name="Prénom")
    last_name = models.CharField(max_length=50, verbose_name="Nom de famille")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    is_active = models.BooleanField(default=True, verbose_name="Client actif")
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class CustomerProfile(models.Model):
    """Extended customer profile information"""
    customer = models.OneToOneField(
        Customer, 
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Client"
    )
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="Numéro de téléphone")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    country = models.ForeignKey(
        Country, 
        on_delete=models.CASCADE,
        verbose_name="Pays de résidence"
    )
    city = models.CharField(max_length=100, verbose_name="Ville")
    is_verified = models.BooleanField(default=False, verbose_name="Profil vérifié")
    
    class Meta:
        verbose_name = "Profil client"
        verbose_name_plural = "Profils clients"
    
    def __str__(self):
        return f"Profile de {self.customer}"


class Product(models.Model):
    """Product model with category and brand relationships"""
    name = models.CharField(max_length=200, verbose_name="Nom du produit")
    description = models.TextField(blank=True, verbose_name="Description")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix")
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE,
        verbose_name="Catégorie"
    )
    brand = models.ForeignKey(
        Brand, 
        on_delete=models.CASCADE,
        verbose_name="Marque"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    is_available = models.BooleanField(default=True, verbose_name="Produit disponible")
    stock_quantity = models.IntegerField(default=0, verbose_name="Quantité en stock")
    
    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
    
    def __str__(self):
        return self.name


class Order(models.Model):
    """Order model with customer relationship"""
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="Client"
    )
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Date de commande")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant total")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'En attente'),
            ('processing', 'En cours de traitement'),
            ('shipped', 'Expédié'),
            ('delivered', 'Livré'),
            ('cancelled', 'Annulé'),
        ],
        default='pending',
        verbose_name="Statut"
    )
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
    
    def __str__(self):
        return f"Commande #{self.id} - {self.customer}"


class OrderItem(models.Model):
    """Order item model linking orders and products"""
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Commande"
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        verbose_name="Produit"
    )
    quantity = models.IntegerField(verbose_name="Quantité")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire")
    
    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"


# GraphQL Types
class CountryType(DjangoObjectType):
    class Meta:
        model = Country
        fields = '__all__'


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = '__all__'


class BrandType(DjangoObjectType):
    class Meta:
        model = Brand
        fields = '__all__'


class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = '__all__'


class CustomerProfileType(DjangoObjectType):
    class Meta:
        model = CustomerProfile
        fields = '__all__'


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = '__all__'


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = '__all__'


class OrderItemType(DjangoObjectType):
    class Meta:
        model = OrderItem
        fields = '__all__'


# Filter Generation Examples
def create_nested_filters():
    """
    Demonstrates how to create nested filters for different models
    with various depth configurations.
    """
    
    # Example 1: Basic nested filtering (depth 2)
    print("=== Example 1: Basic Nested Filtering ===")
    basic_generator = AdvancedFilterGenerator(
        max_nested_depth=2,
        enable_nested_filters=True
    )
    
    product_filter_set = basic_generator.generate_filter_set(Product)
    print(f"Product filters (depth 2): {len(product_filter_set.base_filters)} filters")
    
    # Show some example filters
    sample_filters = [f for f in product_filter_set.base_filters.keys() if '__' in f][:10]
    for filter_name in sample_filters:
        print(f"  - {filter_name}")
    
    # Example 2: Deep nested filtering (depth 3)
    print("\n=== Example 2: Deep Nested Filtering ===")
    deep_generator = AdvancedFilterGenerator(
        max_nested_depth=3,
        enable_nested_filters=True
    )
    
    order_filter_set = deep_generator.generate_filter_set(Order)
    print(f"Order filters (depth 3): {len(order_filter_set.base_filters)} filters")
    
    # Show deep nested filters
    deep_filters = [f for f in order_filter_set.base_filters.keys() if f.count('__') >= 2][:5]
    for filter_name in deep_filters:
        print(f"  - {filter_name}")
    
    # Example 3: Conservative filtering (depth 1)
    print("\n=== Example 3: Conservative Filtering ===")
    conservative_generator = AdvancedFilterGenerator(
        max_nested_depth=1,
        enable_nested_filters=True
    )
    
    customer_filter_set = conservative_generator.generate_filter_set(Customer)
    print(f"Customer filters (depth 1): {len(customer_filter_set.base_filters)} filters")
    
    return {
        'product_filters': product_filter_set,
        'order_filters': order_filter_set,
        'customer_filters': customer_filter_set,
    }


# GraphQL Query Examples
class Query(graphene.ObjectType):
    """GraphQL Query class with nested filtering examples"""
    
    # Products with nested filtering
    products = graphene.List(
        ProductType,
        filters=graphene.Argument(graphene.JSONString),
        description="Query products with nested filtering support"
    )
    
    # Orders with deep nested filtering
    orders = graphene.List(
        OrderType,
        filters=graphene.Argument(graphene.JSONString),
        description="Query orders with deep nested filtering"
    )
    
    # Customers with profile filtering
    customers = graphene.List(
        CustomerType,
        filters=graphene.Argument(graphene.JSONString),
        description="Query customers with profile filtering"
    )
    
    def resolve_products(self, info, filters=None):
        """
        Resolve products with nested filtering.
        
        Example filters:
        {
            "name__icontains": "laptop",
            "category__name__exact": "Electronics",
            "category__parent__name": "Technology",
            "brand__name__in": ["Apple", "Dell"],
            "brand__country__name": "United States",
            "price__range": [500, 2000],
            "created_at__year": 2024,
            "is_available": true
        }
        """
        queryset = Product.objects.select_related(
            'category',
            'category__parent',
            'brand',
            'brand__country'
        )
        
        if filters:
            generator = AdvancedFilterGenerator(max_nested_depth=3)
            filter_set_class = generator.generate_filter_set(Product)
            filter_set = filter_set_class(filters, queryset=queryset)
            return filter_set.qs
        
        return queryset
    
    def resolve_orders(self, info, filters=None):
        """
        Resolve orders with deep nested filtering.
        
        Example filters:
        {
            "customer__email__endswith": "@gmail.com",
            "customer__profile__country__name": "France",
            "customer__profile__city__icontains": "paris",
            "customer__profile__is_verified": true,
            "items__product__category__name": "Electronics",
            "items__product__brand__country__code": "US",
            "total_amount__gte": 100,
            "order_date__year": 2024,
            "status__in": ["processing", "shipped"]
        }
        """
        queryset = Order.objects.select_related(
            'customer',
            'customer__profile',
            'customer__profile__country'
        ).prefetch_related(
            'items',
            'items__product',
            'items__product__category',
            'items__product__brand',
            'items__product__brand__country'
        )
        
        if filters:
            generator = AdvancedFilterGenerator(max_nested_depth=4)
            filter_set_class = generator.generate_filter_set(Order)
            filter_set = filter_set_class(filters, queryset=queryset)
            return filter_set.qs
        
        return queryset
    
    def resolve_customers(self, info, filters=None):
        """
        Resolve customers with profile filtering.
        
        Example filters:
        {
            "first_name__startswith": "John",
            "email__icontains": "example",
            "profile__country__name": "France",
            "profile__city__iexact": "lyon",
            "profile__is_verified": true,
            "profile__birth_date__year__gte": 1990,
            "date_joined__gte": "2024-01-01",
            "is_active": true
        }
        """
        queryset = Customer.objects.select_related(
            'profile',
            'profile__country'
        )
        
        if filters:
            generator = AdvancedFilterGenerator(max_nested_depth=2)
            filter_set_class = generator.generate_filter_set(Customer)
            filter_set = filter_set_class(filters, queryset=queryset)
            return filter_set.qs
        
        return queryset


# Usage Examples and Test Cases
def demonstrate_filtering_scenarios():
    """
    Demonstrates various nested filtering scenarios with practical examples.
    """
    
    print("=== Nested Field Filtering Demonstration ===\n")
    
    # Scenario 1: E-commerce Product Search
    print("Scenario 1: E-commerce Product Search")
    print("Filter products by brand country and category hierarchy:")
    
    example_filters_1 = {
        "brand__country__name__icontains": "japan",
        "category__parent__name__exact": "Technology",
        "price__range": [100, 1000],
        "is_available": True,
        "created_at__year": 2024
    }
    
    print(f"Filters: {example_filters_1}")
    print("GraphQL Query:")
    print("""
    query {
      products(filters: {
        brand__country__name__icontains: "japan"
        category__parent__name__exact: "Technology"
        price__range: [100, 1000]
        is_available: true
        created_at__year: 2024
      }) {
        name
        price
        brand {
          name
          country {
            name
          }
        }
        category {
          name
          parent {
            name
          }
        }
      }
    }
    """)
    
    # Scenario 2: Customer Order Analysis
    print("\nScenario 2: Customer Order Analysis")
    print("Find orders from verified customers in specific regions:")
    
    example_filters_2 = {
        "customer__profile__is_verified": True,
        "customer__profile__country__code": "FR",
        "customer__profile__city__icontains": "paris",
        "total_amount__gte": 50,
        "status__in": ["processing", "shipped", "delivered"],
        "order_date__month": 6
    }
    
    print(f"Filters: {example_filters_2}")
    print("GraphQL Query:")
    print("""
    query {
      orders(filters: {
        customer__profile__is_verified: true
        customer__profile__country__code: "FR"
        customer__profile__city__icontains: "paris"
        total_amount__gte: 50
        status__in: ["processing", "shipped", "delivered"]
        order_date__month: 6
      }) {
        id
        totalAmount
        status
        customer {
          firstName
          lastName
          profile {
            city
            country {
              name
            }
            isVerified
          }
        }
      }
    }
    """)
    
    # Scenario 3: Complex Multi-level Filtering
    print("\nScenario 3: Complex Multi-level Filtering")
    print("Find orders containing specific products from certain brands:")
    
    example_filters_3 = {
        "items__product__name__icontains": "laptop",
        "items__product__brand__name__in": ["Apple", "Dell", "HP"],
        "items__product__brand__country__name": "United States",
        "items__product__category__name__exact": "Computers",
        "customer__email__endswith": "@company.com",
        "total_amount__range": [1000, 5000]
    }
    
    print(f"Filters: {example_filters_3}")
    print("GraphQL Query:")
    print("""
    query {
      orders(filters: {
        items__product__name__icontains: "laptop"
        items__product__brand__name__in: ["Apple", "Dell", "HP"]
        items__product__brand__country__name: "United States"
        items__product__category__name__exact: "Computers"
        customer__email__endswith: "@company.com"
        total_amount__range: [1000, 5000]
      }) {
        id
        totalAmount
        customer {
          email
        }
        items {
          quantity
          product {
            name
            brand {
              name
              country {
                name
              }
            }
            category {
              name
            }
          }
        }
      }
    }
    """)


# Performance Testing and Optimization Examples
def performance_optimization_examples():
    """
    Demonstrates performance optimization techniques for nested filtering.
    """
    
    print("=== Performance Optimization Examples ===\n")
    
    # Example 1: Optimized QuerySet with select_related
    print("Example 1: Optimized Product Queries")
    
    def get_optimized_products_queryset():
        """Optimized queryset for product filtering with nested relationships"""
        return Product.objects.select_related(
            'category',
            'category__parent',
            'brand',
            'brand__country'
        ).prefetch_related(
            'orderitem_set',
            'orderitem_set__order',
            'orderitem_set__order__customer'
        )
    
    # Example 2: Optimized Order Queries with Deep Relationships
    print("Example 2: Optimized Order Queries with Deep Relationships")
    
    def get_optimized_orders_queryset():
        """Optimized queryset for order filtering with deep nested relationships"""
        return Order.objects.select_related(
            'customer',
            'customer__profile',
            'customer__profile__country'
        ).prefetch_related(
            'items',
            'items__product',
            'items__product__category',
            'items__product__category__parent',
            'items__product__brand',
            'items__product__brand__country'
        )
    
    # Example 3: Custom Filter Generator with Performance Monitoring
    class PerformanceOptimizedFilterGenerator(AdvancedFilterGenerator):
        """Custom filter generator with performance optimizations"""
        
        def generate_filter_set(self, model, current_depth=0):
            """Override to add performance monitoring"""
            import time
            start_time = time.time()
            
            filter_set = super().generate_filter_set(model, current_depth)
            
            generation_time = time.time() - start_time
            filter_count = len(filter_set.base_filters)
            
            print(f"Generated {filter_count} filters for {model.__name__} "
                  f"in {generation_time:.4f} seconds")
            
            return filter_set
        
        def _suggest_query_optimizations(self, model, filters):
            """Suggest query optimizations based on used filters"""
            suggestions = []
            
            # Analyze filters for select_related suggestions
            select_related_fields = set()
            prefetch_related_fields = set()
            
            for filter_name in filters.keys():
                if '__' in filter_name:
                    parts = filter_name.split('__')[:-1]  # Remove lookup part
                    field_path = '__'.join(parts)
                    
                    # Check if it's a forward relationship (select_related)
                    try:
                        field = model._meta.get_field(parts[0])
                        if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                            select_related_fields.add(field_path)
                        elif hasattr(field, 'related_model'):
                            prefetch_related_fields.add(field_path)
                    except:
                        pass
            
            if select_related_fields:
                suggestions.append(f"select_related({', '.join(repr(f) for f in select_related_fields)})")
            
            if prefetch_related_fields:
                suggestions.append(f"prefetch_related({', '.join(repr(f) for f in prefetch_related_fields)})")
            
            return suggestions
    
    print("Example 3: Performance Monitoring Filter Generator")
    perf_generator = PerformanceOptimizedFilterGenerator(max_nested_depth=3)
    
    # Test with different models
    for model in [Product, Order, Customer]:
        print(f"\nTesting {model.__name__}:")
        filter_set = perf_generator.generate_filter_set(model)


if __name__ == "__main__":
    """
    Run examples and demonstrations
    """
    
    print("Django GraphQL Auto - Nested Field Filtering Examples")
    print("=" * 60)
    
    # Create filter examples
    filters = create_nested_filters()
    
    # Demonstrate filtering scenarios
    demonstrate_filtering_scenarios()
    
    # Show performance optimization examples
    performance_optimization_examples()
    
    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("\nTo use these examples in your Django project:")
    print("1. Add the models to your Django app")
    print("2. Run migrations: python manage.py makemigrations && python manage.py migrate")
    print("3. Use the GraphQL queries in your GraphQL endpoint")
    print("4. Apply the performance optimizations in your resolvers")