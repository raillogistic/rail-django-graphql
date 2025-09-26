# Production Deployment Guide

This guide covers deploying the Django GraphQL Auto-Generation System to production with security hardening and performance optimization.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Configuration](#environment-configuration)
3. [Security Hardening](#security-hardening)
4. [Performance Optimization](#performance-optimization)
5. [Database Configuration](#database-configuration)
6. [Web Server Configuration](#web-server-configuration)
7. [SSL/TLS Configuration](#ssltls-configuration)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Backup and Recovery](#backup-and-recovery)
10. [Deployment Strategies](#deployment-strategies)
11. [Post-Deployment Verification](#post-deployment-verification)
12. [Maintenance and Updates](#maintenance-and-updates)

## Pre-Deployment Checklist

### Code Quality
- [ ] All tests pass (unit, integration, security)
- [ ] Code review completed
- [ ] Security audit performed
- [ ] Performance testing completed
- [ ] Documentation updated

### Dependencies
- [ ] All dependencies pinned to specific versions
- [ ] Security vulnerabilities checked (`pip audit`)
- [ ] Unused dependencies removed
- [ ] Production requirements.txt created

### Configuration
- [ ] Environment variables configured
- [ ] Secret keys generated and secured
- [ ] Database migrations tested
- [ ] Static files collected
- [ ] Media files handling configured

## Environment Configuration

### Environment Variables

Create a `.env` file for production:

```bash
# Django Settings
DJANGO_SETTINGS_MODULE=myproject.settings.production
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
DATABASE_CONN_MAX_AGE=600

# GraphQL Security
GRAPHQL_JWT_SECRET_KEY=your-jwt-secret-key
GRAPHQL_JWT_EXPIRATION_DELTA=3600
GRAPHQL_RATE_LIMIT_ENABLED=True
GRAPHQL_QUERY_DEPTH_LIMIT=10
GRAPHQL_QUERY_COMPLEXITY_LIMIT=1000

# Cache
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300

# Email
EMAIL_HOST=smtp.yourdomain.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your-email-password
EMAIL_USE_TLS=True

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
X_FRAME_OPTIONS=DENY

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=your-sentry-dsn
```

### Production Settings

Create `settings/production.py`:

```python
from .base import *
import os
from decouple import config

# Security
DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': config('DATABASE_CONN_MAX_AGE', default=600, cast=int),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
        }
    }
}

# Session
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

# CSRF
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Security Headers
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# GraphQL Security
GRAPHQL_AUTO_SECURITY = {
    'AUTHENTICATION_REQUIRED': True,
    'RATE_LIMITING': {
        'ENABLED': True,
        'DEFAULT_RATE': '1000/hour',
        'BURST_RATE': '100/minute',
    },
    'QUERY_ANALYSIS': {
        'DEPTH_LIMIT': 10,
        'COMPLEXITY_LIMIT': 1000,
        'TIMEOUT': 30,
    },
    'INPUT_VALIDATION': {
        'XSS_PROTECTION': True,
        'SQL_INJECTION_PROTECTION': True,
        'FIELD_VALIDATION': True,
    },
}

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
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
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
        'django_graphql_auto': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

## Security Hardening

### 1. Server Security

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install fail2ban
sudo apt install fail2ban -y

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

### 2. Application Security

```python
# Additional security middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_graphql_auto.middleware.SecurityMiddleware',
    'django_graphql_auto.middleware.RateLimitMiddleware',
]

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https:")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
```

### 3. Database Security

```python
# PostgreSQL security configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'sslmode': 'require',
            'sslcert': '/path/to/client-cert.pem',
            'sslkey': '/path/to/client-key.pem',
            'sslrootcert': '/path/to/ca-cert.pem',
        },
    }
}
```

## Performance Optimization

### 1. Database Optimization

```python
# Database connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        },
    }
}

# Query optimization
GRAPHQL_AUTO_PERFORMANCE = {
    'QUERY_OPTIMIZATION': {
        'SELECT_RELATED_DEPTH': 2,
        'PREFETCH_RELATED': True,
        'BATCH_LOADING': True,
    },
    'CACHING': {
        'QUERY_CACHE_TTL': 300,
        'SCHEMA_CACHE_TTL': 3600,
        'RESULT_CACHE_TTL': 60,
    },
}
```

### 2. Caching Strategy

```python
# Multi-level caching
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        }
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
    },
    'graphql': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/3',
    },
}

# GraphQL caching
GRAPHQL_AUTO_CACHE = {
    'SCHEMA_CACHE': 'graphql',
    'QUERY_CACHE': 'graphql',
    'RESULT_CACHE': 'default',
    'CACHE_TIMEOUT': {
        'SCHEMA': 3600,
        'QUERY': 300,
        'RESULT': 60,
    },
}
```

### 3. Static Files Optimization

```python
# Static files with WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = False

