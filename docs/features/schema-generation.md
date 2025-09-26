# Schema Generation

This document explains how the Django GraphQL Auto-Generation Library automatically creates comprehensive GraphQL schemas from your Django models.

## 📚 Table of Contents

- [Overview](#overview)
- [Model Analysis](#model-analysis)
- [Type Generation](#type-generation)
- [Query Generation](#query-generation)
- [Mutation Generation](#mutation-generation)
- [Method Mutations](#method-mutations)
- [Bulk Operations](#bulk-operations)
- [Schema Assembly](#schema-assembly)
- [Configuration Options](#configuration-options)
- [Advanced Features](#advanced-features)

## 🔍 Overview

The schema generation process consists of several phases:

1. **Model Introspection**: Analyze Django models and extract metadata
2. **Type Generation**: Create GraphQL types from Django models
3. **Query Generation**: Generate queries for data retrieval
4. **Mutation Generation**: Create mutations for data manipulation
5. **Schema Assembly**: Combine all components into a unified schema

## 🔬 Model Analysis

### ModelIntrospector Class

The `ModelIntrospector` class is responsible for analyzing Django models and extracting all necessary metadata for GraphQL schema generation.

```python
from django_graphql_auto.generators.introspector import ModelIntrospector

introspector = ModelIntrospector()
field_info = introspector.get_model_fields(MyModel)
relationships = introspector.get_model_relationships(MyModel)
methods = introspector.get_model_methods(MyModel)
```

### Field Analysis

The introspector analyzes each model field and extracts:

- **Field Type**: CharField, IntegerField, ForeignKey, etc.
- **Constraints**: max_length, null, blank, unique, etc.
- **Default Values**: default values and auto-generated fields
- **Validation Rules**: validators and custom validation logic
- **Relationships**: foreign keys, many-to-many, one-to-one relationships

#### Enhanced Field Information

```python
class FieldInfo:
    name: str
    field_type: Type[Field]
    graphql_type: Type[Scalar]
    is_required: bool
    is_list: bool
    max_length: Optional[int]
    choices: Optional[List[Tuple]]
    default: Any
    help_text: str
    
    # Enhanced attributes for smart requirements
    has_auto_now: bool          # auto_now=True
    has_auto_now_add: bool      # auto_now_add=True
    blank: bool                 # blank=True/False
    has_default: bool           # Field has default value
    is_primary_key: bool        # Primary key field
```

### Relationship Analysis

The system identifies and analyzes all types of Django relationships:

```python
class RelationshipInfo:
    name: str
    relationship_type: str      # 'foreign_key', 'many_to_many', 'one_to_one'
    related_model: Type[Model]
    related_name: Optional[str]
    on_delete: str             # CASCADE, PROTECT, SET_NULL, etc.
    through_model: Optional[Type[Model]]  # For M2M through relationships
```

### Method Analysis

The introspector can also analyze model methods and properties for potential GraphQL field generation:

```python
class MethodInfo:
    name: str
    return_type: Type
    is_property: bool
    parameters: List[Parameter]
    docstring: Optional[str]
```

## 🏗️ Type Generation

### TypeGenerator Class

The `TypeGenerator` creates GraphQL types from Django models with intelligent field mapping and requirement detection.

```python
from django_graphql_auto.generators.types import TypeGenerator

generator = TypeGenerator()
object_type = generator.generate_object_type(MyModel)
input_type = generator.generate_input_type(MyModel, mutation_type='create')
```

### Object Type Generation

For each Django model, the generator creates a corresponding GraphQL ObjectType:

```python
# Django Model
class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

# Generated GraphQL Type
class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = '__all__'
    
    # Additional computed fields
    is_recent = graphene.Boolean()
    word_count = graphene.Int()
    
    def resolve_is_recent(self, info):
        return (timezone.now() - self.created_at).days < 7
    
    def resolve_word_count(self, info):
        return len(self.content.split())
```

### Input Type Generation

The generator creates different input types for different mutation operations:

#### Create Input Type

```python
class CreatePostInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    content = graphene.String(required=True)
    author_id = graphene.ID(required=True)
    published = graphene.Boolean()  # Not required (has default)
    # created_at is excluded (auto_now_add=True)
```

#### Update Input Type

```python
class UpdatePostInput(graphene.InputObjectType):
    title = graphene.String()      # All fields optional except ID
    content = graphene.String()
    author_id = graphene.ID()
    published = graphene.Boolean()
    # created_at is excluded (auto_now_add=True)
```

### Smart Field Requirements

The type generator implements intelligent field requirement logic:

```python
def _should_field_be_required_for_create(self, field_info: FieldInfo, field_name: str) -> bool:
    """Determine if a field should be required for create mutations."""
    
    # Primary key fields are never required
    if field_info.is_primary_key:
        return False
    
    # Auto-generated fields are never required
    if field_info.has_auto_now or field_info.has_auto_now_add:
        return False
    
    # Fields with defaults are not required
    if field_info.has_default:
        return False
    
    # Blank fields are not required
    if field_info.blank:
        return False
    
    # Field is required if it's not null and has no default
    return not field_info.null

def _should_field_be_required_for_update(self, field_info: FieldInfo) -> bool:
    """For updates, only ID is typically required."""
    return field_info.is_primary_key
```

## 🔍 Query Generation

### QueryGenerator Class

The `QueryGenerator` creates comprehensive query operations for each model:

```python
from django_graphql_auto.generators.queries import QueryGenerator

generator = QueryGenerator()
single_query = generator.generate_single_query(MyModel)
list_query = generator.generate_list_query(MyModel)
paginated_query = generator.generate_paginated_query(MyModel)
```

### Generated Query Types

#### Single Object Query

```python
# Generated query
post = graphene.Field(PostType, id=graphene.ID(required=True))

def resolve_post(self, info, id):
    try:
        return Post.objects.get(id=id)
    except Post.DoesNotExist:
        return None
```

#### List Query

```python
# Generated query with filtering support
posts = graphene.List(
    PostType,
    filters=PostFilterInput(),
    order_by=graphene.List(graphene.String),
    limit=graphene.Int(),
    offset=graphene.Int()
)

def resolve_posts(self, info, filters=None, order_by=None, limit=None, offset=None):
    queryset = Post.objects.all()
    
    # Apply filters
    if filters:
        queryset = self.apply_filters(queryset, filters)
    
    # Apply ordering
    if order_by:
        queryset = queryset.order_by(*order_by)
    
    # Apply pagination
    if offset:
        queryset = queryset[offset:]
    if limit:
        queryset = queryset[:limit]
    
    return queryset
```

#### Paginated Query

```python
# Generated paginated query
post_pages = graphene.Field(
    PostConnection,
    first=graphene.Int(),
    after=graphene.String(),
    filters=PostFilterInput(),
    order_by=graphene.List(graphene.String)
)

def resolve_post_pages(self, info, first=None, after=None, filters=None, order_by=None):
    queryset = Post.objects.all()
    
    # Apply filters and ordering
    if filters:
        queryset = self.apply_filters(queryset, filters)
    if order_by:
        queryset = queryset.order_by(*order_by)
    
    # Return paginated results
    return queryset
```

### Query Naming Conventions

The library follows consistent naming conventions:

- **Single queries**: `post`, `user`, `category` (singular, snake_case)
- **List queries**: `posts`, `users`, `categories` (plural, snake_case)
- **Paginated queries**: `post_pages`, `user_pages`, `category_pages` (plural + "_pages")

## ✏️ Mutation Generation

### MutationGenerator Class

The `MutationGenerator` creates CRUD mutations with standardized return types:

```python
from django_graphql_auto.generators.mutations import MutationGenerator

generator = MutationGenerator()
create_mutation = generator.generate_create_mutation(MyModel)
update_mutation = generator.generate_update_mutation(MyModel)
delete_mutation = generator.generate_delete_mutation(MyModel)
```

### Standardized Mutation Returns

All mutations follow a consistent return pattern:

```python
class PostMutationResult(graphene.ObjectType):
    ok = graphene.Boolean(required=True)
    post = graphene.Field(PostType)
    errors = graphene.List(graphene.String, required=True)

class CreatePost(graphene.Mutation):
    class Arguments:
        input = CreatePostInput(required=True)
    
    Output = PostMutationResult
    
    def mutate(self, info, input):
        try:
            # Validation
            errors = self.validate_input(input)
            if errors:
                return PostMutationResult(ok=False, errors=errors)
            
            # Create object
            post = Post.objects.create(**input)
            
            return PostMutationResult(ok=True, post=post, errors=[])
            
        except Exception as e:
            return PostMutationResult(ok=False, errors=[str(e)])
```

### Nested Operations Support

The mutation generator supports configurable nested create and update operations with enhanced input sanitization:

```python
# Create post with nested category and tags (when nested relations are enabled)
mutation {
  createPost(input: {
    title: "My Post with \"Quotes\"",
    content: "Content with JSON-like data: {\"key\": \"value\"}",
    category: {
      name: "Technology",
      description: "Tech articles with \"special\" characters"
    },
    tags: [
      { name: "GraphQL" },
      { name: "Django" }
    ]
  }) {
    ok
    post {
      id
      title
      category { name }
      tags { name }
    }
    errors
  }
}
```

### Enhanced Quote Handling

The library includes robust input sanitization for handling special characters:

- **Double Quote Sanitization**: Automatically handles `""` to `"` conversion
- **Recursive Processing**: Sanitizes nested dictionaries and lists
- **JSON Content Support**: Properly handles JSON-like strings in input
- **Special Character Protection**: Prevents injection through special characters

```python
# Input sanitization example
input_data = {
    'title': 'Post with ""double quotes""',
    'content': 'JSON data: {"key": "value with ""quotes"""}',
    'metadata': {
        'tags': ['tag with ""quotes""', 'normal tag']
    }
}

# After sanitization:
sanitized_data = {
    'title': 'Post with "double quotes"',
    'content': 'JSON data: {"key": "value with "quotes""}',
    'metadata': {
        'tags': ['tag with "quotes"', 'normal tag']
    }
}
```
  createPost(input: {
    title: "New Post"
    content: "Content..."
    category: {
      name: "New Category"
      description: "Created inline"
    }
    tags: [
      { name: "tag1", color: "#ff0000" }
      { name: "tag2", color: "#00ff00" }
    ]
  }) {
    ok
    post {
      id
      title
      category {
        id
        name
      }
      tags {
        id
        name
      }
    }
    errors
  }
}
```

## 🎯 Method Mutations

### Method Mutation Generation

The system automatically generates GraphQL mutations for Django model methods decorated with `@graphql_mutation`:

```python
from django_graphql_auto.decorators import graphql_mutation

class Order(models.Model):
    status = models.CharField(max_length=20, default='pending', verbose_name="Statut de la commande")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total de la commande")
    customer = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Client")
    
    @graphql_mutation
    def confirm_order(self):
        """Confirmer la commande et mettre à jour le statut."""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.save()
            return True
        return False
    
    @graphql_mutation
    def cancel_order(self, reason: str = "No reason provided"):
        """Annuler la commande avec une raison."""
        if self.status in ['pending', 'confirmed']:
            self.status = 'cancelled'
            self.cancellation_reason = reason
            self.save()
            return True
        return False
```

### Generated Method Mutations

```graphql
type Mutation {
  # Method mutations for Order model
  orderConfirmOrder(id: ID!): OrderConfirmOrderPayload
  orderCancelOrder(id: ID!, reason: String): OrderCancelOrderPayload
}

type OrderConfirmOrderPayload {
  ok: Boolean!
  order: OrderType
  result: Boolean  # Method return value
  errors: [String]
}

type OrderCancelOrderPayload {
  ok: Boolean!
  order: OrderType
  result: Boolean  # Method return value
  errors: [String]
}
```

### Method Mutation Usage

```graphql
mutation ConfirmOrder($orderId: ID!) {
  orderConfirmOrder(id: $orderId) {
    ok
    order {
      id
      status
    }
    result
    errors
  }
}

mutation CancelOrder($orderId: ID!, $reason: String!) {
  orderCancelOrder(id: $orderId, reason: $reason) {
    ok
    order {
      id
      status
      cancellationReason
    }
    result
    errors
  }
}
```

## 📦 Bulk Operations

### Bulk Operation Generation

The system automatically generates bulk operations for efficient batch processing:

```python
# Configuration for bulk operations
DJANGO_GRAPHQL_AUTO = {
    'MUTATION_SETTINGS': {
        'enable_bulk_operations': True,
        'bulk_batch_size': 100,
        'bulk_max_objects': 1000,
    }
}
```

### Generated Bulk Mutations

```graphql
type Mutation {
  # Bulk operations for Post model
  bulkCreatePost(input: BulkCreatePostInput!): BulkCreatePostPayload
  bulkUpdatePost(input: BulkUpdatePostInput!): BulkUpdatePostPayload
  bulkDeletePost(input: BulkDeletePostInput!): BulkDeletePostPayload
}

input BulkCreatePostInput {
  objects: [CreatePostInput!]!
}

input BulkUpdatePostInput {
  objects: [UpdatePostInput!]!
}

input BulkDeletePostInput {
  ids: [ID!]!
}

type BulkCreatePostPayload {
  ok: Boolean!
  objects: [PostType]
  errors: [String]
}

type BulkUpdatePostPayload {
  ok: Boolean!
  objects: [PostType]
  errors: [String]
}

type BulkDeletePostPayload {
  ok: Boolean!
  deletedIds: [ID]
  errors: [String]
}
```

### Bulk Operation Usage

```graphql
mutation BulkCreatePosts($input: BulkCreatePostInput!) {
  bulkCreatePost(input: $input) {
    ok
    objects {
      id
      title
      author {
        username
      }
    }
    errors
  }
}

mutation BulkUpdatePosts($input: BulkUpdatePostInput!) {
  bulkUpdatePost(input: $input) {
    ok
    objects {
      id
      title
      published
    }
    errors
  }
}

mutation BulkDeletePosts($input: BulkDeletePostInput!) {
  bulkDeletePost(input: $input) {
    ok
    deletedIds
    errors
  }
}
```

## 🔧 Schema Assembly

### SchemaBuilder Class

The `SchemaBuilder` combines all generated components into a unified GraphQL schema:

```python
from django_graphql_auto.core.schema import SchemaBuilder

builder = SchemaBuilder()
schema = builder.build_schema()
```

### Schema Structure

The assembled schema includes:

```python
class Query(graphene.ObjectType):
    # Single object queries
    post = graphene.Field(PostType, id=graphene.ID(required=True))
    user = graphene.Field(UserType, id=graphene.ID(required=True))
    
    # List queries
    posts = graphene.List(PostType, filters=PostFilterInput())
    users = graphene.List(UserType, filters=UserFilterInput())
    
    # Paginated queries
    post_pages = graphene.Field(PostConnection, first=graphene.Int())
    user_pages = graphene.Field(UserConnection, first=graphene.Int())

class Mutation(graphene.ObjectType):
    # CRUD mutations
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()
    
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
```

### Live Schema Updates

The schema builder supports live updates without server restart:

```python
# Automatically refresh schema when models change
builder.enable_auto_refresh()

# Manual schema refresh
builder.refresh_schema()

# Validate schema integrity
validation_errors = builder.validate_schema()
```

## ⚙️ Configuration Options

### Global Configuration

```python
# settings.py
DJANGO_GRAPHQL_AUTO = {
    'SCHEMA_OUTPUT_DIR': 'generated_schema/',
    'AUTO_GENERATE_SCHEMA': True,
    'NAMING_CONVENTION': 'snake_case',
    'ENABLE_MUTATIONS': True,
    'ENABLE_SUBSCRIPTIONS': False,
    'PAGINATION_SIZE': 20,
    'MAX_QUERY_DEPTH': 10,
    
    # Model inclusion/exclusion
    'APPS_TO_INCLUDE': [],  # Empty means all apps
    'APPS_TO_EXCLUDE': ['admin', 'auth', 'contenttypes'],
    'MODELS_TO_EXCLUDE': ['LogEntry', 'Session'],
    
    # Feature toggles
    'ENABLE_FILTERS': True,
    'ENABLE_NESTED_OPERATIONS': True,
    'ENABLE_FILE_UPLOADS': True,
    'ENABLE_CUSTOM_SCALARS': True,
    'ENABLE_INHERITANCE': True,
    
    # Mutation configuration
    'MUTATION_SETTINGS': {
        'enable_nested_relations': True,  # Global control over nested relations
        'nested_relations_config': {
            # Per-model control
            'Post': True,     # Enable nested relations for Post model
            'Comment': False, # Disable nested relations for Comment model
            'User': True,     # Enable nested relations for User model
        },
        'nested_field_config': {
            # Per-field control (most granular)
            'Post': {
                'comments': False,      # Disable nested comments in Post mutations
                'related_posts': True,  # Enable nested related_posts
                'tags': True,          # Enable nested tags
            },
            'Comment': {
                'replies': False,      # Disable nested replies in Comment mutations
            }
        }
    }
}
```

### Nested Relations Configuration

The library provides three levels of control over nested relationship fields in mutations:

#### 1. Global Control
```python
DJANGO_GRAPHQL_AUTO = {
    'MUTATION_SETTINGS': {
        'enable_nested_relations': False,  # Disable all nested relations globally
    }
}
```

#### 2. Per-Model Control
```python
DJANGO_GRAPHQL_AUTO = {
    'MUTATION_SETTINGS': {
        'enable_nested_relations': False,  # Global default: disabled
        'nested_relations_config': {
            'Post': True,     # Override: enable nested relations for Post only
            'Comment': True,  # Override: enable nested relations for Comment only
        }
    }
}
```

#### 3. Per-Field Control (Most Granular)
```python
DJANGO_GRAPHQL_AUTO = {
    'MUTATION_SETTINGS': {
        'nested_field_config': {
            'Post': {
                'comments': False,      # Disable nested comments
                'related_posts': True,  # Enable nested related_posts
                'tags': True,          # Enable nested tags
            }
        }
    }
}
```

### Configuration Priority

The configuration follows this priority order (highest to lowest):
1. **Per-field configuration** (`nested_field_config`)
2. **Per-model configuration** (`nested_relations_config`)
3. **Global configuration** (`enable_nested_relations`)
4. **Default behavior** (nested relations enabled)

### Per-Model Configuration

```python
# models.py
class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    class GraphQLMeta:
        # Exclude specific fields
        exclude_fields = ['internal_notes']
        
        # Custom field types
        field_overrides = {
            'content': 'String',  # Override TextField default
        }
        
        # Custom resolvers
        extra_fields = {
            'word_count': 'Int',
            'is_recent': 'Boolean',
        }
        
        # Mutation permissions
        create_permission = 'auth.add_post'
        update_permission = 'auth.change_post'
        delete_permission = 'auth.delete_post'
```

## 🚀 Advanced Features

### Custom Field Converters

```python
# custom_converters.py
from django_graphql_auto.generators.types import FieldConverter

class CustomFieldConverter(FieldConverter):
    def convert_custom_field(self, field, registry=None):
        return graphene.String(description=field.help_text)

# Register converter
DJANGO_GRAPHQL_AUTO = {
    'FIELD_CONVERTERS': {
        'myapp.fields.CustomField': 'myapp.converters.CustomFieldConverter',
    }
}
```

### Schema Hooks

```python
# hooks.py
from django_graphql_auto.core.hooks import SchemaHook

class CustomSchemaHook(SchemaHook):
    def before_type_generation(self, model, introspector):
        """Called before generating GraphQL type for a model."""
        pass
    
    def after_type_generation(self, model, graphql_type):
        """Called after generating GraphQL type for a model."""
        pass
    
    def before_schema_assembly(self, components):
        """Called before assembling final schema."""
        pass
    
    def after_schema_assembly(self, schema):
        """Called after assembling final schema."""
        pass

# Register hook
DJANGO_GRAPHQL_AUTO = {
    'SCHEMA_HOOKS': [
        'myapp.hooks.CustomSchemaHook',
    ]
}
```

### Performance Optimization

The schema generator includes several performance optimizations:

- **Lazy Loading**: Types are generated only when needed
- **Caching**: Introspection results are cached to avoid repeated analysis
- **Selective Updates**: Only affected parts of the schema are regenerated
- **Query Optimization**: Automatic select_related and prefetch_related hints

## 🔍 Debugging and Introspection

### Debug Mode

Enable debug mode for detailed information:

```python
DJANGO_GRAPHQL_AUTO = {
    'DEBUG_MODE': True,
    'VERBOSE_ERRORS': True,
}
```

### Schema Introspection

```python
from django_graphql_auto.core.schema import get_schema_info

# Get detailed schema information
schema_info = get_schema_info()
print(f"Generated {schema_info.type_count} types")
print(f"Generated {schema_info.query_count} queries")
print(f"Generated {schema_info.mutation_count} mutations")
```

### Management Commands

```bash
# Generate schema files
python manage.py generate_graphql_schema

# Validate schema
python manage.py validate_graphql_schema

# Show schema statistics
python manage.py graphql_schema_info

# Export schema SDL
python manage.py export_graphql_schema --format sdl
```

## 🚀 Next Steps

Now that you understand schema generation:

1. [Learn About Filtering](filtering.md) - Advanced filtering capabilities
2. [Explore Mutations](mutations.md) - CRUD operations and custom mutations
3. [Check Advanced Features](../advanced/custom-scalars.md) - Custom scalars and complex types
4. [Review API Reference](../api/core-classes.md) - Detailed API documentation

## 🤝 Need Help?

- Check the [Troubleshooting Guide](../development/troubleshooting.md)
- Review [Configuration Examples](../setup/configuration.md)
- Join our [Community Discussions](https://github.com/your-repo/django-graphql-auto/discussions)