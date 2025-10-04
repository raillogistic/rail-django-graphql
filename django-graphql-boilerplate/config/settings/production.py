"""
Production settings for django-graphql-boilerplate project (env-driven).
"""

import os
from .base import *
from pathlib import Path
import environ

env = environ.Env()

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DJANGO_DEBUG', default=False)

ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=[])

DATABASES = {
    'default': env.db('DATABASE_URL')
}

_redis_url = env('REDIS_URL', default=None)
if _redis_url:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': _redis_url,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'IGNORE_EXCEPTIONS': True,
            }
        }
    }

# Security toggles
RAIL_DJANGO_GRAPHQL['SECURITY']['ENABLE_GRAPHIQL'] = env.bool('ENABLE_GRAPHIQL', default=False)
RAIL_DJANGO_GRAPHQL['SECURITY']['ENABLE_INTROSPECTION'] = env.bool('ENABLE_INTROSPECTION', default=False)

STATIC_ROOT = Path(env('STATIC_ROOT', default='/app/static/'))
MEDIA_ROOT = Path(env('MEDIA_ROOT', default='/app/media/'))

# Security settings
SECURE_BROWSER_XSS_FILTER = env.bool('SECURE_BROWSER_XSS_FILTER', default=True)
SECURE_CONTENT_TYPE_NOSNIFF = env.bool('SECURE_CONTENT_TYPE_NOSNIFF', default=True)
X_FRAME_OPTIONS = env('X_FRAME_OPTIONS', default='DENY')
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=True)
SECURE_PROXY_SSL_HEADER = env('SECURE_PROXY_SSL_HEADER', default=('HTTP_X_FORWARDED_PROTO', 'https'))
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True)
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])