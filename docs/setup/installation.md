# Installation Guide

This guide covers the installation and initial setup of Django GraphQL Auto.

## Requirements

- Python 3.8+
- Django 3.2+
- GraphQL Core 3.0+

## Installation Methods

### From PyPI (Recommended)

Install the latest stable version from PyPI:

```bash
pip install django-graphql-auto
```

### From GitHub (Latest Development)

Install the latest development version directly from GitHub:

```bash
pip install git+https://github.com/raillogistic/django-graphql-auto.git@main
```

### Development Installation

For development or contributing to the project:

```bash
git clone https://github.com/raillogistic/django-graphql-auto.git
cd django-graphql-auto
pip install -e .
```

## Optional Dependencies

Django GraphQL Auto supports optional features through extra dependencies:

### Authentication & Permissions

```bash
pip install django-graphql-auto[auth]
```

Includes:
- Django REST Framework integration
- JWT authentication support
- Advanced permission classes

### Performance & Caching

```bash
pip install django-graphql-auto[performance]
```

Includes:
- Redis caching support
- Query optimization tools
- Performance monitoring utilities

### File Upload Support

```bash
pip install django-graphql-auto[media]
```

Includes:
- GraphQL file upload support
- Image processing utilities
- Cloud storage integrations

### Documentation Generation

```bash
pip install django-graphql-auto[docs]
```

Includes:
- Sphinx documentation tools
- API documentation generators
- Schema visualization tools

### All Features

Install all optional dependencies:

```bash
pip install django-graphql-auto[all]
```

## ⚙️ Django Configuration

### Step 1: Update Settings

Add the library to your Django `INSTALLED_APPS`:

```python
# settings.py
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
    'django_extensions',

    # Django GraphQL Auto
    'rail_django_graphql',

    # Your apps
    'your_app',
    'another_app',
]
```

### Step 2: Configure GraphQL Settings

```python
# settings.py
import os

# GraphQL Configuration
GRAPHENE = {
    'SCHEMA': 'rail_django_graphql.schema.schema',
    'MIDDLEWARE': [
        'rail_django_graphql.core.middleware.GraphQLAuthMiddleware',
    ],
}

# Django GraphQL Auto Configuration
rail_django_graphql = {
    'SCHEMA_OUTPUT_DIR': os.path.join(BASE_DIR, 'generated_schema'),
    'AUTO_GENERATE_SCHEMA': True,
    'ENABLE_INTROSPECTION': True,
    'ENABLE_PLAYGROUND': DEBUG,
    'NAMING_CONVENTION': 'snake_case',
    'PAGINATION_SIZE': 20,
    'MAX_QUERY_DEPTH': 10,
    'ENABLE_SUBSCRIPTIONS': False,
    'APPS_TO_INCLUDE': [],  # Empty means all apps
    'APPS_TO_EXCLUDE': ['admin', 'auth', 'contenttypes', 'sessions'],
    'MODELS_TO_EXCLUDE': [],
    'ENABLE_MUTATIONS': True,
    'ENABLE_FILTERS': True,
    'ENABLE_NESTED_OPERATIONS': True,
    'ENABLE_FILE_UPLOADS': True,

    # File Upload & Media Configuration
    'FILE_UPLOADS': {
        'ENABLE_FILE_UPLOADS': True,
        'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
        'ALLOWED_EXTENSIONS': ['.jpg', '.png', '.pdf', '.txt'],
        'UPLOAD_PATH': 'uploads/',
        'ENABLE_VIRUS_SCANNING': True,
        'ENABLE_IMAGE_PROCESSING': True,
        'STORAGE_BACKEND': 'local',  # 'local', 's3', 'gcs', 'azure'
    },
}
```

### Step 3: Configure CORS (Optional)

If you plan to access GraphQL from a frontend application:

```python
# settings.py
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ... other middleware
]

# CORS settings for GraphQL
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React default
    "http://127.0.0.1:3000",
    "http://localhost:8080",  # Vue default
]

CORS_ALLOW_CREDENTIALS = True
```

### Step 4: Update URLs

```python
# urls.py
from django.contrib import admin
from django.urls import path, include
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    # Your other URLs
]
```

## 🔧 Initial Setup

### Step 1: System Dependencies (For File Uploads)

If you plan to use file uploads and media processing, install these system dependencies:

#### Ubuntu/Debian:

```bash
# Install ClamAV for virus scanning
sudo apt-get update
sudo apt-get install clamav clamav-daemon

# Install image processing libraries
sudo apt-get install libjpeg-dev libpng-dev libtiff-dev libwebp-dev

# Install file type detection
sudo apt-get install libmagic1

# Update virus definitions
sudo freshclam

# Start ClamAV daemon
sudo systemctl start clamav-daemon
sudo systemctl enable clamav-daemon
```

#### macOS:

```bash
# Install ClamAV
brew install clamav

# Install image processing libraries
brew install jpeg libpng libtiff webp

# Install file type detection
brew install libmagic

# Update virus definitions
freshclam

# Start ClamAV daemon
brew services start clamav
```

#### Windows:

