# Security Configuration Guide

## Overview

This guide provides comprehensive configuration options for the Django GraphQL Auto-Generation System's security features. Learn how to customize authentication, permissions, input validation, rate limiting, and query analysis to meet your specific security requirements.

## 🔧 Configuration Structure

### Main Configuration File

```python
# settings.py
GRAPHQL_AUTO_SETTINGS = {
    'SECURITY': {
        # Authentication Configuration
        'AUTHENTICATION': {
            # JWT Settings
            'JWT': {
                'ENABLE': True,
                'SECRET_KEY': 'your-jwt-secret-key',  # Use environment variable
                'ALGORITHM': 'HS256',
                'ACCESS_TOKEN_LIFETIME': 3600,  # 1 hour in seconds
                'REFRESH_TOKEN_LIFETIME': 604800,  # 7 days in seconds
                'SLIDING_TOKEN_REFRESH_LIFETIME': 86400,  # 1 day in seconds
                'ROTATE_REFRESH_TOKENS': True,
                'BLACKLIST_AFTER_ROTATION': True,
                'UPDATE_LAST_LOGIN': True,
                'ISSUER': 'django-graphql-auto',
                'AUDIENCE': None,
                'LEEWAY': 0,
                'AUTH_HEADER_TYPES': ('Bearer',),
                'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
                'USER_ID_FIELD': 'id',
                'USER_ID_CLAIM': 'user_id',
                'USER_AUTHENTICATION_RULE': 'django_graphql_auto.authentication.default_user_authentication_rule',
                'AUTH_TOKEN_CLASSES': ('django_graphql_auto.tokens.AccessToken',),
                'TOKEN_TYPE_CLAIM': 'token_type',
                'JTI_CLAIM': 'jti',
                'SLIDING_TOKEN_LIFETIME': 300,  # 5 minutes
                'SLIDING_TOKEN_REFRESH_LIFETIME': 86400,  # 1 day
            },
            
            # Session Settings
            'SESSION': {
                'ENABLE': True,
                'SESSION_COOKIE_AGE': 7200,  # 2 hours
                'SESSION_COOKIE_SECURE': True,  # HTTPS only
                'SESSION_COOKIE_HTTPONLY': True,
                'SESSION_COOKIE_SAMESITE': 'Strict',
                'SESSION_SAVE_EVERY_REQUEST': True,
                'SESSION_EXPIRE_AT_BROWSER_CLOSE': False,
            },
            
            # Multi-Factor Authentication
            'MFA': {
                'ENABLE': False,
                'REQUIRED_FOR_STAFF': True,
                'REQUIRED_FOR_SUPERUSER': True,
                'BACKUP_CODES_COUNT': 10,
                'TOTP_ISSUER': 'Django GraphQL Auto',
                'SMS_PROVIDER': None,  # 'twilio', 'aws_sns', etc.
            },
        },
        
        # Permission Configuration
        'PERMISSIONS': {
            'ENABLE': True,
            'DEFAULT_PERMISSION_CLASSES': [
                'django_graphql_auto.permissions.IsAuthenticated',
            ],
            'OPERATION_PERMISSIONS': {
                'CREATE': ['django_graphql_auto.permissions.IsAuthenticated'],
                'READ': ['django_graphql_auto.permissions.AllowAny'],
                'UPDATE': ['django_graphql_auto.permissions.IsOwnerOrStaff'],
                'DELETE': ['django_graphql_auto.permissions.IsOwnerOrStaff'],
            },
            'FIELD_PERMISSIONS': {
                'SENSITIVE_FIELDS': ['password', 'ssn', 'credit_card'],
                'STAFF_ONLY_FIELDS': ['is_staff', 'is_superuser', 'user_permissions'],
                'OWNER_ONLY_FIELDS': ['email', 'phone_number', 'address'],
            },
            'ROLE_BASED_ACCESS': {
                'ENABLE': True,
                'ROLES': {
                    'admin': ['*'],  # All permissions
                    'editor': ['create_post', 'update_post', 'delete_own_post'],
                    'viewer': ['read_post', 'read_comment'],
                    'user': ['create_comment', 'update_own_comment', 'delete_own_comment'],
                },
            },
        },
        
        # Input Validation Configuration
        'INPUT_VALIDATION': {
            'ENABLE': True,
            'XSS_PROTECTION': {
                'ENABLE': True,
                'ALLOWED_TAGS': [
                    'b', 'i', 'u', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li',
                    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre'
                ],
                'ALLOWED_ATTRIBUTES': {
                    'a': ['href', 'title'],
                    'img': ['src', 'alt', 'width', 'height'],
                    'code': ['class'],
                },
                'ALLOWED_PROTOCOLS': ['http', 'https', 'mailto'],
                'STRIP_COMMENTS': True,
                'STRIP_WHITESPACE': True,
            },
            'SQL_INJECTION_PROTECTION': {
                'ENABLE': True,
                'BLOCKED_PATTERNS': [
                    r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
                    r'(--|#|/\*|\*/)',
                    r'(\bOR\b.*=.*\bOR\b)',
                    r'(\bAND\b.*=.*\bAND\b)',
                    r'(\'.*\'.*=.*\'.*\')',
                ],
                'CASE_SENSITIVE': False,
            },
            'FIELD_VALIDATORS': {
                'EMAIL': {
                    'ENABLE': True,
                    'REGEX': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                    'MAX_LENGTH': 254,
                    'NORMALIZE': True,
                },
                'URL': {
                    'ENABLE': True,
                    'ALLOWED_SCHEMES': ['http', 'https'],
                    'MAX_LENGTH': 2048,
                    'REQUIRE_TLD': True,
                },
                'PHONE': {
                    'ENABLE': True,
                    'REGEX': r'^\+?1?-?\.?\s?\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})$',
                    'NORMALIZE': True,
                    'INTERNATIONAL_FORMAT': True,
                },
                'PASSWORD': {
                    'MIN_LENGTH': 8,
                    'MAX_LENGTH': 128,
                    'REQUIRE_UPPERCASE': True,
                    'REQUIRE_LOWERCASE': True,
                    'REQUIRE_DIGITS': True,
                    'REQUIRE_SPECIAL_CHARS': True,
                    'SPECIAL_CHARS': '!@#$%^&*()_+-=[]{}|;:,.<>?',
                    'COMMON_PASSWORDS_CHECK': True,
                    'USER_ATTRIBUTE_SIMILARITY_CHECK': True,
                },
            },
            'CUSTOM_VALIDATORS': [
                'your_app.validators.BusinessLogicValidator',
                'your_app.validators.DateRangeValidator',
                'your_app.validators.FileUploadValidator',
            ],
        },
        
        # Rate Limiting Configuration
        'RATE_LIMITING': {
            'ENABLE': True,
            'STORAGE_BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'KEY_PREFIX': 'graphql_rate_limit',
            'DEFAULT_LIMITS': {
                'ANONYMOUS': {
                    'REQUESTS_PER_MINUTE': 10,
                    'REQUESTS_PER_HOUR': 100,
                    'REQUESTS_PER_DAY': 1000,
                },
                'AUTHENTICATED': {
                    'REQUESTS_PER_MINUTE': 60,
                    'REQUESTS_PER_HOUR': 1000,
                    'REQUESTS_PER_DAY': 10000,
                },
                'STAFF': {
                    'REQUESTS_PER_MINUTE': 120,
                    'REQUESTS_PER_HOUR': 5000,
                    'REQUESTS_PER_DAY': 50000,
                },
                'SUPERUSER': {
                    'REQUESTS_PER_MINUTE': 0,  # Unlimited
                    'REQUESTS_PER_HOUR': 0,
                    'REQUESTS_PER_DAY': 0,
                },
            },
            'OPERATION_SPECIFIC_LIMITS': {
                'CREATE_USER': {
                    'REQUESTS_PER_MINUTE': 5,
                    'REQUESTS_PER_HOUR': 20,
                },
                'LOGIN': {
                    'REQUESTS_PER_MINUTE': 10,
                    'REQUESTS_PER_HOUR': 50,
                },
                'PASSWORD_RESET': {
                    'REQUESTS_PER_MINUTE': 2,
                    'REQUESTS_PER_HOUR': 10,
                },
            },
            'IP_WHITELIST': [
                '127.0.0.1',
                '::1',
                # Add your trusted IPs
            ],
            'HEADERS': {
                'LIMIT_HEADER': 'X-RateLimit-Limit',
                'REMAINING_HEADER': 'X-RateLimit-Remaining',
                'RESET_HEADER': 'X-RateLimit-Reset',
                'RETRY_AFTER_HEADER': 'Retry-After',
            },
        },
        
        # Query Analysis Configuration
        'QUERY_ANALYSIS': {
            'COMPLEXITY_ANALYSIS': {
                'ENABLE': True,
                'MAX_COMPLEXITY': 100,
                'COMPLEXITY_WEIGHTS': {
                    'SCALAR_FIELD': 1,
                    'OBJECT_FIELD': 2,
                    'LIST_FIELD': 5,
                    'CONNECTION_FIELD': 10,
                    'MUTATION_FIELD': 15,
                },
                'USER_SPECIFIC_LIMITS': {
                    'ANONYMOUS': 50,
                    'AUTHENTICATED': 100,
                    'STAFF': 500,
                    'SUPERUSER': 0,  # Unlimited
                },
                'OPERATION_SPECIFIC_LIMITS': {
                    'INTROSPECTION': 1000,  # Higher limit for introspection
                    'ANALYTICS': 200,
                    'REPORTING': 300,
                },
            },
            'DEPTH_ANALYSIS': {
                'ENABLE': True,
                'MAX_DEPTH': 6,
                'USER_SPECIFIC_LIMITS': {
                    'ANONYMOUS': 4,
                    'AUTHENTICATED': 6,
                    'STAFF': 10,
                    'SUPERUSER': 0,  # Unlimited
                },
                'INTROSPECTION_DEPTH_LIMIT': 15,
            },
            'TIMEOUT_ANALYSIS': {
                'ENABLE': True,
                'DEFAULT_TIMEOUT': 30,  # seconds
                'OPERATION_TIMEOUTS': {
                    'SIMPLE_QUERY': 5,
                    'COMPLEX_QUERY': 30,
                    'MUTATION': 60,
                    'SUBSCRIPTION': 300,
                },
            },
        },
        
        # Security Headers Configuration
        'SECURITY_HEADERS': {
            'ENABLE': True,
            'HEADERS': {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Referrer-Policy': 'strict-origin-when-cross-origin',
                'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            },
        },
        
        # Logging and Monitoring Configuration
        'LOGGING': {
            'ENABLE': True,
            'LOG_LEVEL': 'INFO',
            'LOG_AUTHENTICATION': True,
            'LOG_PERMISSIONS': True,
            'LOG_RATE_LIMITING': True,
            'LOG_QUERY_ANALYSIS': True,
            'LOG_VALIDATION_ERRORS': True,
            'LOG_SECURITY_EVENTS': True,
            'SENSITIVE_FIELDS': ['password', 'token', 'secret'],
            'LOG_FORMAT': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
            'LOG_FILE': 'logs/security.log',
            'MAX_LOG_SIZE': '10MB',
            'BACKUP_COUNT': 5,
        },
        
        # Development and Debug Configuration
        'DEBUG': {
            'ENABLE_IN_DEBUG': True,
            'SHOW_QUERY_ANALYSIS': True,
            'SHOW_PERMISSION_CHECKS': True,
            'SHOW_VALIDATION_DETAILS': True,
            'DISABLE_RATE_LIMITING': False,  # Keep rate limiting even in debug
            'ALLOW_INTROSPECTION': True,
            'GRAPHIQL_ENABLED': True,
        },
    }
}
```

