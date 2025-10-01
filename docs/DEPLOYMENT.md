# Deployment Guide

This guide covers deploying the Django GraphQL Multi-Schema System in various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Production Configuration](#production-configuration)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Performance Optimization](#performance-optimization)
- [Monitoring and Logging](#monitoring-and-logging)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- Python 3.8+
- Django 3.2+
- PostgreSQL 12+ (recommended) or MySQL 8.0+
- Redis 6.0+ (for caching and sessions)
- Nginx (for production)
- Gunicorn or uWSGI (WSGI server)

### Dependencies

```bash
# Core dependencies
pip install django>=3.2
pip install graphene-django>=3.0
pip install psycopg2-binary  # PostgreSQL
pip install redis
pip install celery  # For background tasks

# Production dependencies
pip install gunicorn
pip install whitenoise  # Static files
pip install django-cors-headers
pip install django-environ  # Environment variables
```

## Environment Setup

### Environment Variables

Create a `.env` file for environment-specific settings:

```bash
# .env
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0

# GraphQL Multi-Schema Settings
GRAPHQL_MULTI_SCHEMA_ENABLED=True
GRAPHQL_AUTO_DISCOVERY=True
GRAPHQL_ENABLE_PLAYGROUND=False  # Disable in production
GRAPHQL_ENABLE_INTROSPECTION=False  # Disable in production

# CORS Settings
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Cache Settings
CACHE_TIMEOUT=3600
CACHE_KEY_PREFIX=graphql_

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### Django Settings

```python
# settings/production.py
import os
from pathlib import Path
import environ

# Environment variables
env = environ.Env(
    DEBUG=(bool, False),
    GRAPHQL_MULTI_SCHEMA_ENABLED=(bool, True),
    GRAPHQL_AUTO_DISCOVERY=(bool, True),
)

BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(BASE_DIR / '.env')

# Security
DEBUG = env('DEBUG')
SECRET_KEY = env('SECRET_KEY')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost'])

# Database
DATABASES = {
    'default': env.db()
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': env('CACHE_KEY_PREFIX', default='graphql_'),
        'TIMEOUT': env.int('CACHE_TIMEOUT', default=3600),
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CORS
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_CREDENTIALS = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'rail_django_graphql': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# GraphQL Multi-Schema Configuration
RAIL_DJANGO_GRAPHQL = {
    'ENABLED': env.bool('GRAPHQL_MULTI_SCHEMA_ENABLED'),
    'AUTO_DISCOVERY': env.bool('GRAPHQL_AUTO_DISCOVERY'),
    'ENABLE_PLAYGROUND': env.bool('GRAPHQL_ENABLE_PLAYGROUND', default=False),
    'ENABLE_INTROSPECTION': env.bool('GRAPHQL_ENABLE_INTROSPECTION', default=False),
    'DEFAULT_SCHEMA_SETTINGS': {
        'enable_caching': True,
        'cache_timeout': env.int('CACHE_TIMEOUT', default=3600),
        'require_authentication': False,
        'enable_cors': True,
    },
    'PLUGINS': [
        'myproject.plugins.ValidationPlugin',
        'myproject.plugins.CachingPlugin',
        'myproject.plugins.MetricsPlugin',
    ],
    'DISCOVERY_HOOKS': [
        'myproject.hooks.custom_discovery_hook',
    ],
    'RATE_LIMITING': {
        'enabled': True,
        'requests_per_minute': 100,
        'burst_limit': 20,
    },
    'SECURITY': {
        'max_query_depth': 10,
        'max_query_complexity': 1000,
        'disable_introspection': True,
        'require_https': True,
    }
}

# Security settings
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=True)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

## Production Configuration

### WSGI Configuration

```python
# wsgi.py
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings.production')

application = get_wsgi_application()
```

### Gunicorn Configuration

```python
# gunicorn.conf.py
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

# Process naming
proc_name = "graphql_multi_schema"

# Server mechanics
preload_app = True
daemon = False
pidfile = "/var/run/gunicorn/graphql_multi_schema.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# SSL
keyfile = "/path/to/ssl/private.key"
certfile = "/path/to/ssl/certificate.crt"
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/graphql-multi-schema
upstream graphql_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL configuration
    ssl_certificate /path/to/ssl/certificate.crt;
    ssl_certificate_key /path/to/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Static files
    location /static/ {
        alias /path/to/your/project/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /path/to/your/project/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # GraphQL endpoints
    location /graphql/ {
        proxy_pass http://graphql_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers for GraphQL
        add_header Access-Control-Allow-Origin "https://yourdomain.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        add_header Access-Control-Allow-Credentials true always;
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }

    # API endpoints
    location /api/ {
        proxy_pass http://graphql_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }

    # Main application
    location / {
        proxy_pass http://graphql_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Rate limiting configuration
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
}
```

## Docker Deployment

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=myproject.settings.production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create logs directory
RUN mkdir -p /app/logs

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "myproject.wsgi:application"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: graphql_db
      POSTGRES_USER: graphql_user
      POSTGRES_PASSWORD: graphql_password
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    command: gunicorn --config gunicorn.conf.py myproject.wsgi:application
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://graphql_user:graphql_password@db:5432/graphql_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./ssl:/etc/ssl/certs
    depends_on:
      - web

  celery:
    build: .
    command: celery -A myproject worker -l info
    volumes:
      - .:/app
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://graphql_user:graphql_password@db:5432/graphql_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    restart: unless-stopped
    networks:
      - backend

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    networks:
      - backend

  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/conf.d:/etc/nginx/conf.d
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./ssl:/etc/ssl/certs
    depends_on:
      - web
    restart: unless-stopped
    networks:
      - backend
      - frontend

  celery:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: celery -A myproject worker -l info
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - backend

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.prod
    command: celery -A myproject beat -l info
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - backend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

## Cloud Deployment

### AWS Deployment with ECS

```yaml
# aws-task-definition.json
{
  "family": "graphql-multi-schema",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "web",
      "image": "your-account.dkr.ecr.region.amazonaws.com/graphql-multi-schema:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DJANGO_SETTINGS_MODULE",
          "value": "myproject.settings.production"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:graphql/secret-key"
        },
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:graphql/database-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/graphql-multi-schema",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8000/health/ || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: graphql-multi-schema
  labels:
    app: graphql-multi-schema
spec:
  replicas: 3
  selector:
    matchLabels:
      app: graphql-multi-schema
  template:
    metadata:
      labels:
        app: graphql-multi-schema
    spec:
      containers:
      - name: web
        image: your-registry/graphql-multi-schema:latest
        ports:
        - containerPort: 8000
        env:
        - name: DJANGO_SETTINGS_MODULE
          value: "myproject.settings.production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: graphql-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: graphql-secrets
              key: secret-key
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"

---
apiVersion: v1
kind: Service
metadata:
  name: graphql-service
spec:
  selector:
    app: graphql-multi-schema
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer

---
apiVersion: v1
kind: Secret
metadata:
  name: graphql-secrets
type: Opaque
data:
  database-url: <base64-encoded-database-url>
  secret-key: <base64-encoded-secret-key>
```

## Performance Optimization

### Database Optimization

```python
# settings/performance.py

# Database connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        },
        'CONN_MAX_AGE': 600,
    }
}

# Query optimization
RAIL_DJANGO_GRAPHQL = {
    'QUERY_OPTIMIZATION': {
        'enable_query_batching': True,
        'max_batch_size': 10,
        'enable_dataloader': True,
        'prefetch_related_objects': True,
    },
    'CACHING': {
        'enable_query_caching': True,
        'cache_timeout': 300,
        'cache_key_function': 'myproject.utils.cache_key_function',
    }
}
```

### Caching Strategy

```python
# utils/caching.py
from django.core.cache import cache
from django.utils.encoding import force_str
import hashlib
import json

def cache_key_function(query, variables, context):
    """Generate cache key for GraphQL queries."""
    key_data = {
        'query': query,
        'variables': variables or {},
        'user_id': getattr(context.user, 'id', None) if context.user.is_authenticated else None,
    }
    
    key_string = json.dumps(key_data, sort_keys=True)
    return f"graphql:{hashlib.md5(force_str(key_string).encode()).hexdigest()}"

def cached_resolver(cache_timeout=300):
    """Decorator for caching resolver results."""
    def decorator(resolver_func):
        def wrapper(self, info, **kwargs):
            # Generate cache key
            cache_key = f"resolver:{resolver_func.__name__}:{hash(str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute resolver
            result = resolver_func(self, info, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, cache_timeout)
            return result
        
        return wrapper
    return decorator
```

## Monitoring and Logging

### Health Check Endpoint

```python
# health/views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from rail_django_graphql.core.registry import schema_registry
import redis

def health_check(request):
    """Comprehensive health check endpoint."""
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Cache check
    try:
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        health_status['checks']['cache'] = 'healthy'
    except Exception as e:
        health_status['checks']['cache'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Schema registry check
    try:
        schemas = schema_registry.list_schemas()
        health_status['checks']['schema_registry'] = f'healthy ({len(schemas)} schemas)'
    except Exception as e:
        health_status['checks']['schema_registry'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return JsonResponse(health_status, status=status_code)
```

### Prometheus Metrics

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from django.http import HttpResponse
from rail_django_graphql.core.registry import schema_registry

# Metrics
graphql_requests_total = Counter(
    'graphql_requests_total',
    'Total GraphQL requests',
    ['schema_name', 'operation_type', 'status']
)

graphql_request_duration = Histogram(
    'graphql_request_duration_seconds',
    'GraphQL request duration',
    ['schema_name', 'operation_type']
)

graphql_schemas_total = Gauge(
    'graphql_schemas_total',
    'Total number of registered schemas'
)

def metrics_view(request):
    """Prometheus metrics endpoint."""
    # Update schema count
    graphql_schemas_total.set(len(schema_registry.list_schemas()))
    
    return HttpResponse(
        generate_latest(),
        content_type='text/plain; charset=utf-8'
    )

class GraphQLMetricsMiddleware:
    """Middleware to collect GraphQL metrics."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.path.startswith('/graphql/'):
            start_time = time.time()
            
            response = self.get_response(request)
            
            duration = time.time() - start_time
            schema_name = request.path.split('/')[2] if len(request.path.split('/')) > 2 else 'unknown'
            operation_type = self.get_operation_type(request)
            status = 'success' if response.status_code < 400 else 'error'
            
            graphql_requests_total.labels(
                schema_name=schema_name,
                operation_type=operation_type,
                status=status
            ).inc()
            
            graphql_request_duration.labels(
                schema_name=schema_name,
                operation_type=operation_type
            ).observe(duration)
            
            return response
        
        return self.get_response(request)
    
    def get_operation_type(self, request):
        """Extract operation type from request."""
        try:
            if request.method == 'POST':
                body = json.loads(request.body)
                query = body.get('query', '')
                if query.strip().startswith('mutation'):
                    return 'mutation'
                elif query.strip().startswith('subscription'):
                    return 'subscription'
                else:
                    return 'query'
        except:
            pass
        return 'unknown'
```

## Security Considerations

### Query Complexity Analysis

```python
# security/query_analysis.py
from graphql import validate, parse
from graphql.validation import NoSchemaIntrospectionCustomRule
from graphql.validation.rules import QueryComplexityRule, QueryDepthRule

class GraphQLSecurityMiddleware:
    """Middleware for GraphQL security checks."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.max_query_depth = 10
        self.max_query_complexity = 1000
    
    def __call__(self, request):
        if request.path.startswith('/graphql/') and request.method == 'POST':
            try:
                body = json.loads(request.body)
                query = body.get('query', '')
                
                # Parse query
                document = parse(query)
                
                # Validate query depth and complexity
                errors = validate(
                    schema=self.get_schema(request),
                    document=document,
                    rules=[
                        QueryDepthRule(max_depth=self.max_query_depth),
                        QueryComplexityRule(max_complexity=self.max_query_complexity),
                        NoSchemaIntrospectionCustomRule,
                    ]
                )
                
                if errors:
                    return JsonResponse({
                        'errors': [{'message': str(error)} for error in errors]
                    }, status=400)
                
            except Exception as e:
                return JsonResponse({
                    'errors': [{'message': 'Invalid query'}]
                }, status=400)
        
        return self.get_response(request)
```

### Rate Limiting

```python
# security/rate_limiting.py
from django.core.cache import cache
from django.http import JsonResponse
import time

class GraphQLRateLimitMiddleware:
    """Rate limiting middleware for GraphQL endpoints."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.requests_per_minute = 100
        self.burst_limit = 20
    
    def __call__(self, request):
        if request.path.startswith('/graphql/'):
            client_ip = self.get_client_ip(request)
            
            if not self.is_rate_limited(client_ip):
                return JsonResponse({
                    'errors': [{'message': 'Rate limit exceeded'}]
                }, status=429)
        
        return self.get_response(request)
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_rate_limited(self, client_ip):
        """Check if client is rate limited."""
        now = int(time.time())
        minute = now // 60
        
        # Check requests per minute
        minute_key = f"rate_limit:{client_ip}:{minute}"
        minute_requests = cache.get(minute_key, 0)
        
        if minute_requests >= self.requests_per_minute:
            return False
        
        # Check burst limit
        burst_key = f"burst_limit:{client_ip}"
        burst_requests = cache.get(burst_key, 0)
        
        if burst_requests >= self.burst_limit:
            return False
        
        # Increment counters
        cache.set(minute_key, minute_requests + 1, 60)
        cache.set(burst_key, burst_requests + 1, 10)
        
        return True
```

## Troubleshooting

### Common Issues

#### 1. Schema Registration Failures

```python
# Debug schema registration
from rail_django_graphql.core.registry import schema_registry

# Check registered schemas
schemas = schema_registry.list_schemas()
print(f"Registered schemas: {[s.name for s in schemas]}")

# Check for registration errors
try:
    schema_registry.register_schema(
        name='test_schema',
        description='Test schema',
        version='1.0.0'
    )
except Exception as e:
    print(f"Registration error: {e}")
```

#### 2. Performance Issues

```python
# Enable query logging
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        }
    }
}

# Monitor query execution
import time
from django.db import connection

def debug_queries():
    """Debug database queries."""
    start_queries = len(connection.queries)
    start_time = time.time()
    
    # Your GraphQL query here
    
    end_time = time.time()
    end_queries = len(connection.queries)
    
    print(f"Queries executed: {end_queries - start_queries}")
    print(f"Execution time: {end_time - start_time:.2f}s")
    
    for query in connection.queries[start_queries:]:
        print(f"Query: {query['sql']}")
        print(f"Time: {query['time']}")
```

#### 3. Memory Issues

```python
# Monitor memory usage
import psutil
import gc

def monitor_memory():
    """Monitor memory usage."""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    print(f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS: {memory_info.vms / 1024 / 1024:.2f} MB")
    
    # Force garbage collection
    gc.collect()
```

### Deployment Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] SSL certificates installed
- [ ] Nginx configuration tested
- [ ] Gunicorn configuration optimized
- [ ] Redis connection verified
- [ ] Health check endpoint working
- [ ] Monitoring and logging configured
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] Backup strategy implemented
- [ ] Error tracking configured (Sentry)
- [ ] Performance monitoring enabled

### Monitoring Commands

```bash
# Check application logs
tail -f /var/log/gunicorn/error.log

# Monitor system resources
htop

# Check database connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"

# Monitor Redis
redis-cli info

# Check Nginx status
sudo systemctl status nginx

# Test SSL configuration
openssl s_client -connect yourdomain.com:443

# Check certificate expiration
openssl x509 -in /path/to/certificate.crt -text -noout | grep "Not After"
```

This deployment guide provides comprehensive instructions for deploying the Django GraphQL Multi-Schema System in production environments with proper security, monitoring, and performance optimizations.