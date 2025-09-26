# Best Practices Guide

## Django GraphQL Auto-Generation System - Best Practices

This guide provides comprehensive best practices for developing, deploying, and maintaining applications using the Django GraphQL Auto-Generation System. Following these practices will help you build robust, secure, and performant GraphQL APIs.

## Table of Contents

- [Project Structure](#project-structure)
- [Model Design](#model-design)
- [Schema Configuration](#schema-configuration)
- [Security Best Practices](#security-best-practices)
- [Performance Optimization](#performance-optimization)
- [Error Handling](#error-handling)
- [Testing Strategies](#testing-strategies)
- [Documentation](#documentation)
- [Deployment](#deployment)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Code Quality](#code-quality)
- [Team Collaboration](#team-collaboration)

## Project Structure

### Recommended Directory Layout

```
myproject/
├── apps/
│   ├── users/
│   │   ├── models.py
│   │   ├── graphql/
│   │   │   ├── __init__.py
│   │   │   ├── types.py
│   │   │   ├── queries.py
│   │   │   ├── mutations.py
│   │   │   └── resolvers.py
│   │   └── tests/
│   │       ├── test_models.py
│   │       ├── test_graphql.py
│   │       └── test_resolvers.py
│   ├── products/
│   └── orders/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── graphql/
│   │   ├── __init__.py
│   │   ├── schema.py
│   │   ├── middleware.py
│   │   └── permissions.py
│   └── urls.py
├── docs/
├── requirements/
└── tests/
```

### Configuration Organization

**Separate settings by environment:**

```python
# config/settings/base.py
GRAPHQL_AUTO_GEN = {
    'SCHEMA_CONFIG': {
        'models': [
            'users.models.User',
            'products.models.Product',
            'orders.models.Order',
        ],
        'security': {
            'authentication_required': True,
            'rate_limiting': {'enabled': True},
        },
    }
}

# config/settings/development.py
from .base import *

GRAPHQL_AUTO_GEN['SCHEMA_CONFIG'].update({
    'debug': True,
    'enable_introspection': True,
    'log_queries': True,
})

# config/settings/production.py
from .base import *

GRAPHQL_AUTO_GEN['SCHEMA_CONFIG'].update({
    'debug': False,
    'enable_introspection': False,
    'security': {
        'authentication_required': True,
        'rate_limiting': {
            'enabled': True,
            'requests_per_minute': 100,
        },
        'query_analysis': {
            'enabled': True,
            'max_complexity': 1000,
            'max_depth': 10,
        },
    },
})
```

## Model Design

### GraphQL-Friendly Models

**Use descriptive field names:**

```python
class User(models.Model):
    # Good: Clear, descriptive names
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Nom d'utilisateur"
    )
    email_address = models.EmailField(
        unique=True,
        verbose_name="Adresse e-mail"
    )
    date_joined = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'inscription"
    )
    
    # Avoid: Ambiguous abbreviations
    # usr_nm = models.CharField(max_length=150)  # Bad
    # dt_jnd = models.DateTimeField()  # Bad
```

**Design for GraphQL relationships:**

```python
class Product(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name="Nom du produit"
    )
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        related_name='products',  # Clear reverse relationship
        verbose_name="Catégorie"
    )
    tags = models.ManyToManyField(
        'Tag',
        related_name='products',
        blank=True,
        verbose_name="Étiquettes"
    )
    
    class GraphQLMeta:
        # Optimize for common query patterns
        prefetch_related = ['tags']
        select_related = ['category']
        
        # Define filterable fields
        filterable_fields = {
            'name': ['exact', 'icontains', 'startswith'],
            'category': ['exact'],
            'tags': ['exact', 'in'],
            'created_at': ['gte', 'lte', 'range'],
        }
```

### Field-Level Configuration

**Configure field exposure and permissions:**

```python
class User(models.Model):
    username = models.CharField(max_length=150)
    email = models.EmailField()
    password = models.CharField(max_length=128)
    social_security_number = models.CharField(max_length=11, blank=True)
    
    class GraphQLMeta:
        # Expose only safe fields by default
        fields = ['id', 'username', 'email', 'date_joined']
        
        # Explicitly exclude sensitive fields
        exclude_fields = ['password', 'social_security_number']
        
        # Field-level permissions
        field_permissions = {
            'email': ['users.view_user_email'],
            'social_security_number': ['users.view_sensitive_data'],
        }
        
        # Custom field descriptions for GraphQL schema
        descriptions = {
            'username': "Unique identifier for the user",
            'email': "User's email address for communication",
            'date_joined': "When the user account was created",
        }
```

### Computed Fields

**Add computed fields for common use cases:**

```python
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(Product, through='OrderItem')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class GraphQLMeta:
        computed_fields = [
            'total_amount',
            'item_count',
            'status_display',
        ]
    
    def resolve_total_amount(self, info):
        """Calculate total order amount."""
        return self.items.aggregate(
            total=Sum(F('orderitem__quantity') * F('orderitem__price'))
        )['total'] or Decimal('0.00')
    
    def resolve_item_count(self, info):
        """Count total items in order."""
        return self.items.aggregate(
            count=Sum('orderitem__quantity')
        )['count'] or 0
    
    def resolve_status_display(self, info):
        """Human-readable status."""
        return self.get_status_display()
```

## Schema Configuration

### Modular Configuration

**Organize configuration by feature:**

```python
# config/graphql/base_config.py
BASE_GRAPHQL_CONFIG = {
    'debug': False,
    'enable_introspection': False,
    'security': {
        'authentication_required': True,
        'rate_limiting': {'enabled': True},
    },
}

# config/graphql/models_config.py
MODELS_CONFIG = {
    'models': [
        'users.models.User',
        'users.models.Profile',
        'products.models.Product',
        'products.models.Category',
        'orders.models.Order',
        'orders.models.OrderItem',
    ],
    'exclude_models': [
        'auth.models.Permission',
        'contenttypes.models.ContentType',
    ],
}

# config/graphql/security_config.py
SECURITY_CONFIG = {
    'security': {
        'authentication_classes': [
            'graphql_auto_gen.auth.JWTAuthentication',
            'rest_framework.authentication.SessionAuthentication',
        ],
        'permission_classes': ['IsAuthenticated'],
        'query_analysis': {
            'enabled': True,
            'max_complexity': 1000,
            'max_depth': 10,
        },
        'rate_limiting': {
            'enabled': True,
            'requests_per_minute': 100,
            'burst_limit': 20,
        },
    }
}

# settings.py
from config.graphql.base_config import BASE_GRAPHQL_CONFIG
from config.graphql.models_config import MODELS_CONFIG
from config.graphql.security_config import SECURITY_CONFIG

GRAPHQL_AUTO_GEN = {
    'SCHEMA_CONFIG': {
        **BASE_GRAPHQL_CONFIG,
        **MODELS_CONFIG,
        **SECURITY_CONFIG,
    }
}
```

### Environment-Specific Settings

**Use environment variables for sensitive configuration:**

```python
import os
from django.core.exceptions import ImproperlyConfigured

def get_env_variable(var_name, default=None):
    """Get environment variable or raise exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        error_msg = f"Set the {var_name} environment variable"
        raise ImproperlyConfigured(error_msg)

# Security configuration from environment
GRAPHQL_AUTO_GEN = {
    'SCHEMA_CONFIG': {
        'security': {
            'jwt_settings': {
                'secret_key': get_env_variable('JWT_SECRET_KEY'),
                'algorithm': get_env_variable('JWT_ALGORITHM', 'HS256'),
                'expiration_time': int(get_env_variable('JWT_EXPIRATION', '3600')),
            },
            'rate_limiting': {
                'enabled': get_env_variable('RATE_LIMITING_ENABLED', 'true').lower() == 'true',
                'requests_per_minute': int(get_env_variable('RATE_LIMIT_RPM', '100')),
            },
        },
        'caching': {
            'enabled': get_env_variable('GRAPHQL_CACHING_ENABLED', 'false').lower() == 'true',
            'redis_url': get_env_variable('REDIS_URL', 'redis://localhost:6379/0'),
        },
    }
}
```

## Security Best Practices

### Authentication and Authorization

**Implement robust authentication:**

```python
# config/graphql/auth.py
from graphql_auto_gen.auth import BaseAuthentication
from django.contrib.auth import get_user_model
import jwt

class CustomJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        """Custom JWT authentication with additional security checks."""
        token = self.get_token_from_request(request)
        if not token:
            return None
        
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Additional security checks
            if payload.get('token_type') != 'access':
                return None
            
            if self.is_token_blacklisted(token):
                return None
            
            user = get_user_model().objects.get(id=payload['user_id'])
            
            # Check if user is still active
            if not user.is_active:
                return None
            
            return user
            
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return None
    
    def get_token_from_request(self, request):
        """Extract token from Authorization header."""
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header[7:]
        return None
    
    def is_token_blacklisted(self, token):
        """Check if token is blacklisted."""
        # Implement token blacklisting logic
        return False
```

**Implement fine-grained permissions:**

```python
# config/graphql/permissions.py
from graphql_auto_gen.permissions import BasePermission

class IsOwnerOrReadOnly(BasePermission):
    """Allow read access to all, write access only to owners."""
    
    def has_permission(self, user, info):
        """Check if user has basic permission."""
        return user.is_authenticated
    
    def has_object_permission(self, user, obj, info):
        """Check object-level permissions."""
        # Read permissions for any authenticated user
        if self.is_read_request(info):
            return True
        
        # Write permissions only for owners
        return hasattr(obj, 'owner') and obj.owner == user

class IsAdminOrReadOnly(BasePermission):
    """Allow read access to all, write access only to admins."""
    
    def has_permission(self, user, info):
        if self.is_read_request(info):
            return user.is_authenticated
        return user.is_authenticated and user.is_staff

# Apply to models
class Product(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class GraphQLMeta:
        permission_classes = [IsOwnerOrReadOnly]
```

### Input Validation

**Implement comprehensive input validation:**

```python
# config/graphql/validators.py
from graphql_auto_gen.validators import BaseValidator
import re

class ProductValidator(BaseValidator):
    """Custom validation for Product model."""
    
    def validate_name(self, value):
        """Validate product name."""
        if len(value.strip()) < 3:
            raise ValidationError("Product name must be at least 3 characters long")
        
        # Check for potentially malicious content
        if re.search(r'<script|javascript:|data:', value, re.IGNORECASE):
            raise ValidationError("Invalid characters in product name")
        
        return value.strip()
    
    def validate_price(self, value):
        """Validate product price."""
        if value <= 0:
            raise ValidationError("Price must be greater than zero")
        
        if value > 999999.99:
            raise ValidationError("Price cannot exceed $999,999.99")
        
        return value
    
    def validate_description(self, value):
        """Validate and sanitize description."""
        if value:
            # Remove potentially dangerous HTML
            cleaned = bleach.clean(
                value,
                tags=['p', 'br', 'strong', 'em', 'ul', 'ol', 'li'],
                attributes={},
                strip=True
            )
            return cleaned
        return value

# Apply to model
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    
    class GraphQLMeta:
        validator_class = ProductValidator
```

### Query Security

**Implement query complexity analysis:**

```python
# config/graphql/security.py
from graphql_auto_gen.security import QueryAnalyzer

class CustomQueryAnalyzer(QueryAnalyzer):
    """Custom query complexity analysis."""
    
    def analyze_query(self, query, variables=None):
        """Analyze query complexity and security."""
        analysis = super().analyze_query(query, variables)
        
        # Custom complexity rules
        if analysis.depth > 15:
            raise SecurityError("Query depth exceeds maximum allowed (15)")
        
        if analysis.complexity > 2000:
            raise SecurityError("Query complexity exceeds maximum allowed (2000)")
        
        # Check for suspicious patterns
        if self.has_suspicious_patterns(query):
            raise SecurityError("Query contains suspicious patterns")
        
        return analysis
    
    def has_suspicious_patterns(self, query):
        """Check for potentially malicious query patterns."""
        suspicious_patterns = [
            r'__schema',  # Introspection attempts
            r'__type',    # Type introspection
            r'union.*{.*}.*{.*}',  # Complex union queries
        ]
        
        query_str = str(query)
        for pattern in suspicious_patterns:
            if re.search(pattern, query_str, re.IGNORECASE):
                return True
        
        return False

# Configure in settings
GRAPHQL_AUTO_GEN = {
    'SCHEMA_CONFIG': {
        'security': {
            'query_analyzer_class': 'config.graphql.security.CustomQueryAnalyzer',
        }
    }
}
```

## Performance Optimization

### Database Optimization

**Optimize database queries:**

```python
class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)
    
    class GraphQLMeta:
        # Automatic query optimization
        select_related = ['category']
        prefetch_related = ['tags']
        
        # Custom optimization for specific queries
        query_optimizations = {
            'list': {
                'select_related': ['category', 'category__parent'],
                'prefetch_related': ['tags', 'reviews__user'],
            },
            'detail': {
                'select_related': ['category', 'category__parent'],
                'prefetch_related': [
                    'tags',
                    'reviews__user',
                    'variants__attributes',
                ],
            },
        }
        
        # Database indexes for filtering
        indexes = [
            models.Index(fields=['name', 'category']),
            models.Index(fields=['created_at']),
            models.Index(fields=['price']),
        ]

# Custom resolver with optimization
from graphql_auto_gen.resolvers import BaseResolver

class OptimizedProductResolver(BaseResolver):
    model = Product
    
    def get_queryset(self, info):
        """Optimized queryset based on requested fields."""
        queryset = super().get_queryset(info)
        
        # Analyze requested fields
        requested_fields = self.get_requested_fields(info)
        
        # Apply optimizations based on requested fields
        if 'category' in requested_fields:
            queryset = queryset.select_related('category')
        
        if 'tags' in requested_fields:
            queryset = queryset.prefetch_related('tags')
        
        if 'reviews' in requested_fields:
            queryset = queryset.prefetch_related(
                'reviews__user'
            ).annotate(
                avg_rating=Avg('reviews__rating')
            )
        
        return queryset
```

### Caching Strategies

**Implement multi-level caching:**

```python
# config/graphql/caching.py
from graphql_auto_gen.caching import BaseCacheManager
from django.core.cache import cache
import hashlib

class CustomCacheManager(BaseCacheManager):
    """Custom caching with multiple strategies."""
    
    def get_cache_key(self, query, variables=None, user=None):
        """Generate cache key based on query, variables, and user context."""
        key_parts = [
            hashlib.md5(str(query).encode()).hexdigest(),
            hashlib.md5(str(variables or {}).encode()).hexdigest(),
            str(user.id if user and user.is_authenticated else 'anonymous'),
        ]
        return f"graphql:{':'.join(key_parts)}"
    
    def should_cache_query(self, query, info):
        """Determine if query should be cached."""
        # Don't cache mutations
        if self.is_mutation(query):
            return False
        
        # Don't cache queries with real-time data requirements
        if self.has_realtime_fields(query):
            return False
        
        # Cache expensive queries
        if self.is_expensive_query(query):
            return True
        
        return True
    
    def get_cache_timeout(self, query, info):
        """Get cache timeout based on query type."""
        if self.is_user_specific(query):
            return 300  # 5 minutes for user-specific data
        
        if self.is_static_data(query):
            return 3600  # 1 hour for static data
        
        return 600  # 10 minutes default

# Model-level caching configuration
class Product(models.Model):
    name = models.CharField(max_length=200)
    
    class GraphQLMeta:
        caching = {
            'enabled': True,
            'timeout': 1800,  # 30 minutes
            'vary_on': ['user_id'],  # Cache per user
            'invalidate_on': ['save', 'delete'],  # Auto-invalidation
        }
```

### Query Optimization

**Implement query batching and optimization:**

```python
# config/graphql/optimization.py
from graphql_auto_gen.optimization import QueryOptimizer

class CustomQueryOptimizer(QueryOptimizer):
    """Custom query optimization strategies."""
    
    def optimize_query(self, query, info):
        """Apply various optimization strategies."""
        optimized_query = super().optimize_query(query, info)
        
        # Apply custom optimizations
        optimized_query = self.apply_field_selection(optimized_query, info)
        optimized_query = self.apply_query_batching(optimized_query, info)
        optimized_query = self.apply_connection_optimization(optimized_query, info)
        
        return optimized_query
    
    def apply_field_selection(self, query, info):
        """Optimize field selection to reduce data transfer."""
        # Only select fields that are actually requested
        requested_fields = self.get_requested_fields(info)
        return query.only(*requested_fields)
    
    def apply_query_batching(self, query, info):
        """Batch related queries to reduce database hits."""
        # Implement DataLoader pattern for N+1 query prevention
        return query
    
    def apply_connection_optimization(self, query, info):
        """Optimize pagination queries."""
        # Use cursor-based pagination for better performance
        return query

# Configure optimizer
GRAPHQL_AUTO_GEN = {
    'SCHEMA_CONFIG': {
        'performance': {
            'query_optimizer_class': 'config.graphql.optimization.CustomQueryOptimizer',
            'enable_query_batching': True,
            'enable_field_selection': True,
        }
    }
}
```

## Error Handling

### Structured Error Responses

**Implement consistent error handling:**

```python
# config/graphql/errors.py
from graphql_auto_gen.errors import BaseErrorHandler
import logging

logger = logging.getLogger(__name__)

class CustomErrorHandler(BaseErrorHandler):
    """Custom error handling with structured responses."""
    
    def handle_error(self, error, info):
        """Handle and format errors consistently."""
        # Log error for monitoring
        logger.error(
            f"GraphQL Error: {error}",
            extra={
                'query': str(info.field_name),
                'user': getattr(info.context, 'user', None),
                'variables': getattr(info, 'variable_values', {}),
            }
        )
        
        # Format error based on type
        if isinstance(error, ValidationError):
            return self.format_validation_error(error)
        elif isinstance(error, PermissionDenied):
            return self.format_permission_error(error)
        elif isinstance(error, ObjectDoesNotExist):
            return self.format_not_found_error(error)
        else:
            return self.format_generic_error(error)
    
    def format_validation_error(self, error):
        """Format validation errors."""
        return {
            'message': 'Validation failed',
            'code': 'VALIDATION_ERROR',
            'details': error.message_dict if hasattr(error, 'message_dict') else str(error),
        }
    
    def format_permission_error(self, error):
        """Format permission errors."""
        return {
            'message': 'Permission denied',
            'code': 'PERMISSION_DENIED',
            'details': 'You do not have permission to perform this action',
        }
    
    def format_not_found_error(self, error):
        """Format not found errors."""
        return {
            'message': 'Resource not found',
            'code': 'NOT_FOUND',
            'details': 'The requested resource could not be found',
        }
    
    def format_generic_error(self, error):
        """Format generic errors."""
        # Don't expose internal error details in production
        if settings.DEBUG:
            return {
                'message': str(error),
                'code': 'INTERNAL_ERROR',
                'details': str(error),
            }
        else:
            return {
                'message': 'An internal error occurred',
                'code': 'INTERNAL_ERROR',
                'details': 'Please try again later',
            }

# Configure error handler
GRAPHQL_AUTO_GEN = {
    'SCHEMA_CONFIG': {
        'error_handler_class': 'config.graphql.errors.CustomErrorHandler',
    }
}
```

### Error Monitoring

**Implement comprehensive error monitoring:**

```python
# config/graphql/monitoring.py
from graphql_auto_gen.monitoring import BaseMonitor
import sentry_sdk

class GraphQLMonitor(BaseMonitor):
    """Monitor GraphQL operations and errors."""
    
    def track_query_execution(self, query, variables, result, execution_time):
        """Track query execution metrics."""
        # Send metrics to monitoring service
        self.send_metric('graphql.query.execution_time', execution_time)
        self.send_metric('graphql.query.count', 1)
        
        # Track errors
        if result.errors:
            self.send_metric('graphql.query.errors', len(result.errors))
            
            # Send to Sentry for error tracking
            for error in result.errors:
                sentry_sdk.capture_exception(error)
    
    def track_slow_queries(self, query, execution_time, threshold=1.0):
        """Track and alert on slow queries."""
        if execution_time > threshold:
            logger.warning(
                f"Slow GraphQL query detected: {execution_time:.2f}s",
                extra={
                    'query': str(query),
                    'execution_time': execution_time,
                }
            )
            
            # Send alert to monitoring service
            self.send_alert('slow_query', {
                'execution_time': execution_time,
                'threshold': threshold,
                'query': str(query)[:500],  # Truncate for storage
            })
```

## Testing Strategies

### Comprehensive Test Coverage

**Implement thorough testing:**

```python
# tests/test_graphql_queries.py
import pytest
from graphql_auto_gen.test_utils import GraphQLTestCase

class TestProductQueries(GraphQLTestCase):
    """Test Product GraphQL queries."""
    
    def setUp(self):
        """Set up test data."""
        self.user = self.create_user(username='testuser')
        self.category = self.create_category(name='Electronics')
        self.product = self.create_product(
            name='Test Product',
            category=self.category,
            price=99.99
        )
    
    def test_product_list_query(self):
        """Test product list query."""
        query = '''
            query {
                products {
                    edges {
                        node {
                            id
                            name
                            price
                            category {
                                name
                            }
                        }
                    }
                }
            }
        '''
        
        result = self.execute_query(query, user=self.user)
        
        self.assertNoErrors(result)
        self.assertEqual(len(result.data['products']['edges']), 1)
        
        product_data = result.data['products']['edges'][0]['node']
        self.assertEqual(product_data['name'], 'Test Product')
        self.assertEqual(float(product_data['price']), 99.99)
        self.assertEqual(product_data['category']['name'], 'Electronics')
    
    def test_product_filtering(self):
        """Test product filtering."""
        query = '''
            query($filter: ProductFilter) {
                products(filter: $filter) {
                    edges {
                        node {
                            id
                            name
                        }
                    }
                }
            }
        '''
        
        variables = {
            'filter': {
                'name_Icontains': 'test'
            }
        }
        
        result = self.execute_query(query, variables=variables, user=self.user)
        
        self.assertNoErrors(result)
        self.assertEqual(len(result.data['products']['edges']), 1)
    
    def test_unauthorized_access(self):
        """Test unauthorized access handling."""
        query = '''
            query {
                products {
                    edges {
                        node {
                            id
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.execute_query(query)  # No user provided
        
        self.assertHasErrors(result)
        self.assertErrorCode(result, 'AUTHENTICATION_REQUIRED')

# tests/test_graphql_mutations.py
class TestProductMutations(GraphQLTestCase):
    """Test Product GraphQL mutations."""
    
    def test_create_product_success(self):
        """Test successful product creation."""
        mutation = '''
            mutation($input: ProductCreateInput!) {
                createProduct(input: $input) {
                    success
                    product {
                        id
                        name
                        price
                    }
                    errors {
                        field
                        message
                    }
                }
            }
        '''
        
        variables = {
            'input': {
                'name': 'New Product',
                'price': 149.99,
                'categoryId': str(self.category.id),
            }
        }
        
        result = self.execute_mutation(mutation, variables=variables, user=self.user)
        
        self.assertNoErrors(result)
        self.assertTrue(result.data['createProduct']['success'])
        self.assertEqual(result.data['createProduct']['product']['name'], 'New Product')
    
    def test_create_product_validation_error(self):
        """Test product creation with validation errors."""
        mutation = '''
            mutation($input: ProductCreateInput!) {
                createProduct(input: $input) {
                    success
                    errors {
                        field
                        message
                    }
                }
            }
        '''
        
        variables = {
            'input': {
                'name': '',  # Invalid: empty name
                'price': -10,  # Invalid: negative price
            }
        }
        
        result = self.execute_mutation(mutation, variables=variables, user=self.user)
        
        self.assertNoErrors(result)  # No GraphQL errors
        self.assertFalse(result.data['createProduct']['success'])
        self.assertTrue(len(result.data['createProduct']['errors']) > 0)
```

### Performance Testing

**Test performance characteristics:**

```python
# tests/test_performance.py
import time
import pytest
from django.test import TransactionTestCase

class TestGraphQLPerformance(TransactionTestCase):
    """Test GraphQL performance characteristics."""
    
    def setUp(self):
        """Set up performance test data."""
        self.create_test_data(num_products=1000)
    
    def test_query_performance(self):
        """Test query execution time."""
        query = '''
            query {
                products(first: 50) {
                    edges {
                        node {
                            id
                            name
                            category {
                                name
                            }
                        }
                    }
                }
            }
        '''
        
        start_time = time.time()
        result = self.execute_query(query)
        execution_time = time.time() - start_time
        
        self.assertNoErrors(result)
        self.assertLess(execution_time, 0.5)  # Should complete in < 500ms
    
    def test_n_plus_one_prevention(self):
        """Test that N+1 queries are prevented."""
        query = '''
            query {
                products(first: 10) {
                    edges {
                        node {
                            id
                            name
                            category {
                                name
                            }
                            tags {
                                name
                            }
                        }
                    }
                }
            }
        '''
        
        with self.assertNumQueries(3):  # Should be 3 queries max
            result = self.execute_query(query)
            self.assertNoErrors(result)
    
    def test_memory_usage(self):
        """Test memory usage for large result sets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        query = '''
            query {
                products(first: 1000) {
                    edges {
                        node {
                            id
                            name
                        }
                    }
                }
            }
        '''
        
        result = self.execute_query(query)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        self.assertNoErrors(result)
        self.assertLess(memory_increase, 50 * 1024 * 1024)  # < 50MB increase
```

## Documentation

### Code Documentation

**Document GraphQL customizations:**

```python
class Product(models.Model):
    """
    Product model representing items in the catalog.
    
    This model is automatically exposed via GraphQL with the following features:
    - Automatic CRUD operations
    - Advanced filtering by name, category, price, and tags
    - Pagination support with Relay-style connections
    - Permission-based access control
    
    GraphQL Operations:
    - Query: products (list), product (detail)
    - Mutations: createProduct, updateProduct, deleteProduct
    - Subscriptions: productCreated, productUpdated (if enabled)
    
    Example GraphQL Query:
        query {
            products(filter: {category: "electronics", price_Lte: 1000}) {
                edges {
                    node {
                        id
                        name
                        price
                        category {
                            name
                        }
                    }
                }
            }
        }
    """
    
    name = models.CharField(
        max_length=200,
        help_text="Product name (exposed in GraphQL as 'name' field)",
        verbose_name="Nom du produit"
    )
    
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Product price in USD (filterable: exact, gte, lte, range)",
        verbose_name="Prix"
    )
    
    class GraphQLMeta:
        """
        GraphQL configuration for Product model.
        
        This configuration controls how the Product model is exposed
        via the auto-generated GraphQL schema.
        """
        
        # Fields exposed in GraphQL schema
        fields = ['id', 'name', 'price', 'category', 'tags', 'created_at']
        
        # Filterable fields with allowed lookup types
        filterable_fields = {
            'name': ['exact', 'icontains', 'startswith'],
            'price': ['exact', 'gte', 'lte', 'range'],
            'category': ['exact'],
            'tags': ['exact', 'in'],
            'created_at': ['gte', 'lte', 'range'],
        }
        
        # Query optimization
        select_related = ['category']
        prefetch_related = ['tags']
        
        # Permissions
        permission_classes = ['IsAuthenticatedOrReadOnly']
```

### API Documentation

**Generate comprehensive API documentation:**

```python
# docs/generate_schema_docs.py
from graphql_auto_gen.docs import SchemaDocumentationGenerator

def generate_api_docs():
    """Generate comprehensive API documentation."""
    
    generator = SchemaDocumentationGenerator()
    
    # Generate schema documentation
    schema_docs = generator.generate_schema_docs()
    
    # Generate query examples
    query_examples = generator.generate_query_examples()
    
    # Generate mutation examples
    mutation_examples = generator.generate_mutation_examples()
    
    # Write documentation files
    with open('docs/api/schema.md', 'w') as f:
        f.write(schema_docs)
    
    with open('docs/api/queries.md', 'w') as f:
        f.write(query_examples)
    
    with open('docs/api/mutations.md', 'w') as f:
        f.write(mutation_examples)

if __name__ == '__main__':
    generate_api_docs()
```

## Deployment

### Production Configuration

**Optimize for production deployment:**

```python
# config/settings/production.py
import os

# Security settings
GRAPHQL_AUTO_GEN = {
    'SCHEMA_CONFIG': {
        'debug': False,
        'enable_introspection': False,
        
        'security': {
            'authentication_required': True,
            'rate_limiting': {
                'enabled': True,
                'requests_per_minute': 100,
                'burst_limit': 20,
            },
            'query_analysis': {
                'enabled': True,
                'max_complexity': 1000,
                'max_depth': 10,
            },
            'cors': {
                'enabled': True,
                'allowed_origins': os.getenv('CORS_ALLOWED_ORIGINS', '').split(','),
            },
        },
        
        'performance': {
            'caching': {
                'enabled': True,
                'backend': 'redis',
                'default_timeout': 300,
            },
            'query_optimization': {
                'enabled': True,
                'auto_select_related': True,
                'auto_prefetch_related': True,
            },
        },
        
        'monitoring': {
            'enabled': True,
            'metrics_backend': 'prometheus',
            'slow_query_threshold': 1.0,
            'error_tracking': 'sentry',
        },
    }
}

# Database optimization
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        'OPTIONS': {
            'MAX_CONNS': 20,
            'OPTIONS': {
                'MAX_CONNS': 20,
            }
        },
        'CONN_MAX_AGE': 600,
    }
}

# Caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}
```

### Docker Configuration

**Optimize Docker setup:**

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.production

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements/production.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python manage.py health_check

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

## Monitoring and Maintenance

### Health Checks

**Implement comprehensive health checks:**

```python
# management/commands/health_check.py
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
import sys

class Command(BaseCommand):
    """Health check command for monitoring."""
    
    def handle(self, *args, **options):
        """Perform health checks."""
        checks = [
            self.check_database,
            self.check_cache,
            self.check_graphql_schema,
        ]
        
        failed_checks = []
        
        for check in checks:
            try:
                check()
                self.stdout.write(f"✓ {check.__name__}")
            except Exception as e:
                self.stderr.write(f"✗ {check.__name__}: {e}")
                failed_checks.append(check.__name__)
        
        if failed_checks:
            self.stderr.write(f"Failed checks: {', '.join(failed_checks)}")
            sys.exit(1)
        else:
            self.stdout.write("All health checks passed")
    
    def check_database(self):
        """Check database connectivity."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    
    def check_cache(self):
        """Check cache connectivity."""
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') != 'ok':
            raise Exception("Cache not working")
    
    def check_graphql_schema(self):
        """Check GraphQL schema compilation."""
        from graphql_auto_gen.schema import get_schema
        schema = get_schema()
        if not schema:
            raise Exception("GraphQL schema not available")
```

### Monitoring Setup

**Set up comprehensive monitoring:**

```python
# config/monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
graphql_requests_total = Counter(
    'graphql_requests_total',
    'Total GraphQL requests',
    ['operation', 'status']
)

graphql_request_duration = Histogram(
    'graphql_request_duration_seconds',
    'GraphQL request duration',
    ['operation']
)

graphql_active_connections = Gauge(
    'graphql_active_connections',
    'Active GraphQL connections'
)

class GraphQLMetricsMiddleware:
    """Middleware to collect GraphQL metrics."""
    
    def resolve(self, next, root, info, **args):
        """Collect metrics for GraphQL operations."""
        operation_name = info.operation.name.value if info.operation.name else 'anonymous'
        
        # Track active connections
        graphql_active_connections.inc()
        
        start_time = time.time()
        
        try:
            result = next(root, info, **args)
            
            # Track successful requests
            graphql_requests_total.labels(
                operation=operation_name,
                status='success'
            ).inc()
            
            return result
            
        except Exception as e:
            # Track failed requests
            graphql_requests_total.labels(
                operation=operation_name,
                status='error'
            ).inc()
            raise
            
        finally:
            # Track request duration
            duration = time.time() - start_time
            graphql_request_duration.labels(
                operation=operation_name
            ).observe(duration)
            
            # Decrease active connections
            graphql_active_connections.dec()
```

## Code Quality

### Code Review Checklist

**Use this checklist for code reviews:**

- [ ] **Security**: No hardcoded secrets, proper input validation
- [ ] **Performance**: Optimized queries, appropriate caching
- [ ] **Error Handling**: Proper error handling and logging
- [ ] **Testing**: Adequate test coverage (>80%)
- [ ] **Documentation**: Code is well-documented
- [ ] **Configuration**: Environment-specific settings
- [ ] **Permissions**: Proper access control
- [ ] **Validation**: Input validation and sanitization
- [ ] **Monitoring**: Appropriate logging and metrics
- [ ] **Standards**: Follows project coding standards

### Automated Quality Checks

**Set up automated quality checks:**

```yaml
# .github/workflows/quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements/development.txt
    
    - name: Run linting
      run: |
        flake8 .
        black --check .
        isort --check-only .
    
    - name: Run security checks
      run: |
        bandit -r .
        safety check
    
    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Team Collaboration

### Development Workflow

**Establish clear development workflow:**

1. **Feature Development**:
   - Create feature branch from `main`
   - Implement feature with tests
   - Update documentation
   - Submit pull request

2. **Code Review Process**:
   - Automated checks must pass
   - At least one reviewer approval
   - Security review for sensitive changes
   - Performance review for optimization changes

3. **Deployment Process**:
   - Merge to `main` triggers staging deployment
   - Manual approval for production deployment
   - Rollback plan for failed deployments

### Knowledge Sharing

**Promote knowledge sharing:**

```python
# docs/team/graphql_patterns.py
"""
Common GraphQL patterns and best practices for the team.

This module contains examples and patterns that the team should follow
when working with the Django GraphQL Auto-Generation System.
"""

# Pattern: Custom resolver with optimization
class OptimizedResolver(BaseResolver):
    """
    Example of an optimized resolver that minimizes database queries.
    
    Use this pattern when you need custom logic but want to maintain
    performance characteristics.
    """
    
    def get_queryset(self, info):
        # Always analyze requested fields
        requested_fields = self.get_requested_fields(info)
        
        # Apply optimizations based on analysis
        queryset = super().get_queryset(info)
        
        if 'related_field' in requested_fields:
            queryset = queryset.select_related('related_field')
        
        return queryset

# Pattern: Custom validation
class TeamValidator(BaseValidator):
    """
    Example of team-standard validation patterns.
    
    Use these patterns to ensure consistent validation across the project.
    """
    
    def validate_email(self, value):
        # Team standard: Use Django's email validation
        from django.core.validators import validate_email
        validate_email(value)
        return value.lower().strip()
    
    def validate_phone(self, value):
        # Team standard: Use phonenumbers library
        import phonenumbers
        try:
            parsed = phonenumbers.parse(value, 'US')
            if not phonenumbers.is_valid_number(parsed):
                raise ValidationError("Invalid phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValidationError("Invalid phone number format")
```

Following these best practices will help you build robust, secure, and maintainable GraphQL APIs with the Django GraphQL Auto-Generation System. Remember to adapt these practices to your specific project requirements and team preferences.