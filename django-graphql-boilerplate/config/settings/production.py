"""
Production settings for django-graphql-boilerplate project.
"""

import os
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Production database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', os.environ.get('DB_NAME', 'rail_django_graphql')),
        'USER': os.environ.get('POSTGRES_USER', os.environ.get('DB_USER', 'postgres')),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', os.environ.get('DB_PASSWORD')),
        'HOST': os.environ.get('DB_HOST', os.environ.get('POSTGRES_HOST', 'db')),
        'PORT': os.environ.get('DB_PORT', os.environ.get('POSTGRES_PORT', '5432')),
    }
}

# Cache configuration using Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
        }
    }
}

# Disable GraphiQL in production
RAIL_DJANGO_GRAPHQL['SECURITY']['ENABLE_GRAPHIQL'] = False
RAIL_DJANGO_GRAPHQL['SECURITY']['ENABLE_INTROSPECTION'] = False

# Static files
STATIC_ROOT = '/app/static/'

# Media files
MEDIA_ROOT = '/app/media/'

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True