## 🔐 Environment Variables

### Security-Related Environment Variables

```bash
# .env file
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=604800

# Database Security
DATABASE_SSL_REQUIRE=True
DATABASE_SSL_CA=/path/to/ca-cert.pem

# Redis Security (for rate limiting)
REDIS_URL=redis://username:password@localhost:6379/0
REDIS_SSL=True

# Security Headers
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# CORS Configuration
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
CORS_ALLOW_CREDENTIALS=True

# Rate Limiting
RATE_LIMIT_REDIS_URL=redis://localhost:6379/1
RATE_LIMIT_ENABLE=True

# Logging
LOG_LEVEL=INFO
SECURITY_LOG_FILE=/var/log/django-graphql-security.log

# Development Settings
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Loading Environment Variables

```python
# settings.py
import os
from decouple import config

# JWT Settings from environment
GRAPHQL_AUTO_SETTINGS['SECURITY']['AUTHENTICATION']['JWT'].update({
    'SECRET_KEY': config('JWT_SECRET_KEY'),
    'ACCESS_TOKEN_LIFETIME': config('JWT_ACCESS_TOKEN_LIFETIME', default=3600, cast=int),
    'REFRESH_TOKEN_LIFETIME': config('JWT_REFRESH_TOKEN_LIFETIME', default=604800, cast=int),
})

