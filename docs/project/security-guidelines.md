# Security Guidelines

## Django GraphQL Auto-Generation System - Security Guidelines

This document provides comprehensive security guidelines for developing, deploying, and maintaining the Django GraphQL Auto-Generation System.

## Table of Contents

- [Security Philosophy](#security-philosophy)
- [Authentication & Authorization](#authentication--authorization)
- [Input Validation & Sanitization](#input-validation--sanitization)
- [GraphQL Security](#graphql-security)
- [Data Protection](#data-protection)
- [Infrastructure Security](#infrastructure-security)
- [Monitoring & Logging](#monitoring--logging)
- [Incident Response](#incident-response)
- [Security Testing](#security-testing)
- [Compliance & Standards](#compliance--standards)

## Security Philosophy

### Security by Design
- **Defense in Depth**: Multiple layers of security controls
- **Principle of Least Privilege**: Minimal necessary access rights
- **Fail Secure**: System fails to a secure state
- **Zero Trust**: Never trust, always verify

### Security Priorities
1. **Data Protection**: Protect sensitive user and business data
2. **Access Control**: Ensure proper authentication and authorization
3. **Input Validation**: Prevent injection attacks
4. **Monitoring**: Detect and respond to security incidents
5. **Compliance**: Meet regulatory and industry standards

## Authentication & Authorization

### JWT Authentication Implementation

```python
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class JWTAuthentication:
    """Secure JWT authentication implementation."""
    
    @staticmethod
    def generate_token(user: User) -> dict:
        """
        Generate JWT token for authenticated user.
        
        Args:
            user: Authenticated user instance
            
        Returns:
            Dictionary containing access and refresh tokens
        """
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'iat': now,
            'exp': now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_LIFETIME),
            'type': 'access'
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': user.id,
            'iat': now,
            'exp': now + timedelta(days=settings.JWT_REFRESH_TOKEN_LIFETIME),
            'type': 'refresh'
        }
        
        return {
            'access_token': jwt.encode(
                access_payload,
                settings.JWT_SECRET_KEY,
                algorithm='HS256'
            ),
            'refresh_token': jwt.encode(
                refresh_payload,
                settings.JWT_SECRET_KEY,
                algorithm='HS256'
            ),
            'expires_in': settings.JWT_ACCESS_TOKEN_LIFETIME * 60
        }
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            ValidationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=['HS256']
            )
            
            # Verify token type
            if payload.get('type') != 'access':
                raise ValidationError("Invalid token type")
            
            # Verify user exists
            try:
                user = User.objects.get(id=payload['user_id'])
                if not user.is_active:
                    raise ValidationError("User account is disabled")
            except User.DoesNotExist:
                raise ValidationError("User not found")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise ValidationError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValidationError("Invalid token")
```

### Permission System

```python
from enum import Enum
from typing import List, Set
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

class PermissionLevel(Enum):
    """Permission levels for resource access."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

class SecurityPermissionChecker:
    """Advanced permission checking system."""
    
    def __init__(self, user):
        self.user = user
        self._user_permissions = None
    
    @property
    def user_permissions(self) -> Set[str]:
        """Get cached user permissions."""
        if self._user_permissions is None:
            self._user_permissions = set(
                self.user.get_all_permissions()
            )
        return self._user_permissions
    
    def has_model_permission(
        self,
        model_class,
        permission_level: PermissionLevel
    ) -> bool:
        """
        Check if user has permission for model operations.
        
        Args:
            model_class: Django model class
            permission_level: Required permission level
            
        Returns:
            True if user has permission, False otherwise
        """
        if not self.user.is_authenticated:
            return False
        
        # Superuser has all permissions
        if self.user.is_superuser:
            return True
        
        # Check specific model permissions
        app_label = model_class._meta.app_label
        model_name = model_class._meta.model_name
        
        permission_map = {
            PermissionLevel.READ: f"{app_label}.view_{model_name}",
            PermissionLevel.WRITE: f"{app_label}.change_{model_name}",
            PermissionLevel.DELETE: f"{app_label}.delete_{model_name}",
            PermissionLevel.ADMIN: f"{app_label}.admin_{model_name}",
        }
        
        required_permission = permission_map.get(permission_level)
        return required_permission in self.user_permissions
    
    def has_field_permission(
        self,
        model_class,
        field_name: str,
        permission_level: PermissionLevel
    ) -> bool:
        """
        Check if user has permission for specific field operations.
        
        Args:
            model_class: Django model class
            field_name: Field name
            permission_level: Required permission level
            
        Returns:
            True if user has permission, False otherwise
        """
        # Check model-level permission first
        if not self.has_model_permission(model_class, permission_level):
            return False
        
        # Check field-level restrictions
        sensitive_fields = getattr(model_class._meta, 'sensitive_fields', [])
        if field_name in sensitive_fields:
            # Require admin permission for sensitive fields
            return self.has_model_permission(model_class, PermissionLevel.ADMIN)
        
        return True
```

## Input Validation & Sanitization

### GraphQL Input Validation

```python
import re
from typing import Any, Dict, List
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from graphene import InputObjectType, String, Int, Boolean

class SecureInputValidator:
    """Comprehensive input validation for GraphQL."""
    
    # Regex patterns for validation
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,30}$')
    PHONE_PATTERN = re.compile(r'^\+?1?\d{9,15}$')
    
    # Dangerous patterns to block
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)",
        r"(\b(UNION|OR|AND)\b.*\b(SELECT|INSERT|UPDATE|DELETE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(EXEC|EXECUTE|SP_|XP_)\b)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
    ]
    
    @classmethod
    def validate_string_input(
        cls,
        value: str,
        field_name: str,
        max_length: int = 255,
        allow_html: bool = False
    ) -> str:
        """
        Validate and sanitize string input.
        
        Args:
            value: Input string value
            field_name: Name of the field being validated
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML content
            
        Returns:
            Validated and sanitized string
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")
        
        # Check length
        if len(value) > max_length:
            raise ValidationError(
                f"{field_name} must be {max_length} characters or less"
            )
        
        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(f"Invalid characters in {field_name}")
        
        # Check for XSS patterns if HTML is not allowed
        if not allow_html:
            for pattern in cls.XSS_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    raise ValidationError(f"Invalid content in {field_name}")
        
        # Sanitize the string
        sanitized_value = value.strip()
        
        # Remove null bytes
        sanitized_value = sanitized_value.replace('\x00', '')
        
        return sanitized_value
    
    @classmethod
    def validate_email_input(cls, email: str) -> str:
        """
        Validate email input.
        
        Args:
            email: Email address string
            
        Returns:
            Validated email address
            
        Raises:
            ValidationError: If email is invalid
        """
        if not email:
            raise ValidationError("Email is required")
        
        # Basic string validation
        email = cls.validate_string_input(email, "email", max_length=254)
        
        # Django email validation
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError("Invalid email format")
        
        return email.lower()
    
    @classmethod
    def validate_username_input(cls, username: str) -> str:
        """
        Validate username input.
        
        Args:
            username: Username string
            
        Returns:
            Validated username
            
        Raises:
            ValidationError: If username is invalid
        """
        username = cls.validate_string_input(username, "username", max_length=30)
        
        if not cls.USERNAME_PATTERN.match(username):
            raise ValidationError(
                "Username must be 3-30 characters long and contain only "
                "letters, numbers, and underscores"
            )
        
        return username

class UserCreateInput(InputObjectType):
    """Secure user creation input type."""
    
    username = String(required=True)
    email = String(required=True)
    password = String(required=True)
    first_name = String()
    last_name = String()
    
    def clean(self) -> Dict[str, Any]:
        """
        Validate and clean input data.
        
        Returns:
            Cleaned input data
            
        Raises:
            ValidationError: If validation fails
        """
        validator = SecureInputValidator()
        
        cleaned_data = {}
        
        # Validate username
        cleaned_data['username'] = validator.validate_username_input(
            self.username
        )
        
        # Validate email
        cleaned_data['email'] = validator.validate_email_input(self.email)
        
        # Validate password
        if len(self.password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        
        cleaned_data['password'] = self.password
        
        # Validate optional fields
        if self.first_name:
            cleaned_data['first_name'] = validator.validate_string_input(
                self.first_name, "first_name", max_length=30
            )
        
        if self.last_name:
            cleaned_data['last_name'] = validator.validate_string_input(
                self.last_name, "last_name", max_length=30
            )
        
        return cleaned_data
```

## GraphQL Security

### Query Complexity Analysis

```python
from typing import Dict, Any
from graphene import Schema
from graphql import GraphQLError

class QueryComplexityAnalyzer:
    """Analyze and limit GraphQL query complexity."""
    
    def __init__(self, max_complexity: int = 1000, max_depth: int = 10):
        self.max_complexity = max_complexity
        self.max_depth = max_depth
    
    def analyze_query(self, query_ast) -> Dict[str, int]:
        """
        Analyze query complexity and depth.
        
        Args:
            query_ast: GraphQL query AST
            
        Returns:
            Dictionary with complexity and depth metrics
            
        Raises:
            GraphQLError: If query exceeds limits
        """
        complexity = self._calculate_complexity(query_ast)
        depth = self._calculate_depth(query_ast)
        
        if complexity > self.max_complexity:
            raise GraphQLError(
                f"Query complexity {complexity} exceeds maximum {self.max_complexity}"
            )
        
        if depth > self.max_depth:
            raise GraphQLError(
                f"Query depth {depth} exceeds maximum {self.max_depth}"
            )
        
        return {
            'complexity': complexity,
            'depth': depth,
            'max_complexity': self.max_complexity,
            'max_depth': self.max_depth
        }
    
    def _calculate_complexity(self, node, complexity: int = 0) -> int:
        """Calculate query complexity score."""
        # Implementation details for complexity calculation
        # This is a simplified version
        if hasattr(node, 'selection_set') and node.selection_set:
            for selection in node.selection_set.selections:
                complexity += 1
                if hasattr(selection, 'selection_set'):
                    complexity += self._calculate_complexity(selection, 0)
        return complexity
    
    def _calculate_depth(self, node, depth: int = 0) -> int:
        """Calculate query depth."""
        max_depth = depth
        if hasattr(node, 'selection_set') and node.selection_set:
            for selection in node.selection_set.selections:
                if hasattr(selection, 'selection_set'):
                    child_depth = self._calculate_depth(selection, depth + 1)
                    max_depth = max(max_depth, child_depth)
        return max_depth
```

### Rate Limiting

```python
import time
from typing import Dict, Optional
from django.core.cache import cache
from django.http import HttpRequest
from graphql import GraphQLError

class RateLimiter:
    """Rate limiting for GraphQL endpoints."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit
    
    def check_rate_limit(self, request: HttpRequest, user_id: Optional[int] = None) -> bool:
        """
        Check if request is within rate limits.
        
        Args:
            request: HTTP request object
            user_id: Optional user ID for authenticated requests
            
        Returns:
            True if request is allowed, False otherwise
            
        Raises:
            GraphQLError: If rate limit is exceeded
        """
        # Determine identifier for rate limiting
        if user_id:
            identifier = f"user:{user_id}"
        else:
            identifier = f"ip:{self._get_client_ip(request)}"
        
        current_time = int(time.time())
        
        # Check minute-based rate limit
        minute_key = f"rate_limit:minute:{identifier}:{current_time // 60}"
        minute_count = cache.get(minute_key, 0)
        
        if minute_count >= self.requests_per_minute:
            raise GraphQLError("Rate limit exceeded: too many requests per minute")
        
        # Check hour-based rate limit
        hour_key = f"rate_limit:hour:{identifier}:{current_time // 3600}"
        hour_count = cache.get(hour_key, 0)
        
        if hour_count >= self.requests_per_hour:
            raise GraphQLError("Rate limit exceeded: too many requests per hour")
        
        # Check burst limit
        burst_key = f"rate_limit:burst:{identifier}"
        burst_timestamps = cache.get(burst_key, [])
        
        # Remove timestamps older than 10 seconds
        current_burst = [
            ts for ts in burst_timestamps
            if current_time - ts < 10
        ]
        
        if len(current_burst) >= self.burst_limit:
            raise GraphQLError("Rate limit exceeded: too many requests in burst")
        
        # Update counters
        cache.set(minute_key, minute_count + 1, 60)
        cache.set(hour_key, hour_count + 1, 3600)
        
        current_burst.append(current_time)
        cache.set(burst_key, current_burst, 60)
        
        return True
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

## Data Protection

### Encryption and Hashing

```python
import hashlib
import secrets
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password

class DataProtection:
    """Data encryption and protection utilities."""
    
    def __init__(self):
        self.cipher_suite = Fernet(settings.ENCRYPTION_KEY.encode())
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive data for storage.
        
        Args:
            data: Plain text data to encrypt
            
        Returns:
            Encrypted data as base64 string
        """
        encrypted_data = self.cipher_suite.encrypt(data.encode())
        return encrypted_data.decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data as base64 string
            
        Returns:
            Decrypted plain text data
        """
        decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using Django's secure hasher.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return make_password(password)
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return check_password(password, hashed_password)
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Generate cryptographically secure random token.
        
        Args:
            length: Token length in bytes
            
        Returns:
            Secure random token as hex string
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def hash_data(data: str, salt: str = None) -> str:
        """
        Hash data with optional salt.
        
        Args:
            data: Data to hash
            salt: Optional salt value
            
        Returns:
            SHA-256 hash as hex string
        """
        if salt:
            data = f"{data}{salt}"
        
        return hashlib.sha256(data.encode()).hexdigest()
```

### Personal Data Handling

```python
from typing import List, Dict, Any
from django.db import models
from django.core.exceptions import ValidationError

class PersonalDataMixin:
    """Mixin for models containing personal data."""
    
    # Fields containing personal data
    PERSONAL_DATA_FIELDS = []
    
    # Fields containing sensitive data
    SENSITIVE_DATA_FIELDS = []
    
    def anonymize_personal_data(self) -> None:
        """Anonymize personal data for GDPR compliance."""
        for field_name in self.PERSONAL_DATA_FIELDS:
            if hasattr(self, field_name):
                setattr(self, field_name, f"anonymized_{self.pk}")
        
        self.save()
    
    def export_personal_data(self) -> Dict[str, Any]:
        """Export personal data for GDPR data portability."""
        data = {}
        
        for field_name in self.PERSONAL_DATA_FIELDS:
            if hasattr(self, field_name):
                data[field_name] = getattr(self, field_name)
        
        return data
    
    def delete_personal_data(self) -> None:
        """Delete personal data (right to be forgotten)."""
        for field_name in self.PERSONAL_DATA_FIELDS:
            if hasattr(self, field_name):
                field = self._meta.get_field(field_name)
                if field.null:
                    setattr(self, field_name, None)
                else:
                    setattr(self, field_name, "")
        
        self.save()

class SecureUserModel(models.Model, PersonalDataMixin):
    """Example secure user model with personal data handling."""
    
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField()
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Personal data fields for GDPR compliance
    PERSONAL_DATA_FIELDS = [
        'email', 'first_name', 'last_name', 'phone_number'
    ]
    
    SENSITIVE_DATA_FIELDS = ['email', 'phone_number']
    
    class Meta:
        db_table = 'secure_user'
```

## Infrastructure Security

### Security Headers

```python
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to all responses."""
    
    def process_response(self, request, response: HttpResponse) -> HttpResponse:
        """Add security headers to response."""
        
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Enable XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Enforce HTTPS
        response['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains; preload'
        )
        
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy
        response['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=()'
        )
        
        return response
```

### Environment Configuration

```python
# settings/security.py
import os
from pathlib import Path

# Security settings
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Secret key management
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable is required")

# Database security
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# HTTPS settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Content security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# JWT settings
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_ACCESS_TOKEN_LIFETIME = 15  # minutes
JWT_REFRESH_TOKEN_LIFETIME = 7  # days

# Rate limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '[{asctime}] {levelname} SECURITY {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/security.log',
            'formatter': 'security',
        },
    },
    'loggers': {
        'security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

## Monitoring & Logging

### Security Event Logging

```python
import logging
from typing import Dict, Any, Optional
from django.contrib.auth import get_user_model
from django.http import HttpRequest

User = get_user_model()

class SecurityLogger:
    """Centralized security event logging."""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
    
    def log_authentication_attempt(
        self,
        request: HttpRequest,
        username: str,
        success: bool,
        failure_reason: Optional[str] = None
    ) -> None:
        """Log authentication attempt."""
        event_data = {
            'event_type': 'authentication_attempt',
            'username': username,
            'success': success,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'timestamp': self._get_timestamp(),
        }
        
        if not success and failure_reason:
            event_data['failure_reason'] = failure_reason
        
        if success:
            self.logger.info(f"Successful login: {username}", extra=event_data)
        else:
            self.logger.warning(f"Failed login: {username}", extra=event_data)
    
    def log_permission_denied(
        self,
        request: HttpRequest,
        user: User,
        resource: str,
        action: str
    ) -> None:
        """Log permission denied events."""
        event_data = {
            'event_type': 'permission_denied',
            'user_id': user.id if user.is_authenticated else None,
            'username': user.username if user.is_authenticated else 'anonymous',
            'resource': resource,
            'action': action,
            'ip_address': self._get_client_ip(request),
            'timestamp': self._get_timestamp(),
        }
        
        self.logger.warning(
            f"Permission denied: {user.username} -> {action} on {resource}",
            extra=event_data
        )
    
    def log_suspicious_activity(
        self,
        request: HttpRequest,
        activity_type: str,
        details: Dict[str, Any]
    ) -> None:
        """Log suspicious activity."""
        event_data = {
            'event_type': 'suspicious_activity',
            'activity_type': activity_type,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'timestamp': self._get_timestamp(),
            **details
        }
        
        self.logger.error(
            f"Suspicious activity detected: {activity_type}",
            extra=event_data
        )
    
    def log_data_access(
        self,
        user: User,
        model_name: str,
        object_id: str,
        action: str
    ) -> None:
        """Log data access for audit trail."""
        event_data = {
            'event_type': 'data_access',
            'user_id': user.id,
            'username': user.username,
            'model_name': model_name,
            'object_id': object_id,
            'action': action,
            'timestamp': self._get_timestamp(),
        }
        
        self.logger.info(
            f"Data access: {user.username} {action} {model_name}:{object_id}",
            extra=event_data
        )
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
```

## Incident Response

### Security Incident Response Plan

```python
from enum import Enum
from typing import List, Dict, Any
from django.core.mail import send_mail
from django.conf import settings

class IncidentSeverity(Enum):
    """Security incident severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityIncidentResponse:
    """Security incident response system."""
    
    def __init__(self):
        self.security_team_emails = settings.SECURITY_TEAM_EMAILS
        self.logger = logging.getLogger('security.incidents')
    
    def report_incident(
        self,
        incident_type: str,
        severity: IncidentSeverity,
        description: str,
        affected_systems: List[str],
        evidence: Dict[str, Any]
    ) -> str:
        """
        Report security incident.
        
        Args:
            incident_type: Type of security incident
            severity: Incident severity level
            description: Detailed description
            affected_systems: List of affected systems
            evidence: Evidence and supporting data
            
        Returns:
            Incident ID for tracking
        """
        incident_id = self._generate_incident_id()
        
        incident_data = {
            'incident_id': incident_id,
            'incident_type': incident_type,
            'severity': severity.value,
            'description': description,
            'affected_systems': affected_systems,
            'evidence': evidence,
            'timestamp': self._get_timestamp(),
            'status': 'open'
        }
        
        # Log incident
        self.logger.critical(
            f"Security incident reported: {incident_id}",
            extra=incident_data
        )
        
        # Notify security team
        self._notify_security_team(incident_data)
        
        # Take immediate action based on severity
        if severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]:
            self._take_immediate_action(incident_data)
        
        return incident_id
    
    def _notify_security_team(self, incident_data: Dict[str, Any]) -> None:
        """Notify security team of incident."""
        subject = f"Security Incident: {incident_data['incident_id']}"
        message = f"""
        Security Incident Report
        
        Incident ID: {incident_data['incident_id']}
        Type: {incident_data['incident_type']}
        Severity: {incident_data['severity']}
        Timestamp: {incident_data['timestamp']}
        
        Description:
        {incident_data['description']}
        
        Affected Systems:
        {', '.join(incident_data['affected_systems'])}
        
        Evidence:
        {incident_data['evidence']}
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            self.security_team_emails,
            fail_silently=False
        )
    
    def _take_immediate_action(self, incident_data: Dict[str, Any]) -> None:
        """Take immediate action for high/critical incidents."""
        # Implementation depends on specific incident type
        # Examples: disable user accounts, block IP addresses, etc.
        pass
    
    def _generate_incident_id(self) -> str:
        """Generate unique incident ID."""
        import uuid
        return f"SEC-{uuid.uuid4().hex[:8].upper()}"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
```

## Security Testing

### Automated Security Tests

```python
import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class SecurityTestCase(TestCase):
    """Base class for security tests."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'/*",
            "1; DELETE FROM users WHERE 1=1; --"
        ]
        
        for malicious_input in malicious_inputs:
            response = self.client.post('/graphql/', {
                'query': f'''
                    query {{
                        user(username: "{malicious_input}") {{
                            id
                            username
                        }}
                    }}
                '''
            })
            
            # Should not return sensitive data or cause errors
            self.assertNotIn('error', response.json().get('data', {}))
    
    def test_xss_protection(self):
        """Test protection against XSS attacks."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<iframe src='javascript:alert(\"xss\")'></iframe>"
        ]
        
        for payload in xss_payloads:
            response = self.client.post('/graphql/', {
                'query': f'''
                    mutation {{
                        createUser(input: {{
                            username: "test",
                            email: "test@example.com",
                            firstName: "{payload}"
                        }}) {{
                            user {{
                                firstName
                            }}
                        }}
                    }}
                '''
            })
            
            # XSS payload should be sanitized
            if 'data' in response.json():
                user_data = response.json()['data']['createUser']['user']
                self.assertNotIn('<script>', user_data.get('firstName', ''))
    
    def test_authentication_required(self):
        """Test that protected endpoints require authentication."""
        protected_queries = [
            'query { users { id username } }',
            'mutation { deleteUser(id: "1") { success } }'
        ]
        
        for query in protected_queries:
            response = self.client.post('/graphql/', {'query': query})
            
            # Should return authentication error
            self.assertIn('errors', response.json())
            error_message = response.json()['errors'][0]['message']
            self.assertIn('authentication', error_message.lower())
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Make multiple rapid requests
        for i in range(100):
            response = self.client.post('/graphql/', {
                'query': 'query { __schema { types { name } } }'
            })
            
            if i > 60:  # Assuming 60 requests per minute limit
                self.assertEqual(response.status_code, 429)
                break
    
    def test_query_depth_limiting(self):
        """Test query depth limiting."""
        # Create deeply nested query
        deep_query = "query { "
        for i in range(20):  # Assuming max depth of 10
            deep_query += "users { "
        
        deep_query += "id"
        
        for i in range(20):
            deep_query += " }"
        
        deep_query += " }"
        
        response = self.client.post('/graphql/', {'query': deep_query})
        
        # Should return depth limit error
        self.assertIn('errors', response.json())
        error_message = response.json()['errors'][0]['message']
        self.assertIn('depth', error_message.lower())
```

## Compliance & Standards

### GDPR Compliance

```python
from typing import List, Dict, Any
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class GDPRComplianceManager:
    """GDPR compliance management."""
    
    def __init__(self):
        self.personal_data_models = [
            # List of models containing personal data
        ]
    
    def export_user_data(self, user: User) -> Dict[str, Any]:
        """
        Export all user data for GDPR data portability.
        
        Args:
            user: User instance
            
        Returns:
            Complete user data export
        """
        export_data = {
            'user_profile': {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
            },
            'related_data': {}
        }
        
        # Export related data from other models
        for model_class in self.personal_data_models:
            if hasattr(model_class, 'export_user_data'):
                model_name = model_class._meta.model_name
                export_data['related_data'][model_name] = (
                    model_class.export_user_data(user)
                )
        
        return export_data
    
    def anonymize_user_data(self, user: User) -> None:
        """
        Anonymize user data for GDPR right to be forgotten.
        
        Args:
            user: User instance to anonymize
        """
        # Anonymize user profile
        user.email = f"anonymized_{user.id}@example.com"
        user.first_name = "Anonymized"
        user.last_name = "User"
        user.is_active = False
        user.save()
        
        # Anonymize related data
        for model_class in self.personal_data_models:
            if hasattr(model_class, 'anonymize_user_data'):
                model_class.anonymize_user_data(user)
    
    def generate_privacy_report(self) -> Dict[str, Any]:
        """Generate privacy compliance report."""
        return {
            'data_processing_activities': self._get_data_processing_activities(),
            'data_retention_policies': self._get_data_retention_policies(),
            'security_measures': self._get_security_measures(),
            'user_rights_procedures': self._get_user_rights_procedures(),
        }
    
    def _get_data_processing_activities(self) -> List[Dict[str, Any]]:
        """Get list of data processing activities."""
        return [
            {
                'purpose': 'User authentication and authorization',
                'legal_basis': 'Legitimate interest',
                'data_categories': ['Identity data', 'Contact data'],
                'retention_period': '2 years after account deletion'
            },
            # Add more activities as needed
        ]
    
    def _get_data_retention_policies(self) -> Dict[str, str]:
        """Get data retention policies."""
        return {
            'user_accounts': '2 years after last login',
            'audit_logs': '7 years',
            'security_logs': '1 year',
            'backup_data': '30 days'
        }
    
    def _get_security_measures(self) -> List[str]:
        """Get implemented security measures."""
        return [
            'Data encryption at rest and in transit',
            'Access controls and authentication',
            'Regular security audits',
            'Incident response procedures',
            'Staff training on data protection'
        ]
    
    def _get_user_rights_procedures(self) -> Dict[str, str]:
        """Get procedures for user rights."""
        return {
            'data_access': 'Users can request data export through account settings',
            'data_rectification': 'Users can update their data through account settings',
            'data_erasure': 'Users can request account deletion through support',
            'data_portability': 'Data export available in JSON format',
            'objection': 'Users can opt-out of non-essential processing'
        }
```

## Conclusion

This security guidelines document provides comprehensive security measures for the Django GraphQL Auto-Generation System. All team members must follow these guidelines to ensure the security and integrity of the system and user data.

Regular security reviews and updates to these guidelines are essential to address emerging threats and maintain compliance with security standards and regulations.

For security-related questions or to report security vulnerabilities, please contact the security team at security@example.com.