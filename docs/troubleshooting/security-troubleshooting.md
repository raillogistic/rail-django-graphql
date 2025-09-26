# Security Troubleshooting Guide

This guide helps you diagnose and resolve common security issues in the Django GraphQL Auto-Generation System.

## Table of Contents

1. [Authentication Issues](#authentication-issues)
2. [Permission Problems](#permission-problems)
3. [Rate Limiting Issues](#rate-limiting-issues)
4. [Query Analysis Problems](#query-analysis-problems)
5. [Input Validation Errors](#input-validation-errors)
6. [JWT Token Issues](#jwt-token-issues)
7. [Security Middleware Problems](#security-middleware-problems)
8. [Performance and Security](#performance-and-security)
9. [Debugging Tools and Techniques](#debugging-tools-and-techniques)
10. [Common Error Messages](#common-error-messages)
11. [Security Monitoring](#security-monitoring)
12. [Best Practices for Troubleshooting](#best-practices-for-troubleshooting)

## Authentication Issues

### Problem: Authentication Required Error

**Symptoms:**
```json
{
  "errors": [
    {
      "message": "Authentication required",
      "extensions": {
        "code": "AUTHENTICATION_REQUIRED"
      }
    }
  ]
}
```

**Diagnosis:**
```python
# Check authentication middleware
def debug_authentication(request):
    print(f"User: {request.user}")
    print(f"Is authenticated: {request.user.is_authenticated}")
    print(f"Headers: {dict(request.headers)}")
    print(f"Session: {request.session.items()}")
```

**Solutions:**

1. **Check JWT Token Format:**
```javascript
// Correct format
const headers = {
    'Authorization': 'Bearer your-jwt-token-here',
    'Content-Type': 'application/json'
};

// Common mistakes
const wrongHeaders = {
    'Authorization': 'your-jwt-token-here',  // Missing 'Bearer'
    'Authorization': 'JWT your-jwt-token-here',  // Wrong prefix
};
```

2. **Verify Token Validity:**
```python
import jwt
from django.conf import settings

def debug_jwt_token(token):
    try:
        payload = jwt.decode(
            token, 
            settings.GRAPHQL_JWT_SECRET_KEY, 
            algorithms=['HS256']
        )
        print(f"Token payload: {payload}")
        print(f"Token expires: {payload.get('exp')}")
        return True
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return False
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        return False
```

3. **Check Authentication Backend:**
```python
# settings.py
AUTHENTICATION_BACKENDS = [
    'django_graphql_auto.auth.backends.GraphQLJWTBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Verify backend is working
from django.contrib.auth import authenticate
user = authenticate(username='testuser', password='testpass')
print(f"Authentication result: {user}")
```

### Problem: Session Authentication Not Working

**Diagnosis:**
```python
def debug_session_auth(request):
    print(f"Session key: {request.session.session_key}")
    print(f"Session data: {dict(request.session)}")
    print(f"CSRF token: {request.META.get('CSRF_COOKIE')}")
```

**Solutions:**

1. **Check Session Configuration:**
```python
# settings.py
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600
SESSION_COOKIE_SECURE = True  # Only for HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = True
```

2. **Verify CSRF Protection:**
```python
# For GraphQL, you might need to disable CSRF for the endpoint
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def graphql_view(request):
    # Your GraphQL view logic
    pass
```

## Permission Problems

### Problem: Permission Denied Errors

**Symptoms:**
```json
{
  "errors": [
    {
      "message": "Permission denied",
      "extensions": {
        "code": "PERMISSION_DENIED",
        "permission": "view_user"
      }
    }
  ]
}
```

**Diagnosis:**
```python
def debug_permissions(user, obj=None, permission=None):
    print(f"User: {user}")
    print(f"User groups: {list(user.groups.all())}")
    print(f"User permissions: {list(user.user_permissions.all())}")
    print(f"Is superuser: {user.is_superuser}")
    print(f"Is staff: {user.is_staff}")
    
    if obj and permission:
        has_perm = user.has_perm(permission, obj)
        print(f"Has permission '{permission}' for {obj}: {has_perm}")
```

**Solutions:**

1. **Check Permission Configuration:**
```python
# models.py
class MyModel(models.Model):
    class Meta:
        permissions = [
            ('view_mymodel', 'Can view my model'),
            ('change_mymodel', 'Can change my model'),
        ]

# Verify permissions exist
from django.contrib.auth.models import Permission
perms = Permission.objects.filter(content_type__app_label='myapp')
for perm in perms:
    print(f"{perm.codename}: {perm.name}")
```

2. **Check User Permissions:**
```python
# Grant permissions
from django.contrib.auth.models import User, Permission

user = User.objects.get(username='testuser')
permission = Permission.objects.get(codename='view_mymodel')
user.user_permissions.add(permission)

# Or add to group
from django.contrib.auth.models import Group
group = Group.objects.get(name='viewers')
group.permissions.add(permission)
user.groups.add(group)
```

3. **Debug Custom Permission Classes:**
```python
class CustomPermission:
    def has_permission(self, user, info, **kwargs):
        print(f"Checking permission for user: {user}")
        print(f"Info: {info}")
        print(f"Kwargs: {kwargs}")
        
        # Your permission logic
        result = your_permission_logic(user, info, **kwargs)
        print(f"Permission result: {result}")
        return result
```

### Problem: Object-Level Permissions Not Working

**Diagnosis:**
```python
def debug_object_permissions(user, obj):
    # Check if user owns the object
    if hasattr(obj, 'owner'):
        print(f"Object owner: {obj.owner}")
        print(f"User is owner: {obj.owner == user}")
    
    # Check custom object permissions
    if hasattr(obj, 'has_permission'):
        result = obj.has_permission(user, 'view')
        print(f"Object permission result: {result}")
```

**Solutions:**

1. **Implement Object-Level Permissions:**
```python
class MyModel(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def has_permission(self, user, action):
        if action == 'view':
            return True  # Anyone can view
        elif action in ['change', 'delete']:
            return self.owner == user or user.is_staff
        return False
```

2. **Use Django Guardian (Optional):**
```python
# Install: pip install django-guardian
from guardian.shortcuts import assign_perm, get_perms

# Assign object permission
assign_perm('view_mymodel', user, obj)

# Check object permissions
perms = get_perms(user, obj)
print(f"User permissions for object: {perms}")
```

## Rate Limiting Issues

### Problem: Rate Limit Exceeded

**Symptoms:**
```json
{
  "errors": [
    {
      "message": "Rate limit exceeded",
      "extensions": {
        "code": "RATE_LIMIT_EXCEEDED",
        "retry_after": 60
      }
    }
  ]
}
```

**Diagnosis:**
```python
def debug_rate_limiting(request):
    from django.core.cache import cache
    
    # Check current rate limit status
    client_ip = request.META.get('REMOTE_ADDR')
    cache_key = f"rate_limit:{client_ip}"
    
    current_count = cache.get(cache_key, 0)
    print(f"Client IP: {client_ip}")
    print(f"Current request count: {current_count}")
    print(f"Cache TTL: {cache.ttl(cache_key)}")
```

**Solutions:**

1. **Adjust Rate Limit Configuration:**
```python
# settings.py
GRAPHQL_AUTO_SECURITY = {
    'RATE_LIMITING': {
        'ENABLED': True,
        'DEFAULT_RATE': '1000/hour',  # Increase limit
        'BURST_RATE': '100/minute',
        'OPERATION_RATES': {
            'login': '10/minute',
            'register': '5/minute',
            'query': '500/hour',
        },
    },
}
```

2. **Implement Custom Rate Limiting:**
```python
class CustomRateLimiter:
    def is_allowed(self, request, operation=None):
        # Custom rate limiting logic
        if request.user.is_staff:
            return True  # No limits for staff
        
        # Different limits for different users
        if request.user.is_authenticated:
            limit = 1000  # Higher limit for authenticated users
        else:
            limit = 100   # Lower limit for anonymous users
        
        return self.check_limit(request, limit)
```

3. **Whitelist IP Addresses:**
```python
# settings.py
GRAPHQL_AUTO_SECURITY = {
    'RATE_LIMITING': {
        'WHITELIST_IPS': [
            '127.0.0.1',
            '192.168.1.0/24',
            'your-server-ip',
        ],
    },
}
```

### Problem: Rate Limiting Not Working

**Diagnosis:**
```python
def test_rate_limiting():
    import requests
    
    url = 'http://localhost:8000/graphql/'
    query = '{ __schema { types { name } } }'
    
    for i in range(20):
        response = requests.post(url, json={'query': query})
        print(f"Request {i+1}: {response.status_code}")
        if response.status_code == 429:
            print("Rate limiting is working!")
            break
    else:
        print("Rate limiting might not be working")
```

**Solutions:**

1. **Check Middleware Order:**
```python
# settings.py
MIDDLEWARE = [
    'django_graphql_auto.middleware.RateLimitMiddleware',  # Should be early
    'django.middleware.security.SecurityMiddleware',
    # ... other middleware
]
```

2. **Verify Cache Backend:**
```python
# Rate limiting requires a cache backend
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Test cache
from django.core.cache import cache
cache.set('test', 'value', 60)
print(f"Cache test: {cache.get('test')}")
```

## Query Analysis Problems

### Problem: Query Depth Limit Exceeded

**Symptoms:**
```json
{
  "errors": [
    {
      "message": "Query depth limit exceeded",
      "extensions": {
        "code": "QUERY_DEPTH_EXCEEDED",
        "max_depth": 10,
        "actual_depth": 15
      }
    }
  ]
}
```

**Diagnosis:**
```python
def analyze_query_depth(query):
    import graphql
    
    try:
        document = graphql.parse(query)
        depth = calculate_depth(document)
        print(f"Query depth: {depth}")
        return depth
    except Exception as e:
        print(f"Query parsing error: {e}")
        return None

def calculate_depth(node, current_depth=0):
    if hasattr(node, 'selection_set') and node.selection_set:
        max_child_depth = 0
        for selection in node.selection_set.selections:
            child_depth = calculate_depth(selection, current_depth + 1)
            max_child_depth = max(max_child_depth, child_depth)
        return max_child_depth
    return current_depth
```

**Solutions:**

1. **Adjust Depth Limit:**
```python
# settings.py
GRAPHQL_AUTO_SECURITY = {
    'QUERY_ANALYSIS': {
        'DEPTH_LIMIT': 15,  # Increase limit
        'COMPLEXITY_LIMIT': 1000,
    },
}
```

2. **Optimize Query Structure:**
```graphql
# Instead of deep nesting
query DeepQuery {
  user {
    posts {
      comments {
        author {
          posts {
            comments {
              # ... too deep
            }
          }
        }
      }
    }
  }
}

# Use separate queries
query UserPosts {
  user {
    posts {
      id
      title
    }
  }
}

query PostComments($postId: ID!) {
  post(id: $postId) {
    comments {
      id
      content
      author {
        name
      }
    }
  }
}
```

### Problem: Query Complexity Limit Exceeded

**Diagnosis:**
```python
def analyze_query_complexity(query, variables=None):
    from django_graphql_auto.security.query_analysis import QueryComplexityAnalyzer
    
    analyzer = QueryComplexityAnalyzer()
    complexity = analyzer.calculate_complexity(query, variables)
    print(f"Query complexity: {complexity}")
    return complexity
```

**Solutions:**

1. **Optimize Query Complexity:**
```graphql
# High complexity query
query ExpensiveQuery {
  users {  # Complexity: 1000 users
    posts {  # Complexity: 1000 * 100 posts = 100,000
      comments {  # Complexity: 100,000 * 50 comments = 5,000,000
        content
      }
    }
  }
}

# Optimized query with pagination
query OptimizedQuery {
  users(first: 10) {  # Limit users
    posts(first: 5) {  # Limit posts per user
      comments(first: 3) {  # Limit comments per post
        content
      }
    }
  }
}
```

2. **Configure Complexity Weights:**
```python
# settings.py
GRAPHQL_AUTO_SECURITY = {
    'QUERY_ANALYSIS': {
        'COMPLEXITY_WEIGHTS': {
            'User': 1,
            'Post': 2,
            'Comment': 1,
            'users': 10,  # List fields have higher weight
            'posts': 5,
            'comments': 3,
        },
    },
}
```

## Input Validation Errors

### Problem: XSS Protection Blocking Valid Input

**Symptoms:**
```json
{
  "errors": [
    {
      "message": "Potentially malicious input detected",
      "extensions": {
        "code": "XSS_DETECTED",
        "field": "content"
      }
    }
  ]
}
```

**Diagnosis:**
```python
def debug_xss_protection(input_value):
    from django_graphql_auto.security.validators import XSSValidator
    
    validator = XSSValidator()
    try:
        cleaned_value = validator.clean(input_value)
        print(f"Original: {input_value}")
        print(f"Cleaned: {cleaned_value}")
        return cleaned_value
    except ValidationError as e:
        print(f"XSS validation error: {e}")
        return None
```

**Solutions:**

1. **Configure XSS Protection:**
```python
# settings.py
GRAPHQL_AUTO_SECURITY = {
    'INPUT_VALIDATION': {
        'XSS_PROTECTION': {
            'ENABLED': True,
            'STRICT_MODE': False,  # Less strict
            'ALLOWED_TAGS': ['b', 'i', 'u', 'strong', 'em'],
            'ALLOWED_ATTRIBUTES': ['class', 'id'],
        },
    },
}
```

2. **Custom XSS Validator:**
```python
class CustomXSSValidator:
    def clean(self, value):
        import bleach
        
        # Allow more HTML tags for rich content
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'
        ]
        
        allowed_attributes = {
            '*': ['class', 'id'],
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'width', 'height'],
        }
        
        return bleach.clean(
            value,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
```

### Problem: SQL Injection Protection False Positives

**Diagnosis:**
```python
def debug_sql_injection_protection(input_value):
    from django_graphql_auto.security.validators import SQLInjectionValidator
    
    validator = SQLInjectionValidator()
    patterns = validator.get_dangerous_patterns()
    
    for pattern in patterns:
        if pattern.search(input_value.lower()):
            print(f"Matched pattern: {pattern.pattern}")
            print(f"Input: {input_value}")
```

**Solutions:**

1. **Configure SQL Injection Protection:**
```python
# settings.py
GRAPHQL_AUTO_SECURITY = {
    'INPUT_VALIDATION': {
        'SQL_INJECTION_PROTECTION': {
            'ENABLED': True,
            'STRICT_MODE': False,
            'CUSTOM_PATTERNS': [
                r'\bunion\s+select\b',
                r'\bselect\s+.*\bfrom\b',
            ],
            'WHITELIST_PATTERNS': [
                r'select\s+option',  # Allow "select option" in UI text
            ],
        },
    },
}
```

2. **Custom SQL Injection Validator:**
```python
class CustomSQLInjectionValidator:
    def __init__(self):
        self.dangerous_patterns = [
            re.compile(r'\b(union|select|insert|update|delete|drop|create|alter)\s+', re.IGNORECASE),
            re.compile(r'[\'";].*[\'";]', re.IGNORECASE),
            re.compile(r'--.*', re.IGNORECASE),
        ]
        
        self.whitelist_patterns = [
            re.compile(r'select\s+(option|item|choice)', re.IGNORECASE),
        ]
    
    def is_safe(self, value):
        # Check whitelist first
        for pattern in self.whitelist_patterns:
            if pattern.search(value):
                return True
        
        # Check dangerous patterns
        for pattern in self.dangerous_patterns:
            if pattern.search(value):
                return False
        
        return True
```

## JWT Token Issues

### Problem: Token Expired

**Symptoms:**
```json
{
  "errors": [
    {
      "message": "Token has expired",
      "extensions": {
        "code": "TOKEN_EXPIRED"
      }
    }
  ]
}
```

**Solutions:**

1. **Implement Token Refresh:**
```javascript
// Client-side token refresh
async function refreshToken() {
    const refreshToken = localStorage.getItem('refreshToken');
    
    const response = await fetch('/graphql/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query: `
                mutation RefreshToken($refreshToken: String!) {
                    refreshToken(refreshToken: $refreshToken) {
                        token
                        refreshToken
                        success
                        errors
                    }
                }
            `,
            variables: { refreshToken }
        })
    });
    
    const data = await response.json();
    if (data.data.refreshToken.success) {
        localStorage.setItem('token', data.data.refreshToken.token);
        localStorage.setItem('refreshToken', data.data.refreshToken.refreshToken);
        return data.data.refreshToken.token;
    }
    
    throw new Error('Token refresh failed');
}
```

2. **Configure Token Expiration:**
```python
# settings.py
GRAPHQL_JWT = {
    'JWT_EXPIRATION_DELTA': timedelta(hours=1),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
    'JWT_ALLOW_REFRESH': True,
}
```

### Problem: Invalid Token Format

**Diagnosis:**
```python
def debug_token_format(token):
    import base64
    import json
    
    try:
        # JWT has 3 parts separated by dots
        parts = token.split('.')
        if len(parts) != 3:
            print(f"Invalid JWT format: expected 3 parts, got {len(parts)}")
            return False
        
        # Decode header and payload (not signature)
        header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
        
        print(f"Header: {header}")
        print(f"Payload: {payload}")
        return True
        
    except Exception as e:
        print(f"Token decoding error: {e}")
        return False
```

**Solutions:**

1. **Verify Token Generation:**
```python
def generate_debug_token(user):
    import jwt
    from datetime import datetime, timedelta
    from django.conf import settings
    
    payload = {
        'user_id': user.id,
        'username': user.username,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
    }
    
    token = jwt.encode(
        payload,
        settings.GRAPHQL_JWT_SECRET_KEY,
        algorithm='HS256'
    )
    
    print(f"Generated token: {token}")
    return token
```

## Security Middleware Problems

### Problem: Middleware Not Applied

**Diagnosis:**
```python
def debug_middleware_order():
    from django.conf import settings
    
    print("Current middleware order:")
    for i, middleware in enumerate(settings.MIDDLEWARE):
        print(f"{i+1}. {middleware}")
    
    # Check if security middleware is present
    security_middlewares = [
        'django_graphql_auto.middleware.SecurityMiddleware',
        'django_graphql_auto.middleware.RateLimitMiddleware',
        'django_graphql_auto.middleware.AuthenticationMiddleware',
    ]
    
    for middleware in security_middlewares:
        if middleware in settings.MIDDLEWARE:
            print(f"✓ {middleware} is present")
        else:
            print(f"✗ {middleware} is missing")
```

**Solutions:**

1. **Correct Middleware Order:**
```python
# settings.py
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django_graphql_auto.middleware.SecurityMiddleware',  # Early
    'django_graphql_auto.middleware.RateLimitMiddleware',  # Before auth
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_graphql_auto.middleware.AuthenticationMiddleware',  # After Django auth
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

2. **Test Middleware Functionality:**
```python
def test_security_middleware():
    from django.test import RequestFactory
    from django_graphql_auto.middleware import SecurityMiddleware
    
    factory = RequestFactory()
    request = factory.post('/graphql/', {'query': 'malicious query'})
    
    middleware = SecurityMiddleware(lambda r: None)
    response = middleware(request)
    
    print(f"Middleware response: {response}")
```

## Performance and Security

### Problem: Security Checks Causing Performance Issues

**Diagnosis:**
```python
import time
from functools import wraps

def performance_monitor(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper

# Apply to security functions
@performance_monitor
def validate_input(value):
    # Your validation logic
    pass
```

**Solutions:**

1. **Optimize Security Checks:**
```python
# Cache validation results
from django.core.cache import cache

class CachedValidator:
    def validate(self, value):
        cache_key = f"validation:{hash(value)}"
        result = cache.get(cache_key)
        
        if result is None:
            result = self.perform_validation(value)
            cache.set(cache_key, result, 300)  # Cache for 5 minutes
        
        return result
```

2. **Async Security Checks:**
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncSecurityValidator:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def validate_async(self, value):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.perform_validation,
            value
        )
```

## Debugging Tools and Techniques

### 1. Enable Debug Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'security_debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django_graphql_auto.security': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django_graphql_auto.middleware': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### 2. Security Debug Middleware

```python
class SecurityDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log request details
        print(f"Request path: {request.path}")
        print(f"Request method: {request.method}")
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request user: {request.user}")
        
        # Process request
        response = self.get_response(request)
        
        # Log response details
        print(f"Response status: {response.status_code}")
        if hasattr(response, 'content'):
            print(f"Response content: {response.content[:500]}")
        
        return response
```

### 3. GraphQL Query Inspector

```python
def inspect_graphql_query(query, variables=None):
    import graphql
    
    try:
        document = graphql.parse(query)
        
        print("=== GraphQL Query Analysis ===")
        print(f"Query: {query}")
        print(f"Variables: {variables}")
        
        # Extract operations
        for definition in document.definitions:
            if isinstance(definition, graphql.OperationDefinitionNode):
                print(f"Operation: {definition.operation}")
                print(f"Name: {definition.name.value if definition.name else 'Anonymous'}")
                
                # Extract fields
                fields = extract_fields(definition.selection_set)
                print(f"Fields: {fields}")
        
    except Exception as e:
        print(f"Query parsing error: {e}")

def extract_fields(selection_set, depth=0):
    fields = []
    for selection in selection_set.selections:
        if isinstance(selection, graphql.FieldNode):
            field_name = selection.name.value
            fields.append("  " * depth + field_name)
            
            if selection.selection_set:
                fields.extend(extract_fields(selection.selection_set, depth + 1))
    
    return fields
```

### 4. Security Test Suite

```python
# tests/test_security_debug.py
import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User

class SecurityDebugTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_authentication_debug(self):
        """Test authentication debugging"""
        request = self.factory.post('/graphql/')
        request.user = self.user
        
        # Debug authentication
        self.debug_authentication(request)
        
        self.assertTrue(request.user.is_authenticated)
    
    def test_permission_debug(self):
        """Test permission debugging"""
        from django.contrib.auth.models import Permission
        
        # Add permission to user
        permission = Permission.objects.get(codename='add_user')
        self.user.user_permissions.add(permission)
        
        # Debug permissions
        self.debug_permissions(self.user, permission='auth.add_user')
        
        self.assertTrue(self.user.has_perm('auth.add_user'))
    
    def test_rate_limiting_debug(self):
        """Test rate limiting debugging"""
        request = self.factory.post('/graphql/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        # Debug rate limiting
        self.debug_rate_limiting(request)
    
    def debug_authentication(self, request):
        print(f"User: {request.user}")
        print(f"Is authenticated: {request.user.is_authenticated}")
        print(f"User ID: {request.user.id if request.user.is_authenticated else 'N/A'}")
    
    def debug_permissions(self, user, permission=None):
        print(f"User: {user}")
        print(f"User groups: {list(user.groups.all())}")
        print(f"User permissions: {list(user.user_permissions.all())}")
        
        if permission:
            has_perm = user.has_perm(permission)
            print(f"Has permission '{permission}': {has_perm}")
    
    def debug_rate_limiting(self, request):
        from django.core.cache import cache
        
        client_ip = request.META.get('REMOTE_ADDR')
        cache_key = f"rate_limit:{client_ip}"
        
        current_count = cache.get(cache_key, 0)
        print(f"Client IP: {client_ip}")
        print(f"Current request count: {current_count}")
```

## Common Error Messages

### Error Code Reference

| Error Code | Message | Cause | Solution |
|------------|---------|-------|----------|
| `AUTHENTICATION_REQUIRED` | Authentication required | No valid authentication provided | Provide valid JWT token or session |
| `TOKEN_EXPIRED` | Token has expired | JWT token is expired | Refresh token or login again |
| `INVALID_TOKEN` | Invalid token format | Malformed JWT token | Check token format and generation |
| `PERMISSION_DENIED` | Permission denied | User lacks required permissions | Grant appropriate permissions |
| `RATE_LIMIT_EXCEEDED` | Rate limit exceeded | Too many requests | Wait or increase rate limits |
| `QUERY_DEPTH_EXCEEDED` | Query depth limit exceeded | Query too deeply nested | Reduce query depth or increase limit |
| `QUERY_COMPLEXITY_EXCEEDED` | Query complexity limit exceeded | Query too complex | Simplify query or increase limit |
| `XSS_DETECTED` | Potentially malicious input detected | Input contains XSS patterns | Sanitize input or adjust XSS settings |
| `SQL_INJECTION_DETECTED` | SQL injection attempt detected | Input contains SQL injection patterns | Sanitize input or adjust SQL protection |
| `VALIDATION_ERROR` | Input validation failed | Input doesn't meet validation criteria | Fix input format or adjust validation |

### Error Response Format

```json
{
  "errors": [
    {
      "message": "Human-readable error message",
      "extensions": {
        "code": "ERROR_CODE",
        "field": "field_name",
        "details": {
          "additional": "information"
        }
      },
      "locations": [
        {
          "line": 2,
          "column": 3
        }
      ],
      "path": ["fieldName", 0, "subField"]
    }
  ],
  "data": null
}
```

## Security Monitoring

### 1. Real-time Security Alerts

```python
def setup_security_alerts():
    import logging
    from django.core.mail import send_mail
    
    class SecurityAlertHandler(logging.Handler):
        def emit(self, record):
            if record.levelno >= logging.ERROR:
                send_mail(
                    f'Security Alert: {record.levelname}',
                    record.getMessage(),
                    'security@yourdomain.com',
                    ['admin@yourdomain.com'],
                    fail_silently=False,
                )
    
    # Add to security logger
    security_logger = logging.getLogger('django_graphql_auto.security')
    security_logger.addHandler(SecurityAlertHandler())
```

### 2. Security Metrics Collection

```python
from django.core.cache import cache
from datetime import datetime, timedelta

class SecurityMetrics:
    @staticmethod
    def record_security_event(event_type, details=None):
        """Record security events for monitoring"""
        timestamp = datetime.now()
        cache_key = f"security_events:{event_type}:{timestamp.strftime('%Y%m%d%H')}"
        
        current_count = cache.get(cache_key, 0)
        cache.set(cache_key, current_count + 1, 3600)  # 1 hour TTL
        
        # Store event details
        if details:
            detail_key = f"security_details:{event_type}:{timestamp.isoformat()}"
            cache.set(detail_key, details, 3600)
    
    @staticmethod
    def get_security_stats(hours=24):
        """Get security statistics for the last N hours"""
        stats = {}
        now = datetime.now()
        
        for i in range(hours):
            hour = now - timedelta(hours=i)
            hour_key = hour.strftime('%Y%m%d%H')
            
            for event_type in ['auth_failure', 'rate_limit', 'xss_attempt', 'sql_injection']:
                cache_key = f"security_events:{event_type}:{hour_key}"
                count = cache.get(cache_key, 0)
                
                if event_type not in stats:
                    stats[event_type] = 0
                stats[event_type] += count
        
        return stats
```

## Best Practices for Troubleshooting

### 1. Systematic Approach

1. **Identify the Problem**
   - Collect error messages and stack traces
   - Note when the problem occurs
   - Identify affected users or operations

2. **Gather Information**
   - Check logs and monitoring data
   - Review recent changes
   - Test with minimal examples

3. **Isolate the Issue**
   - Disable security features one by one
   - Test with different user roles
   - Use debug tools and logging

4. **Implement Solution**
   - Make minimal changes
   - Test thoroughly
   - Monitor for side effects

5. **Document and Prevent**
   - Document the solution
   - Add tests to prevent regression
   - Update monitoring if needed

### 2. Testing Security Features

```python
# Create comprehensive test cases
class SecurityTestCase(TestCase):
    def test_all_security_features(self):
        """Test all security features together"""
        # Test authentication
        self.test_authentication()
        
        # Test permissions
        self.test_permissions()
        
        # Test rate limiting
        self.test_rate_limiting()
        
        # Test input validation
        self.test_input_validation()
        
        # Test query analysis
        self.test_query_analysis()
    
    def test_security_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Test with empty inputs
        # Test with maximum allowed inputs
        # Test with special characters
        # Test with different user roles
        pass
```

### 3. Monitoring and Alerting

```python
def setup_comprehensive_monitoring():
    """Setup monitoring for all security aspects"""
    
    # Monitor authentication failures
    monitor_auth_failures()
    
    # Monitor rate limiting
    monitor_rate_limits()
    
    # Monitor query complexity
    monitor_query_complexity()
    
    # Monitor input validation failures
    monitor_validation_failures()
    
    # Monitor performance impact
    monitor_security_performance()

def monitor_auth_failures():
    """Monitor authentication failure patterns"""
    # Implementation for monitoring auth failures
    pass
```

This comprehensive troubleshooting guide should help you diagnose and resolve most security-related issues in your Django GraphQL Auto-Generation System. Remember to always test changes in a development environment before applying them to production.