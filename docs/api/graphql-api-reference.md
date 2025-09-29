# GraphQL API Reference

## Overview

This document provides a comprehensive reference for all GraphQL queries, mutations, and types available in the Django GraphQL Auto-Generation System. The API includes automatically generated CRUD operations, security features, and custom business logic mutations.

## 🚀 Schema Structure

```graphql
schema {
  query: Query
  mutation: Mutation
}
```

## 📋 Table of Contents

- [Authentication & Security](#authentication--security)
- [Core Queries](#core-queries)
- [Core Mutations](#core-mutations)
- [Security Queries](#security-queries)
- [Input Types](#input-types)
- [Output Types](#output-types)
- [Scalar Types](#scalar-types)
- [Enums](#enums)
- [Error Handling](#error-handling)

## 🔐 Authentication & Security

### Authentication Mutations

#### `register`
Register a new user account.

```graphql
mutation Register($data: RegisterInput!) {
  register(data: $data) {
    success: Boolean!
    user: UserType
    accessToken: String
    refreshToken: String
    errors: [String]
  }
}
```

**Input Type:**
```graphql
input RegisterInput {
  username: String!
  email: String!
  password: String!
  firstName: String
  lastName: String
  phoneNumber: String
}
```

#### `login`
Authenticate user and obtain tokens.

```graphql
mutation Login($data: LoginInput!) {
  login(data: $data) {
    success: Boolean!
    user: UserType
    accessToken: String
    refreshToken: String
    errors: [String]
  }
}
```

**Input Type:**
```graphql
input LoginInput {
  username: String!
  password: String!
}
```

#### `refreshToken`
Refresh access token using refresh token.

```graphql
mutation RefreshToken($refreshToken: String!) {
  refreshToken(refreshToken: $refreshToken) {
    success: Boolean!
    accessToken: String
    refreshToken: String
    errors: [String]
  }
}
```

#### `logout`
Logout user and invalidate tokens.

```graphql
mutation Logout {
  logout {
    success: Boolean!
    message: String
  }
}
```

#### `changePassword`
Change user password (requires authentication).

```graphql
mutation ChangePassword($data: ChangePasswordInput!) {
  changePassword(data: $data) {
    success: Boolean!
    message: String
    errors: [String]
  }
}
```

**Input Type:**
```graphql
input ChangePasswordInput {
  oldPassword: String!
  newPassword: String!
}
```

#### `requestPasswordReset`
Request password reset email.

```graphql
mutation RequestPasswordReset($email: String!) {
  requestPasswordReset(email: $email) {
    success: Boolean!
    message: String
  }
}
```

#### `resetPassword`
Reset password using reset token.

```graphql
mutation ResetPassword($data: ResetPasswordInput!) {
  resetPassword(data: $data) {
    success: Boolean!
    message: String
    errors: [String]
  }
}
```

**Input Type:**
```graphql
input ResetPasswordInput {
  token: String!
  newPassword: String!
}
```

### Authentication Queries

#### `me`
Get current authenticated user information.

```graphql
query Me {
  me {
    id: ID!
    username: String!
    email: String!
    firstName: String
    lastName: String
    isActive: Boolean!
    isStaff: Boolean!
    isSuperuser: Boolean!
    dateJoined: DateTime!
    lastLogin: DateTime
    groups: [GroupType]
    userPermissions: [PermissionType]
  }
}
```

## 🔍 Core Queries

### Single Object Queries

Retrieve individual objects by ID.

#### Syntax Pattern
```graphql
<modelName>(id: ID!): <ModelType>
```

#### Examples

```graphql
# Get a specific post
query GetPost($id: ID!) {
  post(id: $id) {
    id
    title
    content
    status
    author {
      username
      email
    }
    category {
      name
    }
    tags {
      name
      color
    }
    createdAt
    updatedAt
  }
}

# Get a specific user
query GetUser($id: ID!) {
  user(id: $id) {
    id
    username
    email
    firstName
    lastName
    isActive
    dateJoined
    posts {
      title
      status
    }
  }
}

# Get a specific category
query GetCategory($id: ID!) {
  category(id: $id) {
    id
    name
    description
    isActive
    posts {
      title
      status
    }
  }
}
```

### List Queries

Retrieve multiple objects with filtering and ordering.

#### Syntax Pattern
```graphql
<modelNames>(
  filters: <ModelFilterInput>
  orderBy: [String]
  limit: Int
  offset: Int
): [<ModelType>]
```

#### Examples

```graphql
# Get all published posts
query GetPublishedPosts {
  posts(
    filters: { status: PUBLISHED }
    orderBy: ["-createdAt"]
    limit: 10
  ) {
    id
    title
    content
    author {
      username
    }
    createdAt
  }
}

# Get active users
query GetActiveUsers {
  users(
    filters: { isActive: true }
    orderBy: ["username"]
  ) {
    id
    username
    email
    dateJoined
  }
}

# Get posts by category
query GetPostsByCategory($categoryId: ID!) {
  posts(
    filters: { category: $categoryId }
    orderBy: ["-createdAt"]
  ) {
    id
    title
    status
    createdAt
  }
}
```

### Paginated Queries

Retrieve paginated results using Relay-style connections.

#### Syntax Pattern
```graphql
<modelName>Pages(
  first: Int
  after: String
  last: Int
  before: String
  filters: <ModelFilterInput>
  orderBy: [String]
): <ModelConnection>
```

#### Examples

```graphql
# Paginated posts
query GetPostPages($first: Int, $after: String) {
  postPages(
    first: $first
    after: $after
    filters: { status: PUBLISHED }
    orderBy: ["-createdAt"]
  ) {
    edges {
      node {
        id
        title
        content
        author {
          username
        }
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

# Paginated users with search
query SearchUsers($search: String, $first: Int, $after: String) {
  userPages(
    first: $first
    after: $after
    filters: {
      OR: [
        { username__icontains: $search }
        { email__icontains: $search }
        { firstName__icontains: $search }
        { lastName__icontains: $search }
      ]
    }
  ) {
    edges {
      node {
        id
        username
        email
        firstName
        lastName
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
```

## ✏️ Core Mutations

### Create Operations

Create new objects.

#### Syntax Pattern
```graphql
create<ModelName>(input: Create<ModelName>Input!): Create<ModelName>Payload
```

#### Examples

```graphql
# Create a new post
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ok
    post {
      id
      title
      content
      status
      author {
        username
      }
      category {
        name
      }
      createdAt
    }
    errors
  }
}

# Create a new category
mutation CreateCategory($input: CreateCategoryInput!) {
  createCategory(input: $input) {
    ok
    category {
      id
      name
      description
      isActive
      createdAt
    }
    errors
  }
}

# Create a new tag
mutation CreateTag($input: CreateTagInput!) {
  createTag(input: $input) {
    ok
    tag {
      id
      name
      color
      createdAt
    }
    errors
  }
}
```

### Update Operations

Update existing objects.

#### Syntax Pattern
```graphql
update<ModelName>(input: Update<ModelName>Input!): Update<ModelName>Payload
```

#### Examples

```graphql
# Update a post
mutation UpdatePost($input: UpdatePostInput!) {
  updatePost(input: $input) {
    ok
    post {
      id
      title
      content
      status
      updatedAt
    }
    errors
  }
}

# Update user profile
mutation UpdateUser($input: UpdateUserInput!) {
  updateUser(input: $input) {
    ok
    user {
      id
      username
      email
      firstName
      lastName
      updatedAt
    }
    errors
  }
}
```

### Delete Operations

Delete objects by ID.

#### Syntax Pattern
```graphql
delete<ModelName>(id: ID!): Delete<ModelName>Payload
```

#### Examples

```graphql
# Delete a post
mutation DeletePost($id: ID!) {
  deletePost(id: $id) {
    ok
    deletedId
    errors
  }
}

# Delete a category
mutation DeleteCategory($id: ID!) {
  deleteCategory(id: $id) {
    ok
    deletedId
    errors
  }
}
```

### Bulk Operations

Perform operations on multiple objects.

#### Bulk Create
```graphql
mutation BulkCreatePosts($input: BulkCreatePostInput!) {
  bulkCreatePost(input: $input) {
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

#### Bulk Update
```graphql
mutation BulkUpdatePosts($input: BulkUpdatePostInput!) {
  bulkUpdatePost(input: $input) {
    ok
    objects {
      id
      title
      status
      updatedAt
    }
    errors
  }
}
```

#### Bulk Delete
```graphql
mutation BulkDeletePosts($input: BulkDeletePostInput!) {
  bulkDeletePost(input: $input) {
    ok
    deletedIds
    errors
  }
}
```

## 🛡️ Security Queries

### Permission Queries

#### `checkPermission`
Check if current user has specific permission.

```graphql
query CheckPermission($permission: String!, $objectId: ID) {
  checkPermission(permission: $permission, objectId: $objectId) {
    hasPermission: Boolean!
    reason: String
  }
}
```

#### `userPermissions`
Get all permissions for current user.

```graphql
query UserPermissions {
  userPermissions {
    permissions: [String]
    groups: [String]
    isStaff: Boolean!
    isSuperuser: Boolean!
  }
}
```

### Validation Queries

#### `validateField`
Validate a specific field value.

```graphql
query ValidateField($fieldName: String!, $value: String!, $modelName: String) {
  validateField(field_name: $fieldName, value: $value, model_name: $modelName) {
    isValid: Boolean!
    errors: [String]
    sanitizedValue: String
  }
}
```

#### `validateObject`
Validate an entire object.

```graphql
query ValidateObject($data: JSONString!, $modelName: String!) {
  validateObject(data: $data, model_name: $modelName) {
    isValid: Boolean!
    errors: [String]
    sanitizedData: JSONString
  }
}
```

### Security Information

#### `securityInfo`
Get current security status and information.

```graphql
query SecurityInfo {
  securityInfo {
    rateLimiting {
      remainingRequests: Int
      windowResetTime: DateTime
      currentComplexityLimit: Int
      currentDepthLimit: Int
    }
    authentication {
      isAuthenticated: Boolean!
      user {
        username: String
        lastLogin: DateTime
        loginCount: Int
      }
      tokenExpiresAt: DateTime
      sessionExpiresAt: DateTime
    }
    permissions {
      effectivePermissions: [String]
      roleHierarchy: [String]
      groupMemberships: [String]
    }
    recentActivity {
      lastQueries: [QueryInfo]
      securityEvents: [SecurityEvent]
    }
  }
}
```

#### `queryStats`
Get query statistics and performance metrics.

```graphql
query QueryStats {
  queryStats {
    totalQueries: Int!
    avgComplexity: Float!
    avgDepth: Float!
    avgExecutionTime: Float!
    successRate: Float!
    errorBreakdown {
      validationErrors: Int!
      permissionErrors: Int!
      rateLimitErrors: Int!
      complexityErrors: Int!
      depthErrors: Int!
    }
  }
}
```

## 📝 Input Types

### Authentication Input Types

```graphql
input RegisterInput {
  username: String!
  email: String!
  password: String!
  firstName: String
  lastName: String
  phoneNumber: String
}

input LoginInput {
  username: String!
  password: String!
}

input ChangePasswordInput {
  oldPassword: String!
  newPassword: String!
}

input ResetPasswordInput {
  token: String!
  newPassword: String!
}
```

### Model Input Types

#### Post Input Types
```graphql
input CreatePostInput {
  title: String!
  content: String!
  status: PostStatusChoices = DRAFT
  authorId: ID!
  categoryId: ID!
  tagIds: [ID]
}

input UpdatePostInput {
  id: ID!
  title: String
  content: String
  status: PostStatusChoices
  categoryId: ID
  tagIds: [ID]
}
```

#### Category Input Types
```graphql
input CreateCategoryInput {
  name: String!
  description: String!
  isActive: Boolean = true
}

input UpdateCategoryInput {
  id: ID!
  name: String
  description: String
  isActive: Boolean
}
```

#### Tag Input Types
```graphql
input CreateTagInput {
  name: String!
  color: String = "#000000"
}

input UpdateTagInput {
  id: ID!
  name: String
  color: String
}
```

### Filter Input Types

#### Post Filter Input
```graphql
input PostFilterInput {
  # Basic filters
  id: ID
  title: String
  title__exact: String
  title__iexact: String
  title__contains: String
  title__icontains: String
  title__startswith: String
  title__endswith: String
  title__regex: String
  
  content: String
  content__contains: String
  content__icontains: String
  
  status: PostStatusChoices
  status__in: [PostStatusChoices]
  
  # Date filters
  createdAt: DateTime
  createdAt__exact: DateTime
  createdAt__gt: DateTime
  createdAt__gte: DateTime
  createdAt__lt: DateTime
  createdAt__lte: DateTime
  createdAt__range: [DateTime]
  
  updatedAt: DateTime
  updatedAt__gt: DateTime
  updatedAt__gte: DateTime
  updatedAt__lt: DateTime
  updatedAt__lte: DateTime
  
  publishedAt: DateTime
  publishedAt__isnull: Boolean
  
  # Relationship filters
  author: ID
  author__username: String
  author__username__icontains: String
  author__email: String
  author__isActive: Boolean
  
  category: ID
  category__name: String
  category__name__icontains: String
  category__isActive: Boolean
  
  tags: ID
  tags__name: String
  tags__name__in: [String]
  tags__color: String
  
  # Logical operators
  AND: [PostFilterInput]
  OR: [PostFilterInput]
  NOT: PostFilterInput
}
```

#### User Filter Input
```graphql
input UserFilterInput {
  id: ID
  username: String
  username__exact: String
  username__iexact: String
  username__contains: String
  username__icontains: String
  username__startswith: String
  username__endswith: String
  
  email: String
  email__exact: String
  email__iexact: String
  email__contains: String
  email__icontains: String
  
  firstName: String
  firstName__icontains: String
  
  lastName: String
  lastName__icontains: String
  
  isActive: Boolean
  isStaff: Boolean
  isSuperuser: Boolean
  
  dateJoined: DateTime
  dateJoined__gt: DateTime
  dateJoined__gte: DateTime
  dateJoined__lt: DateTime
  dateJoined__lte: DateTime
  
  lastLogin: DateTime
  lastLogin__isnull: Boolean
  lastLogin__gt: DateTime
  lastLogin__gte: DateTime
  
  # Logical operators
  AND: [UserFilterInput]
  OR: [UserFilterInput]
  NOT: UserFilterInput
}
```

## 📤 Output Types

### Authentication Output Types

```graphql
type AuthPayload {
  success: Boolean!
  user: UserType
  accessToken: String
  refreshToken: String
  errors: [String]
}

type PasswordChangePayload {
  success: Boolean!
  message: String
  errors: [String]
}

type LogoutPayload {
  success: Boolean!
  message: String
}
```

### CRUD Operation Payloads

```graphql
type CreatePostPayload {
  ok: Boolean!
  post: PostType
  errors: [String]
}

type UpdatePostPayload {
  ok: Boolean!
  post: PostType
  errors: [String]
}

type DeletePostPayload {
  ok: Boolean!
  deletedId: ID
  errors: [String]
}
```

### Bulk Operation Payloads

```graphql
type BulkCreatePostPayload {
  ok: Boolean!
  objects: [PostType]
  errors: [String]
}

type BulkUpdatePostPayload {
  ok: Boolean!
  objects: [PostType]
  errors: [String]
}

type BulkDeletePostPayload {
  ok: Boolean!
  deletedIds: [ID]
  errors: [String]
}
```

### Security Output Types

```graphql
type PermissionInfo {
  hasPermission: Boolean!
  reason: String
}

type UserPermissions {
  permissions: [String]
  groups: [String]
  isStaff: Boolean!
  isSuperuser: Boolean!
}

type ValidationResult {
  isValid: Boolean!
  errors: [String]
  sanitizedValue: String
}

type ObjectValidationResult {
  isValid: Boolean!
  errors: [String]
  sanitizedData: JSONString
}

type SecurityInfo {
  rateLimiting: RateLimitInfo
  authentication: AuthenticationInfo
  permissions: PermissionInfo
  recentActivity: ActivityInfo
}

type QueryStats {
  totalQueries: Int!
  avgComplexity: Float!
  avgDepth: Float!
  avgExecutionTime: Float!
  successRate: Float!
  errorBreakdown: ErrorBreakdown!
}
```

### Connection Types

```graphql
type PostConnection {
  edges: [PostEdge]
  pageInfo: PageInfo!
  totalCount: Int
}

type PostEdge {
  node: PostType
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

### Model Types

#### UserType
```graphql
type UserType implements Node {
  id: ID!
  username: String!
  email: String!
  firstName: String
  lastName: String
  isActive: Boolean!
  isStaff: Boolean!
  isSuperuser: Boolean!
  dateJoined: DateTime!
  lastLogin: DateTime
  
  # Relationships
  groups: [GroupType]
  userPermissions: [PermissionType]
  posts: [PostType]
  comments: [CommentType]
}
```

#### PostType
```graphql
type PostType implements Node {
  id: ID!
  title: String!
  content: String!
  status: PostStatusChoices!
  createdAt: DateTime!
  updatedAt: DateTime!
  publishedAt: DateTime
  
  # Relationships
  author: UserType!
  category: CategoryType!
  tags: [TagType]
  comments: [CommentType]
}
```

#### CategoryType
```graphql
type CategoryType implements Node {
  id: ID!
  name: String!
  description: String!
  isActive: Boolean!
  createdAt: DateTime!
  
  # Relationships
  posts: [PostType]
}
```

#### TagType
```graphql
type TagType implements Node {
  id: ID!
  name: String!
  color: String!
  createdAt: DateTime!
  
  # Relationships
  posts: [PostType]
  comments: [CommentType]
}
```

#### CommentType
```graphql
type CommentType implements Node {
  id: ID!
  content: String!
  createdAt: DateTime!
  updatedAt: DateTime!
  
  # Relationships
  author: UserType!
  post: PostType!
  tags: [TagType]
}
```

## 🔢 Scalar Types

### Built-in Scalars
- `ID` - Unique identifier
- `String` - Text data
- `Int` - Integer numbers
- `Float` - Floating-point numbers
- `Boolean` - True/false values

### Custom Scalars
- `DateTime` - ISO 8601 datetime strings
- `Date` - ISO 8601 date strings
- `Time` - ISO 8601 time strings
- `JSONString` - JSON-encoded strings
- `UUID` - UUID strings
- `Decimal` - Decimal numbers
- `Upload` - File upload type

## 📊 Enums

### PostStatusChoices
```graphql
enum PostStatusChoices {
  DRAFT      # "Brouillon"
  PUBLISHED  # "Publié"
  ARCHIVED   # "Archivé"
}
```

### OrderingChoices
```graphql
enum OrderingChoices {
  ASC
  DESC
}
```

## ❌ Error Handling

### Error Types

#### GraphQL Errors
Standard GraphQL errors with extensions:

```json
{
  "errors": [
    {
      "message": "You don't have permission to access this resource",
      "locations": [{"line": 2, "column": 3}],
      "path": ["post"],
      "extensions": {
        "code": "PERMISSION_DENIED",
        "requiredPermission": "view_post",
        "userPermissions": ["add_comment"]
      }
    }
  ]
}
```

#### Validation Errors
Field-specific validation errors with enhanced field extraction:

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
          "field": "content", 
          "message": "Ensure this field has at least 10 characters."
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

#### Database Constraint Errors
Automatic field extraction for database constraint violations:

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

#### Foreign Key Validation Errors
Enhanced error messages for foreign key constraints:

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

#### Rate Limiting Errors
```json
{
  "errors": [
    {
      "message": "Rate limit exceeded. You have made 100 requests in the last hour.",
      "extensions": {
        "code": "RATE_LIMITED",
        "limit": 100,
        "window": 3600,
        "remaining": 0,
        "resetTime": "2024-01-15T13:00:00Z",
        "retryAfter": 2700
      }
    }
  ]
}
```

#### Query Complexity Errors
```json
{
  "errors": [
    {
      "message": "Query complexity limit exceeded",
      "extensions": {
        "code": "QUERY_COMPLEXITY_EXCEEDED",
        "maxComplexity": 100,
        "actualComplexity": 150,
        "suggestions": [
          "Reduce the number of nested fields",
          "Use pagination with smaller page sizes"
        ]
      }
    }
  ]
}
```

### Error Codes

| Code | Description | Field Extraction |
|------|-------------|------------------|
| `UNAUTHENTICATED` | User is not authenticated | N/A |
| `PERMISSION_DENIED` | User lacks required permissions | N/A |
| `VALIDATION_ERROR` | Input validation failed | ✅ Automatic field detection |
| `RATE_LIMITED` | Rate limit exceeded | N/A |
| `QUERY_COMPLEXITY_EXCEEDED` | Query too complex | N/A |
| `QUERY_DEPTH_EXCEEDED` | Query too deep | N/A |
| `OBJECT_NOT_FOUND` | Requested object doesn't exist | N/A |
| `DUPLICATE_ENTRY` | Unique constraint violation | ✅ Automatic field extraction |
| `FOREIGN_KEY_ERROR` | Invalid foreign key reference | ✅ Enhanced field mapping |
| `NOT_NULL_CONSTRAINT` | Required field missing | ✅ Automatic field detection |

## 📚 Usage Examples

### Complete CRUD Workflow

```graphql
# 1. Register and login
mutation Register {
  register(data: {
    username: "johndoe"
    email: "john@example.com"
    password: "SecurePass123!"
    firstName: "John"
    lastName: "Doe"
  }) {
    success
    accessToken
    user { username }
  }
}

# 2. Create a category
mutation CreateCategory {
  createCategory(input: {
    name: "Technology"
    description: "Posts about technology"
  }) {
    ok
    category { id name }
  }
}

# 3. Create a post
mutation CreatePost {
  createPost(input: {
    title: "Getting Started with GraphQL"
    content: "GraphQL is a powerful query language..."
    status: PUBLISHED
    categoryId: "1"
  }) {
    ok
    post {
      id
      title
      status
      author { username }
      category { name }
    }
  }
}

# 4. Query posts with filtering
query GetPosts {
  posts(
    filters: {
      status: PUBLISHED
      author__username: "johndoe"
    }
    orderBy: ["-createdAt"]
    limit: 10
  ) {
    id
    title
    createdAt
    author { username }
  }
}

# 5. Update the post
mutation UpdatePost {
  updatePost(input: {
    id: "1"
    title: "Updated: Getting Started with GraphQL"
  }) {
    ok
    post {
      id
      title
      updatedAt
    }
  }
}

# 6. Check security info
query SecurityCheck {
  securityInfo {
    rateLimiting {
      remainingRequests
    }
    authentication {
      isAuthenticated
      user { username }
    }
  }
}
```

### Advanced Filtering Example

```graphql
query AdvancedSearch($search: String!, $dateFrom: DateTime!, $dateTo: DateTime!) {
  posts(filters: {
    AND: [
      {
        OR: [
          { title__icontains: $search }
          { content__icontains: $search }
          { author__username__icontains: $search }
        ]
      }
      {
        status: PUBLISHED
        createdAt__range: [$dateFrom, $dateTo]
      }
      {
        NOT: {
          title__startswith: "Draft:"
        }
      }
    ]
  }) {
    id
    title
    author { username }
    createdAt
  }
}
```

This comprehensive API reference covers all aspects of the GraphQL schema generated by the Django GraphQL Auto-Generation System, including security features, CRUD operations, and advanced querying capabilities.