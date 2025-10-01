Performance
===========

Comprehensive performance optimization guide for Django GraphQL Auto applications.

Overview
--------

Performance is critical for GraphQL applications, especially when dealing with complex queries and large datasets. This guide covers optimization strategies, monitoring techniques, and best practices for achieving optimal performance.

Performance Philosophy
----------------------

**Our Performance Approach:**

1. **Measure First**: Always profile before optimizing
2. **Optimize Bottlenecks**: Focus on the slowest components
3. **Prevent N+1 Queries**: Use DataLoader and select_related
4. **Cache Strategically**: Cache expensive operations
5. **Monitor Continuously**: Track performance metrics in production

**Performance Pyramid:**

.. code-block:: text

   ┌─────────────────────┐
   │   Application       │  ← Business logic optimization
   │   Optimization      │
   ├─────────────────────┤
   │   GraphQL           │  ← Query optimization, DataLoader
   │   Optimization      │
   ├─────────────────────┤
   │   Database          │  ← Query optimization, indexing
   │   Optimization      │
   ├─────────────────────┤
   │   Infrastructure    │  ← Caching, CDN, load balancing
   │   Optimization      │
   └─────────────────────┘

Performance Monitoring
----------------------

Metrics Collection
~~~~~~~~~~~~~~~~~~

**Performance Metrics Configuration:**

.. code-block:: python

   # settings/performance.py
   
   # GraphQL Auto Performance Settings
   GRAPHQL_AUTO = {
       'PERFORMANCE_MONITORING': True,
       'SLOW_QUERY_THRESHOLD': 1000,  # milliseconds
       'ENABLE_QUERY_COMPLEXITY_ANALYSIS': True,
       'MAX_QUERY_COMPLEXITY': 1000,
       'ENABLE_DATALOADER': True,
       'CACHE_ENABLED': True,
       'CACHE_TTL': 300,  # 5 minutes
   }
   
   # Performance Monitoring Middleware
   MIDDLEWARE = [
       'django_graphql_auto.middleware.PerformanceMiddleware',
       # ... other middleware
   ]
   
   # Logging Configuration for Performance
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'handlers': {
           'performance_file': {
               'class': 'logging.FileHandler',
               'filename': 'performance.log',
               'formatter': 'verbose',
           },
       },
       'loggers': {
           'django_graphql_auto.performance': {
               'handlers': ['performance_file'],
               'level': 'INFO',
               'propagate': False,
           },
       },
   }

**Custom Performance Middleware:**

.. code-block:: python

   # django_graphql_auto/middleware/performance.py
   import time
   import logging
   from django.utils.deprecation import MiddlewareMixin
   from django.conf import settings
   
   logger = logging.getLogger('django_graphql_auto.performance')
   
   class PerformanceMiddleware(MiddlewareMixin):
       """Middleware to monitor GraphQL performance."""
       
       def __init__(self, get_response):
           super().__init__(get_response)
           self.slow_query_threshold = getattr(
               settings, 'GRAPHQL_AUTO', {}
           ).get('SLOW_QUERY_THRESHOLD', 1000)
       
       def process_request(self, request):
           if request.path == '/graphql/':
               request._performance_start = time.time()
               request._db_queries_start = len(connection.queries)
       
       def process_response(self, request, response):
           if hasattr(request, '_performance_start'):
               execution_time = (time.time() - request._performance_start) * 1000
               db_queries = len(connection.queries) - request._db_queries_start
               
               # Log performance metrics
               metrics = {
                   'execution_time_ms': execution_time,
                   'db_queries': db_queries,
                   'status_code': response.status_code,
                   'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
               }
               
               if execution_time > self.slow_query_threshold:
                   logger.warning(f"Slow GraphQL query: {execution_time:.2f}ms", extra=metrics)
               else:
                   logger.info(f"GraphQL query: {execution_time:.2f}ms", extra=metrics)
               
               # Add performance headers
               response['X-GraphQL-Execution-Time'] = f"{execution_time:.2f}ms"
               response['X-GraphQL-DB-Queries'] = str(db_queries)
           
           return response

