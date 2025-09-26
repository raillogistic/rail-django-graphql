# Practical Security Examples

## Overview

This guide provides real-world, practical examples demonstrating all security features of the Django GraphQL Auto-Generation System. These examples show complete workflows, common scenarios, and best practices for implementing secure GraphQL applications.

## 🚀 Complete Authentication Workflow

### User Registration and Login Flow

```graphql
# Step 1: Register a new user
mutation RegisterUser {
  register(data: {
    username: "johndoe"
    email: "john@example.com"
    password: "SecurePass123!"
    firstName: "John"
    lastName: "Doe"
    phoneNumber: "+1-555-123-4567"
  }) {
    success
    user {
      id
      username
      email
      firstName
      lastName
      dateJoined
    }
    accessToken
    refreshToken
    errors
  }
}
```

**Response:**
```json
{
  "data": {
    "register": {
      "success": true,
      "user": {
        "id": "25",
        "username": "johndoe",
        "email": "john@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "dateJoined": "2024-01-15T10:30:00Z"
      },
      "accessToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refreshToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "errors": []
    }
  }
}
```

```graphql
# Step 2: Login with credentials
mutation LoginUser {
  login(data: {
    username: "johndoe"
    password: "SecurePass123!"
  }) {
    success
    user {
      id
      username
      email
      lastLogin
      groups {
        name
        permissions {
          name
          codename
        }
      }
    }
    accessToken
    refreshToken
    errors
  }
}
```

```graphql
# Step 3: Get current user info (with token in header)
# Header: Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
query GetCurrentUser {
  me {
    id
    username
    email
    profile {
      bio
      avatar
      website
    }
    permissions {
      canCreatePosts
      canEditPosts
      canDeletePosts
      canViewAnalytics
    }
    securityInfo {
      lastLogin
      loginCount
      failedLoginAttempts
      accountLocked
      mfaEnabled
    }
  }
}
```

**Response:**
```json
{
  "data": {
    "me": {
      "id": "25",
      "username": "johndoe",
      "email": "john@example.com",
      "profile": {
        "bio": "Software developer passionate about GraphQL",
        "avatar": "https://example.com/avatars/johndoe.jpg",
        "website": "https://johndoe.dev"
      },
      "permissions": {
        "canCreatePosts": true,
        "canEditPosts": true,
        "canDeletePosts": false,
        "canViewAnalytics": false
      },
      "securityInfo": {
        "lastLogin": "2024-01-15T10:30:00Z",
        "loginCount": 15,
        "failedLoginAttempts": 0,
        "accountLocked": false,
        "mfaEnabled": false
      }
    }
  }
}
```

## 🔐 Multi-Level Permission Examples

### Blog Post Management with Permissions

```graphql
# Create a blog post (requires authentication)
mutation CreateBlogPost {
  createPost(data: {
    title: "Getting Started with GraphQL Security"
    content: "In this post, we'll explore the security features..."
    status: "DRAFT"
    tags: ["graphql", "security", "django"]
    category: "TECHNOLOGY"
  }) {
    ok
    post {
      id
      title
      status
      author {
        username
      }
      createdAt
      permissions {
        canEdit
        canDelete
        canPublish
      }
    }
    errors
  }
}
```

**Response:**
```json
{
  "data": {
    "createPost": {
      "ok": true,
      "post": {
        "id": "42",
        "title": "Getting Started with GraphQL Security",
        "status": "DRAFT",
        "author": {
          "username": "johndoe"
        },
        "createdAt": "2024-01-15T11:00:00Z",
        "permissions": {
          "canEdit": true,
          "canDelete": true,
          "canPublish": false
        }
      },
      "errors": []
    }
  }
}
```

```graphql
# Try to edit someone else's post (should fail)
mutation EditOthersPost {
  updatePost(id: "35", data: {
    title: "Hacked Title"
    content: "Malicious content"
  }) {
    ok
    post {
      id
      title
    }
    errors
  }
}
```

