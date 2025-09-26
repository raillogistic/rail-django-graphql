# Authentication Examples

## Overview

This guide provides comprehensive examples for using the JWT authentication system in the Django GraphQL Auto-Generation System. The authentication system provides secure user registration, login, token management, and session handling.

## 🔐 Authentication Flow

### Complete Authentication Workflow

```mermaid
sequenceDiagram
    participant Client
    participant GraphQL API
    participant Auth System
    participant Database

    Client->>GraphQL API: Register User
    GraphQL API->>Auth System: Validate Registration Data
    Auth System->>Database: Create User
    Database-->>Auth System: User Created
    Auth System-->>GraphQL API: Registration Success
    GraphQL API-->>Client: User + Success Response

    Client->>GraphQL API: Login Request
    GraphQL API->>Auth System: Validate Credentials
    Auth System->>Database: Check User
    Database-->>Auth System: User Valid
    Auth System-->>GraphQL API: JWT Tokens
    GraphQL API-->>Client: Access + Refresh Tokens

    Client->>GraphQL API: Authenticated Request
    GraphQL API->>Auth System: Validate Token
    Auth System-->>GraphQL API: Token Valid
    GraphQL API-->>Client: Protected Data
```

## 📝 Registration Examples

### Basic User Registration

```graphql
mutation RegisterUser {
  register(userData: {
    username: "johndoe"
    email: "john.doe@example.com"
    password: "SecurePassword123!"
    firstName: "John"
    lastName: "Doe"
  }) {
    ok
    user {
      id
      username
      email
      firstName
      lastName
      dateJoined
      isActive
    }
    errors
  }
}
```

**Response:**
```json
{
  "data": {
    "register": {
      "ok": true,
      "user": {
        "id": "1",
        "username": "johndoe",
        "email": "john.doe@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "dateJoined": "2024-01-15T10:30:00Z",
        "isActive": true
      },
      "errors": []
    }
  }
}
```

### Registration with Validation Errors

```graphql
mutation RegisterUserWithErrors {
  register(userData: {
    username: "jo"  # Too short
    email: "invalid-email"  # Invalid format
    password: "123"  # Too weak
    firstName: ""  # Empty
    lastName: "Doe"
  }) {
    ok
    user {
      id
      username
    }
    errors
  }
}
```

**Response:**
```json
{
  "data": {
    "register": {
      "ok": false,
      "user": null,
      "errors": [
        "Username must be at least 3 characters long",
        "Enter a valid email address",
        "Password must be at least 8 characters long",
        "First name is required"
      ]
    }
  }
}
```

## 🔑 Login Examples

### Successful Login

```graphql
mutation LoginUser {
  login(username: "johndoe", password: "SecurePassword123!") {
    ok
    token
    refreshToken
    user {
      id
      username
      email
      firstName
      lastName
      isStaff
      isSuperuser
      lastLogin
    }
    errors
  }
}
```

**Response:**
```json
{
  "data": {
    "login": {
      "ok": true,
      "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refreshToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "user": {
        "id": "1",
        "username": "johndoe",
        "email": "john.doe@example.com",
        "firstName": "John",
        "lastName": "Doe",
        "isStaff": false,
        "isSuperuser": false,
        "lastLogin": "2024-01-15T14:30:00Z"
      },
      "errors": []
    }
  }
}
```

### Failed Login Attempt

```graphql
mutation LoginUserFailed {
  login(username: "johndoe", password: "wrongpassword") {
    ok
    token
    refreshToken
    user {
      id
    }
    errors
  }
}
```

**Response:**
```json
{
  "data": {
    "login": {
      "ok": false,
      "token": null,
      "refreshToken": null,
      "user": null,
      "errors": [
        "Invalid username or password"
      ]
    }
  }
}
```

## 🔄 Token Management

### Token Refresh

```graphql
mutation RefreshAuthToken {
  refreshToken(token: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...") {
    ok
    token
    refreshToken
    errors
  }
}
```

**Response:**
```json
{
  "data": {
    "refreshToken": {
      "ok": true,
      "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refreshToken": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "errors": []
    }
  }
}
```

### Expired Token Refresh

```graphql
mutation RefreshExpiredToken {
  refreshToken(token: "expired_refresh_token") {
    ok
    token
    refreshToken
    errors
  }
}
```

**Response:**
```json
{
  "data": {
    "refreshToken": {
      "ok": false,
      "token": null,
      "refreshToken": null,
      "errors": [
        "Refresh token has expired"
      ]
    }
  }
}
```

## 👤 User Information

### Get Current User (Authenticated)

```graphql
query GetCurrentUser {
  me {
    id
    username
    email
    firstName
    lastName
    isActive
    isStaff
    isSuperuser
    dateJoined
    lastLogin
    groups {
      id
      name
    }
  }
}
```