Query Complexity Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~

**Query Complexity Calculator:**

.. code-block:: python

   # django_graphql_auto/performance/complexity.py
   import logging
   from graphql import visit, Visitor
   
   logger = logging.getLogger(__name__)
   
   class QueryComplexityAnalyzer(Visitor):
       """Analyze GraphQL query complexity."""
       
       def __init__(self, max_complexity=1000):
           self.max_complexity = max_complexity
           self.complexity = 0
           self.depth = 0
           self.max_depth = 0
       
       def enter_field(self, node, *_):
           """Calculate complexity when entering a field."""
           self.depth += 1
           self.max_depth = max(self.max_depth, self.depth)
           
           # Base complexity for each field
           field_complexity = 1
           
           # Increase complexity for list fields
           if self._is_list_field(node):
               field_complexity *= 10
           
           # Increase complexity for nested fields
           field_complexity *= self.depth
           
           self.complexity += field_complexity
           
           # Check if complexity exceeds limit
           if self.complexity > self.max_complexity:
               raise ComplexityError(
                   f"Query complexity {self.complexity} exceeds maximum {self.max_complexity}"
               )
       
       def leave_field(self, node, *_):
           """Decrease depth when leaving a field."""
           self.depth -= 1
       
       def _is_list_field(self, node):
           """Check if field returns a list."""
           # This would need to be implemented based on schema introspection
           return node.name.value.endswith('s')  # Simple heuristic
   
   class ComplexityError(Exception):
       """Exception raised when query complexity is too high."""
       pass
   
   def analyze_query_complexity(query_ast, max_complexity=1000):
       """Analyze the complexity of a GraphQL query."""
       analyzer = QueryComplexityAnalyzer(max_complexity)
       visit(query_ast, analyzer)
       
       return {
           'complexity': analyzer.complexity,
           'max_depth': analyzer.max_depth,
           'within_limits': analyzer.complexity <= max_complexity
       }

Database Optimization
---------------------

N+1 Query Prevention
~~~~~~~~~~~~~~~~~~~~

**DataLoader Implementation:**

.. code-block:: python

   # django_graphql_auto/dataloaders.py
   from promise import Promise
   from promise.dataloader import DataLoader
   from django.db import models
   from collections import defaultdict
   import logging
   
   logger = logging.getLogger(__name__)
   
   class ModelDataLoader(DataLoader):
       """Generic DataLoader for Django models."""
       
       def __init__(self, model_class, **kwargs):
           self.model_class = model_class
           super().__init__(**kwargs)
       
       def batch_load_fn(self, keys):
           """Batch load function for the DataLoader."""
           logger.debug(f"DataLoader batch loading {len(keys)} {self.model_class.__name__} objects")
           
           # Fetch all objects in a single query
           objects = self.model_class.objects.filter(id__in=keys)
           object_map = {obj.id: obj for obj in objects}
           
           # Return objects in the same order as keys
           return Promise.resolve([object_map.get(key) for key in keys])
   
   class RelatedDataLoader(DataLoader):
       """DataLoader for related objects (foreign keys)."""
       
       def __init__(self, model_class, related_field, **kwargs):
           self.model_class = model_class
           self.related_field = related_field
           super().__init__(**kwargs)
       
       def batch_load_fn(self, keys):
           """Batch load related objects."""
           logger.debug(f"DataLoader batch loading related {self.model_class.__name__} objects")
           
           # Build filter for related field
           filter_kwargs = {f"{self.related_field}__in": keys}
           objects = self.model_class.objects.filter(**filter_kwargs)
           
           # Group objects by related field value
           grouped = defaultdict(list)
           for obj in objects:
               related_value = getattr(obj, self.related_field + '_id')
               grouped[related_value].append(obj)
           
           # Return lists in the same order as keys
           return Promise.resolve([grouped.get(key, []) for key in keys])
   
   class DataLoaderRegistry:
       """Registry for managing DataLoaders."""
       
       def __init__(self):
           self.loaders = {}
       
       def get_loader(self, model_class, loader_type='model'):
           """Get or create a DataLoader for a model."""
           cache_key = f"{model_class.__name__}_{loader_type}"
           
           if cache_key not in self.loaders:
               if loader_type == 'model':
                   self.loaders[cache_key] = ModelDataLoader(model_class)
               # Add other loader types as needed
           
           return self.loaders[cache_key]
       
       def get_related_loader(self, model_class, related_field):
           """Get or create a DataLoader for related objects."""
           cache_key = f"{model_class.__name__}_{related_field}_related"
           
           if cache_key not in self.loaders:
               self.loaders[cache_key] = RelatedDataLoader(model_class, related_field)
           
           return self.loaders[cache_key]