**Response (Permission Denied):**
```json
{
  "data": {
    "updatePost": {
      "ok": false,
      "post": null,
      "errors": [
        "You don't have permission to edit this post"
      ]
    }
  }
}
```

```graphql
# Staff user can edit any post
# Header: Authorization: Bearer <staff-user-token>
mutation StaffEditPost {
  updatePost(id: "35", data: {
    status: "PUBLISHED"
    moderatorNote: "Approved for publication"
  }) {
    ok
    post {
      id
      status
      moderatorNote
      lastModified
    }
    errors
  }
}
```

### Role-Based Access Control Example

```graphql
# Admin user accessing analytics (requires admin role)
query AdminAnalytics {
  analytics {
    userStats {
      totalUsers
      activeUsers
      newUsersToday
    }
    postStats {
      totalPosts
      publishedPosts
      drafts
      pendingReview
    }
    securityStats {
      failedLogins
      blockedIPs
      suspiciousActivity
    }
    performanceStats {
      avgQueryTime
      slowQueries
      errorRate
    }
  }
}
```

**Response (Admin User):**
```json
{
  "data": {
    "analytics": {
      "userStats": {
        "totalUsers": 1250,
        "activeUsers": 890,
        "newUsersToday": 15
      },
      "postStats": {
        "totalPosts": 3420,
        "publishedPosts": 2890,
        "drafts": 430,
        "pendingReview": 100
      },
      "securityStats": {
        "failedLogins": 25,
        "blockedIPs": 5,
        "suspiciousActivity": 2
      },
      "performanceStats": {
        "avgQueryTime": 145.5,
        "slowQueries": 12,
        "errorRate": 0.02
      }
    }
  }
}
```

**Response (Regular User):**
```json
{
  "errors": [
    {
      "message": "You don't have permission to access analytics",
      "locations": [{"line": 2, "column": 3}],
      "path": ["analytics"],
      "extensions": {
        "code": "PERMISSION_DENIED",
        "requiredRole": "admin",
        "userRole": "user"
      }
    }
  ],
  "data": {
    "analytics": null
  }
}
```

## 🛡️ Input Validation in Action

### E-commerce Order Creation with Validation

```graphql
# Create order with comprehensive validation
mutation CreateOrder {
  createOrder(data: {
    items: [
      {
        productId: "PROD001"
        quantity: 2
        customizations: {
          color: "Blue"
          size: "Large"
          engraving: "Happy Birthday! <script>alert('xss')</script>"
        }
      },
      {
        productId: "PROD002"
        quantity: -1  # Invalid quantity
      }
    ]
    shippingAddress: {
      street: "123 Main St"
      city: "New York"
      state: "NY"
      zipCode: "10001"
      country: "US"
    }
    billingAddress: {
      street: "456 Oak Ave"
      city: "Los Angeles"
      state: "CA"
      zipCode: "90210"
      country: "US"
    }
    paymentMethod: {
      type: "CREDIT_CARD"
      cardNumber: "4111111111111111"
      expiryMonth: 12
      expiryYear: 2025
      cvv: "123"
      cardholderName: "John Doe"
    }
    couponCode: "SAVE20"
    specialInstructions: "Please deliver between 9 AM and 5 PM. <img src=x onerror=alert('xss')>"
  }) {
    ok
    order {
      id
      orderNumber
      status
      total
      items {
        product {
          name
        }
        quantity
        price
        customizations
      }
      shippingAddress {
        formatted
      }
      estimatedDelivery
    }
    errors
  }
}
```

**Response (With Validation Errors and Sanitization):**
```json
{
  "data": {
    "createOrder": {
      "ok": false,
      "order": null,
      "errors": [
        "Item quantity must be greater than 0",
        "Invalid coupon code: SAVE20",
        "Credit card number is invalid"
      ]
    }
  }
}
```

### User Profile Update with Field Validation

