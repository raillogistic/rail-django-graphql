# Security Implementation Guide

## Overview

The Django GraphQL Auto-Generation System includes a comprehensive security layer that provides enterprise-grade protection for your GraphQL API. This implementation covers authentication, authorization, input validation, rate limiting, and query analysis.

## 🔐 Security Architecture

### Core Security Components

1. **Authentication System** - JWT-based authentication with secure token management
2. **Permission System** - Multi-level authorization with role-based access control
3. **Input Validation** - Comprehensive input sanitization and validation
4. **Rate Limiting** - Configurable request rate limiting per user/IP
5. **Query Analysis** - Complexity and depth analysis to prevent malicious queries
6. **File Upload Security** - Comprehensive file validation, virus scanning, and quarantine system
7. **Security Monitoring** - Real-time security information and statistics

### Security Middleware Integration

The security system is integrated at the GraphQL middleware level, ensuring all requests are automatically protected:

```python
# Automatic security checks on every GraphQL request
GRAPHQL_SECURITY = {
    'ENABLE_AUTHENTICATION': True,
    'ENABLE_PERMISSIONS': True,
    'ENABLE_RATE_LIMITING': True,
    'ENABLE_QUERY_ANALYSIS': True,
    'ENABLE_INPUT_VALIDATION': True,
    'ENABLE_FILE_UPLOAD_SECURITY': True,
}
```

## 🛡️ Security Features

### 1. Authentication System

#### JWT Token Management
- Secure token generation with configurable expiration
- Automatic token refresh mechanism
- Secure token storage and validation
- Session-based authentication support

#### Available Authentication Mutations
```graphql
# User Registration
mutation RegisterUser {
  register(userData: {
    username: "newuser"
    email: "user@example.com"
    password: "securepassword"
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
    }
    errors
  }
}

# User Login
mutation LoginUser {
  login(username: "newuser", password: "securepassword") {
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

# Token Refresh
mutation RefreshToken {
  refreshToken(token: "your_refresh_token_here") {
    ok
    token
    refreshToken
    errors
  }
}

# User Logout
mutation LogoutUser {
  logout {
    ok
    errors
  }
}
```

#### Authentication Queries
```graphql
# Get Current User Information
query CurrentUser {
  me {
    id
    username
    email
    firstName
    lastName
    isActive
    dateJoined
  }
}
```

### 2. Permission System

#### Multi-Level Authorization
- **Field-Level Permissions**: Control access to specific GraphQL fields
- **Object-Level Permissions**: Django model-based permissions
- **Operation-Level Permissions**: CRUD operation restrictions
- **Role-Based Access Control**: User groups and custom roles

#### Permission Queries
```graphql
# Get User Permissions
query UserPermissions {
  myPermissions {
    permissions
    groups
    isSuperuser
    isStaff
  }
}
```

#### Permission Configuration
```python
# Field-level permission example
@permission_required('app.view_model')
def resolve_sensitive_field(self, info):
    return self.sensitive_data

# Object-level permission example
@object_permission_required('app.change_model')
def resolve_update_mutation(self, info, **kwargs):
    return update_object(kwargs)
```

### 3. Input Validation & Security

#### Comprehensive Input Protection
- **XSS Prevention**: HTML tag stripping and encoding
- **SQL Injection Prevention**: Parameterized queries and input sanitization
- **Input Sanitization**: Field-specific validation and cleaning
- **Custom Validators**: Extensible validation system

#### Validation Queries
```graphql
# Validate Field Input
query ValidateField {
  validateField(fieldName: "email", value: "test@example.com") {
    fieldName
    isValid
    errorMessage
    sanitizedValue
  }
}
```

#### Available Validators
- Email validation with format checking
- URL validation with protocol verification
- Password strength validation
- Phone number format validation
- Custom regex pattern validation

### 4. Rate Limiting

#### Configurable Rate Limiting
- Per-user rate limiting with JWT token identification
- Per-IP rate limiting for anonymous requests
- Configurable time windows and request limits
- Automatic cleanup of expired entries

#### Rate Limiting Configuration
```python
GRAPHQL_SECURITY = {
    'RATE_LIMITING': {
        'ENABLE': True,
        'MAX_REQUESTS': 100,        # Maximum requests per window
        'WINDOW_SECONDS': 3600,     # Time window in seconds (1 hour)
        'CACHE_PREFIX': 'graphql_rate_limit',
    }
}
```

#### Rate Limiting Behavior
- Requests are tracked per user/IP within the configured time window
- When limit is exceeded, requests return rate limit error
- Rate limit information is included in response headers
- Automatic reset when time window expires

### 5. Query Analysis

