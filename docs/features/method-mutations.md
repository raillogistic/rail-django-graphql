# Method Mutations

Method mutations allow you to automatically generate GraphQL mutations from custom methods defined on your Django models. This feature enables you to expose business logic as GraphQL operations while maintaining clean separation of concerns.

## 📚 Table of Contents

- [Overview](#overview)
- [Configuration](#configuration)
- [Defining Model Methods](#defining-model-methods)
- [Generated GraphQL Schema](#generated-graphql-schema)
- [Usage Examples](#usage-examples)
- [Method Parameters](#method-parameters)
- [Return Values](#return-values)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Advanced Patterns](#advanced-patterns)

## 🔍 Overview

Method mutations automatically convert Django model methods into GraphQL mutations, providing a clean way to expose business logic through your GraphQL API. Each method becomes a mutation that can be called with the model instance ID and any additional parameters.

### Key Features

- ✅ **Automatic Discovery**: Methods are automatically detected and converted to mutations
- ✅ **Parameter Support**: Methods can accept parameters that become GraphQL input fields
- ✅ **Type Safety**: Full type inference and validation
- ✅ **Error Handling**: Comprehensive error handling and validation
- ✅ **French Verbose Names**: Support for French field names via verbose_name
- ✅ **Documentation**: Automatic documentation from method docstrings

## ⚙️ Configuration

Enable method mutations in your Django settings:

```python
# settings.py
DJANGO_GRAPHQL_AUTO = {
    'APPS': ['your_app'],
    'MUTATION_SETTINGS': {
        'enable_method_mutations': True,  # Enable method mutations
        'method_mutation_prefix': '',     # Optional prefix for mutation names
        'include_private_methods': False, # Exclude methods starting with _
    }
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable_method_mutations` | `bool` | `False` | Enable/disable method mutations |
| `method_mutation_prefix` | `str` | `''` | Prefix for generated mutation names |
| `include_private_methods` | `bool` | `False` | Include methods starting with underscore |

## 🏗️ Defining Model Methods

### Basic Method Definition

```python
# models.py
from django.db import models

class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre du post")
    content = models.TextField(verbose_name="Contenu du post")
    published = models.BooleanField(default=False, verbose_name="Publié")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    def publish_post(self):
        """Publier le post (Publish the post)"""
        self.published = True
        self.save()
        return self
    
    def archive_post(self):
        """Archiver le post (Archive the post)"""
        self.published = False
        self.save()
        return self
```

### Methods with Parameters

```python
class Order(models.Model):
    status = models.CharField(max_length=20, verbose_name="Statut de la commande")
    tracking_number = models.CharField(max_length=50, blank=True, verbose_name="Numéro de suivi")
    
    def ship_order(self, tracking_number: str = None):
        """Expédier la commande (Ship the order)"""
        self.status = 'shipped'
        if tracking_number:
            self.tracking_number = tracking_number
        self.save()
        return self
    
    def add_note(self, note: str, priority: int = 1):
        """Ajouter une note (Add a note)"""
        # Create related note object
        self.notes.create(content=note, priority=priority)
        return self
```

### Method Requirements

For a method to be converted to a GraphQL mutation, it must:

1. **Return the model instance**: Methods should return `self` or the modified instance
2. **Be public**: Method names cannot start with underscore (unless configured)
3. **Have a docstring**: Documentation is recommended for better GraphQL schema
4. **Be instance methods**: Class methods and static methods are not supported

## 🔄 Generated GraphQL Schema

### Naming Convention

Method mutations follow this naming pattern:
```
{modelName}{MethodName}
```

Examples:
- `post.publish_post()` → `postPublishPost`
- `order.ship_order()` → `orderShipOrder`
- `user.activate_account()` → `userActivateAccount`

### Input Type Structure

```graphql
input PostPublishPostInput {
  id: ID!  # Always required - the instance to operate on
  # Additional parameters from method signature
}

input OrderShipOrderInput {
  id: ID!
  trackingNumber: String  # From tracking_number parameter
}
```

### Return Type Structure

```graphql
type PostPublishPostPayload {
  ok: Boolean!
  post: Post  # The returned model instance
  errors: [String!]
}
```

## 📝 Usage Examples

### Simple Method Mutation

```graphql
mutation PublishPost($id: ID!) {
  postPublishPost(input: { id: $id }) {
    ok
    post {
      id
      title
      published
    }
    errors
  }
}
```

### Method with Parameters

```graphql
mutation ShipOrder($id: ID!, $trackingNumber: String!) {
  orderShipOrder(input: { 
    id: $id
    trackingNumber: $trackingNumber 
  }) {
    ok
    order {
      id
      status
      trackingNumber
    }
    errors
  }
}
```

### Variables Example

```json
{
  "id": "1",
  "trackingNumber": "TRACK123456"
}
```

## 🔧 Method Parameters

### Supported Parameter Types

| Python Type | GraphQL Type | Example |
|-------------|--------------|---------|
| `str` | `String` | `name: str` |
| `int` | `Int` | `count: int` |
| `float` | `Float` | `price: float` |
| `bool` | `Boolean` | `active: bool` |
| `datetime` | `DateTime` | `scheduled_at: datetime` |
| `date` | `Date` | `due_date: date` |
| `Decimal` | `Decimal` | `amount: Decimal` |

### Optional Parameters

```python
def update_priority(self, priority: int = 1, notes: str = None):
    """Mettre à jour la priorité (Update priority)"""
    self.priority = priority
    if notes:
        self.notes = notes
    self.save()
    return self
```

Generated GraphQL:
```graphql
input TaskUpdatePriorityInput {
  id: ID!
  priority: Int = 1
  notes: String
}
```

### Type Hints

Always use type hints for better GraphQL type inference:

```python
# ✅ Good - with type hints
def set_discount(self, percentage: float, reason: str) -> 'Order':
    """Appliquer une remise (Apply discount)"""
    self.discount_percentage = percentage
    self.discount_reason = reason
    self.save()
    return self

# ❌ Avoid - without type hints
def set_discount(self, percentage, reason):
    # Types will be inferred as String by default
    pass
```

## 🔄 Return Values

### Standard Return Pattern

Always return the model instance for consistency:

```python
def activate_user(self):
    """Activer l'utilisateur (Activate user)"""
    self.is_active = True
    self.save()
    return self  # ✅ Return self
```

### Complex Return Values

For operations that affect multiple objects:

```python
def process_order(self):
    """Traiter la commande (Process order)"""
    # Update order status
    self.status = 'processing'
    self.save()
    
    # Update inventory
    for item in self.items.all():
        item.product.reduce_stock(item.quantity)
    
    return self  # Return the main object
```

## ⚠️ Error Handling

### Validation in Methods

```python
def ship_order(self, tracking_number: str):
    """Expédier la commande (Ship order)"""
    if self.status != 'confirmed':
        raise ValueError("La commande doit être confirmée avant l'expédition")
    
    if not tracking_number:
        raise ValueError("Le numéro de suivi est requis")
    
    self.status = 'shipped'
    self.tracking_number = tracking_number
    self.save()
    return self
```

### GraphQL Error Response

```graphql
mutation ShipOrder($id: ID!, $trackingNumber: String!) {
  orderShipOrder(input: { id: $id, trackingNumber: $trackingNumber }) {
    ok  # false if error occurred
    order {
      # null if error occurred
      id
      status
    }
    errors  # ["La commande doit être confirmée avant l'expédition"]
  }
}
```

## 🎯 Best Practices

### 1. Clear Method Names

Use descriptive method names that clearly indicate the action:

```python
# ✅ Good
def publish_post(self):
def archive_post(self):
def activate_user(self):

# ❌ Avoid
def do_something(self):
def process(self):
def update(self):
```

### 2. Comprehensive Docstrings

Include both French and English descriptions:

```python
def confirm_order(self):
    """
    Confirmer la commande (Confirm the order)
    
    Changes the order status to confirmed and sends
    a confirmation email to the customer.
    """
    pass
```

### 3. Atomic Operations

Ensure methods are atomic and handle transactions:

```python
from django.db import transaction

@transaction.atomic
def process_payment(self, amount: float):
    """Traiter le paiement (Process payment)"""
    # All operations succeed or fail together
    self.charge_amount = amount
    self.status = 'paid'
    self.save()
    
    # Create payment record
    self.payments.create(amount=amount)
    return self
```

### 4. Input Validation

Validate inputs early in the method:

```python
def set_priority(self, priority: int):
    """Définir la priorité (Set priority)"""
    if not 1 <= priority <= 5:
        raise ValueError("La priorité doit être entre 1 et 5")
    
    self.priority = priority
    self.save()
    return self
```

## 🚀 Advanced Patterns

### Conditional Method Exposure

Use decorators to control method exposure:

```python
from django_graphql_auto.decorators import graphql_method

class Post(models.Model):
    # ... fields ...
    
    @graphql_method
    def publish_post(self):
        """Publier le post (Publish post)"""
        return self
    
    @graphql_method(enabled=False)
    def internal_method(self):
        """This method won't be exposed"""
        return self
```

### Method Chaining

Support method chaining for complex operations:

```python
def publish_and_feature(self):
    """Publier et mettre en avant (Publish and feature)"""
    self.published = True
    self.featured = True
    self.save()
    return self

def schedule_publication(self, publish_at: datetime):
    """Programmer la publication (Schedule publication)"""
    self.scheduled_publish_at = publish_at
    self.save()
    return self
```

### Integration with Signals

Trigger Django signals from methods:

```python
from django.db.models.signals import post_save

def approve_comment(self):
    """Approuver le commentaire (Approve comment)"""
    self.is_approved = True
    self.save()
    
    # Signal will be triggered by save()
    # Can be used for notifications, etc.
    return self
```

## 🔍 Troubleshooting

### Common Issues

1. **Method not appearing in schema**
   - Check that `enable_method_mutations` is `True`
   - Ensure method returns `self` or model instance
   - Verify method is public (doesn't start with `_`)

2. **Parameter types incorrect**
   - Add proper type hints to method parameters
   - Use supported Python types

3. **Errors not handled properly**
   - Wrap operations in try/catch blocks
   - Raise appropriate exceptions with clear messages

### Debug Mode

Enable debug logging to see method discovery:

```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django_graphql_auto.generators.mutations': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

This comprehensive guide covers all aspects of method mutations in the Django GraphQL Auto-Generation Library. Method mutations provide a powerful way to expose business logic while maintaining clean, type-safe GraphQL APIs.