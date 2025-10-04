"""
Development settings for django-graphql-boilerplate project (env-driven).
"""

from .base import *
import environ

env = environ.Env()

# Development toggles
DEBUG = env.bool('DJANGO_DEBUG', default=True)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# GraphiQL and introspection
RAIL_DJANGO_GRAPHQL['SECURITY']['ENABLE_GRAPHIQL'] = env.bool('ENABLE_GRAPHIQL', default=True)
RAIL_DJANGO_GRAPHQL['SECURITY']['ENABLE_INTROSPECTION'] = env.bool('ENABLE_INTROSPECTION', default=True)

# Email backend for development
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')