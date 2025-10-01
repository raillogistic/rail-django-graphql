"""
Django Integration Example: Complete Setup for Auto-Generated GraphQL Schema

This example shows how to integrate the auto-generated GraphQL schema into a 
complete Django project with proper URL configuration, views, and settings.
"""

# =============================================================================
# 1. DJANGO SETTINGS CONFIGURATION
# =============================================================================

"""
# settings.py - Complete configuration example

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Django settings
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
    
    # Your apps
    'rail_django_graphql',  # The GraphQL auto-generation library
    'test_app',             # Your app with models
]

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

ROOT_URLCONF = 'myproject.urls'

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# GraphQL Auto-Generation Configuration
GRAPHQL_AUTO_GEN = {
    # Schema generation settings
    'SCHEMA_CONFIG': {
        'auto_generate_schema': True,
        'schema_name': 'auto_schema',
        'schema_description': 'Auto-generated GraphQL schema',
        'schema_version': '1.0.0',
    },
    
    # Apps and models to include/exclude
    'APPS_TO_INCLUDE': ['test_app'],  # Only include specific apps
    'APPS_TO_EXCLUDE': ['admin', 'auth', 'contenttypes', 'sessions'],
    'MODELS_TO_EXCLUDE': ['LogEntry', 'Session'],
    
    # Feature toggles
    'ENABLE_MUTATIONS': True,
    'ENABLE_SUBSCRIPTIONS': False,
    'ENABLE_FILTERS': True,
    'ENABLE_NESTED_OPERATIONS': True,
    'ENABLE_FILE_UPLOADS': True,
    
    # Query settings
    'QUERY_SETTINGS': {
        'enable_single_queries': True,
        'enable_list_queries': True,
        'enable_pagination': True,
        'enable_filtering': True,
        'enable_ordering': True,
        'default_page_size': 20,
        'max_page_size': 100,
    },
    
    # Mutation settings
    'MUTATION_SETTINGS': {
        'generate_create': True,
        'generate_update': True,
        'generate_delete': True,
        'enable_bulk_operations': True,
        'enable_nested_relations': True,
        'enable_method_mutations': True,
    },
    
    # Type generation settings
    'TYPE_SETTINGS': {
        'include_pk_field': True,
        'include_computed_fields': True,
        'auto_camelcase_fields': False,
        'include_meta_fields': True,
    },
    
    # Schema registry settings
    'SCHEMA_REGISTRY': {
        'use_registry': True,
        'auto_register_schemas': True,
        'default_schema': 'main',
    },
    
    # Development settings
    'ENABLE_INTROSPECTION': True,
    'ENABLE_GRAPHIQL': True,
    'DEBUG_MODE': True,
    'VERBOSE_ERRORS': True,
    
    # Security settings
    'AUTHENTICATION': {
        'authentication_required': False,  # Set to True for production
        'authentication_classes': [
            'rest_framework.authentication.SessionAuthentication',
            'rest_framework.authentication.TokenAuthentication',
        ],
        'permission_classes': ['rest_framework.permissions.AllowAny'],
    },
    
    # Performance settings
    'PERFORMANCE': {
        'enable_query_optimization': True,
        'enable_dataloader': True,
        'max_query_depth': 10,
        'query_timeout': 30,
    },
}

# Graphene Django settings (if using graphene-django)
GRAPHENE = {
    'SCHEMA': 'myproject.schema.schema',  # Point to your schema
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

# CORS settings for frontend integration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React dev server
    "http://127.0.0.1:3000",
    "http://localhost:8080",  # Vue dev server
]

CORS_ALLOW_CREDENTIALS = True
"""


# =============================================================================
# 2. URL CONFIGURATION
# =============================================================================

"""
# urls.py - Main project URLs

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # GraphQL endpoints
    path('graphql/', include('rail_django_graphql.urls')),
    
    # Alternative: Custom GraphQL endpoint
    # path('api/graphql/', include('myproject.graphql_urls')),
    
    # API documentation
    path('api/docs/', include('rail_django_graphql.docs.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
"""


# =============================================================================
# 3. CUSTOM SCHEMA CONFIGURATION
# =============================================================================