```powershell
# Install ClamAV (download from https://www.clamav.net/downloads)
# Or use Chocolatey
choco install clamav

# For image processing, Pillow should work out of the box
# File type detection will use python-magic-bin package
```

### Step 2: Run Migrations

```bash
python manage.py migrate
```

### Step 3: Create Upload Directories

Create necessary directories for file uploads:

```bash
# Create upload directories
mkdir -p media/uploads
mkdir -p media/thumbnails
mkdir -p var/quarantine

# Set appropriate permissions (Linux/macOS)
chmod 755 media/uploads
chmod 755 media/thumbnails
chmod 700 var/quarantine  # Restricted access for quarantine
```

### Step 4: Generate GraphQL Schema

```bash
python manage.py generate_graphql_schema
```

This command will:

- Analyze all your Django models
- Generate GraphQL types, queries, and mutations
- Create schema files in the configured output directory
- Register the schema with GraphQL

### Step 5: Verify Installation

Start your Django development server:

```bash
python manage.py runserver
```

Visit `http://localhost:8000/graphql/` to access GraphiQL interface and verify your schema is working.

## 📁 Project Structure After Setup

After running the setup, your project structure will include:

```
your_project/
├── generated_schema/           # Auto-generated GraphQL files
│   ├── __init__.py
│   ├── types.py               # GraphQL types
│   ├── queries.py             # Query definitions
│   ├── mutations.py           # Mutation definitions
│   └── filters.py             # Filter definitions
├── your_app/
│   ├── models.py              # Your Django models
│   └── ...
└── manage.py
```

## 🎯 Quick Test

Create a simple model to test the setup:

```python
# your_app/models.py
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    isbn = models.CharField(max_length=13, unique=True)
    published_date = models.DateField()
    pages = models.PositiveIntegerField()

    def __str__(self):
        return self.title
```

Run migrations and regenerate schema:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py generate_graphql_schema
```

Now test in GraphiQL:

```graphql
# Query all authors
query {
  authors {
    id
    name
    email
    books {
      title
      isbn
    }
  }
}

# Test file upload functionality
mutation {
  uploadFile(
    input: {
      file: null # File will be provided via multipart form
      description: "Test upload"
    }
  ) {
    ok
    file {
      id
      filename
      size
      mimeType
      uploadedAt
    }
    errors
  }
}

# Query file processing status
query {
  fileProcessingStatus(fileId: "1") {
    id
    status
    virusScanResult
    thumbnailGenerated
    processingErrors
  }
}
```

## 🔧 Advanced Configuration

### Custom Schema Generation

```python
# settings.py
rail_django_graphql = {
    # ... other settings
    'CUSTOM_SCALARS': {
        'JSONField': 'rail_django_graphql.scalars.JSONScalar',
        'UUIDField': 'rail_django_graphql.scalars.UUIDScalar',
    },
    'FIELD_CONVERTERS': {
        'custom_field': 'your_app.converters.CustomFieldConverter',
    },
    'MUTATION_PERMISSIONS': {
        'create': 'rail_django_graphql.permissions.IsAuthenticated',
        'update': 'rail_django_graphql.permissions.IsOwnerOrReadOnly',
        'delete': 'rail_django_graphql.permissions.IsOwnerOrAdmin',
    },
}
```

### Environment-Specific Settings

```python
# settings/development.py
from .base import *

rail_django_graphql.update({
    'ENABLE_PLAYGROUND': True,
    'ENABLE_INTROSPECTION': True,
    'DEBUG_MODE': True,
})

# settings/production.py
from .base import *

rail_django_graphql.update({
    'ENABLE_PLAYGROUND': False,
    'ENABLE_INTROSPECTION': False,
    'DEBUG_MODE': False,
    'QUERY_COST_ANALYSIS': True,
    'MAX_QUERY_COMPLEXITY': 1000,
})
```

## 🚨 Troubleshooting

### Common Issues

1. **Schema not generating**: Check that your models are properly defined and migrations are up to date.

2. **GraphiQL not loading**: Ensure CORS is configured correctly and the GraphQL endpoint is accessible.

3. **Permission errors**: Verify that the output directory has write permissions.

4. **Import errors**: Make sure all dependencies are installed and Django apps are properly configured.

### Debug Mode

Enable debug mode for detailed error messages:

```python
# settings.py
rail_django_graphql = {
    # ... other settings
    'DEBUG_MODE': True,
    'VERBOSE_ERRORS': True,
}
```

## ✅ Next Steps

Now that you have the library installed and configured:

1. [Learn Basic Usage](../usage/basic-usage.md) - Start using GraphQL queries and mutations
2. [Explore Features](../features/schema-generation.md) - Understand how schema generation works
3. [Check Examples](../examples/basic-examples.md) - See practical examples
4. [Advanced Configuration](../setup/configuration.md) - Fine-tune your setup

## 🤝 Need Help?

- Check the [Troubleshooting Guide](../development/troubleshooting.md)
- Review [Common Issues](https://github.com/your-repo/django-graphql-auto/issues)
- Join our [Community Discussions](https://github.com/your-repo/django-graphql-auto/discussions)