**Headers:**
```json
{
  "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
  "data": {
    "me": {
      "id": "1",
      "username": "johndoe",
      "email": "john.doe@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "isActive": true,
      "isStaff": false,
      "isSuperuser": false,
      "dateJoined": "2024-01-15T10:30:00Z",
      "lastLogin": "2024-01-15T14:30:00Z",
      "groups": [
        {
          "id": "1",
          "name": "Users"
        }
      ]
    }
  }
}
```

### Unauthenticated Access

```graphql
query GetCurrentUserUnauthenticated {
  me {
    id
    username
  }
}
```

**Response:**
```json
{
  "errors": [
    {
      "message": "Authentication required",
      "locations": [{"line": 2, "column": 3}],
      "path": ["me"]
    }
  ],
  "data": {
    "me": null
  }
}
```

## 🚪 Logout

### User Logout

```graphql
mutation LogoutUser {
  logout {
    ok
    errors
  }
}
```

**Headers:**
```json
{
  "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
  "data": {
    "logout": {
      "ok": true,
      "errors": []
    }
  }
}
```

## 🔧 Client Implementation Examples

### JavaScript/React Example

```javascript
// Authentication service
class AuthService {
  constructor() {
    this.token = localStorage.getItem('accessToken');
    this.refreshToken = localStorage.getItem('refreshToken');
  }

  async register(userData) {
    const mutation = `
      mutation RegisterUser($userData: UserRegistrationInput!) {
        register(userData: $userData) {
          ok
          user {
            id
            username
            email
          }
          errors
        }
      }
    `;

    const response = await this.graphqlRequest(mutation, { userData });
    return response.data.register;
  }

  async login(username, password) {
    const mutation = `
      mutation LoginUser($username: String!, $password: String!) {
        login(username: $username, password: $password) {
          ok
          token
          refreshToken
          user {
            id
            username
            email
          }
          errors
        }
      }
    `;

    const response = await this.graphqlRequest(mutation, { username, password });
    
    if (response.data.login.ok) {
      this.token = response.data.login.token;
      this.refreshToken = response.data.login.refreshToken;
      localStorage.setItem('accessToken', this.token);
      localStorage.setItem('refreshToken', this.refreshToken);
    }

    return response.data.login;
  }

  async refreshAccessToken() {
    const mutation = `
      mutation RefreshToken($token: String!) {
        refreshToken(token: $token) {
          ok
          token
          refreshToken
          errors
        }
      }
    `;

    const response = await this.graphqlRequest(mutation, { token: this.refreshToken });
    
    if (response.data.refreshToken.ok) {
      this.token = response.data.refreshToken.token;
      this.refreshToken = response.data.refreshToken.refreshToken;
      localStorage.setItem('accessToken', this.token);
      localStorage.setItem('refreshToken', this.refreshToken);
    }

    return response.data.refreshToken;
  }

  async getCurrentUser() {
    const query = `
      query GetCurrentUser {
        me {
          id
          username
          email
          firstName
          lastName
        }
      }
    `;

    const response = await this.graphqlRequest(query);
    return response.data.me;
  }

  async logout() {
    const mutation = `
      mutation LogoutUser {
        logout {
          ok
          errors
        }
      }
    `;

    const response = await this.graphqlRequest(mutation);
    
    if (response.data.logout.ok) {
      this.token = null;
      this.refreshToken = null;
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    }

    return response.data.logout;
  }

  async graphqlRequest(query, variables = {}) {
    const headers = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch('/graphql/', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        query,
        variables
      })
    });

    const data = await response.json();

    // Handle token expiration
    if (data.errors && data.errors.some(error => error.message.includes('token'))) {
      const refreshResult = await this.refreshAccessToken();
      if (refreshResult.ok) {
        // Retry original request with new token
        headers['Authorization'] = `Bearer ${this.token}`;
        const retryResponse = await fetch('/graphql/', {
          method: 'POST',
          headers,
          body: JSON.stringify({
            query,
            variables
          })
        });
        return await retryResponse.json();
      }
    }

    return data;
  }

  isAuthenticated() {
    return !!this.token;
  }
}

// Usage example
const authService = new AuthService();

// Register new user
const registerResult = await authService.register({
  username: 'newuser',
  email: 'newuser@example.com',
  password: 'SecurePassword123!',
  firstName: 'New',
  lastName: 'User'
});

// Login user
const loginResult = await authService.login('newuser', 'SecurePassword123!');

// Get current user
const currentUser = await authService.getCurrentUser();

// Logout
const logoutResult = await authService.logout();
```

### Python/Django Client Example