# Rate Limiting Redis URL
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Security Headers
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=0, cast=int)
```

## 🏗️ Custom Configuration Classes

### Custom Authentication Backend

```python
# authentication.py
from django_graphql_auto.authentication import BaseAuthenticationBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomJWTAuthentication(BaseAuthenticationBackend):
    """
    Backend d'authentification JWT personnalisé.
    """
    
    def authenticate(self, request, token=None):
        """Authentifie un utilisateur avec un token JWT."""
        if not token:
            return None
            
        try:
            payload = self.decode_token(token)
            user_id = payload.get('user_id')
            
            if not user_id:
                return None
                
            user = User.objects.get(id=user_id)
            
            # Vérifications personnalisées
            if not user.is_active:
                return None
                
            if self.is_token_blacklisted(token):
                return None
                
            return user
            
        except (User.DoesNotExist, Exception):
            return None
    
    def decode_token(self, token):
        """Décode un token JWT."""
        import jwt
        from django.conf import settings
        
        return jwt.decode(
            token,
            settings.GRAPHQL_AUTO_SETTINGS['SECURITY']['AUTHENTICATION']['JWT']['SECRET_KEY'],
            algorithms=['HS256']
        )
    
    def is_token_blacklisted(self, token):
        """Vérifie si un token est sur liste noire."""
        # Implémentation de la liste noire des tokens
        from .models import BlacklistedToken
        return BlacklistedToken.objects.filter(token=token).exists()
