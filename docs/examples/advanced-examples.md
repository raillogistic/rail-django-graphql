# Advanced Examples

This guide provides comprehensive examples of advanced usage patterns and real-world scenarios for the Django GraphQL Auto-Generation Library, including configurable nested relationships and enhanced quote handling.

## 📚 Table of Contents

- [Configurable Nested Relationships](#configurable-nested-relationships)
- [Enhanced Quote Handling Examples](#enhanced-quote-handling-examples)
- [Complex E-commerce Platform](#complex-e-commerce-platform)
- [Multi-tenant SaaS Application](#multi-tenant-saas-application)
- [Content Management System](#content-management-system)
- [Social Media Platform](#social-media-platform)
- [Real-time Analytics Dashboard](#real-time-analytics-dashboard)
- [File Management System](#file-management-system)
- [Advanced Filtering Scenarios](#advanced-filtering-scenarios)
- [Performance Optimization Examples](#performance-optimization-examples)
- [Custom Scalar Implementations](#custom-scalar-implementations)
- [Complex Inheritance Patterns](#complex-inheritance-patterns)

## ⚙️ Configurable Nested Relationships

### Scenario 1: Blog Platform with Selective Nesting

```python
# models.py
from django.db import models
from django.contrib.auth.models import User

class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True)

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

class Tag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#000000')

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    tags = models.ManyToManyField(Tag, related_name='posts')
    related_posts = models.ManyToManyField('self', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
```

#### Configuration: Granular Control

```python
# settings.py
DJANGO_GRAPHQL_AUTO = {
    'MUTATION_SETTINGS': {
        # Global setting: enable nested relations by default
        'enable_nested_relations': True,
        
        # Per-model overrides
        'nested_relations_config': {
            'Comment': False,  # Disable all nested relations for comments
        },
        
        # Per-field granular control
        'nested_field_config': {
            'Post': {
                'comments': False,      # Disable nested comment creation/updates
                'related_posts': False, # Disable nested related posts
                'tags': True,          # Enable nested tag operations
                'category': True,      # Enable nested category operations
                'author': False,       # Disable nested author updates
            },
            'Author': {
                'posts': False,        # Disable nested post creation in author mutations
            }
        }
    }
}
```

#### GraphQL Mutations with Configuration

```graphql
# ✅ ALLOWED: Create post with nested tags and category
mutation CreatePostWithNesting {
  createPost(input: {
    title: "Advanced GraphQL Tutorial"
    content: "Learn about nested operations..."
    category: {
      name: "Technology"
      description: "Tech-related articles"
    }
    tags: [
      { name: "GraphQL", color: "#e10098" }
      { name: "Django", color: "#092e20" }
    ]
  }) {
    ok
    post {
      id
      title
      category { name }
      tags { name color }
    }
    errors
  }
}

# ❌ BLOCKED: Nested comments disabled by configuration
mutation CreatePostWithComments {
  createPost(input: {
    title: "Post Title"
    content: "Content..."
    comments: [  # This will be ignored due to configuration
      { content: "First comment", author: { bio: "Author bio" } }
    ]
  }) {
    ok
    post { id title }
    errors
  }
}

# ❌ BLOCKED: Nested relations disabled for Comment model
mutation CreateCommentWithNesting {
  createComment(input: {
    content: "Comment content"
    post: {  # This will be ignored due to per-model configuration
      title: "New Post"
      content: "Post content"
    }
  }) {
    ok
    comment { id content }
    errors
  }
}
```

### Scenario 2: E-commerce with Security Constraints

```python
# Configuration for secure e-commerce operations
DJANGO_GRAPHQL_AUTO = {
    'MUTATION_SETTINGS': {
        'enable_nested_relations': False,  # Secure default: disabled globally
        
        # Selectively enable for safe operations only
        'nested_relations_config': {
            'Product': True,   # Allow nested product operations
            'Order': False,    # Disable nested order operations (security)
            'User': False,     # Disable nested user operations (security)
        },
        
        'nested_field_config': {
            'Product': {
                'reviews': True,        # Allow nested review creation
                'variants': True,       # Allow nested product variants
                'categories': True,     # Allow nested category assignment
                'supplier': False,      # Disable nested supplier updates (security)
            },
            'Cart': {
                'items': True,         # Allow nested cart item operations
                'user': False,         # Disable nested user operations
                'payment_method': False # Disable nested payment operations
            }
        }
    }
}
```

## 🛡️ Enhanced Quote Handling Examples

### Scenario 1: Content Management with Rich Text

```python
# Input data with complex quoting
input_data = {
    'title': 'Article about "Advanced GraphQL"',
    'content': '''
        This article discusses "nested operations" and their benefits.
        
        Example JSON configuration:
        {
            "enable_nested_relations": true,
            "nested_field_config": {
                "Post": {
                    "comments": false
                }
            }
        }
    ''',
    'metadata': {
        'seo_title': 'Learn about "GraphQL Nesting"',
        'keywords': ['GraphQL', '"nested operations"', 'Django'],
        'description': 'Comprehensive guide to "configurable nesting"'
    },
    'tags': [
        { 'name': '"Advanced" GraphQL' },
        { 'name': 'Django "ORM"' }
    ]
}

# GraphQL mutation with quote handling
mutation CreateArticleWithQuotes {
  createPost(input: {
    title: "Article about \"Advanced GraphQL\""
    content: """
      This article discusses "nested operations" and their benefits.
      
      Example JSON configuration:
      {
        "enable_nested_relations": true,
        "nested_field_config": {
          "Post": {
            "comments": false
          }
        }
      }
    """
    metadata: {
      seoTitle: "Learn about \"GraphQL Nesting\""
      keywords: ["GraphQL", "\"nested operations\"", "Django"]
      description: "Comprehensive guide to \"configurable nesting\""
    }
    tags: [
      { name: "\"Advanced\" GraphQL" }
      { name: "Django \"ORM\"" }
    ]
  }) {
    ok
    post {
      id
      title
      content
      metadata
      tags { name }
    }
    errors
  }
}
```

### Scenario 2: User-Generated Content with Special Characters

```python
# Handling user input with various quote patterns
user_inputs = [
    {
        'comment': 'I love this "feature" - it\'s amazing!',
        'rating': 5,
        'metadata': {
            'device': 'iPhone "Pro Max"',
            'browser': 'Safari "16.0"'
        }
    },
    {
        'review': '''
            The product description said "premium quality" and it delivered!
            
            Specifications:
            - Material: "Stainless Steel"
            - Warranty: "2 years"
            - Rating: "5 stars"
        ''',
        'tags': ['"excellent"', '"premium"', '"recommended"']
    }
]

# GraphQL mutations with automatic sanitization
mutation CreateReviewWithQuotes {
  createReview(input: {
    comment: "I love this \"feature\" - it's amazing!"
    rating: 5
    metadata: {
      device: "iPhone \"Pro Max\""
      browser: "Safari \"16.0\""
    }
  }) {
    ok
    review {
      id
      comment
      rating
      metadata
    }
    errors
  }
}
```

### Scenario 3: API Integration with JSON Data

```python
# Handling API responses with embedded JSON
api_response_data = {
    'webhook_payload': '{"event": "order.created", "data": {"id": 123, "status": "pending"}}',
    'configuration': {
        'settings': '{"theme": "dark", "notifications": {"email": true, "sms": false}}',
        'preferences': '{"language": "en", "timezone": "UTC"}'
    },
    'logs': [
        {
            'message': 'API call successful: {"status": 200, "response_time": "150ms"}',
            'level': 'INFO'
        },
        {
            'message': 'Error occurred: {"error": "timeout", "details": "Connection failed"}',
            'level': 'ERROR'
        }
    ]
}

# The library automatically handles JSON preservation during sanitization
mutation CreateWebhookLog {
  createWebhookLog(input: {
    webhookPayload: "{\"event\": \"order.created\", \"data\": {\"id\": 123, \"status\": \"pending\"}}"
    configuration: {
      settings: "{\"theme\": \"dark\", \"notifications\": {\"email\": true, \"sms\": false}}"
      preferences: "{\"language\": \"en\", \"timezone\": \"UTC\"}"
    }
    logs: [
      {
        message: "API call successful: {\"status\": 200, \"response_time\": \"150ms\"}"
        level: "INFO"
      }
      {
        message: "Error occurred: {\"error\": \"timeout\", \"details\": \"Connection failed\"}"
        level: "ERROR"
      }
    ]
  }) {
    ok
    webhookLog {
      id
      webhookPayload
      configuration
      logs { message level }
    }
    errors
  }
}
```

## 🛒 Complex E-commerce Platform

### Models

```python
# models.py
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import uuid

class Store(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stores')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class GraphQLMeta:
        filter_fields = {
            'name': ['exact', 'icontains'],
            'is_active': ['exact'],
            'owner': ['exact'],
        }
        ordering = ['name', '-created_at']

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='categories')
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['slug', 'store']
        ordering = ['sort_order', 'name']
    
    class GraphQLMeta:
        filter_fields = {
            'name': ['exact', 'icontains'],
            'parent': ['exact', 'isnull'],
            'store': ['exact'],
            'is_active': ['exact'],
        }

class Brand(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='brands/', null=True, blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    
    class GraphQLMeta:
        filter_fields = {
            'name': ['exact', 'icontains'],
        }

class Product(models.Model):
    PRODUCT_TYPES = [
        ('simple', 'Simple Product'),
        ('variable', 'Variable Product'),
        ('grouped', 'Grouped Product'),
        ('external', 'External Product'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField()
    sku = models.CharField(max_length=100, unique=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default='simple')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    description = models.TextField(blank=True)
    short_description = models.TextField(max_length=500, blank=True)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Inventory
    manage_stock = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=5)
    
    # Physical properties
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    length = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['slug', 'store']
        ordering = ['-created_at']
    
    class GraphQLMeta:
        filter_fields = {
            'name': ['exact', 'icontains'],
            'sku': ['exact', 'icontains'],
            'product_type': ['exact', 'in'],
            'store': ['exact'],
            'category': ['exact'],
            'brand': ['exact'],
            'price': ['exact', 'gte', 'lte', 'range'],
            'sale_price': ['exact', 'gte', 'lte', 'isnull'],
            'is_active': ['exact'],
            'is_featured': ['exact'],
            'stock_quantity': ['exact', 'gte', 'lte'],
            'created_at': ['gte', 'lte', 'range'],
        }
        ordering = ['-created_at', 'name', 'price', '-price']
    
    def get_effective_price(self):
        """Get the current selling price (sale price if available, otherwise regular price)."""
        return self.sale_price if self.sale_price else self.price
    
    def get_discount_percentage(self):
        """Calculate discount percentage if on sale."""
        if self.sale_price and self.price > self.sale_price:
            return round(((self.price - self.sale_price) / self.price) * 100, 2)
        return 0
    
    def is_in_stock(self):
        """Check if product is in stock."""
        if not self.manage_stock:
            return True
        return self.stock_quantity > 0
    
    def is_low_stock(self):
        """Check if product is low in stock."""
        if not self.manage_stock:
            return False
        return self.stock_quantity <= self.low_stock_threshold

class ProductAttribute(models.Model):
    """Product attributes like Color, Size, etc."""
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='attributes')
    
    class Meta:
        unique_together = ['slug', 'store']

class ProductAttributeValue(models.Model):
    """Values for product attributes"""
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=200)
    color_code = models.CharField(max_length=7, blank=True)  # For color attributes
    
    class Meta:
        unique_together = ['attribute', 'value']

class ProductVariation(models.Model):
    """Product variations (e.g., Red T-shirt Size M)"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variations')
    sku = models.CharField(max_length=100, unique=True)
    
    # Override parent product pricing/inventory
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.IntegerField(default=0)
    
    # Physical properties override
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class GraphQLMeta:
        filter_fields = {
            'product': ['exact'],
            'sku': ['exact', 'icontains'],
            'price': ['exact', 'gte', 'lte'],
            'is_active': ['exact'],
            'stock_quantity': ['exact', 'gte', 'lte'],
        }

class ProductVariationAttribute(models.Model):
    """Link variations to their attribute values"""
    variation = models.ForeignKey(ProductVariation, on_delete=models.CASCADE, related_name='attributes')
    attribute_value = models.ForeignKey(ProductAttributeValue, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['variation', 'attribute_value']

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    variation = models.ForeignKey(ProductVariation, on_delete=models.CASCADE, null=True, blank=True, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['sort_order', 'id']

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='orders')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    tracking_number = models.CharField(max_length=100, blank=True)
    
    # Addresses
    billing_address = models.JSONField()
    shipping_address = models.JSONField()
    
    # Notes
    customer_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    class GraphQLMeta:
        filter_fields = {
            'order_number': ['exact', 'icontains'],
            'store': ['exact'],
            'customer': ['exact'],
            'status': ['exact', 'in'],
            'total_amount': ['exact', 'gte', 'lte', 'range'],
            'created_at': ['gte', 'lte', 'range'],
            'shipped_at': ['gte', 'lte', 'isnull'],
            'delivered_at': ['gte', 'lte', 'isnull'],
        }
        ordering = ['-created_at', 'order_number', 'total_amount']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation = models.ForeignKey(ProductVariation, on_delete=models.CASCADE, null=True, blank=True)
    
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Snapshot of product data at time of order
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=100)
    variation_attributes = models.JSONField(null=True, blank=True)  # Snapshot of variation attributes
    
    class GraphQLMeta:
        filter_fields = {
            'order': ['exact'],
            'product': ['exact'],
            'quantity': ['exact', 'gte', 'lte'],
            'unit_price': ['exact', 'gte', 'lte'],
            'total_price': ['exact', 'gte', 'lte'],
        }
```

### GraphQL Queries

```graphql
# Complex product search with filtering and nested data
query ProductSearch($storeId: ID!, $filters: ProductFilterInput, $first: Int, $after: String) {
  store(id: $storeId) {
    id
    name
    products(filters: $filters, first: $first, after: $after) {
      edges {
        node {
          id
          name
          slug
          sku
          productType
          price
          salePrice
          effectivePrice
          discountPercentage
          isInStock
          isLowStock
          stockQuantity
          
          # Category hierarchy
          category {
            id
            name
            slug
            parent {
              id
              name
              parent {
                id
                name
              }
            }
          }
          
          # Brand information
          brand {
            id
            name
            slug
            logo
          }
          
          # Primary image
          images(filters: {isPrimary: true}) {
            edges {
              node {
                id
                image
                altText
              }
            }
          }
          
          # Product variations
          variations(filters: {isActive: true}) {
            edges {
              node {
                id
                sku
                price
                salePrice
                stockQuantity
                isActive
                
                # Variation attributes (e.g., Color: Red, Size: M)
                attributes {
                  edges {
                    node {
                      id
                      attributeValue {
                        id
                        value
                        colorCode
                        attribute {
                          name
                          slug
                        }
                      }
                    }
                  }
                }
                
                # Variation-specific images
                images {
                  edges {
                    node {
                      id
                      image
                      altText
                    }
                  }
                }
              }
            }
          }
          
          # Metadata
          createdAt
          updatedAt
          isFeatured
        }
        cursor
      }
      pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
      }
    }
  }
}

# Variables for the above query
{
  "storeId": "1",
  "filters": {
    "isActive": true,
    "category": "5",
    "price_Range": [10.00, 100.00],
    "brand": "2",
    "isInStock": true,
    "name_Icontains": "shirt"
  },
  "first": 20,
  "after": null
}
```

### Complex Mutations

```graphql
# Create product with variations and images
mutation CreateVariableProduct($input: CreateProductWithVariationsInput!) {
  createProductWithVariations(input: $input) {
    product {
      id
      name
      sku
      productType
      price
      
      # Created variations
      variations {
        edges {
          node {
            id
            sku
            price
            stockQuantity
            
            attributes {
              edges {
                node {
                  attributeValue {
                    value
                    attribute {
                      name
                    }
                  }
                }
              }
            }
          }
        }
      }
      
      # Uploaded images
      images {
        edges {
          node {
            id
            image
            isPrimary
            sortOrder
          }
        }
      }
    }
    success
    errors
  }
}

# Variables
{
  "input": {
    "name": "Premium Cotton T-Shirt",
    "slug": "premium-cotton-t-shirt",
    "sku": "PCT-001",
    "productType": "variable",
    "store": "1",
    "category": "5",
    "brand": "2",
    "description": "High-quality cotton t-shirt available in multiple colors and sizes",
    "shortDescription": "Premium cotton t-shirt",
    "price": 29.99,
    "manageStock": true,
    "isActive": true,
    "isFeatured": true,
    
    # Product images
    "images": [
      {
        "image": "base64_encoded_image_data_1",
        "altText": "Premium Cotton T-Shirt - Front View",
        "isPrimary": true,
        "sortOrder": 1
      },
      {
        "image": "base64_encoded_image_data_2",
        "altText": "Premium Cotton T-Shirt - Back View",
        "isPrimary": false,
        "sortOrder": 2
      }
    ],
    
    # Product variations
    "variations": [
      {
        "sku": "PCT-001-RED-S",
        "price": 29.99,
        "stockQuantity": 50,
        "attributes": [
          {
            "attribute": "color",
            "value": "Red"
          },
          {
            "attribute": "size",
            "value": "S"
          }
        ],
        "images": [
          {
            "image": "base64_encoded_red_shirt_image",
            "altText": "Red T-Shirt Size S"
          }
        ]
      },
      {
        "sku": "PCT-001-RED-M",
        "price": 29.99,
        "stockQuantity": 75,
        "attributes": [
          {
            "attribute": "color",
            "value": "Red"
          },
          {
            "attribute": "size",
            "value": "M"
          }
        ]
      },
      {
        "sku": "PCT-001-BLUE-S",
        "price": 32.99,
        "salePrice": 29.99,
        "stockQuantity": 30,
        "attributes": [
          {
            "attribute": "color",
            "value": "Blue"
          },
          {
            "attribute": "size",
            "value": "S"
          }
        ]
      }
    ]
  }
}
```

### Order Management

```graphql
# Complete order with items and customer data
mutation CreateOrder($input: CreateOrderInput!) {
  createOrder(input: $input) {
    order {
      id
      orderNumber
      status
      subtotal
      taxAmount
      shippingAmount
      discountAmount
      totalAmount
      
      customer {
        id
        username
        email
        firstName
        lastName
      }
      
      items {
        edges {
          node {
            id
            quantity
            unitPrice
            totalPrice
            productName
            productSku
            
            product {
              id
              name
              images(filters: {isPrimary: true}) {
                edges {
                  node {
                    image
                  }
                }
              }
            }
            
            variation {
              id
              sku
              attributes {
                edges {
                  node {
                    attributeValue {
                      value
                      attribute {
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
      
      billingAddress
      shippingAddress
      createdAt
    }
    success
    errors
  }
}

# Order status update with tracking
mutation UpdateOrderStatus($orderId: ID!, $input: UpdateOrderStatusInput!) {
  updateOrderStatus(orderId: $orderId, input: $input) {
    order {
      id
      orderNumber
      status
      trackingNumber
      shippedAt
      deliveredAt
      
      # Send notification to customer
      customer {
        email
      }
    }
    success
    errors
  }
}
```

## 🏢 Multi-tenant SaaS Application

### Models with Tenant Isolation

```python
# models.py
from django.db import models
from django.contrib.auth.models import User
import uuid

class Tenant(models.Model):
    """Multi-tenant organization model"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    domain = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Subscription info
    plan = models.CharField(max_length=50, default='free')
    max_users = models.IntegerField(default=5)
    max_projects = models.IntegerField(default=3)
    
    # Settings
    settings = models.JSONField(default=dict)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class GraphQLMeta:
        filter_fields = {
            'name': ['exact', 'icontains'],
            'plan': ['exact', 'in'],
            'is_active': ['exact'],
            'created_at': ['gte', 'lte'],
        }

class TenantUser(models.Model):
    """User membership in tenants"""
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Administrator'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tenant_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    # Permissions
    permissions = models.JSONField(default=list)
    
    # Status
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['tenant', 'user']
    
    class GraphQLMeta:
        filter_fields = {
            'tenant': ['exact'],
            'user': ['exact'],
            'role': ['exact', 'in'],
            'is_active': ['exact'],
        }

class Project(models.Model):
    """Tenant-scoped project"""
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    
    # Project settings
    settings = models.JSONField(default=dict)
    
    # Access control
    is_public = models.BooleanField(default=False)
    allowed_users = models.ManyToManyField(User, through='ProjectMember', related_name='accessible_projects')
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['tenant', 'slug']
    
    class GraphQLMeta:
        filter_fields = {
            'tenant': ['exact'],
            'name': ['exact', 'icontains'],
            'is_public': ['exact'],
            'is_active': ['exact'],
            'created_at': ['gte', 'lte'],
        }

class ProjectMember(models.Model):
    """Project membership with role-based access"""
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('maintainer', 'Maintainer'),
        ('developer', 'Developer'),
        ('reporter', 'Reporter'),
        ('guest', 'Guest'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    # Specific permissions
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)
    can_admin = models.BooleanField(default=False)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['project', 'user']

class Task(models.Model):
    """Project task/issue"""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('done', 'Done'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Assignment
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_tasks')
    
    # Classification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    labels = models.JSONField(default=list)
    
    # Timing
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class GraphQLMeta:
        filter_fields = {
            'project': ['exact'],
            'assignee': ['exact', 'isnull'],
            'reporter': ['exact'],
            'status': ['exact', 'in'],
            'priority': ['exact', 'in'],
            'due_date': ['gte', 'lte', 'isnull'],
            'created_at': ['gte', 'lte', 'range'],
            'completed_at': ['gte', 'lte', 'isnull'],
        }
        ordering = ['-created_at', 'priority', 'due_date']

class Comment(models.Model):
    """Task comments"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    
    # Metadata
    is_internal = models.BooleanField(default=False)  # Internal team comments
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class GraphQLMeta:
        filter_fields = {
            'task': ['exact'],
            'author': ['exact'],
            'is_internal': ['exact'],
            'created_at': ['gte', 'lte'],
        }
        ordering = ['created_at', '-created_at']

class TimeEntry(models.Model):
    """Time tracking for tasks"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_entries')
    
    description = models.TextField(blank=True)
    hours = models.DecimalField(max_digits=6, decimal_places=2)
    
    # Timing
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    # Billing
    is_billable = models.BooleanField(default=True)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class GraphQLMeta:
        filter_fields = {
            'task': ['exact'],
            'user': ['exact'],
            'date': ['exact', 'gte', 'lte', 'range'],
            'is_billable': ['exact'],
            'created_at': ['gte', 'lte'],
        }
        ordering = ['-date', '-created_at']
```

### Tenant-Aware GraphQL Queries

```graphql
# Get tenant dashboard data
query TenantDashboard($tenantId: ID!) {
  tenant(id: $tenantId) {
    id
    name
    plan
    maxUsers
    maxProjects
    
    # Current usage
    memberships(filters: {isActive: true}) {
      totalCount
    }
    
    projects(filters: {isActive: true}) {
      totalCount
      edges {
        node {
          id
          name
          slug
          
          # Project statistics
          tasks {
            totalCount
          }
          
          tasksByStatus: tasks {
            open: totalCount(filters: {status: "open"})
            inProgress: totalCount(filters: {status: "in_progress"})
            done: totalCount(filters: {status: "done"})
          }
          
          # Recent activity
          recentTasks: tasks(first: 5, orderBy: "-created_at") {
            edges {
              node {
                id
                title
                status
                priority
                assignee {
                  username
                  firstName
                  lastName
                }
                createdAt
              }
            }
          }
          
          createdAt
          updatedAt
        }
      }
    }
    
    # Team members
    memberships(filters: {isActive: true}) {
      edges {
        node {
          id
          role
          user {
            id
            username
            email
            firstName
            lastName
          }
          joinedAt
        }
      }
    }
  }
}

# Project management with role-based filtering
query ProjectDetails($projectId: ID!, $userId: ID!) {
  project(id: $projectId) {
    id
    name
    description
    isPublic
    
    # Check user's role in project
    members(filters: {user: $userId}) {
      edges {
        node {
          role
          canRead
          canWrite
          canAdmin
        }
      }
    }
    
    # Tasks with advanced filtering
    tasks(
      filters: {
        status_In: ["open", "in_progress"]
      }
      orderBy: ["-priority", "due_date"]
      first: 20
    ) {
      edges {
        node {
          id
          title
          description
          status
          priority
          labels
          estimatedHours
          actualHours
          dueDate
          
          assignee {
            id
            username
            firstName
            lastName
          }
          
          reporter {
            id
            username
          }
          
          # Recent comments
          comments(first: 3, orderBy: "-created_at") {
            edges {
              node {
                id
                content
                author {
                  username
                }
                createdAt
              }
            }
          }
          
          # Time tracking
          timeEntries {
            totalCount
            totalHours: sum(field: "hours")
          }
          
          createdAt
          updatedAt
          completedAt
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
    
    # Project statistics
    statistics {
      totalTasks
      openTasks
      completedTasks
      totalHours
      billableHours
      
      # Task distribution by status
      tasksByStatus {
        status
        count
      }
      
      # Task distribution by priority
      tasksByPriority {
        priority
        count
      }
      
      # Team productivity
      teamProductivity {
        user {
          username
          firstName
          lastName
        }
        tasksCompleted
        hoursLogged
        averageTaskCompletionTime
      }
    }
  }
}
```

### Multi-tenant Mutations

```graphql
# Create project with team setup
mutation CreateProjectWithTeam($input: CreateProjectWithTeamInput!) {
  createProjectWithTeam(input: $input) {
    project {
      id
      name
      slug
      
      # Added team members
      members {
        edges {
          node {
            user {
              username
              email
            }
            role
            canRead
            canWrite
            canAdmin
          }
        }
      }
    }
    
    # Invitation results
    invitations {
      email
      status
      error
    }
    
    success
    errors
  }
}

# Bulk task operations
mutation BulkUpdateTasks($input: BulkUpdateTasksInput!) {
  bulkUpdateTasks(input: $input) {
    updatedTasks {
      id
      title
      status
      assignee {
        username
      }
    }
    
    results {
      taskId
      success
      error
    }
    
    totalUpdated
    totalFailed
  }
}
```

## 📝 Content Management System

### Hierarchical Content Models

```python
# models.py
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid

class Site(models.Model):
    """Multi-site CMS support"""
    name = models.CharField(max_length=200)
    domain = models.CharField(max_length=100, unique=True)
    
    # Theme and settings
    theme = models.CharField(max_length=100, default='default')
    settings = models.JSONField(default=dict)
    
    # SEO defaults
    default_meta_title = models.CharField(max_length=200, blank=True)
    default_meta_description = models.TextField(max_length=300, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ContentType(models.Model):
    """Define different content types (Article, Page, Product, etc.)"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    
    # Content structure definition
    fields_schema = models.JSONField(default=dict)  # JSON schema for custom fields
    
    # Display settings
    template = models.CharField(max_length=200, blank=True)
    list_template = models.CharField(max_length=200, blank=True)
    
    # Permissions
    can_create = models.ManyToManyField(User, related_name='can_create_content_types', blank=True)
    can_edit = models.ManyToManyField(User, related_name='can_edit_content_types', blank=True)
    
    is_active = models.BooleanField(default=True)

class Category(models.Model):
    """Hierarchical content categories"""
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=200)
    slug = models.SlugField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    description = models.TextField(blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)
    
    # Display
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    sort_order = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['site', 'slug']
        ordering = ['sort_order', 'name']
    
    class GraphQLMeta:
        filter_fields = {
            'site': ['exact'],
            'parent': ['exact', 'isnull'],
            'is_active': ['exact'],
        }

class Content(models.Model):
    """Main content model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    # Basic info
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='content')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='content')
    
    title = models.CharField(max_length=300)
    slug = models.SlugField()
    excerpt = models.TextField(max_length=500, blank=True)
    content = models.TextField()
    
    # Custom fields (stored as JSON)
    custom_fields = models.JSONField(default=dict)
    
    # Categorization
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='content')
    tags = models.ManyToManyField('Tag', blank=True, related_name='content')
    
    # Authorship
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_content')
    editor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_content')
    
    # Publishing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)
    canonical_url = models.URLField(blank=True)
    
    # Social media
    social_image = models.ImageField(upload_to='social/', null=True, blank=True)
    social_title = models.CharField(max_length=200, blank=True)
    social_description = models.TextField(max_length=300, blank=True)
    
    # Analytics
    view_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['site', 'slug']
        ordering = ['-published_at', '-created_at']
    
    class GraphQLMeta:
        filter_fields = {
            'site': ['exact'],
            'content_type': ['exact'],
            'category': ['exact'],
            'author': ['exact'],
            'status': ['exact', 'in'],
            'published_at': ['gte', 'lte', 'isnull'],
            'created_at': ['gte', 'lte', 'range'],
            'title': ['icontains'],
            'content': ['icontains'],
        }
        ordering = ['-published_at', '-created_at', 'title', 'view_count']

class Tag(models.Model):
    """Content tags"""
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#000000')
    
    class Meta:
        unique_together = ['site', 'slug']
    
    class GraphQLMeta:
        filter_fields = {
            'site': ['exact'],
            'name': ['icontains'],
        }

class Media(models.Model):
    """Media library"""
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('other', 'Other'),
    ]
    
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='media')
    
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='media/')
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)
    
    # Metadata
    alt_text = models.CharField(max_length=200, blank=True)
    caption = models.TextField(blank=True)
    description = models.TextField(blank=True)
    
    # File info
    file_size = models.IntegerField()  # in bytes
    mime_type = models.CharField(max_length=100)
    
    # Image-specific
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    
    # Organization
    folder = models.CharField(max_length=200, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='media')
    
    # Usage tracking
    usage_count = models.IntegerField(default=0)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class GraphQLMeta:
        filter_fields = {
            'site': ['exact'],
            'media_type': ['exact', 'in'],
            'folder': ['exact', 'icontains'],
            'uploaded_by': ['exact'],
            'uploaded_at': ['gte', 'lte'],
            'title': ['icontains'],
        }
        ordering = ['-uploaded_at', 'title', 'file_size']

class ContentRevision(models.Model):
    """Content version history"""
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='revisions')
    
    # Snapshot of content at revision time
    title = models.CharField(max_length=300)
    content_data = models.TextField()
    custom_fields = models.JSONField(default=dict)
    
    # Revision metadata
    revision_note = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Change tracking
    changes_summary = models.JSONField(default=dict)  # Summary of what changed
    
    class GraphQLMeta:
        filter_fields = {
            'content': ['exact'],
            'created_by': ['exact'],
            'created_at': ['gte', 'lte'],
        }
        ordering = ['-created_at']

class Menu(models.Model):
    """Site navigation menus"""
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='menus')
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    location = models.CharField(max_length=100)  # header, footer, sidebar, etc.
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['site', 'slug']

class MenuItem(models.Model):
    """Menu items with hierarchy"""
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='items')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    title = models.CharField(max_length=200)
    url = models.CharField(max_length=500, blank=True)
    
    # Link to content
    content = models.ForeignKey(Content, on_delete=models.CASCADE, null=True, blank=True)
    
    # Display options
    css_class = models.CharField(max_length=100, blank=True)
    target = models.CharField(max_length=20, default='_self')  # _self, _blank, etc.
    
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['sort_order', 'title']
```

### Advanced CMS Queries

```graphql
# Complete site content with navigation
query SiteContent($domain: String!, $path: String) {
  site(domain: $domain) {
    id
    name
    theme
    settings
    defaultMetaTitle
    defaultMetaDescription
    
    # Main navigation
    menus(filters: {location: "header", isActive: true}) {
      edges {
        node {
          id
          name
          items(filters: {parent_Isnull: true, isActive: true}) {
            edges {
              node {
                id
                title
                url
                target
                cssClass
                
                # Nested menu items
                children(filters: {isActive: true}) {
                  edges {
                    node {
                      id
                      title
                      url
                      target
                      
                      # Third level
                      children(filters: {isActive: true}) {
                        edges {
                          node {
                            id
                            title
                            url
                          }
                        }
                      }
                    }
                  }
                }
                
                # Linked content
                content {
                  id
                  title
                  slug
                }
              }
            }
          }
        }
      }
    }
    
    # Page content (if path provided)
    content(slug: $path) {
      id
      title
      slug
      excerpt
      content
      customFields
      
      contentType {
        name
        slug
        template
      }
      
      category {
        id
        name
        slug
        
        # Category hierarchy
        parent {
          id
          name
          parent {
            id
            name
          }
        }
      }
      
      tags {
        edges {
          node {
            id
            name
            slug
            color
          }
        }
      }
      
      author {
        id
        username
        firstName
        lastName
      }
      
      # SEO data
      metaTitle
      metaDescription
      canonicalUrl
      socialImage
      socialTitle
      socialDescription
      
      status
      publishedAt
      viewCount
      
      # Related content
      relatedContent: content(
        filters: {
          category: category.id,
          status: "published",
          id_Not: id
        }
        first: 5
      ) {
        edges {
          node {
            id
            title
            slug
            excerpt
            publishedAt
          }
        }
      }
    }
    
    # Recent blog posts
    recentPosts: content(
      filters: {
        contentType_Slug: "blog-post",
        status: "published"
      }
      first: 5
      orderBy: "-published_at"
    ) {
      edges {
        node {
          id
          title
          slug
          excerpt
          publishedAt
          
          author {
            firstName
            lastName
          }
          
          category {
            name
            slug
          }
        }
      }
    }
  }
}

# Content management dashboard
query ContentDashboard($siteId: ID!) {
  site(id: $siteId) {
    id
    name
    
    # Content statistics
    contentStats {
      totalContent
      publishedContent
      draftContent
      
      # By content type
      byContentType {
        contentType {
          name
          slug
        }
        count
      }
      
      # Recent activity
      recentActivity: content(
        first: 10
        orderBy: "-updated_at"
      ) {
        edges {
          node {
            id
            title
            status
            updatedAt
            
            author {
              username
            }
            
            contentType {
              name
            }
          }
        }
      }
    }
    
    # Media library stats
    mediaStats {
      totalFiles
      totalSize
      
      # By media type
      byMediaType {
        mediaType
        count
        totalSize
      }
      
      # Recent uploads
      recentUploads: media(
        first: 10
        orderBy: "-uploaded_at"
      ) {
        edges {
          node {
            id
            title
            mediaType
            fileSize
            uploadedAt
            
            uploadedBy {
              username
            }
          }
        }
      }
    }
  }
}
```

### Content Publishing Workflow

```graphql
# Create content with workflow
mutation CreateContentWithWorkflow($input: CreateContentInput!) {
  createContent(input: $input) {
    content {
      id
      title
      slug
      status
      
      # Auto-generated revision
      revisions(first: 1, orderBy: "-created_at") {
        edges {
          node {
            id
            revisionNote
            createdAt
            createdBy {
              username
            }
          }
        }
      }
    }
    
    # Workflow notifications sent
    notifications {
      recipient {
        email
      }
      type
      sent
    }
    
    success
    errors
  }
}

# Bulk content operations
mutation BulkContentOperation($input: BulkContentOperationInput!) {
  bulkContentOperation(input: $input) {
    results {
      contentId
      success
      error
      
      content {
        id
        title
        status
      }
    }
    
    summary {
      totalProcessed
      successful
      failed
    }
  }
}
```

## 📱 Social Media Platform

### Social Models with Complex Relationships

```python
# models.py
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation

class Profile(models.Model):
    """Extended user profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Profile info
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    
    # Avatar and cover
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    cover_image = models.ImageField(upload_to='covers/', null=True, blank=True)
    
    # Privacy settings
    is_private = models.BooleanField(default=False)
    show_email = models.BooleanField(default=False)
    show_birth_date = models.BooleanField(default=False)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verification_type = models.CharField(max_length=50, blank=True)  # blue_check, business, etc.
    
    # Statistics (denormalized for performance)
    followers_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    posts_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class GraphQLMeta:
        filter_fields = {
            'user': ['exact'],
            'location': ['icontains'],
            'is_private': ['exact'],
            'is_verified': ['exact'],
            'followers_count': ['gte', 'lte'],
            'following_count': ['gte', 'lte'],
            'posts_count': ['gte', 'lte'],
        }

class Follow(models.Model):
    """User following relationships"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    
    # Follow metadata
    is_mutual = models.BooleanField(default=False)  # Both users follow each other
    notification_enabled = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['follower', 'following']
    
    class GraphQLMeta:
        filter_fields = {
            'follower': ['exact'],
            'following': ['exact'],
            'is_mutual': ['exact'],
            'created_at': ['gte', 'lte'],
        }

class Post(models.Model):
    """Social media posts"""
    POST_TYPES = [
        ('text', 'Text Post'),
        ('image', 'Image Post'),
        ('video', 'Video Post'),
        ('link', 'Link Post'),
        ('poll', 'Poll Post'),
    ]
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='text')
    
    # Content
    content = models.TextField(max_length=2000, blank=True)
    
    # Media attachments
    images = GenericRelation('MediaAttachment', related_query_name='post_images')
    videos = GenericRelation('MediaAttachment', related_query_name='post_videos')
    
    # Link preview (for link posts)
    link_url = models.URLField(blank=True)
    link_title = models.CharField(max_length=200, blank=True)
    link_description = models.TextField(max_length=500, blank=True)
    link_image = models.URLField(blank=True)
    
    # Engagement (denormalized)
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)
    
    # Visibility
    is_public = models.BooleanField(default=True)
    is_pinned = models.BooleanField(default=False)
    
    # Moderation
    is_flagged = models.BooleanField(default=False)
    is_removed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class GraphQLMeta:
        filter_fields = {
            'author': ['exact'],
            'post_type': ['exact', 'in'],
            'is_public': ['exact'],
            'is_pinned': ['exact'],
            'is_flagged': ['exact'],
            'is_removed': ['exact'],
            'created_at': ['gte', 'lte', 'range'],
            'likes_count': ['gte', 'lte'],
            'comments_count': ['gte', 'lte'],
        }
        ordering = ['-created_at', '-likes_count', '-comments_count']

class MediaAttachment(models.Model):
    """Generic media attachments for posts"""
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('gif', 'GIF'),
    ]
    
    # Generic foreign key to attach to any model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)
    file = models.FileField(upload_to='media/')
    
    # Metadata
    alt_text = models.CharField(max_length=200, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)  # For videos in seconds
    
    # Processing status (for videos)
    is_processed = models.BooleanField(default=True)
    processing_status = models.CharField(max_length=50, blank=True)
    
    sort_order = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Like(models.Model):
    """Generic likes for posts, comments, etc."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    
    # Generic foreign key
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'content_type', 'object_id']
    
    class GraphQLMeta:
        filter_fields = {
            'user': ['exact'],
            'content_type': ['exact'],
            'created_at': ['gte', 'lte'],
        }

class Comment(models.Model):
    """Comments on posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    content = models.TextField(max_length=1000)
    
    # Engagement
    likes_count = models.IntegerField(default=0)
    replies_count = models.IntegerField(default=0)
    
    # Generic relations for likes
    likes = GenericRelation(Like, related_query_name='comment_likes')
    
    # Moderation
    is_flagged = models.BooleanField(default=False)
    is_removed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class GraphQLMeta:
        filter_fields = {
            'post': ['exact'],
            'author': ['exact'],
            'parent': ['exact', 'isnull'],
            'is_flagged': ['exact'],
            'is_removed': ['exact'],
            'created_at': ['gte', 'lte'],
        }
        ordering = ['created_at', '-created_at', '-likes_count']

class Hashtag(models.Model):
    """Hashtags extracted from posts"""
    tag = models.CharField(max_length=100, unique=True)
    
    # Statistics
    usage_count = models.IntegerField(default=0)
    trending_score = models.FloatField(default=0.0)
    
    # Timestamps
    first_used = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    
    class GraphQLMeta:
        filter_fields = {
            'tag': ['exact', 'icontains'],
            'usage_count': ['gte', 'lte'],
            'trending_score': ['gte', 'lte'],
            'last_used': ['gte', 'lte'],
        }
        ordering = ['-trending_score', '-usage_count', 'tag']

class PostHashtag(models.Model):
    """Many-to-many relationship between posts and hashtags"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='hashtags')
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE, related_name='posts')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['post', 'hashtag']

class Mention(models.Model):
    """User mentions in posts"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='mentions')
    mentioned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentions')
    
    # Position in content
    start_position = models.IntegerField()
    end_position = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['post', 'mentioned_user']

class Story(models.Model):
    """Instagram-style stories"""
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stories')
    
    # Content
    media = GenericRelation(MediaAttachment, related_query_name='story_media')
    text_overlay = models.TextField(max_length=500, blank=True)
    
    # Story-specific features
    background_color = models.CharField(max_length=7, default='#000000')
    music_track = models.CharField(max_length=200, blank=True)
    
    # Visibility
    is_public = models.BooleanField(default=True)
    close_friends_only = models.BooleanField(default=False)
    
    # Analytics
    views_count = models.IntegerField(default=0)
    
    # Auto-expiry (24 hours default)
    expires_at = models.DateTimeField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class GraphQLMeta:
        filter_fields = {
            'author': ['exact'],
            'is_public': ['exact'],
            'close_friends_only': ['exact'],
            'expires_at': ['gte', 'lte'],
            'created_at': ['gte', 'lte'],
        }
        ordering = ['-created_at']

class StoryView(models.Model):
    """Story view tracking"""
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='story_views')
    
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['story', 'viewer']
```

### Social Media GraphQL Queries

```graphql
# User feed with complex filtering and relationships
query UserFeed($userId: ID!, $first: Int, $after: String) {
  user(id: $userId) {
    id
    username
    
    profile {
      avatar
      isPrivate
    }
    
    # Following users for feed content
    following {
      edges {
        node {
          following {
            id
            username
          }
        }
      }
    }
  }
  
  # Feed posts from followed users
  posts(
    filters: {
      author_In: [/* following user IDs */],
      isPublic: true,
      isRemoved: false
    }
    first: $first
    after: $after
    orderBy: "-created_at"
  ) {
    edges {
      node {
        id
        postType
        content
        
        author {
          id
          username
          firstName
          lastName
          
          profile {
            avatar
            isVerified
            verificationType
          }
        }
        
        # Media attachments
        images {
          edges {
            node {
              id
              file
              altText
              width
              height
            }
          }
        }
        
        videos {
          edges {
            node {
              id
              file
              duration
              isProcessed
            }
          }
        }
        
        # Link preview
        linkUrl
        linkTitle
        linkDescription
        linkImage
        
        # Engagement
        likesCount
        commentsCount
        sharesCount
        
        # User's interaction with this post
        userLiked: likes(filters: {user: $userId}) {
          totalCount
        }
        
        # Hashtags
        hashtags {
          edges {
            node {
              hashtag {
                tag
              }
            }
          }
        }
        
        # Mentions
        mentions {
          edges {
            node {
              mentionedUser {
                username
              }
              startPosition
              endPosition
            }
          }
        }
        
        # Recent comments
        comments(
          filters: {
            parent_Isnull: true,
            isRemoved: false
          }
          first: 3
          orderBy: "-created_at"
        ) {
          edges {
            node {
              id
              content
              likesCount
              repliesCount
              
              author {
                username
                profile {
                  avatar
                }
              }
              
              # User's like on comment
              userLiked: likes(filters: {user: $userId}) {
                totalCount
              }
              
              createdAt
            }
          }
          
          totalCount
        }
        
        createdAt
        updatedAt
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}

# User profile with comprehensive data
query UserProfile($username: String!, $viewerId: ID) {
  userByUsername(username: $username) {
    id
    username
    email
    firstName
    lastName
    dateJoined
    
    profile {
      bio
      location
      website
      birthDate
      avatar
      coverImage
      
      # Privacy settings (only show to profile owner)
      isPrivate
      showEmail
      showBirthDate
      
      # Verification
      isVerified
      verificationType
      
      # Statistics
      followersCount
      followingCount
      postsCount
      
      createdAt
    }
    
    # Relationship with viewer
    relationshipWithViewer: followers(filters: {follower: $viewerId}) {
      totalCount
    }
    
    viewerFollowsUser: following(filters: {following: $viewerId}) {
      totalCount
    }
    
    # Recent posts (if public or following)
    posts(
      filters: {
        isPublic: true,
        isRemoved: false
      }
      first: 12
      orderBy: "-created_at"
    ) {
      edges {
        node {
          id
          postType
          content
          
          # Thumbnail for media posts
          images(first: 1) {
            edges {
              node {
                file
                width
                height
              }
            }
          }
          
          likesCount
          commentsCount
          createdAt
        }
      }
    }
    
    # Pinned posts
    pinnedPosts: posts(
      filters: {
        isPinned: true,
        isPublic: true,
        isRemoved: false
      }
      orderBy: "-created_at"
    ) {
      edges {
        node {
          id
          content
          createdAt
        }
      }
    }
    
    # Active stories
    stories(
      filters: {
        expiresAt_Gte: "now",
        isPublic: true
      }
      orderBy: "-created_at"
    ) {
      edges {
        node {
          id
          textOverlay
          backgroundColor
          
          media {
            edges {
              node {
                mediaType
                file
              }
            }
          }
          
          viewsCount
          createdAt
          expiresAt
        }
      }
    }
  }
}

# Trending content discovery
query TrendingContent($timeframe: String = "24h") {
  # Trending hashtags
  trendingHashtags: hashtags(
    filters: {
      lastUsed_Gte: $timeframe
    }
    first: 20
    orderBy: "-trending_score"
  ) {
    edges {
      node {
        tag
        usageCount
        trendingScore
        
        # Recent posts with this hashtag
        posts(
          first: 3
          orderBy: "-created_at"
        ) {
          edges {
            node {
              id
              content
              author {
                username
                profile {
                  avatar
                }
              }
              likesCount
            }
          }
        }
      }
    }
  }
  
  # Trending posts
  trendingPosts: posts(
    filters: {
      createdAt_Gte: $timeframe,
      isPublic: true,
      isRemoved: false
    }
    first: 20
    orderBy: "-likes_count"
  ) {
    edges {
      node {
        id
        postType
        content
        
        author {
          username
          profile {
            avatar
            isVerified
          }
        }
        
        images(first: 1) {
          edges {
            node {
              file
            }
          }
        }
        
        likesCount
        commentsCount
        sharesCount
        createdAt
      }
    }
  }
  
  # Suggested users to follow
  suggestedUsers: users(
    filters: {
      profile_IsPrivate: false
    }
    first: 10
    orderBy: "-profile__followers_count"
  ) {
    edges {
      node {
        id
        username
        firstName
        lastName
        
        profile {
          bio
          avatar
          isVerified
          followersCount
        }
        
        # Mutual connections
        mutualFollowers(viewerId: $viewerId) {
          totalCount
          
          # Sample mutual followers
          edges(first: 3) {
            node {
              follower {
                username
                profile {
                  avatar
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### Social Media Mutations

```graphql
# Create post with media and hashtags
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    post {
      id
      postType
      content
      
      # Uploaded media
      images {
        edges {
          node {
            id
            file
            width
            height
          }
        }
      }
      
      videos {
        edges {
          node {
            id
            file
            duration
            isProcessed
            processingStatus
          }
        }
      }
      
      # Extracted hashtags
      hashtags {
        edges {
          node {
            hashtag {
              tag
            }
          }
        }
      }
      
      # Detected mentions
      mentions {
        edges {
          node {
            mentionedUser {
              username
            }
          }
        }
      }
      
      createdAt
    }
    
    # Notifications sent
    notifications {
      type
      recipient {
        username
      }
      sent
    }
    
    success
    errors
  }
}

# Follow/unfollow user
mutation ToggleFollow($userId: ID!) {
  toggleFollow(userId: $userId) {
    relationship {
      follower {
        username
      }
      following {
        username
        profile {
          followersCount
        }
      }
      isMutual
      createdAt
    }
    
    action  # "followed" or "unfollowed"
    success
  }
}

# Create story with media
mutation CreateStory($input: CreateStoryInput!) {
  createStory(input: $input) {
    story {
      id
      textOverlay
      backgroundColor
      
      media {
        edges {
          node {
            mediaType
            file
          }
        }
      }
      
      isPublic
      closeFriendsOnly
      expiresAt
      createdAt
    }
    
    success
    errors
  }
}
```

## 📊 Real-time Analytics Dashboard

### Analytics Models

```python
# models.py
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from decimal import Decimal
import uuid

class AnalyticsEvent(models.Model):
    """Generic analytics event tracking"""
    EVENT_TYPES = [
        ('page_view', 'Page View'),
        ('click', 'Click'),
        ('form_submit', 'Form Submit'),
        ('purchase', 'Purchase'),
        ('signup', 'Sign Up'),
        ('login', 'Login'),
        ('search', 'Search'),
        ('download', 'Download'),
        ('video_play', 'Video Play'),
        ('custom', 'Custom Event'),
    ]
    
    # Event identification
    event_id = models.UUIDField(default=uuid.uuid4, unique=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    event_name = models.CharField(max_length=200)
    
    # User tracking
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='analytics_events')
    session_id = models.CharField(max_length=100)
    
    # Event data
    properties = models.JSONField(default=dict)  # Custom event properties
    
    # Context
    url = models.URLField()
    referrer = models.URLField(blank=True)
    user_agent = models.TextField()
    ip_address = models.GenericIPAddressField()
    
    # Geographic data
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Device info
    device_type = models.CharField(max_length=50, blank=True)  # desktop, mobile, tablet
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    
    # Timing
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class GraphQLMeta:
        filter_fields = {
            'event_type': ['exact', 'in'],
            'event_name': ['exact', 'icontains'],
            'user': ['exact', 'isnull'],
            'country': ['exact', 'in'],
            'device_type': ['exact', 'in'],
            'browser': ['exact', 'in'],
            'timestamp': ['gte', 'lte', 'range'],
        }
        ordering = ['-timestamp', 'event_type']

class PageView(models.Model):
    """Detailed page view tracking"""
    # Basic info
    url = models.URLField()
    title = models.CharField(max_length=300)
    
    # User tracking
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=100)
    
    # Navigation
    referrer = models.URLField(blank=True)
    landing_page = models.BooleanField(default=False)
    exit_page = models.BooleanField(default=False)
    
    # Engagement metrics
    time_on_page = models.IntegerField(null=True, blank=True)  # seconds
    scroll_depth = models.IntegerField(null=True, blank=True)  # percentage
    
    # Technical details
    load_time = models.IntegerField(null=True, blank=True)  # milliseconds
    user_agent = models.TextField()
    ip_address = models.GenericIPAddressField()
    
    # Geographic
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Device
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    screen_resolution = models.CharField(max_length=20, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class GraphQLMeta:
        filter_fields = {
            'url': ['exact', 'icontains'],
            'user': ['exact', 'isnull'],
            'landing_page': ['exact'],
            'exit_page': ['exact'],
            'country': ['exact', 'in'],
            'device_type': ['exact', 'in'],
            'browser': ['exact', 'in'],
            'timestamp': ['gte', 'lte', 'range'],
        }

class ConversionFunnel(models.Model):
    """Define conversion funnels"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Funnel steps (ordered)
    steps = models.JSONField()  # List of step definitions
    
    # Configuration
    time_window = models.IntegerField(default=86400)  # seconds (24 hours default)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class FunnelStep(models.Model):
    """Individual funnel step"""
    funnel = models.ForeignKey(ConversionFunnel, on_delete=models.CASCADE, related_name='funnel_steps')
    
    name = models.CharField(max_length=200)
    step_order = models.IntegerField()
    
    # Step criteria
    event_type = models.CharField(max_length=50)
    event_conditions = models.JSONField(default=dict)  # Conditions to match
    
    class Meta:
        unique_together = ['funnel', 'step_order']
        ordering = ['step_order']

class UserSession(models.Model):
    """User session tracking"""
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Session details
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)  # seconds
    
    # Entry/exit
    landing_page = models.URLField()
    exit_page = models.URLField(blank=True)
    
    # Engagement
    page_views = models.IntegerField(default=0)
    events_count = models.IntegerField(default=0)
    
    # Attribution
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    utm_term = models.CharField(max_length=100, blank=True)
    utm_content = models.CharField(max_length=100, blank=True)
    
    # Device/location (from first event)
    country = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    
    class GraphQLMeta:
        filter_fields = {
            'user': ['exact', 'isnull'],
            'start_time': ['gte', 'lte', 'range'],
            'duration': ['gte', 'lte'],
            'utm_source': ['exact', 'in'],
            'utm_medium': ['exact', 'in'],
            'utm_campaign': ['exact', 'in'],
            'country': ['exact', 'in'],
            'device_type': ['exact', 'in'],
        }

class Goal(models.Model):
    """Conversion goals"""
    GOAL_TYPES = [
        ('event', 'Event Goal'),
        ('page', 'Page Goal'),
        ('duration', 'Duration Goal'),
        ('pages_per_session', 'Pages per Session Goal'),
    ]
    
    name = models.CharField(max_length=200)
    goal_type = models.CharField(max_length=50, choices=GOAL_TYPES)
    
    # Goal criteria
    conditions = models.JSONField()
    
    # Value
    goal_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class GoalConversion(models.Model):
    """Goal conversion tracking"""
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='conversions')
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE, related_name='goal_conversions')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Conversion details
    conversion_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Attribution
    first_touch_source = models.CharField(max_length=100, blank=True)
    last_touch_source = models.CharField(max_length=100, blank=True)
    
    converted_at = models.DateTimeField(auto_now_add=True)
    
    class GraphQLMeta:
        filter_fields = {
            'goal': ['exact'],
            'user': ['exact', 'isnull'],
            'converted_at': ['gte', 'lte', 'range'],
            'first_touch_source': ['exact', 'in'],
            'last_touch_source': ['exact', 'in'],
        }

class ABTest(models.Model):
    """A/B testing framework"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Test configuration
    variants = models.JSONField()  # List of variant definitions
    traffic_allocation = models.JSONField()  # Traffic split percentages
    
    # Targeting
    targeting_rules = models.JSONField(default=dict)
    
    # Status
    is_active = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    # Goals
    primary_goal = models.ForeignKey(Goal, on_delete=models.SET_NULL, null=True, related_name='primary_tests')
    secondary_goals = models.ManyToManyField(Goal, blank=True, related_name='secondary_tests')
    
    created_at = models.DateTimeField(auto_now_add=True)

class ABTestAssignment(models.Model):
    """User assignments to A/B test variants"""
    test = models.ForeignKey(ABTest, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100)
    
    variant = models.CharField(max_length=100)
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['test', 'user', 'session_id']
```

### Analytics Dashboard Queries

```graphql
# Comprehensive analytics dashboard
query AnalyticsDashboard($dateRange: DateRangeInput!, $filters: AnalyticsFiltersInput) {
  # Overview metrics
  overview: analyticsOverview(dateRange: $dateRange, filters: $filters) {
    totalPageViews
    uniqueVisitors
    totalSessions
    averageSessionDuration
    bounceRate
    conversionRate
    
    # Comparison with previous period
    previousPeriod {
      totalPageViews
      uniqueVisitors
      totalSessions
      averageSessionDuration
      bounceRate
      conversionRate
    }
    
    # Growth percentages
    growth {
      pageViewsGrowth
      visitorsGrowth
      sessionsGrowth
      durationGrowth
      bounceRateChange
      conversionRateChange
    }
  }
  
  # Traffic sources
  trafficSources: userSessions(
    dateRange: $dateRange
    filters: $filters
    groupBy: ["utm_source", "utm_medium"]
  ) {
    groups {
      source
      medium
      sessions
      users
      pageViews
      averageDuration
      conversionRate
      
      # Trend data
      trend(interval: "day") {
        date
        sessions
        users
      }
    }
  }
  
  # Geographic distribution
  geographic: userSessions(
    dateRange: $dateRange
    filters: $filters
    groupBy: ["country"]
    orderBy: "-sessions"
    limit: 20
  ) {
    groups {
      country
      sessions
      users
      pageViews
      conversionRate
    }
  }
  
  # Device breakdown
  devices: userSessions(
    dateRange: $dateRange
    filters: $filters
    groupBy: ["device_type", "browser"]
  ) {
    groups {
      deviceType
      browser
      sessions
      users
      averageDuration
      bounceRate
    }
  }
  
  # Top pages
  topPages: pageViews(
    dateRange: $dateRange
    filters: $filters
    groupBy: ["url", "title"]
    orderBy: "-page_views"
    limit: 20
  ) {
    groups {
      url
      title
      pageViews
      uniquePageViews
      averageTimeOnPage
      exitRate
      
      # Page performance metrics
      averageLoadTime
      averageScrollDepth
    }
  }
  
  # Real-time data (last 30 minutes)
  realTime: analyticsRealTime {
    activeUsers
    pageViewsLast30Min
    topActivePages {
      url
      title
      activeUsers
    }
    
    # Live events stream
    recentEvents(limit: 50) {
      eventType
      eventName
      url
      country
      deviceType
      timestamp
    }
  }
  
  # Conversion funnels
  funnels: conversionFunnels(dateRange: $dateRange, filters: $filters) {
    edges {
      node {
        id
        name
        
        # Funnel analysis
        analysis {
          totalEntries
          
          steps {
            stepName
            stepOrder
            users
            conversionRate
            dropoffRate
            
            # Step-to-step conversion
            fromPreviousStep {
              users
              conversionRate
            }
          }
          
          # Overall funnel metrics
          overallConversionRate
          totalDropoffs
        }
        
        # Funnel visualization data
        visualization {
          stepName
          users
          percentage
        }
      }
    }
  }
  
  # Goal conversions
  goals: goals(filters: {isActive: true}) {
    edges {
      node {
        id
        name
        goalType
        goalValue
        
        # Goal performance
        performance(dateRange: $dateRange) {
          totalConversions
          conversionRate
          totalValue
          
          # Conversion trend
          trend(interval: "day") {
            date
            conversions
            conversionRate
            value
          }
          
          # Attribution analysis
          attribution {
            firstTouchSources {
              source
              conversions
              percentage
            }
            
            lastTouchSources {
              source
              conversions
              percentage
            }
          }
        }
      }
    }
  }
  
  # A/B tests
  abTests: abTests(filters: {isActive: true}) {
    edges {
      node {
        id
        name
        description
        
        # Test results
        results(dateRange: $dateRange) {
          variants {
            variantName
            participants
            
            # Primary goal performance
            primaryGoal {
              conversions
              conversionRate
              confidence
              significance
            }
            
            # Secondary goals
            secondaryGoals {
              goalName
              conversions
              conversionRate
            }
          }
          
          # Statistical significance
          statisticalSignificance
          recommendedWinner
        }
      }
    }
  }
}

# Event analytics with custom dimensions
query EventAnalytics($dateRange: DateRangeInput!, $eventType: String!, $dimensions: [String!]) {
  events: analyticsEvents(
    dateRange: $dateRange
    filters: {eventType: $eventType}
    groupBy: $dimensions
  ) {
    groups {
      # Dynamic dimensions based on input
      dimensions
      
      # Metrics
      totalEvents
      uniqueUsers
      
      # Event properties analysis
      properties {
        propertyName
        values {
          value
          count
          percentage
        }
      }
      
      # Trend analysis
      trend(interval: "hour") {
        timestamp
        events
        users
      }
    }
  }
  
  # Event flow analysis
  eventFlow: eventFlow(
    dateRange: $dateRange
    startEvent: $eventType
    maxSteps: 5
  ) {
    steps {
      stepNumber
      eventType
      eventName
      users
      
      # Flow to next events
      nextEvents {
        eventType
        eventName
        users
        percentage
      }
    }
  }
}

# User journey analysis
query UserJourneyAnalysis($userId: ID!, $dateRange: DateRangeInput) {
  user(id: $userId) {
    id
    username
    
    # User's sessions in date range
    sessions(dateRange: $dateRange, orderBy: "start_time") {
      edges {
        node {
          sessionId
          startTime
          endTime
          duration
          pageViews
          
          # Attribution
          utmSource
          utmMedium
          utmCampaign
          
          # Journey events
          events(orderBy: "timestamp") {
            edges {
              node {
                eventType
                eventName
                url
                properties
                timestamp
              }
            }
          }
          
          # Page views in session
          pageViews(orderBy: "timestamp") {
            edges {
              node {
                url
                title
                timeOnPage
                scrollDepth
                timestamp
              }
            }
          }
          
          # Goal conversions in session
          goalConversions {
            edges {
              node {
                goal {
                  name
                }
                conversionValue
                convertedAt
              }
            }
          }
        }
      }
    }
    
    # User's overall analytics
    analytics(dateRange: $dateRange) {
      totalSessions
      totalPageViews
      totalTimeSpent
      averageSessionDuration
      
      # Conversion history
      conversions {
        totalConversions
        totalValue
        
        byGoal {
          goalName
          conversions
          totalValue
        }
      }
      
      # Engagement patterns
      engagementPatterns {
        mostActiveHours
        mostActiveDays
        preferredDevices
        topPages
      }
    }
  }
}
```

This comprehensive advanced examples documentation covers:

1. **Complex E-commerce Platform** - Multi-store, products with variations, orders
2. **Multi-tenant SaaS Application** - Tenant isolation, role-based access, project management
3. **Content Management System** - Hierarchical content, media management, publishing workflow
4. **Social Media Platform** - Posts, relationships, engagement, stories
5. **Real-time Analytics Dashboard** - Event tracking, funnels, A/B testing, user journeys

Each section includes:
- Detailed Django models with GraphQL configuration
- Complex GraphQL queries with nested relationships
- Advanced filtering and pagination
- Mutations for creating and updating data
- Real-world scenarios and use cases

The examples demonstrate the library's capabilities for handling complex business logic, relationships, and data structures while maintaining performance and usability.