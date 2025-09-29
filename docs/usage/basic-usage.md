# Basic Usage Guide

This guide covers the fundamental usage patterns of the Django GraphQL Auto-Generation Library. After following the [Installation Guide](../setup/installation.md), you'll learn how to use the automatically generated GraphQL schema.

## 📚 Table of Contents

- [Understanding Auto-Generated Schema](#understanding-auto-generated-schema)
- [Basic Queries](#basic-queries)
- [Basic Mutations](#basic-mutations)
- [Working with Relationships](#working-with-relationships)
- [Filtering and Pagination](#filtering-and-pagination)
- [Error Handling](#error-handling)

## 🔍 Understanding Auto-Generated Schema

The library automatically generates GraphQL schema based on your Django models. For each model, it creates:

- **Object Types**: GraphQL representations of your Django models
- **Queries**: Single object, list, and paginated queries
- **Mutations**: Create, update, and delete operations
- **Filters**: Advanced filtering capabilities
- **Input Types**: For mutation inputs

### Example Model

Let's use this example model throughout this guide:

```python
# models.py
from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    tags = models.ManyToManyField('Tag', blank=True, related_name='posts')
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#000000')  # Hex color
    
    def __str__(self):
        return self.name
```

## 🔍 Basic Queries

### Single Object Queries

Query a single object by ID:

```graphql
# Get a specific post
query {
  post(id: 1) {
    id
    title
    content
    published
    createdAt
    author {
      id
      username
      email
    }
    category {
      id
      name
    }
  }
}
```

### List Queries

Query multiple objects:

```graphql
# Get all posts
query {
  posts {
    id
    title
    published
    author {
      username
    }
    category {
      name
    }
  }
}
```

### Paginated Queries

For large datasets, use paginated queries:

```graphql
# Get paginated posts
query {
  postPages(first: 10, after: "cursor_value") {
    edges {
      node {
        id
        title
        published
        createdAt
      }
      cursor
    }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
    totalCount
  }
}
```

## ✏️ Basic Mutations

### Create Operations

Create new objects:

```graphql
# Create a new category
mutation {
  createCategory(input: {
    name: "Technology"
    description: "Posts about technology and programming"
  }) {
    ok
    category {
      id
      name
      description
      createdAt
    }
    errors
  }
}

# Create a new post
mutation {
  createPost(input: {
    title: "Getting Started with GraphQL"
    content: "GraphQL is a powerful query language..."
    authorId: 1
    categoryId: 1
    published: true
  }) {
    ok
    post {
      id
      title
      content
      published
      author {
        username
      }
      category {
        name
      }
    }
    errors
  }
}
```

### Update Operations

Update existing objects:

```graphql
# Update a post
mutation {
  updatePost(id: 1, input: {
    title: "Getting Started with GraphQL - Updated"
    published: true
  }) {
    ok
    post {
      id
      title
      published
      updatedAt
    }
    errors
  }
}
```

### Delete Operations

Delete objects:

```graphql
# Delete a post
mutation {
  deletePost(id: 1) {
    ok
    post {
      id
      title
    }
    errors
  }
}
```

## 🔗 Working with Relationships

### Querying Related Objects

```graphql
# Get posts with related data
query {
  posts {
    id
    title
    # Foreign key relationship
    author {
      id
      username
      email
    }
    category {
      id
      name
      description
    }
    # Many-to-many relationship
    tags {
      id
      name
      color
    }
  }
}

# Get category with related posts
query {
  category(id: 1) {
    id
    name
    posts {
      id
      title
      published
    }
  }
}
```

### Creating with Relationships

```graphql
# Create post with existing relationships
mutation {
  createPost(input: {
    title: "New Post"
    content: "Content here..."
    authorId: 1
    categoryId: 2
    tagIds: [1, 2, 3]  # Connect to existing tags
    published: false
  }) {
    ok
    post {
      id
      title
      author {
        username
      }
      category {
        name
      }
      tags {
        name
      }
    }
    errors
  }
}
```

### Nested Creation (Advanced)

Create objects with nested relationships:

```graphql
# Create post with new category and tags
mutation {
  createPost(input: {
    title: "Post with Nested Creation"
    content: "Content..."
    authorId: 1
    category: {
      name: "New Category"
      description: "Created inline"
    }
    tags: [
      { name: "new-tag-1", color: "#ff0000" }
      { name: "new-tag-2", color: "#00ff00" }
    ]
    published: true
  }) {
    ok
    post {
      id
      title
      category {
        id
        name
      }
      tags {
        id
        name
        color
      }
    }
    errors
  }
}
```

## 🔍 Filtering and Pagination

### Basic Filtering

```graphql
# Filter posts by published status
query {
  posts(filters: { published: true }) {
    id
    title
    published
  }
}

# Filter by text content
query {
  posts(filters: { 
    title_Icontains: "GraphQL"
    published: true 
  }) {
    id
    title
    content
  }
}
```

### Advanced Filtering

```graphql
# Complex filtering with AND/OR operations
query {
  posts(filters: {
    AND: [
      { published: true }
      { 
        OR: [
          { title_Icontains: "GraphQL" }
          { content_Icontains: "Django" }
        ]
      }
    ]
  }) {
    id
    title
    published
  }
}
```

### Date Range Filtering

```graphql
# Filter by date range
query {
  posts(filters: {
    createdAt_Gte: "2024-01-01"
    createdAt_Lt: "2024-12-31"
  }) {
    id
    title
    createdAt
  }
}
```

### Relationship Filtering

```graphql
# Filter by related object properties
query {
  posts(filters: {
    author_Username: "john_doe"
    category_Name_Icontains: "tech"
  }) {
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
```

### Ordering

```graphql
# Order results
query {
  posts(orderBy: "-created_at") {  # Descending order
    id
    title
    createdAt
  }
}

# Multiple ordering fields
query {
  posts(orderBy: ["category__name", "-created_at"]) {
    id
    title
    category {
      name
    }
    createdAt
  }
}
```

### Pagination with Filtering

```graphql
# Combine pagination with filtering
query {
  postPages(
    first: 5
    filters: { published: true }
    orderBy: "-created_at"
  ) {
    edges {
      node {
        id
        title
        createdAt
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
```

## ❌ Error Handling

### Mutation Errors

The library provides consistent error handling across all mutations with enhanced field-specific error reporting:

```graphql
# Example mutation with validation errors
mutation {
  createPost(input: {
    title: ""  # Empty title will cause validation error
    content: "Some content"
    authorId: 999  # Non-existent author
  }) {
    ok
    post {
      id
      title
    }
    errors {
      field    # Field name where error occurred
      message  # Human-readable error message
    }
  }
}

# Response with field-specific errors:
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
          "field": "author",
          "message": "Invalid author: The selected user does not exist."
        }
      ]
    }
  }
}
```

### Database Constraint Errors

The system automatically extracts field information from database constraint violations:

```graphql
# Attempting to create duplicate entry
mutation {
  createUser(input: {
    email: "existing@example.com"  # Email already exists
    username: "newuser"
  }) {
    ok
    user {
      id
      email
    }
    errors {
      field
      message
    }
  }
}

# Response with automatic field extraction:
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

### Query Errors

```graphql
# Querying non-existent object
query {
  post(id: 999) {
    id
    title
  }
}

# Response:
{
  "data": {
    "post": null
  }
}
```

## 🎯 Best Practices

### 1. Use Specific Field Selection

Only request the fields you need:

```graphql
# Good - specific fields
query {
  posts {
    id
    title
    published
  }
}

# Avoid - requesting all fields unnecessarily
query {
  posts {
    id
    title
    content
    author {
      id
      username
      email
      firstName
      lastName
      dateJoined
    }
    # ... many more fields
  }
}
```

### 2. Use Pagination for Large Datasets

```graphql
# Good - paginated query
query {
  postPages(first: 20) {
    edges {
      node {
        id
        title
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

### 3. Handle Errors Gracefully

Always check the `ok` field and `errors` array in mutations:

```javascript
// Frontend example (JavaScript)
const result = await graphqlClient.mutate({
  mutation: CREATE_POST,
  variables: { input: postData }
});

if (result.data.createPost.ok) {
  // Success
  const newPost = result.data.createPost.post;
  console.log('Post created:', newPost);
} else {
  // Handle errors
  const errors = result.data.createPost.errors;
  console.error('Validation errors:', errors);
}
```

### 4. Use Filtering Efficiently

Combine filters to reduce data transfer:

```graphql
# Good - filtered at the database level
query {
  posts(filters: { 
    published: true 
    author_IsActive: true
  }) {
    id
    title
  }
}
```

## 🚀 Next Steps

Now that you understand the basics:

1. [Explore Advanced Features](../features/filtering.md) - Learn about complex filtering and nested operations
2. [Check API Reference](../api/core-classes.md) - Understand the underlying classes
3. [See Advanced Examples](../examples/advanced-examples.md) - Complex real-world scenarios
4. [Learn About Custom Scalars](../advanced/custom-scalars.md) - Work with complex data types

## 🤝 Need Help?

- Check the [Troubleshooting Guide](../development/troubleshooting.md)
- Review [Advanced Examples](../examples/advanced-examples.md)
- Join our [Community Discussions](https://github.com/your-repo/django-graphql-auto/discussions)