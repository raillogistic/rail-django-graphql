# Django GraphQL Boilerplate - Structure Design

## 📦 Boilerplate Overview

The `django-graphql-boilerplate` is a ready-to-use Django project template that demonstrates the full capabilities of the `rail-django-graphql` library. It includes a complete example application (`test_app`) with models, configurations, and best practices.

## 🏗️ Repository Structure

```
django-graphql-boilerplate/                # Root repository
├── .github/                               # GitHub workflows and templates
│   ├── workflows/
│   │   ├── test.yml                      # Testing workflow
│   │   ├── deploy.yml                    # Deployment workflow
│   │   ├── security.yml                  # Security scanning
│   │   └── docs.yml                      # Documentation building
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── question.md
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/                                  # Project documentation
│   ├── installation.md                   # Installation guide
│   ├── configuration.md                  # Configuration guide
│   ├── deployment.md                     # Deployment guide
│   ├── api-examples.md                   # API usage examples
│   ├── customization.md                  # Customization guide
│   ├── troubleshooting.md                # Troubleshooting guide
│   └── architecture.md                   # Architecture overview
├── deploy/                                # Deployment configurations
│   ├── docker/
│   │   ├── Dockerfile                    # Production Dockerfile
│   │   ├── Dockerfile.dev                # Development Dockerfile
│   │   └── docker-compose.yml            # Docker Compose configuration
│   ├── kubernetes/
│   │   ├── namespace.yaml                # Kubernetes namespace
│   │   ├── deployment.yaml               # Kubernetes deployment
│   │   ├── service.yaml                  # Kubernetes service
│   │   ├── ingress.yaml                  # Kubernetes ingress
│   │   └── configmap.yaml                # Kubernetes config map
│   ├── nginx/
│   │   ├── nginx.conf                    # Nginx configuration
│   │   └── ssl.conf                      # SSL configuration
│   └── scripts/
│       ├── deploy.sh                     # Deployment script
│       ├── backup.sh                     # Backup script
│       └── restore.sh                    # Restore script
├── config/                                # Configuration files
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                       # Base settings
│   │   ├── development.py                # Development settings
│   │   ├── production.py                 # Production settings
│   │   ├── testing.py                    # Testing settings
│   │   └── local.py.example              # Local settings example
│   ├── urls.py                           # Root URL configuration
│   ├── wsgi.py                           # WSGI configuration
│   ├── asgi.py                           # ASGI configuration
│   └── celery.py                         # Celery configuration
├── apps/                                  # Django applications
│   ├── __init__.py
│   ├── core/                             # Core application
│   │   ├── __init__.py
│   │   ├── apps.py                       # App configuration
│   │   ├── models.py                     # Core models
│   │   ├── admin.py                      # Admin configuration
│   │   ├── views.py                      # Core views
│   │   ├── urls.py                       # Core URLs
│   │   ├── permissions.py                # Custom permissions
│   │   ├── middleware.py                 # Custom middleware
│   │   ├── utils.py                      # Utility functions
│   │   ├── signals.py                    # Django signals
│   │   ├── managers.py                   # Custom managers
│   │   ├── validators.py                 # Custom validators
│   │   ├── migrations/
│   │   │   └── __init__.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       └── test_utils.py
│   ├── users/                            # User management app
│   │   ├── __init__.py
│   │   ├── apps.py                       # App configuration
│   │   ├── models.py                     # User models
│   │   ├── admin.py                      # User admin
│   │   ├── views.py                      # User views
│   │   ├── urls.py                       # User URLs
│   │   ├── serializers.py                # DRF serializers
│   │   ├── permissions.py                # User permissions
│   │   ├── managers.py                   # User managers
│   │   ├── signals.py                    # User signals
│   │   ├── forms.py                      # User forms
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   └── 0001_initial.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       └── test_auth.py
│   ├── blog/                             # Blog application (example)
│   │   ├── __init__.py
│   │   ├── apps.py                       # App configuration
│   │   ├── models.py                     # Blog models
│   │   ├── admin.py                      # Blog admin
│   │   ├── views.py                      # Blog views
│   │   ├── urls.py                       # Blog URLs
│   │   ├── serializers.py                # Blog serializers
│   │   ├── permissions.py                # Blog permissions
│   │   ├── filters.py                    # Blog filters
│   │   ├── managers.py                   # Blog managers
│   │   ├── signals.py                    # Blog signals
│   │   ├── utils.py                      # Blog utilities
│   │   ├── migrations/
│   │   │   ├── __init__.py
│   │   │   └── 0001_initial.py
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       ├── test_graphql.py
│   │       └── test_permissions.py
│   └── ecommerce/                        # E-commerce application (example)
│       ├── __init__.py
│       ├── apps.py                       # App configuration
│       ├── models.py                     # E-commerce models
│       ├── admin.py                      # E-commerce admin
│       ├── views.py                      # E-commerce views
│       ├── urls.py                       # E-commerce URLs
│       ├── serializers.py                # E-commerce serializers
│       ├── permissions.py                # E-commerce permissions
│       ├── filters.py                    # E-commerce filters
│       ├── managers.py                   # E-commerce managers
│       ├── signals.py                    # E-commerce signals
│       ├── utils.py                      # E-commerce utilities
│       ├── migrations/
│       │   ├── __init__.py
│       │   └── 0001_initial.py
│       └── tests/
│           ├── __init__.py
│           ├── test_models.py
│           ├── test_views.py
│           ├── test_graphql.py
│           └── test_orders.py
├── static/                                # Static files
│   ├── css/
│   │   ├── main.css                      # Main stylesheet
│   │   └── admin.css                     # Admin customizations
│   ├── js/
│   │   ├── main.js                       # Main JavaScript
│   │   └── graphql-client.js             # GraphQL client
│   ├── images/
│   │   ├── logo.png                      # Project logo
│   │   └── favicon.ico                   # Favicon
│   └── fonts/
│       └── custom-font.woff2             # Custom fonts
├── media/                                 # Media files (uploads)
│   ├── uploads/
│   │   ├── images/                       # Image uploads
│   │   ├── documents/                    # Document uploads
│   │   └── avatars/                      # User avatars
│   └── .gitkeep                          # Keep directory in git
├── templates/                             # Django templates
│   ├── base.html                         # Base template
│   ├── index.html                        # Home page template
│   ├── admin/
│   │   └── base_site.html                # Admin customization
│   ├── registration/
│   │   ├── login.html                    # Login template
│   │   ├── logout.html                   # Logout template
│   │   └── password_reset.html           # Password reset
│   ├── graphql/
│   │   ├── graphiql.html                 # GraphiQL interface
│   │   └── playground.html               # GraphQL Playground
│   └── errors/
│       ├── 404.html                      # 404 error page
│       ├── 500.html                      # 500 error page
│       └── 403.html                      # 403 error page
├── locale/                                # Internationalization
│   ├── en/
│   │   └── LC_MESSAGES/
│   │       ├── django.po                 # English translations
│   │       └── django.mo                 # Compiled translations
│   └── fr/
│       └── LC_MESSAGES/
│           ├── django.po                 # French translations
│           └── django.mo                 # Compiled translations
├── tests/                                 # Project-wide tests
│   ├── __init__.py
│   ├── conftest.py                       # Pytest configuration
│   ├── fixtures/                         # Test fixtures
│   │   ├── __init__.py
│   │   ├── users.py                      # User fixtures
│   │   ├── blog.py                       # Blog fixtures
│   │   └── ecommerce.py                  # E-commerce fixtures
│   ├── integration/                      # Integration tests
│   │   ├── __init__.py
│   │   ├── test_graphql_schema.py        # Schema integration tests
│   │   ├── test_authentication.py        # Auth integration tests
│   │   └── test_permissions.py           # Permission integration tests
│   ├── e2e/                             # End-to-end tests
│   │   ├── __init__.py
│   │   ├── test_user_workflow.py         # User workflow tests
│   │   ├── test_blog_workflow.py         # Blog workflow tests
│   │   └── test_ecommerce_workflow.py    # E-commerce workflow tests
│   └── performance/                      # Performance tests
│       ├── __init__.py
│       ├── test_query_performance.py     # Query performance tests
│       └── test_load_testing.py          # Load testing
├── scripts/                               # Utility scripts
│   ├── setup.py                          # Initial setup script
│   ├── seed_data.py                      # Database seeding
│   ├── backup.py                         # Database backup
│   ├── migrate.py                        # Migration helper
│   ├── test.py                           # Test runner
│   └── deploy.py                         # Deployment helper
├── requirements/                          # Requirements files
│   ├── base.txt                          # Base requirements
│   ├── development.txt                   # Development requirements
│   ├── production.txt                    # Production requirements
│   └── testing.txt                       # Testing requirements
├── .env.example                          # Environment variables example
├── .gitignore                            # Git ignore rules
├── .pre-commit-config.yaml               # Pre-commit hooks
├── .editorconfig                         # Editor configuration
├── .dockerignore                         # Docker ignore rules
├── docker-compose.yml                    # Docker Compose for development
├── docker-compose.prod.yml               # Docker Compose for production
├── Dockerfile                            # Production Dockerfile
├── Dockerfile.dev                        # Development Dockerfile
├── manage.py                             # Django management script
├── pytest.ini                            # Pytest configuration
├── mypy.ini                              # MyPy configuration
├── .coveragerc                           # Coverage configuration
├── tox.ini                               # Tox configuration
├── setup.cfg                             # Setup configuration
├── pyproject.toml                        # Modern Python configuration
├── README.md                             # Project README
├── CHANGELOG.md                          # Version changelog
├── CONTRIBUTING.md                       # Contribution guidelines
├── CODE_OF_CONDUCT.md                    # Code of conduct
├── SECURITY.md                           # Security policy
└── LICENSE                               # MIT License
```

