# Polymorphic Models Support

Django GraphQL Auto provides built-in support for Django polymorphic models, automatically handling the complexities of inheritance and polymorphic relationships in GraphQL schemas.

## Overview

When using `django-polymorphic` with Django models, certain internal fields are automatically managed by the library. Django GraphQL Auto automatically excludes these internal fields from the generated GraphQL schema to prevent exposure of implementation details.

## Automatically Excluded Fields

The following fields are automatically excluded from GraphQL schemas when working with polymorphic models:

- `polymorphic_ctype`: Internal field used by django-polymorphic to track the actual model type
- Fields ending with `_ptr`: OneToOneField pointers used in Django model inheritance (e.g., `client_ptr`)

## Example

```python
from polymorphic.models import PolymorphicModel
from django.db import models

class Client(PolymorphicModel):
    """Base client model"""
    name = models.CharField(max_length=100)
    email = models.EmailField()

class LocalClient(Client):
    """Local client with additional fields"""
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
```

In the generated GraphQL schema:

```graphql
type ClientType {
  id: ID!
  name: String!
  email: String!
  # polymorphic_ctype is automatically excluded
}

type LocalClientType {
  id: ID!
  name: String!
  email: String!
  address: String!
  phone: String!
  # client_ptr is automatically excluded
}

input CreateLocalClientInput {
  name: String!
  email: String!
  address: String!
  phone: String!
  # Internal polymorphic fields are excluded from input types
}
```

## Benefits

1. **Clean API**: Internal implementation details are hidden from GraphQL consumers
2. **Automatic Handling**: No manual configuration required for polymorphic field exclusion
3. **Consistent Behavior**: Works across queries, mutations, and input types
4. **Type Safety**: Prevents invalid mutations that could break polymorphic relationships

## Configuration

No additional configuration is required. The polymorphic field exclusion is handled automatically by the type generator.

If you need to exclude additional fields from polymorphic models, you can use the standard field exclusion configuration:

```python
# In your Django settings
DJANGO_GRAPHQL_AUTO = {
    'exclude_fields': {
        'Client': ['internal_field'],
        'LocalClient': ['debug_field'],
    }
}
```

## Troubleshooting

If you encounter issues with polymorphic models:

1. Ensure `django-polymorphic` is properly installed and configured
2. Verify that your models inherit from `PolymorphicModel`
3. Check that migrations have been applied for polymorphic fields
4. Clear the schema cache if changes don't appear: `python manage.py clear_schema_cache`

## Related Documentation

- [Django Polymorphic Documentation](https://django-polymorphic.readthedocs.io/)
- [Model Inheritance](inheritance.md)
- [Field Configuration](../configuration-guide.md#field-configuration)