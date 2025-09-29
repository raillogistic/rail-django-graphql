# Troubleshooting Guide

This guide helps you diagnose and resolve common issues when using the Django GraphQL Auto-Generation Library.

## 📚 Table of Contents

- [Common Issues](#common-issues)
- [Schema Generation Problems](#schema-generation-problems)
- [Query and Mutation Errors](#query-and-mutation-errors)
- [Filtering Issues](#filtering-issues)
- [Relationship Problems](#relationship-problems)
- [Performance Issues](#performance-issues)
- [Configuration Problems](#configuration-problems)
- [Development and Debugging](#development-and-debugging)
- [FAQ](#faq)

## 🚨 Common Issues

### Issue: Schema Not Generated

**Symptoms:**
- GraphQL schema is empty or missing types
- No queries or mutations available
- Error: "Schema contains no types"

**Possible Causes:**
1. Models not properly registered
2. Missing `GraphQLMeta` configuration
3. Import errors in models
4. Circular import issues

**Solutions:**

```python
# 1. Ensure models are properly imported
# apps.py
from django.apps import AppConfig

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'your_app'
    
    def ready(self):
        # Import models to ensure they're registered
        from . import models

# 2. Check model registration
# models.py
from django_graphql_auto.registry import model_registry

class YourModel(models.Model):
    name = models.CharField(max_length=100)
    
    class GraphQLMeta:
        enable_queries = True
        enable_mutations = True

# Verify registration
print(model_registry.get_registered_models())

# 3. Debug schema generation
from django_graphql_auto.schema import build_schema

try:
    schema = build_schema()
    print("Schema generated successfully")
    print(f"Types: {list(schema.type_map.keys())}")
except Exception as e:
    print(f"Schema generation failed: {e}")
    import traceback
    traceback.print_exc()
```

### Issue: Import Errors

**Symptoms:**
- `ImportError` or `ModuleNotFoundError`
- "No module named 'django_graphql_auto'"
- Circular import errors

**Solutions:**

```python
# 1. Check installation
pip list | grep django-graphql-auto

# 2. Verify INSTALLED_APPS
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'graphene_django',
    'django_graphql_auto',
    'your_app',  # Make sure your app is included
]

# 3. Fix circular imports
# Instead of importing in models.py
from django_graphql_auto.decorators import graphql_model

@graphql_model
class MyModel(models.Model):
    pass

# Import in apps.py ready() method
class MyAppConfig(AppConfig):
    def ready(self):
        from . import models  # Import here to avoid circular imports
```

### Issue: Database Connection Errors

**Symptoms:**
- "Database connection failed"
- "Table doesn't exist" errors
- Migration-related issues

**Solutions:**

```bash
# 1. Run migrations
python manage.py makemigrations
python manage.py migrate

# 2. Check database configuration
python manage.py dbshell

# 3. Verify model registration after migrations
python manage.py shell
>>> from your_app.models import YourModel
>>> YourModel.objects.count()
```

## 🏗️ Schema Generation Problems

### Issue: Missing Fields in GraphQL Types

**Symptoms:**
- Some model fields don't appear in GraphQL schema
- Fields are None in GraphQL responses
- Type definitions incomplete

**Diagnosis:**

```python
# Debug field generation
from django_graphql_auto.generators.types import TypeGenerator
from your_app.models import YourModel

generator = TypeGenerator()
type_info = generator.generate_type(YourModel)

print("Generated fields:")
for field_name, field_info in type_info.fields.items():
    print(f"  {field_name}: {field_info}")

# Check field exclusions
meta = getattr(YourModel, 'GraphQLMeta', None)
if meta:
    print(f"Excluded fields: {getattr(meta, 'exclude_fields', [])}")
    print(f"Only fields: {getattr(meta, 'only_fields', [])}")
```

**Solutions:**

```python
# 1. Check field configuration
class YourModel(models.Model):
    name = models.CharField(max_length=100)
    secret = models.CharField(max_length=100)
    
    class GraphQLMeta:
        # Include specific fields
        only_fields = ['name']  # Only 'name' will be included
        
        # Or exclude specific fields
        exclude_fields = ['secret']  # 'secret' will be excluded
        
        # Enable all fields (default)
        # exclude_fields = []
        # only_fields = []

# 2. Handle custom field types
from django_graphql_auto.scalars import register_scalar
import graphene

# Register custom scalar for unsupported field types
register_scalar(YourCustomField, graphene.String)

# 3. Debug field introspection
from django_graphql_auto.introspection import ModelIntrospector

introspector = ModelIntrospector()
field_info = introspector.get_field_info(YourModel, 'problematic_field')
print(f"Field info: {field_info}")
```

### Issue: Incorrect Field Types

**Symptoms:**
- GraphQL fields have wrong types (String instead of Int, etc.)
- Type conversion errors
- Scalar type mismatches

**Solutions:**

```python
# 1. Check field type mapping
from django_graphql_auto.type_mapping import get_graphql_type
from django.db import models

# Debug type mapping
field = models.IntegerField()
graphql_type = get_graphql_type(field)
print(f"Django field: {field} -> GraphQL type: {graphql_type}")

# 2. Register custom type mappings
from django_graphql_auto.type_mapping import register_type_mapping
import graphene

# Map custom Django field to GraphQL type
register_type_mapping(YourCustomField, graphene.String)

# 3. Override field types in model
class YourModel(models.Model):
    special_field = models.TextField()
    
    class GraphQLMeta:
        field_types = {
            'special_field': graphene.String(description="Special text field")
        }
```

## 🔍 Query and Mutation Errors

### Issue: Query Execution Errors

**Symptoms:**
- "Field doesn't exist" errors
- Permission denied errors
- Validation errors during queries

**Debugging:**

```python
# Enable GraphQL debugging
# settings.py
GRAPHENE = {
    'SCHEMA': 'your_project.schema.schema',
    'MIDDLEWARE': [
        'graphene_django.debug.DjangoDebugMiddleware',
    ],
}

# Debug query execution
import graphene
from graphene_django.debug import DjangoDebugMiddleware

class Query(graphene.ObjectType):
    debug = graphene.Field(DjangoDebugMiddleware)

# Test query in shell
from graphene.test import Client
from your_project.schema import schema

client = Client(schema)
result = client.execute('''
    query {
        allYourModels {
            id
            name
        }
    }
''')

print("Errors:", result.get('errors'))
print("Data:", result.get('data'))
```

**Solutions:**

```python
# 1. Check field permissions
class YourModel(models.Model):
    name = models.CharField(max_length=100)
    
    class GraphQLMeta:
        # Configure field permissions
        field_permissions = {
            'name': 'your_app.view_yourmodel'
        }

# 2. Handle query errors gracefully
from django_graphql_auto.exceptions import GraphQLError

class CustomQuery(graphene.ObjectType):
    your_model = graphene.Field(YourModelType, id=graphene.ID())
    
    def resolve_your_model(self, info, id):
        try:
            return YourModel.objects.get(id=id)
        except YourModel.DoesNotExist:
            raise GraphQLError(f"YourModel with id {id} not found")
        except Exception as e:
            raise GraphQLError(f"Error fetching YourModel: {str(e)}")

# 3. Validate query arguments
def resolve_your_models(self, info, **kwargs):
    # Validate arguments
    if 'limit' in kwargs and kwargs['limit'] > 100:
        raise GraphQLError("Limit cannot exceed 100")
    
    return YourModel.objects.all()[:kwargs.get('limit', 10)]
```

### Issue: Mutation Validation Errors

**Symptoms:**
- "Validation failed" errors
- Required field errors
- Data type conversion errors
- Field-specific error information missing

**Enhanced Error Handling:**

The system now provides detailed field-specific error information for better debugging:

```python
# Example mutation with enhanced error response
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ok
    post {
      id
      title
    }
    errors {
      field       # Specific field that caused the error
      message     # Human-readable error message
      code        # Error code for programmatic handling
    }
  }
}
```

**Common Error Scenarios:**

#### 1. Validation Errors with Field Extraction
```python
# Input with validation error
{
  "input": {
    "title": "",  # Empty title
    "content": "Some content"
  }
}

# Enhanced error response
{
  "data": {
    "createPost": {
      "ok": false,
      "post": null,
      "errors": [{
        "field": "title",
        "message": "Ce champ ne peut pas être vide.",
        "code": "VALIDATION_ERROR"
      }]
    }
  }
}
```

#### 2. Database Constraint Errors
```python
# Duplicate entry error
{
  "input": {
    "username": "existing_user",  # Already exists
    "email": "user@example.com"
  }
}

# Enhanced error response
{
  "data": {
    "createUser": {
      "ok": false,
      "user": null,
      "errors": [{
        "field": "username",
        "message": "Ce nom d'utilisateur existe déjà",
        "code": "DUPLICATE_ENTRY"
      }]
    }
  }
}
```

#### 3. Foreign Key Validation Errors
```python
# Invalid foreign key reference
{
  "input": {
    "title": "New Post",
    "category_id": 999  # Non-existent category
  }
}

# Enhanced error response
{
  "data": {
    "createPost": {
      "ok": false,
      "post": null,
      "errors": [{
        "field": "category",
        "message": "La catégorie spécifiée n'existe pas",
        "code": "FOREIGN_KEY_ERROR"
      }]
    }
  }
}
```

**Solutions:**

```python
# 1. Debug mutation input validation
from django_graphql_auto.mutations import get_mutation_class

MutationClass = get_mutation_class(YourModel, 'create')
mutation = MutationClass()

# Test validation
test_input = {
    'name': 'Test',
    'invalid_field': 'value'
}

try:
    validated_data = mutation.validate_input(test_input)
    print("Validation passed:", validated_data)
except Exception as e:
    print("Validation failed:", e)

# 2. Custom validation with enhanced error handling
class YourModel(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom")
    email = models.EmailField(verbose_name="Adresse email")
    
    def clean(self):
        if not self.name:
            raise ValidationError({
                'name': "Le nom est requis"
            })
        
        if len(self.name) < 3:
            raise ValidationError({
                'name': "Le nom doit contenir au moins 3 caractères"
            })
    
    class GraphQLMeta:
        # Enable model validation
        enable_model_validation = True

# 3. Handle validation errors in mutations
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django_graphql_auto.mutations import BaseMutation

class CustomCreateMutation(BaseMutation):
    class Meta:
        model = YourModel
        operation = 'create'
    
    @classmethod
    def perform_mutation(cls, root, info, **input_data):
        try:
            return super().perform_mutation(root, info, **input_data)
        except ValidationError as e:
            # Enhanced error handling with field extraction
            errors = []
            if hasattr(e, 'error_dict'):
                for field, field_errors in e.error_dict.items():
                    for error in field_errors:
                        errors.append({
                            'field': field,
                            'message': str(error),
                            'code': 'VALIDATION_ERROR'
                        })
            else:
                errors.append({
                    'field': None,
                    'message': str(e),
                    'code': 'VALIDATION_ERROR'
                })
            
            return cls(
                ok=False,
                errors=errors
            )
        except IntegrityError as e:
            # Database constraint error handling
            error_message = str(e)
            field = None
            code = 'INTEGRITY_ERROR'
            
            # Extract field from constraint error
            if 'UNIQUE constraint failed' in error_message:
                # Extract field name from error message
                import re
                match = re.search(r'UNIQUE constraint failed: \w+\.(\w+)', error_message)
                if match:
                    field = match.group(1)
                code = 'DUPLICATE_ENTRY'
            
            return cls(
                ok=False,
                errors=[{
                    'field': field,
                    'message': "Cette valeur existe déjà" if field else error_message,
                    'code': code
                }]
            )

# 4. Testing error scenarios
def test_mutation_errors():
    """Test various error scenarios with enhanced error handling"""
    
    # Test validation error
    result = schema.execute('''
        mutation {
            createPost(input: { title: "" }) {
                ok
                errors {
                    field
                    message
                    code
                }
            }
        }
    ''')
    
    assert not result.data['createPost']['ok']
    assert result.data['createPost']['errors'][0]['field'] == 'title'
    assert result.data['createPost']['errors'][0]['code'] == 'VALIDATION_ERROR'
    
    # Test duplicate entry error
    result = schema.execute('''
        mutation {
            createUser(input: { username: "existing_user" }) {
                ok
                errors {
                    field
                    message
                    code
                }
            }
        }
    ''')
    
    assert not result.data['createUser']['ok']
    assert result.data['createUser']['errors'][0]['field'] == 'username'
    assert result.data['createUser']['errors'][0]['code'] == 'DUPLICATE_ENTRY'
```

## 🔧 Filtering Issues

### Issue: Filters Not Working

**Symptoms:**
- Filter arguments ignored
- "Unknown filter" errors
- Incorrect filter results

**Debugging:**

```python
# Debug filter generation
from django_graphql_auto.filters import FilterGenerator
from your_app.models import YourModel

generator = FilterGenerator()
filter_info = generator.generate_filters(YourModel)

print("Available filters:")
for filter_name, filter_config in filter_info.items():
    print(f"  {filter_name}: {filter_config}")

# Test filter in shell
queryset = YourModel.objects.all()
filtered = generator.apply_filters(queryset, {
    'name__icontains': 'test'
})
print(f"Filtered results: {filtered.count()}")
```

**Solutions:**

```python
# 1. Enable filtering
class YourModel(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class GraphQLMeta:
        # Enable filtering
        enable_filtering = True
        
        # Configure available filters
        filter_fields = {
            'name': ['exact', 'icontains', 'startswith'],
            'created_at': ['exact', 'gte', 'lte'],
        }

# 2. Custom filter implementation
from django_graphql_auto.filters import BaseFilter

class CustomFilter(BaseFilter):
    def filter_custom_field(self, queryset, value):
        # Custom filtering logic
        return queryset.filter(custom_condition=value)

# Register custom filter
from django_graphql_auto.filters import register_filter
register_filter(YourModel, 'custom', CustomFilter)

# 3. Debug filter application
# In GraphQL query
query {
  allYourModels(filters: {name_Icontains: "test"}) {
    id
    name
  }
}

# Check generated SQL
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('django.db.backends')
logger.setLevel(logging.DEBUG)
```

### Issue: Complex Filter Combinations

**Symptoms:**
- AND/OR combinations not working
- Nested filter errors
- Performance issues with complex filters

**Solutions:**

```python
# 1. Use Q objects for complex filtering
from django.db.models import Q
from django_graphql_auto.filters import ComplexFilter

class YourModelFilter(ComplexFilter):
    class Meta:
        model = YourModel
        fields = {
            'name': ['exact', 'icontains'],
            'status': ['exact', 'in'],
            'created_at': ['gte', 'lte'],
        }
    
    def filter_complex_condition(self, queryset, value):
        """Custom complex filter."""
        return queryset.filter(
            Q(name__icontains=value) | Q(description__icontains=value)
        )

# 2. Configure filter combinations
class YourModel(models.Model):
    name = models.CharField(max_length=100)
    
    class GraphQLMeta:
        filter_config = {
            'enable_and_or': True,
            'max_filter_depth': 3,
            'enable_negation': True,
        }

# 3. Optimize complex filters
from django.db import models

class YourModel(models.Model):
    name = models.CharField(max_length=100, db_index=True)  # Add index
    status = models.CharField(max_length=20, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name', 'status']),  # Composite index
        ]
```

## 🔗 Relationship Problems

### Issue: Related Objects Not Loading

**Symptoms:**
- Related fields return null
- N+1 query problems
- "RelatedObjectDoesNotExist" errors

**Solutions:**

```python
# 1. Configure relationship loading
from django_graphql_auto.optimization import QueryOptimizer

class YourModel(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    
    class GraphQLMeta:
        # Enable relationship optimization
        optimize_queries = True
        
        # Configure prefetching
        select_related = ['author']
        prefetch_related = ['tags', 'comments']

# 2. Debug relationship queries
from django.db import connection
from django.test.utils import override_settings

with override_settings(DEBUG=True):
    # Execute GraphQL query
    result = schema.execute('''
        query {
            allYourModels {
                id
                name
                author {
                    name
                }
            }
        }
    ''')
    
    # Check executed queries
    print(f"Number of queries: {len(connection.queries)}")
    for query in connection.queries:
        print(query['sql'])

# 3. Handle missing relationships
class YourModelType(DjangoObjectType):
    class Meta:
        model = YourModel
        fields = '__all__'
    
    def resolve_author(self, info):
        try:
            return self.author
        except Author.DoesNotExist:
            return None
```

### Issue: Circular Relationship Errors

**Symptoms:**
- "Maximum recursion depth exceeded"
- Circular import errors
- Infinite loops in schema generation

**Solutions:**

```python
# 1. Use string references for forward declarations
class Author(models.Model):
    name = models.CharField(max_length=100)

class Post(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey('Author', on_delete=models.CASCADE)  # String reference

class Comment(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE)  # String reference
    content = models.TextField()

# 2. Configure relationship depth limits
class YourModel(models.Model):
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True)
    
    class GraphQLMeta:
        # Limit recursion depth
        max_relationship_depth = 3
        
        # Exclude circular relationships
        exclude_relationships = ['parent__parent__parent']

# 3. Use lazy loading for complex relationships
from django_graphql_auto.types import LazyType

class PostType(DjangoObjectType):
    comments = graphene.List(LazyType('CommentType'))
    
    class Meta:
        model = Post
        fields = '__all__'
```

## ⚡ Performance Issues

### Issue: Slow Query Performance

**Symptoms:**
- Long response times
- High database load
- Memory usage issues

**Diagnosis:**

```python
# 1. Enable query logging
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}

# 2. Profile GraphQL queries
import time
from django.db import connection

def profile_query(query_string):
    start_time = time.time()
    start_queries = len(connection.queries)
    
    result = schema.execute(query_string)
    
    end_time = time.time()
    end_queries = len(connection.queries)
    
    print(f"Execution time: {end_time - start_time:.2f}s")
    print(f"Database queries: {end_queries - start_queries}")
    
    return result

# 3. Analyze query complexity
from graphql.validation import validate
from graphql.validation.rules import QueryComplexityRule

# Add complexity analysis
complexity_rule = QueryComplexityRule(max_complexity=1000)
```

**Solutions:**

```python
# 1. Optimize database queries
class YourModel(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    
    class GraphQLMeta:
        # Enable query optimization
        optimize_queries = True
        
        # Configure pagination
        pagination = {
            'page_size': 20,
            'max_page_size': 100,
        }
        
        # Limit query depth
        max_query_depth = 5

# 2. Use database indexes
class YourModel(models.Model):
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['-created_at']),  # For ordering
        ]

# 3. Implement caching
from django.core.cache import cache
from django_graphql_auto.caching import CacheManager

class CachedYourModelType(DjangoObjectType):
    class Meta:
        model = YourModel
        fields = '__all__'
    
    @staticmethod
    def resolve_expensive_field(root, info):
        cache_key = f"expensive_field_{root.id}"
        result = cache.get(cache_key)
        
        if result is None:
            result = expensive_calculation(root)
            cache.set(cache_key, result, timeout=300)  # 5 minutes
        
        return result
```

### Issue: Memory Usage Problems

**Symptoms:**
- High memory consumption
- Out of memory errors
- Slow garbage collection

**Solutions:**

```python
# 1. Implement pagination
from django_graphql_auto.pagination import CursorPagination

class YourModel(models.Model):
    name = models.CharField(max_length=100)
    
    class GraphQLMeta:
        # Enable pagination
        enable_pagination = True
        pagination_class = CursorPagination
        default_page_size = 20
        max_page_size = 100

# 2. Use iterator for large datasets
from django_graphql_auto.resolvers import IteratorResolver

class YourModelResolver(IteratorResolver):
    def resolve_large_dataset(self, info, **kwargs):
        # Use iterator to avoid loading all objects into memory
        return YourModel.objects.iterator(chunk_size=1000)

# 3. Optimize object creation
from django_graphql_auto.optimization import ObjectPool

class OptimizedYourModelType(DjangoObjectType):
    class Meta:
        model = YourModel
        fields = '__all__'
    
    @classmethod
    def get_node(cls, info, id):
        # Use object pooling for frequently accessed objects
        return ObjectPool.get_or_create(YourModel, id)
```

## ⚙️ Configuration Problems

### Issue: Settings Not Applied

**Symptoms:**
- Configuration changes ignored
- Default behavior instead of custom settings
- Settings validation errors

**Solutions:**

```python
# 1. Verify settings structure
# settings.py
DJANGO_GRAPHQL_AUTO = {
    'SCHEMA_GENERATION': {
        'AUTO_GENERATE_SCHEMA': True,
        'INCLUDE_DJANGO_CONTRIB_MODELS': False,
    },
    'QUERY_OPTIMIZATION': {
        'ENABLE_QUERY_OPTIMIZATION': True,
        'DEFAULT_PAGE_SIZE': 20,
    },
    'FILTERING': {
        'ENABLE_FILTERING': True,
        'DEFAULT_FILTER_BACKEND': 'django_graphql_auto.filters.DjangoFilterBackend',
    }
}

# 2. Validate settings
from django_graphql_auto.settings import validate_settings

try:
    validate_settings()
    print("Settings are valid")
except Exception as e:
    print(f"Settings validation failed: {e}")

# 3. Debug settings loading
from django_graphql_auto.settings import app_settings

print("Current settings:")
for key, value in app_settings.items():
    print(f"  {key}: {value}")
```

### Issue: Model Configuration Conflicts

**Symptoms:**
- Conflicting GraphQLMeta settings
- Inheritance issues with configuration
- Settings not inherited properly

**Solutions:**

```python
# 1. Use proper inheritance
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
    
    class GraphQLMeta:
        # Base configuration
        enable_queries = True
        enable_mutations = True
        exclude_fields = ['created_at']

class YourModel(BaseModel):
    name = models.CharField(max_length=100)
    
    class GraphQLMeta(BaseModel.GraphQLMeta):
        # Extend base configuration
        include_fields = ['created_at']  # Override exclusion
        filter_fields = ['name']

# 2. Debug configuration inheritance
from django_graphql_auto.configuration import get_model_config

config = get_model_config(YourModel)
print("Final configuration:")
for key, value in config.items():
    print(f"  {key}: {value}")

# 3. Resolve configuration conflicts
class YourModel(models.Model):
    name = models.CharField(max_length=100)
    
    class GraphQLMeta:
        # Explicit configuration to avoid conflicts
        enable_queries = True
        enable_mutations = True
        
        # Clear field configuration
        exclude_fields = []
        only_fields = []
        
        # Explicit filter configuration
        enable_filtering = True
        filter_fields = {
            'name': ['exact', 'icontains']
        }
```

## 🐛 Development and Debugging

### Enable Debug Mode

```python
# settings.py
DEBUG = True

DJANGO_GRAPHQL_AUTO = {
    'DEBUG': True,
    'ENABLE_INTROSPECTION': True,
    'ENABLE_PLAYGROUND': True,
}

GRAPHENE = {
    'SCHEMA': 'your_project.schema.schema',
    'MIDDLEWARE': [
        'graphene_django.debug.DjangoDebugMiddleware',
    ],
}
```

### Debug Schema Generation

```python
# Debug script
from django_graphql_auto.schema import SchemaBuilder
from django_graphql_auto.registry import model_registry

# Check registered models
print("Registered models:")
for model in model_registry.get_registered_models():
    print(f"  {model.__name__}")

# Debug schema building
builder = SchemaBuilder()
try:
    schema = builder.build()
    print("Schema built successfully")
    
    # Print schema types
    print("Schema types:")
    for type_name in schema.type_map.keys():
        if not type_name.startswith('__'):
            print(f"  {type_name}")
            
except Exception as e:
    print(f"Schema building failed: {e}")
    import traceback
    traceback.print_exc()
```

### Test GraphQL Queries

```python
# Test script
from graphene.test import Client
from your_project.schema import schema

client = Client(schema)

# Test introspection
introspection_query = '''
    query IntrospectionQuery {
        __schema {
            types {
                name
                kind
            }
        }
    }
'''

result = client.execute(introspection_query)
print("Introspection result:", result)

# Test basic query
test_query = '''
    query {
        allYourModels {
            id
            name
        }
    }
'''

result = client.execute(test_query)
print("Query result:", result)
```

## ❓ FAQ

### Q: Why is my schema empty?

**A:** Common causes:
1. Models not imported in `apps.py`
2. Missing `GraphQLMeta` configuration
3. All fields excluded in configuration
4. Import errors preventing model registration

### Q: How do I handle custom field types?

**A:** Register custom scalar mappings:

```python
from django_graphql_auto.scalars import register_scalar
import graphene

register_scalar(YourCustomField, graphene.String)
```

### Q: Why are my filters not working?

**A:** Check:
1. `enable_filtering = True` in `GraphQLMeta`
2. Fields included in `filter_fields`
3. Correct filter syntax in GraphQL query
4. Database indexes for filtered fields

### Q: How do I optimize query performance?

**A:** Use:
1. Database indexes on filtered/ordered fields
2. `select_related` and `prefetch_related`
3. Pagination for large datasets
4. Query complexity limits
5. Caching for expensive operations

### Q: Can I customize the generated mutations?

**A:** Yes, several ways:
1. Override mutation classes
2. Use custom mutation mixins
3. Implement custom validation
4. Add custom business logic

### Q: How do I handle permissions?

**A:** Configure permissions in `GraphQLMeta`:

```python
class YourModel(models.Model):
    class GraphQLMeta:
        query_permissions = ['your_app.view_yourmodel']
        mutation_permissions = ['your_app.change_yourmodel']
        field_permissions = {
            'sensitive_field': 'your_app.view_sensitive_data'
        }
```

### Q: What about file uploads?

**A:** Use the built-in file handling:

```python
class YourModel(models.Model):
    file = models.FileField(upload_to='uploads/')
    
    class GraphQLMeta:
        enable_file_uploads = True
```

### Q: How do I add custom business logic?

**A:** Override mutation methods:

```python
from django_graphql_auto.mutations import CreateMutation

class CustomCreateMutation(CreateMutation):
    class Meta:
        model = YourModel
    
    @classmethod
    def perform_mutation(cls, root, info, **input_data):
        # Add custom logic here
        instance = super().perform_mutation(root, info, **input_data)
        
        # Post-creation logic
        send_notification(instance)
        
        return instance
```

## 🆘 Getting Help

If you're still experiencing issues:

1. **Check the logs** - Enable Django and GraphQL debugging
2. **Review the documentation** - Especially the [API Reference](../api/core-classes.md)
3. **Search existing issues** - Check our GitHub issues
4. **Create a minimal reproduction** - Isolate the problem
5. **Ask for help** - Join our community discussions

## 🔗 Related Documentation

- [Installation Guide](../setup/installation.md)
- [Configuration Reference](../setup/configuration.md)
- [API Documentation](../api/core-classes.md)
- [Performance Guide](../development/performance.md)
- [Testing Guide](../development/testing.md)