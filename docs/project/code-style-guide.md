# Code Style Guide

## Django GraphQL Auto-Generation System - Code Style Guide

This document outlines the coding standards and style guidelines for the Django GraphQL Auto-Generation System project.

## Table of Contents

- [General Principles](#general-principles)
- [Python Code Style](#python-code-style)
- [Django Conventions](#django-conventions)
- [GraphQL Conventions](#graphql-conventions)
- [Documentation Standards](#documentation-standards)
- [Testing Standards](#testing-standards)
- [Security Guidelines](#security-guidelines)
- [Performance Guidelines](#performance-guidelines)
- [Code Review Guidelines](#code-review-guidelines)

## General Principles

### Code Quality
- **Readability First**: Code should be self-documenting and easy to understand
- **Consistency**: Follow established patterns throughout the codebase
- **Simplicity**: Prefer simple, clear solutions over complex ones
- **Maintainability**: Write code that is easy to modify and extend

### Development Philosophy
- **Test-Driven Development**: Write tests before implementation
- **Security by Design**: Consider security implications in every decision
- **Performance Awareness**: Consider performance impact of code changes
- **Documentation**: Document complex logic and public APIs

## Python Code Style

### PEP 8 Compliance
Follow [PEP 8](https://pep8.org/) with the following specific guidelines:

```python
# Line length: 100 characters maximum
# Indentation: 4 spaces (no tabs)
# Imports: grouped and sorted

# Standard library imports
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

# Third-party imports
import graphene
from django.contrib.auth.models import User
from django.db import models

# Local imports
from .models import BaseModel
from .utils import format_field_name
```

### Naming Conventions

#### Variables and Functions
```python
# Use snake_case for variables and functions
user_count = 10
field_name = "email"

def get_user_permissions(user_id: int) -> List[str]:
    """Retrieve user permissions."""
    pass

def calculate_total_price(items: List[Dict]) -> float:
    """Calculate total price including tax."""
    pass
```

#### Classes
```python
# Use PascalCase for classes
class UserTypeGenerator:
    """Generates GraphQL types for User model."""
    pass

class QueryFieldBuilder:
    """Builds GraphQL query fields."""
    pass
```

#### Constants
```python
# Use UPPER_CASE for constants
DEFAULT_PAGE_SIZE = 20
MAX_QUERY_DEPTH = 10
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
}
```

### Type Hints
Always use type hints for function parameters and return values:

```python
from typing import Dict, List, Optional, Union, Any
from django.db.models import Model

def generate_field_type(
    field: models.Field,
    model: Model,
    options: Optional[Dict[str, Any]] = None
) -> graphene.Field:
    """
    Generate GraphQL field type from Django model field.
    
    Args:
        field: Django model field
        model: Django model class
        options: Optional configuration options
        
    Returns:
        GraphQL field instance
        
    Raises:
        ValueError: If field type is not supported
    """
    pass
```

### Error Handling
Use specific exception types and proper error handling:

```python
import logging

logger = logging.getLogger(__name__)

def process_model_field(field: models.Field) -> graphene.Field:
    """Process Django model field to GraphQL field."""
    try:
        if isinstance(field, models.CharField):
            return graphene.String()
        elif isinstance(field, models.IntegerField):
            return graphene.Int()
        else:
            raise ValueError(f"Unsupported field type: {type(field)}")
    except ValueError as e:
        logger.error(f"Field processing error: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error processing field {field.name}")
        raise ValueError(f"Failed to process field: {field.name}") from e
```

### Context Managers
Use context managers for resource management:

```python
from contextlib import contextmanager
from django.db import transaction

@contextmanager
def schema_generation_context():
    """Context manager for schema generation."""
    logger.info("Starting schema generation")
    try:
        with transaction.atomic():
            yield
    except Exception as e:
        logger.error(f"Schema generation failed: {e}")
        raise
    finally:
        logger.info("Schema generation completed")
```

## Django Conventions

### Model Definitions
```python
from django.db import models
from django.contrib.auth.models import AbstractUser

class BaseModel(models.Model):
    """Base model with common fields."""
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        abstract = True

class User(AbstractUser):
    """Extended user model."""
    
    email = models.EmailField(
        unique=True,
        verbose_name="Adresse e-mail"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Numéro de téléphone"
    )
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        db_table = "auth_user_extended"
```

### View and Serializer Patterns
```python
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

class UserSerializer(serializers.ModelSerializer):
    """User model serializer."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number']
        read_only_fields = ['id']

class UserViewSet(viewsets.ModelViewSet):
    """User management viewset."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        return super().get_queryset().filter(is_active=True)
```

## GraphQL Conventions

### Type Definitions
```python
import graphene
from graphene_django import DjangoObjectType

class UserType(DjangoObjectType):
    """GraphQL type for User model."""
    
    full_name = graphene.String(description="User's full name")
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        description = "User account information"
    
    def resolve_full_name(self, info):
        """Resolve full name field."""
        return f"{self.first_name} {self.last_name}".strip()
```

### Query Definitions
```python
class Query(graphene.ObjectType):
    """Root query type."""
    
    users = graphene.List(
        UserType,
        description="List all users"
    )
    user = graphene.Field(
        UserType,
        id=graphene.ID(required=True),
        description="Get user by ID"
    )
    
    def resolve_users(self, info):
        """Resolve users query."""
        return User.objects.filter(is_active=True)
    
    def resolve_user(self, info, id):
        """Resolve single user query."""
        try:
            return User.objects.get(id=id, is_active=True)
        except User.DoesNotExist:
            return None
```

### Mutation Definitions
```python
class CreateUserMutation(graphene.Mutation):
    """Create new user mutation."""
    
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
    
    user = graphene.Field(UserType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, username, email, password):
        """Execute user creation."""
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            return CreateUserMutation(
                user=user,
                success=True,
                errors=[]
            )
        except Exception as e:
            return CreateUserMutation(
                user=None,
                success=False,
                errors=[str(e)]
            )
```

## Documentation Standards

### Docstring Format
Use Google-style docstrings:

```python
def generate_graphql_schema(
    models: List[Model],
    config: Optional[Dict[str, Any]] = None
) -> graphene.Schema:
    """
    Generate GraphQL schema from Django models.
    
    This function analyzes Django models and automatically generates
    a complete GraphQL schema with queries, mutations, and types.
    
    Args:
        models: List of Django model classes to include
        config: Optional configuration dictionary with schema options
            - include_mutations: Whether to generate mutations (default: True)
            - max_depth: Maximum query depth allowed (default: 10)
            - enable_filtering: Enable field filtering (default: True)
    
    Returns:
        Complete GraphQL schema instance ready for use
        
    Raises:
        ValueError: If models list is empty or contains invalid models
        ConfigurationError: If configuration options are invalid
        
    Example:
        >>> from myapp.models import User, Product
        >>> schema = generate_graphql_schema([User, Product])
        >>> print(schema)
        <Schema(query=Query, mutation=Mutation)>
        
    Note:
        This function performs introspection on model fields and
        relationships to generate appropriate GraphQL types.
    """
    pass
```

### Inline Comments
```python
def process_model_relationships(model: Model) -> Dict[str, Any]:
    """Process model relationships for GraphQL schema."""
    relationships = {}
    
    # Process forward relationships (ForeignKey, OneToOne)
    for field in model._meta.get_fields():
        if isinstance(field, (models.ForeignKey, models.OneToOneField)):
            # Generate field name using snake_case convention
            field_name = format_field_name(field.name)
            relationships[field_name] = {
                'type': 'forward',
                'related_model': field.related_model,
                'nullable': field.null
            }
    
    # Process reverse relationships (related_name)
    for field in model._meta.get_fields():
        if hasattr(field, 'related_name') and field.related_name:
            # Use explicit related_name if provided
            relationships[field.related_name] = {
                'type': 'reverse',
                'related_model': field.model,
                'multiple': field.one_to_many or field.many_to_many
            }
    
    return relationships
```

## Testing Standards

### Test Structure
```python
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from graphene.test import Client

from myapp.schema import schema

User = get_user_model()

class TestUserQueries(TestCase):
    """Test user-related GraphQL queries."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client(schema)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_query_success(self):
        """Test successful user query."""
        # Arrange
        query = '''
            query GetUser($id: ID!) {
                user(id: $id) {
                    id
                    username
                    email
                }
            }
        '''
        variables = {'id': str(self.user.id)}
        
        # Act
        result = self.client.execute(query, variables=variables)
        
        # Assert
        self.assertIsNone(result.get('errors'))
        user_data = result['data']['user']
        self.assertEqual(user_data['username'], 'testuser')
        self.assertEqual(user_data['email'], 'test@example.com')
    
    def test_user_query_not_found(self):
        """Test user query with non-existent ID."""
        # Arrange
        query = '''
            query GetUser($id: ID!) {
                user(id: $id) {
                    id
                    username
                }
            }
        '''
        variables = {'id': '999999'}
        
        # Act
        result = self.client.execute(query, variables=variables)
        
        # Assert
        self.assertIsNone(result.get('errors'))
        self.assertIsNone(result['data']['user'])
```

### Test Naming
```python
# Test method naming pattern: test_[component]_[scenario]_[expected_result]
def test_user_creation_with_valid_data_creates_user(self):
    """Test user creation with valid data creates user successfully."""
    pass

def test_user_creation_with_duplicate_email_raises_error(self):
    """Test user creation with duplicate email raises validation error."""
    pass

def test_schema_generation_with_empty_models_raises_value_error(self):
    """Test schema generation with empty models list raises ValueError."""
    pass
```

## Security Guidelines

### Input Validation
```python
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

def validate_user_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate user input data.
    
    Args:
        data: Input data dictionary
        
    Returns:
        Validated and sanitized data
        
    Raises:
        ValidationError: If validation fails
    """
    validated_data = {}
    
    # Validate email
    if 'email' in data:
        try:
            validate_email(data['email'])
            validated_data['email'] = data['email'].lower().strip()
        except ValidationError:
            raise ValidationError("Invalid email format")
    
    # Validate username (alphanumeric + underscore only)
    if 'username' in data:
        username = data['username'].strip()
        if not username.replace('_', '').isalnum():
            raise ValidationError("Username must contain only letters, numbers, and underscores")
        validated_data['username'] = username
    
    return validated_data
```

### Permission Checks
```python
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

def check_user_permissions(user, action: str, resource: str) -> bool:
    """
    Check if user has permission for specific action on resource.
    
    Args:
        user: User instance
        action: Action to perform (create, read, update, delete)
        resource: Resource name
        
    Returns:
        True if user has permission, False otherwise
    """
    if not user.is_authenticated:
        return False
    
    # Check specific permissions
    permission_name = f"{resource}.{action}"
    return user.has_perm(permission_name)

@login_required
def secure_mutation_resolver(self, info, **kwargs):
    """Secure mutation resolver with permission checks."""
    user = info.context.user
    
    if not check_user_permissions(user, 'create', 'user'):
        raise PermissionDenied("Insufficient permissions")
    
    # Proceed with mutation logic
    pass
```

## Performance Guidelines

### Database Optimization
```python
from django.db.models import Prefetch, select_related, prefetch_related

def get_users_with_related_data():
    """Get users with optimized related data loading."""
    return User.objects.select_related(
        'profile'
    ).prefetch_related(
        'groups',
        Prefetch(
            'orders',
            queryset=Order.objects.select_related('product')
        )
    )

def resolve_users_efficiently(self, info):
    """Resolve users query with optimized database access."""
    # Analyze requested fields to optimize queries
    requested_fields = get_requested_fields(info)
    
    queryset = User.objects.all()
    
    # Add select_related for foreign keys
    if 'profile' in requested_fields:
        queryset = queryset.select_related('profile')
    
    # Add prefetch_related for reverse relationships
    if 'orders' in requested_fields:
        queryset = queryset.prefetch_related('orders')
    
    return queryset
```

### Caching Strategies
```python
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

def get_cached_schema(cache_key: str, generator_func, timeout: int = 3600):
    """Get schema from cache or generate if not exists."""
    schema = cache.get(cache_key)
    
    if schema is None:
        schema = generator_func()
        cache.set(cache_key, schema, timeout)
    
    return schema

@method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
def schema_view(request):
    """Cached schema view."""
    pass
```

## Code Review Guidelines

### Review Checklist
- [ ] Code follows style guidelines
- [ ] All functions have proper type hints
- [ ] Comprehensive error handling is implemented
- [ ] Security considerations are addressed
- [ ] Performance implications are considered
- [ ] Tests are included and comprehensive
- [ ] Documentation is complete and accurate
- [ ] No hardcoded secrets or credentials
- [ ] Database queries are optimized
- [ ] Logging is appropriate and informative

### Review Comments Format
```python
# Good review comment:
# Consider using select_related() here to avoid N+1 queries
# when accessing the related user profile data.

# Bad review comment:
# This is wrong.
```

### Approval Criteria
- All automated tests pass
- Code coverage meets minimum threshold (80%)
- Security scan passes
- Performance benchmarks are within acceptable limits
- Documentation is updated
- Breaking changes are documented

## Tools and Automation

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
```

### IDE Configuration
```json
// VS Code settings.json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.rulers": [100],
    "files.trimTrailingWhitespace": true
}
```

## Conclusion

This style guide ensures consistency, maintainability, and quality across the Django GraphQL Auto-Generation System codebase. All contributors should familiarize themselves with these guidelines and apply them consistently.

For questions or suggestions regarding this style guide, please open an issue or submit a pull request.