"""
# myproject/schema.py - Custom schema setup

import graphene
from rail_django_graphql.core.schema import SchemaBuilder
from rail_django_graphql.core.settings import (
    SchemaSettings, 
    MutationGeneratorSettings,
    QueryGeneratorSettings
)
from rail_django_graphql.core.registry import get_schema_registry


class CustomQuery(graphene.ObjectType):
    '''Custom queries that extend the auto-generated schema.'''
    
    hello = graphene.String(name=graphene.String(default_value="World"))
    
    def resolve_hello(self, info, name):
        return f"Hello {name}!"
    
    # Custom business logic queries
    popular_posts = graphene.List('test_app.schema.PostType')
    
    def resolve_popular_posts(self, info):
        from test_app.models import Post
        return Post.objects.filter(is_published=True).order_by('-view_count')[:10]


class CustomMutation(graphene.ObjectType):
    '''Custom mutations that extend the auto-generated schema.'''
    
    # Custom business logic mutations
    publish_multiple_posts = graphene.Field(
        'rail_django_graphql.types.BulkOperationResult',
        post_ids=graphene.List(graphene.ID, required=True)
    )
    
    def resolve_publish_multiple_posts(self, info, post_ids):
        from test_app.models import Post
        from django.utils import timezone
        
        posts = Post.objects.filter(id__in=post_ids)
        updated_count = posts.update(
            is_published=True,
            published_at=timezone.now()
        )
        
        return {
            'success': True,
            'count': updated_count,
            'message': f'Published {updated_count} posts'
        }


def create_auto_schema():
    '''Create the auto-generated schema with custom extensions.'''
    
    # Configure auto-generation settings
    schema_settings = SchemaSettings(
        excluded_apps=['admin', 'auth', 'contenttypes', 'sessions'],
        enable_introspection=True,
        enable_graphiql=True,
    )
    
    mutation_settings = MutationGeneratorSettings(
        generate_create=True,
        generate_update=True,
        generate_delete=True,
        enable_method_mutations=True,
    )
    
    query_settings = QueryGeneratorSettings(
        enable_pagination=True,
        enable_filtering=True,
        default_page_size=20,
    )
    
    # Build the auto-generated schema
    schema_builder = SchemaBuilder(
        schema_settings=schema_settings,
        mutation_settings=mutation_settings,
        query_settings=query_settings
    )
    
    auto_schema = schema_builder.get_schema()
    
    # Extend with custom queries and mutations
    class ExtendedQuery(schema_builder.query_class, CustomQuery):
        pass
    
    class ExtendedMutation(schema_builder.mutation_class, CustomMutation):
        pass
    
    # Create the final schema
    schema = graphene.Schema(
        query=ExtendedQuery,
        mutation=ExtendedMutation
    )
    
    return schema


# Create the main schema
schema = create_auto_schema()
"""


# =============================================================================
# 4. CUSTOM GRAPHQL URLS (Alternative approach)
# =============================================================================

"""
# myproject/graphql_urls.py - Custom GraphQL URL configuration

from django.urls import path
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .schema import schema
from rail_django_graphql.views import (
    AutoGraphQLView,
    SchemaRegistryView,
    GraphQLPlaygroundView
)


# Custom GraphQL view with authentication
class AuthenticatedGraphQLView(GraphQLView):
    '''GraphQL view that requires authentication.'''
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


urlpatterns = [
    # Main GraphQL endpoint
    path('', csrf_exempt(GraphQLView.as_view(
        graphiql=True,
        schema=schema
    )), name='graphql'),
    
    # Auto-generated schema endpoint
    path('auto/', csrf_exempt(AutoGraphQLView.as_view()), name='auto_graphql'),
    
    # Authenticated endpoint
    path('private/', csrf_exempt(AuthenticatedGraphQLView.as_view(
        graphiql=True,
        schema=schema
    )), name='private_graphql'),
    
    # Schema registry management
    path('registry/', SchemaRegistryView.as_view(), name='schema_registry'),
    
    # GraphQL Playground (alternative to GraphiQL)
    path('playground/', GraphQLPlaygroundView.as_view(), name='graphql_playground'),
    
    # Schema introspection endpoint
    path('schema/', csrf_exempt(GraphQLView.as_view(
        graphiql=False,
        schema=schema
    )), name='graphql_schema'),
]
"""


# =============================================================================
# 5. DJANGO MANAGEMENT COMMAND
# =============================================================================

"""
# management/commands/generate_graphql_schema.py - Custom management command

from django.core.management.base import BaseCommand
from django.conf import settings
from rail_django_graphql.core.schema import SchemaBuilder
from rail_django_graphql.core.settings import SchemaSettings
import json


class Command(BaseCommand):
    help = 'Generate GraphQL schema file from Django models'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='schema.graphql',
            help='Output file path for the schema'
        )
        parser.add_argument(
            '--format',
            choices=['graphql', 'json'],
            default='graphql',
            help='Output format (graphql or json)'
        )
        parser.add_argument(
            '--apps',
            nargs='+',
            help='Specific apps to include'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Generating GraphQL schema...')
        
        # Configure schema settings
        schema_settings = SchemaSettings(
            excluded_apps=['admin', 'auth', 'contenttypes', 'sessions'],
        )
        
        if options['apps']:
            # Include only specified apps
            schema_settings.excluded_apps = []
            # Add logic to include only specified apps
        
        # Build schema
        schema_builder = SchemaBuilder(schema_settings)
        schema = schema_builder.get_schema()
        
        # Generate schema string
        if options['format'] == 'graphql':
            from graphql import print_schema
            schema_str = print_schema(schema)
        else:
            from graphql import build_client_schema, get_introspection_query
            introspection = schema.execute(get_introspection_query())
            schema_str = json.dumps(introspection.data, indent=2)
        
        # Write to file
        output_path = options['output']
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(schema_str)
        
        self.stdout.write(
            self.style.SUCCESS(f'Schema generated successfully: {output_path}')
        )
        
        # Show statistics
        type_map = schema.type_map
        types_count = len([t for t in type_map.values() if not t.name.startswith('__')])
        
        self.stdout.write(f'Generated {types_count} types')
        self.stdout.write('Schema generation completed!')
"""


