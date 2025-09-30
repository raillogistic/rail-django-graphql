"""Configuration for unified test suite."""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure Django settings for testing
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'graphene_django',
            'rail_django_graphql',
            'test_app',
        ],
        SECRET_KEY='test-secret-key-for-testing-only',
        ROOT_URLCONF='rail_django_graphql.urls',
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ],
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.debug',
                        'django.template.context_processors.request',
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                    ],
                },
            },
        ],
        USE_TZ=True,
        DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
        GRAPHENE={
            'SCHEMA': 'rail_django_graphql.schema.schema'
        },
        DJANGO_GRAPHQL_AUTO={
            'MODELS': {
                'test_app.Category': {
                    'fields': '__all__',
                    'mutations': True,
                    'properties': ['uppercase_name', 'post_count'],
                },
                'test_app.Tag': {
                    'fields': '__all__',
                    'mutations': True,
                },
                'test_app.Post': {
                    'fields': '__all__',
                    'mutations': True,
                },
                'test_app.Comment': {
                    'fields': '__all__',
                    'mutations': True,
                },
                'test_app.Client': {
                    'fields': '__all__',
                    'mutations': True,
                },
                'test_app.Bill': {
                    'fields': '__all__',
                    'mutations': True,
                },
            }
        }
    )

# Setup Django
django.setup()