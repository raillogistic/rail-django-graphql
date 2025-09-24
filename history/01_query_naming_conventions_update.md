# Chat History 01: Query Naming Conventions Update

## Summary
Updated GraphQL query naming conventions from `_list` and `_paginated` suffixes to more intuitive naming patterns.

## Key Changes Made
- **Query Naming Convention Changes:**
  - `model_name_list` → `model_names` (plural form with 's' suffix)
  - `model_name_paginated` → `model_name_pages`

## Files Modified
1. **schema.py** - Updated query field generation and removal logic
2. **files.py** - Modified query name generation in code templates
3. **queries.py** - Updated query generation methods

## Technical Details
- Modified `_query_fields` generation in SchemaBuilder
- Updated `remove_model` method to handle new naming conventions
- Changed code generation templates to use new naming patterns

## Impact
- More intuitive and consistent query naming
- Better alignment with GraphQL best practices
- Improved developer experience with clearer query names