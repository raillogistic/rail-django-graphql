# Bulk Operations

Bulk operations enable efficient handling of multiple records in a single GraphQL mutation, providing significant performance improvements for batch processing scenarios. This feature supports bulk create, update, and delete operations with transaction safety and comprehensive error handling.

## 📚 Table of Contents

- [Overview](#overview)
- [Configuration](#configuration)
- [Available Operations](#available-operations)
- [Usage Examples](#usage-examples)
- [Performance Features](#performance-features)
- [Error Handling](#error-handling)
- [Security Considerations](#security-considerations)
- [Best Practices](#best-practices)
- [Advanced Patterns](#advanced-patterns)
- [Troubleshooting](#troubleshooting)

## 🔍 Overview

Bulk operations allow you to perform create, update, and delete operations on multiple records simultaneously, reducing the number of database queries and improving overall performance.

### Key Features

- ✅ **Bulk Create**: Create multiple records in a single operation
- ✅ **Bulk Update**: Update multiple records with different values
- ✅ **Bulk Delete**: Delete multiple records by ID
- ✅ **Transaction Safety**: All operations are wrapped in database transactions
- ✅ **Batch Processing**: Configurable batch sizes for large datasets
- ✅ **Error Handling**: Comprehensive error reporting with partial success support
- ✅ **Performance Optimization**: Optimized database queries and memory usage
- ✅ **French Verbose Names**: Support for French field names via verbose_name

## ⚙️ Configuration

Enable bulk operations in your Django settings:

```python
# settings.py
rail_django_graphql = {
    'APPS': ['your_app'],
    'MUTATION_SETTINGS': {
        'enable_bulk_operations': True,   # Enable bulk operations
        'bulk_batch_size': 100,          # Records per batch
        'bulk_max_objects': 1000,        # Maximum objects per operation
        'bulk_transaction_timeout': 30,   # Transaction timeout in seconds
    }
}
```

### Configuration Options

| Option                     | Type   | Default | Description                           |
| -------------------------- | ------ | ------- | ------------------------------------- |
| `enable_bulk_operations`   | `bool` | `False` | Enable/disable bulk operations        |
| `bulk_batch_size`          | `int`  | `100`   | Number of records processed per batch |
| `bulk_max_objects`         | `int`  | `1000`  | Maximum objects allowed per operation |
| `bulk_transaction_timeout` | `int`  | `30`    | Transaction timeout in seconds        |

## 🔄 Available Operations

### Bulk Create

Create multiple records of the same model type:

```graphql
mutation BulkCreatePosts($input: BulkCreatePostInput!) {
  bulkCreatePost(input: $input) {
    ok
    objects {
      id
      title
      author {
        username
      }
    }
    errors
  }
}
```

### Bulk Update

Update multiple existing records:

```graphql
mutation BulkUpdatePosts($input: BulkUpdatePostInput!) {
  bulkUpdatePost(input: $input) {
    ok
    objects {
      id
      title
      published
    }
    errors
  }
}
```

### Bulk Delete

Delete multiple records by ID:

```graphql
mutation BulkDeletePosts($input: BulkDeletePostInput!) {
  bulkDeletePost(input: $input) {
    ok
    deletedIds
    errors
  }
}
```

## 📝 Usage Examples

### Bulk Create Example

```python
# models.py
class Article(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre de l'article")
    content = models.TextField(verbose_name="Contenu de l'article")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Auteur")
    published = models.BooleanField(default=False, verbose_name="Publié")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
```

```graphql
mutation BulkCreateArticles($input: BulkCreateArticleInput!) {
  bulkCreateArticle(input: $input) {
    ok
    objects {
      id
      title
      author {
        username
      }
      published
    }
    errors
  }
}
```

Variables:

```json
{
  "input": {
    "objects": [
      {
        "title": "Introduction to GraphQL",
        "content": "GraphQL is a query language for APIs...",
        "authorId": 1,
        "published": false
      },
      {
        "title": "Advanced Django Patterns",
        "content": "In this article, we explore...",
        "authorId": 2,
        "published": true
      },
      {
        "title": "Performance Optimization",
        "content": "Learn how to optimize...",
        "authorId": 1,
        "published": false
      }
    ]
  }
}
```

### Bulk Update Example

```graphql
mutation BulkUpdateArticles($input: BulkUpdateArticleInput!) {
  bulkUpdateArticle(input: $input) {
    ok
    objects {
      id
      title
      published
    }
    errors
  }
}
```

Variables:

```json
{
  "input": {
    "objects": [
      {
        "id": "1",
        "published": true
      },
      {
        "id": "2",
        "title": "Updated Title",
        "published": true
      },
      {
        "id": "3",
        "published": false
      }
    ]
  }
}
```

### Bulk Delete Example

```graphql
mutation BulkDeleteArticles($input: BulkDeleteArticleInput!) {
  bulkDeleteArticle(input: $input) {
    ok
    deletedIds
    errors
  }
}
```

Variables:

```json
{
  "input": {
    "ids": ["10", "11", "12", "13"]
  }
}
```

## ⚡ Performance Features

### Batch Processing

Large datasets are automatically processed in batches to prevent memory issues:

```python
# Automatically processes 1000 records in 10 batches of 100
{
  "input": {
    "objects": [
      # ... 1000 objects
    ]
  }
}
```

### Optimized Database Queries

- **Bulk Create**: Uses `bulk_create()` for efficient insertion
- **Bulk Update**: Uses `bulk_update()` for efficient updates
- **Bulk Delete**: Uses `filter().delete()` for efficient deletion

### Memory Management

- Streaming processing for large datasets
- Automatic garbage collection between batches
- Memory usage monitoring and limits

## ⚠️ Error Handling

### Partial Success Support

Bulk operations support partial success, where some records succeed while others fail:

```json
{
  "data": {
    "bulkCreateArticle": {
      "ok": false,
      "objects": [
        {
          "id": "1",
          "title": "Successfully Created Article"
        },
        null // Failed to create
      ],
      "errors": [
        "Object 2: Title is required",
        "Object 2: Author does not exist"
      ]
    }
  }
}
```

### Validation Errors

Each object is validated individually:

```python
# Example validation error response
{
  "ok": false,
  "objects": [],
  "errors": [
    "Object 1: Title cannot be empty",
    "Object 3: Invalid author ID: 999",
    "Object 5: Content exceeds maximum length"
  ]
}
```

### Transaction Rollback

Failed operations trigger automatic rollback:

```python
# If any critical error occurs, entire batch is rolled back
{
  "ok": false,
  "objects": [],
  "errors": ["Transaction failed: Database constraint violation"]
}
```

## 🔒 Security Considerations

### Permission Checks

Bulk operations respect Django model permissions:

```python
# Each object creation/update/delete is checked for permissions
class ArticlePermissions:
    def has_add_permission(self, request):
        return request.user.has_perm('blog.add_article')

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm('blog.change_article')
```

### Rate Limiting

Implement rate limiting for bulk operations:

```python
# settings.py
rail_django_graphql = {
    'MUTATION_SETTINGS': {
        'bulk_rate_limit': {
            'max_operations_per_minute': 10,
            'max_objects_per_hour': 10000,
        }
    }
}
```

### Input Validation

All input data is validated before processing:

```python
# Automatic validation includes:
# - Required field checks
# - Data type validation
# - Foreign key existence
# - Custom model validation
```

## 🎯 Best Practices

### 1. Optimal Batch Sizes

Choose appropriate batch sizes based on your data:

```python
# For simple models with few fields
'bulk_batch_size': 500

# For complex models with many relationships
'bulk_batch_size': 50

# For models with file uploads
'bulk_batch_size': 10
```

### 2. Error Handling Strategy

Implement comprehensive error handling:

```javascript
// Frontend error handling
const handleBulkCreate = async (objects) => {
  try {
    const result = await bulkCreateArticles({ objects });

    if (result.ok) {
      console.log("All objects created successfully");
    } else {
      // Handle partial success
      const successful = result.objects.filter((obj) => obj !== null);
      console.log(`${successful.length}/${objects.length} objects created`);
      console.error("Errors:", result.errors);
    }
  } catch (error) {
    console.error("Network or GraphQL error:", error);
  }
};
```

### 3. Progress Tracking

For large operations, implement progress tracking:

```python
# Custom mutation with progress tracking
class BulkCreateWithProgress(graphene.Mutation):
    class Arguments:
        input = BulkCreateInput(required=True)

    ok = graphene.Boolean()
    progress = graphene.Int()  # Percentage complete
    objects = graphene.List(ObjectType)
    errors = graphene.List(graphene.String)
```

### 4. Data Preparation

Prepare data efficiently before bulk operations:

```javascript
// Prepare data for bulk create
const prepareArticlesForBulk = (articles) => {
  return articles.map((article) => ({
    title: article.title.trim(),
    content: article.content,
    authorId: article.author.id,
    published: article.published || false,
    // Ensure all required fields are present
  }));
};
```

## 🚀 Advanced Patterns

### Conditional Bulk Operations

Implement conditional logic in bulk operations:

```python
# Custom bulk mutation with conditions
def bulk_create_with_conditions(objects):
    valid_objects = []
    errors = []

    for i, obj_data in enumerate(objects):
        if should_create_object(obj_data):
            valid_objects.append(obj_data)
        else:
            errors.append(f"Object {i+1}: Condition not met")

    return bulk_create(valid_objects), errors
```

### Bulk Operations with Relationships

Handle related objects in bulk operations:

```graphql
mutation BulkCreatePostsWithTags($input: BulkCreatePostInput!) {
  bulkCreatePost(input: $input) {
    ok
    objects {
      id
      title
      tags {
        name
      }
    }
    errors
  }
}
```

Variables with relationships:

```json
{
  "input": {
    "objects": [
      {
        "title": "Post with Tags",
        "content": "Content...",
        "authorId": 1,
        "tagIds": [1, 2, 3] // Many-to-many relationships
      }
    ]
  }
}
```

### Bulk Operations with File Uploads

Handle file uploads in bulk operations:

```python
# Model with file field
class Document(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre du document")
    file = models.FileField(upload_to='documents/', verbose_name="Fichier")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Auteur")
```

```graphql
mutation BulkCreateDocuments($input: BulkCreateDocumentInput!) {
  bulkCreateDocument(input: $input) {
    ok
    objects {
      id
      title
      file
    }
    errors
  }
}
```

## 🔍 Troubleshooting

### Common Issues

1. **Memory errors with large datasets**

   - Reduce `bulk_batch_size`
   - Implement streaming for very large datasets
   - Monitor memory usage

2. **Transaction timeout errors**

   - Increase `bulk_transaction_timeout`
   - Reduce batch size
   - Optimize database queries

3. **Partial success not working**
   - Check error handling configuration
   - Verify validation logic
   - Review transaction settings

### Performance Monitoring

Monitor bulk operation performance:

```python
# Add logging for performance monitoring
import logging
import time

logger = logging.getLogger('bulk_operations')

def monitor_bulk_operation(operation_name, object_count):
    start_time = time.time()

    def log_completion():
        duration = time.time() - start_time
        logger.info(f"{operation_name}: {object_count} objects in {duration:.2f}s")

    return log_completion
```

### Debug Mode

Enable detailed logging for troubleshooting:

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
        'rail_django_graphql.generators.mutations': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## 📊 Performance Benchmarks

Typical performance improvements with bulk operations:

| Operation           | Individual Mutations | Bulk Operation | Improvement |
| ------------------- | -------------------- | -------------- | ----------- |
| Create 100 records  | ~2000ms              | ~200ms         | 10x faster  |
| Update 500 records  | ~5000ms              | ~300ms         | 16x faster  |
| Delete 1000 records | ~8000ms              | ~100ms         | 80x faster  |

_Benchmarks may vary based on model complexity and database configuration._

This comprehensive guide covers all aspects of bulk operations in the Django GraphQL Auto-Generation Library. Bulk operations provide significant performance improvements for batch processing while maintaining data integrity and comprehensive error handling.