```python
import requests
import json
from datetime import datetime, timedelta

class GraphQLAuthClient:
    def __init__(self, endpoint='http://localhost:8000/graphql/'):
        self.endpoint = endpoint
        self.token = None
        self.refresh_token = None

    def _make_request(self, query, variables=None):
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        
        response = requests.post(
            self.endpoint,
            headers=headers,
            data=json.dumps(payload)
        )
        
        return response.json()

    def register(self, user_data):
        mutation = """
        mutation RegisterUser($userData: UserRegistrationInput!) {
            register(userData: $userData) {
                ok
                user {
                    id
                    username
                    email
                }
                errors
            }
        }
        """
        
        return self._make_request(mutation, {'userData': user_data})

    def login(self, username, password):
        mutation = """
        mutation LoginUser($username: String!, $password: String!) {
            login(username: $username, password: $password) {
                ok
                token
                refreshToken
                user {
                    id
                    username
                    email
                }
                errors
            }
        }
        """
        
        result = self._make_request(mutation, {
            'username': username,
            'password': password
        })
        
        if result['data']['login']['ok']:
            self.token = result['data']['login']['token']
            self.refresh_token = result['data']['login']['refreshToken']
        
        return result

    def refresh_access_token(self):
        mutation = """
        mutation RefreshToken($token: String!) {
            refreshToken(token: $token) {
                ok
                token
                refreshToken
                errors
            }
        }
        """
        
        result = self._make_request(mutation, {'token': self.refresh_token})
        
        if result['data']['refreshToken']['ok']:
            self.token = result['data']['refreshToken']['token']
            self.refresh_token = result['data']['refreshToken']['refreshToken']
        
        return result

    def get_current_user(self):
        query = """
        query GetCurrentUser {
            me {
                id
                username
                email
                firstName
                lastName
            }
        }
        """
        
        return self._make_request(query)

    def logout(self):
        mutation = """
        mutation LogoutUser {
            logout {
                ok
                errors
            }
        }
        """
        
        result = self._make_request(mutation)
        
        if result['data']['logout']['ok']:
            self.token = None
            self.refresh_token = None
        
        return result

# Usage example
client = GraphQLAuthClient()

# Register new user
register_result = client.register({
    'username': 'pythonuser',
    'email': 'python@example.com',
    'password': 'SecurePassword123!',
    'firstName': 'Python',
    'lastName': 'User'
})

# Login
login_result = client.login('pythonuser', 'SecurePassword123!')

# Get current user
user_info = client.get_current_user()

# Logout
logout_result = client.logout()
```

## 🔒 Security Considerations

### Token Security
- Store tokens securely (avoid localStorage for sensitive applications)
- Implement proper token rotation
- Use HTTPS in production
- Set appropriate token expiration times

### Password Security
- Enforce strong password policies
- Implement password hashing (handled automatically)
- Consider implementing password reset functionality
- Monitor failed login attempts

### Session Management
- Implement proper logout functionality
- Handle token expiration gracefully
- Consider implementing session timeout
- Monitor active sessions

## 🧪 Testing Authentication

### Unit Test Examples

```python
import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from graphene.test import Client
from your_app.schema import schema

class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = Client(schema)
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'firstName': 'Test',
            'lastName': 'User'
        }

    def test_user_registration(self):
        mutation = """
        mutation RegisterUser($userData: UserRegistrationInput!) {
            register(userData: $userData) {
                ok
                user {
                    username
                    email
                }
                errors
            }
        }
        """
        
        result = self.client.execute(mutation, variables={'userData': self.user_data})
        
        assert result['data']['register']['ok'] is True
        assert result['data']['register']['user']['username'] == 'testuser'
        assert len(result['data']['register']['errors']) == 0

    def test_user_login(self):
        # Create user first
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        
        mutation = """
        mutation LoginUser($username: String!, $password: String!) {
            login(username: $username, password: $password) {
                ok
                token
                user {
                    username
                }
                errors
            }
        }
        """
        
        result = self.client.execute(mutation, variables={
            'username': 'testuser',
            'password': 'TestPassword123!'
        })
        
        assert result['data']['login']['ok'] is True
        assert result['data']['login']['token'] is not None
        assert result['data']['login']['user']['username'] == 'testuser'

    def test_authenticated_query(self):
        # Create and login user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        
        # Simulate authentication
        self.client.context = type('Context', (), {'user': user})()
        
        query = """
        query GetCurrentUser {
            me {
                username
                email
            }
        }
        """
        
        result = self.client.execute(query)
        
        assert result['data']['me']['username'] == 'testuser'
        assert result['data']['me']['email'] == 'test@example.com'
```

## 📚 Additional Resources

- [Security Overview](../features/security.md)
- [Permission Examples](permission-examples.md)
- [Security Testing Guide](../development/security-testing.md)
- [JWT Configuration](../setup/jwt-configuration.md)