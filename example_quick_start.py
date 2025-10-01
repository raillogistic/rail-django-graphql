"""
Quick Start Example: Minimal Setup for Auto-Generated GraphQL Schema

This example shows the absolute minimum configuration needed to get 
auto-generated GraphQL schema working in your Django project.
"""

# =============================================================================
# STEP 1: MINIMAL DJANGO SETTINGS
# =============================================================================

"""
# settings.py - Add these to your existing Django settings

INSTALLED_APPS = [
    # ... your existing apps ...
    'graphene_django',
    'rail_django_graphql',  # Add this line
    'your_app',             # Your app with models
]

# Add GraphQL configuration
GRAPHQL_AUTO_GEN = {
    'ENABLE_MUTATIONS': True,
    'ENABLE_INTROSPECTION': True,
    'ENABLE_GRAPHIQL': True,
}

# Optional: Configure Graphene (if you want to extend the schema)
GRAPHENE = {
    'SCHEMA': 'your_project.schema.schema'
}
"""


# =============================================================================
# STEP 2: ADD URLS
# =============================================================================

"""
# urls.py - Add GraphQL endpoint to your main URLs

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', include('rail_django_graphql.urls')),  # Add this line
]
"""


# =============================================================================
# STEP 3: CREATE MODELS WITH DECORATORS
# =============================================================================

"""
# your_app/models.py - Example models with auto-generation decorators

from django.db import models
from rail_django_graphql.decorators import mutation, business_logic


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
    
    def __str__(self):
        return self.name
    
    @mutation()
    def activate_category(self):
        '''Activer cette catégorie.'''
        self.is_active = True
        self.save()
        return {"success": True, "message": "Catégorie activée"}
    
    @business_logic()
    def get_post_count(self):
        '''Obtenir le nombre de posts dans cette catégorie.'''
        return self.posts.count()


class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="Titre")
    content = models.TextField(verbose_name="Contenu")
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='posts',
        verbose_name="Catégorie"
    )
    is_published = models.BooleanField(default=False, verbose_name="Publié")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @mutation()
    def publish_post(self, publish_notes=None):
        '''Publier cet article.'''
        from django.utils import timezone
        
        self.is_published = True
        self.published_at = timezone.now()
        self.save()
        
        return {
            "success": True,
            "message": f"Article '{self.title}' publié",
            "published_at": self.published_at.isoformat()
        }
    
    @business_logic()
    def get_word_count(self):
        '''Obtenir le nombre de mots dans le contenu.'''
        return len(self.content.split()) if self.content else 0
"""


# =============================================================================
# STEP 4: RUN MIGRATIONS
# =============================================================================

"""
# Terminal commands to set up the database

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Optional: create admin user
"""


# =============================================================================
# STEP 5: START THE SERVER AND TEST
# =============================================================================

"""
# Terminal command to start the development server

python manage.py runserver

# Then visit: http://localhost:8000/graphql/
# You'll see GraphiQL interface where you can test queries
"""


# =============================================================================
# STEP 6: EXAMPLE QUERIES TO TEST
# =============================================================================

# Copy these queries into GraphiQL to test your setup

EXAMPLE_QUERIES = """
# Query 1: Get all categories
query GetAllCategories {
  allCategories {
    edges {
      node {
        id
        name
        description
        isActive
        createdAt
        postCount  # This comes from the @business_logic decorator
      }
    }
  }
}

# Query 2: Get all posts with category information
query GetAllPosts {
  allPosts {
    edges {
      node {
        id
        title
        content
        isPublished
        createdAt
        wordCount  # This comes from the @business_logic decorator
        category {
          name
          description
        }
      }
    }
  }
}

# Query 3: Get a specific post by ID
query GetPost($id: ID!) {
  post(id: $id) {
    id
    title
    content
    isPublished
    category {
      name
    }
  }
}

# Query 4: Paginated posts
query GetPostsPaginated($first: Int, $after: String) {
  allPosts(first: $first, after: $after) {
    edges {
      node {
        id
        title
        isPublished
      }
    }
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
  }
}
"""

EXAMPLE_MUTATIONS = """
# Mutation 1: Create a new category
mutation CreateCategory {
  createCategory(input: {
    name: "Technology"
    description: "Tech-related posts"
    isActive: true
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

# Mutation 2: Create a new post
mutation CreatePost($categoryId: ID!) {
  createPost(input: {
    title: "My First Post"
    content: "This is the content of my first post."
    categoryId: $categoryId
    isPublished: false
  }) {
    post {
      id
      title
      content
      category {
        name
      }
    }
    success
    errors
  }
}

# Mutation 3: Update a post
mutation UpdatePost($id: ID!) {
  updatePost(id: $id, input: {
    title: "Updated Post Title"
    isPublished: true
  }) {
    post {
      id
      title
      isPublished
    }
    success
    errors
  }
}

# Mutation 4: Use custom model method (from @mutation decorator)
mutation PublishPost($id: ID!) {
  publishPost(id: $id, publishNotes: "Ready for publication") {
    success
    result
    errors
  }
}

# Mutation 5: Activate category (from @mutation decorator)
mutation ActivateCategory($id: ID!) {
  activateCategory(id: $id) {
    success
    result
    errors
  }
}

# Mutation 6: Delete a post
mutation DeletePost($id: ID!) {
  deletePost(id: $id) {
    success
    errors
  }
}
"""


