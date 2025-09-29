# Error Handling

The Django GraphQL Auto-Generation System provides comprehensive error handling with automatic field extraction, user-friendly error messages, and consistent error formats across all operations.

## 🎯 Overview

The error handling system automatically:
- ✅ **Field Extraction**: Identifies which field caused the error
- ✅ **Database Constraints**: Handles UNIQUE, NOT NULL, and FOREIGN KEY violations
- ✅ **Validation Errors**: Processes Django model validation errors
- ✅ **User-Friendly Messages**: Converts technical errors to readable messages
- ✅ **Consistent Format**: Standardized error response structure

## 📋 Table of Contents

- [Error Response Format](#error-response-format)
- [Field Extraction](#field-extraction)
- [Database Constraint Errors](#database-constraint-errors)
- [Validation Errors](#validation-errors)
- [Foreign Key Errors](#foreign-key-errors)
- [Error Types](#error-types)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## 🔧 Error Response Format

All mutation errors follow a consistent structure:

```graphql
type MutationError {
  field: String      # Field name where error occurred (null for general errors)
  message: String!   # Human-readable error message
}

type CreatePostMutation {
  ok: Boolean!
  post: PostType
  errors: [MutationError!]!
}
```

### Example Response

```json
{
  "data": {
    "createPost": {
      "ok": false,
      "post": null,
      "errors": [
        {
          "field": "title",
          "message": "This field is required."
        },
        {
          "field": "email",
          "message": "A User with this email already exists."
        }
      ]
    }
  }
}
```

## 🎯 Field Extraction

The system automatically extracts field names from various error sources:

### 1. Django ValidationError

```python
# Django model validation
def clean(self):
    if not self.title:
        raise ValidationError({'title': 'Title is required'})
```

**GraphQL Response:**
```json
{
  "field": "title",
  "message": "Title is required"
}
```

### 2. Database Constraint Violations

```sql
-- Database error: UNIQUE constraint failed: app_user.email
```

**GraphQL Response:**
```json
{
  "field": "email", 
  "message": "A User with this email already exists."
}
```

### 3. Foreign Key Validation

```python
# Error: "Category with id '999' does not exist"
```

**GraphQL Response:**
```json
{
  "field": "category",
  "message": "Invalid category: The selected category does not exist."
}
```

## 🗄️ Database Constraint Errors

### UNIQUE Constraint Violations

Automatically detects and extracts field names from UNIQUE constraint failures:

```graphql
mutation {
  createUser(input: {
    email: "existing@example.com"
    username: "duplicate_user"
  }) {
    ok
    user { id }
    errors {
      field
      message
    }
  }
}
```

**Response:**
```json
{
  "data": {
    "createUser": {
      "ok": false,
      "user": null,
      "errors": [
        {
          "field": "email",
          "message": "A User with this email already exists."
        }
      ]
    }
  }
}
```

### NOT NULL Constraint Violations

Handles required field violations:

```sql
-- Database error: NOT NULL constraint failed: app_post.title
```

**GraphQL Response:**
```json
{
  "field": "title",
  "message": "This field is required."
}
```

### FOREIGN KEY Constraint Violations

Handles invalid foreign key references:

```sql
-- Database error: FOREIGN KEY constraint failed
```

**GraphQL Response:**
```json
{
  "field": null,
  "message": "Invalid reference to related object."
}
```

## ✅ Validation Errors

### Django Model Validation

```python
class Post(models.Model):
    title = models.CharField(max_length=100)
    
    def clean(self):
        if len(self.title) < 3:
            raise ValidationError({
                'title': 'Title must be at least 3 characters long'
            })
```

**GraphQL Response:**
```json
{
  "field": "title",
  "message": "Title must be at least 3 characters long"
}
```

### Form Validation

```python
class PostForm(forms.ModelForm):
    def clean_title(self):
        title = self.cleaned_data['title']
        if 'spam' in title.lower():
            raise ValidationError('Title cannot contain spam')
        return title
```

**GraphQL Response:**
```json
{
  "field": "title", 
  "message": "Title cannot contain spam"
}
```

## 🔗 Foreign Key Errors

The system intelligently maps foreign key errors to the correct field:

### Model Relationships

```python
class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
```

### Error Mapping

```graphql
mutation {
  createPost(input: {
    title: "Test Post"
    author: "999"      # Non-existent user
    category: "888"    # Non-existent category
  }) {
    ok
    post { id }
    errors {
      field
      message
    }
  }
}
```

**Response:**
```json
{
  "data": {
    "createPost": {
      "ok": false,
      "post": null,
      "errors": [
        {
          "field": "author",
          "message": "Invalid author: The selected user does not exist."
        },
        {
          "field": "category", 
          "message": "Invalid category: The selected category does not exist."
        }
      ]
    }
  }
}
```

## 📊 Error Types

### 1. Field-Specific Errors

Errors that can be attributed to a specific field:

```json
{
  "field": "email",
  "message": "Enter a valid email address."
}
```

### 2. General Errors

Errors that affect the entire operation:

```json
{
  "field": null,
  "message": "You don't have permission to perform this action."
}
```

### 3. Multiple Field Errors

Multiple validation errors in a single response:

```json
{
  "errors": [
    {
      "field": "title",
      "message": "This field is required."
    },
    {
      "field": "email",
      "message": "A User with this email already exists."
    },
    {
      "field": "password",
      "message": "Password must be at least 8 characters long."
    }
  ]
}
```

## 🎯 Best Practices

### 1. Frontend Error Handling

```javascript
// React example
const handleMutation = async (input) => {
  const result = await createPost({ variables: { input } });
  
  if (!result.data.createPost.ok) {
    const errors = result.data.createPost.errors;
    
    // Handle field-specific errors
    errors.forEach(error => {
      if (error.field) {
        setFieldError(error.field, error.message);
      } else {
        setGeneralError(error.message);
      }
    });
  }
};
```

### 2. Error Display

```jsx
// Display field-specific errors
{errors.map(error => (
  <div key={error.field || 'general'} className="error">
    {error.field && <strong>{error.field}:</strong>} {error.message}
  </div>
))}
```

### 3. Form Validation

```javascript
// Validate before submission
const validateForm = (data) => {
  const errors = [];
  
  if (!data.title) {
    errors.push({ field: 'title', message: 'Title is required' });
  }
  
  if (!data.email || !isValidEmail(data.email)) {
    errors.push({ field: 'email', message: 'Valid email is required' });
  }
  
  return errors;
};
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Field Not Extracted

**Problem:** Error shows `field: null` when it should show a specific field.

**Solution:** Check if the error message contains recognizable patterns:
- Database constraint format: `UNIQUE constraint failed: table.field`
- Foreign key format: `ModelName with id 'X' does not exist`

#### 2. Generic Error Messages

**Problem:** Error messages are too technical.

**Solution:** The system automatically converts technical errors to user-friendly messages:
- `UNIQUE constraint failed` → `"A {Model} with this {field} already exists."`
- `NOT NULL constraint failed` → `"This field is required."`

#### 3. Missing Field Information

**Problem:** Custom validation errors don't include field information.

**Solution:** Use Django's ValidationError with field mapping:

```python
# Good
raise ValidationError({'field_name': 'Error message'})

# Bad  
raise ValidationError('Generic error message')
```

### Debug Mode

Enable debug logging to see error processing:

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
            'level': 'INFO',
        },
    },
}
```

**Debug Output:**
```
INFO CreateMutation exception: IntegrityError: UNIQUE constraint failed: app_user.email
INFO Extracted field name: email
INFO CreateMutation exception: ValidationError: Category with id '999' does not exist
INFO Extracted field name from foreign key error: category
```

## 🚀 Advanced Usage

### Custom Error Processing

```python
from django_graphql_auto.generators.mutations import CreateMutation

class CustomCreateMutation(CreateMutation):
    @classmethod
    def process_error(cls, error, model):
        """Custom error processing logic"""
        if "custom_constraint" in str(error):
            return {
                'field': 'custom_field',
                'message': 'Custom error message'
            }
        return super().process_error(error, model)
```

### Error Middleware

```python
class ErrorMiddleware:
    def resolve(self, next, root, info, **args):
        try:
            return next(root, info, **args)
        except Exception as e:
            # Custom error handling
            logger.error(f"GraphQL Error: {e}")
            raise
```

## 📚 Related Documentation

- [API Reference - Error Handling](../api/graphql-api-reference.md#error-handling)
- [Basic Usage - Error Handling](../usage/basic-usage.md#error-handling)
- [Troubleshooting Guide](../development/troubleshooting.md)
- [Validation Examples](../examples/validation-examples.md)

---

This comprehensive error handling system ensures that your GraphQL API provides clear, actionable error messages that help both developers and end-users understand and resolve issues quickly.