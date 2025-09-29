# Fix Documentation: NOT NULL Constraint Failed Error

## Problem Description

The Django GraphQL Auto library was encountering a `NOT NULL constraint failed: test_app_comment.author_id` error when creating nested comments through GraphQL mutations. This occurred specifically when using the `update_post` mutation with `nested_comments` that included an `author` field.

## Root Cause Analysis

The issue was located in the `handle_nested_create` method within `django_graphql_auto/generators/nested_operations.py`. The method was not properly handling foreign key fields when the value was already a model instance (as opposed to a string/integer ID).

### Specific Issue

In the `handle_nested_create` method, when processing foreign key fields:

1. The method correctly identified foreign key fields and their values
2. When the value was a string or integer ID, it properly retrieved the related instance and added it to `regular_fields`
3. **However, when the value was already a model instance with a `pk` attribute, it was not being added to `regular_fields`**
4. This caused the foreign key field to be missing during the actual database insert operation, resulting in the NOT NULL constraint violation

### Code Location

File: `django_graphql_auto/generators/nested_operations.py`
Method: `handle_nested_create` (around lines 135-150)

## Solution Implemented

Added explicit handling for foreign key values that are already model instances:

```python
# In handle_nested_create method, within the foreign key processing loop:
if hasattr(value, 'pk') and value.pk:
    # Value is already a model instance with a primary key
    regular_fields[field_name] = value
elif isinstance(value, dict):
    # ... existing nested create/update logic
elif isinstance(value, (str, int)):
    # ... existing ID lookup logic
```

### Complete Fix

The fix ensures that when a foreign key field value is already a model instance (which happens during nested operations), it gets properly assigned to the `regular_fields` dictionary that is used for the database insert operation.

## Testing

The fix was verified with multiple test scenarios:

1. **Nested Comment Creation**: Creating comments within post updates ✓
2. **Multiple Foreign Key Fields**: Handling multiple foreign key relationships ✓  
3. **Direct Comment Creation**: Ensuring non-nested operations still work ✓
4. **Nested Post Creation**: Creating posts with nested comments ✓

## Files Modified

- `django_graphql_auto/generators/nested_operations.py`: Added missing foreign key instance handling

## Impact

- **Positive**: Fixes the NOT NULL constraint error for nested operations with foreign key fields
- **Risk**: Minimal - the change only adds a missing case that should have been handled originally
- **Backward Compatibility**: Fully maintained - existing functionality is unchanged

## Prevention

To prevent similar issues in the future:

1. Ensure comprehensive test coverage for all foreign key value types (instances, IDs, nested objects)
2. Add explicit handling for all possible value types in foreign key processing logic
3. Include integration tests that cover nested operations with various field combinations

## Related Issues

This fix resolves the core issue where nested GraphQL mutations would fail with NOT NULL constraint errors when foreign key fields were passed as model instances rather than IDs.