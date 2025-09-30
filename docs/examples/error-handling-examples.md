# Error Handling Examples

This document provides comprehensive examples of error handling in the Django GraphQL Auto-Generation System, showcasing the enhanced field-specific error extraction capabilities.

## 📚 Table of Contents

- [Overview](#overview)
- [Validation Error Examples](#validation-error-examples)
- [Database Constraint Error Examples](#database-constraint-error-examples)
- [Foreign Key Error Examples](#foreign-key-error-examples)
- [Custom Error Handling](#custom-error-handling)
- [Testing Error Scenarios](#testing-error-scenarios)
- [Best Practices](#best-practices)

## 🔍 Overview

The enhanced error handling system provides detailed field-specific information for better debugging and user experience. Each error includes:

- **field**: The specific field that caused the error
- **message**: Human-readable error message (in French)
- **code**: Error code for programmatic handling

## ✅ Validation Error Examples

### Basic Field Validation

```python
# models.py
class User(models.Model):
    username = models.CharField(max_length=50, verbose_name="Nom d'utilisateur")
    email = models.EmailField(verbose_name="Adresse email")
    age = models.IntegerField(verbose_name="Âge")

    def clean(self):
        if self.age and self.age < 18:
            raise ValidationError({
                'age': "L'utilisateur doit être majeur"
            })
```

**GraphQL Mutation:**

```graphql
mutation CreateUser($input: CreateUserInput!) {
  createUser(input: $input) {
    ok
    user {
      id
      username
      email
    }
    errors {
      field
      message
      code
    }
  }
}
```

**Test Cases:**

#### 1. Empty Required Field

```json
// Input
{
  "input": {
    "username": "",
    "email": "user@example.com",
    "age": 25
  }
}

// Response
{
  "data": {
    "createUser": {
      "ok": false,
      "user": null,
      "errors": [{
        "field": "username",
        "message": "Ce champ ne peut pas être vide.",
        "code": "VALIDATION_ERROR"
      }]
    }
  }
}
```

#### 2. Invalid Email Format

```json
// Input
{
  "input": {
    "username": "testuser",
    "email": "invalid-email",
    "age": 25
  }
}

// Response
{
  "data": {
    "createUser": {
      "ok": false,
      "user": null,
      "errors": [{
        "field": "email",
        "message": "Saisissez une adresse de courriel valide.",
        "code": "VALIDATION_ERROR"
      }]
    }
  }
}
```

#### 3. Custom Validation Error

```json
// Input
{
  "input": {
    "username": "testuser",
    "email": "user@example.com",
    "age": 16
  }
}

// Response
{
  "data": {
    "createUser": {
      "ok": false,
      "user": null,
      "errors": [{
        "field": "age",
        "message": "L'utilisateur doit être majeur",
        "code": "VALIDATION_ERROR"
      }]
    }
  }
}
```

### Multiple Field Validation Errors

```python
# models.py
class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre")
    content = models.TextField(verbose_name="Contenu")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Catégorie")

    def clean(self):
        errors = {}

        if not self.title or len(self.title.strip()) < 5:
            errors['title'] = "Le titre doit contenir au moins 5 caractères"

        if not self.content or len(self.content.strip()) < 20:
            errors['content'] = "Le contenu doit contenir au moins 20 caractères"

        if errors:
            raise ValidationError(errors)
```

**Test Case:**

```json
// Input
{
  "input": {
    "title": "Hi",
    "content": "Short",
    "categoryId": 1
  }
}

// Response
{
  "data": {
    "createPost": {
      "ok": false,
      "post": null,
      "errors": [
        {
          "field": "title",
          "message": "Le titre doit contenir au moins 5 caractères",
          "code": "VALIDATION_ERROR"
        },
        {
          "field": "content",
          "message": "Le contenu doit contenir au moins 20 caractères",
          "code": "VALIDATION_ERROR"
        }
      ]
    }
  }
}
```

## 🔒 Database Constraint Error Examples

### Unique Constraint Violations

```python
# models.py
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom du tag")
    slug = models.SlugField(unique=True, verbose_name="Slug")
```

**Test Cases:**

#### 1. Duplicate Name

```json
// Input (when "python" tag already exists)
{
  "input": {
    "name": "python",
    "slug": "python-new"
  }
}

// Response
{
  "data": {
    "createTag": {
      "ok": false,
      "tag": null,
      "errors": [{
        "field": "name",
        "message": "Cette valeur existe déjà",
        "code": "DUPLICATE_ENTRY"
      }]
    }
  }
}
```

#### 2. Duplicate Slug

```json
// Input (when "django" slug already exists)
{
  "input": {
    "name": "Django Framework",
    "slug": "django"
  }
}

// Response
{
  "data": {
    "createTag": {
      "ok": false,
      "tag": null,
      "errors": [{
        "field": "slug",
        "message": "Cette valeur existe déjà",
        "code": "DUPLICATE_ENTRY"
      }]
    }
  }
}
```

### Not Null Constraint Violations

```python
# models.py
class Order(models.Model):
    customer_name = models.CharField(max_length=100, verbose_name="Nom du client")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant total")
```

**Test Case:**

```json
// Input (missing required field)
{
  "input": {
    "customerName": "John Doe"
    // totalAmount is missing
  }
}

// Response
{
  "data": {
    "createOrder": {
      "ok": false,
      "order": null,
      "errors": [{
        "field": "total_amount",
        "message": "Ce champ ne peut pas être null",
        "code": "NOT_NULL_CONSTRAINT"
      }]
    }
  }
}
```

## 🔗 Foreign Key Error Examples

### Non-existent Foreign Key References

```python
# models.py
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom de la catégorie")

class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Catégorie")
```

**Test Cases:**

#### 1. Invalid Category ID

```json
// Input
{
  "input": {
    "title": "New Post",
    "categoryId": 999  // Non-existent category
  }
}

// Response
{
  "data": {
    "createPost": {
      "ok": false,
      "post": null,
      "errors": [{
        "field": "category",
        "message": "La catégorie spécifiée n'existe pas",
        "code": "FOREIGN_KEY_ERROR"
      }]
    }
  }
}
```

#### 2. Multiple Foreign Key Errors

```python
# models.py
class Article(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Auteur")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Catégorie")
```

```json
// Input
{
  "input": {
    "title": "New Article",
    "authorId": 888,    // Non-existent author
    "categoryId": 999   // Non-existent category
  }
}

// Response
{
  "data": {
    "createArticle": {
      "ok": false,
      "article": null,
      "errors": [
        {
          "field": "author",
          "message": "L'auteur spécifié n'existe pas",
          "code": "FOREIGN_KEY_ERROR"
        },
        {
          "field": "category",
          "message": "La catégorie spécifiée n'existe pas",
          "code": "FOREIGN_KEY_ERROR"
        }
      ]
    }
  }
}
```

## 🛠️ Custom Error Handling

### Custom Mutation with Enhanced Error Handling

```python
# mutations.py
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rail_django_graphql.mutations import BaseMutation
import re

class CustomCreatePostMutation(BaseMutation):
    class Meta:
        model = Post
        operation = 'create'

    @classmethod
    def perform_mutation(cls, root, info, **input_data):
        try:
            return super().perform_mutation(root, info, **input_data)
        except ValidationError as e:
            return cls._handle_validation_error(e)
        except IntegrityError as e:
            return cls._handle_integrity_error(e)
        except Exception as e:
            return cls._handle_general_error(e)

    @classmethod
    def _handle_validation_error(cls, e):
        """Handle Django validation errors with field extraction"""
        errors = []

        if hasattr(e, 'error_dict'):
            # Field-specific errors
            for field, field_errors in e.error_dict.items():
                for error in field_errors:
                    errors.append({
                        'field': field,
                        'message': str(error),
                        'code': 'VALIDATION_ERROR'
                    })
        elif hasattr(e, 'error_list'):
            # Non-field errors
            for error in e.error_list:
                errors.append({
                    'field': None,
                    'message': str(error),
                    'code': 'VALIDATION_ERROR'
                })
        else:
            errors.append({
                'field': None,
                'message': str(e),
                'code': 'VALIDATION_ERROR'
            })

        return cls(ok=False, errors=errors)

    @classmethod
    def _handle_integrity_error(cls, e):
        """Handle database integrity errors with field extraction"""
        error_message = str(e)
        field = None
        code = 'INTEGRITY_ERROR'
        message = error_message

        # UNIQUE constraint
        if 'UNIQUE constraint failed' in error_message:
            match = re.search(r'UNIQUE constraint failed: \w+\.(\w+)', error_message)
            if match:
                field = match.group(1)
                message = "Cette valeur existe déjà"
                code = 'DUPLICATE_ENTRY'

        # NOT NULL constraint
        elif 'NOT NULL constraint failed' in error_message:
            match = re.search(r'NOT NULL constraint failed: \w+\.(\w+)', error_message)
            if match:
                field = match.group(1)
                message = "Ce champ ne peut pas être null"
                code = 'NOT_NULL_CONSTRAINT'

        # FOREIGN KEY constraint
        elif 'FOREIGN KEY constraint failed' in error_message:
            # Try to extract field from error message
            match = re.search(r'FOREIGN KEY constraint failed', error_message)
            if match:
                message = "Référence invalide vers un objet lié"
                code = 'FOREIGN_KEY_ERROR'

        return cls(
            ok=False,
            errors=[{
                'field': field,
                'message': message,
                'code': code
            }]
        )

    @classmethod
    def _handle_general_error(cls, e):
        """Handle general exceptions"""
        # Check for foreign key validation errors in exception message
        error_message = str(e)

        if "does not exist" in error_message:
            # Extract model name and field
            match = re.search(r'(\w+) with id \'(\d+)\' does not exist', error_message)
            if match:
                model_name = match.group(1).lower()
                return cls(
                    ok=False,
                    errors=[{
                        'field': model_name,
                        'message': f"L'objet {model_name} spécifié n'existe pas",
                        'code': 'FOREIGN_KEY_ERROR'
                    }]
                )

        return cls(
            ok=False,
            errors=[{
                'field': None,
                'message': error_message,
                'code': 'GENERAL_ERROR'
            }]
        )
```

## 🧪 Testing Error Scenarios

### Comprehensive Test Suite

```python
# tests/test_error_handling.py
import pytest
from django.test import TestCase
from graphene.test import Client
from your_app.schema import schema
from your_app.models import User, Post, Category

class ErrorHandlingTestCase(TestCase):
    def setUp(self):
        self.client = Client(schema)
        self.category = Category.objects.create(name="Technology")

    def test_validation_error_field_extraction(self):
        """Test that validation errors extract field information correctly"""
        result = self.client.execute('''
            mutation {
                createUser(input: { username: "", email: "invalid-email" }) {
                    ok
                    errors {
                        field
                        message
                        code
                    }
                }
            }
        ''')

        self.assertFalse(result['data']['createUser']['ok'])
        errors = result['data']['createUser']['errors']

        # Should have errors for both username and email
        self.assertEqual(len(errors), 2)

        # Check username error
        username_error = next(e for e in errors if e['field'] == 'username')
        self.assertEqual(username_error['code'], 'VALIDATION_ERROR')
        self.assertIn('vide', username_error['message'])

        # Check email error
        email_error = next(e for e in errors if e['field'] == 'email')
        self.assertEqual(email_error['code'], 'VALIDATION_ERROR')
        self.assertIn('valide', email_error['message'])

    def test_duplicate_entry_error(self):
        """Test duplicate entry error handling"""
        # Create initial user
        User.objects.create(username="testuser", email="test@example.com")

        result = self.client.execute('''
            mutation {
                createUser(input: {
                    username: "testuser",
                    email: "different@example.com"
                }) {
                    ok
                    errors {
                        field
                        message
                        code
                    }
                }
            }
        ''')

        self.assertFalse(result['data']['createUser']['ok'])
        error = result['data']['createUser']['errors'][0]

        self.assertEqual(error['field'], 'username')
        self.assertEqual(error['code'], 'DUPLICATE_ENTRY')
        self.assertIn('existe déjà', error['message'])

    def test_foreign_key_error(self):
        """Test foreign key validation error handling"""
        result = self.client.execute('''
            mutation {
                createPost(input: {
                    title: "Test Post",
                    content: "This is a test post content",
                    categoryId: 999
                }) {
                    ok
                    errors {
                        field
                        message
                        code
                    }
                }
            }
        ''')

        self.assertFalse(result['data']['createPost']['ok'])
        error = result['data']['createPost']['errors'][0]

        self.assertEqual(error['field'], 'category')
        self.assertEqual(error['code'], 'FOREIGN_KEY_ERROR')
        self.assertIn('existe pas', error['message'])

    def test_multiple_errors(self):
        """Test handling of multiple simultaneous errors"""
        result = self.client.execute('''
            mutation {
                createPost(input: {
                    title: "",
                    content: "Short",
                    categoryId: 999
                }) {
                    ok
                    errors {
                        field
                        message
                        code
                    }
                }
            }
        ''')

        self.assertFalse(result['data']['createPost']['ok'])
        errors = result['data']['createPost']['errors']

        # Should have multiple errors
        self.assertGreater(len(errors), 1)

        # Check that different error types are present
        error_codes = [e['code'] for e in errors]
        self.assertIn('VALIDATION_ERROR', error_codes)
        self.assertIn('FOREIGN_KEY_ERROR', error_codes)
```

## 📋 Best Practices

### 1. Consistent Error Messages

```python
# Use consistent French error messages
ERROR_MESSAGES = {
    'required': "Ce champ est requis",
    'invalid_email': "Adresse email invalide",
    'too_short': "Ce champ est trop court",
    'too_long': "Ce champ est trop long",
    'duplicate': "Cette valeur existe déjà",
    'not_found': "L'objet spécifié n'existe pas",
}

class User(models.Model):
    email = models.EmailField(
        verbose_name="Adresse email",
        error_messages={
            'invalid': ERROR_MESSAGES['invalid_email'],
            'required': ERROR_MESSAGES['required'],
        }
    )
```

### 2. Comprehensive Error Logging

```python
import logging

logger = logging.getLogger(__name__)

class CustomMutation(BaseMutation):
    @classmethod
    def perform_mutation(cls, root, info, **input_data):
        try:
            return super().perform_mutation(root, info, **input_data)
        except Exception as e:
            # Log error for debugging
            logger.error(
                f"Mutation {cls.__name__} failed: {str(e)}",
                extra={
                    'input_data': input_data,
                    'user': info.context.user.id if info.context.user.is_authenticated else None,
                    'exception_type': type(e).__name__,
                }
            )
            raise
```

### 3. Client-Side Error Handling

```javascript
// Frontend error handling example
const handleMutationErrors = (errors) => {
  const fieldErrors = {};
  const generalErrors = [];

  errors.forEach((error) => {
    if (error.field) {
      fieldErrors[error.field] = error.message;
    } else {
      generalErrors.push(error.message);
    }
  });

  return { fieldErrors, generalErrors };
};

// Usage in React component
const [createUser] = useMutation(CREATE_USER_MUTATION, {
  onCompleted: (data) => {
    if (!data.createUser.ok) {
      const { fieldErrors, generalErrors } = handleMutationErrors(
        data.createUser.errors
      );
      setFieldErrors(fieldErrors);
      setGeneralErrors(generalErrors);
    }
  },
});
```

### 4. Error Code Documentation

```python
# Document all error codes for API consumers
ERROR_CODES = {
    'VALIDATION_ERROR': 'Field validation failed',
    'DUPLICATE_ENTRY': 'Unique constraint violation',
    'NOT_NULL_CONSTRAINT': 'Required field is null',
    'FOREIGN_KEY_ERROR': 'Referenced object does not exist',
    'PERMISSION_DENIED': 'User lacks required permissions',
    'RATE_LIMIT_EXCEEDED': 'Too many requests',
    'GENERAL_ERROR': 'Unexpected error occurred',
}
```

This comprehensive error handling system provides clear, actionable feedback to both developers and end users, making debugging and user experience significantly better.