**Optimized Resolvers with DataLoader:**

.. code-block:: python

   # django_graphql_auto/resolvers/optimized.py
   from django_graphql_auto.dataloaders import DataLoaderRegistry
   from django.db import models
   import logging
   
   logger = logging.getLogger(__name__)
   
   class OptimizedResolver:
       """Base resolver with DataLoader optimization."""
       
       def __init__(self):
           self.dataloader_registry = DataLoaderRegistry()
       
       def resolve_user(self, info, id):
           """Resolve user using DataLoader."""
           from tests.models import User
           loader = self.dataloader_registry.get_loader(User)
           return loader.load(id)
       
       def resolve_user_posts(self, info, user_id):
           """Resolve user posts using DataLoader."""
           from tests.models import Post
           loader = self.dataloader_registry.get_related_loader(Post, 'author')
           return loader.load(user_id)
       
       def resolve_posts_with_authors(self, info, **kwargs):
           """Resolve posts with authors using select_related."""
           from tests.models import Post
           
           # Use select_related to avoid N+1 queries
           queryset = Post.objects.select_related('author', 'category')
           
           # Apply filters
           if 'author_id' in kwargs:
               queryset = queryset.filter(author_id=kwargs['author_id'])
           
           logger.debug(f"Executing optimized query: {queryset.query}")
           return queryset

Query Optimization
~~~~~~~~~~~~~~~~~~

**Optimized QuerySet Patterns:**

.. code-block:: python

   # django_graphql_auto/optimization/queries.py
   from django.db import models
   from django.db.models import Prefetch, Count, Q
   import logging
   
   logger = logging.getLogger(__name__)
   
   class QueryOptimizer:
       """Optimize Django QuerySets for GraphQL."""
       
       def optimize_user_query(self, queryset, info):
           """Optimize user query based on requested fields."""
           requested_fields = self._get_requested_fields(info)
           
           # Apply select_related for foreign keys
           if 'profile' in requested_fields:
               queryset = queryset.select_related('profile')
           
           # Apply prefetch_related for reverse foreign keys
           if 'posts' in requested_fields:
               posts_prefetch = Prefetch(
                   'posts',
                   queryset=models.Post.objects.select_related('category')
               )
               queryset = queryset.prefetch_related(posts_prefetch)
           
           # Add annotations for computed fields
           if 'post_count' in requested_fields:
               queryset = queryset.annotate(post_count=Count('posts'))
           
           logger.debug(f"Optimized user query: {queryset.query}")
           return queryset
       
       def optimize_post_query(self, queryset, info):
           """Optimize post query based on requested fields."""
           requested_fields = self._get_requested_fields(info)
           
           # Always select related author and category to avoid N+1
           queryset = queryset.select_related('author', 'category')
           
           # Prefetch comments if requested
           if 'comments' in requested_fields:
               comments_prefetch = Prefetch(
                   'comments',
                   queryset=models.Comment.objects.select_related('author')
               )
               queryset = queryset.prefetch_related(comments_prefetch)
           
           # Add full-text search optimization
           if 'search' in requested_fields:
               queryset = queryset.extra(
                   select={'relevance': "MATCH(title, content) AGAINST(%s)"},
                   select_params=[requested_fields['search']],
                   where=["MATCH(title, content) AGAINST(%s)"],
                   params=[requested_fields['search']]
               )
           
           return queryset
       
       def _get_requested_fields(self, info):
           """Extract requested fields from GraphQL info."""
           # This would parse the GraphQL selection set
           # Simplified implementation
           return set()

