"""
Configuration Django pour les tests.

Ce module configure:
- Base de données en mémoire pour les tests
- Cache local pour les tests
- Paramètres de sécurité pour les tests
- Configuration de logging
- Paramètres GraphQL
"""

import os
import sys
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Ajouter le répertoire du projet au path Python
sys.path.insert(0, str(BASE_DIR))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-test-secret-key-not-for-production-use-only'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Test mode
TESTING = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'graphene_django',
    
    # Local apps
    'django_graphql_auto',
    
    # Test apps
    'tests',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tests.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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
]

WSGI_APPLICATION = 'tests.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 20,
        },
        'TEST': {
            'NAME': ':memory:',
        }
    }
}

# Cache configuration for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = []  # Désactivé pour les tests

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================================================
# CONFIGURATION GRAPHQL
# ============================================================================

# Configuration Graphene
GRAPHENE = {
    'SCHEMA': 'tests.schema.schema',
    'MIDDLEWARE': [
        'graphene_django.debug.DjangoDebugMiddleware',
    ],
    'TESTING_ENDPOINT': '/graphql/',
}

# Configuration GraphQL personnalisée
GRAPHQL_AUTO_SETTINGS = {
    'ENABLE_INTROSPECTION': True,
    'ENABLE_PLAYGROUND': True,
    'ENABLE_SUBSCRIPTIONS': False,
    'MAX_QUERY_DEPTH': 10,
    'MAX_QUERY_COMPLEXITY': 1000,
    'ENABLE_QUERY_COST_ANALYSIS': True,
    'ENABLE_CACHING': True,
    'CACHE_TIMEOUT': 300,
    'ENABLE_PERMISSIONS': True,
    'ENABLE_RATE_LIMITING': False,  # Désactivé pour les tests
    'ENABLE_LOGGING': True,
    'LOG_LEVEL': 'DEBUG',
    'ENABLE_METRICS': True,
    'ENABLE_TRACING': False,  # Désactivé pour les tests
}

# ============================================================================
# CONFIGURATION DE LOGGING
# ============================================================================

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
        'test': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'test',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'tests.log',
            'formatter': 'verbose',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['null'],  # Désactiver les logs SQL par défaut
            'level': 'DEBUG',
            'propagate': False,
        },
        'django_graphql_auto': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'graphene': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'tests': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# ============================================================================
# CONFIGURATION DE SÉCURITÉ POUR LES TESTS
# ============================================================================

# Désactiver certaines vérifications de sécurité pour les tests
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_BROWSER_XSS_FILTER = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Configuration CORS pour les tests
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ============================================================================
# CONFIGURATION DE PERFORMANCE POUR LES TESTS
# ============================================================================

# Désactiver les migrations pour accélérer les tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

# Utiliser cette classe si --nomigrations est passé
if '--nomigrations' in sys.argv:
    MIGRATION_MODULES = DisableMigrations()

# Configuration de la base de données pour les tests parallèles
if 'test' in sys.argv:
    DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'
    DATABASES['default']['NAME'] = ':memory:'
    
    # Configuration pour les tests parallèles
    import multiprocessing
    TEST_RUNNER = 'django.test.runner.DiscoverRunner'
    
    # Utiliser une base de données séparée pour chaque worker
    if hasattr(multiprocessing, 'current_process'):
        process_name = multiprocessing.current_process().name
        if process_name != 'MainProcess':
            DATABASES['default']['NAME'] = f':memory:{process_name}'

# ============================================================================
# CONFIGURATION EMAIL POUR LES TESTS
# ============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# ============================================================================
# CONFIGURATION SESSION POUR LES TESTS
# ============================================================================

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ============================================================================
# CONFIGURATION CELERY POUR LES TESTS (si utilisé)
# ============================================================================

# Exécuter les tâches de manière synchrone pendant les tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ============================================================================
# CONFIGURATION SPÉCIFIQUE AUX TESTS
# ============================================================================

# Désactiver les signaux Django qui peuvent interférer avec les tests
SILENCED_SYSTEM_CHECKS = [
    'models.W042',  # Auto-created primary key warning
]

# Configuration pour les tests de performance
PERFORMANCE_TEST_SETTINGS = {
    'ENABLE_PROFILING': True,
    'PROFILE_MEMORY': True,
    'PROFILE_QUERIES': True,
    'MAX_QUERY_TIME': 1.0,  # secondes
    'MAX_MEMORY_USAGE': 100 * 1024 * 1024,  # 100MB
    'MAX_QUERIES_PER_REQUEST': 50,
}

# Configuration pour les tests de concurrence
CONCURRENCY_TEST_SETTINGS = {
    'MAX_WORKERS': 10,
    'TIMEOUT': 30,  # secondes
    'ENABLE_DEADLOCK_DETECTION': True,
}

# Configuration pour les tests d'API
API_TEST_SETTINGS = {
    'BASE_URL': 'http://testserver',
    'TIMEOUT': 10,  # secondes
    'RETRY_COUNT': 3,
    'ENABLE_RATE_LIMITING': False,
}

# Configuration pour les fixtures de test
FIXTURE_DIRS = [
    BASE_DIR / 'tests' / 'fixtures' / 'data',
]

# Configuration pour les tests de cache
CACHE_TEST_SETTINGS = {
    'ENABLE_CACHE_TESTING': True,
    'CACHE_TIMEOUT': 300,
    'ENABLE_CACHE_INVALIDATION_TESTING': True,
}

# Configuration pour les tests de validation
VALIDATION_TEST_SETTINGS = {
    'STRICT_VALIDATION': True,
    'COMPREHENSIVE_TESTING': True,
    'ENABLE_EDGE_CASE_TESTING': True,
}

# Configuration pour les tests de sécurité
SECURITY_TEST_SETTINGS = {
    'ENABLE_SECURITY_TESTING': True,
    'TEST_AUTHENTICATION': True,
    'TEST_AUTHORIZATION': True,
    'TEST_INPUT_VALIDATION': True,
    'TEST_SQL_INJECTION': True,
    'TEST_XSS': True,
    'TEST_CSRF': True,
}

# ============================================================================
# VARIABLES D'ENVIRONNEMENT POUR LES TESTS
# ============================================================================

# Marquer que nous sommes en mode test
os.environ['TESTING'] = 'true'
os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'

# Configuration pour les tests CI/CD
if os.environ.get('CI'):
    # Configuration spécifique pour l'intégration continue
    LOGGING['handlers']['console']['level'] = 'WARNING'
    DATABASES['default']['OPTIONS']['timeout'] = 30