# =============================================================================
# 6. FRONTEND INTEGRATION EXAMPLE
# =============================================================================

"""
# Frontend integration examples

# JavaScript/React with Apollo Client
const client = new ApolloClient({
    uri: 'http://localhost:8000/graphql/',
    cache: new InMemoryCache(),
    headers: {
        'X-CSRFToken': getCsrfToken(),
    }
});

// Example query
const GET_POSTS = gql`
    query GetPosts($first: Int, $after: String) {
        allPosts(first: $first, after: $after) {
            edges {
                node {
                    id
                    title
                    content
                    isPublished
                    createdAt
                    category {
                        name
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
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
`;

// Example mutation
const CREATE_POST = gql`
    mutation CreatePost($input: PostInput!) {
        createPost(input: $input) {
            post {
                id
                title
                content
            }
            success
            errors
        }
    }
`;

# Python client example
import requests

def query_graphql(query, variables=None):
    response = requests.post(
        'http://localhost:8000/graphql/',
        json={
            'query': query,
            'variables': variables or {}
        },
        headers={
            'Content-Type': 'application/json',
            'X-CSRFToken': get_csrf_token(),
        }
    )
    return response.json()

# Query posts
posts_query = '''
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
'''

result = query_graphql(posts_query)
posts = result['data']['allPosts']['edges']
"""


# =============================================================================
# 7. TESTING CONFIGURATION
# =============================================================================

"""
# tests/test_graphql_integration.py - Integration tests

import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from test_app.models import Category, Post, Tag


class GraphQLIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test data
        self.category = Category.objects.create(
            name='Test Category',
            description='Test description'
        )
        
        self.post = Post.objects.create(
            title='Test Post',
            content='Test content',
            category=self.category,
            is_published=True
        )
    
    def execute_query(self, query, variables=None):
        '''Helper method to execute GraphQL queries.'''
        response = self.client.post(
            '/graphql/',
            data={
                'query': query,
                'variables': json.dumps(variables or {})
            },
            content_type='application/json'
        )
        return response.json()
    
    def test_query_posts(self):
        '''Test querying posts.'''
        query = '''
            query {
                allPosts {
                    edges {
                        node {
                            title
                            content
                            isPublished
                            category {
                                name
                            }
                        }
                    }
                }
            }
        '''
        
        result = self.execute_query(query)
        
        self.assertIsNone(result.get('errors'))
        posts = result['data']['allPosts']['edges']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]['node']['title'], 'Test Post')
    
    def test_create_category_mutation(self):
        '''Test creating a category via mutation.'''
        mutation = '''
            mutation CreateCategory($input: CategoryInput!) {
                createCategory(input: $input) {
                    category {
                        id
                        name
                        description
                    }
                    success
                    errors
                }
            }
        '''
        
        variables = {
            'input': {
                'name': 'New Category',
                'description': 'New category description',
                'isActive': True
            }
        }
        
        result = self.execute_query(mutation, variables)
        
        self.assertIsNone(result.get('errors'))
        create_result = result['data']['createCategory']
        self.assertTrue(create_result['success'])
        self.assertEqual(create_result['category']['name'], 'New Category')
    
    def test_custom_method_mutation(self):
        '''Test custom model method mutation.'''
        mutation = '''
            mutation PublishPost($id: ID!, $publishNotes: String) {
                publishPost(id: $id, publishNotes: $publishNotes) {
                    success
                    result
                    errors
                }
            }
        '''
        
        variables = {
            'id': str(self.post.id),
            'publishNotes': 'Ready for publication'
        }
        
        result = self.execute_query(mutation, variables)
        
        self.assertIsNone(result.get('errors'))
        publish_result = result['data']['publishPost']
        self.assertTrue(publish_result['success'])
"""


if __name__ == "__main__":
    print("Django GraphQL Integration Example")
    print("=" * 50)
    print("\nThis file contains complete examples for:")
    print("✅ Django settings configuration")
    print("✅ URL routing setup")
    print("✅ Custom schema creation")
    print("✅ Management commands")
    print("✅ Frontend integration")
    print("✅ Testing configuration")
    print("\nCopy the relevant sections to your Django project!")