**Database Indexing Strategy:**

.. code-block:: python

   # models.py - Optimized model definitions
   from django.db import models
   
   class User(models.Model):
       username = models.CharField(max_length=150, unique=True, db_index=True)
       email = models.EmailField(unique=True, db_index=True)
       first_name = models.CharField(max_length=30, db_index=True)
       last_name = models.CharField(max_length=30, db_index=True)
       is_active = models.BooleanField(default=True, db_index=True)
       created_at = models.DateTimeField(auto_now_add=True, db_index=True)
       
       class Meta:
           indexes = [
               models.Index(fields=['username', 'email']),
               models.Index(fields=['created_at', 'is_active']),
               models.Index(fields=['last_name', 'first_name']),
           ]
   
   class Post(models.Model):
       title = models.CharField(max_length=200, db_index=True)
       content = models.TextField()
       author = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
       category = models.ForeignKey('Category', on_delete=models.CASCADE, db_index=True)
       published = models.BooleanField(default=False, db_index=True)
       created_at = models.DateTimeField(auto_now_add=True, db_index=True)
       updated_at = models.DateTimeField(auto_now=True)
       
       class Meta:
           indexes = [
               models.Index(fields=['author', 'published']),
               models.Index(fields=['category', 'created_at']),
               models.Index(fields=['published', 'created_at']),
               models.Index(fields=['title'], name='post_title_idx'),
           ]
           
           # Full-text search index (MySQL/PostgreSQL)
           # This would be database-specific

Caching Strategies
------------------

Query Result Caching
~~~~~~~~~~~~~~~~~~~~~

**Redis-based Query Caching:**

.. code-block:: python

   # django_graphql_auto/caching/query_cache.py
   import hashlib
   import json
   import logging
   from django.core.cache import cache
   from django.conf import settings
   
   logger = logging.getLogger(__name__)
   
   class GraphQLQueryCache:
       """Cache GraphQL query results."""
       
       def __init__(self):
           self.enabled = getattr(settings, 'GRAPHQL_AUTO', {}).get('CACHE_ENABLED', False)
           self.ttl = getattr(settings, 'GRAPHQL_AUTO', {}).get('CACHE_TTL', 300)
           self.cache_prefix = 'graphql_query:'
       
       def get_cache_key(self, query, variables=None, user_id=None):
           """Generate cache key for query."""
           cache_data = {
               'query': query,
               'variables': variables or {},
               'user_id': user_id,
           }
           
           # Create hash of query data
           cache_string = json.dumps(cache_data, sort_keys=True)
           cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
           
           return f"{self.cache_prefix}{cache_hash}"
       
       def get(self, query, variables=None, user_id=None):
           """Get cached query result."""
           if not self.enabled:
               return None
           
           cache_key = self.get_cache_key(query, variables, user_id)
           result = cache.get(cache_key)
           
           if result:
               logger.debug(f"Cache hit for query: {cache_key}")
           else:
               logger.debug(f"Cache miss for query: {cache_key}")
           
           return result
       
       def set(self, query, variables, result, user_id=None, ttl=None):
           """Cache query result."""
           if not self.enabled:
               return
           
           cache_key = self.get_cache_key(query, variables, user_id)
           cache_ttl = ttl or self.ttl
           
           cache.set(cache_key, result, cache_ttl)
           logger.debug(f"Cached query result: {cache_key} (TTL: {cache_ttl}s)")
       
       def invalidate_pattern(self, pattern):
           """Invalidate cache entries matching pattern."""
           # This would require a cache backend that supports pattern deletion
           # Redis with django-redis supports this
           try:
               cache.delete_pattern(f"{self.cache_prefix}*{pattern}*")
               logger.info(f"Invalidated cache pattern: {pattern}")
           except AttributeError:
               logger.warning("Cache backend doesn't support pattern deletion")

**Field-level Caching:**