#### Query Complexity Analysis
- Assigns complexity scores to GraphQL operations
- Prevents expensive queries from overwhelming the system
- Configurable complexity limits per operation type
- Real-time complexity calculation and enforcement

#### Query Depth Analysis
- Analyzes nested query depth to prevent deeply nested attacks
- Configurable maximum depth limits
- Protection against circular reference exploitation
- Efficient depth calculation algorithm

#### Query Analysis Configuration
```python
GRAPHQL_SECURITY = {
    'QUERY_ANALYSIS': {
        'ENABLE_COMPLEXITY_ANALYSIS': True,
        'ENABLE_DEPTH_ANALYSIS': True,
        'MAX_QUERY_COMPLEXITY': 1000,
        'MAX_QUERY_DEPTH': 10,
    }
}
```

### 6. File Upload Security

#### Comprehensive File Validation
- **File Type Validation**: Whitelist-based MIME type and extension checking
- **File Size Limits**: Configurable maximum file size restrictions
- **Content Validation**: Deep file content analysis beyond extension checking
- **Malicious File Detection**: Advanced pattern matching for suspicious content

#### Virus Scanning Integration
- **ClamAV Integration**: Real-time antivirus scanning using ClamAV engine
- **Quarantine System**: Automatic isolation of infected or suspicious files
- **Scan Result Logging**: Comprehensive audit trail of all scan results
- **Configurable Scan Timeout**: Prevents hanging on large files

#### File Upload Security Configuration
```python
GRAPHQL_SECURITY = {
    'FILE_UPLOAD_SECURITY': {
        'ENABLE_VIRUS_SCANNING': True,
        'VIRUS_SCANNER_TYPE': 'clamav',  # 'clamav' or 'mock'
        'VIRUS_SCAN_TIMEOUT': 30,
        'QUARANTINE_PATH': '/var/quarantine/',
        'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
        'ALLOWED_MIME_TYPES': [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain'
        ],
        'ALLOWED_EXTENSIONS': [
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.txt'
        ],
        'ENABLE_CONTENT_VALIDATION': True,
        'SCAN_RESULT_RETENTION_DAYS': 30,
    }
}
```

#### File Upload Security Mutations
```graphql
# Secure File Upload with Validation
mutation SecureFileUpload {
  uploadFile(input: {
    file: "base64EncodedContent"
    filename: "document.pdf"
    mimeType: "application/pdf"
    validateVirus: true
    validateContent: true
  }) {
    ok
    file {
      id
      filename
      scanResult {
        status  # CLEAN, INFECTED, SUSPICIOUS, ERROR
        scanTime
        threats
      }
      quarantined
    }
    errors
  }
}

# Check File Scan Status
query FileScanStatus($fileId: ID!) {
  fileScanStatus(fileId: $fileId) {
    status
    scanResult {
      status
      threats
      scanTime
      scannerVersion
    }
    quarantined
    quarantineReason
  }
}
```

#### Security Monitoring for File Uploads
```graphql
# File Upload Security Statistics
query FileUploadSecurityStats {
  fileUploadStats {
    totalUploads
    cleanFiles
    infectedFiles
    quarantinedFiles
    scanFailures
    avgScanTime
    threatTypes {
      type
      count
    }
  }
}
```

### 7. Security Monitoring

#### Real-Time Security Information
```graphql
# Get Security Status
query SecurityInfo {
  securityInfo {
    remainingRequests
    windowResetTime
    currentComplexityLimit
    currentDepthLimit
  }
}

# Get Query Statistics
query QueryStats {
  queryStats {
    totalQueries
    avgComplexity
    avgDepth
    avgExecutionTime
    successRate
  }
}
```

## 🔧 Configuration Options

