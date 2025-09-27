# Quick Start Guide

Get your Django GraphQL API up and running in minutes with the Django GraphQL Auto-Generation Library.

## 🚀 5-Minute Setup

### Step 1: Install the Library

```bash
pip install django-graphql-auto
```

### Step 2: Add to Django Settings

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
    'django_graphql_auto',  # Add this line
    
    # Your apps
    'myapp',
]

# GraphQL Auto-Generation Configuration
DJANGO_GRAPHQL_AUTO = {
    'MODELS': [
        'myapp.models.Post',
        'myapp.models.Category',
        'myapp.models.Author',
    ],
    'ENABLE_MUTATIONS': True,
    'ENABLE_FILTERS': True,
    'ENABLE_PAGINATION': True,
}

# Graphene Django Configuration
GRAPHENE = {
    'SCHEMA': 'django_graphql_auto.schema.schema'
}
```

### Step 3: Add URL Configuration

```python
# urls.py
from django.contrib import admin
from django.urls import path
from graphene_django.views import GraphQLView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', GraphQLView.as_view(graphiql=True)),
]
```

### Step 4: Create Your Models

```python
# myapp/models.py
from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField("Nom de la catégorie", max_length=100)
    description = models.TextField("Description", blank=True)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
    
    def __str__(self):
        return self.name

class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField("Biographie", blank=True)
    website = models.URLField("Site web", blank=True)
    
    class Meta:
        verbose_name = "Auteur"
        verbose_name_plural = "Auteurs"
    
    def __str__(self):
        return self.user.username

class Post(models.Model):
    title = models.CharField("Titre", max_length=200)
    content = models.TextField("Contenu")
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name="Auteur")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Catégorie")
    tags = models.ManyToManyField('Tag', blank=True, verbose_name="Tags")
    published = models.BooleanField("Publié", default=False)
    created_at = models.DateTimeField("Date de création", auto_now_add=True)
    updated_at = models.DateTimeField("Date de modification", auto_now=True)
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class Tag(models.Model):
    name = models.CharField("Nom du tag", max_length=50, unique=True)
    color = models.CharField("Couleur", max_length=7, default="#007bff")
    
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
    
    def __str__(self):
        return self.name
```

### Step 5: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Sample Data (Optional)

```python
# Create a management command: myapp/management/commands/create_sample_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Category, Author, Post, Tag

class Command(BaseCommand):
    help = 'Create sample data for testing'
    
    def handle(self, *args, **options):
        # Create categories
        tech_category = Category.objects.create(
            name="Technologie",
            description="Articles sur la technologie et l'innovation"
        )
        
        lifestyle_category = Category.objects.create(
            name="Style de vie",
            description="Articles sur le style de vie et les loisirs"
        )
        
        # Create tags
        python_tag = Tag.objects.create(name="Python", color="#3776ab")
        django_tag = Tag.objects.create(name="Django", color="#092e20")
        graphql_tag = Tag.objects.create(name="GraphQL", color="#e10098")
        
        # Create user and author
        user = User.objects.create_user(
            username='john_doe',
            email='john@example.com',
            first_name='John',
            last_name='Doe'
        )
        
        author = Author.objects.create(
            user=user,
            bio="Développeur passionné par les technologies web modernes.",
            website="https://johndoe.dev"
        )
        
        # Create posts
        post1 = Post.objects.create(
            title="Introduction à GraphQL avec Django",
            content="GraphQL est une technologie révolutionnaire...",
            author=author,
            category=tech_category,
            published=True
        )
        post1.tags.add(python_tag, django_tag, graphql_tag)
        
        post2 = Post.objects.create(
            title="Les meilleures pratiques Django en 2024",
            content="Django continue d'évoluer avec de nouvelles fonctionnalités...",
            author=author,
            category=tech_category,
            published=True
        )
        post2.tags.add(python_tag, django_tag)
        
        self.stdout.write(
            self.style.SUCCESS('Sample data created successfully!')
        )
```

Run the command:
```bash
python manage.py create_sample_data
```

### Step 7: Start the Server

```bash
python manage.py runserver
```

## 🎯 Test Your GraphQL API

Visit `http://localhost:8000/graphql/` to access GraphiQL interface.

### Basic Queries

#### 1. Get All Posts
```graphql
query {
  posts {
    edges {
      node {
        id
        title
        content
        published
        createdAt
        author {
          user {
            username
            firstName
            lastName
          }
          bio
        }
        category {
          name
          description
        }
        tags {
          edges {
            node {
              name
              color
            }
          }
        }
      }
    }
  }
}
```

#### 2. Get Single Post
```graphql
query {
  post(id: "1") {
    id
    title
    content
    author {
      user {
        username
      }
    }
    category {
      name
    }
  }
}
```

#### 3. Filter Posts by Category
```graphql
query {
  posts(category: "1") {
    edges {
      node {
        id
        title
        category {
          name
        }
      }
    }
  }
}
```

#### 4. Search Posts
```graphql
query {
  posts(title_Icontains: "GraphQL") {
    edges {
      node {
        id
        title
        content
      }
    }
  }
}
```

### Basic Mutations

#### 1. Create a New Category
```graphql
mutation {
  createCategory(input: {
    name: "Science"
    description: "Articles scientifiques et recherche"
  }) {
    category {
      id
      name
      description
    }
    success
    errors
  }
}
```