.. code-block:: python

   # django_graphql_auto/caching/field_cache.py
   import functools
   import logging
   from django.core.cache import cache
   
   logger = logging.getLogger(__name__)
   
   def cache_field(ttl=300, key_func=None):
       """Decorator to cache GraphQL field results."""
       def decorator(resolver_func):
           @functools.wraps(resolver_func)
           def wrapper(self, info, **kwargs):
               # Generate cache key
               if key_func:
                   cache_key = key_func(self, info, **kwargs)
               else:
                   cache_key = f"field:{resolver_func.__name__}:{hash(str(kwargs))}"
               
               # Try to get from cache
               result = cache.get(cache_key)
               if result is not None:
                   logger.debug(f"Field cache hit: {cache_key}")
                   return result
               
               # Execute resolver
               result = resolver_func(self, info, **kwargs)
               
               # Cache result
               cache.set(cache_key, result, ttl)
               logger.debug(f"Field cached: {cache_key}")
               
               return result
           
           return wrapper
       return decorator
   
   # Usage example
   class CachedResolver:
       @cache_field(ttl=600)  # Cache for 10 minutes
       def resolve_expensive_computation(self, info, **kwargs):
           """Expensive computation that should be cached."""
           # Simulate expensive operation
           import time
           time.sleep(1)
           return "expensive_result"
       
       @cache_field(
           ttl=300,
           key_func=lambda self, info, user_id: f"user_posts:{user_id}"
       )
       def resolve_user_posts(self, info, user_id):
           """Cache user posts with custom key."""
           from tests.models import Post
           return Post.objects.filter(author_id=user_id)

Model-level Caching
~~~~~~~~~~~~~~~~~~~

**Cached Model Manager:**

.. code-block:: python

   # django_graphql_auto/caching/models.py
   from django.db import models
   from django.core.cache import cache
   import logging
   
   logger = logging.getLogger(__name__)
   
   class CachedManager(models.Manager):
       """Manager with built-in caching."""
       
       def __init__(self, cache_ttl=300):
           super().__init__()
           self.cache_ttl = cache_ttl
       
       def get_cached(self, **kwargs):
           """Get object with caching."""
           cache_key = self._get_cache_key(**kwargs)
           
           # Try cache first
           obj = cache.get(cache_key)
           if obj:
               logger.debug(f"Model cache hit: {cache_key}")
               return obj
           
           # Get from database
           obj = self.get(**kwargs)
           
           # Cache the object
           cache.set(cache_key, obj, self.cache_ttl)
           logger.debug(f"Model cached: {cache_key}")
           
           return obj
       
       def _get_cache_key(self, **kwargs):
           """Generate cache key for model lookup."""
           model_name = self.model.__name__.lower()
           key_parts = [f"{k}:{v}" for k, v in sorted(kwargs.items())]
           return f"model:{model_name}:{'_'.join(key_parts)}"
   
   # Usage in models
   class User(models.Model):
       username = models.CharField(max_length=150, unique=True)
       email = models.EmailField(unique=True)
       
       objects = models.Manager()  # Default manager
       cached = CachedManager(cache_ttl=600)  # Cached manager
       
       def save(self, *args, **kwargs):
           """Override save to invalidate cache."""
           super().save(*args, **kwargs)
           
           # Invalidate related cache entries
           cache_keys = [
               f"model:user:id:{self.id}",
               f"model:user:username:{self.username}",
               f"model:user:email:{self.email}",
           ]
           
           for key in cache_keys:
               cache.delete(key)
               logger.debug(f"Invalidated cache: {key}")

Performance Testing
-------------------

Load Testing
~~~~~~~~~~~~

**GraphQL Load Testing with Locust:**