```graphql
# Update user profile with various validation scenarios
mutation UpdateUserProfile {
  updateProfile(data: {
    bio: "Software developer passionate about GraphQL and security. Visit my site: javascript:alert('xss')"
    website: "not-a-valid-url"
    socialMedia: {
      twitter: "https://twitter.com/johndoe"
      linkedin: "https://linkedin.com/in/johndoe"
      github: "https://github.com/johndoe"
      instagram: "invalid-instagram-url"
    }
    contactInfo: {
      email: "invalid-email-format"
      phone: "123-456-7890"
      alternatePhone: "+1-555-987-6543"
    }
    preferences: {
      newsletter: true
      notifications: {
        email: true
        sms: false
        push: true
      }
      privacy: {
        showEmail: false
        showPhone: false
        profileVisibility: "PUBLIC"
      }
    }
  }) {
    ok
    profile {
      bio
      website
      socialMedia {
        twitter
        linkedin
        github
        instagram
      }
      contactInfo {
        email
        phone
        alternatePhone
      }
    }
    errors
  }
}
```

**Response (With Sanitization and Validation):**
```json
{
  "data": {
    "updateProfile": {
      "ok": false,
      "profile": null,
      "errors": [
        "Website must be a valid URL",
        "Instagram URL is invalid",
        "Email format is invalid"
      ]
    }
  }
}
```

## ⚡ Rate Limiting Scenarios

### API Usage Patterns

