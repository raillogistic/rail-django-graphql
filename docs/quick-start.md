# 🚀 Quick Start Guide

Get up and running with the Django GraphQL Auto-Generation Library in just a few minutes!

## Prerequisites

- Python 3.8+
- Django 3.2+
- Basic knowledge of Django and GraphQL

## 1. Installation

```bash
pip install django-graphql-auto
```

## 2. Django Configuration

Add to your `settings.py`:

```python
INSTALLED_APPS = [
    # ... your other apps
    'graphene_django',
    'django_graphql_auto',
    'corsheaders',  # For frontend integration
]

# GraphQL Configuration
GRAPHENE = {
    'SCHEMA': 'django_graphql_auto.schema.schema'
}

# Auto-generation settings
DJANGO_GRAPHQL_AUTO = {
    'APPS': ['your_app'],  # Apps to generate schema for
    'AUTO_GENERATE': True,
    'ENABLE_FILTERING': True,
    'ENABLE_PAGINATION': True,
    'MUTATION_SETTINGS': {
        'enable_method_mutations': True,  # Enable method mutations
        'enable_bulk_operations': True,   # Enable bulk operations
        'bulk_batch_size': 100,          # Batch size for bulk operations
        'enable_nested_relations': True,  # Enable nested operations
    },
    # Performance Optimization Settings (Phase 5)
    'PERFORMANCE': {
        'ENABLE_QUERY_OPTIMIZATION': True,    # Enable automatic N+1 prevention
        'ENABLE_CACHING': True,               # Enable multi-level caching
        'ENABLE_PERFORMANCE_MONITORING': True, # Enable performance monitoring
        'CACHE_BACKEND': 'redis',             # Cache backend (redis, memcached, database)
        'CACHE_TTL': 300,                     # Default cache TTL in seconds
        'MAX_QUERY_COMPLEXITY': 1000,        # Maximum query complexity
        'ENABLE_QUERY_ANALYSIS': True,       # Enable query analysis
    }
}

# CORS (for frontend integration)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React default
    "http://127.0.0.1:3000",
]
```

## 3. URL Configuration

Add to your main `urls.py`:

```python
from django.urls import path, include
from graphene_django.views import GraphQLView
from django_graphql_auto.middleware import setup_performance_monitoring

# Setup performance monitoring (optional but recommended)
setup_performance_monitoring()

urlpatterns = [
    # ... your other URLs
    path('graphql/', GraphQLView.as_view(graphiql=True)),
    # Performance monitoring endpoint (optional)
    path('graphql/performance/', include('django_graphql_auto.urls')),
]
```

## 4. Create Your Models

```python
# models.py
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='posts')
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    # Custom methods that will become GraphQL mutations
    def publish_post(self):
        """Publier le post (Publish the post)"""
        self.published = True
        self.save()
        return self
    
    def archive_post(self):
        """Archiver le post (Archive the post)"""
        self.published = False
        self.save()
        return self

# Optional: Use performance optimization decorators for custom methods
from django_graphql_auto import optimize_query, cache_query

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, verbose_name="Description")
    
    @optimize_query  # Automatically optimize N+1 queries
    def get_popular_posts(self):
        """Obtenir les posts populaires de cette catégorie"""
        return self.posts.filter(published=True).order_by('-created_at')[:10]
    
    @cache_query(ttl=300)  # Cache for 5 minutes
    def get_post_count(self):
        """Obtenir le nombre de posts dans cette catégorie"""
        return self.posts.filter(published=True).count()
```

## 5. Generate Schema & Run Performance Benchmarks

```bash
python manage.py migrate
python manage.py generate_graphql_schema

# Optional: Run performance benchmarks to test optimization
python manage.py run_performance_benchmarks --test-type all --output-dir benchmarks/
```

## 6. Test Your API

Start the development server:

```bash
python manage.py runserver
```

Visit `http://localhost:8000/graphql/` and try these queries:

### Query All Authors
```graphql
query {
  authors {
    edges {
      node {
        id
        name
        email
        posts {
          edges {
            node {
              title
              published
            }
          }
        }
      }
    }
  }
}
```

### Create a New Author
```graphql
mutation {
  createAuthor(input: {
    name: "John Doe"
    email: "john@example.com"
    bio: "A passionate writer"
  }) {
    author {
      id
      name
      email
    }
    success
    errors
  }
}
```

### Create a Post
```graphql
mutation {
  createPost(input: {
    title: "My First Post"
    content: "This is the content of my first post"
    authorId: "1"  # Use the ID from the author you created
    published: true
  }) {
    post {
      id
      title
      author {
        name
      }
    }
    success
    errors
  }
}
```

### Use Method Mutations
```graphql
mutation {
  postPublishPost(input: {
    id: "1"  # ID of the post to publish
  }) {
    ok
    post {
      id
      title
      published
    }
    errors
  }
}
```

### Bulk Create Posts
```graphql
mutation {
  bulkCreatePost(input: {
    objects: [
      {
        title: "Post 1"
        content: "Content for post 1"
        authorId: "1"
      },
      {
        title: "Post 2"
        content: "Content for post 2"
        authorId: "1"
      }
    ]
  }) {
    ok
    objects {
      id
      title
    }
    errors
  }
}
```
### Query with Filtering and Performance Optimization
```graphql
# This query automatically benefits from N+1 prevention and caching
query {
  posts(published: true, title_Icontains: "first") {
    edges {
      node {
        title
        content
        author {
          name
          email  # No N+1 queries thanks to automatic optimization
        }
        createdAt
      }
    }
  }
}
```

### Performance Monitoring Query
```graphql
# Check query performance metrics
query {
  __performance {
    queryCount
    executionTime
    cacheHits
    cacheMisses
  }
}
```

## 🎉 That's It!

You now have a fully functional GraphQL API with:
- ✅ Automatic schema generation
- ✅ CRUD operations for all models
- ✅ Method mutations for custom model methods
- ✅ Bulk operations for efficient data handling
- ✅ Relationship handling
- ✅ Filtering and pagination
- ✅ GraphiQL interface for testing
- ✅ **N+1 Query Prevention** - Automatic optimization of database queries
- ✅ **Multi-Level Caching** - Schema, query, and field-level caching
- ✅ **Performance Monitoring** - Real-time performance metrics and alerts
- ✅ **Query Complexity Control** - Protection against expensive queries
- ✅ **Benchmarking Tools** - Performance testing and optimization

## Next Steps

1. **[📖 Read the Full Documentation](index.md)** - Learn about all features
2. **[⚡ Explore Performance Optimization](performance-optimization.md)** - Deep dive into N+1 prevention, caching, and monitoring
3. **[🔧 Advanced Features](advanced/)** - Custom scalars, inheritance, nested operations
4. **[💡 Check Out Examples](examples/)** - Real-world usage patterns
5. **[📊 Performance Benchmarking](development/performance.md)** - Best practices for production optimization

## Common Issues

### Schema Not Generating?
- Make sure your app is in `DJANGO_GRAPHQL_AUTO['APPS']`
- Run `python manage.py generate_graphql_schema` after model changes
- Check the console for any error messages

### CORS Issues?
- Add your frontend URL to `CORS_ALLOWED_ORIGINS`
- Install `django-cors-headers` if not already installed

### GraphiQL Not Loading?
- Ensure `graphiql=True` in your GraphQLView
- Check that you're accessing the correct URL (`/graphql/`)

### Performance Issues?
- Check query complexity with `python manage.py run_performance_benchmarks`
- Enable caching in `DJANGO_GRAPHQL_AUTO['PERFORMANCE']` settings
- Monitor performance at `/graphql/performance/` endpoint
- Review N+1 query prevention in the performance documentation

## Need Help?

- 📚 [Full Documentation](index.md)
- 🛠️ [Troubleshooting Guide](development/troubleshooting.md)
- 💬 [Contributing Guide](CONTRIBUTING.md)

---

**Happy coding!** 🚀