# Compression
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True
```

## Database Configuration

### PostgreSQL Production Setup

```sql
-- Create database and user
CREATE DATABASE myproject_prod;
CREATE USER myproject_user WITH PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE myproject_prod TO myproject_user;
ALTER USER myproject_user CREATEDB;

-- Performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Reload configuration
SELECT pg_reload_conf();
```

### Database Indexes

```python
# Custom indexes for GraphQL queries
class Meta:
    indexes = [
        models.Index(fields=['created_at']),
        models.Index(fields=['updated_at']),
        models.Index(fields=['status', 'created_at']),
        models.Index(fields=['user', 'created_at']),
    ]
```

## Web Server Configuration

### Nginx Configuration

```nginx
upstream django {
    server unix:///tmp/uwsgi.sock;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=graphql:10m rate=5r/s;

    # Static Files
    location /static/ {
        alias /path/to/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        gzip_static on;
    }

    location /media/ {
        alias /path/to/media/;
        expires 1M;
        add_header Cache-Control "public";
    }

    # GraphQL Endpoint
    location /graphql/ {
        limit_req zone=graphql burst=10 nodelay;
        uwsgi_pass django;
        include /etc/nginx/uwsgi_params;
        uwsgi_read_timeout 300s;
        uwsgi_send_timeout 300s;
    }

    # API Endpoints
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        uwsgi_pass django;
        include /etc/nginx/uwsgi_params;
    }

    # Main Application
    location / {
        uwsgi_pass django;
        include /etc/nginx/uwsgi_params;
    }
}
```

### uWSGI Configuration

```ini
[uwsgi]
# Django settings
module = myproject.wsgi:application
home = /path/to/venv
chdir = /path/to/project

# Process management
master = true
processes = 4
threads = 2
enable-threads = true
thunder-lock = true

# Socket
socket = /tmp/uwsgi.sock
chmod-socket = 666
vacuum = true

# Performance
buffer-size = 32768
post-buffering = 8192
harakiri = 300
max-requests = 5000
max-worker-lifetime = 3600

# Logging
logto = /var/log/uwsgi/uwsgi.log
log-maxsize = 50000000
log-backupname = /var/log/uwsgi/uwsgi.log.old

# Security
uid = www-data
gid = www-data
```

## SSL/TLS Configuration

### Let's Encrypt Setup

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### SSL Security Test

```bash
# Test SSL configuration
curl -I https://yourdomain.com
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

## Monitoring and Logging

### Application Monitoring

```python
# Sentry integration
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn=config('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(
            transaction_style='url',
            middleware_spans=True,
            signals_spans=True,
        ),
        RedisIntegration(),
    ],
    traces_sample_rate=0.1,
    send_default_pii=True,
    environment='production',
)
```

### System Monitoring

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Setup log rotation
sudo nano /etc/logrotate.d/django
```

```
/var/log/django/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload uwsgi
    endscript
}
```

### Health Check Endpoint

```python
# health/views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis

def health_check(request):
    """System health check endpoint"""
    status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'services': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['services']['database'] = 'healthy'
    except Exception as e:
        status['services']['database'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    # Cache check
    try:
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        status['services']['cache'] = 'healthy'
    except Exception as e:
        status['services']['cache'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    return JsonResponse(status)
```

## Backup and Recovery

### Database Backup

```bash
#!/bin/bash
# backup_db.sh

DB_NAME="myproject_prod"
DB_USER="myproject_user"
BACKUP_DIR="/backups/database"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/backup_$DATE.sql.gz s3://your-backup-bucket/database/
```

### Media Files Backup

```bash
#!/bin/bash
# backup_media.sh

MEDIA_DIR="/path/to/media"
BACKUP_DIR="/backups/media"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C $MEDIA_DIR .

# Sync to S3
aws s3 sync $MEDIA_DIR s3://your-media-bucket/media/
```

## Deployment Strategies

### Blue-Green Deployment

```bash
#!/bin/bash
# deploy.sh

# Variables
BLUE_DIR="/var/www/myproject-blue"
GREEN_DIR="/var/www/myproject-green"
CURRENT_LINK="/var/www/myproject-current"

# Determine current and new environments
if [ -L $CURRENT_LINK ] && [ "$(readlink $CURRENT_LINK)" = "$BLUE_DIR" ]; then
    CURRENT_ENV="blue"
    NEW_ENV="green"
    NEW_DIR=$GREEN_DIR
else
    CURRENT_ENV="green"
    NEW_ENV="blue"
    NEW_DIR=$BLUE_DIR
fi

echo "Deploying to $NEW_ENV environment..."

# Deploy to new environment
cd $NEW_DIR
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# Run tests
python manage.py test

# Switch traffic
sudo ln -sfn $NEW_DIR $CURRENT_LINK
sudo systemctl reload nginx

echo "Deployment to $NEW_ENV completed successfully!"
```

### Rolling Deployment

```bash
#!/bin/bash
# rolling_deploy.sh

SERVERS=("server1" "server2" "server3")
DEPLOY_DIR="/var/www/myproject"

for server in "${SERVERS[@]}"; do
    echo "Deploying to $server..."
    
    # Remove from load balancer
    ssh $server "sudo nginx -s reload"
    
    # Deploy
    ssh $server "cd $DEPLOY_DIR && git pull && pip install -r requirements.txt"
    ssh $server "cd $DEPLOY_DIR && python manage.py migrate && python manage.py collectstatic --noinput"
    ssh $server "sudo systemctl restart uwsgi"
    
    # Add back to load balancer
    ssh $server "sudo nginx -s reload"
    
    # Wait before next server
    sleep 30
done
```

## Post-Deployment Verification

### Automated Tests

```python
# tests/test_deployment.py
import requests
import pytest

class TestDeployment:
    def test_health_check(self):
        """Test health check endpoint"""
        response = requests.get('https://yourdomain.com/health/')
        assert response.status_code == 200
        assert response.json()['status'] == 'healthy'
    
    def test_graphql_endpoint(self):
        """Test GraphQL endpoint availability"""
        query = """
        query {
            __schema {
                types {
                    name
                }
            }
        }
        """
        response = requests.post(
            'https://yourdomain.com/graphql/',
            json={'query': query}
        )
        assert response.status_code == 200
        assert 'data' in response.json()
    
    def test_ssl_certificate(self):
        """Test SSL certificate validity"""
        response = requests.get('https://yourdomain.com/')
        assert response.status_code == 200
        assert response.url.startswith('https://')
    
    def test_security_headers(self):
        """Test security headers"""
        response = requests.get('https://yourdomain.com/')
        headers = response.headers
        
        assert 'Strict-Transport-Security' in headers
        assert 'X-Content-Type-Options' in headers
        assert 'X-Frame-Options' in headers
```

### Performance Testing

```bash
# Load testing with Apache Bench
ab -n 1000 -c 10 https://yourdomain.com/graphql/

# Load testing with wrk
wrk -t12 -c400 -d30s https://yourdomain.com/graphql/
```

## Maintenance and Updates

### Regular Maintenance Tasks

```bash
#!/bin/bash
# maintenance.sh

# Update system packages
sudo apt update && sudo apt upgrade -y

# Clean up logs
sudo journalctl --vacuum-time=30d
find /var/log -name "*.log" -mtime +30 -delete

# Database maintenance
sudo -u postgres psql -c "VACUUM ANALYZE;"

# Clear expired cache
python manage.py clearcache

# Update SSL certificates
sudo certbot renew --quiet

# Restart services
sudo systemctl restart uwsgi nginx redis-server postgresql
```

### Update Process

```bash
#!/bin/bash
# update.sh

# Backup before update
./backup_db.sh
./backup_media.sh

# Update code
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Run tests
python manage.py test

# Restart services
sudo systemctl restart uwsgi
sudo systemctl reload nginx
```

### Monitoring Scripts

```python
# monitoring/check_performance.py
import psutil
import requests
import time
from django.core.mail import send_mail

def check_system_health():
    """Monitor system performance"""
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    if cpu_percent > 80:
        send_alert(f"High CPU usage: {cpu_percent}%")
    
    # Memory usage
    memory = psutil.virtual_memory()
    if memory.percent > 85:
        send_alert(f"High memory usage: {memory.percent}%")
    
    # Disk usage
    disk = psutil.disk_usage('/')
    if disk.percent > 90:
        send_alert(f"High disk usage: {disk.percent}%")
    
    # GraphQL response time
    start_time = time.time()
    response = requests.post(
        'https://yourdomain.com/graphql/',
        json={'query': '{ __schema { types { name } } }'}
    )
    response_time = time.time() - start_time
    
    if response_time > 5:
        send_alert(f"Slow GraphQL response: {response_time}s")

def send_alert(message):
    """Send alert email"""
    send_mail(
        'System Alert',
        message,
        'alerts@yourdomain.com',
        ['admin@yourdomain.com'],
        fail_silently=False,
    )
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   free -h
   ps aux --sort=-%mem | head
   
   # Restart services
   sudo systemctl restart uwsgi
   ```

2. **Database Connection Issues**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Check connections
   sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
   ```

3. **SSL Certificate Issues**
   ```bash
   # Check certificate expiry
   openssl x509 -in /path/to/cert.pem -text -noout | grep "Not After"
   
   # Renew certificate
   sudo certbot renew
   ```

### Performance Optimization

1. **Database Query Optimization**
   ```python
   # Enable query logging
   LOGGING['loggers']['django.db.backends'] = {
       'level': 'DEBUG',
       'handlers': ['console'],
   }
   ```

2. **Cache Optimization**
   ```bash
   # Monitor Redis
   redis-cli info memory
   redis-cli monitor
   ```

3. **Static File Optimization**
   ```bash
   # Compress static files
   python manage.py compress --force
   python manage.py collectstatic --noinput
   ```

This comprehensive deployment guide ensures your Django GraphQL Auto-Generation System is deployed securely and performs optimally in production.