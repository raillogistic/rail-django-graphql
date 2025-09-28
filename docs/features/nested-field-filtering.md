# Nested Field Filtering

## Overview

The Django GraphQL Auto System provides powerful nested field filtering capabilities that allow you to filter queries based on related model fields. This feature enables complex filtering scenarios across model relationships while maintaining performance and preventing infinite recursion.

## Table of Contents

1. [Basic Nested Filtering](#basic-nested-filtering)
2. [Configuration](#configuration)
3. [Filter Types](#filter-types)
4. [Examples](#examples)
5. [Performance Considerations](#performance-considerations)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## Basic Nested Filtering

Nested field filtering allows you to filter on fields of related models using Django's double underscore (`__`) syntax in GraphQL queries.

### Syntax

```graphql
query {
  users(filters: {
    profile__country__icontains: "France"
    posts__title__startswith: "Django"
    posts__created_at__gte: "2024-01-01"
  }) {
    id
    username
    profile {
      country
    }
    posts {
      title
      createdAt
    }
  }
}
```

## Configuration

### Generator Configuration

```python
from django_graphql_auto.generators.filters import AdvancedFilterGenerator

# Configure nested filtering
filter_generator = AdvancedFilterGenerator(
    max_nested_depth=3,        # Maximum nesting depth (default: 3, max: 5)
    enable_nested_filters=True  # Enable/disable nested filtering (default: True)
)

# Generate FilterSet for a model
UserFilterSet = filter_generator.generate_filter_set(User)
```

### Settings Configuration

```python
# settings.py
DJANGO_GRAPHQL_AUTO = {
    'FILTERING': {
        'MAX_NESTED_DEPTH': 3,
        'ENABLE_NESTED_FILTERS': True,
        'CACHE_FILTER_SETS': True,
    }
}
```

## Filter Types

### Text Field Filters

For `CharField` and `TextField` in related models:

```graphql
query {
  posts(filters: {
    author__username__contains: "john"
    author__username__icontains: "JOHN"
    author__username__startswith: "j"
    author__username__endswith: "n"
    author__username__exact: "john_doe"
  }) {
    title
    author {
      username
    }
  }
}
```

### Numeric Field Filters

For `IntegerField`, `FloatField`, `DecimalField` in related models:

```graphql
query {
  orders(filters: {
    customer__age__gt: 18
    customer__age__gte: 21
    customer__age__lt: 65
    customer__age__lte: 64
    customer__age__range: [25, 45]
  }) {
    id
    customer {
      age
    }
  }
}
```

### Date Field Filters

For `DateField` and `DateTimeField` in related models:

```graphql
query {
  articles(filters: {
    author__created_at__exact: "2024-01-01"
    author__created_at__gt: "2024-01-01"
    author__created_at__gte: "2024-01-01T00:00:00Z"
    author__created_at__lt: "2024-12-31"
    author__created_at__lte: "2024-12-31T23:59:59Z"
    author__created_at__year: 2024
    author__created_at__month: 6
    author__created_at__day: 15
  }) {
    title
    author {
      createdAt
    }
  }
}
```

### Boolean Field Filters

For `BooleanField` in related models:

```graphql
query {
  users(filters: {
    profile__is_verified: true
    profile__is_verified__isnull: false
  }) {
    username
    profile {
      isVerified
    }
  }
}
```

### Foreign Key Filters

For nested foreign key relationships:

```graphql
query {
  posts(filters: {
    author__profile__country: 1  # Filter by country ID
    category__parent__name__icontains: "tech"
  }) {
    title
    author {
      profile {
        country {
          name
        }
      }
    }
  }
}
```

## Examples

### Example 1: E-commerce Product Filtering

```python
# Models
class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

class Brand(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
```

```graphql
query {
  products(filters: {
    # Filter by category name
    category__name__icontains: "electronics"
    
    # Filter by parent category
    category__parent__name__exact: "Technology"
    
    # Filter by brand country
    brand__country__icontains: "japan"
    
    # Filter by brand name and price range
    brand__name__in: ["Sony", "Nintendo"]
    price__range: [100, 500]
    
    # Filter by creation date
    created_at__year: 2024
  }) {
    name
    price
    category {
      name
      parent {
        name
      }
    }
    brand {
      name
      country
    }
  }
}
```

### Example 2: Blog System with Complex Relationships

```python
# Models
class Author(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

class Profile(models.Model):
    author = models.OneToOneField(Author, on_delete=models.CASCADE)
    bio = models.TextField()
    country = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)

class Category(models.Model):
    name = models.CharField(max_length=100)

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    published_at = models.DateTimeField()
    is_published = models.BooleanField(default=False)
```

```graphql
query {
  posts(filters: {
    # Filter by author details
    author__username__startswith: "john"
    author__email__endswith: "@example.com"
    author__created_at__year: 2023
    
    # Filter by author profile
    author__profile__country__icontains: "united"
    author__profile__is_verified: true
    author__profile__bio__icontains: "developer"
    
    # Filter by category
    category__name__in: ["Technology", "Programming"]
    
    # Filter by publication details
    is_published: true
    published_at__gte: "2024-01-01"
  }) {
    title
    publishedAt
    author {
      username
      profile {
        country
        isVerified
      }
    }
    category {
      name
    }
  }
}
```

### Example 3: Deep Nesting (3 levels)

```graphql
query {
  orders(filters: {
    # 3-level deep filtering
    customer__profile__address__city__icontains: "paris"
    customer__profile__address__country__code: "FR"
    
    # Mixed depth filtering
    customer__email__endswith: "@gmail.com"
    items__product__category__name: "Electronics"
    items__product__brand__country: "Japan"
  }) {
    id
    customer {
      email
      profile {
        address {
          city
          country {
            code
          }
        }
      }
    }
    items {
      product {
        name
        category {
          name
        }
        brand {
          country
        }
      }
    }
  }
}
```

## Performance Considerations

### Automatic Query Optimization

The system automatically suggests query optimizations:

```python
# The filter generator will log suggestions like:
# "Consider using select_related('author', 'author__profile') for better performance"
# "Consider using prefetch_related('author__posts') for reverse relationships"
```

### Manual Optimization

```python
# In your GraphQL resolver
def resolve_posts(self, info, **kwargs):
    queryset = Post.objects.select_related(
        'author',
        'author__profile',
        'category'
    ).prefetch_related(
        'author__posts',
        'comments'
    )
    
    # Apply filters
    filter_set = PostFilterSet(kwargs.get('filters', {}), queryset=queryset)
    return filter_set.qs
```

### Depth Limitations

- **Default maximum depth**: 3 levels
- **Maximum allowed depth**: 5 levels
- **Circular reference protection**: Automatic detection and prevention

## Best Practices

### 1. Use Appropriate Depth Limits

```python
# For simple applications
filter_generator = AdvancedFilterGenerator(max_nested_depth=2)

# For complex applications with deep relationships
filter_generator = AdvancedFilterGenerator(max_nested_depth=4)
```

### 2. Optimize Database Queries

```python
# Always use select_related for forward relationships
queryset = queryset.select_related('author', 'author__profile')

# Use prefetch_related for reverse relationships
queryset = queryset.prefetch_related('comments', 'tags')
```

### 3. Cache Filter Sets

```python
# Enable caching in settings
DJANGO_GRAPHQL_AUTO = {
    'FILTERING': {
        'CACHE_FILTER_SETS': True,
    }
}
```

### 4. Monitor Performance

```python
import logging

# Enable debug logging
logging.getLogger('django_graphql_auto.generators.filters').setLevel(logging.DEBUG)
```

### 5. Handle Large Datasets

```python
# Use pagination with nested filtering
query {
  posts(
    filters: {
      author__profile__country: "France"
    }
    first: 20
    after: "cursor_value"
  ) {
    edges {
      node {
        title
        author {
          username
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## Troubleshooting

### Common Issues

#### 1. Circular Reference Errors

**Problem**: Infinite recursion in model relationships

**Solution**: The system automatically detects and prevents circular references by limiting depth and tracking visited models.

#### 2. Performance Issues

**Problem**: Slow queries with nested filtering

**Solution**: 
- Use `select_related()` for forward relationships
- Use `prefetch_related()` for reverse relationships
- Reduce `max_nested_depth` if not needed

#### 3. Filter Not Working

**Problem**: Nested filter not applying correctly

**Solution**:
- Check field names match model field names
- Verify relationship exists in models
- Ensure `enable_nested_filters=True`

#### 4. Memory Issues

**Problem**: High memory usage with deep nesting

**Solution**:
- Reduce `max_nested_depth`
- Enable filter set caching
- Use pagination

### Debug Mode

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check generated filters
filter_generator = AdvancedFilterGenerator(max_nested_depth=3)
filter_set = filter_generator.generate_filter_set(Post)
print(f"Generated filters: {list(filter_set.base_filters.keys())}")
```

### Validation

```python
# Validate filter configuration
def validate_nested_filters(model, max_depth=3):
    generator = AdvancedFilterGenerator(max_nested_depth=max_depth)
    filter_set = generator.generate_filter_set(model)
    
    print(f"Model: {model.__name__}")
    print(f"Available filters: {len(filter_set.base_filters)}")
    
    for filter_name in sorted(filter_set.base_filters.keys()):
        print(f"  - {filter_name}")

# Usage
validate_nested_filters(Post)
```

## Advanced Configuration

### Custom Filter Depth per Model

```python
class CustomFilterGenerator(AdvancedFilterGenerator):
    def get_model_max_depth(self, model):
        """Override to set custom depth per model"""
        depth_config = {
            'User': 2,
            'Post': 3,
            'Order': 4,
        }
        return depth_config.get(model.__name__, self.max_nested_depth)
```

### Selective Nested Filtering

```python
class SelectiveFilterGenerator(AdvancedFilterGenerator):
    def should_include_nested_field(self, field, current_depth):
        """Override to selectively include nested fields"""
        # Skip certain field types
        if isinstance(field, models.TextField) and current_depth > 1:
            return False
        
        # Skip certain model relationships
        if field.related_model.__name__ in ['LogEntry', 'Session']:
            return False
            
        return super().should_include_nested_field(field, current_depth)
```

This comprehensive nested field filtering system provides powerful querying capabilities while maintaining performance and preventing common pitfalls like infinite recursion and N+1 queries.