## ⚙️ Configuration Structure

### Settings Organization
```python
# config/settings/base.py
"""
Base settings for Django GraphQL Boilerplate project.
"""
import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
DEBUG = False
ALLOWED_HOSTS = []

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rail_django_graphql',  # Our GraphQL library
    'graphene_django',
    'django_filters',
    'corsheaders',
    'rest_framework',
]

LOCAL_APPS = [
    'apps.core',
    'apps.users',
    'apps.blog',
    'apps.ecommerce',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# GraphQL Configuration
GRAPHENE = {
    'SCHEMA': 'config.schema.schema',
    'MIDDLEWARE': [
        'rail_django_graphql.middleware.auth.AuthenticationMiddleware',
        'rail_django_graphql.middleware.permissions.PermissionMiddleware',
        'rail_django_graphql.middleware.caching.CachingMiddleware',
        'rail_django_graphql.middleware.logging.LoggingMiddleware',
    ],
}

# Rail Django GraphQL Configuration
RAIL_DJANGO_GRAPHQL = {
    'SCHEMA_CONFIGS': {
        'default': {
            'models': [
                'apps.users.models.User',
                'apps.users.models.Profile',
                'apps.blog.models.Post',
                'apps.blog.models.Comment',
                'apps.blog.models.Category',
                'apps.blog.models.Tag',
                'apps.ecommerce.models.Product',
                'apps.ecommerce.models.Category',
                'apps.ecommerce.models.Order',
                'apps.ecommerce.models.OrderItem',
            ],
            'enable_mutations': True,
            'enable_subscriptions': True,
            'enable_filters': True,
            'enable_pagination': True,
            'max_query_depth': 10,
            'max_query_complexity': 1000,
        }
    },
    'AUTHENTICATION': {
        'backends': [
            'rail_django_graphql.auth.backends.JWTBackend',
            'rail_django_graphql.auth.backends.SessionBackend',
        ],
        'jwt_secret': os.environ.get('JWT_SECRET', SECRET_KEY),
        'jwt_algorithm': 'HS256',
        'jwt_expiration': 3600,  # 1 hour
    },
    'PERMISSIONS': {
        'default_permission_classes': [
            'rail_django_graphql.permissions.IsAuthenticated',
        ],
        'enable_object_permissions': True,
        'enable_field_permissions': True,
    },
    'CACHING': {
        'enabled': True,
        'backend': 'django.core.cache.backends.redis.RedisCache',
        'timeout': 300,  # 5 minutes
        'key_prefix': 'graphql',
    },
    'PERFORMANCE': {
        'enable_dataloader': True,
        'enable_query_optimization': True,
        'max_batch_size': 100,
    },
}
```

