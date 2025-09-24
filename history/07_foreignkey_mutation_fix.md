# ForeignKey Mutation Fix

**Date:** September 24, 2025  
**Issue:** ForeignKey fields in mutations were not properly handling ID values passed as strings  
**Status:** ✅ Resolved

## Problem Description

When executing GraphQL mutations with ForeignKey fields, passing ID values as strings (e.g., `author: "2"`) resulted in the following error:

```
"errors": [
    "Failed to create Post: Cannot assign \"'2'\": \"Post.author\" must be a \"User\" instance."
]
```

The mutation generator was not properly converting string/integer ID values to actual model instances for ForeignKey relationships.

## Root Cause

In the `generate_create_mutation` method in <mcfile name="mutations.py" path="django_graphql_auto/generators/mutations.py"></mcfile>, the code only handled nested object creation for ForeignKey fields when the value was a dictionary:

```python
if isinstance(field, (models.ForeignKey, models.OneToOneField)) and isinstance(value, dict):
    # Only handled dict values for nested creation
```

It did not handle the common case where ForeignKey fields receive ID values as strings or integers.

## Solution

Enhanced the ForeignKey handling logic in the `mutate` method to support both nested object creation and ID-based references:

```python
if isinstance(field, (models.ForeignKey, models.OneToOneField)):
    if isinstance(value, dict):
        # Create new related object from nested data
        related_model = field.related_model
        related_fields[field_name] = related_model.objects.create(**value)
        input[field_name] = related_fields[field_name]
    elif isinstance(value, (str, int)):
        # Fetch existing related object by ID
        related_model = field.related_model
        try:
            related_instance = related_model.objects.get(pk=value)
            input[field_name] = related_instance
        except related_model.DoesNotExist:
            raise ValidationError(f"{related_model.__name__} with id '{value}' does not exist")
```

## Key Changes

1. **Extended ForeignKey Handling**: Added support for string/integer ID values in addition to nested object creation
2. **Proper Instance Resolution**: Convert ID values to actual model instances using `related_model.objects.get(pk=value)`
3. **Error Handling**: Added proper error handling for non-existent related objects with descriptive error messages
4. **Backward Compatibility**: Maintained existing nested object creation functionality

## Testing Results

The fix was verified with a test mutation:

```graphql
mutation createPost {
    create_post(input: {
        title: "Test Post",
        slug: "test-post", 
        content: "Test content",
        author: "3",
        category: "2"
    }) {
        ok
        errors
        object {
            id
            title
            author {
                username
            }
            category {
                name
            }
        }
    }
}
```

**Result:** ✅ Success
```json
{
    "create_post": {
        "ok": true,
        "errors": null,
        "object": {
            "id": "UG9zdFR5cGU6Mg==",
            "title": "Test Post",
            "author": {
                "username": "testuser"
            },
            "category": {
                "name": "Test Category"
            }
        }
    }
}
```

## Benefits

1. **Improved Usability**: ForeignKey fields now accept both ID values and nested objects
2. **Better Error Messages**: Clear error messages when referenced objects don't exist
3. **Consistent Behavior**: Aligns with GraphQL best practices for relationship handling
4. **Backward Compatibility**: Existing nested object creation continues to work

## Modified Files

- <mcfile name="mutations.py" path="django_graphql_auto/generators/mutations.py"></mcfile>: Enhanced ForeignKey handling in `generate_create_mutation` method

## Impact

This fix resolves a critical usability issue where users couldn't easily reference existing related objects in mutations using their IDs, which is the most common use case in GraphQL APIs.