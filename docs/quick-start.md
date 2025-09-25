# 🚀 Quick Start Guide

Get up and running with the Django GraphQL Auto-Generation Library in just a few minutes!

## Prerequisites

- Python 3.8+
- Django 3.2+
- Basic knowledge of Django and GraphQL

## 1. Installation

```bash
pip install django-graphql-auto
```

## 2. Django Configuration

Add to your `settings.py`:

```python
INSTALLED_APPS = [
    # ... your other apps
    'graphene_django',
    'django_graphql_auto',
    'corsheaders',  # For frontend integration
]

# GraphQL Configuration
GRAPHENE = {
    'SCHEMA': 'django_graphql_auto.schema.schema'
}

# Auto-generation settings
DJANGO_GRAPHQL_AUTO = {
    'APPS': ['your_app'],  # Apps to generate schema for
    'AUTO_GENERATE': True,
    'ENABLE_FILTERING': True,
    'ENABLE_PAGINATION': True,
}

# CORS (for frontend integration)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React default
    "http://127.0.0.1:3000",
]
```

## 3. URL Configuration

Add to your main `urls.py`:

```python
from django.urls import path, include
from graphene_django.views import GraphQLView

urlpatterns = [
    # ... your other URLs
    path('graphql/', GraphQLView.as_view(graphiql=True)),
]
```

## 4. Create Your Models

```python
# models.py
from django.db import models

class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='posts')
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
```

## 5. Generate Schema

```bash
python manage.py migrate
python manage.py generate_graphql_schema
```

## 6. Test Your API

Start the development server:

```bash
python manage.py runserver
```

Visit `http://localhost:8000/graphql/` and try these queries:

### Query All Authors
```graphql
query {
  authors {
    edges {
      node {
        id
        name
        email
        posts {
          edges {
            node {
              title
              published
            }
          }
        }
      }
    }
  }
}
```

### Create a New Author
```graphql
mutation {
  createAuthor(input: {
    name: "John Doe"
    email: "john@example.com"
    bio: "A passionate writer"
  }) {
    author {
      id
      name
      email
    }
    success
    errors
  }
}
```

### Create a Post
```graphql
mutation {
  createPost(input: {
    title: "My First Post"
    content: "This is the content of my first post"
    authorId: "1"  # Use the ID from the author you created
    published: true
  }) {
    post {
      id
      title
      author {
        name
      }
    }
    success
    errors
  }
}
```

### Query with Filtering
```graphql
query {
  posts(published: true, title_Icontains: "first") {
    edges {
      node {
        title
        content
        author {
          name
        }
        createdAt
      }
    }
  }
}
```

## 🎉 That's It!

You now have a fully functional GraphQL API with:
- ✅ Automatic schema generation
- ✅ CRUD operations for all models
- ✅ Relationship handling
- ✅ Filtering and pagination
- ✅ GraphiQL interface for testing

## Next Steps

1. **[📖 Read the Full Documentation](index.md)** - Learn about all features
2. **[⚡ Explore Advanced Features](advanced/)** - Custom scalars, inheritance, nested operations
3. **[💡 Check Out Examples](examples/)** - Real-world usage patterns
4. **[🔧 Optimize Performance](development/performance.md)** - Best practices for production

## Common Issues

### Schema Not Generating?
- Make sure your app is in `DJANGO_GRAPHQL_AUTO['APPS']`
- Run `python manage.py generate_graphql_schema` after model changes
- Check the console for any error messages

### CORS Issues?
- Add your frontend URL to `CORS_ALLOWED_ORIGINS`
- Install `django-cors-headers` if not already installed

### GraphiQL Not Loading?
- Ensure `graphiql=True` in your GraphQLView
- Check that you're accessing the correct URL (`/graphql/`)

## Need Help?

- 📚 [Full Documentation](index.md)
- 🛠️ [Troubleshooting Guide](development/troubleshooting.md)
- 💬 [Contributing Guide](CONTRIBUTING.md)

---

**Happy coding!** 🚀