.. code-block:: python

   # tests/performance/locustfile.py
   from locust import HttpUser, task, between
   import json
   import random
   
   class GraphQLUser(HttpUser):
       wait_time = between(1, 3)
       
       def on_start(self):
           """Setup for each user."""
           self.graphql_endpoint = "/graphql/"
           self.queries = self._load_test_queries()
       
       @task(3)
       def query_users(self):
           """Test user queries."""
           query = '''
           query GetUsers($first: Int) {
               users(first: $first) {
                   edges {
                       node {
                           id
                           username
                           email
                       }
                   }
               }
           }
           '''
           
           variables = {"first": random.randint(10, 50)}
           self._execute_query(query, variables)
       
       @task(2)
       def query_user_with_posts(self):
           """Test user with posts query."""
           query = '''
           query GetUserWithPosts($userId: ID!) {
               user(id: $userId) {
                   username
                   posts {
                       edges {
                           node {
                               title
                               createdAt
                           }
                       }
                   }
               }
           }
           '''
           
           variables = {"userId": str(random.randint(1, 100))}
           self._execute_query(query, variables)
       
       @task(1)
       def complex_query(self):
           """Test complex nested query."""
           query = '''
           query ComplexQuery {
               users(first: 10) {
                   edges {
                       node {
                           username
                           posts(first: 5) {
                               edges {
                                   node {
                                       title
                                       category {
                                           name
                                       }
                                       comments(first: 3) {
                                           edges {
                                               node {
                                                   content
                                                   author {
                                                       username
                                                   }
                                               }
                                           }
                                       }
                                   }
                               }
                           }
                       }
                   }
               }
           }
           '''
           
           self._execute_query(query)
       
       def _execute_query(self, query, variables=None):
           """Execute GraphQL query."""
           payload = {
               "query": query,
               "variables": variables or {}
           }
           
           with self.client.post(
               self.graphql_endpoint,
               json=payload,
               catch_response=True
           ) as response:
               if response.status_code == 200:
                   data = response.json()
                   if "errors" in data:
                       response.failure(f"GraphQL errors: {data['errors']}")
                   else:
                       response.success()
               else:
                   response.failure(f"HTTP {response.status_code}")
       
       def _load_test_queries(self):
           """Load test queries from file."""
           # This would load queries from a file
           return []

**Performance Benchmarking:**

.. code-block:: python

   # tests/performance/benchmark.py
   import time
   import statistics
   import logging
   from django.test import TestCase, Client
   from tests.factories import UserFactory, PostFactory
   
   logger = logging.getLogger(__name__)
   
   class PerformanceBenchmark(TestCase):
       """Benchmark GraphQL query performance."""
       
       def setUp(self):
           self.client = Client()
           self.create_test_data()
       
       def create_test_data(self):
           """Create test data for benchmarking."""
           # Create users
           self.users = UserFactory.create_batch(100)
           
           # Create posts for each user
           for user in self.users:
               PostFactory.create_batch(10, author=user)
       
       def benchmark_query(self, query, variables=None, iterations=10):
           """Benchmark a GraphQL query."""
           execution_times = []
           
           for i in range(iterations):
               start_time = time.time()
               
               response = self.client.post(
                   '/graphql/',
                   {
                       'query': query,
                       'variables': variables or {}
                   },
                   content_type='application/json'
               )
               
               end_time = time.time()
               execution_time = (end_time - start_time) * 1000  # Convert to ms
               execution_times.append(execution_time)
               
               # Verify response is successful
               self.assertEqual(response.status_code, 200)
               data = response.json()
               self.assertNotIn('errors', data)
           
           # Calculate statistics
           stats = {
               'mean': statistics.mean(execution_times),
               'median': statistics.median(execution_times),
               'min': min(execution_times),
               'max': max(execution_times),
               'stdev': statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
           }
           
           logger.info(f"Query benchmark results: {stats}")
           return stats
       
       def test_user_list_performance(self):
           """Benchmark user list query."""
           query = '''
           query GetUsers {
               users(first: 50) {
                   edges {
                       node {
                           id
                           username
                           email
                       }
                   }
               }
           }
           '''
           
           stats = self.benchmark_query(query)
           
           # Assert performance requirements
           self.assertLess(stats['mean'], 100)  # Average < 100ms
           self.assertLess(stats['max'], 500)   # Max < 500ms
       
       def test_complex_query_performance(self):
           """Benchmark complex nested query."""
           query = '''
           query ComplexQuery {
               users(first: 10) {
                   edges {
                       node {
                           username
                           posts(first: 5) {
                               edges {
                                   node {
                                       title
                                       category {
                                           name
                                       }
                                   }
                               }
                           }
                       }
                   }
               }
           }
           '''
           
           stats = self.benchmark_query(query)
           
           # More lenient requirements for complex queries
           self.assertLess(stats['mean'], 500)   # Average < 500ms
           self.assertLess(stats['max'], 2000)   # Max < 2s

