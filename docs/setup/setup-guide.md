# Django GraphQL Auto-Generation - Complete Setup Guide

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Basic Configuration](#basic-configuration)
- [Advanced Configuration](#advanced-configuration)
- [Quick Start Tutorial](#quick-start-tutorial)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

## 🔧 Prerequisites

### System Requirements

- **Python**: 3.8 or higher
- **Django**: 3.2 or higher
- **Database**: PostgreSQL, MySQL, or SQLite
- **Memory**: Minimum 512MB RAM (2GB+ recommended for production)

### Required Knowledge

- Basic understanding of Django framework
- Familiarity with GraphQL concepts
- Python package management (pip/pipenv/poetry)

## 📦 Installation

### 1. Install the Package

Choose your preferred installation method:

#### Using pip (Recommended)
```bash
pip install django-graphql-auto
```

#### Using pipenv
```bash
pipenv install django-graphql-auto
```

#### Using poetry
```bash
poetry add django-graphql-auto
```

#### Development Installation
```bash
git clone https://github.com/your-org/django-graphql-auto.git
cd django-graphql-auto
pip install -e .
```

### 2. Install Dependencies

The package automatically installs core dependencies:
- `graphene-django>=3.0.0`
- `django-filter>=22.1`
- `django-cors-headers>=4.0.0`
- `graphene-file-upload>=1.3.0`

For additional features, install optional dependencies:

```bash
# For file uploads and media processing
pip install Pillow python-magic pyclamd

# For cloud storage (choose one)
pip install boto3                    # AWS S3
pip install google-cloud-storage     # Google Cloud Storage
pip install azure-storage-blob       # Azure Blob Storage

# For caching and performance
pip install redis django-redis

# For monitoring and logging
pip install sentry-sdk
```

### 3. System Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y \
    libmagic1 \
    libmagic-dev \
    clamav \
    clamav-daemon \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev
```

#### macOS
```bash
brew install libmagic clamav jpeg libpng webp
```

#### Windows
```powershell
# Install using chocolatey
choco install imagemagick
# ClamAV for Windows available from official website
```

## ⚙️ Basic Configuration

### 1. Django Settings

Add to your `settings.py`:

```python
# settings.py

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'graphene_django',
    'corsheaders',
    
    # Django GraphQL Auto
    'django_graphql_auto',
    
    # Your apps
    'your_app',
]

# Add CORS middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# GraphQL Configuration
GRAPHENE = {
    'SCHEMA': 'django_graphql_auto.schema.schema',
    'MIDDLEWARE': [
        'django_graphql_auto.middleware.AuthenticationMiddleware',
        'django_graphql_auto.middleware.PermissionMiddleware',
        'django_graphql_auto.middleware.RateLimitingMiddleware',
    ],
}

# Django GraphQL Auto Configuration
DJANGO_GRAPHQL_AUTO = {
    # Schema Generation
    'AUTO_GENERATE_SCHEMA': True,
    'SCHEMA_OUTPUT_DIR': 'generated_schema/',
    'NAMING_CONVENTION': 'snake_case',
    
    # Feature Toggles
    'ENABLE_MUTATIONS': True,
    'ENABLE_SUBSCRIPTIONS': False,
    'ENABLE_FILTERS': True,
    'ENABLE_FILE_UPLOADS': True,
    'ENABLE_PERMISSIONS': True,
    
    # Model Configuration
    'APPS_TO_INCLUDE': ['your_app'],  # Specify your apps
    'APPS_TO_EXCLUDE': ['admin', 'auth', 'contenttypes', 'sessions'],
    'MODELS_TO_EXCLUDE': [],
    
    # Pagination
    'PAGINATION_SIZE': 20,
    'MAX_QUERY_DEPTH': 10,
    
    # Performance
    'ENABLE_QUERY_OPTIMIZATION': True,
    'ENABLE_CACHING': False,  # Enable if Redis is configured
    'CACHE_TIMEOUT': 300,
    
    # Security
    'ENABLE_RATE_LIMITING': True,
    'RATE_LIMIT_PER_MINUTE': 100,
    'MAX_QUERY_COMPLEXITY': 1000,
}

# File Upload Configuration
FILE_UPLOADS = {
    'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
    'ALLOWED_EXTENSIONS': ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx'],
    'ALLOWED_MIME_TYPES': [
        'image/jpeg', 'image/png', 'image/gif',
        'application/pdf', 'application/msword'
    ],
    'UPLOAD_PATH': 'media/uploads/',
    'ENABLE_VIRUS_SCANNING': True,
    'ENABLE_IMAGE_PROCESSING': True,
    'STORAGE_BACKEND': 'local',  # 'local', 's3', 'gcs', 'azure'
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React development server
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### 2. URL Configuration

Add to your `urls.py`:

```python
# urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # GraphQL endpoint
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    
    # Optional: Include auto-generated URLs
    path('api/', include('django_graphql_auto.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 3. Create Required Directories

```bash
# Create media directories
mkdir -p media/uploads
mkdir -p media/thumbnails
mkdir -p var/quarantine

# Set permissions (Linux/macOS)
chmod 755 media/uploads
chmod 755 media/thumbnails
chmod 700 var/quarantine
```

## 🚀 Advanced Configuration

### Authentication & Security

```python
# settings.py

# JWT Authentication (if using)
DJANGO_GRAPHQL_AUTO.update({
    'AUTHENTICATION': {
        'BACKEND': 'django_graphql_auto.auth.JWTAuthentication',
        'JWT_SECRET_KEY': 'your-secret-key',
        'JWT_EXPIRATION_DELTA': timedelta(hours=24),
        'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=7),
    },
    
    'PERMISSIONS': {
        'DEFAULT_PERMISSION_CLASSES': [
            'django_graphql_auto.permissions.IsAuthenticated',
        ],
        'FIELD_LEVEL_PERMISSIONS': True,
        'OBJECT_LEVEL_PERMISSIONS': True,
    },
    
    'SECURITY': {
        'ENABLE_QUERY_DEPTH_ANALYSIS': True,
        'ENABLE_QUERY_COMPLEXITY_ANALYSIS': True,
        'ENABLE_INTROSPECTION': settings.DEBUG,
        'ENABLE_PLAYGROUND': settings.DEBUG,
    }
})
```

### Caching Configuration

```python
# settings.py

# Redis Cache (if using)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Enable caching in GraphQL Auto
DJANGO_GRAPHQL_AUTO.update({
    'ENABLE_CACHING': True,
    'CACHE_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'graphql_auto',
})
```

### Cloud Storage Configuration

#### AWS S3
```python
# settings.py
FILE_UPLOADS.update({
    'STORAGE_BACKEND': 's3',
    'S3_BUCKET_NAME': 'your-bucket-name',
    'S3_REGION': 'us-east-1',
    'S3_ACCESS_KEY_ID': 'your-access-key',
    'S3_SECRET_ACCESS_KEY': 'your-secret-key',
})
```

#### Google Cloud Storage
```python
# settings.py
FILE_UPLOADS.update({
    'STORAGE_BACKEND': 'gcs',
    'GCS_BUCKET_NAME': 'your-bucket-name',
    'GCS_CREDENTIALS_PATH': '/path/to/credentials.json',
})
```

## 🎯 Quick Start Tutorial

### 1. Create a Sample Model

```python
# your_app/models.py
from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
    
    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre")
    content = models.TextField(verbose_name="Contenu")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Auteur")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Catégorie")
    published = models.BooleanField(default=False, verbose_name="Publié")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
```

### 2. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Generate Schema

```bash
python manage.py generate_graphql_schema
```

### 4. Start Development Server

```bash
python manage.py runserver
```

### 5. Test GraphQL Endpoint

Visit `http://localhost:8000/graphql/` to access GraphiQL interface.

#### Sample Queries

```graphql
# Get all posts
query {
  posts {
    edges {
      node {
        id
        title
        content
        author {
          username
        }
        category {
          name
        }
        published
        createdAt
      }
    }
  }
}

# Get single post
query {
  post(id: "1") {
    id
    title
    content
    author {
      username
      email
    }
    category {
      name
      description
    }
  }
}

# Create new post
mutation {
  createPost(input: {
    title: "My First Post"
    content: "This is the content of my first post."
    authorId: 1
    categoryId: 1
    published: true
  }) {
    post {
      id
      title
      published
    }
    success
    errors
  }
}
```

## ✅ Verification

### 1. Check Schema Generation

```bash
# Verify schema file is generated
ls generated_schema/
# Should show: schema.graphql, types.py, queries.py, mutations.py

# Check schema content
cat generated_schema/schema.graphql
```

### 2. Test GraphQL Endpoint

```python
# test_graphql.py
import requests

def test_graphql_endpoint():
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
        'http://localhost:8000/graphql/',
        json={'query': query}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'data' in data
    print("GraphQL endpoint is working!")

if __name__ == "__main__":
    test_graphql_endpoint()
```

### 3. Verify File Upload

```bash
# Test file upload endpoint
curl -X POST \
  -F "operations={\"query\": \"mutation { uploadFile(file: null) { file { id url } } }\"}" \
  -F "map={\"0\": [\"variables.file\"]}" \
  -F "0=@test-image.jpg" \
  http://localhost:8000/graphql/
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Schema Not Generated
```bash
# Check if apps are properly configured
python manage.py shell
>>> from django_graphql_auto.core.schema_generator import SchemaGenerator
>>> generator = SchemaGenerator()
>>> generator.generate_schema()
```

#### 2. GraphQL Endpoint Not Working
- Verify `GRAPHENE` settings in `settings.py`
- Check URL configuration
- Ensure CORS is properly configured

#### 3. File Upload Issues
- Check file permissions on upload directories
- Verify system dependencies are installed
- Check `FILE_UPLOADS` configuration

#### 4. Permission Errors
```python
# Check permission configuration
python manage.py shell
>>> from django_graphql_auto.security.permissions import PermissionChecker
>>> checker = PermissionChecker()
>>> checker.check_permissions(user, 'query', 'Post')
```

### Debug Mode

Enable debug mode for detailed error messages:

```python
# settings.py
DJANGO_GRAPHQL_AUTO.update({
    'DEBUG': True,
    'ENABLE_QUERY_LOGGING': True,
    'LOG_LEVEL': 'DEBUG',
})
```

### Performance Issues

```python
# Enable query optimization
DJANGO_GRAPHQL_AUTO.update({
    'ENABLE_QUERY_OPTIMIZATION': True,
    'ENABLE_CACHING': True,
    'CACHE_TIMEOUT': 300,
})
```

## 📚 Next Steps

1. **Read the [Usage Guide](../usage/basic-usage.md)** - Learn how to use the generated GraphQL API
2. **Explore [Advanced Features](../features/)** - Security, file uploads, performance optimization
3. **Check [API Reference](../api/)** - Detailed API documentation
4. **Review [Examples](../examples/)** - Real-world usage examples
5. **Join the Community** - Get help and share experiences

## 🤝 Getting Help

- **Documentation**: [Full Documentation](../README.md)
- **GitHub Issues**: [Report bugs or request features](https://github.com/your-org/django-graphql-auto/issues)
- **Community**: [Join our Discord](https://discord.gg/django-graphql-auto)
- **Email**: support@django-graphql-auto.com

---

**Congratulations!** 🎉 You've successfully set up Django GraphQL Auto-Generation. Your GraphQL API is now automatically generated from your Django models with advanced features like security, file uploads, and performance optimization.