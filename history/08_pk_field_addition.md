# Primary Key (pk) Field Addition

**Date:** 2025-01-24  
**Status:** ✅ Completed  
**Type:** Feature Enhancement

## Overview

Added a `pk` field to all GraphQL object types that resolves to the Django model's primary key field. This provides a consistent way to access the primary key value regardless of the actual primary key field name in the Django model.

## Problem Description

Users needed a consistent way to access the primary key of Django models through GraphQL queries. While Django models can have different primary key field names (e.g., `id`, `uuid`, custom fields), there was no standardized way to access the primary key value in GraphQL.

## Solution

Enhanced the `TypeGenerator.generate_object_type()` method in <mcfile name="types.py" path="django_graphql_auto/generators/types.py"></mcfile> to automatically add a `pk` field to all generated GraphQL object types.

### Key Changes

1. **Added pk field to object types**: Every GraphQL object type now includes a `pk` field of type `graphene.ID`
2. **Dynamic primary key resolution**: The `resolve_pk` method dynamically resolves to the actual primary key field of the Django model
3. **Consistent API**: Provides a uniform way to access primary keys across all models

### Implementation Details

```python
# Added to generate_object_type method
type_attrs['pk'] = graphene.ID(description="Primary key of the model")
type_attrs['resolve_pk'] = lambda self, info: getattr(self, self._meta.pk.name)
```

The resolver uses `self._meta.pk.name` to dynamically get the primary key field name and return its value.

## Testing Results

✅ **Schema Introspection Test**: Confirmed `pk` field is present in all GraphQL object types:
- LogEntryType ✓
- UserType ✓  
- GroupType ✓
- PermissionType ✓
- ContentTypeType ✓
- PostType ✓
- CategoryType ✓
- TagType ✓
- CommentType ✓
- SessionType ✓

✅ **Query Execution Test**: Successfully executed queries with `pk` field:
```graphql
query {
  posts {
    pk      # Returns: "3"
    id      # Returns: "UG9zdFR5cGU6Mw=="
    title   # Returns: "title"
  }
}
```

## Benefits

1. **Consistency**: Uniform access to primary keys across all models
2. **Flexibility**: Works with any Django primary key field type (AutoField, UUIDField, etc.)
3. **Backward Compatibility**: Existing queries continue to work unchanged
4. **Developer Experience**: Simplified primary key access in GraphQL queries

## Files Modified

- <mcfile name="types.py" path="django_graphql_auto/generators/types.py"></mcfile>: Added pk field generation logic

## Usage Examples

```graphql
# Basic query with pk field
query {
  posts {
    pk
    title
  }
}

# Using pk for mutations
mutation {
  updatePost(pk: "3", input: { title: "New Title" }) {
    post {
      pk
      title
    }
  }
}

# Filtering by pk (if supported)
query {
  post(pk: "3") {
    pk
    title
    content
  }
}
```

## Notes

- The `pk` field returns the same value as the model's actual primary key field but provides a consistent interface
- This enhancement is automatically applied to all existing and future GraphQL object types
- The field is of type `graphene.ID` to maintain GraphQL best practices for identifier fields