Memory Profiling
~~~~~~~~~~~~~~~~

**Memory Usage Analysis:**

.. code-block:: python

   # tests/performance/memory_profiling.py
   import psutil
   import os
   import gc
   from django.test import TestCase
   from memory_profiler import profile
   
   class MemoryProfiler(TestCase):
       """Profile memory usage of GraphQL operations."""
       
       def setUp(self):
           self.process = psutil.Process(os.getpid())
           self.initial_memory = self.process.memory_info().rss
       
       def tearDown(self):
           # Force garbage collection
           gc.collect()
           
           final_memory = self.process.memory_info().rss
           memory_diff = final_memory - self.initial_memory
           
           if memory_diff > 50 * 1024 * 1024:  # 50MB threshold
               self.fail(f"Memory usage increased by {memory_diff / 1024 / 1024:.1f}MB")
       
       @profile
       def test_large_query_memory_usage(self):
           """Profile memory usage of large queries."""
           # Create large dataset
           from tests.factories import UserFactory, PostFactory
           
           users = UserFactory.create_batch(1000)
           for user in users:
               PostFactory.create_batch(10, author=user)
           
           # Execute large query
           query = '''
           query LargeQuery {
               users(first: 1000) {
                   edges {
                       node {
                           username
                           posts {
                               edges {
                                   node {
                                       title
                                       content
                                   }
                               }
                           }
                       }
                   }
               }
           }
           '''
           
           response = self.client.post('/graphql/', {'query': query})
           self.assertEqual(response.status_code, 200)

Production Optimization
-----------------------

Server Configuration
~~~~~~~~~~~~~~~~~~~~

**Gunicorn Configuration:**

.. code-block:: python

   # gunicorn.conf.py
   import multiprocessing
   
   # Server socket
   bind = "0.0.0.0:8000"
   backlog = 2048
   
   # Worker processes
   workers = multiprocessing.cpu_count() * 2 + 1
   worker_class = "gevent"
   worker_connections = 1000
   max_requests = 1000
   max_requests_jitter = 50
   
   # Timeout settings
   timeout = 30
   keepalive = 2
   
   # Memory management
   preload_app = True
   
   # Logging
   accesslog = "/var/log/gunicorn/access.log"
   errorlog = "/var/log/gunicorn/error.log"
   loglevel = "info"
   
   # Performance tuning
   def when_ready(server):
       server.log.info("Server is ready. Spawning workers")
   
   def worker_int(worker):
       worker.log.info("worker received INT or QUIT signal")
   
   def pre_fork(server, worker):
       server.log.info("Worker spawned (pid: %s)", worker.pid)

**Nginx Configuration:**

.. code-block:: nginx

   # nginx.conf
   upstream django_app {
       server 127.0.0.1:8000;
       keepalive 32;
   }
   
   server {
       listen 80;
       server_name your-domain.com;
       
       # GraphQL endpoint optimization
       location /graphql/ {
           proxy_pass http://django_app;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           
           # Connection settings
           proxy_http_version 1.1;
           proxy_set_header Connection "";
           
           # Timeout settings
           proxy_connect_timeout 30s;
           proxy_send_timeout 30s;
           proxy_read_timeout 30s;
           
           # Buffer settings
           proxy_buffering on;
           proxy_buffer_size 4k;
           proxy_buffers 8 4k;
           
           # Compression
           gzip on;
           gzip_types application/json;
       }
       
       # Static files
       location /static/ {
           alias /path/to/static/files/;
           expires 1y;
           add_header Cache-Control "public, immutable";
       }
   }