#### 2. Create a New Post
```graphql
mutation {
  createPost(input: {
    title: "Mon Premier Article GraphQL"
    content: "Ceci est le contenu de mon premier article créé via GraphQL..."
    authorId: 1
    categoryId: 1
    published: true
  }) {
    post {
      id
      title
      published
      createdAt
    }
    success
    errors
  }
}
```

#### 3. Update a Post
```graphql
mutation {
  updatePost(input: {
    id: 1
    title: "Titre Mis à Jour"
    published: true
  }) {
    post {
      id
      title
      updatedAt
    }
    success
    errors
  }
}
```

#### 4. Delete a Post
```graphql
mutation {
  deletePost(input: {
    id: 1
  }) {
    success
    errors
  }
}
```

## 🔧 Advanced Configuration

### Enable Authentication

```python
# settings.py
DJANGO_GRAPHQL_AUTO = {
    'MODELS': [
        'myapp.models.Post',
        'myapp.models.Category',
        'myapp.models.Author',
    ],
    'ENABLE_MUTATIONS': True,
    'ENABLE_FILTERS': True,
    'ENABLE_PAGINATION': True,
    'AUTHENTICATION': {
        'ENABLE': True,
        'REQUIRED_FOR_MUTATIONS': True,
        'LOGIN_REQUIRED_MODELS': ['myapp.models.Post'],
    },
}
```

### Add Permissions

```python
# myapp/models.py
class Post(models.Model):
    # ... existing fields ...
    
    class GraphQLMeta:
        permissions = {
            'create': ['myapp.add_post'],
            'update': ['myapp.change_post'],
            'delete': ['myapp.delete_post'],
        }
```

### Enable Caching

```python
# settings.py
DJANGO_GRAPHQL_AUTO = {
    # ... existing config ...
    'CACHING': {
        'ENABLE': True,
        'TIMEOUT': 300,  # 5 minutes
        'CACHE_QUERIES': True,
        'CACHE_MUTATIONS': False,
    },
}

# Add Redis cache backend
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Add Rate Limiting

```python
# settings.py
DJANGO_GRAPHQL_AUTO = {
    # ... existing config ...
    'RATE_LIMITING': {
        'ENABLE': True,
        'QUERIES_PER_MINUTE': 100,
        'MUTATIONS_PER_MINUTE': 20,
        'BURST_LIMIT': 10,
    },
}
```

## 📊 Monitoring and Debugging

### Enable Query Logging

```python
# settings.py
DJANGO_GRAPHQL_AUTO = {
    # ... existing config ...
    'LOGGING': {
        'ENABLE_QUERY_LOGGING': True,
        'ENABLE_PERFORMANCE_LOGGING': True,
        'LOG_SLOW_QUERIES': True,
        'SLOW_QUERY_THRESHOLD': 1.0,  # seconds
    },
}

# Configure Django logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'graphql.log',
        },
    },
    'loggers': {
        'django_graphql_auto': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Performance Monitoring Query

```graphql
query {
  __schema {
    queryType {
      fields {
        name
        type {
          name
        }
      }
    }
    mutationType {
      fields {
        name
        type {
          name
        }
      }
    }
  }
}
```

## 🚀 Next Steps

### 1. Explore Advanced Features
- **File Uploads**: [File Upload Guide](features/file-uploads-media.md)
- **Real-time Subscriptions**: [Subscription Guide](features/subscriptions.md)
- **Custom Extensions**: [Extension Development](development/developer-guide.md)

### 2. Production Deployment
- **Security Configuration**: [Security Guide](features/security.md)
- **Performance Optimization**: [Performance Guide](setup/performance.md)
- **Monitoring Setup**: [Monitoring Guide](setup/monitoring.md)

### 3. Integration Examples
- **React Frontend**: [React Integration](examples/react-integration.md)
- **Vue.js Frontend**: [Vue Integration](examples/vue-integration.md)
- **Mobile Apps**: [Mobile Integration](examples/mobile-integration.md)

### 4. Community Resources
- **GitHub Repository**: [Source Code](https://github.com/your-org/django-graphql-auto)
- **Documentation**: [Full Documentation](README.md)
- **Examples**: [Real-world Examples](examples/)
- **Support**: [Community Forum](https://github.com/your-org/django-graphql-auto/discussions)

## 🆘 Troubleshooting

### Common Issues

#### Schema Not Generated
```python
# Check if models are properly configured
python manage.py shell
>>> from django_graphql_auto.core.schema_generator import SchemaGenerator
>>> generator = SchemaGenerator(debug=True)
>>> schema = generator.generate_schema()
```

#### GraphiQL Not Loading
- Ensure `DEBUG = True` in development
- Check that `graphene_django` is installed
- Verify URL configuration

#### Permission Errors
```python
# Check user permissions
python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='your_username')
>>> user.user_permissions.all()
>>> user.groups.all()
```

#### Performance Issues
- Enable query optimization in settings
- Add database indexes for filtered fields
- Use pagination for large datasets
- Enable caching for frequently accessed data

### Getting Help

1. **Check the Documentation**: [Full Documentation](README.md)
2. **Search Issues**: [GitHub Issues](https://github.com/your-org/django-graphql-auto/issues)
3. **Ask Questions**: [Community Discussions](https://github.com/your-org/django-graphql-auto/discussions)
4. **Report Bugs**: [Bug Reports](https://github.com/your-org/django-graphql-auto/issues/new)

---

**Congratulations!** 🎉 You now have a fully functional GraphQL API generated automatically from your Django models. Start building amazing applications with the power of GraphQL and Django!