```

### Custom Permission Class

```python
# permissions.py
from django_graphql_auto.permissions import BasePermission

class IsOwnerOrReadOnly(BasePermission):
    """
    Permission personnalisée : propriétaire ou lecture seule.
    """
    
    def has_permission(self, info, **kwargs):
        """Vérifie la permission au niveau de l'opération."""
        # Lecture autorisée pour tous
        if info.operation.operation == 'query':
            return True
            
        # Écriture nécessite une authentification
        return info.context.user and info.context.user.is_authenticated
    
    def has_object_permission(self, info, obj, **kwargs):
        """Vérifie la permission au niveau de l'objet."""
        # Lecture autorisée pour tous
        if info.operation.operation == 'query':
            return True
            
        # Écriture autorisée seulement pour le propriétaire
        return obj.owner == info.context.user

class BusinessHoursPermission(BasePermission):
    """
    Permission basée sur les heures d'ouverture.
    """
    
    def has_permission(self, info, **kwargs):
        """Vérifie si l'accès est autorisé pendant les heures d'ouverture."""
        from datetime import datetime, time
        
        now = datetime.now().time()
        business_start = time(9, 0)  # 9:00 AM
        business_end = time(17, 0)   # 5:00 PM
        
        # Staff peut accéder à tout moment
        if info.context.user and info.context.user.is_staff:
            return True
            
        # Autres utilisateurs seulement pendant les heures d'ouverture
        return business_start <= now <= business_end
```

### Custom Validator

```python
# validators.py
from django_graphql_auto.extensions.validation import BaseValidator
import re

