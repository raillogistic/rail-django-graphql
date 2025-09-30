# Advanced Usage Guide

This guide covers advanced usage patterns, API reference, and schema generation examples for the Django GraphQL Auto-Generation Library.

## 📚 Table of Contents

- [Schema Generation](#schema-generation)
- [Advanced Queries](#advanced-queries)
- [Complex Mutations](#complex-mutations)
- [File Upload Operations](#file-upload-operations)
- [Authentication & Permissions](#authentication--permissions)
- [Performance Optimization](#performance-optimization)
- [Custom Extensions](#custom-extensions)
- [API Reference](#api-reference)

## 🏗️ Schema Generation

### Automatic Schema Generation

The library automatically generates GraphQL schema from your Django models:

```python
# management/commands/generate_schema.py
from django.core.management.base import BaseCommand
from rail_django_graphql.core.schema_generator import SchemaGenerator

class Command(BaseCommand):
    help = 'Generate GraphQL schema from Django models'

    def handle(self, *args, **options):
        generator = SchemaGenerator()
        schema = generator.generate_schema()

        self.stdout.write(
            self.style.SUCCESS(f'Schema generated with {len(schema.types)} types')
        )
```

### Custom Schema Configuration

```python
# settings.py
rail_django_graphql = {
    'SCHEMA_CONFIG': {
        # Model inclusion/exclusion
        'models': [
            'blog.models.Post',
            'blog.models.Category',
            'auth.models.User',
        ],
        'exclude_models': [
            'admin.models.LogEntry',
            'sessions.models.Session',
        ],

        # Feature configuration
        'mutations': {
            'enabled': True,
            'create': True,
            'update': True,
            'delete': True,
            'bulk_operations': True,
        },

        'queries': {
            'pagination': 'relay',  # 'relay', 'offset', 'cursor'
            'filtering': True,
            'ordering': True,
            'search': True,
        },

        # Field configuration
        'fields': {
            'auto_resolve_foreign_keys': True,
            'include_reverse_relations': True,
            'max_depth': 5,
        },

        # Security
        'permissions': {
            'require_authentication': False,
            'field_level_permissions': True,
            'object_level_permissions': True,
        }
    }
}
```

### Schema Introspection

```python
# utils/schema_inspector.py
from rail_django_graphql.generators.introspector import ModelIntrospector
from django.apps import apps

def inspect_models():
    """Inspect all models and generate schema information."""
    introspector = ModelIntrospector()

    for model in apps.get_models():
        analysis = introspector.analyze_model(model)

        print(f"Model: {analysis.model_name}")
        print(f"Fields: {list(analysis.fields.keys())}")
        print(f"Relationships: {list(analysis.relationships.keys())}")
        print(f"Methods: {list(analysis.methods.keys())}")
        print("---")
```

## 🔍 Advanced Queries

### Complex Filtering

```graphql
# Multiple filter conditions
query {
  posts(
    filters: {
      and: [
        { title: { icontains: "django" } }
        { published: { eq: true } }
        { createdAt: { gte: "2024-01-01" } }
        { author: { username: { in: ["john", "jane"] } } }
      ]
    }
  ) {
    edges {
      node {
        id
        title
        author {
          username
        }
        category {
          name
        }
      }
    }
  }
}

# OR conditions
query {
  posts(
    filters: {
      or: [
        { category: { name: { eq: "Technology" } } }
        { tags: { name: { in: ["python", "django"] } } }
      ]
    }
  ) {
    edges {
      node {
        id
        title
      }
    }
  }
}

# Nested relationship filtering
query {
  users(
    filters: {
      posts: {
        some: {
          and: [
            { published: { eq: true } }
            { category: { name: { eq: "Technology" } } }
          ]
        }
      }
    }
  ) {
    edges {
      node {
        username
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

### Advanced Pagination

```graphql
# Relay-style pagination
query {
  posts(first: 10, after: "cursor123") {
    edges {
      node {
        id
        title
      }
      cursor
    }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
    totalCount
  }
}

# Offset-based pagination
query {
  posts(limit: 10, offset: 20) {
    results {
      id
      title
    }
    pagination {
      totalCount
      hasNext
      hasPrevious
      currentPage
      totalPages
    }
  }
}
```

### Aggregation Queries

```graphql
# Count and aggregation
query {
  postStats {
    totalPosts
    publishedPosts
    draftPosts
    postsByCategory {
      category
      count
    }
    postsByMonth {
      month
      count
    }
  }

  userStats {
    totalUsers
    activeUsers
    averagePostsPerUser
    topAuthors(limit: 5) {
      username
      postCount
    }
  }
}
```

### Search Operations

```graphql
# Full-text search
query {
  searchPosts(query: "django graphql tutorial") {
    results {
      id
      title
      content
      score
      highlights {
        field
        fragments
      }
    }
    facets {
      categories {
        name
        count
      }
      authors {
        username
        count
      }
    }
  }
}
```

## ✏️ Complex Mutations

### Bulk Operations

```graphql
# Bulk create
mutation {
  bulkCreatePosts(
    input: {
      posts: [
        { title: "Post 1", content: "Content 1", authorId: 1, categoryId: 1 }
        { title: "Post 2", content: "Content 2", authorId: 2, categoryId: 1 }
      ]
    }
  ) {
    posts {
      id
      title
    }
    success
    errors
  }
}

# Bulk update
mutation {
  bulkUpdatePosts(
    input: {
      updates: [
        { id: 1, data: { published: true } }
        { id: 2, data: { published: false } }
      ]
    }
  ) {
    posts {
      id
      published
    }
    success
    errors
  }
}

# Bulk delete
mutation {
  bulkDeletePosts(input: { ids: [1, 2, 3] }) {
    deletedCount
    success
    errors
  }
}
```

### Nested Mutations

```graphql
# Create post with nested category
mutation {
  createPost(
    input: {
      title: "New Post"
      content: "Post content"
      authorId: 1
      category: {
        create: { name: "New Category", description: "Category description" }
      }
      tags: { connect: [1, 2], create: [{ name: "new-tag" }] }
    }
  ) {
    post {
      id
      title
      category {
        id
        name
      }
      tags {
        edges {
          node {
            id
            name
          }
        }
      }
    }
    success
    errors
  }
}
```

### Conditional Mutations

```graphql
# Update with conditions
mutation {
  updatePost(
    id: 1
    input: { title: "Updated Title", published: true }
    conditions: { author: { id: { eq: 1 } }, published: { eq: false } }
  ) {
    post {
      id
      title
      published
    }
    success
    errors
  }
}
```

## 📁 File Upload Operations

### Single File Upload

```graphql
# Upload single file
mutation {
  uploadFile(file: null) {
    file {
      id
      filename
      url
      size
      mimeType
      uploadedAt
    }
    success
    errors
  }
}
```

### Multiple File Upload

```graphql
# Upload multiple files
mutation {
  uploadMultipleFiles(files: [null, null, null]) {
    files {
      id
      filename
      url
      size
      processingStatus
    }
    success
    errors
  }
}
```

### File Processing Status

```graphql
# Check file processing status
query {
  file(id: "1") {
    id
    filename
    processingStatus
    virusScanResult
    thumbnails {
      size
      url
    }
    metadata {
      width
      height
      format
      colorSpace
    }
  }
}
```

### File Management

```graphql
# List files with filtering
query {
  files(
    filters: {
      mimeType: { startsWith: "image/" }
      size: { lte: 5242880 } # 5MB
      uploadedAt: { gte: "2024-01-01" }
    }
    orderBy: [{ field: "uploadedAt", direction: DESC }]
  ) {
    edges {
      node {
        id
        filename
        url
        size
        uploadedBy {
          username
        }
      }
    }
  }
}

# Delete file
mutation {
  deleteFile(id: "1") {
    success
    errors
  }
}
```

## 🔐 Authentication & Permissions

### JWT Authentication

```graphql
# Login
mutation {
  login(input: { username: "user@example.com", password: "password123" }) {
    token
    refreshToken
    user {
      id
      username
      email
    }
    success
    errors
  }
}

# Refresh token
mutation {
  refreshToken(input: { refreshToken: "refresh_token_here" }) {
    token
    refreshToken
    success
    errors
  }
}

# Logout
mutation {
  logout {
    success
  }
}
```

### Permission-based Queries

```graphql
# Query with permission checks
query {
  posts {
    edges {
      node {
        id
        title
        # Only visible to post author or admin
        content @include(if: $canViewContent)
        # Only visible to authenticated users
        author @include(if: $isAuthenticated) {
          username
        }
      }
    }
  }
}
```

### Role-based Access

```python
# Custom permission classes
from rail_django_graphql.security.permissions import BasePermission

class IsAuthorOrReadOnly(BasePermission):
    """Allow read access to all, write access only to author."""

    def has_permission(self, user, operation, model):
        if operation == 'read':
            return True
        return user.is_authenticated

    def has_object_permission(self, user, operation, obj):
        if operation == 'read':
            return True
        return obj.author == user

# Apply to model
class Post(models.Model):
    # ... fields ...

    class GraphQLMeta:
        permission_classes = [IsAuthorOrReadOnly]
```

## ⚡ Performance Optimization

### Query Optimization

```python
# Enable query optimization
rail_django_graphql = {
    'PERFORMANCE': {
        'ENABLE_QUERY_OPTIMIZATION': True,
        'ENABLE_DATALOADER': True,
        'ENABLE_QUERY_BATCHING': True,
        'MAX_QUERY_DEPTH': 10,
        'MAX_QUERY_COMPLEXITY': 1000,
    }
}
```

### Caching Strategies

```graphql
# Cache query results
query {
  posts @cached(ttl: 300) {
    edges {
      node {
        id
        title
        # Cache expensive computed field
        wordCount @cached(ttl: 3600)
      }
    }
  }
}
```

### DataLoader Usage

```python
# Custom DataLoader
from rail_django_graphql.extensions.optimization import BaseDataLoader

class CategoryLoader(BaseDataLoader):
    def batch_load_fn(self, category_ids):
        categories = Category.objects.filter(id__in=category_ids)
        category_map = {cat.id: cat for cat in categories}
        return [category_map.get(cat_id) for cat_id in category_ids]

# Use in resolver
class PostType(DjangoObjectType):
    class Meta:
        model = Post

    def resolve_category(self, info):
        return CategoryLoader(info.context).load(self.category_id)
```

## 🔧 Custom Extensions

### Custom Scalar Types

```python
# Custom scalar for JSON data
import graphene
from graphene.scalars import Scalar
from graphql.language import ast

class JSONScalar(Scalar):
    """JSON scalar type."""

    @staticmethod
    def serialize(value):
        return value

    @staticmethod
    def parse_literal(node):
        if isinstance(node, ast.StringValue):
            return json.loads(node.value)

    @staticmethod
    def parse_value(value):
        return value

# Register custom scalar
rail_django_graphql = {
    'CUSTOM_SCALARS': {
        'JSONField': 'myapp.scalars.JSONScalar',
    }
}
```

### Custom Filters

```python
# Custom filter for full-text search
from rail_django_graphql.generators.filters import BaseFilter

class FullTextSearchFilter(BaseFilter):
    """Full-text search filter."""

    def filter_queryset(self, queryset, value, info):
        if hasattr(queryset.model, 'search_vector'):
            return queryset.filter(search_vector=value)
        return queryset.filter(
            Q(title__icontains=value) | Q(content__icontains=value)
        )

# Register custom filter
rail_django_graphql = {
    'CUSTOM_FILTERS': {
        'fullTextSearch': 'myapp.filters.FullTextSearchFilter',
    }
}
```

### Custom Middleware

```python
# Custom GraphQL middleware
class TimingMiddleware:
    """Middleware to track query execution time."""

    def resolve(self, next, root, info, **args):
        start_time = time.time()
        result = next(root, info, **args)
        end_time = time.time()

        # Log slow queries
        if end_time - start_time > 1.0:
            logger.warning(
                f"Slow query detected: {info.field_name} took {end_time - start_time:.2f}s"
            )

        return result

# Add to settings
GRAPHENE = {
    'MIDDLEWARE': [
        'myapp.middleware.TimingMiddleware',
        'rail_django_graphql.middleware.AuthenticationMiddleware',
    ],
}
```

## 📖 API Reference

### Core Classes

#### SchemaGenerator

```python
from rail_django_graphql.core.schema_generator import SchemaGenerator

generator = SchemaGenerator(config=config)
schema = generator.generate_schema()
```

**Methods:**

- `generate_schema()` - Generate complete GraphQL schema
- `generate_types()` - Generate GraphQL types only
- `generate_queries()` - Generate query operations
- `generate_mutations()` - Generate mutation operations

#### TypeGenerator

```python
from rail_django_graphql.generators.types import TypeGenerator

type_gen = TypeGenerator(config=config)
post_type = type_gen.generate_type(Post)
```

**Methods:**

- `generate_type(model)` - Generate GraphQL type for model
- `get_field_type(field)` - Get GraphQL type for Django field
- `generate_input_type(model)` - Generate input type for mutations

#### QueryGenerator

```python
from rail_django_graphql.generators.queries import QueryGenerator

query_gen = QueryGenerator(type_generator, filter_generator)
queries = query_gen.generate_queries([Post, Category])
```

**Methods:**

- `generate_single_query(model)` - Generate single object query
- `generate_list_query(model)` - Generate list query with pagination
- `generate_search_query(model)` - Generate search query

#### MutationGenerator

```python
from rail_django_graphql.generators.mutations import MutationGenerator

mutation_gen = MutationGenerator(type_generator)
mutations = mutation_gen.generate_mutations([Post, Category])
```

**Methods:**

- `generate_create_mutation(model)` - Generate create mutation
- `generate_update_mutation(model)` - Generate update mutation
- `generate_delete_mutation(model)` - Generate delete mutation
- `generate_bulk_mutations(model)` - Generate bulk operations

### Configuration Options

```python
rail_django_graphql = {
    # Schema generation
    'AUTO_GENERATE_SCHEMA': True,
    'SCHEMA_OUTPUT_DIR': 'generated_schema/',
    'NAMING_CONVENTION': 'snake_case',  # 'snake_case', 'camelCase'

    # Features
    'ENABLE_MUTATIONS': True,
    'ENABLE_SUBSCRIPTIONS': False,
    'ENABLE_FILTERS': True,
    'ENABLE_FILE_UPLOADS': True,
    'ENABLE_PERMISSIONS': True,
    'ENABLE_CACHING': False,

    # Model configuration
    'APPS_TO_INCLUDE': [],
    'APPS_TO_EXCLUDE': ['admin', 'auth', 'contenttypes'],
    'MODELS_TO_EXCLUDE': [],

    # Pagination
    'PAGINATION_SIZE': 20,
    'MAX_QUERY_DEPTH': 10,

    # Performance
    'ENABLE_QUERY_OPTIMIZATION': True,
    'CACHE_TIMEOUT': 300,

    # Security
    'ENABLE_RATE_LIMITING': True,
    'RATE_LIMIT_PER_MINUTE': 100,
    'MAX_QUERY_COMPLEXITY': 1000,

    # Custom components
    'CUSTOM_SCALARS': {},
    'CUSTOM_FILTERS': {},
    'FIELD_CONVERTERS': {},
}
```

## 🔍 Debugging & Monitoring

### Query Analysis

```graphql
# Get query statistics
query {
  queryStats {
    totalQueries
    averageExecutionTime
    slowQueries {
      query
      executionTime
      timestamp
    }
    popularQueries {
      query
      count
    }
  }
}
```

### Performance Monitoring

```python
# Enable performance monitoring
from rail_django_graphql.extensions.optimization import get_performance_monitor

monitor = get_performance_monitor()
stats = monitor.get_stats()

print(f"Total queries: {stats.total_queries}")
print(f"Average execution time: {stats.avg_execution_time}")
print(f"Cache hit rate: {stats.cache_hit_rate}")
```

### Error Handling

```python
# Custom error handler
from rail_django_graphql.core.exceptions import GraphQLAutoError

class CustomErrorHandler:
    def handle_error(self, error, info):
        if isinstance(error, GraphQLAutoError):
            return {
                'message': error.message,
                'code': error.code,
                'field': error.field,
            }
        return {'message': 'An unexpected error occurred'}

# Register error handler
rail_django_graphql = {
    'ERROR_HANDLER': 'myapp.handlers.CustomErrorHandler',
}
```

## 📚 Next Steps

1. **Explore [Security Features](../features/security.md)** - Authentication, permissions, rate limiting
2. **Learn [File Upload System](../features/file-uploads-media.md)** - File handling and media processing
3. **Check [Performance Guide](../development/performance.md)** - Optimization techniques
4. **Review [Examples](../examples/)** - Real-world usage examples
5. **Read [Developer Guide](../development/developer-guide.md)** - Extension development

---

This advanced usage guide provides comprehensive coverage of the Django GraphQL Auto-Generation Library's capabilities. For specific use cases or advanced customization, refer to the detailed API documentation and examples.
