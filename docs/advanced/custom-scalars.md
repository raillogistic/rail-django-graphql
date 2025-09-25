# Custom Scalars and Advanced Types

This document explains the custom scalar system in the Django GraphQL Auto-Generation Library, including built-in scalars, custom scalar creation, and advanced type handling.

## 📚 Table of Contents

- [Overview](#overview)
- [Built-in Custom Scalars](#built-in-custom-scalars)
- [Custom Scalar Registry](#custom-scalar-registry)
- [Method Return Type Analysis](#method-return-type-analysis)
- [Creating Custom Scalars](#creating-custom-scalars)
- [Advanced Type Mapping](#advanced-type-mapping)
- [Validation and Serialization](#validation-and-serialization)
- [Examples](#examples)

## 🔍 Overview

The custom scalar system provides:

- **Built-in scalars** for common Django field types
- **Automatic type detection** from Django fields and Python types
- **Custom scalar registration** for domain-specific types
- **Method return type analysis** for computed fields
- **Validation and serialization** with proper error handling

## 🎯 Built-in Custom Scalars

### JSONScalar

Handles JSON data with proper serialization and validation.

```python
from django_graphql_auto.generators.scalars import JSONScalar
import graphene

class JSONScalar(graphene.Scalar):
    """
    Custom scalar for JSON data.
    Supports serialization of Python objects to JSON and vice versa.
    """
    
    @staticmethod
    def serialize(value):
        """Serialize Python object to JSON string."""
        if value is None:
            return None
        
        if isinstance(value, str):
            # Already a JSON string
            try:
                json.loads(value)  # Validate JSON
                return value
            except json.JSONDecodeError:
                raise GraphQLError(f"Invalid JSON string: {value}")
        
        try:
            return json.dumps(value, default=str, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            raise GraphQLError(f"Cannot serialize to JSON: {e}")
    
    @staticmethod
    def parse_literal(node):
        """Parse JSON from GraphQL literal."""
        if isinstance(node, StringValueNode):
            try:
                return json.loads(node.value)
            except json.JSONDecodeError as e:
                raise GraphQLError(f"Invalid JSON literal: {e}")
        return None
    
    @staticmethod
    def parse_value(value):
        """Parse JSON from variable value."""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                raise GraphQLError(f"Invalid JSON value: {e}")
        return value
```

#### Usage Example

```python
# Django Model
class Settings(models.Model):
    name = models.CharField(max_length=100)
    config = models.JSONField(default=dict)

# GraphQL Query
query {
  settings {
    id
    name
    config  # Returns as JSON scalar
  }
}

# GraphQL Mutation
mutation {
  createSettings(input: {
    name: "App Settings"
    config: "{\"theme\": \"dark\", \"notifications\": true}"
  }) {
    ok
    settings {
      id
      config
    }
  }
}
```

### DateTimeScalar

Enhanced DateTime handling with timezone support.

```python
class DateTimeScalar(graphene.Scalar):
    """
    Custom scalar for DateTime with enhanced timezone handling.
    """
    
    @staticmethod
    def serialize(value):
        """Serialize datetime to ISO string."""
        if value is None:
            return None
        
        if isinstance(value, datetime):
            # Ensure timezone awareness
            if timezone.is_naive(value):
                value = timezone.make_aware(value)
            return value.isoformat()
        
        if isinstance(value, str):
            # Validate datetime string
            try:
                parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return parsed.isoformat()
            except ValueError as e:
                raise GraphQLError(f"Invalid datetime string: {e}")
        
        raise GraphQLError(f"Cannot serialize datetime: {type(value)}")
    
    @staticmethod
    def parse_literal(node):
        """Parse datetime from GraphQL literal."""
        if isinstance(node, StringValueNode):
            try:
                return datetime.fromisoformat(node.value.replace('Z', '+00:00'))
            except ValueError as e:
                raise GraphQLError(f"Invalid datetime literal: {e}")
        return None
    
    @staticmethod
    def parse_value(value):
        """Parse datetime from variable value."""
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError as e:
                raise GraphQLError(f"Invalid datetime value: {e}")
        elif isinstance(value, datetime):
            return value
        return None
```

### DecimalScalar

Precise decimal handling for financial data.

```python
class DecimalScalar(graphene.Scalar):
    """
    Custom scalar for Decimal with precision handling.
    """
    
    @staticmethod
    def serialize(value):
        """Serialize Decimal to string."""
        if value is None:
            return None
        
        if isinstance(value, Decimal):
            return str(value)
        
        if isinstance(value, (int, float)):
            return str(Decimal(str(value)))
        
        if isinstance(value, str):
            try:
                return str(Decimal(value))
            except (InvalidOperation, ValueError) as e:
                raise GraphQLError(f"Invalid decimal string: {e}")
        
        raise GraphQLError(f"Cannot serialize decimal: {type(value)}")
    
    @staticmethod
    def parse_literal(node):
        """Parse Decimal from GraphQL literal."""
        if isinstance(node, StringValueNode):
            try:
                return Decimal(node.value)
            except (InvalidOperation, ValueError) as e:
                raise GraphQLError(f"Invalid decimal literal: {e}")
        elif isinstance(node, (IntValueNode, FloatValueNode)):
            try:
                return Decimal(str(node.value))
            except (InvalidOperation, ValueError) as e:
                raise GraphQLError(f"Invalid decimal literal: {e}")
        return None
    
    @staticmethod
    def parse_value(value):
        """Parse Decimal from variable value."""
        if isinstance(value, str):
            try:
                return Decimal(value)
            except (InvalidOperation, ValueError) as e:
                raise GraphQLError(f"Invalid decimal value: {e}")
        elif isinstance(value, (int, float)):
            return Decimal(str(value))
        elif isinstance(value, Decimal):
            return value
        return None
```

### UUIDScalar

UUID handling with validation.

```python
class UUIDScalar(graphene.Scalar):
    """
    Custom scalar for UUID with validation.
    """
    
    @staticmethod
    def serialize(value):
        """Serialize UUID to string."""
        if value is None:
            return None
        
        if isinstance(value, UUID):
            return str(value)
        
        if isinstance(value, str):
            try:
                UUID(value)  # Validate UUID format
                return value
            except ValueError as e:
                raise GraphQLError(f"Invalid UUID string: {e}")
        
        raise GraphQLError(f"Cannot serialize UUID: {type(value)}")
    
    @staticmethod
    def parse_literal(node):
        """Parse UUID from GraphQL literal."""
        if isinstance(node, StringValueNode):
            try:
                return UUID(node.value)
            except ValueError as e:
                raise GraphQLError(f"Invalid UUID literal: {e}")
        return None
    
    @staticmethod
    def parse_value(value):
        """Parse UUID from variable value."""
        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError as e:
                raise GraphQLError(f"Invalid UUID value: {e}")
        elif isinstance(value, UUID):
            return value
        return None
```

### DurationScalar

Time duration handling.

```python
class DurationScalar(graphene.Scalar):
    """
    Custom scalar for Duration/timedelta.
    """
    
    @staticmethod
    def serialize(value):
        """Serialize timedelta to ISO 8601 duration string."""
        if value is None:
            return None
        
        if isinstance(value, timedelta):
            # Convert to ISO 8601 duration format
            total_seconds = int(value.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"PT{hours}H{minutes}M{seconds}S"
        
        if isinstance(value, str):
            # Validate duration string
            try:
                return DurationScalar._parse_duration_string(value)
            except ValueError as e:
                raise GraphQLError(f"Invalid duration string: {e}")
        
        raise GraphQLError(f"Cannot serialize duration: {type(value)}")
    
    @staticmethod
    def parse_literal(node):
        """Parse duration from GraphQL literal."""
        if isinstance(node, StringValueNode):
            try:
                return DurationScalar._parse_duration_string(node.value)
            except ValueError as e:
                raise GraphQLError(f"Invalid duration literal: {e}")
        return None
    
    @staticmethod
    def parse_value(value):
        """Parse duration from variable value."""
        if isinstance(value, str):
            try:
                return DurationScalar._parse_duration_string(value)
            except ValueError as e:
                raise GraphQLError(f"Invalid duration value: {e}")
        elif isinstance(value, timedelta):
            return value
        return None
    
    @staticmethod
    def _parse_duration_string(duration_str):
        """Parse ISO 8601 duration string to timedelta."""
        # Simple parser for PT{hours}H{minutes}M{seconds}S format
        import re
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        if not match:
            raise ValueError(f"Invalid duration format: {duration_str}")
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
```

## 🗂️ Custom Scalar Registry

The `CustomScalarRegistry` manages all custom scalars and provides automatic type mapping.

```python
from django_graphql_auto.generators.scalars import CustomScalarRegistry

class CustomScalarRegistry:
    """
    Registry for managing custom GraphQL scalars and their mappings.
    """
    
    def __init__(self):
        self._scalars = {}
        self._field_mappings = {}
        self._type_mappings = {}
        self._register_builtin_scalars()
    
    def register_scalar(self, name: str, scalar_class: Type[graphene.Scalar]):
        """Register a custom scalar."""
        self._scalars[name] = scalar_class
    
    def register_field_mapping(self, field_type: Type[Field], scalar_name: str):
        """Map Django field type to scalar."""
        self._field_mappings[field_type] = scalar_name
    
    def register_type_mapping(self, python_type: Type, scalar_name: str):
        """Map Python type to scalar."""
        self._type_mappings[python_type] = scalar_name
    
    def get_scalar_for_field(self, field: Field) -> Optional[Type[graphene.Scalar]]:
        """Get appropriate scalar for Django field."""
        field_type = type(field)
        scalar_name = self._field_mappings.get(field_type)
        return self._scalars.get(scalar_name) if scalar_name else None
    
    def get_scalar_for_type(self, python_type: Type) -> Optional[Type[graphene.Scalar]]:
        """Get appropriate scalar for Python type."""
        scalar_name = self._type_mappings.get(python_type)
        return self._scalars.get(scalar_name) if scalar_name else None
    
    def _register_builtin_scalars(self):
        """Register built-in custom scalars."""
        # Register scalars
        self.register_scalar('JSON', JSONScalar)
        self.register_scalar('DateTime', DateTimeScalar)
        self.register_scalar('Decimal', DecimalScalar)
        self.register_scalar('UUID', UUIDScalar)
        self.register_scalar('Duration', DurationScalar)
        
        # Register field mappings
        from django.db import models
        self.register_field_mapping(models.JSONField, 'JSON')
        self.register_field_mapping(models.DateTimeField, 'DateTime')
        self.register_field_mapping(models.DecimalField, 'Decimal')
        self.register_field_mapping(models.UUIDField, 'UUID')
        self.register_field_mapping(models.DurationField, 'Duration')
        
        # Register type mappings
        from decimal import Decimal
        from uuid import UUID
        from datetime import datetime, timedelta
        
        self.register_type_mapping(dict, 'JSON')
        self.register_type_mapping(list, 'JSON')
        self.register_type_mapping(datetime, 'DateTime')
        self.register_type_mapping(Decimal, 'Decimal')
        self.register_type_mapping(UUID, 'UUID')
        self.register_type_mapping(timedelta, 'Duration')

# Global registry instance
scalar_registry = CustomScalarRegistry()
```

## 🔍 Method Return Type Analysis

The `MethodReturnTypeAnalyzer` analyzes model methods and properties to determine appropriate GraphQL types.

```python
from django_graphql_auto.generators.scalars import MethodReturnTypeAnalyzer

class MethodReturnTypeAnalyzer:
    """
    Analyzes method return types and maps them to appropriate GraphQL types.
    """
    
    def __init__(self, scalar_registry: CustomScalarRegistry):
        self.scalar_registry = scalar_registry
    
    def analyze_method(self, method: Callable) -> Optional[Type[graphene.Scalar]]:
        """
        Analyze a method and determine its GraphQL return type.
        
        Args:
            method: Method or property to analyze
            
        Returns:
            Appropriate GraphQL scalar type or None
        """
        # Get type hints
        type_hints = get_type_hints(method)
        return_type = type_hints.get('return')
        
        if return_type:
            return self._map_type_to_scalar(return_type)
        
        # Fallback to docstring analysis
        return self._analyze_docstring(method)
    
    def _map_type_to_scalar(self, python_type: Type) -> Optional[Type[graphene.Scalar]]:
        """Map Python type to GraphQL scalar."""
        # Handle basic types
        if python_type == str:
            return graphene.String
        elif python_type == int:
            return graphene.Int
        elif python_type == float:
            return graphene.Float
        elif python_type == bool:
            return graphene.Boolean
        
        # Handle custom scalars
        scalar = self.scalar_registry.get_scalar_for_type(python_type)
        if scalar:
            return scalar
        
        # Handle generic types
        origin = get_origin(python_type)
        if origin is list:
            args = get_args(python_type)
            if args:
                item_type = self._map_type_to_scalar(args[0])
                return graphene.List(item_type) if item_type else None
        
        elif origin is dict:
            return JSONScalar
        
        elif origin is Union:
            # Handle Optional types
            args = get_args(python_type)
            if len(args) == 2 and type(None) in args:
                non_none_type = next(arg for arg in args if arg != type(None))
                return self._map_type_to_scalar(non_none_type)
        
        return None
    
    def _analyze_docstring(self, method: Callable) -> Optional[Type[graphene.Scalar]]:
        """Analyze method docstring for return type information."""
        docstring = inspect.getdoc(method)
        if not docstring:
            return None
        
        # Look for return type patterns in docstring
        patterns = {
            r'returns?\s*:?\s*str': graphene.String,
            r'returns?\s*:?\s*int': graphene.Int,
            r'returns?\s*:?\s*float': graphene.Float,
            r'returns?\s*:?\s*bool': graphene.Boolean,
            r'returns?\s*:?\s*dict': JSONScalar,
            r'returns?\s*:?\s*list': graphene.List(graphene.String),
        }
        
        for pattern, scalar_type in patterns.items():
            if re.search(pattern, docstring, re.IGNORECASE):
                return scalar_type
        
        return None

# Usage example
analyzer = MethodReturnTypeAnalyzer(scalar_registry)

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_word_count(self) -> int:
        """Returns the word count of the content."""
        return len(self.content.split())
    
    def get_reading_time(self) -> timedelta:
        """Returns estimated reading time."""
        words = len(self.content.split())
        minutes = words / 200  # Average reading speed
        return timedelta(minutes=minutes)
    
    @property
    def metadata(self) -> dict:
        """Returns post metadata as JSON."""
        return {
            'word_count': self.get_word_count(),
            'reading_time_minutes': self.get_reading_time().total_seconds() / 60,
            'created_date': self.created_at.date().isoformat(),
        }

# Analyze methods
word_count_type = analyzer.analyze_method(Post.get_word_count)  # Returns graphene.Int
reading_time_type = analyzer.analyze_method(Post.get_reading_time)  # Returns DurationScalar
metadata_type = analyzer.analyze_method(Post.metadata.fget)  # Returns JSONScalar
```

## 🎨 Creating Custom Scalars

### Basic Custom Scalar

```python
import graphene
from graphene.types.scalar import Scalar
from graphql.language.ast import StringValueNode

class ColorScalar(Scalar):
    """
    Custom scalar for color values (hex, rgb, hsl).
    """
    
    @staticmethod
    def serialize(value):
        """Serialize color to string."""
        if value is None:
            return None
        
        if isinstance(value, str):
            if ColorScalar._is_valid_color(value):
                return value
            else:
                raise GraphQLError(f"Invalid color format: {value}")
        
        raise GraphQLError(f"Cannot serialize color: {type(value)}")
    
    @staticmethod
    def parse_literal(node):
        """Parse color from GraphQL literal."""
        if isinstance(node, StringValueNode):
            if ColorScalar._is_valid_color(node.value):
                return node.value
            else:
                raise GraphQLError(f"Invalid color literal: {node.value}")
        return None
    
    @staticmethod
    def parse_value(value):
        """Parse color from variable value."""
        if isinstance(value, str):
            if ColorScalar._is_valid_color(value):
                return value
            else:
                raise GraphQLError(f"Invalid color value: {value}")
        return None
    
    @staticmethod
    def _is_valid_color(color_str):
        """Validate color string format."""
        import re
        
        # Hex color pattern
        hex_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        if re.match(hex_pattern, color_str):
            return True
        
        # RGB pattern
        rgb_pattern = r'^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$'
        rgb_match = re.match(rgb_pattern, color_str)
        if rgb_match:
            r, g, b = map(int, rgb_match.groups())
            return all(0 <= val <= 255 for val in [r, g, b])
        
        # HSL pattern
        hsl_pattern = r'^hsl\(\s*(\d{1,3})\s*,\s*(\d{1,3})%\s*,\s*(\d{1,3})%\s*\)$'
        hsl_match = re.match(hsl_pattern, color_str)
        if hsl_match:
            h, s, l = map(int, hsl_match.groups())
            return 0 <= h <= 360 and 0 <= s <= 100 and 0 <= l <= 100
        
        return False

# Register the custom scalar
scalar_registry.register_scalar('Color', ColorScalar)
```

### Advanced Custom Scalar with Validation

```python
class EmailScalar(Scalar):
    """
    Custom scalar for email addresses with validation.
    """
    
    @staticmethod
    def serialize(value):
        """Serialize email to string."""
        if value is None:
            return None
        
        if isinstance(value, str):
            if EmailScalar._is_valid_email(value):
                return value.lower()  # Normalize to lowercase
            else:
                raise GraphQLError(f"Invalid email format: {value}")
        
        raise GraphQLError(f"Cannot serialize email: {type(value)}")
    
    @staticmethod
    def parse_literal(node):
        """Parse email from GraphQL literal."""
        if isinstance(node, StringValueNode):
            if EmailScalar._is_valid_email(node.value):
                return node.value.lower()
            else:
                raise GraphQLError(f"Invalid email literal: {node.value}")
        return None
    
    @staticmethod
    def parse_value(value):
        """Parse email from variable value."""
        if isinstance(value, str):
            if EmailScalar._is_valid_email(value):
                return value.lower()
            else:
                raise GraphQLError(f"Invalid email value: {value}")
        return None
    
    @staticmethod
    def _is_valid_email(email_str):
        """Validate email format using Django's validator."""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        try:
            validate_email(email_str)
            return True
        except ValidationError:
            return False

# Register with field mapping
scalar_registry.register_scalar('Email', EmailScalar)
scalar_registry.register_field_mapping(models.EmailField, 'Email')
```

## 🔧 Advanced Type Mapping

### Custom Field Converter

```python
from django_graphql_auto.generators.types import TypeGenerator

class CustomTypeGenerator(TypeGenerator):
    """Extended type generator with custom field handling."""
    
    def convert_field(self, field_info):
        """Convert Django field to GraphQL field with custom scalar support."""
        # Check for custom scalar mapping first
        custom_scalar = self.scalar_registry.get_scalar_for_field(field_info.field)
        if custom_scalar:
            return graphene.Field(
                custom_scalar,
                required=field_info.is_required,
                description=field_info.help_text
            )
        
        # Handle special field types
        if isinstance(field_info.field, models.FileField):
            return self._convert_file_field(field_info)
        elif isinstance(field_info.field, models.ImageField):
            return self._convert_image_field(field_info)
        elif hasattr(field_info.field, 'choices') and field_info.field.choices:
            return self._convert_choice_field(field_info)
        
        # Fallback to default conversion
        return super().convert_field(field_info)
    
    def _convert_file_field(self, field_info):
        """Convert FileField to custom File scalar."""
        return graphene.Field(
            FileScalar,
            required=field_info.is_required,
            description=f"File field: {field_info.help_text}"
        )
    
    def _convert_image_field(self, field_info):
        """Convert ImageField to custom Image scalar."""
        return graphene.Field(
            ImageScalar,
            required=field_info.is_required,
            description=f"Image field: {field_info.help_text}"
        )
    
    def _convert_choice_field(self, field_info):
        """Convert field with choices to Enum."""
        enum_name = f"{field_info.model.__name__}{field_info.name.title()}Enum"
        enum_values = {
            choice[0].upper().replace(' ', '_'): choice[0]
            for choice in field_info.field.choices
        }
        
        enum_type = type(enum_name, (graphene.Enum,), enum_values)
        
        return graphene.Field(
            enum_type,
            required=field_info.is_required,
            description=field_info.help_text
        )
```

### File and Image Scalars

```python
class FileScalar(Scalar):
    """Custom scalar for file uploads and references."""
    
    @staticmethod
    def serialize(value):
        """Serialize file to URL or file info."""
        if value is None:
            return None
        
        if hasattr(value, 'url'):
            return {
                'url': value.url,
                'name': value.name,
                'size': value.size if hasattr(value, 'size') else None,
            }
        elif isinstance(value, str):
            return {'url': value, 'name': value.split('/')[-1]}
        
        return str(value)
    
    @staticmethod
    def parse_literal(node):
        """Parse file from GraphQL literal."""
        if isinstance(node, StringValueNode):
            return node.value
        return None
    
    @staticmethod
    def parse_value(value):
        """Parse file from variable value."""
        if isinstance(value, str):
            return value
        elif hasattr(value, 'read'):  # File-like object
            return value
        return None

class ImageScalar(FileScalar):
    """Custom scalar for image files with additional metadata."""
    
    @staticmethod
    def serialize(value):
        """Serialize image with dimensions and metadata."""
        if value is None:
            return None
        
        result = FileScalar.serialize(value)
        
        if hasattr(value, 'width') and hasattr(value, 'height'):
            if isinstance(result, dict):
                result.update({
                    'width': value.width,
                    'height': value.height,
                })
        
        return result
```

## 📊 Usage Examples

### Model with Custom Scalars

```python
# Django Model
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.CharField(max_length=50)  # Will use ColorScalar
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    
    def get_price_range(self) -> dict:
        """Returns price range information."""
        return {
            'min': float(self.price * Decimal('0.9')),
            'max': float(self.price * Decimal('1.1')),
            'currency': 'USD'
        }
    
    @property
    def processing_time(self) -> timedelta:
        """Estimated processing time."""
        return timedelta(days=3)

# Register custom field mappings
scalar_registry.register_field_mapping(models.CharField, 'Color')  # For color field specifically

# GraphQL Schema will include:
# - price: Decimal
# - color: Color
# - metadata: JSON
# - created_at: DateTime
# - uuid: UUID
# - price_range: JSON (from method)
# - processing_time: Duration (from property)
```

### GraphQL Operations

```graphql
# Query with custom scalars
query {
  products {
    id
    name
    price          # Returns as decimal string
    color          # Validated color format
    metadata       # JSON object
    created_at     # ISO datetime string
    uuid           # UUID string
    price_range    # JSON object with min/max
    processing_time # ISO duration string
  }
}

# Mutation with custom scalars
mutation {
  createProduct(input: {
    name: "Red Widget"
    price: "29.99"
    color: "#ff0000"
    metadata: "{\"category\": \"widgets\", \"featured\": true}"
  }) {
    ok
    product {
      id
      price
      color
      metadata
    }
    errors
  }
}

# Variables with custom scalars
mutation CreateProduct($input: CreateProductInput!) {
  createProduct(input: $input) {
    ok
    product {
      id
      uuid
      created_at
    }
  }
}

# Variables:
{
  "input": {
    "name": "Blue Widget",
    "price": "39.99",
    "color": "rgb(0, 100, 255)",
    "metadata": {
      "category": "premium",
      "tags": ["new", "featured"]
    }
  }
}
```

## ⚙️ Configuration

### Global Scalar Configuration

```python
# settings.py
DJANGO_GRAPHQL_AUTO = {
    'CUSTOM_SCALARS': {
        # Built-in scalars
        'ENABLE_JSON_SCALAR': True,
        'ENABLE_DATETIME_SCALAR': True,
        'ENABLE_DECIMAL_SCALAR': True,
        'ENABLE_UUID_SCALAR': True,
        'ENABLE_DURATION_SCALAR': True,
        
        # Custom scalar mappings
        'FIELD_MAPPINGS': {
            'myapp.fields.ColorField': 'Color',
            'myapp.fields.EmailField': 'Email',
        },
        
        # Type mappings
        'TYPE_MAPPINGS': {
            'myapp.types.CustomType': 'JSON',
        },
    },
    
    'METHOD_ANALYSIS': {
        'ENABLE_METHOD_ANALYSIS': True,
        'ANALYZE_PROPERTIES': True,
        'ANALYZE_CACHED_PROPERTIES': True,
        'INCLUDE_PRIVATE_METHODS': False,
    }
}
```

### Per-Model Configuration

```python
# models.py
class Product(models.Model):
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=50)
    
    class GraphQLMeta:
        # Override scalar for specific fields
        scalar_overrides = {
            'color': 'Color',
            'metadata': 'JSON',
        }
        
        # Include computed fields
        computed_fields = {
            'price_range': 'JSON',
            'processing_time': 'Duration',
        }
```

## 🚀 Next Steps

Now that you understand custom scalars:

1. [Learn About Inheritance Support](inheritance.md) - Model inheritance and polymorphism
2. [Explore Nested Operations](nested-operations.md) - Complex nested create/update operations
3. [Check Performance Guide](../development/performance.md) - Optimization techniques
4. [Review Testing Guide](../development/testing.md) - Testing custom scalars

## 🤝 Need Help?

- Check the [Troubleshooting Guide](../development/troubleshooting.md)
- Review [Advanced Examples](../examples/advanced-examples.md)
- Join our [Community Discussions](https://github.com/your-repo/django-graphql-auto/discussions)