### Security Settings
```python
# django_graphql_auto/settings.py
GRAPHQL_SECURITY = {
    # Authentication Settings
    'ENABLE_AUTHENTICATION': True,
    'JWT_SECRET_KEY': 'your-secret-key',
    'JWT_EXPIRATION_DELTA': timedelta(hours=24),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
    
    # Permission Settings
    'ENABLE_PERMISSIONS': True,
    'REQUIRE_AUTHENTICATION_FOR_MUTATIONS': True,
    'REQUIRE_AUTHENTICATION_FOR_QUERIES': False,
    
    # Rate Limiting Settings
    'RATE_LIMITING': {
        'ENABLE': True,
        'MAX_REQUESTS': 100,
        'WINDOW_SECONDS': 3600,
        'CACHE_PREFIX': 'graphql_rate_limit',
    },
    
    # Query Analysis Settings
    'QUERY_ANALYSIS': {
        'ENABLE_COMPLEXITY_ANALYSIS': True,
        'ENABLE_DEPTH_ANALYSIS': True,
        'MAX_QUERY_COMPLEXITY': 1000,
        'MAX_QUERY_DEPTH': 10,
    },
    
    # Input Validation Settings
    'INPUT_VALIDATION': {
        'ENABLE_XSS_PROTECTION': True,
        'ENABLE_SQL_INJECTION_PROTECTION': True,
        'STRIP_HTML_TAGS': True,
        'CUSTOM_VALIDATORS': {},
    },
    
    # File Upload Security Settings
    'FILE_UPLOAD_SECURITY': {
        'ENABLE_VIRUS_SCANNING': True,
        'VIRUS_SCANNER_TYPE': 'clamav',
        'VIRUS_SCAN_TIMEOUT': 30,
        'QUARANTINE_PATH': '/var/quarantine/',
        'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
        'ALLOWED_MIME_TYPES': [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain'
        ],
        'ALLOWED_EXTENSIONS': [
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.txt'
        ],
        'ENABLE_CONTENT_VALIDATION': True,
        'SCAN_RESULT_RETENTION_DAYS': 30,
    }
}
```

## 🚀 Getting Started

### 1. Enable Security Features
Add security configuration to your Django settings:

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'django_graphql_auto.extensions.auth',
    'django_graphql_auto.extensions.permissions',
    'django_graphql_auto.extensions.validation',
    'django_graphql_auto.extensions.rate_limiting',
]

# Enable security middleware
GRAPHQL_MIDDLEWARE = [
    'django_graphql_auto.extensions.auth.AuthenticationMiddleware',
    'django_graphql_auto.extensions.permissions.PermissionMiddleware',
    'django_graphql_auto.extensions.rate_limiting.RateLimitingMiddleware',
    'django_graphql_auto.extensions.validation.ValidationMiddleware',
]
```

### 2. Configure Security Settings
Customize security settings based on your requirements:

```python
# Minimal security configuration
GRAPHQL_SECURITY = {
    'ENABLE_AUTHENTICATION': True,
    'ENABLE_RATE_LIMITING': True,
    'RATE_LIMITING': {
        'MAX_REQUESTS': 50,
        'WINDOW_SECONDS': 3600,
    }
}
```

### 3. Test Security Features
Use the GraphQL endpoint to test security features:

```bash
# Access GraphQL endpoint
curl -X POST http://localhost:8000/graphql/ \
  -H "Content-Type: application/json" \
  -d '{"query": "query { securityInfo { remainingRequests } }"}'
```

## 🔍 Security Best Practices

### 1. Authentication
- Use strong JWT secret keys
- Implement proper token rotation
- Set appropriate token expiration times
- Use HTTPS in production

### 2. Authorization
- Follow principle of least privilege
- Implement field-level permissions for sensitive data
- Use Django's built-in permission system
- Regular permission audits

### 3. Input Validation
- Validate all user inputs
- Use parameterized queries
- Implement custom validators for business logic
- Regular security testing

### 4. Rate Limiting
- Set appropriate rate limits based on usage patterns
- Monitor rate limit violations
- Implement different limits for different user types
- Use distributed rate limiting for scaled deployments

### 5. Query Analysis
- Set reasonable complexity and depth limits
- Monitor query patterns for anomalies
- Implement query whitelisting for critical operations
- Regular performance testing

## 📊 Security Monitoring

### Logging and Monitoring
The security system provides comprehensive logging for:
- Authentication attempts (success/failure)
- Permission violations
- Rate limit violations
- Query complexity violations
- Input validation failures

### Security Metrics
Monitor these key security metrics:
- Authentication success/failure rates
- Permission violation frequency
- Rate limit hit rates
- Query complexity trends
- Input validation failure patterns

## 🛠️ Troubleshooting

### Common Issues

#### Authentication Issues
```python
# Check JWT configuration
GRAPHQL_SECURITY = {
    'JWT_SECRET_KEY': 'ensure-this-is-set',
    'JWT_EXPIRATION_DELTA': timedelta(hours=24),
}
```

#### Permission Issues
```python
# Verify permission middleware is enabled
GRAPHQL_MIDDLEWARE = [
    'django_graphql_auto.extensions.permissions.PermissionMiddleware',
]
```

#### Rate Limiting Issues
```python
# Check cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### Debug Mode
Enable debug mode for detailed security information:

```python
GRAPHQL_SECURITY = {
    'DEBUG_MODE': True,  # Only for development
}
```

## 📚 Additional Resources

- [Authentication Examples](../examples/authentication-examples.md)
- [Permission Configuration Guide](../examples/permission-examples.md)
- [Security Testing Guide](../development/security-testing.md)
- [Performance Optimization](../development/performance.md)