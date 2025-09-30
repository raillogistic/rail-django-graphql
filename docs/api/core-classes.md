# Core Classes API Reference

This document provides detailed API reference for the core classes in the Django GraphQL Auto-Generation Library.

## 📚 Table of Contents

- [ModelIntrospector](#modelintrospector)
- [TypeGenerator](#typegenerator)
- [QueryGenerator](#querygenerator)
- [MutationGenerator](#mutationgenerator)
- [FilterGenerator](#filtergenerator)
- [SchemaBuilder](#schemabuilder)
- [Configuration Classes](#configuration-classes)
- [Utility Classes](#utility-classes)

## 🔍 ModelIntrospector

The `ModelIntrospector` class analyzes Django models and extracts metadata for GraphQL schema generation.

### Class Definition

```python
from rail_django_graphql.generators.introspector import ModelIntrospector

class ModelIntrospector:
    """
    Analyzes Django models and extracts comprehensive metadata
    for GraphQL schema generation.
    """
```

### Constructor

```python
def __init__(self, config: Optional[Config] = None):
    """
    Initialize the ModelIntrospector.

    Args:
        config: Optional configuration object
    """
```

### Methods

#### get_model_fields()

```python
def get_model_fields(self, model: Type[Model]) -> Dict[str, FieldInfo]:
    """
    Extract field information from a Django model.

    Args:
        model: Django model class

    Returns:
        Dictionary mapping field names to FieldInfo objects

    Example:
        >>> introspector = ModelIntrospector()
        >>> fields = introspector.get_model_fields(Post)
        >>> print(fields['title'].field_type)
        <class 'django.db.models.fields.CharField'>
    """
```

#### get_model_relationships()

```python
def get_model_relationships(self, model: Type[Model]) -> Dict[str, RelationshipInfo]:
    """
    Extract relationship information from a Django model.

    Args:
        model: Django model class

    Returns:
        Dictionary mapping relationship names to RelationshipInfo objects

    Example:
        >>> relationships = introspector.get_model_relationships(Post)
        >>> print(relationships['author'].relationship_type)
        'foreign_key'
    """
```

#### get_model_methods()

```python
def get_model_methods(self, model: Type[Model]) -> Dict[str, MethodInfo]:
    """
    Extract method and property information from a Django model.

    Args:
        model: Django model class

    Returns:
        Dictionary mapping method names to MethodInfo objects

    Example:
        >>> methods = introspector.get_model_methods(Post)
        >>> print(methods['get_absolute_url'].return_type)
        <class 'str'>
    """
```

#### analyze_model()

```python
def analyze_model(self, model: Type[Model]) -> ModelAnalysis:
    """
    Perform comprehensive analysis of a Django model.

    Args:
        model: Django model class

    Returns:
        ModelAnalysis object containing all extracted information

    Example:
        >>> analysis = introspector.analyze_model(Post)
        >>> print(analysis.model_name)
        'Post'
        >>> print(len(analysis.fields))
        5
    """
```

### Data Classes

#### FieldInfo

```python
@dataclass
class FieldInfo:
    """Information about a Django model field."""

    name: str
    field_type: Type[Field]
    graphql_type: Optional[Type[Scalar]]
    is_required: bool
    is_list: bool
    max_length: Optional[int]
    choices: Optional[List[Tuple]]
    default: Any
    help_text: str
    null: bool
    blank: bool
    unique: bool
    db_index: bool

    # Enhanced attributes
    has_auto_now: bool
    has_auto_now_add: bool
    has_default: bool
    is_primary_key: bool
    is_foreign_key: bool
    is_many_to_many: bool

    # Validation attributes
    validators: List[Callable]
    min_value: Optional[Union[int, float]]
    max_value: Optional[Union[int, float]]
    min_length: Optional[int]
    max_length: Optional[int]
```

#### RelationshipInfo

```python
@dataclass
class RelationshipInfo:
    """Information about a Django model relationship."""

    name: str
    relationship_type: str  # 'foreign_key', 'many_to_many', 'one_to_one'
    related_model: Type[Model]
    related_name: Optional[str]
    on_delete: Optional[str]
    through_model: Optional[Type[Model]]
    symmetrical: bool

    # Reverse relationship info
    is_reverse: bool
    accessor_name: Optional[str]

    # Many-to-many specific
    through_fields: Optional[Tuple[str, str]]
    db_table: Optional[str]
```

#### MethodInfo

```python
@dataclass
class MethodInfo:
    """Information about a Django model method or property."""

    name: str
    return_type: Type
    is_property: bool
    is_cached_property: bool
    parameters: List[Parameter]
    docstring: Optional[str]

    # GraphQL specific
    graphql_type: Optional[Type[Scalar]]
    is_resolver_method: bool
    requires_info: bool
    requires_context: bool
```

#### ModelAnalysis

```python
@dataclass
class ModelAnalysis:
    """Complete analysis of a Django model."""

    model: Type[Model]
    model_name: str
    app_label: str
    table_name: str

    fields: Dict[str, FieldInfo]
    relationships: Dict[str, RelationshipInfo]
    methods: Dict[str, MethodInfo]

    # Inheritance information
    is_abstract: bool
    parent_models: List[Type[Model]]
    child_models: List[Type[Model]]
    mixin_classes: List[Type]

    # Meta information
    meta_options: Dict[str, Any]
    permissions: List[Tuple[str, str]]
    ordering: List[str]
    unique_together: List[Tuple[str, ...]]
    indexes: List[Any]
```

## 🏗️ TypeGenerator

The `TypeGenerator` creates GraphQL types from Django models.

### Class Definition

```python
from rail_django_graphql.generators.types import TypeGenerator

class TypeGenerator:
    """
    Generates GraphQL types from Django models with intelligent
    field mapping and requirement detection.
    """
```

### Constructor

```python
def __init__(self, introspector: ModelIntrospector, config: Optional[Config] = None):
    """
    Initialize the TypeGenerator.

    Args:
        introspector: ModelIntrospector instance
        config: Optional configuration object
    """
```

### Methods

#### generate_object_type()

```python
def generate_object_type(self, model: Type[Model]) -> Type[DjangoObjectType]:
    """
    Generate a GraphQL ObjectType from a Django model.

    Args:
        model: Django model class

    Returns:
        Generated GraphQL ObjectType class

    Example:
        >>> generator = TypeGenerator(introspector)
        >>> PostType = generator.generate_object_type(Post)
        >>> print(PostType._meta.model)
        <class 'myapp.models.Post'>
    """
```

#### generate_input_type()

```python
def generate_input_type(
    self,
    model: Type[Model],
    mutation_type: str = 'create',
    exclude_fields: Optional[List[str]] = None
) -> Type[graphene.InputObjectType]:
    """
    Generate a GraphQL InputObjectType from a Django model.

    Args:
        model: Django model class
        mutation_type: Type of mutation ('create', 'update', 'delete')
        exclude_fields: Fields to exclude from input type

    Returns:
        Generated GraphQL InputObjectType class

    Example:
        >>> CreatePostInput = generator.generate_input_type(Post, 'create')
        >>> UpdatePostInput = generator.generate_input_type(Post, 'update')
    """
```

#### generate_connection_type()

```python
def generate_connection_type(self, model: Type[Model]) -> Type[Connection]:
    """
    Generate a GraphQL Connection type for pagination.

    Args:
        model: Django model class

    Returns:
        Generated Connection type class

    Example:
        >>> PostConnection = generator.generate_connection_type(Post)
        >>> # Used for paginated queries
    """
```

#### generate_enum_type()

```python
def generate_enum_type(self, field: Field) -> Optional[Type[graphene.Enum]]:
    """
    Generate a GraphQL Enum type from a Django field with choices.

    Args:
        field: Django field with choices

    Returns:
        Generated Enum type class or None

    Example:
        >>> # For a field with choices
        >>> STATUS_CHOICES = [('draft', 'Draft'), ('published', 'Published')]
        >>> status = models.CharField(max_length=20, choices=STATUS_CHOICES)
        >>> StatusEnum = generator.generate_enum_type(status)
    """
```

### Field Conversion Methods

#### convert_field()

```python
def convert_field(self, field_info: FieldInfo) -> graphene.Field:
    """
    Convert a Django field to a GraphQL field.

    Args:
        field_info: FieldInfo object

    Returns:
        GraphQL field
    """
```

#### get_graphql_type_for_field()

```python
def get_graphql_type_for_field(self, field_info: FieldInfo) -> Type[Scalar]:
    """
    Get the appropriate GraphQL scalar type for a Django field.

    Args:
        field_info: FieldInfo object

    Returns:
        GraphQL scalar type
    """
```

## 🔍 QueryGenerator

The `QueryGenerator` creates GraphQL query operations.

### Class Definition

```python
from rail_django_graphql.generators.queries import QueryGenerator

class QueryGenerator:
    """
    Generates comprehensive GraphQL query operations for Django models.
    """
```

### Constructor

```python
def __init__(
    self,
    type_generator: TypeGenerator,
    filter_generator: FilterGenerator,
    config: Optional[Config] = None
):
    """
    Initialize the QueryGenerator.

    Args:
        type_generator: TypeGenerator instance
        filter_generator: FilterGenerator instance
        config: Optional configuration object
    """
```

### Methods

#### generate_single_query()

```python
def generate_single_query(self, model: Type[Model]) -> graphene.Field:
    """
    Generate a single object query field.

    Args:
        model: Django model class

    Returns:
        GraphQL field for single object queries

    Example:
        >>> post_field = generator.generate_single_query(Post)
        >>> # Generates: post(id: ID!): PostType
    """
```

#### generate_list_query()

```python
def generate_list_query(self, model: Type[Model]) -> graphene.Field:
    """
    Generate a list query field with filtering and ordering.

    Args:
        model: Django model class

    Returns:
        GraphQL field for list queries

    Example:
        >>> posts_field = generator.generate_list_query(Post)
        >>> # Generates: posts(filters: PostFilterInput, orderBy: [String]): [PostType]
    """
```

#### generate_paginated_query()

```python
def generate_paginated_query(self, model: Type[Model]) -> graphene.Field:
    """
    Generate a paginated query field using Relay-style connections.

    Args:
        model: Django model class

    Returns:
        GraphQL field for paginated queries

    Example:
        >>> post_pages_field = generator.generate_paginated_query(Post)
        >>> # Generates: postPages(first: Int, after: String): PostConnection
    """
```

#### create_resolver()

```python
def create_resolver(
    self,
    model: Type[Model],
    query_type: str
) -> Callable:
    """
    Create a resolver function for a query.

    Args:
        model: Django model class
        query_type: Type of query ('single', 'list', 'paginated')

    Returns:
        Resolver function
    """
```

## ✏️ MutationGenerator

The `MutationGenerator` creates GraphQL mutation operations.

### Class Definition

```python
from rail_django_graphql.generators.mutations import MutationGenerator

class MutationGenerator:
    """
    Generates CRUD mutations with standardized return types and error handling.
    """
```

### Constructor

```python
def __init__(
    self,
    type_generator: TypeGenerator,
    config: Optional[Config] = None
):
    """
    Initialize the MutationGenerator.

    Args:
        type_generator: TypeGenerator instance
        config: Optional configuration object
    """
```

### Methods

#### generate_create_mutation()

```python
def generate_create_mutation(self, model: Type[Model]) -> Type[graphene.Mutation]:
    """
    Generate a create mutation for a Django model.

    Args:
        model: Django model class

    Returns:
        GraphQL Mutation class

    Example:
        >>> CreatePost = generator.generate_create_mutation(Post)
        >>> # Generates: createPost(input: CreatePostInput!): PostMutationResult!
    """
```

#### generate_update_mutation()

```python
def generate_update_mutation(self, model: Type[Model]) -> Type[graphene.Mutation]:
    """
    Generate an update mutation for a Django model.

    Args:
        model: Django model class

    Returns:
        GraphQL Mutation class

    Example:
        >>> UpdatePost = generator.generate_update_mutation(Post)
        >>> # Generates: updatePost(id: ID!, input: UpdatePostInput!): PostMutationResult!
    """
```

#### generate_delete_mutation()

```python
def generate_delete_mutation(self, model: Type[Model]) -> Type[graphene.Mutation]:
    """
    Generate a delete mutation for a Django model.

    Args:
        model: Django model class

    Returns:
        GraphQL Mutation class

    Example:
        >>> DeletePost = generator.generate_delete_mutation(Post)
        >>> # Generates: deletePost(id: ID!): PostMutationResult!
    """
```

#### generate_mutation_result_type()

```python
def generate_mutation_result_type(self, model: Type[Model]) -> Type[graphene.ObjectType]:
    """
    Generate a standardized mutation result type.

    Args:
        model: Django model class

    Returns:
        GraphQL ObjectType for mutation results

    Example:
        >>> PostMutationResult = generator.generate_mutation_result_type(Post)
        >>> # Contains: ok, post, errors fields
    """
```

### Mutation Result Structure

```python
class MutationResult(graphene.ObjectType):
    """Base class for all mutation results."""

    ok = graphene.Boolean(required=True, description="Success status")
    errors = graphene.List(
        graphene.String,
        required=True,
        description="List of error messages"
    )

class PostMutationResult(MutationResult):
    """Result type for Post mutations."""

    post = graphene.Field(PostType, description="The affected post object")
```

## 🔧 FilterGenerator

The `FilterGenerator` creates comprehensive filtering capabilities.

### Class Definition

```python
from rail_django_graphql.generators.filters import FilterGenerator

class FilterGenerator:
    """
    Generates comprehensive filter inputs and logic for GraphQL queries.
    """
```

### Constructor

```python
def __init__(
    self,
    introspector: ModelIntrospector,
    config: Optional[Config] = None
):
    """
    Initialize the FilterGenerator.

    Args:
        introspector: ModelIntrospector instance
        config: Optional configuration object
    """
```

### Methods

#### generate_filter_input()

```python
def generate_filter_input(self, model: Type[Model]) -> Type[graphene.InputObjectType]:
    """
    Generate a comprehensive filter input type for a model.

    Args:
        model: Django model class

    Returns:
        GraphQL InputObjectType for filtering

    Example:
        >>> PostFilterInput = generator.generate_filter_input(Post)
        >>> # Contains all field filters, relationship filters, and logical operators
    """
```

#### generate_field_filters()

```python
def generate_field_filters(self, field_info: FieldInfo) -> Dict[str, graphene.InputField]:
    """
    Generate filter fields for a specific model field.

    Args:
        field_info: FieldInfo object

    Returns:
        Dictionary of filter field names to InputField objects
    """
```

#### create_filter_resolver()

```python
def create_filter_resolver(self, model: Type[Model]) -> Callable:
    """
    Create a resolver function that applies filters to a queryset.

    Args:
        model: Django model class

    Returns:
        Filter resolver function
    """
```

## 🏗️ SchemaBuilder

The `SchemaBuilder` assembles all components into a unified GraphQL schema.

### Class Definition

```python
from rail_django_graphql.core.schema import SchemaBuilder

class SchemaBuilder:
    """
    Assembles all generated components into a unified GraphQL schema.
    """
```

### Constructor

```python
def __init__(self, config: Optional[Config] = None):
    """
    Initialize the SchemaBuilder.

    Args:
        config: Optional configuration object
    """
```

### Methods

#### build_schema()

```python
def build_schema(self, models: Optional[List[Type[Model]]] = None) -> graphene.Schema:
    """
    Build a complete GraphQL schema from Django models.

    Args:
        models: Optional list of models to include. If None, includes all models.

    Returns:
        Complete GraphQL schema

    Example:
        >>> builder = SchemaBuilder()
        >>> schema = builder.build_schema()
        >>> # Complete schema with all queries and mutations
    """
```

#### discover_models()

```python
def discover_models(self) -> List[Type[Model]]:
    """
    Discover all Django models in the project.

    Returns:
        List of Django model classes
    """
```

#### generate_query_class()

```python
def generate_query_class(self, models: List[Type[Model]]) -> Type[graphene.ObjectType]:
    """
    Generate the root Query class.

    Args:
        models: List of Django model classes

    Returns:
        GraphQL ObjectType class for queries
    """
```

#### generate_mutation_class()

```python
def generate_mutation_class(self, models: List[Type[Model]]) -> Type[graphene.ObjectType]:
    """
    Generate the root Mutation class.

    Args:
        models: List of Django model classes

    Returns:
        GraphQL ObjectType class for mutations
    """
```

#### validate_schema()

```python
def validate_schema(self, schema: graphene.Schema) -> List[str]:
    """
    Validate the generated schema for common issues.

    Args:
        schema: GraphQL schema to validate

    Returns:
        List of validation error messages
    """
```

## ⚙️ Configuration Classes

### Config

```python
from rail_django_graphql.core.config import Config

@dataclass
class Config:
    """Main configuration class for the library."""

    # Schema generation
    auto_generate_schema: bool = True
    schema_output_dir: str = 'generated_schema/'
    naming_convention: str = 'snake_case'

    # Feature toggles
    enable_mutations: bool = True
    enable_subscriptions: bool = False
    enable_filters: bool = True
    enable_nested_operations: bool = True
    enable_file_uploads: bool = True
    enable_custom_scalars: bool = True
    enable_inheritance: bool = True

    # Model inclusion/exclusion
    apps_to_include: List[str] = field(default_factory=list)
    apps_to_exclude: List[str] = field(default_factory=lambda: ['admin', 'auth', 'contenttypes'])
    models_to_exclude: List[str] = field(default_factory=list)

    # Pagination
    pagination_size: int = 20
    max_query_depth: int = 10

    # Performance
    enable_query_optimization: bool = True
    enable_caching: bool = False
    cache_timeout: int = 300

    # Security
    enable_permissions: bool = False
    enable_rate_limiting: bool = False
    rate_limit_per_minute: int = 100

    # Custom components
    custom_scalars: Dict[str, str] = field(default_factory=dict)
    custom_filters: Dict[str, str] = field(default_factory=dict)
    field_converters: Dict[str, str] = field(default_factory=dict)
    schema_hooks: List[str] = field(default_factory=list)
```

### FilterConfig

```python
@dataclass
class FilterConfig:
    """Configuration for filtering system."""

    enable_filters: bool = True
    enable_logical_operators: bool = True
    enable_relationship_filters: bool = True
    max_filter_depth: int = 3
    enable_custom_filters: bool = True

    default_operators: Dict[str, List[str]] = field(default_factory=lambda: {
        'CharField': ['exact', 'icontains', 'startswith', 'endswith'],
        'IntegerField': ['exact', 'gt', 'gte', 'lt', 'lte', 'range'],
        'BooleanField': ['exact'],
        'DateTimeField': ['exact', 'gt', 'gte', 'lt', 'lte', 'range', 'date'],
    })
```

## 🛠️ Utility Classes

### FieldConverter

```python
from rail_django_graphql.utils.converters import FieldConverter

class FieldConverter:
    """Converts Django fields to GraphQL types."""

    @classmethod
    def convert_field(cls, field: Field) -> Type[Scalar]:
        """Convert a Django field to GraphQL scalar type."""
        pass

    @classmethod
    def register_converter(cls, field_type: Type[Field], converter: Callable):
        """Register a custom field converter."""
        pass
```

### NamingConvention

```python
from rail_django_graphql.utils.naming import NamingConvention

class NamingConvention:
    """Handles naming conventions for GraphQL schema elements."""

    @staticmethod
    def to_graphql_name(django_name: str, convention: str = 'snake_case') -> str:
        """Convert Django name to GraphQL naming convention."""
        pass

    @staticmethod
    def to_mutation_name(model_name: str, operation: str) -> str:
        """Generate mutation name from model and operation."""
        pass
```

### ValidationHelper

```python
from rail_django_graphql.utils.validation import ValidationHelper

class ValidationHelper:
    """Provides validation utilities for GraphQL operations."""

    @staticmethod
    def validate_input(input_data: Dict, model: Type[Model]) -> List[str]:
        """Validate input data against model constraints."""
        pass

    @staticmethod
    def validate_permissions(user, model: Type[Model], operation: str) -> bool:
        """Validate user permissions for model operations."""
        pass
```

## 🔍 Usage Examples

### Basic Usage

```python
from rail_django_graphql.core.schema import SchemaBuilder
from rail_django_graphql.generators.introspector import ModelIntrospector
from rail_django_graphql.generators.types import TypeGenerator

# Initialize components
introspector = ModelIntrospector()
type_generator = TypeGenerator(introspector)
schema_builder = SchemaBuilder()

# Generate schema
schema = schema_builder.build_schema()

# Use with Graphene-Django
from graphene_django.views import GraphQLView
from django.urls import path

urlpatterns = [
    path('graphql/', GraphQLView.as_view(schema=schema)),
]
```

### Advanced Usage

```python
from rail_django_graphql.core.config import Config
from myapp.models import Post, User, Category

# Custom configuration
config = Config(
    enable_mutations=True,
    enable_filters=True,
    pagination_size=50,
    apps_to_include=['myapp'],
    custom_scalars={
        'JSONField': 'graphene.JSONString',
    }
)

# Build schema with specific models
builder = SchemaBuilder(config)
schema = builder.build_schema([Post, User, Category])

# Validate schema
errors = builder.validate_schema(schema)
if errors:
    print("Schema validation errors:", errors)
```

## 🚀 Next Steps

Now that you understand the core classes:

1. [Learn About Configuration](../setup/configuration.md) - Detailed configuration options
2. [Explore Advanced Features](../advanced/custom-scalars.md) - Custom scalars and complex types
3. [Check Examples](../examples/advanced-examples.md) - Real-world usage examples
4. [Review Performance Guide](../development/performance.md) - Optimization techniques

## 🤝 Need Help?

- Check the [Troubleshooting Guide](../development/troubleshooting.md)
- Review [Configuration Examples](../setup/configuration.md)
- Join our [Community Discussions](https://github.com/your-repo/django-graphql-auto/discussions)