### Environment Configuration
```bash
# .env.example
# Django Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/django_graphql_boilerplate
REDIS_URL=redis://localhost:6379/0

# GraphQL
JWT_SECRET=your-jwt-secret-here
GRAPHQL_DEBUG=True
ENABLE_GRAPHIQL=True

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password

# Media & Static Files
MEDIA_URL=/media/
STATIC_URL=/static/
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket

# Monitoring
SENTRY_DSN=your-sentry-dsn-here
ENABLE_PROMETHEUS=True

# Security
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 📱 Example Applications

### Blog Application Models
```python
# apps/blog/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from rail_django_graphql.decorators import graphql_model, graphql_field

User = get_user_model()

@graphql_model(
    enable_mutations=['create', 'update', 'delete'],
    enable_filters=['title', 'content', 'status', 'created_at'],
    permissions=['blog.view_post', 'blog.add_post']
)
class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    content = models.TextField(verbose_name="Contenu")
    excerpt = models.TextField(max_length=500, blank=True, verbose_name="Extrait")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Auteur")
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, verbose_name="Catégorie")
    tags = models.ManyToManyField('Tag', blank=True, verbose_name="Tags")
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Brouillon'),
            ('published', 'Publié'),
            ('archived', 'Archivé'),
        ],
        default='draft',
        verbose_name="Statut"
    )
    featured_image = models.ImageField(upload_to='blog/images/', blank=True, verbose_name="Image mise en avant")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="Publié le")

    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @graphql_field
    def comment_count(self):
        """Nombre de commentaires approuvés"""
        return self.comments.filter(approved=True).count()

    @graphql_field
    def reading_time(self):
        """Temps de lecture estimé en minutes"""
        word_count = len(self.content.split())
        return max(1, word_count // 200)  # 200 mots par minute

@graphql_model(
    enable_mutations=['create', 'update', 'delete'],
    enable_filters=['name', 'created_at'],
)
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']

    def __str__(self):
        return self.name

@graphql_model(
    enable_mutations=['create', 'update', 'delete'],
    enable_filters=['name'],
)
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']

    def __str__(self):
        return self.name

@graphql_model(
    enable_mutations=['create', 'update', 'delete'],
    enable_filters=['approved', 'created_at'],
    permissions=['blog.view_comment', 'blog.add_comment']
)
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name="Article")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Auteur")
    content = models.TextField(verbose_name="Contenu")
    approved = models.BooleanField(default=False, verbose_name="Approuvé")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"
        ordering = ['-created_at']

    def __str__(self):
        return f"Commentaire de {self.author.username} sur {self.post.title}"