Database Optimization
~~~~~~~~~~~~~~~~~~~~~

**PostgreSQL Configuration:**

.. code-block:: sql

   -- postgresql.conf optimizations
   
   -- Memory settings
   shared_buffers = 256MB
   effective_cache_size = 1GB
   work_mem = 4MB
   maintenance_work_mem = 64MB
   
   -- Connection settings
   max_connections = 100
   
   -- Query optimization
   random_page_cost = 1.1
   effective_io_concurrency = 200
   
   -- WAL settings
   wal_buffers = 16MB
   checkpoint_completion_target = 0.9
   
   -- Logging
   log_min_duration_statement = 1000  -- Log slow queries
   log_statement = 'mod'  -- Log modifications

**Database Monitoring Queries:**

.. code-block:: sql

   -- Find slow queries
   SELECT query, mean_time, calls, total_time
   FROM pg_stat_statements
   ORDER BY mean_time DESC
   LIMIT 10;
   
   -- Find queries with high I/O
   SELECT query, shared_blks_read, shared_blks_hit
   FROM pg_stat_statements
   WHERE shared_blks_read > 1000
   ORDER BY shared_blks_read DESC;
   
   -- Check index usage
   SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
   FROM pg_stat_user_indexes
   ORDER BY idx_scan DESC;

Monitoring and Alerting
-----------------------

Performance Metrics
~~~~~~~~~~~~~~~~~~~

**Custom Metrics Collection:**

.. code-block:: python

   # django_graphql_auto/monitoring/metrics.py
   import time
   import logging
   from django.core.cache import cache
   from django.conf import settings
   
   logger = logging.getLogger(__name__)
   
   class PerformanceMetrics:
       """Collect and store performance metrics."""
       
       def __init__(self):
           self.enabled = getattr(settings, 'PERFORMANCE_MONITORING', False)
       
       def record_query_time(self, query_hash, execution_time):
           """Record query execution time."""
           if not self.enabled:
               return
           
           # Store in cache for aggregation
           cache_key = f"metrics:query_time:{query_hash}"
           current_data = cache.get(cache_key, {'times': [], 'count': 0})
           
           current_data['times'].append(execution_time)
           current_data['count'] += 1
           
           # Keep only last 100 measurements
           if len(current_data['times']) > 100:
               current_data['times'] = current_data['times'][-100:]
           
           cache.set(cache_key, current_data, timeout=3600)
       
       def record_db_queries(self, query_count):
           """Record database query count."""
           if not self.enabled:
               return
           
           cache_key = "metrics:db_queries"
           current_data = cache.get(cache_key, {'counts': [], 'total': 0})
           
           current_data['counts'].append(query_count)
           current_data['total'] += query_count
           
           if len(current_data['counts']) > 100:
               current_data['counts'] = current_data['counts'][-100:]
           
           cache.set(cache_key, current_data, timeout=3600)
       
       def get_performance_summary(self):
           """Get performance metrics summary."""
           if not self.enabled:
               return {}
           
           # Aggregate metrics from cache
           summary = {
               'query_times': self._get_query_time_stats(),
               'db_queries': self._get_db_query_stats(),
               'timestamp': time.time(),
           }
           
           return summary
       
       def _get_query_time_stats(self):
           """Get query time statistics."""
           # This would aggregate data from all query time metrics
           return {
               'average': 0,
               'median': 0,
               'p95': 0,
               'p99': 0,
           }
       
       def _get_db_query_stats(self):
           """Get database query statistics."""
           cache_key = "metrics:db_queries"
           data = cache.get(cache_key, {'counts': [], 'total': 0})
           
           if not data['counts']:
               return {'average': 0, 'total': 0}
           
           return {
               'average': sum(data['counts']) / len(data['counts']),
               'total': data['total'],
           }

---

*This performance guide provides comprehensive strategies for optimizing Django GraphQL Auto applications. Regular monitoring and profiling are essential for maintaining optimal performance in production environments.*