```graphql
# Rapid successive queries (testing rate limits)
query GetPosts {
  posts(first: 10) {
    edges {
      node {
        id
        title
        author {
          username
        }
        createdAt
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

**After 100 requests in an hour (anonymous user):**
```json
{
  "errors": [
    {
      "message": "Rate limit exceeded. You have made 100 requests in the last hour. Please try again in 45 minutes.",
      "extensions": {
        "code": "RATE_LIMITED",
        "limit": 100,
        "window": 3600,
        "remaining": 0,
        "resetTime": "2024-01-15T12:45:00Z",
        "retryAfter": 2700
      }
    }
  ],
  "data": null
}
```

### Operation-Specific Rate Limits

```graphql
# Password reset (limited to 5 per hour)
mutation RequestPasswordReset {
  requestPasswordReset(email: "john@example.com") {
    success
    message
  }
}
```

**After 5 attempts:**
```json
{
  "errors": [
    {
      "message": "Too many password reset requests. Please try again in 55 minutes.",
      "extensions": {
        "code": "OPERATION_RATE_LIMITED",
        "operation": "requestPasswordReset",
        "limit": 5,
        "window": 3600,
        "remaining": 0,
        "resetTime": "2024-01-15T12:55:00Z"
      }
    }
  ],
  "data": null
}
```

## 📊 Query Complexity Management

### Simple vs Complex Queries

```graphql
# Simple query (complexity ~10)
query SimplePostList {
  posts(first: 5) {
    edges {
      node {
        id
        title
        status
        createdAt
      }
    }
  }
}
```

```graphql
# Complex query (complexity ~200, exceeds limit)
query ComplexPostAnalysis {
  posts(first: 20) {
    edges {
      node {
        id
        title
        content
        author {
          id
          username
          profile {
            bio
            avatar
            socialMedia {
              twitter
              linkedin
            }
          }
          posts(first: 10) {
            edges {
              node {
                id
                title
                comments(first: 5) {
                  edges {
                    node {
                      id
                      content
                      author {
                        username
                        profile {
                          avatar
                        }
                      }
                      replies(first: 3) {
                        edges {
                          node {
                            id
                            content
                            author {
                              username
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        comments(first: 10) {
          edges {
            node {
              id
              content
              author {
                username
              }
            }
          }
        }
        tags {
          id
          name
          posts(first: 5) {
            edges {
              node {
                id
                title
              }
            }
          }
        }
      }
    }
  }
}
```

**Response (Complexity Exceeded):**
```json
{
  "errors": [
    {
      "message": "Query complexity limit exceeded",
      "extensions": {
        "code": "QUERY_COMPLEXITY_EXCEEDED",
        "maxComplexity": 100,
        "actualComplexity": 200,
        "suggestions": [
          "Reduce the number of nested fields",
          "Use pagination with smaller page sizes",
          "Split into multiple smaller queries",
          "Consider using fragments to optimize structure"
        ],
        "complexityBreakdown": {
          "posts": 20,
          "posts.author": 40,
          "posts.author.posts": 80,
          "posts.comments": 30,
          "posts.tags": 30
        }
      }
    }
  ],
  "data": null
}
```

### Optimized Query Alternative

```graphql
# Optimized version using fragments and pagination
fragment PostSummary on Post {
  id
  title
  status
  createdAt
}

fragment AuthorInfo on User {
  id
  username
  profile {
    avatar
  }
}

query OptimizedPostList {
  posts(first: 10) {
    edges {
      node {
        ...PostSummary
        author {
          ...AuthorInfo
        }
        commentCount
        tagCount
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

## 🔍 Security Monitoring and Alerts

### Real-time Security Information

```graphql
# Monitor security status
query SecurityDashboard {
  securityInfo {
    rateLimiting {
      remainingRequests
      windowResetTime
      currentComplexityLimit
      currentDepthLimit
    }
    authentication {
      isAuthenticated
      user {
        username
        lastLogin
        loginCount
      }
      tokenExpiresAt
      sessionExpiresAt
    }
    permissions {
      effectivePermissions
      roleHierarchy
      groupMemberships
    }
    recentActivity {
      lastQueries(limit: 5) {
        query
        timestamp
        complexity
        executionTime
        success
      }
      securityEvents(limit: 5) {
        type
        timestamp
        description
        severity
      }
    }
  }
  
  queryStats {
    totalQueries
    avgComplexity
    avgDepth
    avgExecutionTime
    successRate
    errorBreakdown {
      validationErrors
      permissionErrors
      rateLimitErrors
      complexityErrors
      depthErrors
    }
  }
}
```

**Response:**
```json
{
  "data": {
    "securityInfo": {
      "rateLimiting": {
        "remainingRequests": 87,
        "windowResetTime": "2024-01-15T13:00:00Z",
        "currentComplexityLimit": 100,
        "currentDepthLimit": 6
      },
      "authentication": {
        "isAuthenticated": true,
        "user": {
          "username": "johndoe",
          "lastLogin": "2024-01-15T11:30:00Z",
          "loginCount": 16
        },
        "tokenExpiresAt": "2024-01-15T12:30:00Z",
        "sessionExpiresAt": "2024-01-15T15:30:00Z"
      },
      "permissions": {
        "effectivePermissions": [
          "create_post",
          "edit_own_post",
          "delete_own_post",
          "create_comment"
        ],
        "roleHierarchy": ["user", "content_creator"],
        "groupMemberships": ["Users", "Content Creators"]
      },
      "recentActivity": {
        "lastQueries": [
          {
            "query": "GetPosts",
            "timestamp": "2024-01-15T12:15:00Z",
            "complexity": 25,
            "executionTime": 150,
            "success": true
          },
          {
            "query": "CreatePost",
            "timestamp": "2024-01-15T12:10:00Z",
            "complexity": 15,
            "executionTime": 200,
            "success": true
          }
        ],
        "securityEvents": [
          {
            "type": "AUTHENTICATION_SUCCESS",
            "timestamp": "2024-01-15T11:30:00Z",
            "description": "User johndoe logged in successfully",
            "severity": "INFO"
          },
          {
            "type": "RATE_LIMIT_WARNING",
            "timestamp": "2024-01-15T12:00:00Z",
            "description": "User approaching rate limit (80/100 requests)",
            "severity": "WARNING"
          }
        ]
      }
    },
    "queryStats": {
      "totalQueries": 1250,
      "avgComplexity": 28.5,
      "avgDepth": 4.2,
      "avgExecutionTime": 175.3,
      "successRate": 98.4,
      "errorBreakdown": {
        "validationErrors": 12,
        "permissionErrors": 8,
        "rateLimitErrors": 3,
        "complexityErrors": 2,
        "depthErrors": 1
      }
    }
  }
}
```

## 🧪 Security Testing Scenarios

### Penetration Testing Queries

```graphql
# Test XSS protection
mutation TestXSSProtection {
  createComment(data: {
    content: "<script>alert('XSS Attack!');</script>This is a test comment"
    postId: "42"
  }) {
    ok
    comment {
      id
      content
      sanitizedContent
    }
    errors
  }
}
```

**Response (XSS Sanitized):**
```json
{
  "data": {
    "createComment": {
      "ok": true,
      "comment": {
        "id": "156",
        "content": "This is a test comment",
        "sanitizedContent": "This is a test comment"
      },
      "errors": []
    }
  }
}
```

```graphql
# Test SQL injection protection
query TestSQLInjection {
  posts(filters: {
    title_contains: "'; DROP TABLE posts; SELECT * FROM users WHERE '1'='1"
  }) {
    id
    title
  }
}
```

**Response (Safe - No SQL Injection):**
```json
{
  "data": {
    "posts": []
  }
}
```

```graphql
# Test authorization bypass attempt
mutation TestAuthBypass {
  updateUser(id: "1", data: {
    isStaff: true
    isSuperuser: true
    groups: ["Administrators"]
  }) {
    ok
    user {
      id
      isStaff
      isSuperuser
    }
    errors
  }
}
```

**Response (Permission Denied):**
```json
{
  "data": {
    "updateUser": {
      "ok": false,
      "user": null,
      "errors": [
        "You don't have permission to modify user privileges",
        "Field 'isStaff' is restricted to staff users only",
        "Field 'isSuperuser' is restricted to superusers only"
      ]
    }
  }
}
```

## 🔧 Client-Side Implementation Examples

### JavaScript/React Client

```javascript
// GraphQL client with security features
import { ApolloClient, InMemoryCache, createHttpLink, from } from '@apollo/client';
import { setContext } from '@apollo/client/link/context';
import { onError } from '@apollo/client/link/error';
import { RetryLink } from '@apollo/client/link/retry';

// HTTP link
const httpLink = createHttpLink({
  uri: 'https://api.example.com/graphql/',
});

// Auth link - adds JWT token to requests
const authLink = setContext((_, { headers }) => {
  const token = localStorage.getItem('accessToken');
  return {
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : "",
    }
  };
});

// Error link - handles authentication and rate limiting errors
const errorLink = onError(({ graphQLErrors, networkError, operation, forward }) => {
  if (graphQLErrors) {
    graphQLErrors.forEach(({ message, locations, path, extensions }) => {
      console.error(`GraphQL error: ${message}`);
      
      // Handle authentication errors
      if (extensions?.code === 'UNAUTHENTICATED') {
        // Redirect to login
        window.location.href = '/login';
      }
      
      // Handle rate limiting
      if (extensions?.code === 'RATE_LIMITED') {
        const retryAfter = extensions.retryAfter;
        console.warn(`Rate limited. Retry after ${retryAfter} seconds`);
        
        // Show user-friendly message
        showNotification(`Too many requests. Please wait ${retryAfter} seconds.`);
      }
      
      // Handle permission errors
      if (extensions?.code === 'PERMISSION_DENIED') {
        showNotification('You don\'t have permission to perform this action.');
      }
      
      // Handle query complexity errors
      if (extensions?.code === 'QUERY_COMPLEXITY_EXCEEDED') {
        console.warn('Query too complex:', extensions.suggestions);
        showNotification('Query is too complex. Please simplify your request.');
      }
    });
  }
  
  if (networkError) {
    console.error(`Network error: ${networkError}`);
  }
});

// Retry link - retries failed requests
const retryLink = new RetryLink({
  delay: {
    initial: 300,
    max: Infinity,
    jitter: true
  },
  attempts: {
    max: 3,
    retryIf: (error, _operation) => {
      // Retry on network errors but not on GraphQL errors
      return !!error && !error.result;
    }
  }
});

// Create Apollo Client
const client = new ApolloClient({
  link: from([authLink, errorLink, retryLink, httpLink]),
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      errorPolicy: 'all'
    },
    query: {
      errorPolicy: 'all'
    }
  }
});

// Security-aware React component
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, gql } from '@apollo/client';

const GET_SECURITY_INFO = gql`
  query GetSecurityInfo {
    securityInfo {
      rateLimiting {
        remainingRequests
        windowResetTime
      }
      authentication {
        isAuthenticated
        user {
          username
        }
        tokenExpiresAt
      }
    }
  }
`;

const CREATE_POST = gql`
  mutation CreatePost($data: PostInput!) {
    createPost(data: $data) {
      ok
      post {
        id
        title
        status
      }
      errors
    }
  }
`;

function SecurityAwareComponent() {
  const [rateLimitWarning, setRateLimitWarning] = useState(false);
  
  const { data: securityData, refetch: refetchSecurity } = useQuery(GET_SECURITY_INFO, {
    pollInterval: 30000, // Poll every 30 seconds
  });
  
  const [createPost, { loading, error }] = useMutation(CREATE_POST, {
    onCompleted: (data) => {
      if (data.createPost.ok) {
        console.log('Post created successfully');
        refetchSecurity(); // Update security info
      }
    },
    onError: (error) => {
      console.error('Error creating post:', error);
    }
  });
  
  // Monitor rate limiting
  useEffect(() => {
    if (securityData?.securityInfo?.rateLimiting) {
      const { remainingRequests } = securityData.securityInfo.rateLimiting;
      
      if (remainingRequests < 10) {
        setRateLimitWarning(true);
      } else {
        setRateLimitWarning(false);
      }
    }
  }, [securityData]);
  
  const handleCreatePost = (postData) => {
    // Check rate limit before making request
    if (rateLimitWarning) {
      if (!confirm('You are approaching your rate limit. Continue?')) {
        return;
      }
    }
    
    createPost({
      variables: {
        data: {
          title: postData.title,
          content: postData.content,
          status: 'DRAFT'
        }
      }
    });
  };
  
  return (
    <div>
      {/* Rate limit warning */}
      {rateLimitWarning && (
        <div className="alert alert-warning">
          ⚠️ You are approaching your rate limit. 
          Remaining requests: {securityData?.securityInfo?.rateLimiting?.remainingRequests}
        </div>
      )}
      
      {/* Security status */}
      <div className="security-status">
        <h3>Security Status</h3>
        <p>
          Authenticated: {securityData?.securityInfo?.authentication?.isAuthenticated ? '✅' : '❌'}
        </p>
        <p>
          User: {securityData?.securityInfo?.authentication?.user?.username || 'Anonymous'}
        </p>
        <p>
          Rate Limit: {securityData?.securityInfo?.rateLimiting?.remainingRequests || 0} requests remaining
        </p>
      </div>
      
      {/* Your component content */}
      <button 
        onClick={() => handleCreatePost({ title: 'Test Post', content: 'Test content' })}
        disabled={loading}
      >
        {loading ? 'Creating...' : 'Create Post'}
      </button>
      
      {error && (
        <div className="alert alert-error">
          Error: {error.message}
        </div>
      )}
    </div>
  );
}

export default SecurityAwareComponent;
```

### Python Client Example

```python
# Python client with security features
import requests
import json
import time
from datetime import datetime, timedelta
import jwt

class SecureGraphQLClient:
    """
    Client GraphQL sécurisé avec gestion des erreurs et de la sécurité.
    """
    
    def __init__(self, endpoint, access_token=None):
        self.endpoint = endpoint
        self.access_token = access_token
        self.refresh_token = None
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
        
    def set_tokens(self, access_token, refresh_token=None):
        """Définit les tokens d'authentification."""
        self.access_token = access_token
        self.refresh_token = refresh_token
        
    def get_headers(self):
        """Retourne les en-têtes pour les requêtes."""
        headers = {
            'Content-Type': 'application/json',
        }
        
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
            
        return headers
    
    def is_token_expired(self):
        """Vérifie si le token d'accès a expiré."""
        if not self.access_token:
            return True
            
        try:
            # Décode le token sans vérification (juste pour lire l'expiration)
            payload = jwt.decode(self.access_token, options={"verify_signature": False})
            exp = payload.get('exp')
            
            if exp:
                return datetime.utcnow().timestamp() > exp
                
        except jwt.InvalidTokenError:
            return True
            
        return False
    
    def refresh_access_token(self):
        """Rafraîchit le token d'accès."""
        if not self.refresh_token:
            raise Exception("No refresh token available")
            
        mutation = """
        mutation RefreshToken($refreshToken: String!) {
            refreshToken(refreshToken: $refreshToken) {
                success
                accessToken
                refreshToken
                errors
            }
        }
        """
        
        variables = {"refreshToken": self.refresh_token}
        
        response = self.execute(mutation, variables, skip_auth_check=True)
        
        if response.get('data', {}).get('refreshToken', {}).get('success'):
            token_data = response['data']['refreshToken']
            self.access_token = token_data['accessToken']
            if token_data.get('refreshToken'):
                self.refresh_token = token_data['refreshToken']
        else:
            raise Exception("Failed to refresh token")
    
    def check_rate_limit(self):
        """Vérifie les limites de taux."""
        if self.rate_limit_remaining is not None and self.rate_limit_remaining <= 0:
            if self.rate_limit_reset:
                wait_time = self.rate_limit_reset - time.time()
                if wait_time > 0:
                    print(f"Rate limit exceeded. Waiting {wait_time:.0f} seconds...")
                    time.sleep(wait_time)
    
    def execute(self, query, variables=None, skip_auth_check=False):
        """Exécute une requête GraphQL."""
        # Vérifier et rafraîchir le token si nécessaire
        if not skip_auth_check and self.is_token_expired():
            if self.refresh_token:
                self.refresh_access_token()
            else:
                raise Exception("Access token expired and no refresh token available")
        
        # Vérifier les limites de taux
        self.check_rate_limit()
        
        # Préparer la requête
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        # Faire la requête
        response = requests.post(
            self.endpoint,
            headers=self.get_headers(),
            json=payload
        )
        
        # Mettre à jour les informations de limite de taux
        self.rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
        if self.rate_limit_remaining:
            self.rate_limit_remaining = int(self.rate_limit_remaining)
            
        rate_limit_reset = response.headers.get('X-RateLimit-Reset')
        if rate_limit_reset:
            self.rate_limit_reset = int(rate_limit_reset)
        
        # Traiter la réponse
        if response.status_code == 200:
            data = response.json()
            
            # Gérer les erreurs GraphQL
            if 'errors' in data:
                for error in data['errors']:
                    self.handle_graphql_error(error)
            
            return data
        else:
            raise Exception(f"HTTP Error {response.status_code}: {response.text}")
    
    def handle_graphql_error(self, error):
        """Gère les erreurs GraphQL spécifiques."""
        extensions = error.get('extensions', {})
        code = extensions.get('code')
        
        if code == 'UNAUTHENTICATED':
            print("Authentication required")
            # Logique de redirection vers la connexion
            
        elif code == 'PERMISSION_DENIED':
            print(f"Permission denied: {error['message']}")
            
        elif code == 'RATE_LIMITED':
            retry_after = extensions.get('retryAfter', 60)
            print(f"Rate limited. Retry after {retry_after} seconds")
            time.sleep(retry_after)
            
        elif code == 'QUERY_COMPLEXITY_EXCEEDED':
            print(f"Query too complex: {error['message']}")
            suggestions = extensions.get('suggestions', [])
            for suggestion in suggestions:
                print(f"  - {suggestion}")
                
        elif code == 'VALIDATION_ERROR':
            print(f"Validation error: {error['message']}")
            
        else:
            print(f"GraphQL Error: {error['message']}")

# Exemple d'utilisation
def main():
    client = SecureGraphQLClient('https://api.example.com/graphql/')
    
    # Connexion
    login_mutation = """
    mutation Login($username: String!, $password: String!) {
        login(data: {username: $username, password: $password}) {
            success
            accessToken
            refreshToken
            user {
                username
            }
            errors
        }
    }
    """
    
    login_response = client.execute(login_mutation, {
        'username': 'johndoe',
        'password': 'SecurePass123!'
    })
    
    if login_response['data']['login']['success']:
        # Définir les tokens
        login_data = login_response['data']['login']
        client.set_tokens(login_data['accessToken'], login_data['refreshToken'])
        
        print(f"Logged in as: {login_data['user']['username']}")
        
        # Faire des requêtes sécurisées
        posts_query = """
        query GetPosts {
            posts(first: 10) {
                edges {
                    node {
                        id
                        title
                        author {
                            username
                        }
                    }
                }
            }
        }
        """
        
        posts_response = client.execute(posts_query)
        print(f"Retrieved {len(posts_response['data']['posts']['edges'])} posts")
        
        # Vérifier les informations de sécurité
        security_query = """
        query GetSecurityInfo {
            securityInfo {
                rateLimiting {
                    remainingRequests
                    windowResetTime
                }
                authentication {
                    user {
                        username
                    }
                    tokenExpiresAt
                }
            }
        }
        """
        
        security_response = client.execute(security_query)
        security_info = security_response['data']['securityInfo']
        
        print(f"Rate limit remaining: {security_info['rateLimiting']['remainingRequests']}")
        print(f"Token expires at: {security_info['authentication']['tokenExpiresAt']}")
        
    else:
        print("Login failed:", login_response['data']['login']['errors'])

if __name__ == '__main__':
    main()
```

## 📚 Best Practices Summary

### Security Implementation Checklist

1. **Authentication**
   - ✅ Implement JWT with proper expiration
   - ✅ Use refresh tokens for long-term sessions
   - ✅ Implement secure logout with token blacklisting
   - ✅ Add multi-factor authentication for sensitive operations

2. **Authorization**
   - ✅ Implement role-based access control
   - ✅ Use object-level permissions
   - ✅ Protect sensitive fields
   - ✅ Audit permission changes

3. **Input Validation**
   - ✅ Sanitize all user inputs
   - ✅ Validate field formats (email, URL, phone)
   - ✅ Implement business logic validation
   - ✅ Prevent XSS and SQL injection

4. **Rate Limiting**
   - ✅ Implement per-user rate limits
   - ✅ Use operation-specific limits
   - ✅ Provide clear error messages
   - ✅ Monitor and alert on violations

5. **Query Analysis**
   - ✅ Limit query complexity
   - ✅ Limit query depth
   - ✅ Monitor query performance
   - ✅ Provide optimization suggestions

6. **Monitoring**
   - ✅ Log security events
   - ✅ Monitor performance metrics
   - ✅ Set up alerting
   - ✅ Regular security audits

### Development Guidelines

1. **Security First**: Design with security in mind from the start
2. **Defense in Depth**: Use multiple security layers
3. **Principle of Least Privilege**: Grant minimum necessary permissions
4. **Regular Testing**: Implement comprehensive security testing
5. **Continuous Monitoring**: Monitor security metrics continuously
6. **User Education**: Educate users about security best practices

## 📚 Additional Resources

- [Security Overview](../features/security.md)
- [Authentication Examples](authentication-examples.md)
- [Permission Examples](permission-examples.md)
- [Validation Examples](validation-examples.md)
- [Security Configuration](../setup/security-configuration.md)
- [Performance Optimization](../development/performance.md)
- [Testing Guide](../development/testing.md)