# =============================================================================
# STEP 7: OPTIONAL SCHEMA CUSTOMIZATION
# =============================================================================

"""
# your_project/schema.py - Optional: Extend the auto-generated schema

import graphene
from rail_django_graphql.core.schema import get_auto_schema


class CustomQuery(graphene.ObjectType):
    hello = graphene.String(name=graphene.String(default_value="World"))
    
    def resolve_hello(self, info, name):
        return f"Hello {name}!"


# Get the auto-generated schema
auto_schema = get_auto_schema()

# Extend it with custom queries
class Query(auto_schema.Query, CustomQuery):
    pass

# Create the final schema
schema = graphene.Schema(
    query=Query,
    mutation=auto_schema.Mutation
)
"""


# =============================================================================
# STEP 8: FRONTEND INTEGRATION EXAMPLE
# =============================================================================

"""
# JavaScript example for frontend integration

// Using fetch API
async function queryGraphQL(query, variables = {}) {
    const response = await fetch('http://localhost:8000/graphql/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(), // Get CSRF token from cookie
        },
        body: JSON.stringify({
            query: query,
            variables: variables
        })
    });
    
    return await response.json();
}

// Example usage
const query = `
    query {
        allPosts {
            edges {
                node {
                    title
                    category {
                        name
                    }
                }
            }
        }
    }
`;

queryGraphQL(query).then(result => {
    console.log('Posts:', result.data.allPosts.edges);
});

// Create a new post
const createMutation = `
    mutation CreatePost($input: PostInput!) {
        createPost(input: $input) {
            post {
                id
                title
            }
            success
            errors
        }
    }
`;

const variables = {
    input: {
        title: "New Post from Frontend",
        content: "This post was created from the frontend",
        categoryId: "1",
        isPublished: true
    }
};

queryGraphQL(createMutation, variables).then(result => {
    if (result.data.createPost.success) {
        console.log('Post created:', result.data.createPost.post);
    } else {
        console.error('Errors:', result.data.createPost.errors);
    }
});
"""


# =============================================================================
# TROUBLESHOOTING TIPS
# =============================================================================

TROUBLESHOOTING_TIPS = """
Common Issues and Solutions:

1. "No module named 'rail_django_graphql'"
   → Make sure you've installed the package: pip install rail-django-graphql

2. "GraphQL endpoint not found"
   → Check that you've added 'rail_django_graphql.urls' to your main urls.py

3. "No schema found"
   → Ensure your models are in an app listed in INSTALLED_APPS
   → Check that your models have proper decorators (@mutation, @business_logic)

4. "CSRF token missing"
   → For frontend integration, make sure to include CSRF token in requests
   → Or disable CSRF for GraphQL endpoint (not recommended for production)

5. "Permission denied"
   → Check your authentication settings in GRAPHQL_AUTO_GEN configuration
   → Make sure the user has proper permissions for the models

6. "Introspection disabled"
   → Set ENABLE_INTROSPECTION: True in GRAPHQL_AUTO_GEN settings

7. "GraphiQL not loading"
   → Set ENABLE_GRAPHIQL: True in GRAPHQL_AUTO_GEN settings
   → Check that DEBUG=True in development

8. "Mutations not working"
   → Set ENABLE_MUTATIONS: True in GRAPHQL_AUTO_GEN settings
   → Check that your model methods have @mutation() decorator (with parentheses)

9. "Custom fields not showing"
   → Make sure @business_logic() decorator is used (with parentheses)
   → Check that the method returns a serializable value

10. "Database errors"
    → Run: python manage.py makemigrations && python manage.py migrate
    → Check your database connection settings
"""


if __name__ == "__main__":
    print("🚀 Quick Start Guide for Auto-Generated GraphQL Schema")
    print("=" * 60)
    print("\n📋 Steps to get started:")
    print("1. Add 'rail_django_graphql' to INSTALLED_APPS")
    print("2. Add GraphQL URL to your urls.py")
    print("3. Create models with @mutation and @business_logic decorators")
    print("4. Run migrations")
    print("5. Start server and visit http://localhost:8000/graphql/")
    print("\n✅ Copy the code sections above to your Django project!")
    print("\n🔧 Need help? Check the troubleshooting section at the bottom.")