# Mutations API Reference

This document provides a comprehensive reference for all GraphQL mutations available in the Django GraphQL Auto-Generation System, including the enhanced error handling capabilities.

## 📚 Table of Contents

- [Overview](#overview)
- [Standard CRUD Mutations](#standard-crud-mutations)
- [Method Mutations](#method-mutations)
- [Error Response Format](#error-response-format)
- [Authentication Mutations](#authentication-mutations)
- [Bulk Operations](#bulk-operations)
- [File Upload Mutations](#file-upload-mutations)
- [Custom Mutations](#custom-mutations)

## 🔍 Overview

The Django GraphQL Auto-Generation System automatically creates mutations for all registered Django models. Each mutation follows a consistent pattern and includes enhanced error handling with field-specific information.

### Mutation Naming Convention

- **Create**: `create{ModelName}` (e.g., `createUser`, `createPost`)
- **Update**: `update{ModelName}` (e.g., `updateUser`, `updatePost`)
- **Delete**: `delete{ModelName}` (e.g., `deleteUser`, `deletePost`)
- **Method**: `{modelName}{MethodName}` (e.g., `userActivate`, `postPublish`)

## 🔧 Standard CRUD Mutations

### Create Mutations

Creates a new instance of the specified model.

**Pattern:**
```graphql
mutation Create{ModelName}($input: Create{ModelName}Input!) {
  create{ModelName}(input: $input) {
    ok
    {modelName} {
      # Model fields
    }
    errors {
      field
      message
      code
    }
  }
}
```

**Example - Create User:**
```graphql
mutation CreateUser($input: CreateUserInput!) {
  createUser(input: $input) {
    ok
    user {
      id
      username
      email
      firstName
      lastName
      isActive
      dateJoined
    }
    errors {
      field
      message
      code
    }
  }
}
```

**Input Type:**
```graphql
input CreateUserInput {
  username: String!
  email: String!
  firstName: String
  lastName: String
  password: String!
}
```

**Success Response:**
```json
{
  "data": {
    "createUser": {
      "ok": true,
      "user": {
        "id": "1",
        "username": "johndoe",
        "email": "john@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "isActive": true,
        "dateJoined": "2024-01-15T10:30:00Z"
      },
      "errors": []
    }
  }
}
```

**Error Response:**
```json
{
  "data": {
    "createUser": {
      "ok": false,
      "user": null,
      "errors": [
        {
          "field": "username",
          "message": "Ce nom d'utilisateur existe déjà",
          "code": "DUPLICATE_ENTRY"
        },
        {
          "field": "email",
          "message": "Saisissez une adresse de courriel valide.",
          "code": "VALIDATION_ERROR"
        }
      ]
    }
  }
}
```

### Update Mutations

Updates an existing instance of the specified model.

**Pattern:**
```graphql
mutation Update{ModelName}($input: Update{ModelName}Input!) {
  update{ModelName}(input: $input) {
    ok
    {modelName} {
      # Model fields
    }
    errors {
      field
      message
      code
    }
  }
}
```

**Example - Update Post:**
```graphql
mutation UpdatePost($input: UpdatePostInput!) {
  updatePost(input: $input) {
    ok
    post {
      id
      title
      content
      published
      updatedAt
    }
    errors {
      field
      message
      code
    }
  }
}
```

**Input Type:**
```graphql
input UpdatePostInput {
  id: ID!
  title: String
  content: String
  published: Boolean
  categoryId: ID
}
```

### Delete Mutations

Deletes an existing instance of the specified model.

**Pattern:**
```graphql
mutation Delete{ModelName}($input: Delete{ModelName}Input!) {
  delete{ModelName}(input: $input) {
    ok
    deletedId: ID
    errors {
      field
      message
      code
    }
  }
}
```

**Example - Delete Comment:**
```graphql
mutation DeleteComment($input: DeleteCommentInput!) {
  deleteComment(input: $input) {
    ok
    deletedId
    errors {
      field
      message
      code
    }
  }
}
```

**Input Type:**
```graphql
input DeleteCommentInput {
  id: ID!
}
```

## 🎯 Method Mutations

Method mutations are automatically generated from custom methods defined on Django models.

**Pattern:**
```graphql
mutation {ModelName}{MethodName}($input: {ModelName}{MethodName}Input!) {
  {modelName}{MethodName}(input: $input) {
    ok
    {modelName} {
      # Model fields
    }
    errors {
      field
      message
      code
    }
  }
}
```

**Example - User Activation:**
```graphql
mutation UserActivate($input: UserActivateInput!) {
  userActivate(input: $input) {
    ok
    user {
      id
      username
      isActive
    }
    errors {
      field
      message
      code
    }
  }
}
```

**Example - Post Publishing:**
```graphql
mutation PostPublish($input: PostPublishInput!) {
  postPublish(input: $input) {
    ok
    post {
      id
      title
      published
      publishedAt
    }
    errors {
      field
      message
      code
    }
  }
}
```

**Example - Order Shipping:**
```graphql
mutation OrderShip($input: OrderShipInput!) {
  orderShip(input: $input) {
    ok
    order {
      id
      status
      trackingNumber
      shippedAt
    }
    errors {
      field
      message
      code
    }
  }
}
```

**Input Type with Parameters:**
```graphql
input OrderShipInput {
  id: ID!
  trackingNumber: String!
  carrier: String
}
```

## ⚠️ Error Response Format

All mutations return a consistent error format with enhanced field-specific information:

### Error Object Structure

```graphql
type MutationError {
  field: String        # The specific field that caused the error (null for general errors)
  message: String!     # Human-readable error message in French
  code: String!        # Error code for programmatic handling
}
```

### Error Codes

| Code | Description | Field Extraction | Example |
|------|-------------|------------------|---------|
| `VALIDATION_ERROR` | Field validation failed | ✅ Automatic | Empty required field, invalid format |
| `DUPLICATE_ENTRY` | Unique constraint violation | ✅ Enhanced | Username already exists |
| `NOT_NULL_CONSTRAINT` | Required field is null | ✅ Enhanced | Missing required field |
| `FOREIGN_KEY_ERROR` | Referenced object doesn't exist | ✅ Enhanced | Invalid category ID |
| `PERMISSION_DENIED` | User lacks required permissions | ❌ Manual | Insufficient privileges |
| `RATE_LIMIT_EXCEEDED` | Too many requests | ❌ Manual | API rate limit hit |
| `GENERAL_ERROR` | Unexpected error occurred | ❌ Manual | System error |

### Error Examples

#### Validation Error
```json
{
  "field": "email",
  "message": "Saisissez une adresse de courriel valide.",
  "code": "VALIDATION_ERROR"
}
```

#### Duplicate Entry Error
```json
{
  "field": "username",
  "message": "Ce nom d'utilisateur existe déjà",
  "code": "DUPLICATE_ENTRY"
}
```

#### Foreign Key Error
```json
{
  "field": "category",
  "message": "La catégorie spécifiée n'existe pas",
  "code": "FOREIGN_KEY_ERROR"
}
```

#### Multiple Errors
```json
[
  {
    "field": "title",
    "message": "Ce champ ne peut pas être vide.",
    "code": "VALIDATION_ERROR"
  },
  {
    "field": "category",
    "message": "La catégorie spécifiée n'existe pas",
    "code": "FOREIGN_KEY_ERROR"
  }
]
```

## 🔐 Authentication Mutations

### Register User

```graphql
mutation Register($input: RegisterInput!) {
  register(input: $input) {
    ok
    user {
      id
      username
      email
    }
    token
    refreshToken
    errors {
      field
      message
      code
    }
  }
}
```

**Input:**
```graphql
input RegisterInput {
  username: String!
  email: String!
  password: String!
  firstName: String
  lastName: String
}
```

### Login User

```graphql
mutation Login($input: LoginInput!) {
  login(input: $input) {
    ok
    user {
      id
      username
      email
    }
    token
    refreshToken
    errors {
      field
      message
      code
    }
  }
}
```

**Input:**
```graphql
input LoginInput {
  username: String!
  password: String!
}
```

### Refresh Token

```graphql
mutation RefreshToken($input: RefreshTokenInput!) {
  refreshToken(input: $input) {
    ok
    token
    refreshToken
    errors {
      field
      message
      code
    }
  }
}
```

### Logout User

```graphql
mutation Logout {
  logout {
    ok
    errors {
      field
      message
      code
    }
  }
}
```

## 📦 Bulk Operations

### Bulk Create

```graphql
mutation BulkCreatePosts($input: BulkCreatePostsInput!) {
  bulkCreatePosts(input: $input) {
    ok
    posts {
      id
      title
      content
    }
    errors {
      field
      message
      code
      index  # Index of the item that failed (for bulk operations)
    }
  }
}
```

**Input:**
```graphql
input BulkCreatePostsInput {
  posts: [CreatePostInput!]!
}
```

### Bulk Update

```graphql
mutation BulkUpdateUsers($input: BulkUpdateUsersInput!) {
  bulkUpdateUsers(input: $input) {
    ok
    users {
      id
      username
      isActive
    }
    errors {
      field
      message
      code
      index
    }
  }
}
```

### Bulk Delete

```graphql
mutation BulkDeleteComments($input: BulkDeleteCommentsInput!) {
  bulkDeleteComments(input: $input) {
    ok
    deletedIds: [ID!]
    errors {
      field
      message
      code
      index
    }
  }
}
```

**Input:**
```graphql
input BulkDeleteCommentsInput {
  ids: [ID!]!
}
```

## 📁 File Upload Mutations

### Single File Upload

```graphql
mutation UploadFile($input: UploadFileInput!) {
  uploadFile(input: $input) {
    ok
    file {
      id
      filename
      url
      size
      contentType
    }
    errors {
      field
      message
      code
    }
  }
}
```

**Input:**
```graphql
input UploadFileInput {
  file: Upload!
  description: String
  tags: [String!]
}
```

### Multiple File Upload

```graphql
mutation UploadFiles($input: UploadFilesInput!) {
  uploadFiles(input: $input) {
    ok
    files {
      id
      filename
      url
      size
      contentType
    }
    errors {
      field
      message
      code
      index
    }
  }
}
```

**Input:**
```graphql
input UploadFilesInput {
  files: [Upload!]!
  description: String
}
```

## 🛠️ Custom Mutations

### Creating Custom Mutations

```python
# mutations.py
from django_graphql_auto.mutations import BaseMutation
import graphene

class CustomBusinessLogicMutation(BaseMutation):
    class Arguments:
        input = graphene.Argument(CustomBusinessLogicInput, required=True)
    
    class Meta:
        description = "Performs custom business logic operation"
    
    result = graphene.Field(CustomResultType)
    
    @classmethod
    def perform_mutation(cls, root, info, **input_data):
        try:
            # Custom business logic here
            result = perform_custom_operation(input_data)
            
            return cls(
                ok=True,
                result=result,
                errors=[]
            )
        except ValidationError as e:
            return cls._handle_validation_error(e)
        except Exception as e:
            return cls._handle_general_error(e)
```

### Custom Error Handling

```python
class CustomMutation(BaseMutation):
    @classmethod
    def _handle_custom_error(cls, error):
        """Handle custom business logic errors"""
        if isinstance(error, CustomBusinessError):
            return cls(
                ok=False,
                errors=[{
                    'field': error.field,
                    'message': error.message,
                    'code': 'BUSINESS_LOGIC_ERROR'
                }]
            )
        
        return super()._handle_general_error(error)
```

## 📋 Best Practices

### 1. Input Validation

```graphql
# Always validate inputs on both client and server side
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ok
    post {
      id
      title
    }
    errors {
      field
      message
      code
    }
  }
}
```

### 2. Error Handling

```javascript
// Client-side error handling
const handleMutationResponse = (response) => {
  if (!response.ok) {
    const fieldErrors = {};
    const generalErrors = [];
    
    response.errors.forEach(error => {
      if (error.field) {
        fieldErrors[error.field] = error.message;
      } else {
        generalErrors.push(error.message);
      }
    });
    
    return { fieldErrors, generalErrors };
  }
  
  return { success: true, data: response };
};
```

### 3. Optimistic Updates

```javascript
// Use optimistic updates for better UX
const [updatePost] = useMutation(UPDATE_POST_MUTATION, {
  optimisticResponse: {
    updatePost: {
      ok: true,
      post: {
        ...existingPost,
        ...updatedFields
      },
      errors: []
    }
  },
  onError: (error) => {
    // Handle network errors
    console.error('Mutation failed:', error);
  }
});
```

### 4. Rate Limiting

```python
# Implement rate limiting for mutations
from django_ratelimit.decorators import ratelimit

class CreatePostMutation(BaseMutation):
    @ratelimit(key='user', rate='10/m', method='POST')
    @classmethod
    def perform_mutation(cls, root, info, **input_data):
        return super().perform_mutation(root, info, **input_data)
```

This comprehensive mutations API reference provides all the information needed to effectively use the GraphQL mutations generated by the Django GraphQL Auto-Generation System, including the enhanced error handling capabilities.