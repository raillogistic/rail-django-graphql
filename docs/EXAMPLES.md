# Examples

This document provides comprehensive examples for using the Django GraphQL Multi-Schema System.

## Table of Contents

- [Basic Usage](#basic-usage)
- [Schema Registration](#schema-registration)
- [Multi-Schema Setup](#multi-schema-setup)
- [Plugin Development](#plugin-development)
- [Discovery Hooks](#discovery-hooks)
- [REST API Usage](#rest-api-usage)
- [Advanced Patterns](#advanced-patterns)
- [Real-World Examples](#real-world-examples)

## Basic Usage

### Simple Schema Registration

```python
# myapp/schema.py
import graphene
from rail_django_graphql.decorators import register_schema
from .models import User

class UserType(graphene.ObjectType):
    id = graphene.ID()
    username = graphene.String()
    email = graphene.String()

class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    user = graphene.Field(UserType, id=graphene.ID(required=True))

    def resolve_users(self, info):
        return User.objects.all()

    def resolve_user(self, info, id):
        return User.objects.get(pk=id)

# Register the schema using decorator
@register_schema(
    name='user_schema',
    description='User management GraphQL schema',
    version='1.0.0',
    apps=['myapp']
)
def create_user_schema():
    return graphene.Schema(query=Query)
```

### Manual Schema Registration

```python
# myapp/apps.py
from django.apps import AppConfig
from rail_django_graphql.core.registry import schema_registry

class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        from .schema import create_user_schema
        
        schema_registry.register_schema(
            name='user_schema',
            description='User management schema',
            version='1.0.0',
            apps=['myapp'],
            builder=create_user_schema,
            auto_discover=True,
            enabled=True
        )
```

## Schema Registration

### Using Class-Based Registration

```python
# myapp/schema.py
import graphene
from rail_django_graphql.decorators import register_schema
from .models import Product, Category

class ProductType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    price = graphene.Decimal()
    category = graphene.Field('CategoryType')

class CategoryType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    products = graphene.List(ProductType)

class Query(graphene.ObjectType):
    products = graphene.List(ProductType)
    categories = graphene.List(CategoryType)
    product = graphene.Field(ProductType, id=graphene.ID(required=True))

    def resolve_products(self, info):
        return Product.objects.select_related('category').all()

    def resolve_categories(self, info):
        return Category.objects.prefetch_related('products').all()

    def resolve_product(self, info, id):
        return Product.objects.select_related('category').get(pk=id)

@register_schema(
    name='product_schema',
    description='Product catalog GraphQL schema',
    version='2.0.0',
    apps=['products'],
    models=['Product', 'Category']
)
class ProductSchemaProvider:
    """Schema provider for product management."""
    
    def get_schema(self):
        return graphene.Schema(query=Query)
    
    def get_description(self):
        return "Comprehensive product catalog with categories"
    
    def validate_configuration(self):
        """Custom validation for schema configuration."""
        # Check if required models exist
        from django.apps import apps
        try:
            apps.get_model('products', 'Product')
            apps.get_model('products', 'Category')
            return True
        except LookupError:
            return False
```

### Dynamic Schema Building

```python
# myapp/schema_builder.py
import graphene
from django.apps import apps
from rail_django_graphql.core.registry import schema_registry

def build_dynamic_schema(app_name):
    """Build a GraphQL schema dynamically for any Django app."""
    
    app_config = apps.get_app_config(app_name)
    models = app_config.get_models()
    
    # Create types dynamically
    types = {}
    for model in models:
        type_name = f"{model.__name__}Type"
        fields = {}
        
        for field in model._meta.fields:
            if field.name == 'id':
                fields[field.name] = graphene.ID()
            elif isinstance(field, models.CharField):
                fields[field.name] = graphene.String()
            elif isinstance(field, models.IntegerField):
                fields[field.name] = graphene.Int()
            # Add more field type mappings as needed
        
        types[type_name] = type(type_name, (graphene.ObjectType,), fields)
    
    # Create query class
    query_fields = {}
    for model in models:
        model_name = model.__name__.lower()
        type_name = f"{model.__name__}Type"
        
        # List field
        query_fields[f"{model_name}s"] = graphene.List(types[type_name])
        
        # Single item field
        query_fields[model_name] = graphene.Field(
            types[type_name], 
            id=graphene.ID(required=True)
        )
        
        # Add resolvers
        def make_list_resolver(model_class):
            def resolver(self, info):
                return model_class.objects.all()
            return resolver
        
        def make_single_resolver(model_class):
            def resolver(self, info, id):
                return model_class.objects.get(pk=id)
            return resolver
        
        query_fields[f"resolve_{model_name}s"] = make_list_resolver(model)
        query_fields[f"resolve_{model_name}"] = make_single_resolver(model)
    
    Query = type('Query', (graphene.ObjectType,), query_fields)
    
    return graphene.Schema(query=Query)

# Register dynamic schemas for multiple apps
for app_name in ['users', 'products', 'orders']:
    schema_registry.register_schema(
        name=f'{app_name}_auto_schema',
        description=f'Auto-generated schema for {app_name}',
        version='1.0.0',
        apps=[app_name],
        builder=lambda: build_dynamic_schema(app_name),
        auto_discover=False
    )
```

## Multi-Schema Setup

### E-commerce Multi-Schema Example

```python
# ecommerce/schemas/__init__.py
from .user_schema import UserSchema
from .product_schema import ProductSchema
from .order_schema import OrderSchema
from .admin_schema import AdminSchema

__all__ = ['UserSchema', 'ProductSchema', 'OrderSchema', 'AdminSchema']
```

```python
# ecommerce/schemas/user_schema.py
import graphene
from django.contrib.auth import get_user_model
from rail_django_graphql.decorators import register_schema

User = get_user_model()

class UserType(graphene.ObjectType):
    id = graphene.ID()
    username = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    is_active = graphene.Boolean()
    date_joined = graphene.DateTime()

class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String()
        last_name = graphene.String()

    user = graphene.Field(UserType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, username, email, password, **kwargs):
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                **kwargs
            )
            return CreateUser(user=user, success=True, errors=[])
        except Exception as e:
            return CreateUser(user=None, success=False, errors=[str(e)])

class Query(graphene.ObjectType):
    me = graphene.Field(UserType)
    users = graphene.List(UserType)

    def resolve_me(self, info):
        if info.context.user.is_authenticated:
            return info.context.user
        return None

    def resolve_users(self, info):
        if info.context.user.is_staff:
            return User.objects.all()
        return []

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()

@register_schema(
    name='user_schema',
    description='User management and authentication',
    version='1.0.0',
    apps=['users', 'auth'],
    models=['User']
)
def create_user_schema():
    return graphene.Schema(query=Query, mutation=Mutation)
```

```python
# ecommerce/schemas/product_schema.py
import graphene
from decimal import Decimal
from rail_django_graphql.decorators import register_schema
from ..models import Product, Category, Review

class CategoryType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    products = graphene.List('ProductType')

    def resolve_products(self, info):
        return self.products.filter(is_active=True)

class ReviewType(graphene.ObjectType):
    id = graphene.ID()
    rating = graphene.Int()
    comment = graphene.String()
    user = graphene.Field('UserType')
    created_at = graphene.DateTime()

class ProductType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    price = graphene.Decimal()
    category = graphene.Field(CategoryType)
    reviews = graphene.List(ReviewType)
    average_rating = graphene.Float()
    is_active = graphene.Boolean()

    def resolve_reviews(self, info):
        return self.reviews.select_related('user').all()

    def resolve_average_rating(self, info):
        reviews = self.reviews.all()
        if reviews:
            return sum(r.rating for r in reviews) / len(reviews)
        return 0.0

class ProductFilter(graphene.InputObjectType):
    category_id = graphene.ID()
    min_price = graphene.Decimal()
    max_price = graphene.Decimal()
    search = graphene.String()

class Query(graphene.ObjectType):
    products = graphene.List(
        ProductType,
        filters=ProductFilter(),
        limit=graphene.Int(default_value=20),
        offset=graphene.Int(default_value=0)
    )
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    categories = graphene.List(CategoryType)
    featured_products = graphene.List(ProductType, limit=graphene.Int(default_value=10))

    def resolve_products(self, info, filters=None, limit=20, offset=0):
        queryset = Product.objects.filter(is_active=True).select_related('category')
        
        if filters:
            if filters.get('category_id'):
                queryset = queryset.filter(category_id=filters['category_id'])
            if filters.get('min_price'):
                queryset = queryset.filter(price__gte=filters['min_price'])
            if filters.get('max_price'):
                queryset = queryset.filter(price__lte=filters['max_price'])
            if filters.get('search'):
                queryset = queryset.filter(
                    name__icontains=filters['search']
                ) | queryset.filter(
                    description__icontains=filters['search']
                )
        
        return queryset[offset:offset + limit]

    def resolve_product(self, info, id):
        return Product.objects.select_related('category').get(pk=id, is_active=True)

    def resolve_categories(self, info):
        return Category.objects.filter(is_active=True)

    def resolve_featured_products(self, info, limit=10):
        return Product.objects.filter(
            is_active=True, 
            is_featured=True
        ).select_related('category')[:limit]

@register_schema(
    name='product_schema',
    description='Product catalog and reviews',
    version='2.1.0',
    apps=['products'],
    models=['Product', 'Category', 'Review'],
    settings={
        'enable_caching': True,
        'cache_timeout': 300,
        'enable_filtering': True
    }
)
def create_product_schema():
    return graphene.Schema(query=Query)
```

```python
# ecommerce/schemas/order_schema.py
import graphene
from django.contrib.auth import get_user_model
from rail_django_graphql.decorators import register_schema
from ..models import Order, OrderItem, Product

User = get_user_model()

class OrderItemType(graphene.ObjectType):
    id = graphene.ID()
    product = graphene.Field('ProductType')
    quantity = graphene.Int()
    price = graphene.Decimal()
    total = graphene.Decimal()

    def resolve_total(self, info):
        return self.quantity * self.price

class OrderType(graphene.ObjectType):
    id = graphene.ID()
    user = graphene.Field('UserType')
    items = graphene.List(OrderItemType)
    status = graphene.String()
    total_amount = graphene.Decimal()
    created_at = graphene.DateTime()
    updated_at = graphene.DateTime()

    def resolve_items(self, info):
        return self.items.select_related('product').all()

    def resolve_total_amount(self, info):
        return sum(item.quantity * item.price for item in self.items.all())

class CreateOrder(graphene.Mutation):
    class Arguments:
        items = graphene.List(graphene.NonNull(graphene.InputObjectType(
            'OrderItemInput',
            (
                ('product_id', graphene.ID(required=True)),
                ('quantity', graphene.Int(required=True)),
            )
        )), required=True)

    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, items):
        if not info.context.user.is_authenticated:
            return CreateOrder(
                order=None, 
                success=False, 
                errors=['Authentication required']
            )

        try:
            order = Order.objects.create(
                user=info.context.user,
                status='pending'
            )

            for item_data in items:
                product = Product.objects.get(pk=item_data['product_id'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item_data['quantity'],
                    price=product.price
                )

            return CreateOrder(order=order, success=True, errors=[])
        except Exception as e:
            return CreateOrder(order=None, success=False, errors=[str(e)])

class Query(graphene.ObjectType):
    my_orders = graphene.List(OrderType)
    order = graphene.Field(OrderType, id=graphene.ID(required=True))
    all_orders = graphene.List(OrderType)  # Admin only

    def resolve_my_orders(self, info):
        if info.context.user.is_authenticated:
            return Order.objects.filter(
                user=info.context.user
            ).prefetch_related('items__product')
        return []

    def resolve_order(self, info, id):
        if info.context.user.is_authenticated:
            return Order.objects.filter(
                id=id,
                user=info.context.user
            ).prefetch_related('items__product').first()
        return None

    def resolve_all_orders(self, info):
        if info.context.user.is_staff:
            return Order.objects.all().prefetch_related('items__product')
        return []

class Mutation(graphene.ObjectType):
    create_order = CreateOrder.Field()

@register_schema(
    name='order_schema',
    description='Order management and processing',
    version='1.5.0',
    apps=['orders'],
    models=['Order', 'OrderItem'],
    settings={
        'require_authentication': True,
        'enable_subscriptions': True
    }
)
def create_order_schema():
    return graphene.Schema(query=Query, mutation=Mutation)
```

## Plugin Development

### Custom Validation Plugin

```python
# myapp/plugins/validation_plugin.py
from rail_django_graphql.plugins.base import BasePlugin
from rail_django_graphql.core.registry import SchemaInfo
import logging

logger = logging.getLogger(__name__)

class SchemaValidationPlugin(BasePlugin):
    """Plugin for validating schema configurations."""
    
    name = "schema_validation"
    version = "1.0.0"
    
    def __init__(self):
        super().__init__()
        self.validation_rules = {
            'required_fields': ['name', 'description', 'version'],
            'version_pattern': r'^\d+\.\d+\.\d+$',
            'max_description_length': 500
        }
    
    def on_pre_registration(self, schema_name: str, **kwargs) -> dict:
        """Validate schema configuration before registration."""
        logger.info(f"Validating schema configuration for: {schema_name}")
        
        # Check required fields
        for field in self.validation_rules['required_fields']:
            if not kwargs.get(field):
                raise ValueError(f"Required field '{field}' is missing for schema '{schema_name}'")
        
        # Validate version format
        import re
        version = kwargs.get('version', '')
        if not re.match(self.validation_rules['version_pattern'], version):
            raise ValueError(f"Invalid version format '{version}' for schema '{schema_name}'")
        
        # Validate description length
        description = kwargs.get('description', '')
        if len(description) > self.validation_rules['max_description_length']:
            raise ValueError(f"Description too long for schema '{schema_name}'")
        
        # Add validation metadata
        kwargs.setdefault('settings', {})
        kwargs['settings']['validated_by'] = self.name
        kwargs['settings']['validation_timestamp'] = timezone.now().isoformat()
        
        return kwargs
    
    def on_post_registration(self, schema_name: str, schema_info: SchemaInfo) -> None:
        """Log successful registration."""
        logger.info(f"Schema '{schema_name}' successfully registered and validated")
        
        # Optionally perform additional validation on the GraphQL schema
        try:
            graphql_schema = schema_info.get_graphql_schema()
            # Validate schema structure
            if not graphql_schema.query_type:
                logger.warning(f"Schema '{schema_name}' has no query type")
        except Exception as e:
            logger.error(f"Failed to validate GraphQL schema for '{schema_name}': {e}")
    
    def validate_schema(self, schema_info: SchemaInfo) -> bool:
        """Validate schema information."""
        try:
            # Check if schema can be built
            graphql_schema = schema_info.get_graphql_schema()
            
            # Validate schema has required types
            if not graphql_schema.query_type:
                return False
            
            # Check for common issues
            type_map = graphql_schema.type_map
            if len(type_map) < 3:  # At least Query, String, Boolean
                logger.warning(f"Schema '{schema_info.name}' has very few types")
            
            return True
        except Exception as e:
            logger.error(f"Schema validation failed for '{schema_info.name}': {e}")
            return False
```

### Caching Plugin

```python
# myapp/plugins/caching_plugin.py
from rail_django_graphql.plugins.base import BasePlugin
from rail_django_graphql.core.registry import SchemaInfo
from django.core.cache import cache
import hashlib
import json

class SchemaCachingPlugin(BasePlugin):
    """Plugin for caching GraphQL schemas and results."""
    
    name = "schema_caching"
    version = "1.0.0"
    
    def __init__(self):
        super().__init__()
        self.cache_prefix = "graphql_schema_"
        self.default_timeout = 3600  # 1 hour
    
    def on_pre_registration(self, schema_name: str, **kwargs) -> dict:
        """Add caching configuration to schema settings."""
        settings = kwargs.setdefault('settings', {})
        
        # Set default caching options if not specified
        if 'enable_caching' not in settings:
            settings['enable_caching'] = True
        
        if 'cache_timeout' not in settings:
            settings['cache_timeout'] = self.default_timeout
        
        if 'cache_key_prefix' not in settings:
            settings['cache_key_prefix'] = f"{self.cache_prefix}{schema_name}_"
        
        return kwargs
    
    def on_post_registration(self, schema_name: str, schema_info: SchemaInfo) -> None:
        """Cache the schema after registration."""
        if schema_info.settings.get('enable_caching', False):
            self._cache_schema(schema_name, schema_info)
    
    def _cache_schema(self, schema_name: str, schema_info: SchemaInfo) -> None:
        """Cache schema information and GraphQL schema."""
        try:
            cache_key = f"{self.cache_prefix}{schema_name}"
            timeout = schema_info.settings.get('cache_timeout', self.default_timeout)
            
            # Cache schema info
            cache.set(f"{cache_key}_info", schema_info.to_dict(), timeout)
            
            # Cache GraphQL schema string representation
            graphql_schema = schema_info.get_graphql_schema()
            schema_str = str(graphql_schema)
            cache.set(f"{cache_key}_schema", schema_str, timeout)
            
            logger.info(f"Cached schema '{schema_name}' for {timeout} seconds")
        except Exception as e:
            logger.error(f"Failed to cache schema '{schema_name}': {e}")
    
    def get_cached_schema(self, schema_name: str) -> dict:
        """Retrieve cached schema information."""
        cache_key = f"{self.cache_prefix}{schema_name}"
        return cache.get(f"{cache_key}_info")
    
    def invalidate_cache(self, schema_name: str) -> None:
        """Invalidate cached schema data."""
        cache_key = f"{self.cache_prefix}{schema_name}"
        cache.delete(f"{cache_key}_info")
        cache.delete(f"{cache_key}_schema")
        logger.info(f"Invalidated cache for schema '{schema_name}'")
```

### Metrics Collection Plugin

```python
# myapp/plugins/metrics_plugin.py
from rail_django_graphql.plugins.base import BasePlugin
from rail_django_graphql.core.registry import SchemaInfo
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class MetricsCollectionPlugin(BasePlugin):
    """Plugin for collecting schema usage metrics."""
    
    name = "metrics_collection"
    version = "1.0.0"
    
    def __init__(self):
        super().__init__()
        self.metrics = {
            'schema_registrations': 0,
            'schema_discoveries': 0,
            'registration_times': [],
            'schema_usage': {}
        }
    
    def on_pre_registration(self, schema_name: str, **kwargs) -> dict:
        """Record registration start time."""
        kwargs.setdefault('settings', {})
        kwargs['settings']['registration_start'] = timezone.now().isoformat()
        return kwargs
    
    def on_post_registration(self, schema_name: str, schema_info: SchemaInfo) -> None:
        """Record registration metrics."""
        self.metrics['schema_registrations'] += 1
        
        # Calculate registration time
        start_time_str = schema_info.settings.get('registration_start')
        if start_time_str:
            start_time = timezone.datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            registration_time = (timezone.now() - start_time).total_seconds()
            self.metrics['registration_times'].append(registration_time)
        
        # Initialize usage tracking
        self.metrics['schema_usage'][schema_name] = {
            'query_count': 0,
            'mutation_count': 0,
            'error_count': 0,
            'last_used': None
        }
        
        logger.info(f"Recorded metrics for schema '{schema_name}'")
    
    def on_schema_discovery(self, discovered_schemas: list) -> None:
        """Record discovery metrics."""
        self.metrics['schema_discoveries'] += 1
        logger.info(f"Discovered {len(discovered_schemas)} schemas")
    
    def record_query_execution(self, schema_name: str, query_type: str, success: bool) -> None:
        """Record query execution metrics."""
        if schema_name not in self.metrics['schema_usage']:
            self.metrics['schema_usage'][schema_name] = {
                'query_count': 0,
                'mutation_count': 0,
                'error_count': 0,
                'last_used': None
            }
        
        usage = self.metrics['schema_usage'][schema_name]
        
        if query_type == 'query':
            usage['query_count'] += 1
        elif query_type == 'mutation':
            usage['mutation_count'] += 1
        
        if not success:
            usage['error_count'] += 1
        
        usage['last_used'] = timezone.now().isoformat()
    
    def get_metrics(self) -> dict:
        """Get collected metrics."""
        avg_registration_time = 0
        if self.metrics['registration_times']:
            avg_registration_time = sum(self.metrics['registration_times']) / len(self.metrics['registration_times'])
        
        return {
            'total_registrations': self.metrics['schema_registrations'],
            'total_discoveries': self.metrics['schema_discoveries'],
            'average_registration_time': avg_registration_time,
            'schema_usage': self.metrics['schema_usage']
        }
```

## Discovery Hooks

### Custom Discovery Hook

```python
# myapp/hooks/discovery_hooks.py
from rail_django_graphql.plugins.hooks import hook_registry
from django.apps import apps
import logging

logger = logging.getLogger(__name__)

def custom_model_discovery_hook(discovered_schemas: list) -> None:
    """Custom hook to enhance schema discovery with model analysis."""
    logger.info(f"Running custom discovery hook for {len(discovered_schemas)} schemas")
    
    for schema_name in discovered_schemas:
        # Analyze models for this schema
        app_name = schema_name.replace('_schema', '')
        try:
            app_config = apps.get_app_config(app_name)
            models = app_config.get_models()
            
            model_info = []
            for model in models:
                model_info.append({
                    'name': model.__name__,
                    'fields': [f.name for f in model._meta.fields],
                    'relations': [f.name for f in model._meta.fields if f.is_relation]
                })
            
            logger.info(f"Schema '{schema_name}' has {len(models)} models: {[m['name'] for m in model_info]}")
            
        except LookupError:
            logger.warning(f"App '{app_name}' not found for schema '{schema_name}'")

def schema_validation_hook(discovered_schemas: list) -> None:
    """Hook to validate discovered schemas."""
    logger.info("Validating discovered schemas")
    
    valid_schemas = []
    invalid_schemas = []
    
    for schema_name in discovered_schemas:
        # Perform validation logic
        if schema_name.endswith('_schema') and len(schema_name) > 7:
            valid_schemas.append(schema_name)
        else:
            invalid_schemas.append(schema_name)
    
    if invalid_schemas:
        logger.warning(f"Invalid schema names found: {invalid_schemas}")
    
    logger.info(f"Validated {len(valid_schemas)} schemas successfully")

def pre_registration_enhancement_hook(schema_name: str, **kwargs) -> dict:
    """Hook to enhance schema registration with additional metadata."""
    logger.info(f"Enhancing registration for schema: {schema_name}")
    
    # Add automatic tags based on schema name
    settings = kwargs.setdefault('settings', {})
    
    if 'user' in schema_name.lower():
        settings['tags'] = settings.get('tags', []) + ['authentication', 'user-management']
    elif 'product' in schema_name.lower():
        settings['tags'] = settings.get('tags', []) + ['catalog', 'e-commerce']
    elif 'order' in schema_name.lower():
        settings['tags'] = settings.get('tags', []) + ['transactions', 'e-commerce']
    
    # Add automatic versioning if not specified
    if not kwargs.get('version'):
        kwargs['version'] = '1.0.0'
    
    # Add automatic description enhancement
    if kwargs.get('description'):
        kwargs['description'] = f"[Auto-enhanced] {kwargs['description']}"
    
    return kwargs

def post_registration_notification_hook(schema_name: str, schema_info) -> None:
    """Hook to send notifications after schema registration."""
    logger.info(f"Schema '{schema_name}' registered successfully")
    
    # Send notification (example: webhook, email, etc.)
    notification_data = {
        'event': 'schema_registered',
        'schema_name': schema_name,
        'version': schema_info.version,
        'timestamp': schema_info.registered_at.isoformat(),
        'apps': schema_info.apps
    }
    
    # Example: Send to monitoring system
    # send_to_monitoring_system(notification_data)
    
    logger.info(f"Notification sent for schema registration: {schema_name}")

# Register hooks
hook_registry.register_hook('discovery', custom_model_discovery_hook, 'model_analysis')
hook_registry.register_hook('discovery', schema_validation_hook, 'schema_validation')
hook_registry.register_hook('pre_registration', pre_registration_enhancement_hook, 'registration_enhancement')
hook_registry.register_hook('post_registration', post_registration_notification_hook, 'registration_notification')
```

### Hook Usage in Apps

```python
# myapp/apps.py
from django.apps import AppConfig
from rail_django_graphql.plugins.hooks import hook_registry

class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        # Register custom hooks
        from .hooks.discovery_hooks import (
            custom_model_discovery_hook,
            pre_registration_enhancement_hook
        )
        
        hook_registry.register_hook(
            'discovery', 
            custom_model_discovery_hook, 
            'myapp_model_discovery'
        )
        
        hook_registry.register_hook(
            'pre_registration', 
            pre_registration_enhancement_hook, 
            'myapp_registration_enhancement'
        )
```

## REST API Usage

### Python Client Example

```python
# client/graphql_client.py
import requests
import json
from typing import Dict, List, Optional

class GraphQLSchemaClient:
    """Client for interacting with the GraphQL Schema REST API."""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/v1"
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
    
    def list_schemas(self) -> List[Dict]:
        """Get all registered schemas."""
        response = self.session.get(f"{self.api_url}/schemas/")
        response.raise_for_status()
        return response.json()['data']['schemas']
    
    def get_schema(self, schema_name: str) -> Dict:
        """Get specific schema details."""
        response = self.session.get(f"{self.api_url}/schemas/{schema_name}/")
        response.raise_for_status()
        return response.json()['data']
    
    def create_schema(self, schema_data: Dict) -> Dict:
        """Create a new schema."""
        response = self.session.post(
            f"{self.api_url}/schemas/",
            json=schema_data
        )
        response.raise_for_status()
        return response.json()['data']
    
    def update_schema(self, schema_name: str, updates: Dict) -> Dict:
        """Update an existing schema."""
        response = self.session.put(
            f"{self.api_url}/schemas/{schema_name}/",
            json=updates
        )
        response.raise_for_status()
        return response.json()['data']
    
    def delete_schema(self, schema_name: str) -> bool:
        """Delete a schema."""
        response = self.session.delete(f"{self.api_url}/schemas/{schema_name}/")
        response.raise_for_status()
        return response.json()['status'] == 'success'
    
    def enable_schema(self, schema_name: str) -> bool:
        """Enable a schema."""
        return self._management_action('enable', schema_name)
    
    def disable_schema(self, schema_name: str) -> bool:
        """Disable a schema."""
        return self._management_action('disable', schema_name)
    
    def clear_all_schemas(self) -> bool:
        """Clear all schemas."""
        return self._management_action('clear_all')
    
    def _management_action(self, action: str, schema_name: str = None) -> bool:
        """Perform management action."""
        data = {'action': action}
        if schema_name:
            data['schema_name'] = schema_name
        
        response = self.session.post(f"{self.api_url}/management/", json=data)
        response.raise_for_status()
        return response.json()['status'] == 'success'
    
    def trigger_discovery(self) -> Dict:
        """Trigger schema discovery."""
        response = self.session.post(f"{self.api_url}/discovery/")
        response.raise_for_status()
        return response.json()['data']
    
    def get_health(self) -> Dict:
        """Get system health status."""
        response = self.session.get(f"{self.api_url}/health/")
        response.raise_for_status()
        return response.json()['data']
    
    def get_metrics(self) -> Dict:
        """Get system metrics."""
        response = self.session.get(f"{self.api_url}/metrics/")
        response.raise_for_status()
        return response.json()['data']

# Usage example
if __name__ == "__main__":
    client = GraphQLSchemaClient("http://localhost:8000")
    
    # List all schemas
    schemas = client.list_schemas()
    print(f"Found {len(schemas)} schemas:")
    for schema in schemas:
        print(f"  - {schema['name']}: {schema['description']}")
    
    # Create a new schema
    new_schema = {
        'name': 'test_schema',
        'description': 'Test schema created via API',
        'version': '1.0.0',
        'apps': ['testapp'],
        'enabled': True
    }
    
    try:
        created = client.create_schema(new_schema)
        print(f"Created schema: {created['name']}")
        
        # Update the schema
        updates = {'description': 'Updated test schema'}
        updated = client.update_schema('test_schema', updates)
        print(f"Updated schema description: {updated['description']}")
        
        # Get health status
        health = client.get_health()
        print(f"System health: {health['status']}")
        
        # Get metrics
        metrics = client.get_metrics()
        print(f"Total schemas: {metrics['schema_metrics']['total_schemas']}")
        
    except requests.exceptions.HTTPError as e:
        print(f"API error: {e}")
```

### JavaScript Client Example

```javascript
// client/graphql-client.js
class GraphQLSchemaClient {
    constructor(baseUrl, apiKey = null) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.apiUrl = `${this.baseUrl}/api/v1`;
        this.headers = {
            'Content-Type': 'application/json'
        };
        
        if (apiKey) {
            this.headers['Authorization'] = `Bearer ${apiKey}`;
        }
    }
    
    async request(method, endpoint, data = null) {
        const config = {
            method,
            headers: this.headers
        };
        
        if (data) {
            config.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${this.apiUrl}${endpoint}`, config);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return response.json();
    }
    
    async listSchemas() {
        const result = await this.request('GET', '/schemas/');
        return result.data.schemas;
    }
    
    async getSchema(schemaName) {
        const result = await this.request('GET', `/schemas/${schemaName}/`);
        return result.data;
    }
    
    async createSchema(schemaData) {
        const result = await this.request('POST', '/schemas/', schemaData);
        return result.data;
    }
    
    async updateSchema(schemaName, updates) {
        const result = await this.request('PUT', `/schemas/${schemaName}/`, updates);
        return result.data;
    }
    
    async deleteSchema(schemaName) {
        const result = await this.request('DELETE', `/schemas/${schemaName}/`);
        return result.status === 'success';
    }
    
    async enableSchema(schemaName) {
        return this.managementAction('enable', schemaName);
    }
    
    async disableSchema(schemaName) {
        return this.managementAction('disable', schemaName);
    }
    
    async clearAllSchemas() {
        return this.managementAction('clear_all');
    }
    
    async managementAction(action, schemaName = null) {
        const data = { action };
        if (schemaName) {
            data.schema_name = schemaName;
        }
        
        const result = await this.request('POST', '/management/', data);
        return result.status === 'success';
    }
    
    async triggerDiscovery() {
        const result = await this.request('POST', '/discovery/');
        return result.data;
    }
    
    async getHealth() {
        const result = await this.request('GET', '/health/');
        return result.data;
    }
    
    async getMetrics() {
        const result = await this.request('GET', '/metrics/');
        return result.data;
    }
}

// Usage example
async function main() {
    const client = new GraphQLSchemaClient('http://localhost:8000');
    
    try {
        // List schemas
        const schemas = await client.listSchemas();
        console.log(`Found ${schemas.length} schemas:`);
        schemas.forEach(schema => {
            console.log(`  - ${schema.name}: ${schema.description}`);
        });
        
        // Check health
        const health = await client.getHealth();
        console.log(`System health: ${health.status}`);
        
        // Get metrics
        const metrics = await client.getMetrics();
        console.log(`Total schemas: ${metrics.schema_metrics.total_schemas}`);
        
    } catch (error) {
        console.error('API error:', error.message);
    }
}

// Run if in Node.js environment
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GraphQLSchemaClient;
    
    // Run example if this file is executed directly
    if (require.main === module) {
        main();
    }
}
```

## Advanced Patterns

### Schema Composition

```python
# advanced/schema_composition.py
import graphene
from rail_django_graphql.core.registry import schema_registry
from rail_django_graphql.decorators import register_schema

class BaseQuery(graphene.ObjectType):
    """Base query with common fields."""
    health = graphene.String()
    version = graphene.String()
    
    def resolve_health(self, info):
        return "OK"
    
    def resolve_version(self, info):
        return "1.0.0"

class UserMixin:
    """Mixin for user-related fields."""
    current_user = graphene.Field('UserType')
    
    def resolve_current_user(self, info):
        if info.context.user.is_authenticated:
            return info.context.user
        return None

class PaginationMixin:
    """Mixin for pagination support."""
    
    @staticmethod
    def add_pagination_args(field_class):
        """Add pagination arguments to a field."""
        class PaginatedField(field_class):
            class Arguments(getattr(field_class, 'Arguments', object)):
                limit = graphene.Int(default_value=20)
                offset = graphene.Int(default_value=0)
        
        return PaginatedField

# Composed schema using mixins
class ComposedQuery(BaseQuery, UserMixin):
    """Query class composed from multiple mixins."""
    
    # Use pagination mixin
    @PaginationMixin.add_pagination_args
    class products(graphene.List):
        pass

@register_schema(
    name='composed_schema',
    description='Schema using composition patterns',
    version='1.0.0'
)
def create_composed_schema():
    return graphene.Schema(query=ComposedQuery)
```

### Dynamic Schema Generation

```python
# advanced/dynamic_generation.py
import graphene
from django.apps import apps
from django.db import models
from rail_django_graphql.core.registry import schema_registry

class DynamicSchemaGenerator:
    """Generate GraphQL schemas dynamically from Django models."""
    
    TYPE_MAPPING = {
        models.CharField: graphene.String,
        models.TextField: graphene.String,
        models.IntegerField: graphene.Int,
        models.FloatField: graphene.Float,
        models.BooleanField: graphene.Boolean,
        models.DateTimeField: graphene.DateTime,
        models.DateField: graphene.Date,
        models.DecimalField: graphene.Decimal,
        models.EmailField: graphene.String,
        models.URLField: graphene.String,
    }
    
    def __init__(self, app_name: str):
        self.app_name = app_name
        self.app_config = apps.get_app_config(app_name)
        self.models = self.app_config.get_models()
        self.types = {}
    
    def generate_type(self, model):
        """Generate GraphQL type for Django model."""
        type_name = f"{model.__name__}Type"
        
        if type_name in self.types:
            return self.types[type_name]
        
        fields = {}
        
        # Add model fields
        for field in model._meta.fields:
            graphql_type = self.TYPE_MAPPING.get(type(field), graphene.String)
            
            if field.null:
                graphql_type = graphql_type()
            else:
                graphql_type = graphql_type(required=True)
            
            fields[field.name] = graphql_type
        
        # Add foreign key relationships
        for field in model._meta.fields:
            if isinstance(field, models.ForeignKey):
                related_model = field.related_model
                related_type = self.generate_type(related_model)
                fields[field.name] = graphene.Field(related_type)
        
        # Add reverse relationships
        for rel in model._meta.related_objects:
            if isinstance(rel, models.ManyToOneRel):
                related_type = self.generate_type(rel.related_model)
                field_name = f"{rel.get_accessor_name()}_set"
                fields[field_name] = graphene.List(related_type)
        
        # Create the type
        graphql_type = type(type_name, (graphene.ObjectType,), fields)
        self.types[type_name] = graphql_type
        
        return graphql_type
    
    def generate_query(self):
        """Generate Query class with resolvers."""
        query_fields = {}
        
        for model in self.models:
            model_type = self.generate_type(model)
            model_name = model.__name__.lower()
            
            # List field
            query_fields[f"{model_name}s"] = graphene.List(model_type)
            
            # Single item field
            query_fields[model_name] = graphene.Field(
                model_type,
                id=graphene.ID(required=True)
            )
            
            # Add resolvers
            def make_list_resolver(model_class):
                def resolver(self, info):
                    return model_class.objects.all()
                return resolver
            
            def make_single_resolver(model_class):
                def resolver(self, info, id):
                    return model_class.objects.get(pk=id)
                return resolver
            
            query_fields[f"resolve_{model_name}s"] = make_list_resolver(model)
            query_fields[f"resolve_{model_name}"] = make_single_resolver(model)
        
        return type('Query', (graphene.ObjectType,), query_fields)
    
    def generate_schema(self):
        """Generate complete GraphQL schema."""
        query_class = self.generate_query()
        return graphene.Schema(query=query_class)

# Register dynamic schemas for multiple apps
for app_name in ['users', 'products', 'orders']:
    generator = DynamicSchemaGenerator(app_name)
    
    schema_registry.register_schema(
        name=f'{app_name}_dynamic',
        description=f'Dynamically generated schema for {app_name}',
        version='1.0.0',
        apps=[app_name],
        builder=generator.generate_schema,
        settings={
            'dynamic': True,
            'generator': 'DynamicSchemaGenerator'
        }
    )
```

## Real-World Examples

### Complete E-commerce System

```python
# ecommerce/complete_example.py
"""
Complete e-commerce GraphQL system with multiple schemas.
"""

import graphene
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import transaction
from rail_django_graphql.decorators import register_schema
from rail_django_graphql.plugins.hooks import hook_registry

User = get_user_model()

# Models (assumed to exist)
# from .models import Product, Category, Order, OrderItem, Cart, CartItem, Review

# Shared types
class UserType(graphene.ObjectType):
    id = graphene.ID()
    username = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()

# Product Schema
class CategoryType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    products = graphene.List('ProductType')

class ProductType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    price = graphene.Decimal()
    category = graphene.Field(CategoryType)
    average_rating = graphene.Float()
    review_count = graphene.Int()

class ProductQuery(graphene.ObjectType):
    products = graphene.List(
        ProductType,
        category_id=graphene.ID(),
        search=graphene.String(),
        min_price=graphene.Decimal(),
        max_price=graphene.Decimal(),
        limit=graphene.Int(default_value=20),
        offset=graphene.Int(default_value=0)
    )
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    categories = graphene.List(CategoryType)

    def resolve_products(self, info, **filters):
        queryset = Product.objects.select_related('category')
        
        if filters.get('category_id'):
            queryset = queryset.filter(category_id=filters['category_id'])
        if filters.get('search'):
            queryset = queryset.filter(name__icontains=filters['search'])
        if filters.get('min_price'):
            queryset = queryset.filter(price__gte=filters['min_price'])
        if filters.get('max_price'):
            queryset = queryset.filter(price__lte=filters['max_price'])
        
        limit = filters.get('limit', 20)
        offset = filters.get('offset', 0)
        
        return queryset[offset:offset + limit]

@register_schema(
    name='product_catalog',
    description='Product catalog and categories',
    version='2.0.0',
    apps=['products'],
    settings={'enable_caching': True, 'cache_timeout': 300}
)
def create_product_schema():
    return graphene.Schema(query=ProductQuery)

# Cart Schema
class CartItemType(graphene.ObjectType):
    id = graphene.ID()
    product = graphene.Field(ProductType)
    quantity = graphene.Int()
    subtotal = graphene.Decimal()

class CartType(graphene.ObjectType):
    id = graphene.ID()
    user = graphene.Field(UserType)
    items = graphene.List(CartItemType)
    total = graphene.Decimal()
    item_count = graphene.Int()

class AddToCart(graphene.Mutation):
    class Arguments:
        product_id = graphene.ID(required=True)
        quantity = graphene.Int(default_value=1)

    cart_item = graphene.Field(CartItemType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, product_id, quantity):
        if not info.context.user.is_authenticated:
            return AddToCart(success=False, errors=['Authentication required'])

        try:
            with transaction.atomic():
                cart, created = Cart.objects.get_or_create(
                    user=info.context.user,
                    defaults={'status': 'active'}
                )
                
                product = Product.objects.get(pk=product_id)
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=product,
                    defaults={'quantity': quantity}
                )
                
                if not created:
                    cart_item.quantity += quantity
                    cart_item.save()

                return AddToCart(cart_item=cart_item, success=True, errors=[])
        except Exception as e:
            return AddToCart(success=False, errors=[str(e)])

class CartQuery(graphene.ObjectType):
    my_cart = graphene.Field(CartType)

    def resolve_my_cart(self, info):
        if info.context.user.is_authenticated:
            return Cart.objects.filter(
                user=info.context.user,
                status='active'
            ).prefetch_related('items__product').first()
        return None

class CartMutation(graphene.ObjectType):
    add_to_cart = AddToCart.Field()

@register_schema(
    name='shopping_cart',
    description='Shopping cart management',
    version='1.5.0',
    apps=['cart'],
    settings={'require_authentication': True}
)
def create_cart_schema():
    return graphene.Schema(query=CartQuery, mutation=CartMutation)

# Order Schema
class OrderItemType(graphene.ObjectType):
    id = graphene.ID()
    product = graphene.Field(ProductType)
    quantity = graphene.Int()
    price = graphene.Decimal()
    subtotal = graphene.Decimal()

class OrderType(graphene.ObjectType):
    id = graphene.ID()
    user = graphene.Field(UserType)
    items = graphene.List(OrderItemType)
    status = graphene.String()
    total = graphene.Decimal()
    created_at = graphene.DateTime()

class CreateOrder(graphene.Mutation):
    class Arguments:
        cart_id = graphene.ID()

    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, cart_id=None):
        if not info.context.user.is_authenticated:
            return CreateOrder(success=False, errors=['Authentication required'])

        try:
            with transaction.atomic():
                if cart_id:
                    cart = Cart.objects.get(pk=cart_id, user=info.context.user)
                else:
                    cart = Cart.objects.get(user=info.context.user, status='active')

                if not cart.items.exists():
                    return CreateOrder(success=False, errors=['Cart is empty'])

                order = Order.objects.create(
                    user=info.context.user,
                    status='pending'
                )

                for cart_item in cart.items.all():
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price
                    )

                # Clear cart
                cart.items.all().delete()
                cart.status = 'completed'
                cart.save()

                return CreateOrder(order=order, success=True, errors=[])
        except Exception as e:
            return CreateOrder(success=False, errors=[str(e)])

class OrderQuery(graphene.ObjectType):
    my_orders = graphene.List(OrderType)
    order = graphene.Field(OrderType, id=graphene.ID(required=True))

    def resolve_my_orders(self, info):
        if info.context.user.is_authenticated:
            return Order.objects.filter(
                user=info.context.user
            ).prefetch_related('items__product').order_by('-created_at')
        return []

    def resolve_order(self, info, id):
        if info.context.user.is_authenticated:
            return Order.objects.filter(
                id=id,
                user=info.context.user
            ).prefetch_related('items__product').first()
        return None

class OrderMutation(graphene.ObjectType):
    create_order = CreateOrder.Field()

@register_schema(
    name='order_management',
    description='Order processing and management',
    version='1.8.0',
    apps=['orders'],
    settings={
        'require_authentication': True,
        'enable_subscriptions': True
    }
)
def create_order_schema():
    return graphene.Schema(query=OrderQuery, mutation=OrderMutation)

# Custom hooks for the e-commerce system
def ecommerce_pre_registration_hook(schema_name: str, **kwargs) -> dict:
    """Add e-commerce specific settings to schemas."""
    if any(keyword in schema_name for keyword in ['product', 'cart', 'order']):
        settings = kwargs.setdefault('settings', {})
        settings['domain'] = 'ecommerce'
        settings['requires_ssl'] = True
        
        if 'cart' in schema_name or 'order' in schema_name:
            settings['session_required'] = True
    
    return kwargs

def ecommerce_post_registration_hook(schema_name: str, schema_info) -> None:
    """Log e-commerce schema registrations."""
    if schema_info.settings.get('domain') == 'ecommerce':
        logger.info(f"E-commerce schema '{schema_name}' registered successfully")

# Register hooks
hook_registry.register_hook(
    'pre_registration',
    ecommerce_pre_registration_hook,
    'ecommerce_enhancement'
)

hook_registry.register_hook(
    'post_registration',
    ecommerce_post_registration_hook,
    'ecommerce_logging'
)
```

This comprehensive examples document demonstrates various usage patterns and real-world scenarios for the Django GraphQL Multi-Schema System. Each example includes detailed code with proper error handling, authentication, and best practices.