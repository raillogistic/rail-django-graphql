# Advanced Filtering System

This document explains the comprehensive filtering capabilities of the Django GraphQL Auto-Generation Library, including basic filters, advanced operators, relationship filtering, and custom filter implementations.

## 📚 Table of Contents

- [Overview](#overview)
- [Basic Filtering](#basic-filtering)
- [Filter Operators](#filter-operators)
- [Relationship Filtering](#relationship-filtering)
- [Date and Time Filtering](#date-and-time-filtering)
- [Custom Filters](#custom-filters)
- [Performance Optimization](#performance-optimization)
- [Examples](#examples)

## 🔍 Overview

The filtering system automatically generates comprehensive filter inputs for all your Django models, supporting:

- **Basic field filtering** with multiple operators
- **Relationship filtering** across foreign keys and many-to-many fields
- **Date/time range filtering** with flexible operators
- **Custom filter logic** for complex business requirements
- **Performance optimization** with automatic query optimization

## 🎯 Basic Filtering

### Auto-Generated Filter Inputs

For each model, the system generates a corresponding filter input type:

```python
# Django Model
class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre du post")
    content = models.TextField(verbose_name="Contenu du post")
    published = models.BooleanField(default=False, verbose_name="Publié")
    view_count = models.IntegerField(default=0, verbose_name="Nombre de vues")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Auteur")

# Auto-Generated Filter Input
class PostFilterInput(graphene.InputObjectType):
    # Basic field filters
    title = graphene.String()
    title__icontains = graphene.String()
    title__startswith = graphene.String()
    title__endswith = graphene.String()

    content = graphene.String()
    content__icontains = graphene.String()

    published = graphene.Boolean()

    view_count = graphene.Int()
    view_count__gt = graphene.Int()
    view_count__gte = graphene.Int()
    view_count__lt = graphene.Int()
    view_count__lte = graphene.Int()
    view_count__in = graphene.List(graphene.Int)

    created_at = graphene.DateTime()
    created_at__gt = graphene.DateTime()
    created_at__gte = graphene.DateTime()
    created_at__lt = graphene.DateTime()
    created_at__lte = graphene.DateTime()
    created_at__range = graphene.List(graphene.DateTime)

    # Relationship filters
    author = UserFilterInput()
    author__id = graphene.ID()
    author__username = graphene.String()

    # Logical operators
    AND = graphene.List(lambda: PostFilterInput)
    OR = graphene.List(lambda: PostFilterInput)
    NOT = lambda: PostFilterInput
```

### Basic Usage

```graphql
query {
  posts(
    filters: {
      title__icontains: "django"
      published: true
      view_count__gte: 100
    }
  ) {
    id
    title
    view_count
    published
  }
}
```

## 🔧 Filter Operators

### String Field Operators

```python
# Available for CharField, TextField, etc.
STRING_OPERATORS = {
    'exact': 'Exact match',
    'iexact': 'Case-insensitive exact match',
    'contains': 'Contains substring',
    'icontains': 'Case-insensitive contains',
    'startswith': 'Starts with',
    'istartswith': 'Case-insensitive starts with',
    'endswith': 'Ends with',
    'iendswith': 'Case-insensitive ends with',
    'regex': 'Regular expression match',
    'iregex': 'Case-insensitive regex match',
    'in': 'Value in list',
    'isnull': 'Is null/empty',
}
```

#### String Filter Examples

```graphql
query {
  posts(
    filters: {
      # Exact match
      title: "Django Tutorial"
      # Case-insensitive contains
      title__icontains: "graphql"
      # Starts with
      title__startswith: "How to"
      # Multiple values
      title__in: ["Tutorial 1", "Tutorial 2", "Tutorial 3"]
      # Null check
      content__isnull: false
    }
  ) {
    id
    title
  }
}
```

### Numeric Field Operators

```python
# Available for IntegerField, FloatField, DecimalField, etc.
NUMERIC_OPERATORS = {
    'exact': 'Exact match',
    'gt': 'Greater than',
    'gte': 'Greater than or equal',
    'lt': 'Less than',
    'lte': 'Less than or equal',
    'range': 'Between two values',
    'in': 'Value in list',
    'isnull': 'Is null',
}
```

#### Numeric Filter Examples

```graphql
query {
  posts(
    filters: {
      # Greater than
      view_count__gt: 1000
      # Range
      view_count__range: [100, 500]
      # Multiple values
      view_count__in: [10, 50, 100, 200]
    }
  ) {
    id
    title
    view_count
  }
}
```

### Boolean Field Operators

```python
# Available for BooleanField
BOOLEAN_OPERATORS = {
    'exact': 'Exact match (true/false)',
    'isnull': 'Is null',
}
```

#### Boolean Filter Examples

```graphql
query {
  posts(filters: { published: true, featured__isnull: false }) {
    id
    title
    published
  }
}
```

## 🔗 Relationship Filtering

### Foreign Key Filtering

Filter by related model fields:

```graphql
query {
  posts(
    filters: {
      # Filter by author ID
      author__id: "1"
      # Filter by author username
      author__username: "john_doe"
      # Filter by author email domain
      author__email__endswith: "@company.com"
      # Nested relationship filtering
      author__profile__country: "US"
    }
  ) {
    id
    title
    author {
      username
      email
    }
  }
}
```

### Many-to-Many Filtering

```python
# Django Model
class Post(models.Model):
    title = models.CharField(max_length=200)
    tags = models.ManyToManyField(Tag, blank=True)
    categories = models.ManyToManyField(Category, blank=True)
```

```graphql
query {
  posts(
    filters: {
      # Posts with specific tag
      tags__name: "django"
      # Posts with tag ID in list
      tags__id__in: ["1", "2", "3"]
      # Posts in specific category
      categories__slug: "tutorials"
      # Posts with multiple conditions on related fields
      tags__name__icontains: "python"
      categories__is_active: true
    }
  ) {
    id
    title
    tags {
      name
    }
    categories {
      name
    }
  }
}
```

### Reverse Relationship Filtering

```python
# Filter users by their posts
query {
  users(filters: {
    # Users who have published posts
    posts__published: true

    # Users with posts containing specific content
    posts__title__icontains: "tutorial"

    # Users with posts created in date range
    posts__created_at__range: ["2024-01-01", "2024-12-31"]
  }) {
    id
    username
    posts {
      title
      published
    }
  }
}
```

## 📅 Date and Time Filtering

### DateTime Field Operators

```python
DATETIME_OPERATORS = {
    'exact': 'Exact datetime match',
    'date': 'Date part match',
    'year': 'Year match',
    'month': 'Month match',
    'day': 'Day match',
    'week': 'Week of year',
    'week_day': 'Day of week (1=Sunday)',
    'quarter': 'Quarter of year',
    'time': 'Time part match',
    'hour': 'Hour match',
    'minute': 'Minute match',
    'second': 'Second match',
    'gt': 'Greater than',
    'gte': 'Greater than or equal',
    'lt': 'Less than',
    'lte': 'Less than or equal',
    'range': 'Between two datetimes',
    'isnull': 'Is null',
}
```

### Date Filtering Examples

```graphql
query {
  posts(
    filters: {
      # Exact date
      created_at__date: "2024-01-15"
      # Year filtering
      created_at__year: 2024
      # Month filtering
      created_at__month: 1
      # Date range
      created_at__range: ["2024-01-01T00:00:00Z", "2024-01-31T23:59:59Z"]
      # Recent posts (last 7 days)
      created_at__gte: "2024-01-08T00:00:00Z"
      # Posts from specific weekday (Monday = 2)
      created_at__week_day: 2
      # Posts from Q1
      created_at__quarter: 1
    }
  ) {
    id
    title
    created_at
  }
}
```

### Time-based Filtering Helpers

The system provides convenient time-based filters:

```graphql
query {
  posts(
    filters: {
      # Predefined time ranges
      created_at__today: true
      created_at__yesterday: true
      created_at__this_week: true
      created_at__this_month: true
      created_at__this_year: true
      # Relative time filtering
      created_at__days_ago: 7 # Posts from 7 days ago
      created_at__hours_ago: 24 # Posts from 24 hours ago
    }
  ) {
    id
    title
    created_at
  }
}
```

## 🔍 Logical Operators

### AND, OR, NOT Operations

```graphql
query {
  posts(
    filters: {
      # AND operation (default behavior)
      title__icontains: "django"
      published: true
      # Explicit OR operation
      OR: [{ title__icontains: "django" }, { title__icontains: "graphql" }]
      # NOT operation
      NOT: { author__username: "spam_user" }
      # Complex nested logic
      AND: [
        {
          OR: [{ title__icontains: "tutorial" }, { title__icontains: "guide" }]
        }
        { NOT: { tags__name: "deprecated" } }
      ]
    }
  ) {
    id
    title
    author {
      username
    }
  }
}
```

## 🎨 Custom Filters

### FilterSet Class

Create custom filter logic using the `FilterSet` class:

```python
# filters.py
from rail_django_graphql.filtering.base import FilterSet
from rail_django_graphql.filtering.fields import FilterField
import graphene

class PostFilterSet(FilterSet):
    class Meta:
        model = Post
        fields = '__all__'

    # Custom filter fields
    search = graphene.String()
    popular = graphene.Boolean()
    author_type = graphene.String()
    content_length = graphene.String()  # 'short', 'medium', 'long'

    def filter_search(self, queryset, name, value):
        """Full-text search across multiple fields."""
        if value:
            return queryset.filter(
                Q(title__icontains=value) |
                Q(content__icontains=value) |
                Q(tags__name__icontains=value)
            ).distinct()
        return queryset

    def filter_popular(self, queryset, name, value):
        """Filter popular posts based on view count and likes."""
        if value:
            return queryset.filter(
                Q(view_count__gte=1000) |
                Q(likes__gte=100)
            )
        return queryset

    def filter_author_type(self, queryset, name, value):
        """Filter by author type (staff, premium, regular)."""
        if value == 'staff':
            return queryset.filter(author__is_staff=True)
        elif value == 'premium':
            return queryset.filter(author__profile__is_premium=True)
        elif value == 'regular':
            return queryset.filter(
                author__is_staff=False,
                author__profile__is_premium=False
            )
        return queryset

    def filter_content_length(self, queryset, name, value):
        """Filter by content length categories."""
        if value == 'short':
            return queryset.extra(
                where=["CHAR_LENGTH(content) < 500"]
            )
        elif value == 'medium':
            return queryset.extra(
                where=["CHAR_LENGTH(content) BETWEEN 500 AND 2000"]
            )
        elif value == 'long':
            return queryset.extra(
                where=["CHAR_LENGTH(content) > 2000"]
            )
        return queryset

# Register custom filter
rail_django_graphql = {
    'CUSTOM_FILTERS': {
        'Post': 'myapp.filters.PostFilterSet',
    }
}
```

### Using Custom Filters

```graphql
query {
  posts(
    filters: {
      # Use custom search filter
      search: "django graphql tutorial"
      # Use custom popular filter
      popular: true
      # Use custom author type filter
      author_type: "staff"
      # Use custom content length filter
      content_length: "long"
      # Combine with standard filters
      published: true
      created_at__gte: "2024-01-01"
    }
  ) {
    id
    title
    view_count
    author {
      username
      is_staff
    }
  }
}
```

## 🚀 Performance Optimization

### Automatic Query Optimization

The filtering system includes several performance optimizations:

```python
class OptimizedFilterSet(FilterSet):
    def optimize_queryset(self, queryset, filters):
        """Automatically optimize queryset based on filters."""

        # Add select_related for foreign key filters
        if any(key.startswith('author__') for key in filters.keys()):
            queryset = queryset.select_related('author', 'author__profile')

        # Add prefetch_related for many-to-many filters
        if any(key.startswith('tags__') for key in filters.keys()):
            queryset = queryset.prefetch_related('tags')

        if any(key.startswith('categories__') for key in filters.keys()):
            queryset = queryset.prefetch_related('categories')

        return queryset
```

### Database Indexes

The system can suggest database indexes for optimal performance:

```python
# Generated index suggestions
class Post(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    published = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    view_count = models.IntegerField(default=0, db_index=True)

    class Meta:
        indexes = [
            # Composite indexes for common filter combinations
            models.Index(fields=['published', 'created_at']),
            models.Index(fields=['author', 'published']),
            models.Index(fields=['view_count', 'created_at']),
        ]
```

### Filter Caching

Enable filter result caching for expensive operations:

```python
rail_django_graphql = {
    'ENABLE_FILTER_CACHING': True,
    'FILTER_CACHE_TIMEOUT': 300,  # 5 minutes
    'FILTER_CACHE_KEY_PREFIX': 'graphql_filter',
}
```

## 📊 Complex Filter Examples

### E-commerce Product Filtering

```graphql
query {
  products(
    filters: {
      # Price range
      price__range: [10.00, 100.00]
      # In stock only
      stock_quantity__gt: 0
      # Specific categories
      categories__slug__in: ["electronics", "computers"]
      # Brand filtering
      brand__name__in: ["Apple", "Samsung", "Google"]
      # Rating filtering
      average_rating__gte: 4.0
      # Discount filtering
      discount_percentage__gt: 10
      # Search in name and description
      OR: [
        { name__icontains: "smartphone" }
        { description__icontains: "smartphone" }
      ]
      # Exclude out of stock
      NOT: { stock_quantity: 0 }
    }
  ) {
    id
    name
    price
    stock_quantity
    average_rating
    brand {
      name
    }
    categories {
      name
    }
  }
}
```

### Blog Post Advanced Filtering

```graphql
query {
  posts(
    filters: {
      # Published posts only
      published: true
      # From last 30 days
      created_at__gte: "2024-01-01"
      # Popular posts
      OR: [
        { view_count__gte: 1000 }
        { likes_count__gte: 50 }
        { comments_count__gte: 10 }
      ]
      # Specific authors or author types
      OR: [
        { author__is_staff: true }
        { author__username__in: ["john_doe", "jane_smith"] }
      ]
      # Content filters
      AND: [
        { title__icontains: "tutorial" }
        { content_length: "long" }
        { NOT: { tags__name: "deprecated" } }
      ]
      # Language and region
      language: "en"
      author__profile__country: "US"
    }
  ) {
    id
    title
    view_count
    likes_count
    comments_count
    author {
      username
      is_staff
    }
    tags {
      name
    }
  }
}
```

### User Management Filtering

```graphql
query {
  users(
    filters: {
      # Active users only
      is_active: true
      # Joined in the last year
      date_joined__gte: "2023-01-01"
      # Users with specific roles
      OR: [
        { is_staff: true }
        { groups__name: "premium_users" }
        { user_permissions__codename: "can_publish" }
      ]
      # Profile-based filtering
      profile__country__in: ["US", "CA", "UK"]
      profile__age__range: [18, 65]
      profile__is_verified: true
      # Activity-based filtering
      posts__published: true
      posts__created_at__gte: "2024-01-01"
      # Exclude inactive or banned users
      NOT: { OR: [{ is_active: false }, { profile__is_banned: true }] }
    }
  ) {
    id
    username
    email
    date_joined
    is_staff
    profile {
      country
      age
      is_verified
    }
    posts {
      title
      published
    }
  }
}
```

## 🔧 Configuration Options

### Global Filter Configuration

```python
# settings.py
rail_django_graphql = {
    'FILTERING': {
        'ENABLE_FILTERS': True,
        'DEFAULT_FILTER_OPERATORS': {
            'CharField': ['exact', 'icontains', 'startswith', 'endswith'],
            'IntegerField': ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
            'BooleanField': ['exact'],
            'DateTimeField': ['exact', 'gt', 'gte', 'lt', 'lte', 'range', 'date'],
        },
        'ENABLE_LOGICAL_OPERATORS': True,
        'ENABLE_RELATIONSHIP_FILTERS': True,
        'MAX_FILTER_DEPTH': 3,
        'ENABLE_CUSTOM_FILTERS': True,
    }
}
```

### Per-Model Filter Configuration

```python
# models.py
class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()

    class GraphQLMeta:
        filter_fields = {
            'title': ['exact', 'icontains', 'startswith'],
            'content': ['icontains'],
            'created_at': ['exact', 'gt', 'gte', 'date', 'range'],
        }

        # Exclude certain fields from filtering
        filter_exclude = ['internal_notes', 'draft_content']

        # Custom filter class
        filter_class = 'myapp.filters.PostFilterSet'
```

## 🚀 Next Steps

Now that you understand filtering:

1. [Learn About Mutations](mutations.md) - CRUD operations and data manipulation
2. [Explore Nested Operations](nested-operations.md) - Complex nested create/update operations
3. [Check Custom Scalars](../advanced/custom-scalars.md) - Custom data types and validation
4. [Review Performance Guide](../development/performance.md) - Optimization techniques

## 🤝 Need Help?

- Check the [Troubleshooting Guide](../development/troubleshooting.md)
- Review [Filter Examples](../examples/filtering-examples.md)
- Join our [Community Discussions](https://github.com/your-repo/django-graphql-auto/discussions)