class BusinessLogicValidator(BaseValidator):
    """
    Validateur personnalisé pour la logique métier.
    """
    
    def validate_field(self, field_name, value, context=None):
        """Valide un champ spécifique."""
        errors = []
        
        if field_name == 'product_code':
            errors.extend(self.validate_product_code(value))
        elif field_name == 'order_total':
            errors.extend(self.validate_order_total(value, context))
        elif field_name == 'delivery_date':
            errors.extend(self.validate_delivery_date(value))
            
        return errors
    
    def validate_product_code(self, code):
        """Valide un code produit."""
        if not code:
            return ["Le code produit est requis"]
            
        if not re.match(r'^[A-Z]{2}\d{4}$', code):
            return ["Le code produit doit suivre le format: XX0000"]
            
        # Vérifier l'unicité
        from your_app.models import Product
        if Product.objects.filter(code=code).exists():
            return ["Ce code produit existe déjà"]
            
        return []
    
    def validate_order_total(self, total, context):
        """Valide le total d'une commande."""
        if total <= 0:
            return ["Le total de la commande doit être positif"]
            
        # Vérifier les limites par type d'utilisateur
        user = context.get('user') if context else None
        if user and not user.is_staff:
            max_order = 10000  # Limite pour les utilisateurs normaux
            if total > max_order:
                return [f"Le total ne peut pas dépasser {max_order}€"]
                
        return []
    
    def validate_delivery_date(self, date):
        """Valide une date de livraison."""
        from datetime import datetime, timedelta
        
        if not date:
            return ["La date de livraison est requise"]
            
        # Doit être dans le futur
        if date <= datetime.now().date():
            return ["La date de livraison doit être dans le futur"]
            
        # Pas plus de 30 jours à l'avance
        max_date = datetime.now().date() + timedelta(days=30)
        if date > max_date:
            return ["La date de livraison ne peut pas être plus de 30 jours à l'avance"]
            
        return []
```

## 🔧 Advanced Configuration Examples

### Multi-Tenant Security Configuration

```python
# Multi-tenant security settings
GRAPHQL_AUTO_SETTINGS['SECURITY']['MULTI_TENANT'] = {
    'ENABLE': True,
    'TENANT_MODEL': 'your_app.Tenant',
    'TENANT_FIELD': 'tenant_id',
    'ISOLATION_LEVEL': 'STRICT',  # STRICT, MODERATE, LOOSE
    'CROSS_TENANT_ACCESS': {
        'SUPERUSER_ONLY': True,
        'ALLOWED_OPERATIONS': ['read'],
        'AUDIT_LOG': True,
    },
    'TENANT_SPECIFIC_LIMITS': {
        'premium': {
            'RATE_LIMIT_MULTIPLIER': 5,
            'COMPLEXITY_LIMIT_MULTIPLIER': 3,
        },
        'basic': {
            'RATE_LIMIT_MULTIPLIER': 1,
            'COMPLEXITY_LIMIT_MULTIPLIER': 1,
        },
    },
}
```

### API Key Authentication

```python
# API Key authentication configuration
GRAPHQL_AUTO_SETTINGS['SECURITY']['API_KEYS'] = {
    'ENABLE': True,
    'HEADER_NAME': 'X-API-Key',
    'QUERY_PARAM_NAME': 'api_key',
    'KEY_LENGTH': 32,
    'RATE_LIMITS': {
        'DEFAULT': 1000,  # requests per hour
        'PREMIUM': 10000,
        'ENTERPRISE': 0,  # unlimited
    },
    'SCOPES': {
        'read': ['query'],
        'write': ['mutation'],
        'admin': ['query', 'mutation', 'subscription'],
    },
    'AUDIT_LOG': True,
}
```

### Geographic Restrictions

```python
# Geographic access control
GRAPHQL_AUTO_SETTINGS['SECURITY']['GEO_RESTRICTIONS'] = {
    'ENABLE': True,
    'ALLOWED_COUNTRIES': ['US', 'CA', 'GB', 'FR', 'DE'],
    'BLOCKED_COUNTRIES': ['XX', 'YY'],  # ISO country codes
    'IP_GEOLOCATION_SERVICE': 'maxmind',  # maxmind, ipapi, etc.
    'BYPASS_FOR_STAFF': True,
    'AUDIT_BLOCKED_ATTEMPTS': True,
}
```

### Content Security Policy

```python
# Advanced CSP configuration
GRAPHQL_AUTO_SETTINGS['SECURITY']['CSP'] = {
    'ENABLE': True,
    'DIRECTIVES': {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'", 'cdn.jsdelivr.net'],
        'style-src': ["'self'", "'unsafe-inline'", 'fonts.googleapis.com'],
        'font-src': ["'self'", 'fonts.gstatic.com'],
        'img-src': ["'self'", 'data:', 'https:'],
        'connect-src': ["'self'", 'api.yourdomain.com'],
        'frame-ancestors': ["'none'"],
        'base-uri': ["'self'"],
        'form-action': ["'self'"],
    },
    'REPORT_URI': '/csp-report/',
    'REPORT_ONLY': False,
}
```

## 📊 Monitoring and Analytics Configuration

### Security Event Logging

```python
# Security event logging configuration
GRAPHQL_AUTO_SETTINGS['SECURITY']['EVENT_LOGGING'] = {
    'ENABLE': True,
    'EVENTS': {
        'AUTHENTICATION_SUCCESS': True,
        'AUTHENTICATION_FAILURE': True,
        'AUTHORIZATION_FAILURE': True,
        'RATE_LIMIT_EXCEEDED': True,
        'QUERY_COMPLEXITY_EXCEEDED': True,
        'VALIDATION_FAILURE': True,
        'SUSPICIOUS_ACTIVITY': True,
    },
    'STORAGE': {
        'BACKEND': 'database',  # database, elasticsearch, file
        'RETENTION_DAYS': 90,
        'COMPRESSION': True,
    },
    'ALERTING': {
        'ENABLE': True,
        'THRESHOLDS': {
            'FAILED_LOGINS_PER_MINUTE': 10,
            'RATE_LIMIT_VIOLATIONS_PER_HOUR': 100,
            'VALIDATION_ERRORS_PER_MINUTE': 50,
        },
        'NOTIFICATION_CHANNELS': ['email', 'slack', 'webhook'],
    },
}
```

### Performance Monitoring

```python
# Performance monitoring configuration
GRAPHQL_AUTO_SETTINGS['SECURITY']['PERFORMANCE'] = {
    'ENABLE': True,
    'METRICS': {
        'QUERY_EXECUTION_TIME': True,
        'VALIDATION_TIME': True,
        'AUTHENTICATION_TIME': True,
        'PERMISSION_CHECK_TIME': True,
    },
    'SLOW_QUERY_THRESHOLD': 1000,  # milliseconds
    'MEMORY_USAGE_TRACKING': True,
    'EXPORT_TO': ['prometheus', 'statsd'],
}
```

## 🧪 Testing Configuration

### Security Testing Settings

```python
# Testing-specific security configuration
if 'test' in sys.argv or 'pytest' in sys.modules:
    GRAPHQL_AUTO_SETTINGS['SECURITY'].update({
        'RATE_LIMITING': {
            'ENABLE': False,  # Disable for faster tests
        },
        'AUTHENTICATION': {
            'JWT': {
                'ACCESS_TOKEN_LIFETIME': 60,  # Short lifetime for tests
            },
        },
        'LOGGING': {
            'LOG_LEVEL': 'DEBUG',
            'LOG_FILE': 'test_security.log',
        },
    })