```

### E-commerce Application Models
```python
# apps/ecommerce/models.py
from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from rail_django_graphql.decorators import graphql_model, graphql_field

User = get_user_model()

@graphql_model(
    enable_mutations=['create', 'update', 'delete'],
    enable_filters=['name', 'category', 'price', 'in_stock', 'created_at'],
    permissions=['ecommerce.view_product', 'ecommerce.add_product']
)
class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(verbose_name="Description")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix")
    category = models.ForeignKey('Category', on_delete=models.CASCADE, verbose_name="Catégorie")
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU")
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name="Quantité en stock")
    image = models.ImageField(upload_to='products/', blank=True, verbose_name="Image")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @graphql_field
    def in_stock(self):
        """Vérifie si le produit est en stock"""
        return self.stock_quantity > 0

    @graphql_field
    def average_rating(self):
        """Note moyenne du produit"""
        reviews = self.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0

@graphql_model(
    enable_mutations=['create', 'update', 'delete'],
    enable_filters=['status', 'created_at', 'total'],
    permissions=['ecommerce.view_order', 'ecommerce.add_order']
)
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours de traitement'),
        ('shipped', 'Expédié'),
        ('delivered', 'Livré'),
        ('cancelled', 'Annulé'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")
    shipping_address = models.TextField(verbose_name="Adresse de livraison")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-created_at']

    def __str__(self):
        return f"Commande #{self.id} - {self.user.username}"

    @graphql_field
    def item_count(self):
        """Nombre d'articles dans la commande"""
        return self.items.count()
```

## 🚀 Quick Start Guide

### 1. Installation
```bash
# Clone the boilerplate
git clone https://github.com/raillogistic/django-graphql-boilerplate.git
cd django-graphql-boilerplate

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/development.txt

# Copy environment file
cp .env.example .env
```

### 2. Database Setup
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data
python scripts/seed_data.py
```

### 3. Run Development Server
```bash
# Start development server
python manage.py runserver

# Access GraphiQL interface
# http://localhost:8000/graphql/
```

### 4. Docker Setup
```bash
# Build and run with Docker Compose
docker-compose up --build

# Run migrations in container
docker-compose exec web python manage.py migrate

# Create superuser in container
docker-compose exec web python manage.py createsuperuser
```

## 🧪 Testing Strategy

### Test Configuration
```python
# pytest.ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = config.settings.testing
python_files = tests.py test_*.py *_tests.py
addopts = --cov=apps --cov-report=html --cov-report=term-missing --reuse-db
testpaths = tests apps
```

### Example GraphQL Tests
```python
# tests/integration/test_graphql_schema.py
import pytest
from graphene.test import Client
from config.schema import schema

@pytest.mark.django_db
class TestBlogGraphQL:
    def test_query_posts(self, user, blog_post):
        """Test querying blog posts"""
        client = Client(schema)
        query = '''
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
                            commentCount
                            readingTime
                        }
                    }
                }
            }
        '''
        result = client.execute(query)
        assert not result.get('errors')
        assert len(result['data']['posts']['edges']) == 1

    def test_create_post_mutation(self, user):
        """Test creating a blog post"""
        client = Client(schema)
        mutation = '''
            mutation CreatePost($input: CreatePostInput!) {
                createPost(input: $input) {
                    post {
                        id
                        title
                        content
                        status
                    }
                    success
                    errors
                }
            }
        '''
        variables = {
            'input': {
                'title': 'Test Post',
                'content': 'This is a test post content.',
                'status': 'published'
            }
        }
        result = client.execute(mutation, variables=variables, context={'user': user})
        assert not result.get('errors')
        assert result['data']['createPost']['success'] is True
```

## 📚 Documentation Features

### API Documentation
- **GraphiQL Interface**: Interactive GraphQL explorer
- **Schema Documentation**: Auto-generated schema docs
- **Query Examples**: Comprehensive query examples
- **Mutation Examples**: Complete mutation examples

### Deployment Guides
- **Docker Deployment**: Complete Docker setup
- **Kubernetes Deployment**: K8s manifests and guides
- **Cloud Deployment**: AWS, GCP, Azure guides
- **CI/CD Setup**: GitHub Actions workflows

## 🔧 Customization Options

### Adding New Apps
```bash
# Create new app
python manage.py startapp myapp apps/myapp

# Add to INSTALLED_APPS in settings
# Configure GraphQL models with decorators
# Add to RAIL_DJANGO_GRAPHQL models list
```

### Custom GraphQL Types
```python
# apps/myapp/graphql_types.py
import graphene
from rail_django_graphql.types import DjangoObjectType
from .models import MyModel

class MyModelType(DjangoObjectType):
    custom_field = graphene.String()

    class Meta:
        model = MyModel
        fields = '__all__'

    def resolve_custom_field(self, info):
        return f"Custom value for {self.name}"
```

### Custom Permissions
```python
# apps/core/permissions.py
from rail_django_graphql.permissions import BasePermission

class IsOwnerOrReadOnly(BasePermission):
    """
    Permission qui permet seulement aux propriétaires d'un objet de le modifier.
    """
    
    def has_permission(self, info, **kwargs):
        return info.context.user.is_authenticated
    
    def has_object_permission(self, info, obj, **kwargs):
        if info.operation.operation == 'query':
            return True
        return obj.owner == info.context.user
```

---

This boilerplate structure provides a comprehensive, production-ready Django project that showcases all the capabilities of the `rail-django-graphql` library while following Django best practices and modern development patterns.