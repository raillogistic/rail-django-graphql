# Installation & Setup Guide

This guide will walk you through installing and setting up the Django GraphQL Auto-Generation Library in your Django project.

## 📋 Prerequisites

- Python 3.8 or higher
- Django 3.2 or higher
- Basic understanding of Django models and GraphQL concepts

## 🚀 Installation

### Step 1: Install Dependencies

```bash
# Install the core library (when published)
pip install django-graphql-auto

# Or install from source
git clone https://github.com/your-repo/django-graphql-auto.git
cd django-graphql-auto
pip install -e .
```

### Step 2: Install Required Dependencies

```bash
pip install graphene-django>=3.0.0
pip install django-filter>=22.1
pip install django-cors-headers>=4.0.0
pip install django-extensions>=3.2.0
pip install graphene-file-upload>=1.3.0
```

Or use the provided requirements file:

```bash
pip install -r requirements.txt
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
    'django_graphql_auto',
    
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
    'SCHEMA': 'django_graphql_auto.schema.schema',
    'MIDDLEWARE': [
        'django_graphql_auto.core.middleware.GraphQLAuthMiddleware',
    ],
}

# Django GraphQL Auto Configuration
DJANGO_GRAPHQL_AUTO = {
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

### Step 1: Run Migrations

```bash
python manage.py migrate
```

### Step 2: Generate GraphQL Schema

```bash
python manage.py generate_graphql_schema
```

This command will:
- Analyze all your Django models
- Generate GraphQL types, queries, and mutations
- Create schema files in the configured output directory
- Register the schema with GraphQL

### Step 3: Verify Installation

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

# Create a new author
mutation {
  createAuthor(input: {
    name: "Jane Doe"
    email: "jane@example.com"
    bio: "A prolific writer"
  }) {
    ok
    author {
      id
      name
      email
    }
    errors
  }
}
```

## 🔧 Advanced Configuration

### Custom Schema Generation

```python
# settings.py
DJANGO_GRAPHQL_AUTO = {
    # ... other settings
    'CUSTOM_SCALARS': {
        'JSONField': 'django_graphql_auto.scalars.JSONScalar',
        'UUIDField': 'django_graphql_auto.scalars.UUIDScalar',
    },
    'FIELD_CONVERTERS': {
        'custom_field': 'your_app.converters.CustomFieldConverter',
    },
    'MUTATION_PERMISSIONS': {
        'create': 'django_graphql_auto.permissions.IsAuthenticated',
        'update': 'django_graphql_auto.permissions.IsOwnerOrReadOnly',
        'delete': 'django_graphql_auto.permissions.IsOwnerOrAdmin',
    },
}
```

### Environment-Specific Settings

```python
# settings/development.py
from .base import *

DJANGO_GRAPHQL_AUTO.update({
    'ENABLE_PLAYGROUND': True,
    'ENABLE_INTROSPECTION': True,
    'DEBUG_MODE': True,
})

# settings/production.py
from .base import *

DJANGO_GRAPHQL_AUTO.update({
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
DJANGO_GRAPHQL_AUTO = {
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