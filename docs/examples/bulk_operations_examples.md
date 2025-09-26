# Bulk Operations Guide

This guide explains how to enable and use bulk operations in the Django GraphQL Auto-Generation Library.

## 🚀 Enabling Bulk Operations

### 1. Configuration in Django Settings

Add the following configuration to your Django settings:

```python
DJANGO_GRAPHQL_AUTO = {
    'MUTATION_SETTINGS': {
        'enable_bulk_operations': True,  # Enable bulk create, update, delete operations
        'bulk_batch_size': 100,  # Maximum number of items in bulk operations (default: 100)
        # ... other settings
    }
}
```

### 2. Available Bulk Operations

Once enabled, the following bulk mutations are automatically generated for each model:

- `bulk_create_{model_name}` - Create multiple instances
- `bulk_update_{model_name}` - Update multiple instances  
- `bulk_delete_{model_name}` - Delete multiple instances

## 📝 Usage Examples

### Bulk Create Posts

```graphql
mutation BulkCreatePosts {
  bulkCreatePost(inputs: [
    {
      title: "First Post"
      content: "Content of first post"
      status: "draft"
      authorId: 1
      categoryId: 1
    }
    {
      title: "Second Post"
      content: "Content of second post"
      status: "published"
      authorId: 1
      categoryId: 2
    }
  ]) {
    ok
    objects {
      id
      title
      status
    }
    errors
  }
}
```

### Bulk Update Posts

```graphql
mutation BulkUpdatePosts {
  bulkUpdatePost(inputs: [
    {
      id: "1"
      data: {
        status: "published"
        title: "Updated First Post"
      }
    }
    {
      id: "2"
      data: {
        status: "archived"
      }
    }
  ]) {
    ok
    objects {
      id
      title
      status
    }
    errors
  }
}
```

### Bulk Delete Posts

```graphql
mutation BulkDeletePosts {
  bulkDeletePost(ids: ["1", "2", "3"]) {
    ok
    objects {
      id
      title
    }
    errors
  }
}
```

## 🔧 Configuration Options

### Batch Size Limit

Control the maximum number of items that can be processed in a single bulk operation:

```python
DJANGO_GRAPHQL_AUTO = {
    'MUTATION_SETTINGS': {
        'enable_bulk_operations': True,
        'bulk_batch_size': 50,  # Limit to 50 items per bulk operation
    }
}
```

### Per-Model Configuration

You can enable/disable bulk operations for specific models by customizing the mutation generator settings in your schema configuration.

## ⚡ Performance Features

### Transaction Safety
- All bulk operations are wrapped in database transactions
- If any item fails, the entire operation is rolled back
- Ensures data consistency across all operations

### Error Handling
- Detailed error messages for each failed item
- Partial success handling where applicable
- Validation errors are reported clearly

### Optimization
- Uses Django's `bulk_create()` for efficient database operations
- Minimizes database queries through batching
- Automatic query optimization for large datasets

## 🛡️ Security Considerations

### Validation
- All input data is validated before processing
- Model-level validation is enforced
- Custom validation rules are respected

### Permissions
- Standard Django permissions apply to bulk operations
- User authentication is required
- Model-level permissions are checked

### Rate Limiting
- Batch size limits prevent resource exhaustion
- Transaction timeouts prevent long-running operations
- Memory usage is controlled through batching

## 📊 Response Format

All bulk operations return a standardized response:

```graphql
type BulkMutationResponse {
  ok: Boolean!           # Overall success status
  objects: [ModelType]   # Successfully processed objects
  errors: [String]       # List of error messages
}
```

## 🔍 Monitoring and Debugging

### Logging
Bulk operations are logged with detailed information:
- Number of items processed
- Execution time
- Error details
- Transaction status

### GraphiQL Integration
- Full schema introspection support
- Auto-completion for bulk mutations
- Built-in documentation for all operations

## 🎯 Best Practices

1. **Batch Size**: Keep batch sizes reasonable (50-100 items) for optimal performance
2. **Validation**: Validate data on the client side before sending bulk requests
3. **Error Handling**: Always check the `ok` field and `errors` array in responses
4. **Transactions**: Rely on automatic transaction management for data consistency
5. **Testing**: Test bulk operations with various data scenarios and edge cases

## 🚨 Troubleshooting

### Common Issues

1. **Batch Size Exceeded**: Reduce the number of items in your bulk operation
2. **Validation Errors**: Check individual item data for validation issues
3. **Permission Denied**: Ensure the user has appropriate model permissions
4. **Transaction Timeout**: Reduce batch size for complex operations

### Debug Mode
Enable debug logging to see detailed bulk operation information:

```python
LOGGING = {
    'loggers': {
        'django_graphql_auto': {
            'level': 'DEBUG',
        },
    },
}
```