```

### Mock Security Services

```python
# Mock services for testing
class MockRateLimiter:
    """Mock rate limiter pour les tests."""
    
    def is_allowed(self, key, limit, window):
        return True
    
    def get_usage(self, key, window):
        return {'count': 0, 'remaining': 100}

class MockValidator:
    """Mock validator pour les tests."""
    
    def validate(self, value):
        return []

# Use mocks in test settings
if 'test' in sys.argv:
    GRAPHQL_AUTO_SETTINGS['SECURITY']['RATE_LIMITING']['BACKEND'] = MockRateLimiter
    GRAPHQL_AUTO_SETTINGS['SECURITY']['INPUT_VALIDATION']['CUSTOM_VALIDATORS'] = [MockValidator]
```

## 🚀 Production Deployment Configuration

### Production Security Checklist

```python
# Production security configuration
PRODUCTION_SECURITY_SETTINGS = {
    'SECURITY': {
        'AUTHENTICATION': {
            'JWT': {
                'SECRET_KEY': os.environ['JWT_SECRET_KEY'],  # From environment
                'ALGORITHM': 'RS256',  # Use RSA for production
                'ACCESS_TOKEN_LIFETIME': 900,  # 15 minutes
                'REFRESH_TOKEN_LIFETIME': 86400,  # 1 day
                'ROTATE_REFRESH_TOKENS': True,
                'BLACKLIST_AFTER_ROTATION': True,
            },
        },
        'RATE_LIMITING': {
            'ENABLE': True,
            'STORAGE_BACKEND': 'django_redis.cache.RedisCache',
            'DEFAULT_LIMITS': {
                'ANONYMOUS': {
                    'REQUESTS_PER_MINUTE': 5,
                    'REQUESTS_PER_HOUR': 50,
                },
                'AUTHENTICATED': {
                    'REQUESTS_PER_MINUTE': 30,
                    'REQUESTS_PER_HOUR': 500,
                },
            },
        },
        'QUERY_ANALYSIS': {
            'COMPLEXITY_ANALYSIS': {
                'MAX_COMPLEXITY': 50,  # Stricter in production
            },
            'DEPTH_ANALYSIS': {
                'MAX_DEPTH': 4,  # Stricter in production
            },
        },
        'SECURITY_HEADERS': {
            'ENABLE': True,
            'HEADERS': {
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
                'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self';",
            },
        },
        'LOGGING': {
            'LOG_LEVEL': 'WARNING',  # Less verbose in production
            'LOG_SECURITY_EVENTS': True,
            'AUDIT_ALL_REQUESTS': True,
        },
        'DEBUG': {
            'ENABLE_IN_DEBUG': False,
            'ALLOW_INTROSPECTION': False,  # Disable in production
            'GRAPHIQL_ENABLED': False,
        },
    }
}

