# Performance Optimization Guide

This guide covers performance optimization techniques for the Django GraphQL Auto-Generation Library, helping you build fast and scalable GraphQL APIs.

## 📚 Table of Contents

- [Overview](#overview)
- [Database Optimization](#database-optimization)
- [Query Optimization](#query-optimization)
- [Caching Strategies](#caching-strategies)
- [Pagination and Limiting](#pagination-and-limiting)
- [Memory Management](#memory-management)
- [Monitoring and Profiling](#monitoring-and-profiling)
- [Production Optimization](#production-optimization)
- [Best Practices](#best-practices)

## 🎯 Overview

Performance optimization in GraphQL involves several key areas:

- **Database Query Optimization** - Reducing N+1 queries and optimizing database access
- **Caching** - Implementing effective caching strategies
- **Pagination** - Handling large datasets efficiently
- **Memory Management** - Optimizing memory usage for large operations
- **Query Complexity** - Limiting and analyzing query complexity

## 🗄️ Database Optimization

### N+1 Query Problem

The N+1 query problem is common in GraphQL when fetching related objects.

**Problem Example:**

```python
# This GraphQL query:
query {
  allPosts {
    id
    title
    author {
      name
    }
    comments {
      content
      author {
        name
      }
    }
  }
}

# Without optimization, generates:
# 1 query for posts
# N queries for authors (one per post)
# N queries for comments (one per post)
# M queries for comment authors (one per comment)
```

**Solution - Query Optimization:**

```python
from rail_django_graphql.optimization import QueryOptimizer

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class GraphQLMeta:
        # Enable automatic query optimization
        optimize_queries = True

        # Configure relationship prefetching
        select_related = ['author']  # For ForeignKey and OneToOne
        prefetch_related = ['comments__author']  # For reverse ForeignKey and ManyToMany

        # Advanced optimization
        optimization_config = {
            'max_prefetch_depth': 3,
            'enable_select_related_optimization': True,
            'enable_prefetch_related_optimization': True,
        }

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

    class GraphQLMeta:
        select_related = ['author', 'post']
```

**Custom Query Optimization:**

```python
from rail_django_graphql.resolvers import OptimizedResolver
from django.db.models import Prefetch

class PostResolver(OptimizedResolver):
    """Custom resolver with advanced optimization."""

    def get_queryset(self, info, **kwargs):
        """Get optimized queryset based on requested fields."""
        queryset = Post.objects.all()

        # Analyze requested fields from GraphQL info
        requested_fields = self.get_requested_fields(info)

        # Dynamic optimization based on requested fields
        if 'author' in requested_fields:
            queryset = queryset.select_related('author')

        if 'comments' in requested_fields:
            # Optimize comments prefetching
            comments_prefetch = Prefetch(
                'comments',
                queryset=Comment.objects.select_related('author')
            )
            queryset = queryset.prefetch_related(comments_prefetch)

        if 'tags' in requested_fields:
            queryset = queryset.prefetch_related('tags')

        return queryset

    def get_requested_fields(self, info):
        """Extract requested fields from GraphQL info."""
        from graphql.execution.collect_fields import collect_fields

        fields = collect_fields(
            info.schema,
            info.fragments,
            info.field_nodes[0].selection_set,
            info.variable_values
        )

        return list(fields.keys())

# Register custom resolver
from rail_django_graphql.registry import resolver_registry
resolver_registry.register(Post, PostResolver)
```

### Database Indexes

**Strategic Index Creation:**

```python
class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    view_count = models.IntegerField(default=0)

    class Meta:
        indexes = [
            # Single field indexes for filtering
            models.Index(fields=['status']),
            models.Index(fields=['author']),
            models.Index(fields=['-created_at']),  # For ordering

            # Composite indexes for common filter combinations
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['author', 'status']),

            # Partial indexes for specific conditions
            models.Index(
                fields=['title'],
                condition=models.Q(status='published'),
                name='published_posts_title_idx'
            ),

            # Functional indexes (PostgreSQL)
            models.Index(
                fields=['title'],
                name='title_lower_idx',
                opclasses=['varchar_pattern_ops']
            ),
        ]

        # Database constraints for performance
        constraints = [
            models.CheckConstraint(
                check=models.Q(view_count__gte=0),
                name='positive_view_count'
            ),
        ]

    class GraphQLMeta:
        # Configure filtering to use indexes
        filter_fields = {
            'status': ['exact', 'in'],
            'author': ['exact'],
            'created_at': ['gte', 'lte', 'range'],
            'title': ['icontains', 'istartswith'],
        }

        # Default ordering to use index
        ordering = ['-created_at']
```

**Index Usage Analysis:**

```python
from django.db import connection
from django.test.utils import override_settings

def analyze_query_performance():
    """Analyze query performance and index usage."""

    with override_settings(DEBUG=True):
        # Clear previous queries
        connection.queries_log.clear()

        # Execute GraphQL query
        result = schema.execute('''
            query {
                allPosts(filters: {status: "published"}, orderBy: "-createdAt") {
                    id
                    title
                    author {
                        name
                    }
                }
            }
        ''')

        # Analyze queries
        for query in connection.queries:
            print(f"SQL: {query['sql']}")
            print(f"Time: {query['time']}s")

            # Check if indexes are used (PostgreSQL)
            if 'EXPLAIN' in query['sql'].upper():
                print("Execution plan available")

# PostgreSQL specific index analysis
def explain_query(queryset):
    """Get query execution plan."""
    from django.db import connection

    sql, params = queryset.query.sql_with_params()

    with connection.cursor() as cursor:
        cursor.execute(f"EXPLAIN ANALYZE {sql}", params)
        plan = cursor.fetchall()

        for row in plan:
            print(row[0])
```

### Database Connection Optimization

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            # Connection pooling
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,

            # Connection timeout
            'CONN_MAX_AGE': 600,  # 10 minutes

            # Query optimization
            'OPTIONS': {
                'statement_timeout': '30000',  # 30 seconds
                'lock_timeout': '10000',       # 10 seconds
            }
        }
    }
}

# Connection pooling with django-db-pool
DATABASES['default']['ENGINE'] = 'django_db_pool.backends.postgresql'
DATABASES['default']['POOL_OPTIONS'] = {
    'POOL_SIZE': 10,
    'MAX_OVERFLOW': 10,
    'RECYCLE': 24 * 60 * 60,  # 24 hours
}
```

## 🔍 Query Optimization

### DataLoader Pattern

Implement DataLoader pattern for efficient batch loading:

```python
from rail_django_graphql.loaders import DataLoader
from collections import defaultdict

class AuthorLoader(DataLoader):
    """Batch load authors to avoid N+1 queries."""

    def batch_load_fn(self, author_ids):
        """Load authors in batch."""
        authors = Author.objects.filter(id__in=author_ids)
        author_map = {author.id: author for author in authors}

        # Return authors in the same order as requested IDs
        return [author_map.get(author_id) for author_id in author_ids]

class CommentsByPostLoader(DataLoader):
    """Batch load comments by post IDs."""

    def batch_load_fn(self, post_ids):
        """Load comments for multiple posts."""
        comments = Comment.objects.filter(
            post_id__in=post_ids
        ).select_related('author')

        # Group comments by post_id
        comments_by_post = defaultdict(list)
        for comment in comments:
            comments_by_post[comment.post_id].append(comment)

        # Return comments in the same order as post_ids
        return [comments_by_post.get(post_id, []) for post_id in post_ids]

# Use DataLoaders in resolvers
class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = '__all__'

    def resolve_author(self, info):
        """Resolve author using DataLoader."""
        return info.context.loaders['author'].load(self.author_id)

    def resolve_comments(self, info):
        """Resolve comments using DataLoader."""
        return info.context.loaders['comments_by_post'].load(self.id)

# Configure DataLoaders in context
class GraphQLContext:
    def __init__(self, request):
        self.request = request
        self.user = getattr(request, 'user', None)

        # Initialize DataLoaders
        self.loaders = {
            'author': AuthorLoader(),
            'comments_by_post': CommentsByPostLoader(),
        }

# In your GraphQL view
from graphene_django.views import GraphQLView

class OptimizedGraphQLView(GraphQLView):
    def get_context(self, request):
        return GraphQLContext(request)
```

### Query Complexity Analysis

```python
from rail_django_graphql.complexity import QueryComplexityAnalyzer

class ComplexityAnalyzer(QueryComplexityAnalyzer):
    """Analyze and limit query complexity."""

    def __init__(self, max_complexity=1000):
        self.max_complexity = max_complexity

    def analyze_query(self, query_ast, variables=None):
        """Analyze query complexity."""
        complexity = self.calculate_complexity(query_ast, variables)

        if complexity > self.max_complexity:
            raise GraphQLError(
                f"Query complexity {complexity} exceeds maximum {self.max_complexity}"
            )

        return complexity

    def calculate_complexity(self, node, variables=None, depth=0):
        """Calculate complexity score for a query node."""
        if depth > 10:  # Prevent infinite recursion
            return 1000  # High penalty for deep queries

        complexity = 1  # Base complexity

        # Add complexity for each field
        if hasattr(node, 'selection_set') and node.selection_set:
            for selection in node.selection_set.selections:
                if hasattr(selection, 'name'):
                    field_name = selection.name.value

                    # Higher complexity for relationship fields
                    if self.is_relationship_field(field_name):
                        complexity += 5

                    # Recursive complexity calculation
                    complexity += self.calculate_complexity(
                        selection, variables, depth + 1
                    )

        return complexity

    def is_relationship_field(self, field_name):
        """Check if field represents a relationship."""
        # Implementation depends on your schema structure
        relationship_indicators = ['all', 'list', 'connection']
        return any(indicator in field_name.lower() for indicator in relationship_indicators)

# Apply complexity analysis
from graphene.validation import depth_limit_validator

schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    validation_rules=[
        depth_limit_validator(max_depth=10),
        ComplexityAnalyzer(max_complexity=1000),
    ]
)
```

### Query Batching

```python
from rail_django_graphql.batching import QueryBatcher

class GraphQLBatcher(QueryBatcher):
    """Batch multiple GraphQL queries into a single request."""

    def __init__(self, max_batch_size=10):
        self.max_batch_size = max_batch_size

    def batch_queries(self, queries):
        """Execute multiple queries in a single batch."""
        if len(queries) > self.max_batch_size:
            raise GraphQLError(f"Batch size {len(queries)} exceeds maximum {self.max_batch_size}")

        results = []

        # Use database transaction for consistency
        with transaction.atomic():
            for query in queries:
                try:
                    result = schema.execute(
                        query['query'],
                        variables=query.get('variables'),
                        context=query.get('context')
                    )
                    results.append({
                        'data': result.data,
                        'errors': [str(e) for e in result.errors] if result.errors else None
                    })
                except Exception as e:
                    results.append({
                        'data': None,
                        'errors': [str(e)]
                    })

        return results

# Batch execution endpoint
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def graphql_batch_view(request):
    """Handle batched GraphQL requests."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)

    try:
        data = json.loads(request.body)

        if isinstance(data, list):
            # Batch request
            batcher = GraphQLBatcher()
            results = batcher.batch_queries(data)
            return JsonResponse(results, safe=False)
        else:
            # Single request
            result = schema.execute(
                data['query'],
                variables=data.get('variables'),
                context=request
            )
            return JsonResponse({
                'data': result.data,
                'errors': [str(e) for e in result.errors] if result.errors else None
            })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
```

## 💾 Caching Strategies

### Query Result Caching

```python
from django.core.cache import cache
from rail_django_graphql.caching import QueryCache
import hashlib
import json

class GraphQLQueryCache(QueryCache):
    """Cache GraphQL query results."""

    def __init__(self, default_timeout=300):
        self.default_timeout = default_timeout

    def get_cache_key(self, query, variables=None, user=None):
        """Generate cache key for query."""
        key_data = {
            'query': query,
            'variables': variables or {},
            'user_id': user.id if user and user.is_authenticated else None
        }

        key_string = json.dumps(key_data, sort_keys=True)
        return f"graphql_query:{hashlib.md5(key_string.encode()).hexdigest()}"

    def get_cached_result(self, query, variables=None, user=None):
        """Get cached query result."""
        cache_key = self.get_cache_key(query, variables, user)
        return cache.get(cache_key)

    def cache_result(self, query, variables, user, result, timeout=None):
        """Cache query result."""
        if result.errors:
            return  # Don't cache error results

        cache_key = self.get_cache_key(query, variables, user)
        cache.set(cache_key, result.data, timeout or self.default_timeout)

    def invalidate_cache(self, patterns=None):
        """Invalidate cached results."""
        if patterns:
            # Invalidate specific patterns
            for pattern in patterns:
                cache.delete_pattern(f"graphql_query:*{pattern}*")
        else:
            # Clear all GraphQL cache
            cache.delete_pattern("graphql_query:*")

# Cached GraphQL view
class CachedGraphQLView(GraphQLView):
    def __init__(self):
        super().__init__()
        self.query_cache = GraphQLQueryCache()

    def execute_graphql_request(self, request, data, query, variables, operation_name, show_graphiql=False):
        """Execute GraphQL request with caching."""

        # Check cache first
        cached_result = self.query_cache.get_cached_result(
            query, variables, request.user
        )

        if cached_result:
            return ExecutionResult(data=cached_result)

        # Execute query
        result = super().execute_graphql_request(
            request, data, query, variables, operation_name, show_graphiql
        )

        # Cache successful results
        if not result.errors:
            self.query_cache.cache_result(
                query, variables, request.user, result
            )

        return result
```

### Field-Level Caching

```python
from rail_django_graphql.caching import FieldCache
from functools import wraps

def cached_field(timeout=300, key_func=None):
    """Decorator for caching individual field results."""

    def decorator(resolver_func):
        @wraps(resolver_func)
        def wrapper(root, info, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(root, info, **kwargs)
            else:
                cache_key = f"{root.__class__.__name__}:{root.id}:{resolver_func.__name__}"

            # Check cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute resolver
            result = resolver_func(root, info, **kwargs)

            # Cache result
            cache.set(cache_key, result, timeout)

            return result

        return wrapper
    return decorator

# Usage in resolvers
class PostType(DjangoObjectType):
    expensive_calculation = graphene.String()

    class Meta:
        model = Post
        fields = '__all__'

    @cached_field(timeout=600)  # Cache for 10 minutes
    def resolve_expensive_calculation(self, info):
        """Expensive calculation that should be cached."""
        import time
        time.sleep(1)  # Simulate expensive operation
        return f"Expensive result for post {self.id}"

    @cached_field(
        timeout=300,
        key_func=lambda root, info, **kwargs: f"comment_count:{root.id}"
    )
    def resolve_comment_count(self, info):
        """Cache comment count with custom key."""
        return self.comments.count()
```

### Cache Invalidation

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from rail_django_graphql.caching import CacheInvalidator

class SmartCacheInvalidator(CacheInvalidator):
    """Intelligent cache invalidation based on model changes."""

    def __init__(self):
        self.invalidation_rules = {
            'Post': {
                'patterns': ['post:*', 'all_posts:*'],
                'related_models': ['Comment', 'Tag'],
            },
            'Comment': {
                'patterns': ['comment:*', 'post:*'],
                'related_fields': ['post'],
            },
            'Author': {
                'patterns': ['author:*', 'post:*'],
                'related_fields': ['posts'],
            }
        }

    def invalidate_for_model(self, model_class, instance=None, action='update'):
        """Invalidate cache for model changes."""
        model_name = model_class.__name__
        rules = self.invalidation_rules.get(model_name, {})

        # Invalidate direct patterns
        patterns = rules.get('patterns', [])
        if instance:
            patterns.extend([f"{model_name.lower()}:{instance.id}:*"])

        for pattern in patterns:
            cache.delete_pattern(pattern)

        # Invalidate related models
        if instance and action in ['update', 'delete']:
            self._invalidate_related_models(instance, rules)

    def _invalidate_related_models(self, instance, rules):
        """Invalidate cache for related models."""
        for field_name in rules.get('related_fields', []):
            if hasattr(instance, field_name):
                related_objects = getattr(instance, field_name)

                if hasattr(related_objects, 'all'):
                    # Many-to-many or reverse foreign key
                    for related_obj in related_objects.all():
                        cache.delete_pattern(f"{related_obj.__class__.__name__.lower()}:{related_obj.id}:*")
                else:
                    # Foreign key
                    if related_objects:
                        cache.delete_pattern(f"{related_objects.__class__.__name__.lower()}:{related_objects.id}:*")

# Connect to Django signals
invalidator = SmartCacheInvalidator()

@receiver([post_save, post_delete])
def invalidate_cache_on_model_change(sender, instance, **kwargs):
    """Invalidate cache when models change."""
    action = 'delete' if kwargs.get('signal') == post_delete else 'update'
    invalidator.invalidate_for_model(sender, instance, action)
```

## 📄 Pagination and Limiting

### Cursor-Based Pagination

```python
from rail_django_graphql.pagination import CursorPagination
import base64
import json

class OptimizedCursorPagination(CursorPagination):
    """Optimized cursor-based pagination."""

    def __init__(self, max_page_size=100, default_page_size=20):
        self.max_page_size = max_page_size
        self.default_page_size = default_page_size

    def paginate_queryset(self, queryset, cursor=None, first=None, last=None):
        """Paginate queryset with cursor-based pagination."""

        # Validate page size
        page_size = first or last or self.default_page_size
        if page_size > self.max_page_size:
            raise GraphQLError(f"Page size {page_size} exceeds maximum {self.max_page_size}")

        # Apply cursor filtering
        if cursor:
            cursor_data = self.decode_cursor(cursor)
            if cursor_data:
                queryset = queryset.filter(id__gt=cursor_data['id'])

        # Apply ordering for consistent pagination
        queryset = queryset.order_by('id')

        # Fetch one extra item to determine if there are more pages
        items = list(queryset[:page_size + 1])
        has_next_page = len(items) > page_size

        if has_next_page:
            items = items[:-1]

        # Generate cursors
        start_cursor = self.encode_cursor({'id': items[0].id}) if items else None
        end_cursor = self.encode_cursor({'id': items[-1].id}) if items else None

        return {
            'items': items,
            'page_info': {
                'has_next_page': has_next_page,
                'has_previous_page': cursor is not None,
                'start_cursor': start_cursor,
                'end_cursor': end_cursor,
            }
        }

    def encode_cursor(self, data):
        """Encode cursor data."""
        json_string = json.dumps(data, sort_keys=True)
        return base64.b64encode(json_string.encode()).decode()

    def decode_cursor(self, cursor):
        """Decode cursor data."""
        try:
            json_string = base64.b64decode(cursor.encode()).decode()
            return json.loads(json_string)
        except (ValueError, json.JSONDecodeError):
            return None

# Usage in GraphQL types
class PostConnection(graphene.Connection):
    class Meta:
        node = PostType

    total_count = graphene.Int()

    def resolve_total_count(self, info):
        return self.length

class Query(graphene.ObjectType):
    all_posts = graphene.ConnectionField(
        PostConnection,
        description="Get all posts with pagination"
    )

    def resolve_all_posts(self, info, **kwargs):
        queryset = Post.objects.all()

        # Apply filtering
        filters = kwargs.get('filters', {})
        if filters:
            queryset = apply_filters(queryset, filters)

        # Apply pagination
        paginator = OptimizedCursorPagination()
        return paginator.paginate_queryset(queryset, **kwargs)
```

### Offset-Based Pagination with Optimization

```python
from rail_django_graphql.pagination import OffsetPagination
from django.core.paginator import Paginator

class OptimizedOffsetPagination(OffsetPagination):
    """Optimized offset-based pagination."""

    def __init__(self, max_page_size=100, default_page_size=20):
        self.max_page_size = max_page_size
        self.default_page_size = default_page_size

    def paginate_queryset(self, queryset, page=1, page_size=None):
        """Paginate queryset with offset-based pagination."""

        page_size = page_size or self.default_page_size
        if page_size > self.max_page_size:
            raise GraphQLError(f"Page size {page_size} exceeds maximum {self.max_page_size}")

        # Use Django's Paginator with optimization
        paginator = Paginator(queryset, page_size)

        # Optimize count query for large datasets
        if queryset.count() > 10000:
            # Use approximate count for very large datasets
            paginator._count = self.get_approximate_count(queryset)

        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            raise GraphQLError(f"Page {page} is out of range")

        return {
            'items': list(page_obj.object_list),
            'page_info': {
                'page': page,
                'page_size': page_size,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        }

    def get_approximate_count(self, queryset):
        """Get approximate count for large datasets."""
        from django.db import connection

        # PostgreSQL specific optimization
        if connection.vendor == 'postgresql':
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT reltuples::BIGINT AS estimate FROM pg_class WHERE relname = %s",
                    [queryset.model._meta.db_table]
                )
                row = cursor.fetchone()
                return row[0] if row else queryset.count()

        # Fallback to exact count
        return queryset.count()
```

## 🧠 Memory Management

### Memory-Efficient Query Processing

```python
from rail_django_graphql.memory import MemoryOptimizer
import gc

class MemoryEfficientResolver:
    """Memory-efficient resolver for large datasets."""

    def __init__(self, chunk_size=1000):
        self.chunk_size = chunk_size

    def resolve_large_dataset(self, queryset, info):
        """Resolve large dataset with memory optimization."""

        # Use iterator to avoid loading all objects into memory
        for chunk in self.chunked_queryset(queryset):
            # Process chunk
            yield from chunk

            # Force garbage collection after each chunk
            gc.collect()

    def chunked_queryset(self, queryset):
        """Split queryset into chunks."""
        count = queryset.count()

        for start in range(0, count, self.chunk_size):
            end = min(start + self.chunk_size, count)
            chunk = queryset[start:end]
            yield list(chunk)

class MemoryMonitor:
    """Monitor memory usage during GraphQL execution."""

    def __init__(self):
        import psutil
        self.process = psutil.Process()

    def get_memory_usage(self):
        """Get current memory usage."""
        memory_info = self.process.memory_info()
        return {
            'rss': memory_info.rss / 1024 / 1024,  # MB
            'vms': memory_info.vms / 1024 / 1024,  # MB
        }

    def check_memory_limit(self, limit_mb=1000):
        """Check if memory usage exceeds limit."""
        usage = self.get_memory_usage()
        if usage['rss'] > limit_mb:
            raise GraphQLError(f"Memory usage {usage['rss']:.1f}MB exceeds limit {limit_mb}MB")

# Memory-optimized GraphQL view
class MemoryOptimizedGraphQLView(GraphQLView):
    def __init__(self):
        super().__init__()
        self.memory_monitor = MemoryMonitor()

    def execute_graphql_request(self, request, data, query, variables, operation_name, show_graphiql=False):
        """Execute GraphQL request with memory monitoring."""

        # Check initial memory
        initial_memory = self.memory_monitor.get_memory_usage()

        try:
            # Execute query
            result = super().execute_graphql_request(
                request, data, query, variables, operation_name, show_graphiql
            )

            # Check memory after execution
            self.memory_monitor.check_memory_limit()

            return result

        finally:
            # Force garbage collection
            gc.collect()

            # Log memory usage
            final_memory = self.memory_monitor.get_memory_usage()
            memory_diff = final_memory['rss'] - initial_memory['rss']

            if memory_diff > 100:  # Log if memory increased by more than 100MB
                logger.warning(f"High memory usage: {memory_diff:.1f}MB increase")
```

### Object Pool for Frequently Used Objects

```python
from rail_django_graphql.pooling import ObjectPool
from threading import Lock

class GraphQLObjectPool:
    """Object pool for frequently accessed GraphQL objects."""

    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.pools = {}
        self.lock = Lock()

    def get_or_create(self, model_class, obj_id):
        """Get object from pool or create new one."""
        pool_key = f"{model_class.__name__}:{obj_id}"

        with self.lock:
            if pool_key in self.pools:
                return self.pools[pool_key]

            # Create new object
            try:
                obj = model_class.objects.get(id=obj_id)

                # Add to pool if not full
                if len(self.pools) < self.max_size:
                    self.pools[pool_key] = obj

                return obj

            except model_class.DoesNotExist:
                return None

    def invalidate(self, model_class, obj_id=None):
        """Invalidate objects in pool."""
        with self.lock:
            if obj_id:
                # Invalidate specific object
                pool_key = f"{model_class.__name__}:{obj_id}"
                self.pools.pop(pool_key, None)
            else:
                # Invalidate all objects of this model
                keys_to_remove = [
                    key for key in self.pools.keys()
                    if key.startswith(f"{model_class.__name__}:")
                ]
                for key in keys_to_remove:
                    del self.pools[key]

    def clear(self):
        """Clear entire pool."""
        with self.lock:
            self.pools.clear()

# Global object pool instance
object_pool = GraphQLObjectPool()

# Use in resolvers
class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = '__all__'

    @staticmethod
    def get_node(info, id):
        """Get node using object pool."""
        return object_pool.get_or_create(Post, id)

# Invalidate pool on model changes
@receiver([post_save, post_delete])
def invalidate_object_pool(sender, instance, **kwargs):
    """Invalidate object pool when models change."""
    object_pool.invalidate(sender, instance.id)
```

## 📊 Monitoring and Profiling

### Performance Monitoring

```python
from rail_django_graphql.monitoring import PerformanceMonitor
import time
from django.db import connection

class GraphQLPerformanceMonitor:
    """Monitor GraphQL query performance."""

    def __init__(self):
        self.metrics = {}

    def start_monitoring(self, query_name):
        """Start monitoring a query."""
        self.metrics[query_name] = {
            'start_time': time.time(),
            'start_queries': len(connection.queries),
        }

    def end_monitoring(self, query_name):
        """End monitoring and return metrics."""
        if query_name not in self.metrics:
            return None

        start_data = self.metrics[query_name]

        metrics = {
            'execution_time': time.time() - start_data['start_time'],
            'database_queries': len(connection.queries) - start_data['start_queries'],
            'query_name': query_name,
        }

        # Clean up
        del self.metrics[query_name]

        return metrics

    def log_slow_queries(self, metrics, threshold=1.0):
        """Log slow queries."""
        if metrics['execution_time'] > threshold:
            logger.warning(
                f"Slow GraphQL query: {metrics['query_name']} "
                f"took {metrics['execution_time']:.2f}s "
                f"with {metrics['database_queries']} DB queries"
            )

# Performance monitoring middleware
class PerformanceMiddleware:
    """GraphQL middleware for performance monitoring."""

    def __init__(self):
        self.monitor = GraphQLPerformanceMonitor()

    def resolve(self, next, root, info, **args):
        """Monitor resolver performance."""
        field_name = info.field_name

        # Start monitoring
        self.monitor.start_monitoring(field_name)

        try:
            # Execute resolver
            result = next(root, info, **args)
            return result

        finally:
            # End monitoring and log metrics
            metrics = self.monitor.end_monitoring(field_name)
            if metrics:
                self.monitor.log_slow_queries(metrics)

# Add to GraphQL schema
schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    middleware=[PerformanceMiddleware()]
)
```

### Query Analysis and Optimization Suggestions

```python
from rail_django_graphql.analysis import QueryAnalyzer

class GraphQLQueryAnalyzer:
    """Analyze GraphQL queries and provide optimization suggestions."""

    def analyze_query(self, query_ast, schema):
        """Analyze query and return optimization suggestions."""
        analysis = {
            'complexity': self.calculate_complexity(query_ast),
            'depth': self.calculate_depth(query_ast),
            'field_count': self.count_fields(query_ast),
            'suggestions': []
        }

        # Generate suggestions
        if analysis['complexity'] > 500:
            analysis['suggestions'].append(
                "Consider reducing query complexity by limiting nested fields"
            )

        if analysis['depth'] > 8:
            analysis['suggestions'].append(
                "Query depth is high, consider using pagination for nested lists"
            )

        if analysis['field_count'] > 50:
            analysis['suggestions'].append(
                "Large number of fields requested, consider splitting into multiple queries"
            )

        # Check for N+1 potential
        n_plus_one_risk = self.check_n_plus_one_risk(query_ast, schema)
        if n_plus_one_risk:
            analysis['suggestions'].extend(n_plus_one_risk)

        return analysis

    def check_n_plus_one_risk(self, query_ast, schema):
        """Check for potential N+1 query problems."""
        suggestions = []

        # Analyze field selections for relationship patterns
        relationship_fields = self.find_relationship_fields(query_ast, schema)

        for field_path in relationship_fields:
            suggestions.append(
                f"Potential N+1 query risk at {field_path}. "
                f"Consider using select_related or prefetch_related"
            )

        return suggestions

    def find_relationship_fields(self, node, schema, path=""):
        """Find fields that represent database relationships."""
        relationship_fields = []

        if hasattr(node, 'selection_set') and node.selection_set:
            for selection in node.selection_set.selections:
                if hasattr(selection, 'name'):
                    field_name = selection.name.value
                    current_path = f"{path}.{field_name}" if path else field_name

                    # Check if field is a relationship (simplified check)
                    if self.is_likely_relationship(field_name):
                        relationship_fields.append(current_path)

                    # Recurse into nested selections
                    relationship_fields.extend(
                        self.find_relationship_fields(selection, schema, current_path)
                    )

        return relationship_fields

    def is_likely_relationship(self, field_name):
        """Check if field name suggests a database relationship."""
        relationship_indicators = [
            'author', 'user', 'post', 'comment', 'tag', 'category',
            'all', 'list', 'connection', 'related'
        ]

        return any(indicator in field_name.lower() for indicator in relationship_indicators)

# Use in GraphQL view
class AnalyzedGraphQLView(GraphQLView):
    def __init__(self):
        super().__init__()
        self.analyzer = GraphQLQueryAnalyzer()

    def execute_graphql_request(self, request, data, query, variables, operation_name, show_graphiql=False):
        """Execute GraphQL request with query analysis."""

        # Parse and analyze query
        try:
            from graphql import parse
            query_ast = parse(query)
            analysis = self.analyzer.analyze_query(query_ast, self.schema)

            # Log analysis results
            if analysis['suggestions']:
                logger.info(f"Query optimization suggestions: {analysis['suggestions']}")

        except Exception as e:
            logger.warning(f"Query analysis failed: {e}")

        # Execute query
        return super().execute_graphql_request(
            request, data, query, variables, operation_name, show_graphiql
        )
```

## 🚀 Production Optimization

### Production Settings

```python
# settings/production.py

# Database optimization
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'your_host',
        'PORT': '5432',
        'OPTIONS': {
            'MAX_CONNS': 20,
            'CONN_MAX_AGE': 600,
        }
    }
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}

# GraphQL optimization settings
rail_django_graphql = {
    'PERFORMANCE': {
        'ENABLE_QUERY_OPTIMIZATION': True,
        'ENABLE_CACHING': True,
        'CACHE_TIMEOUT': 300,
        'MAX_QUERY_COMPLEXITY': 1000,
        'MAX_QUERY_DEPTH': 10,
        'DEFAULT_PAGE_SIZE': 20,
        'MAX_PAGE_SIZE': 100,
    },
    'MONITORING': {
        'ENABLE_PERFORMANCE_MONITORING': True,
        'LOG_SLOW_QUERIES': True,
        'SLOW_QUERY_THRESHOLD': 1.0,
        'ENABLE_MEMORY_MONITORING': True,
        'MEMORY_LIMIT_MB': 1000,
    }
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'graphql_performance.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'rail_django_graphql.performance': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Load Testing and Benchmarking

```python
# load_test.py
import asyncio
import aiohttp
import time
import json
from concurrent.futures import ThreadPoolExecutor

class GraphQLLoadTester:
    """Load test GraphQL endpoints."""

    def __init__(self, endpoint_url, concurrent_requests=10):
        self.endpoint_url = endpoint_url
        self.concurrent_requests = concurrent_requests

    async def run_load_test(self, query, variables=None, duration=60):
        """Run load test for specified duration."""

        start_time = time.time()
        end_time = start_time + duration

        results = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'errors': []
        }

        async with aiohttp.ClientSession() as session:
            tasks = []

            while time.time() < end_time:
                # Create batch of concurrent requests
                for _ in range(self.concurrent_requests):
                    task = self.execute_query(session, query, variables, results)
                    tasks.append(task)

                # Wait for batch to complete
                await asyncio.gather(*tasks, return_exceptions=True)
                tasks.clear()

        # Calculate statistics
        avg_response_time = sum(results['response_times']) / len(results['response_times'])
        requests_per_second = results['total_requests'] / duration

        return {
            'duration': duration,
            'total_requests': results['total_requests'],
            'successful_requests': results['successful_requests'],
            'failed_requests': results['failed_requests'],
            'requests_per_second': requests_per_second,
            'average_response_time': avg_response_time,
            'errors': results['errors'][:10]  # First 10 errors
        }

    async def execute_query(self, session, query, variables, results):
        """Execute single GraphQL query."""

        payload = {
            'query': query,
            'variables': variables or {}
        }

        start_time = time.time()

        try:
            async with session.post(
                self.endpoint_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:

                response_time = time.time() - start_time
                results['response_times'].append(response_time)
                results['total_requests'] += 1

                if response.status == 200:
                    data = await response.json()
                    if not data.get('errors'):
                        results['successful_requests'] += 1
                    else:
                        results['failed_requests'] += 1
                        results['errors'].append(data['errors'])
                else:
                    results['failed_requests'] += 1
                    results['errors'].append(f"HTTP {response.status}")

        except Exception as e:
            results['failed_requests'] += 1
            results['errors'].append(str(e))

# Usage
async def main():
    tester = GraphQLLoadTester('http://localhost:8000/graphql/')

    query = '''
        query {
            allPosts(first: 10) {
                edges {
                    node {
                        id
                        title
                        author {
                            name
                        }
                    }
                }
            }
        }
    '''

    results = await tester.run_load_test(query, duration=60)

    print(f"Load test results:")
    print(f"  Duration: {results['duration']}s")
    print(f"  Total requests: {results['total_requests']}")
    print(f"  Successful: {results['successful_requests']}")
    print(f"  Failed: {results['failed_requests']}")
    print(f"  Requests/second: {results['requests_per_second']:.2f}")
    print(f"  Average response time: {results['average_response_time']:.3f}s")

if __name__ == '__main__':
    asyncio.run(main())
```

## 📋 Best Practices

### 1. Database Optimization

- **Use appropriate indexes** for filtered and ordered fields
- **Implement select_related and prefetch_related** for relationships
- **Use database connection pooling** in production
- **Monitor query performance** and optimize slow queries

### 2. Caching Strategy

- **Cache expensive calculations** at the field level
- **Implement query result caching** for frequently accessed data
- **Use intelligent cache invalidation** based on model changes
- **Consider CDN caching** for static GraphQL schemas

### 3. Query Optimization

- **Implement query complexity limits** to prevent abuse
- **Use pagination** for large datasets
- **Batch related queries** using DataLoader pattern
- **Monitor and analyze** query patterns

### 4. Memory Management

- **Use iterators** for large datasets
- **Implement object pooling** for frequently accessed objects
- **Monitor memory usage** in production
- **Force garbage collection** after heavy operations

### 5. Production Deployment

- **Use production-optimized settings**
- **Implement comprehensive monitoring**
- **Set up load testing** and performance benchmarks
- **Configure proper logging** for debugging

## 🔗 Next Steps

Now that you understand performance optimization:

1. [Review Testing Guide](../development/testing.md) - Test your optimizations
2. [Check Troubleshooting Guide](../development/troubleshooting.md) - Debug performance issues
3. [Explore Advanced Examples](../examples/advanced-examples.md) - See optimized implementations
4. [Read API Reference](../api/core-classes.md) - Understand optimization APIs

## 🤝 Need Help?

- Check the [Troubleshooting Guide](../development/troubleshooting.md)
- Review [Configuration Options](../setup/configuration.md)
- Join our [Community Discussions](https://github.com/your-repo/django-graphql-auto/discussions)
