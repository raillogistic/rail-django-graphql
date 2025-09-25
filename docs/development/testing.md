# Testing Guide

This guide covers comprehensive testing strategies for the Django GraphQL Auto-Generation Library, including unit tests, integration tests, and GraphQL-specific testing patterns.

## 📚 Table of Contents

- [Overview](#overview)
- [Test Setup](#test-setup)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [GraphQL Testing](#graphql-testing)
- [Performance Testing](#performance-testing)
- [Test Data Management](#test-data-management)
- [Mocking and Fixtures](#mocking-and-fixtures)
- [Continuous Integration](#continuous-integration)
- [Best Practices](#best-practices)

## 🎯 Overview

Testing the Django GraphQL Auto-Generation Library involves several layers:

- **Unit Tests** - Test individual components and functions
- **Integration Tests** - Test component interactions
- **GraphQL Tests** - Test schema generation and query execution
- **Performance Tests** - Test query performance and optimization
- **End-to-End Tests** - Test complete workflows

## 🛠️ Test Setup

### Test Configuration

```python
# tests/settings.py
from django.conf import settings

# Test-specific settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Test-specific GraphQL settings
DJANGO_GRAPHQL_AUTO = {
    'TESTING': True,
    'CACHE_ENABLED': False,  # Disable caching in tests
    'PERFORMANCE_MONITORING': False,
    'DEFAULT_PAGE_SIZE': 5,  # Smaller page size for tests
}

# Use in-memory cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'graphene_django',
    'django_graphql_auto',
    'tests.test_app',  # Test application
]
```

### Test Models

```python
# tests/test_app/models.py
from django.db import models
from django.contrib.auth.models import User

class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class GraphQLMeta:
        filter_fields = {
            'name': ['exact', 'icontains'],
            'is_active': ['exact'],
            'created_at': ['gte', 'lte'],
        }
        ordering = ['name', '-created_at']

class Category(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "categories"

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='posts')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField('Tag', blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('draft', 'Draft'), ('published', 'Published')],
        default='draft'
    )
    view_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class GraphQLMeta:
        filter_fields = {
            'title': ['exact', 'icontains'],
            'status': ['exact', 'in'],
            'author': ['exact'],
            'category': ['exact'],
            'created_at': ['gte', 'lte', 'range'],
        }
        ordering = ['-created_at', 'title']

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#000000')  # Hex color
    
    def __str__(self):
        return self.name

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class GraphQLMeta:
        filter_fields = {
            'post': ['exact'],
            'author': ['exact'],
            'is_approved': ['exact'],
            'created_at': ['gte', 'lte'],
        }
```

### Test Base Classes

```python
# tests/base.py
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from graphene.test import Client
from django_graphql_auto.schema import build_schema
from tests.test_app.models import Author, Post, Category, Tag, Comment

class GraphQLTestCase(TestCase):
    """Base test case for GraphQL tests."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.schema = build_schema()
        cls.client = Client(cls.schema)
    
    def setUp(self):
        """Set up test data."""
        self.author = Author.objects.create(
            name="Test Author",
            email="test@example.com",
            bio="Test bio"
        )
        
        self.category = Category.objects.create(
            name="Test Category",
            description="Test description"
        )
        
        self.tag1 = Tag.objects.create(name="Python", color="#3776ab")
        self.tag2 = Tag.objects.create(name="Django", color="#092e20")
        
        self.post = Post.objects.create(
            title="Test Post",
            content="Test content",
            author=self.author,
            category=self.category,
            status="published"
        )
        self.post.tags.add(self.tag1, self.tag2)
        
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.author,
            content="Test comment",
            is_approved=True
        )
    
    def execute_query(self, query, variables=None, context=None):
        """Execute GraphQL query and return result."""
        return self.client.execute(query, variables=variables, context=context)
    
    def assertNoErrors(self, result):
        """Assert that GraphQL result has no errors."""
        if result.errors:
            self.fail(f"GraphQL errors: {[str(e) for e in result.errors]}")
    
    def assertHasErrors(self, result):
        """Assert that GraphQL result has errors."""
        self.assertTrue(result.errors, "Expected GraphQL errors but got none")

class PerformanceTestCase(TransactionTestCase):
    """Base test case for performance tests."""
    
    def setUp(self):
        self.schema = build_schema()
        self.client = Client(self.schema)
    
    def create_test_data(self, num_authors=10, num_posts_per_author=5):
        """Create test data for performance tests."""
        authors = []
        posts = []
        
        for i in range(num_authors):
            author = Author.objects.create(
                name=f"Author {i}",
                email=f"author{i}@example.com"
            )
            authors.append(author)
            
            for j in range(num_posts_per_author):
                post = Post.objects.create(
                    title=f"Post {i}-{j}",
                    content=f"Content for post {i}-{j}",
                    author=author,
                    status="published"
                )
                posts.append(post)
        
        return authors, posts
    
    def measure_query_performance(self, query, variables=None):
        """Measure query execution time and database queries."""
        from django.test.utils import override_settings
        from django.db import connection
        import time
        
        with override_settings(DEBUG=True):
            # Clear previous queries
            connection.queries_log.clear()
            
            # Measure execution time
            start_time = time.time()
            result = self.client.execute(query, variables=variables)
            execution_time = time.time() - start_time
            
            # Count database queries
            query_count = len(connection.queries)
            
            return {
                'result': result,
                'execution_time': execution_time,
                'query_count': query_count,
                'queries': connection.queries
            }
```

## 🧪 Unit Testing

### Testing Schema Generation

```python
# tests/test_schema_generation.py
from tests.base import GraphQLTestCase
from django_graphql_auto.introspection import ModelIntrospector
from django_graphql_auto.generators import TypeGenerator, QueryGenerator, MutationGenerator
from tests.test_app.models import Post, Author

class TestSchemaGeneration(GraphQLTestCase):
    """Test schema generation components."""
    
    def test_model_introspection(self):
        """Test model introspection."""
        introspector = ModelIntrospector()
        
        # Test field introspection
        fields = introspector.get_model_fields(Post)
        
        self.assertIn('title', fields)
        self.assertIn('content', fields)
        self.assertIn('author', fields)
        self.assertIn('created_at', fields)
        
        # Test relationship detection
        relationships = introspector.get_model_relationships(Post)
        
        self.assertIn('author', relationships)
        self.assertEqual(relationships['author']['type'], 'ForeignKey')
        self.assertEqual(relationships['author']['related_model'], Author)
    
    def test_type_generation(self):
        """Test GraphQL type generation."""
        generator = TypeGenerator()
        
        # Generate type for Post model
        post_type = generator.generate_type(Post)
        
        self.assertIsNotNone(post_type)
        self.assertEqual(post_type._meta.name, 'PostType')
        
        # Check fields
        fields = post_type._meta.fields
        self.assertIn('title', fields)
        self.assertIn('content', fields)
        self.assertIn('author', fields)
    
    def test_query_generation(self):
        """Test query generation."""
        generator = QueryGenerator()
        
        # Generate queries for Post model
        queries = generator.generate_queries(Post)
        
        self.assertIn('post', queries)
        self.assertIn('all_posts', queries)
        
        # Test query execution
        query = '''
            query {
                post(id: %d) {
                    id
                    title
                    author {
                        name
                    }
                }
            }
        ''' % self.post.id
        
        result = self.execute_query(query)
        self.assertNoErrors(result)
        self.assertEqual(result.data['post']['title'], self.post.title)
    
    def test_mutation_generation(self):
        """Test mutation generation."""
        generator = MutationGenerator()
        
        # Generate mutations for Post model
        mutations = generator.generate_mutations(Post)
        
        self.assertIn('create_post', mutations)
        self.assertIn('update_post', mutations)
        self.assertIn('delete_post', mutations)
    
    def test_filter_generation(self):
        """Test filter generation."""
        from django_graphql_auto.filters import FilterGenerator
        
        generator = FilterGenerator()
        filter_class = generator.generate_filter(Post)
        
        self.assertIsNotNone(filter_class)
        
        # Test filter fields
        filter_fields = filter_class._meta.fields
        self.assertIn('title', filter_fields)
        self.assertIn('status', filter_fields)
        self.assertIn('author', filter_fields)

class TestCustomScalars(GraphQLTestCase):
    """Test custom scalar handling."""
    
    def test_datetime_scalar(self):
        """Test DateTime scalar."""
        query = '''
            query {
                post(id: %d) {
                    createdAt
                }
            }
        ''' % self.post.id
        
        result = self.execute_query(query)
        self.assertNoErrors(result)
        self.assertIsNotNone(result.data['post']['createdAt'])
    
    def test_json_scalar(self):
        """Test JSON scalar with model method."""
        # Add a method that returns JSON to Post model
        def get_metadata(self):
            return {
                'view_count': self.view_count,
                'tags': [tag.name for tag in self.tags.all()],
                'status': self.status
            }
        
        Post.get_metadata = get_metadata
        
        # Regenerate schema to include new method
        self.schema = build_schema()
        self.client = Client(self.schema)
        
        query = '''
            query {
                post(id: %d) {
                    metadata
                }
            }
        ''' % self.post.id
        
        result = self.execute_query(query)
        self.assertNoErrors(result)
        
        metadata = result.data['post']['metadata']
        self.assertIsInstance(metadata, dict)
        self.assertIn('view_count', metadata)
        self.assertIn('tags', metadata)
```

### Testing Filters and Pagination

```python
# tests/test_filters.py
from tests.base import GraphQLTestCase
from tests.test_app.models import Post, Author

class TestFiltering(GraphQLTestCase):
    """Test filtering functionality."""
    
    def setUp(self):
        super().setUp()
        
        # Create additional test data
        self.author2 = Author.objects.create(
            name="Second Author",
            email="second@example.com"
        )
        
        self.post2 = Post.objects.create(
            title="Second Post",
            content="Second content",
            author=self.author2,
            status="draft"
        )
    
    def test_exact_filter(self):
        """Test exact field filtering."""
        query = '''
            query {
                allPosts(filters: {status: "published"}) {
                    edges {
                        node {
                            id
                            title
                            status
                        }
                    }
                }
            }
        '''
        
        result = self.execute_query(query)
        self.assertNoErrors(result)
        
        posts = result.data['allPosts']['edges']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]['node']['status'], 'published')
    
    def test_icontains_filter(self):
        """Test case-insensitive contains filtering."""
        query = '''
            query {
                allPosts(filters: {title_Icontains: "test"}) {
                    edges {
                        node {
                            id
                            title
                        }
                    }
                }
            }
        '''
        
        result = self.execute_query(query)
        self.assertNoErrors(result)
        
        posts = result.data['allPosts']['edges']
        self.assertEqual(len(posts), 1)
        self.assertIn('Test', posts[0]['node']['title'])
    
    def test_relationship_filter(self):
        """Test filtering by relationship."""
        query = '''
            query {
                allPosts(filters: {author: %d}) {
                    edges {
                        node {
                            id
                            title
                            author {
                                name
                            }
                        }
                    }
                }
            }
        ''' % self.author.id
        
        result = self.execute_query(query)
        self.assertNoErrors(result)
        
        posts = result.data['allPosts']['edges']
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]['node']['author']['name'], self.author.name)
    
    def test_date_range_filter(self):
        """Test date range filtering."""
        from datetime import date, timedelta
        
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        query = '''
            query($startDate: Date!, $endDate: Date!) {
                allPosts(filters: {createdAt_Range: [$startDate, $endDate]}) {
                    edges {
                        node {
                            id
                            title
                            createdAt
                        }
                    }
                }
            }
        '''
        
        variables = {
            'startDate': yesterday.isoformat(),
            'endDate': tomorrow.isoformat()
        }
        
        result = self.execute_query(query, variables=variables)
        self.assertNoErrors(result)
        
        posts = result.data['allPosts']['edges']
        self.assertGreaterEqual(len(posts), 1)
    
    def test_multiple_filters(self):
        """Test combining multiple filters."""
        query = '''
            query {
                allPosts(filters: {
                    status: "published",
                    author: %d
                }) {
                    edges {
                        node {
                            id
                            title
                            status
                            author {
                                name
                            }
                        }
                    }
                }
            }
        ''' % self.author.id
        
        result = self.execute_query(query)
        self.assertNoErrors(result)
        
        posts = result.data['allPosts']['edges']
        self.assertEqual(len(posts), 1)
        
        post = posts[0]['node']
        self.assertEqual(post['status'], 'published')
        self.assertEqual(post['author']['name'], self.author.name)

class TestPagination(GraphQLTestCase):
    """Test pagination functionality."""
    
    def setUp(self):
        super().setUp()
        
        # Create multiple posts for pagination testing
        for i in range(10):
            Post.objects.create(
                title=f"Post {i}",
                content=f"Content {i}",
                author=self.author,
                status="published"
            )
    
    def test_cursor_pagination(self):
        """Test cursor-based pagination."""
        query = '''
            query {
                allPosts(first: 5) {
                    edges {
                        node {
                            id
                            title
                        }
                        cursor
                    }
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                        startCursor
                        endCursor
                    }
                }
            }
        '''
        
        result = self.execute_query(query)
        self.assertNoErrors(result)
        
        data = result.data['allPosts']
        self.assertEqual(len(data['edges']), 5)
        self.assertTrue(data['pageInfo']['hasNextPage'])
        self.assertFalse(data['pageInfo']['hasPreviousPage'])
        self.assertIsNotNone(data['pageInfo']['endCursor'])
    
    def test_cursor_pagination_after(self):
        """Test cursor pagination with 'after' parameter."""
        # First, get the first page
        first_query = '''
            query {
                allPosts(first: 3) {
                    edges {
                        cursor
                    }
                    pageInfo {
                        endCursor
                    }
                }
            }
        '''
        
        first_result = self.execute_query(first_query)
        self.assertNoErrors(first_result)
        
        end_cursor = first_result.data['allPosts']['pageInfo']['endCursor']
        
        # Then get the next page
        second_query = '''
            query($after: String!) {
                allPosts(first: 3, after: $after) {
                    edges {
                        node {
                            id
                            title
                        }
                    }
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                    }
                }
            }
        '''
        
        second_result = self.execute_query(second_query, variables={'after': end_cursor})
        self.assertNoErrors(second_result)
        
        data = second_result.data['allPosts']
        self.assertEqual(len(data['edges']), 3)
        self.assertTrue(data['pageInfo']['hasPreviousPage'])
    
    def test_offset_pagination(self):
        """Test offset-based pagination."""
        query = '''
            query($offset: Int!, $limit: Int!) {
                allPostsPaginated(offset: $offset, limit: $limit) {
                    items {
                        id
                        title
                    }
                    pageInfo {
                        totalCount
                        hasNext
                        hasPrevious
                    }
                }
            }
        '''
        
        variables = {'offset': 0, 'limit': 5}
        result = self.execute_query(query, variables=variables)
        self.assertNoErrors(result)
        
        data = result.data['allPostsPaginated']
        self.assertEqual(len(data['items']), 5)
        self.assertGreaterEqual(data['pageInfo']['totalCount'], 10)
        self.assertTrue(data['pageInfo']['hasNext'])
        self.assertFalse(data['pageInfo']['hasPrevious'])
```

## 🔗 Integration Testing

### Testing Complete Workflows

```python
# tests/test_integration.py
from tests.base import GraphQLTestCase
from tests.test_app.models import Post, Author, Category, Tag

class TestCompleteWorkflows(GraphQLTestCase):
    """Test complete GraphQL workflows."""
    
    def test_create_post_workflow(self):
        """Test complete post creation workflow."""
        
        # Step 1: Create author
        create_author_mutation = '''
            mutation {
                createAuthor(input: {
                    name: "New Author"
                    email: "new@example.com"
                    bio: "New author bio"
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
        '''
        
        author_result = self.execute_query(create_author_mutation)
        self.assertNoErrors(author_result)
        self.assertTrue(author_result.data['createAuthor']['success'])
        
        author_id = author_result.data['createAuthor']['author']['id']
        
        # Step 2: Create category
        create_category_mutation = '''
            mutation {
                createCategory(input: {
                    name: "New Category"
                    description: "New category description"
                }) {
                    category {
                        id
                        name
                    }
                    success
                }
            }
        '''
        
        category_result = self.execute_query(create_category_mutation)
        self.assertNoErrors(category_result)
        
        category_id = category_result.data['createCategory']['category']['id']
        
        # Step 3: Create tags
        tag_ids = []
        for tag_name in ['Python', 'GraphQL']:
            create_tag_mutation = '''
                mutation($name: String!) {
                    createTag(input: {
                        name: $name
                        color: "#ff0000"
                    }) {
                        tag {
                            id
                            name
                        }
                        success
                    }
                }
            '''
            
            tag_result = self.execute_query(
                create_tag_mutation,
                variables={'name': tag_name}
            )
            self.assertNoErrors(tag_result)
            tag_ids.append(tag_result.data['createTag']['tag']['id'])
        
        # Step 4: Create post with relationships
        create_post_mutation = '''
            mutation($authorId: ID!, $categoryId: ID!, $tagIds: [ID!]!) {
                createPost(input: {
                    title: "Integration Test Post"
                    content: "This is a test post created through integration testing"
                    author: $authorId
                    category: $categoryId
                    tags: $tagIds
                    status: "published"
                }) {
                    post {
                        id
                        title
                        content
                        status
                        author {
                            name
                            email
                        }
                        category {
                            name
                        }
                        tags {
                            edges {
                                node {
                                    name
                                }
                            }
                        }
                    }
                    success
                    errors
                }
            }
        '''
        
        post_result = self.execute_query(
            create_post_mutation,
            variables={
                'authorId': author_id,
                'categoryId': category_id,
                'tagIds': tag_ids
            }
        )
        
        self.assertNoErrors(post_result)
        self.assertTrue(post_result.data['createPost']['success'])
        
        post_data = post_result.data['createPost']['post']
        self.assertEqual(post_data['title'], 'Integration Test Post')
        self.assertEqual(post_data['author']['name'], 'New Author')
        self.assertEqual(post_data['category']['name'], 'New Category')
        self.assertEqual(len(post_data['tags']['edges']), 2)
        
        # Step 5: Query the created post
        post_id = post_data['id']
        query_post = '''
            query($id: ID!) {
                post(id: $id) {
                    id
                    title
                    content
                    author {
                        name
                        posts {
                            edges {
                                node {
                                    title
                                }
                            }
                        }
                    }
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
        '''
        
        query_result = self.execute_query(query_post, variables={'id': post_id})
        self.assertNoErrors(query_result)
        
        queried_post = query_result.data['post']
        self.assertEqual(queried_post['title'], 'Integration Test Post')
        self.assertGreaterEqual(len(queried_post['author']['posts']['edges']), 1)
    
    def test_nested_create_workflow(self):
        """Test nested object creation."""
        
        nested_create_mutation = '''
            mutation {
                createPostWithNested(input: {
                    title: "Nested Creation Test"
                    content: "Testing nested creation"
                    status: "published"
                    author: {
                        name: "Nested Author"
                        email: "nested@example.com"
                        bio: "Created through nested mutation"
                    }
                    category: {
                        name: "Nested Category"
                        description: "Created through nested mutation"
                    }
                    tags: [
                        {
                            name: "NestedTag1"
                            color: "#ff0000"
                        },
                        {
                            name: "NestedTag2"
                            color: "#00ff00"
                        }
                    ]
                }) {
                    post {
                        id
                        title
                        author {
                            id
                            name
                        }
                        category {
                            id
                            name
                        }
                        tags {
                            edges {
                                node {
                                    id
                                    name
                                }
                            }
                        }
                    }
                    success
                    errors
                }
            }
        '''
        
        result = self.execute_query(nested_create_mutation)
        self.assertNoErrors(result)
        self.assertTrue(result.data['createPostWithNested']['success'])
        
        post_data = result.data['createPostWithNested']['post']
        self.assertEqual(post_data['title'], 'Nested Creation Test')
        self.assertEqual(post_data['author']['name'], 'Nested Author')
        self.assertEqual(post_data['category']['name'], 'Nested Category')
        self.assertEqual(len(post_data['tags']['edges']), 2)
    
    def test_update_workflow(self):
        """Test post update workflow."""
        
        # Create initial post
        initial_post = Post.objects.create(
            title="Original Title",
            content="Original content",
            author=self.author,
            status="draft"
        )
        
        # Update post
        update_mutation = '''
            mutation($id: ID!) {
                updatePost(id: $id, input: {
                    title: "Updated Title"
                    content: "Updated content"
                    status: "published"
                }) {
                    post {
                        id
                        title
                        content
                        status
                        updatedAt
                    }
                    success
                    errors
                }
            }
        '''
        
        result = self.execute_query(
            update_mutation,
            variables={'id': str(initial_post.id)}
        )
        
        self.assertNoErrors(result)
        self.assertTrue(result.data['updatePost']['success'])
        
        updated_post = result.data['updatePost']['post']
        self.assertEqual(updated_post['title'], 'Updated Title')
        self.assertEqual(updated_post['content'], 'Updated content')
        self.assertEqual(updated_post['status'], 'published')
        
        # Verify in database
        initial_post.refresh_from_db()
        self.assertEqual(initial_post.title, 'Updated Title')
        self.assertEqual(initial_post.status, 'published')
    
    def test_delete_workflow(self):
        """Test post deletion workflow."""
        
        # Create post to delete
        post_to_delete = Post.objects.create(
            title="Post to Delete",
            content="This post will be deleted",
            author=self.author
        )
        
        post_id = post_to_delete.id
        
        # Delete post
        delete_mutation = '''
            mutation($id: ID!) {
                deletePost(id: $id) {
                    success
                    errors
                }
            }
        '''
        
        result = self.execute_query(
            delete_mutation,
            variables={'id': str(post_id)}
        )
        
        self.assertNoErrors(result)
        self.assertTrue(result.data['deletePost']['success'])
        
        # Verify post is deleted
        self.assertFalse(Post.objects.filter(id=post_id).exists())
        
        # Verify query returns null
        query_deleted_post = '''
            query($id: ID!) {
                post(id: $id) {
                    id
                    title
                }
            }
        '''
        
        query_result = self.execute_query(
            query_deleted_post,
            variables={'id': str(post_id)}
        )
        
        self.assertNoErrors(query_result)
        self.assertIsNone(query_result.data['post'])
```

## 🚀 Performance Testing

### Query Performance Tests

```python
# tests/test_performance.py
from tests.base import PerformanceTestCase
from tests.test_app.models import Post, Author, Comment
from django.test import override_settings

class TestQueryPerformance(PerformanceTestCase):
    """Test GraphQL query performance."""
    
    def test_n_plus_one_prevention(self):
        """Test that N+1 queries are prevented."""
        
        # Create test data
        authors, posts = self.create_test_data(num_authors=10, num_posts_per_author=5)
        
        # Query that could cause N+1 problem
        query = '''
            query {
                allPosts {
                    edges {
                        node {
                            id
                            title
                            author {
                                name
                                email
                            }
                        }
                    }
                }
            }
        '''
        
        performance = self.measure_query_performance(query)
        
        # Should use select_related to avoid N+1
        # Expected: 1 query for posts with authors
        self.assertLessEqual(performance['query_count'], 3)
        self.assertNoErrors(performance['result'])
        
        posts_data = performance['result'].data['allPosts']['edges']
        self.assertEqual(len(posts_data), 50)  # 10 authors * 5 posts each
    
    def test_prefetch_related_optimization(self):
        """Test prefetch_related optimization for reverse relationships."""
        
        # Create test data with comments
        authors, posts = self.create_test_data(num_authors=5, num_posts_per_author=3)
        
        # Add comments to posts
        for post in posts:
            for i in range(3):
                Comment.objects.create(
                    post=post,
                    author=post.author,
                    content=f"Comment {i} on {post.title}",
                    is_approved=True
                )
        
        # Query with reverse relationship
        query = '''
            query {
                allPosts {
                    edges {
                        node {
                            id
                            title
                            author {
                                name
                            }
                            comments {
                                edges {
                                    node {
                                        content
                                        author {
                                            name
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        '''
        
        performance = self.measure_query_performance(query)
        
        # Should use prefetch_related for comments
        # Expected: 1 query for posts, 1 for authors, 1 for comments, 1 for comment authors
        self.assertLessEqual(performance['query_count'], 5)
        self.assertNoErrors(performance['result'])
    
    def test_pagination_performance(self):
        """Test pagination performance with large datasets."""
        
        # Create large dataset
        authors, posts = self.create_test_data(num_authors=50, num_posts_per_author=10)
        
        # Test cursor pagination
        cursor_query = '''
            query {
                allPosts(first: 20) {
                    edges {
                        node {
                            id
                            title
                            author {
                                name
                            }
                        }
                        cursor
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        '''
        
        performance = self.measure_query_performance(cursor_query)
        
        # Pagination should be efficient
        self.assertLess(performance['execution_time'], 1.0)  # Less than 1 second
        self.assertLessEqual(performance['query_count'], 3)
        self.assertNoErrors(performance['result'])
        
        # Verify correct number of results
        edges = performance['result'].data['allPosts']['edges']
        self.assertEqual(len(edges), 20)
    
    def test_filtering_performance(self):
        """Test filtering performance with indexes."""
        
        # Create test data
        authors, posts = self.create_test_data(num_authors=20, num_posts_per_author=10)
        
        # Update some posts to published status
        Post.objects.filter(id__in=[p.id for p in posts[:100]]).update(status='published')
        
        # Query with filtering (should use index)
        filter_query = '''
            query {
                allPosts(filters: {status: "published"}) {
                    edges {
                        node {
                            id
                            title
                            status
                            author {
                                name
                            }
                        }
                    }
                }
            }
        '''
        
        performance = self.measure_query_performance(filter_query)
        
        # Filtering should be fast with proper indexes
        self.assertLess(performance['execution_time'], 0.5)
        self.assertNoErrors(performance['result'])
        
        # Verify filtering worked
        posts_data = performance['result'].data['allPosts']['edges']
        for post in posts_data:
            self.assertEqual(post['node']['status'], 'published')
    
    @override_settings(DEBUG=True)
    def test_complex_query_performance(self):
        """Test performance of complex nested queries."""
        
        # Create comprehensive test data
        authors, posts = self.create_test_data(num_authors=10, num_posts_per_author=5)
        
        # Add comments and tags
        from tests.test_app.models import Tag
        tags = [Tag.objects.create(name=f"Tag{i}") for i in range(10)]
        
        for post in posts:
            # Add tags to posts
            post.tags.add(*tags[:3])
            
            # Add comments
            for i in range(2):
                Comment.objects.create(
                    post=post,
                    author=post.author,
                    content=f"Comment {i}",
                    is_approved=True
                )
        
        # Complex nested query
        complex_query = '''
            query {
                allPosts(first: 10, filters: {status: "draft"}) {
                    edges {
                        node {
                            id
                            title
                            content
                            status
                            viewCount
                            createdAt
                            author {
                                id
                                name
                                email
                                bio
                                posts {
                                    edges {
                                        node {
                                            title
                                        }
                                    }
                                }
                            }
                            category {
                                id
                                name
                                description
                            }
                            tags {
                                edges {
                                    node {
                                        id
                                        name
                                        color
                                    }
                                }
                            }
                            comments {
                                edges {
                                    node {
                                        id
                                        content
                                        isApproved
                                        author {
                                            name
                                        }
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
        '''
        
        performance = self.measure_query_performance(complex_query)
        
        # Complex query should still be reasonably fast
        self.assertLess(performance['execution_time'], 2.0)
        self.assertLessEqual(performance['query_count'], 10)
        self.assertNoErrors(performance['result'])
        
        # Print performance metrics for analysis
        print(f"\nComplex Query Performance:")
        print(f"  Execution time: {performance['execution_time']:.3f}s")
        print(f"  Database queries: {performance['query_count']}")
        print(f"  Queries executed:")
        for i, query in enumerate(performance['queries'], 1):
            print(f"    {i}. {query['sql'][:100]}... ({query['time']}s)")
```

## 🎭 Mocking and Fixtures

### Test Fixtures

```python
# tests/fixtures.py
import pytest
from django.test import TestCase
from tests.test_app.models import Author, Post, Category, Tag, Comment

class TestDataMixin:
    """Mixin providing test data creation methods."""
    
    def create_author(self, **kwargs):
        """Create test author."""
        defaults = {
            'name': 'Test Author',
            'email': 'test@example.com',
            'bio': 'Test bio'
        }
        defaults.update(kwargs)
        return Author.objects.create(**defaults)
    
    def create_category(self, **kwargs):
        """Create test category."""
        defaults = {
            'name': 'Test Category',
            'description': 'Test description'
        }
        defaults.update(kwargs)
        return Category.objects.create(**defaults)
    
    def create_tag(self, **kwargs):
        """Create test tag."""
        defaults = {
            'name': 'Test Tag',
            'color': '#000000'
        }
        defaults.update(kwargs)
        return Tag.objects.create(**defaults)
    
    def create_post(self, **kwargs):
        """Create test post."""
        if 'author' not in kwargs:
            kwargs['author'] = self.create_author()
        
        defaults = {
            'title': 'Test Post',
            'content': 'Test content',
            'status': 'published'
        }
        defaults.update(kwargs)
        return Post.objects.create(**defaults)
    
    def create_comment(self, **kwargs):
        """Create test comment."""
        if 'post' not in kwargs:
            kwargs['post'] = self.create_post()
        if 'author' not in kwargs:
            kwargs['author'] = kwargs['post'].author
        
        defaults = {
            'content': 'Test comment',
            'is_approved': True
        }
        defaults.update(kwargs)
        return Comment.objects.create(**defaults)

# Pytest fixtures
@pytest.fixture
def author():
    """Create test author."""
    return Author.objects.create(
        name='Test Author',
        email='test@example.com',
        bio='Test bio'
    )

@pytest.fixture
def category():
    """Create test category."""
    return Category.objects.create(
        name='Test Category',
        description='Test description'
    )

@pytest.fixture
def post(author, category):
    """Create test post."""
    return Post.objects.create(
        title='Test Post',
        content='Test content',
        author=author,
        category=category,
        status='published'
    )

@pytest.fixture
def graphql_client():
    """Create GraphQL test client."""
    from graphene.test import Client
    from django_graphql_auto.schema import build_schema
    
    schema = build_schema()
    return Client(schema)
```

### Mocking External Services

```python
# tests/test_mocking.py
from unittest.mock import patch, Mock
from tests.base import GraphQLTestCase

class TestExternalServiceMocking(GraphQLTestCase):
    """Test mocking of external services."""
    
    @patch('requests.get')
    def test_external_api_call(self, mock_get):
        """Test mocking external API calls."""
        
        # Mock external API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'weather': 'sunny',
            'temperature': 25
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Add method to Post model that calls external API
        def get_weather_info(self):
            import requests
            response = requests.get(f'http://api.weather.com/location/{self.id}')
            return response.json()
        
        Post.get_weather_info = get_weather_info
        
        # Regenerate schema
        self.schema = build_schema()
        self.client = Client(self.schema)
        
        # Test query
        query = '''
            query {
                post(id: %d) {
                    weatherInfo
                }
            }
        ''' % self.post.id
        
        result = self.execute_query(query)
        self.assertNoErrors(result)
        
        weather_info = result.data['post']['weatherInfo']
        self.assertEqual(weather_info['weather'], 'sunny')
        self.assertEqual(weather_info['temperature'], 25)
        
        # Verify mock was called
        mock_get.assert_called_once_with(f'http://api.weather.com/location/{self.post.id}')
    
    @patch('django.core.mail.send_mail')
    def test_email_sending_mock(self, mock_send_mail):
        """Test mocking email sending."""
        
        # Mock successful email sending
        mock_send_mail.return_value = True
        
        # Test mutation that sends email
        mutation = '''
            mutation {
                sendPostNotification(postId: %d, email: "test@example.com") {
                    success
                    message
                }
            }
        ''' % self.post.id
        
        result = self.execute_query(mutation)
        self.assertNoErrors(result)
        self.assertTrue(result.data['sendPostNotification']['success'])
        
        # Verify email was "sent"
        mock_send_mail.assert_called_once()
    
    @patch('django_graphql_auto.cache.cache')
    def test_cache_mocking(self, mock_cache):
        """Test mocking cache operations."""
        
        # Mock cache miss then hit
        mock_cache.get.side_effect = [None, {'cached': 'data'}]
        mock_cache.set.return_value = True
        
        # Query that uses caching
        query = '''
            query {
                post(id: %d) {
                    expensiveCalculation
                }
            }
        ''' % self.post.id
        
        # First call - cache miss
        result1 = self.execute_query(query)
        self.assertNoErrors(result1)
        
        # Second call - cache hit
        result2 = self.execute_query(query)
        self.assertNoErrors(result2)
        
        # Verify cache operations
        self.assertEqual(mock_cache.get.call_count, 2)
        mock_cache.set.assert_called_once()
```

## 🔄 Continuous Integration

### GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10', 3.11]
        django-version: [3.2, 4.0, 4.1, 4.2]
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install Django==${{ matrix.django-version }}
        pip install -r requirements-test.txt
    
    - name: Run linting
      run: |
        flake8 django_graphql_auto tests
        black --check django_graphql_auto tests
        isort --check-only django_graphql_auto tests
    
    - name: Run type checking
      run: |
        mypy django_graphql_auto
    
    - name: Run tests
      env:
        DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
      run: |
        python -m pytest tests/ -v --cov=django_graphql_auto --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
    
    - name: Run performance tests
      env:
        DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_db
      run: |
        python -m pytest tests/test_performance.py -v --benchmark-only
```

### Test Configuration Files

```python
# pytest.ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = tests.settings
python_files = tests.py test_*.py *_tests.py
addopts = 
    --verbose
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=django_graphql_auto
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    performance: marks tests as performance tests
    unit: marks tests as unit tests

# setup.cfg
[coverage:run]
source = django_graphql_auto
omit = 
    */migrations/*
    */tests/*
    */venv/*
    manage.py
    setup.py

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:

[flake8]
max-line-length = 88
exclude = 
    migrations,
    __pycache__,
    manage.py,
    settings.py,
    env,
    venv
ignore = E203, W503

[isort]
profile = black
multi_line_output = 3
line_length = 88
```

## 📋 Best Practices

### 1. Test Organization

- **Separate test types** - Unit, integration, and performance tests
- **Use descriptive test names** that explain what is being tested
- **Group related tests** in test classes
- **Use fixtures and mixins** for common test data

### 2. Test Data Management

- **Create minimal test data** for each test
- **Use factories** for complex object creation
- **Clean up after tests** to avoid side effects
- **Use transactions** for test isolation

### 3. GraphQL Testing

- **Test schema generation** separately from query execution
- **Verify both success and error cases**
- **Test pagination and filtering** thoroughly
- **Check query optimization** and performance

### 4. Performance Testing

- **Set performance benchmarks** and monitor regressions
- **Test with realistic data volumes**
- **Monitor database query counts**
- **Use profiling tools** for detailed analysis

### 5. Continuous Integration

- **Test multiple Python and Django versions**
- **Include linting and type checking**
- **Monitor test coverage**
- **Run performance tests** in CI

## 🔗 Next Steps

Now that you understand testing:

1. [Review Performance Guide](../development/performance.md) - Optimize your code
2. [Check Troubleshooting Guide](../development/troubleshooting.md) - Debug issues
3. [Explore Advanced Examples](../examples/advanced-examples.md) - See complex implementations
4. [Read API Reference](../api/core-classes.md) - Understand testing APIs

## 🤝 Need Help?

- Check the [Troubleshooting Guide](../development/troubleshooting.md)
- Review [Configuration Options](../setup/configuration.md)
- Join our [Community Discussions](https://github.com/your-repo/django-graphql-auto/discussions)