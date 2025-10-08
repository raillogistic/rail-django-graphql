# GraphQLMeta Configuration Guide

This guide covers the `GraphQLMeta` class, which provides advanced configuration options for customizing GraphQL schema generation, filtering, and query behavior for Django models.

## 📚 Table of Contents

- [Overview](#overview)
- [Basic Configuration](#basic-configuration)
- [Custom Resolvers](#custom-resolvers)
- [Custom Filters](#custom-filters)
- [Quick Filter](#quick-filter)
- [Date/DateTime Filters](#datetime-filters)
- [Field Configuration](#field-configuration)
- [Complete Examples](#complete-examples)
- [Best Practices](#best-practices)

## 🔍 Overview

The `GraphQLMeta` class allows you to extend and customize the GraphQL schema generation for your Django models. It provides fine-grained control over:

- **Custom Resolvers**: Intercept and modify model queries
- **Custom Filters**: Define specialized filtering logic
- **Quick Filter**: Enable cross-field search functionality
- **Field Configuration**: Control field inclusion, exclusion, and behavior
- **Date/DateTime Filters**: Built-in time-based filtering options

## 🚀 Basic Configuration

### Adding GraphQLMeta to Your Model

```python
from django.db import models
from rail_django_graphql.core.meta import GraphQLMeta

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    published_date = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=False)
    tags = models.ManyToManyField('Tag', blank=True)

    class GraphQLMeta(GraphQLMeta):
        # Basic field configuration
        exclude_fields = ['internal_notes']
        include_fields = ['title', 'content', 'author', 'published_date']
        
        # Enable filtering and ordering
        filter_fields = {
            'title': ['exact', 'icontains', 'startswith'],
            'is_published': ['exact'],
            'published_date': ['exact', 'gt', 'lt', 'range'],
            'author': ['exact'],
            'category': ['exact', 'in'],
        }
        
        ordering_fields = ['title', 'published_date', 'author__username']
```

## 🔧 Custom Resolvers

Custom resolvers allow you to intercept and modify queries before they're executed:

```python
from django.db.models import Q, Count
from django_filters import CharFilter

class BlogPost(models.Model):
    # ... model fields ...

    class GraphQLMeta(GraphQLMeta):
        custom_resolvers = {
            'popular_posts': 'get_popular_posts',
            'recent_posts': 'get_recent_posts',
            'author_posts': 'get_posts_by_author',
        }

    @classmethod
    def get_popular_posts(cls, queryset, info, **kwargs):
        """Get posts with high engagement."""
        return queryset.annotate(
            comment_count=Count('comments')
        ).filter(
            comment_count__gte=10,
            is_published=True
        ).order_by('-comment_count')

    @classmethod
    def get_recent_posts(cls, queryset, info, **kwargs):
        """Get posts from the last 30 days."""
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        return queryset.filter(
            published_date__gte=thirty_days_ago,
            is_published=True
        ).order_by('-published_date')

    @classmethod
    def get_posts_by_author(cls, queryset, info, author_id=None, **kwargs):
        """Get posts by specific author."""
        if author_id:
            return queryset.filter(author_id=author_id, is_published=True)
        return queryset.filter(is_published=True)
```

### Using Custom Resolvers in GraphQL

```graphql
query {
  # Using custom resolvers
  popularPosts {
    edges {
      node {
        title
        commentCount
        author {
          username
        }
      }
    }
  }
  
  recentPosts {
    edges {
      node {
        title
        publishedDate
      }
    }
  }
  
  authorPosts(authorId: 1) {
    edges {
      node {
        title
        author {
          username
        }
      }
    }
  }
}
```

## 🎯 Custom Filters

Define specialized filtering logic for complex use cases:

```python
from django_filters import CharFilter, NumberFilter, BooleanFilter

class BlogPost(models.Model):
    # ... model fields ...

    class GraphQLMeta(GraphQLMeta):
        custom_filters = {
            'content_length': CharFilter(method='filter_by_content_length'),
            'has_tags': BooleanFilter(method='filter_has_tags'),
            'tag_count': NumberFilter(method='filter_by_tag_count'),
            'author_active': BooleanFilter(method='filter_by_author_active'),
        }

    @classmethod
    def filter_by_content_length(cls, queryset, name, value):
        """Filter by content length (short, medium, long)."""
        if value == 'short':
            return queryset.extra(where=["LENGTH(content) < 500"])
        elif value == 'medium':
            return queryset.extra(where=["LENGTH(content) BETWEEN 500 AND 2000"])
        elif value == 'long':
            return queryset.extra(where=["LENGTH(content) > 2000"])
        return queryset

    @classmethod
    def filter_has_tags(cls, queryset, name, value):
        """Filter posts that have or don't have tags."""
        if value:
            return queryset.filter(tags__isnull=False).distinct()
        return queryset.filter(tags__isnull=True)

    @classmethod
    def filter_by_tag_count(cls, queryset, name, value):
        """Filter by number of tags."""
        return queryset.annotate(
            tag_count=Count('tags')
        ).filter(tag_count=value)

    @classmethod
    def filter_by_author_active(cls, queryset, name, value):
        """Filter by author's active status."""
        return queryset.filter(author__is_active=value)
```

### Using Custom Filters in GraphQL

```graphql
query {
  blogPosts(
    contentLength: "medium"
    hasTags: true
    tagCount: 3
    authorActive: true
  ) {
    edges {
      node {
        title
        content
        tags {
          edges {
            node {
              name
            }
          }
        }
        author {
          username
          isActive
        }
      }
    }
  }
}
```

## ⚡ Quick Filter

The quick filter enables cross-field search functionality:

```python
class BlogPost(models.Model):
    # ... model fields ...

    class GraphQLMeta(GraphQLMeta):
        # Enable quick filter across multiple fields
        quick_filter_fields = [
            'title',
            'content',
            'author__username',
            'author__first_name',
            'author__last_name',
            'category__name',
            'tags__name',
        ]
        
        # Additional filter configuration
        filter_fields = {
            'quick': ['icontains'],  # This enables the quick filter
            'title': ['exact', 'icontains'],
            'is_published': ['exact'],
        }
```

### Using Quick Filter in GraphQL

```graphql
query {
  # Search across title, content, author name, category, and tags
  blogPosts(quick: "django tutorial") {
    edges {
      node {
        title
        content
        author {
          username
          firstName
          lastName
        }
        category {
          name
        }
        tags {
          edges {
            node {
              name
            }
          }
        }
      }
    }
  }
}
```

## 📅 Date/DateTime Filters

Built-in time-based filtering options are automatically generated for date and datetime fields:

```python
class BlogPost(models.Model):
    published_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    scheduled_date = models.DateField(null=True, blank=True)

    class GraphQLMeta(GraphQLMeta):
        filter_fields = {
            'published_date': ['exact', 'gt', 'lt', 'range'],
            'updated_date': ['exact', 'gt', 'lt'],
            'scheduled_date': ['exact', 'gt', 'lt'],
        }
```

### Available Date/DateTime Filters

For each date/datetime field, the following filters are automatically generated:

- `fieldname_today` - Filter for today's date
- `fieldname_yesterday` - Filter for yesterday's date
- `fieldname_this_week` - Filter for this week (Monday to Sunday)
- `fieldname_past_week` - Filter for past week
- `fieldname_this_month` - Filter for current month
- `fieldname_past_month` - Filter for previous month
- `fieldname_this_year` - Filter for current year
- `fieldname_past_year` - Filter for previous year

### Using Date/DateTime Filters in GraphQL

```graphql
query {
  # Posts published today
  todayPosts: blogPosts(publishedDateToday: true) {
    edges {
      node {
        title
        publishedDate
      }
    }
  }
  
  # Posts published this week
  thisWeekPosts: blogPosts(publishedDateThisWeek: true) {
    edges {
      node {
        title
        publishedDate
      }
    }
  }
  
  # Posts updated this month
  recentlyUpdated: blogPosts(updatedDateThisMonth: true) {
    edges {
      node {
        title
        updatedDate
      }
    }
  }
  
  # Posts scheduled for this year
  scheduledPosts: blogPosts(scheduledDateThisYear: true) {
    edges {
      node {
        title
        scheduledDate
      }
    }
  }
}
```

## ⚙️ Field Configuration

Control field behavior and inclusion:

```python
class BlogPost(models.Model):
    # ... model fields ...

    class GraphQLMeta(GraphQLMeta):
        # Field inclusion/exclusion
        include_fields = ['title', 'content', 'author', 'published_date']
        exclude_fields = ['internal_notes', 'admin_comments']
        
        # Field-specific configuration
        field_config = {
            'content': {
                'description': 'The main content of the blog post',
                'deprecation_reason': None,
            },
            'author': {
                'description': 'The author of this blog post',
                'required': True,
            },
        }
        
        # Relationship configuration
        relationship_config = {
            'comments': {
                'max_depth': 2,
                'enable_filtering': True,
                'enable_ordering': True,
            },
            'tags': {
                'enable_filtering': True,
                'prefetch_related': True,
            },
        }
```

## 📋 Complete Examples

### E-commerce Product Model

```python
from django.db import models
from rail_django_graphql.core.meta import GraphQLMeta

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    brand = models.ForeignKey('Brand', on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    stock_quantity = models.IntegerField(default=0)
    tags = models.ManyToManyField('Tag', blank=True)

    class GraphQLMeta(GraphQLMeta):
        # Quick search across multiple fields
        quick_filter_fields = [
            'name',
            'description',
            'category__name',
            'brand__name',
            'tags__name',
        ]
        
        # Custom resolvers
        custom_resolvers = {
            'featured_products': 'get_featured_products',
            'on_sale_products': 'get_on_sale_products',
            'low_stock_products': 'get_low_stock_products',
        }
        
        # Custom filters
        custom_filters = {
            'price_range': 'filter_by_price_range',
            'in_stock': 'filter_in_stock',
            'popular': 'filter_popular_products',
        }
        
        # Standard filters
        filter_fields = {
            'name': ['exact', 'icontains', 'startswith'],
            'price': ['exact', 'gt', 'lt', 'range'],
            'category': ['exact', 'in'],
            'brand': ['exact', 'in'],
            'is_active': ['exact'],
            'stock_quantity': ['exact', 'gt', 'lt'],
            'created_date': ['exact', 'gt', 'lt', 'range'],
        }
        
        ordering_fields = ['name', 'price', 'created_date', 'stock_quantity']

    @classmethod
    def get_featured_products(cls, queryset, info, **kwargs):
        """Get featured products."""
        return queryset.filter(
            is_active=True,
            stock_quantity__gt=0,
            tags__name='featured'
        ).distinct()

    @classmethod
    def get_on_sale_products(cls, queryset, info, **kwargs):
        """Get products on sale."""
        return queryset.filter(
            is_active=True,
            tags__name='sale'
        ).distinct()

    @classmethod
    def get_low_stock_products(cls, queryset, info, **kwargs):
        """Get products with low stock."""
        return queryset.filter(
            is_active=True,
            stock_quantity__lt=10,
            stock_quantity__gt=0
        )

    @classmethod
    def filter_by_price_range(cls, queryset, name, value):
        """Filter by price range (budget, mid, premium)."""
        if value == 'budget':
            return queryset.filter(price__lt=50)
        elif value == 'mid':
            return queryset.filter(price__gte=50, price__lt=200)
        elif value == 'premium':
            return queryset.filter(price__gte=200)
        return queryset

    @classmethod
    def filter_in_stock(cls, queryset, name, value):
        """Filter products in stock."""
        if value:
            return queryset.filter(stock_quantity__gt=0)
        return queryset.filter(stock_quantity=0)

    @classmethod
    def filter_popular_products(cls, queryset, name, value):
        """Filter popular products based on order count."""
        if value:
            return queryset.annotate(
                order_count=Count('orderitem')
            ).filter(order_count__gte=10)
        return queryset
```

### User Profile Model

```python
class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=True)

    class GraphQLMeta(GraphQLMeta):
        # Quick search
        quick_filter_fields = [
            'user__username',
            'user__first_name',
            'user__last_name',
            'user__email',
            'bio',
            'location',
        ]
        
        # Custom resolvers
        custom_resolvers = {
            'active_users': 'get_active_users',
            'recent_joiners': 'get_recent_joiners',
        }
        
        # Custom filters
        custom_filters = {
            'age_range': 'filter_by_age_range',
            'has_website': 'filter_has_website',
        }
        
        # Standard filters
        filter_fields = {
            'user__username': ['exact', 'icontains'],
            'user__is_active': ['exact'],
            'location': ['exact', 'icontains'],
            'is_public': ['exact'],
            'birth_date': ['exact', 'gt', 'lt'],
            'created_date': ['exact', 'gt', 'lt'],
        }

    @classmethod
    def get_active_users(cls, queryset, info, **kwargs):
        """Get profiles of active users."""
        return queryset.filter(
            user__is_active=True,
            is_public=True
        )

    @classmethod
    def get_recent_joiners(cls, queryset, info, **kwargs):
        """Get profiles of users who joined recently."""
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.now() - timedelta(days=30)
        return queryset.filter(
            created_date__gte=thirty_days_ago,
            is_public=True
        )

    @classmethod
    def filter_by_age_range(cls, queryset, name, value):
        """Filter by age range."""
        from datetime import date, timedelta
        today = date.today()
        
        if value == 'teen':
            start_date = today - timedelta(days=365*19)
            end_date = today - timedelta(days=365*13)
        elif value == 'young_adult':
            start_date = today - timedelta(days=365*35)
            end_date = today - timedelta(days=365*20)
        elif value == 'adult':
            start_date = today - timedelta(days=365*65)
            end_date = today - timedelta(days=365*36)
        else:
            return queryset
            
        return queryset.filter(
            birth_date__gte=start_date,
            birth_date__lte=end_date
        )

    @classmethod
    def filter_has_website(cls, queryset, name, value):
        """Filter profiles with or without website."""
        if value:
            return queryset.exclude(website='')
        return queryset.filter(website='')
```

## 🎯 Best Practices

### 1. Performance Considerations

```python
class GraphQLMeta(GraphQLMeta):
    # Use select_related for foreign keys
    select_related = ['author', 'category']
    
    # Use prefetch_related for many-to-many and reverse foreign keys
    prefetch_related = ['tags', 'comments']
    
    # Limit quick filter fields to essential ones
    quick_filter_fields = ['title', 'content']  # Don't include too many
    
    # Use database indexes for filtered fields
    filter_fields = {
        'published_date': ['exact', 'gt', 'lt'],  # Ensure DB index exists
        'is_published': ['exact'],  # Boolean fields are usually indexed
    }
```

### 2. Security Considerations

```python
class GraphQLMeta(GraphQLMeta):
    # Exclude sensitive fields
    exclude_fields = ['internal_notes', 'admin_comments', 'secret_key']
    
    # Implement permission checks in custom resolvers
    @classmethod
    def get_admin_posts(cls, queryset, info, **kwargs):
        """Only allow admin users to access this resolver."""
        if not info.context.user.is_staff:
            return queryset.none()
        return queryset.filter(is_admin_post=True)
```

### 3. Maintainability

```python
class GraphQLMeta(GraphQLMeta):
    # Group related configurations
    quick_filter_fields = [
        # User-related fields
        'author__username',
        'author__first_name',
        'author__last_name',
        
        # Content fields
        'title',
        'content',
        
        # Category fields
        'category__name',
    ]
    
    # Use descriptive method names
    custom_resolvers = {
        'published_posts': 'get_published_posts',
        'draft_posts': 'get_draft_posts',
        'featured_posts': 'get_featured_posts',
    }
    
    # Document complex filters
    custom_filters = {
        'engagement_level': 'filter_by_engagement_level',  # High/Medium/Low engagement
        'content_type': 'filter_by_content_type',  # Article/Tutorial/News
    }
```

### 4. Testing Custom Logic

```python
# tests/test_graphql_meta.py
from django.test import TestCase
from myapp.models import BlogPost

class GraphQLMetaTest(TestCase):
    def test_popular_posts_resolver(self):
        """Test the popular posts custom resolver."""
        # Create test data
        post1 = BlogPost.objects.create(title="Popular Post", is_published=True)
        post2 = BlogPost.objects.create(title="Unpopular Post", is_published=True)
        
        # Add comments to make post1 popular
        for i in range(15):
            post1.comments.create(content=f"Comment {i}")
        
        # Test the resolver
        queryset = BlogPost.objects.all()
        popular_posts = BlogPost.get_popular_posts(queryset, None)
        
        self.assertIn(post1, popular_posts)
        self.assertNotIn(post2, popular_posts)

    def test_quick_filter(self):
        """Test the quick filter functionality."""
        post1 = BlogPost.objects.create(title="Django Tutorial", content="Learn Django")
        post2 = BlogPost.objects.create(title="Python Guide", content="Learn Python")
        
        # Test quick filter
        # This would be tested through GraphQL queries in integration tests
        pass
```

## 🔗 Related Documentation

- [Basic Usage Guide](basic-usage.md) - Learn the fundamentals
- [Advanced Usage Guide](advanced-usage.md) - Advanced patterns and API reference
- [Filtering Guide](../features/filtering.md) - Detailed filtering documentation
- [Performance Guide](../development/performance.md) - Performance optimization tips
- [Security Guide](../features/security.md) - Security best practices

---

**Next Steps:**
1. Try implementing `GraphQLMeta` in your models
2. Experiment with custom resolvers and filters
3. Test the quick filter functionality
4. Explore the date/datetime filters
5. Check out the [Advanced Usage Guide](advanced-usage.md) for more patterns