# Apply production settings
if not DEBUG:
    GRAPHQL_AUTO_SETTINGS.update(PRODUCTION_SECURITY_SETTINGS)
```

### Docker Configuration

```dockerfile
# Dockerfile security configuration
FROM python:3.11-slim

# Security: Create non-root user
RUN groupadd -r django && useradd -r -g django django

# Security: Set secure file permissions
COPY --chown=django:django . /app
WORKDIR /app

# Security: Install security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Security: Use non-root user
USER django

# Security: Expose only necessary port
EXPOSE 8000

# Security: Use secure startup command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "myproject.wsgi:application"]
```

### Kubernetes Security Configuration

```yaml
# kubernetes-security.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: django-graphql-security-config
data:
  RATE_LIMIT_ENABLE: "true"
  JWT_ACCESS_TOKEN_LIFETIME: "900"
  QUERY_COMPLEXITY_LIMIT: "50"
  QUERY_DEPTH_LIMIT: "4"
  LOG_LEVEL: "WARNING"
  SECURE_SSL_REDIRECT: "true"
---
apiVersion: v1
kind: Secret
metadata:
  name: django-graphql-secrets
type: Opaque
data:
  JWT_SECRET_KEY: <base64-encoded-secret>
  DATABASE_PASSWORD: <base64-encoded-password>
  REDIS_PASSWORD: <base64-encoded-password>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: django-graphql-app
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: app
        image: your-app:latest
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        envFrom:
        - configMapRef:
            name: django-graphql-security-config
        - secretRef:
            name: django-graphql-secrets
```

## 📚 Configuration Best Practices

### Security Guidelines

1. **Environment Variables**: Store sensitive configuration in environment variables
2. **Principle of Least Privilege**: Grant minimum necessary permissions
3. **Defense in Depth**: Use multiple security layers
4. **Regular Updates**: Keep security configurations up to date
5. **Monitoring**: Implement comprehensive security monitoring
6. **Testing**: Regularly test security configurations

### Performance Considerations

1. **Caching**: Use Redis for rate limiting and session storage
2. **Database Optimization**: Optimize permission and validation queries
3. **Async Processing**: Use async for heavy security operations
4. **Resource Limits**: Set appropriate resource limits

### Maintenance

1. **Regular Audits**: Conduct regular security audits
2. **Log Analysis**: Regularly analyze security logs
3. **Configuration Reviews**: Review configurations quarterly
4. **Incident Response**: Have incident response procedures
5. **Backup and Recovery**: Backup security configurations

## 📚 Additional Resources

- [Security Overview](../features/security.md)
- [Authentication Examples](../examples/authentication-examples.md)
- [Permission Examples](../examples/permission-examples.md)
- [Validation Examples](../examples/validation-examples.md)
- [Performance Optimization](../development/performance.md)
- [Deployment Guide](../deployment/production.md)