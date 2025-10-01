Testing
=======

Comprehensive testing guide for Django GraphQL Auto development and usage.

Overview
--------

Testing is a critical part of Django GraphQL Auto development. This guide covers testing strategies, tools, and best practices for both contributors and users of the library.

Testing Philosophy
------------------

**Our Testing Approach:**

1. **Test-Driven Development (TDD)**: Write tests before implementing features
2. **Comprehensive Coverage**: Aim for 95%+ code coverage
3. **Multiple Test Types**: Unit, integration, and end-to-end tests
4. **Continuous Testing**: Automated testing in CI/CD pipeline
5. **Performance Testing**: Regular performance regression testing

**Testing Pyramid:**

.. code-block:: text

   ┌─────────────────┐
   │   E2E Tests     │  ← Few, slow, high confidence
   ├─────────────────┤
   │ Integration     │  ← Some, medium speed
   │    Tests        │
   ├─────────────────┤
   │   Unit Tests    │  ← Many, fast, focused
   └─────────────────┘

Test Environment Setup
----------------------

Development Environment
~~~~~~~~~~~~~~~~~~~~~~~

**Install Testing Dependencies:**

.. code-block:: bash

   # Install development dependencies
   pip install -e ".[dev]"
   
   # Or install specific testing tools
   pip install pytest pytest-django pytest-cov
   pip install factory-boy faker
   pip install pytest-mock pytest-asyncio
   pip install coverage

**Configure Test Settings:**

.. code-block:: python

   # tests/settings.py
   from django_graphql_auto.settings import *
   
   # Test database configuration
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
   
   # Test-specific settings
   SECRET_KEY = 'test-secret-key'
   DEBUG = True
   USE_TZ = True
   
   # GraphQL Auto test configuration
   GRAPHQL_AUTO = {
       'TESTING': True,
       'CACHE_ENABLED': False,
       'MONITORING_ENABLED': False,
   }

**Pytest Configuration:**

.. code-block:: ini

   # pytest.ini
   [tool:pytest]
   DJANGO_SETTINGS_MODULE = tests.settings
   python_files = tests.py test_*.py *_tests.py
   python_classes = Test*
   python_functions = test_*
   addopts = 
       --verbose
       --tb=short
       --strict-markers
       --disable-warnings
       --cov=django_graphql_auto
       --cov-report=html
       --cov-report=term-missing
       --cov-fail-under=90

Unit Testing
------------

Model Testing
~~~~~~~~~~~~~

**Testing Django Models:**

.. code-block:: python

   import pytest
   from django.test import TestCase
   from django.core.exceptions import ValidationError
   from tests.models import User, Post, Category
   
   class TestUserModel(TestCase):
       def test_user_creation_with_valid_data(self):
           """Test creating a user with valid data."""
           user = User.objects.create(
               username='testuser',
               email='test@example.com',
               first_name='Test',
               last_name='User'
           )
           
           assert user.username == 'testuser'
           assert user.email == 'test@example.com'
           assert str(user) == 'testuser'
       
       def test_user_email_validation(self):
           """Test email validation in user model."""
           with pytest.raises(ValidationError):
               user = User(
                   username='testuser',
                   email='invalid-email'
               )
               user.full_clean()
       
       def test_user_str_representation(self):
           """Test string representation of user model."""
           user = User(username='testuser')
           assert str(user) == 'testuser'

**Testing Model Relationships:**

.. code-block:: python

   class TestModelRelationships(TestCase):
       def setUp(self):
           self.user = User.objects.create(
               username='author',
               email='author@example.com'
           )
           self.category = Category.objects.create(
               name='Technology',
               slug='technology'
           )
       
       def test_post_creation_with_relationships(self):
           """Test creating post with foreign key relationships."""
           post = Post.objects.create(
               title='Test Post',
               content='Test content',
               author=self.user,
               category=self.category
           )
           
           assert post.author == self.user
           assert post.category == self.category
           assert post in self.user.posts.all()
           assert post in self.category.posts.all()

Schema Testing
~~~~~~~~~~~~~~

**Testing GraphQL Schema Generation:**

.. code-block:: python

   import pytest
   from graphql import build_schema, validate_schema
   from django_graphql_auto.schema import SchemaGenerator
   from tests.models import User, Post
   
   class TestSchemaGeneration:
       def test_schema_generation_for_simple_model(self):
           """Test schema generation for a simple model."""
           generator = SchemaGenerator()
           schema = generator.generate_schema([User])
           
           # Validate schema is valid GraphQL
           assert validate_schema(schema) == []
           
           # Check if User type exists
           user_type = schema.type_map.get('User')
           assert user_type is not None
           
           # Check if expected fields exist
           fields = user_type.fields
           assert 'id' in fields
           assert 'username' in fields
           assert 'email' in fields
       
       def test_schema_generation_with_relationships(self):
           """Test schema generation for models with relationships."""
           generator = SchemaGenerator()
           schema = generator.generate_schema([User, Post])
           
           # Check relationship fields
           post_type = schema.type_map.get('Post')
           assert 'author' in post_type.fields
           
           user_type = schema.type_map.get('User')
           assert 'posts' in user_type.fields

**Testing Custom Resolvers:**

.. code-block:: python

   from django_graphql_auto.resolvers import BaseResolver
   from unittest.mock import Mock, patch
   
   class TestCustomResolvers:
       def test_user_resolver_with_valid_id(self):
           """Test user resolver with valid user ID."""
           # Create test user
           user = User.objects.create(
               username='testuser',
               email='test@example.com'
           )
           
           # Test resolver
           resolver = BaseResolver()
           info = Mock()
           result = resolver.resolve_user(info, id=user.id)
           
           assert result == user
       
       def test_user_resolver_with_invalid_id(self):
           """Test user resolver with non-existent user ID."""
           resolver = BaseResolver()
           info = Mock()
           
           with pytest.raises(User.DoesNotExist):
               resolver.resolve_user(info, id=99999)

Integration Testing
-------------------

API Testing
~~~~~~~~~~~

**Testing GraphQL Queries:**

.. code-block:: python

   import json
   from django.test import TestCase, Client
   from django.urls import reverse
   from tests.factories import UserFactory, PostFactory
   
   class TestGraphQLAPI(TestCase):
       def setUp(self):
           self.client = Client()
           self.graphql_url = reverse('graphql')
           self.user = UserFactory()
           self.posts = PostFactory.create_batch(3, author=self.user)
       
       def execute_query(self, query, variables=None):
           """Helper method to execute GraphQL queries."""
           body = {'query': query}
           if variables:
               body['variables'] = variables
           
           response = self.client.post(
               self.graphql_url,
               json.dumps(body),
               content_type='application/json'
           )
           return json.loads(response.content)
       
       def test_user_query(self):
           """Test querying a single user."""
           query = '''
           query GetUser($id: ID!) {
               user(id: $id) {
                   id
                   username
                   email
                   posts {
                       id
                       title
                   }
               }
           }
           '''
           
           result = self.execute_query(query, {'id': str(self.user.id)})
           
           assert 'errors' not in result
           user_data = result['data']['user']
           assert user_data['username'] == self.user.username
           assert len(user_data['posts']) == 3
       
       def test_posts_query_with_filtering(self):
           """Test querying posts with filtering."""
           query = '''
           query GetPosts($authorId: ID!) {
               posts(author: $authorId) {
                   edges {
                       node {
                           id
                           title
                           author {
                               username
                           }
                       }
                   }
               }
           }
           '''
           
           result = self.execute_query(query, {'authorId': str(self.user.id)})
           
           assert 'errors' not in result
           posts_data = result['data']['posts']['edges']
           assert len(posts_data) == 3
           
           for edge in posts_data:
               assert edge['node']['author']['username'] == self.user.username

**Testing GraphQL Mutations:**

.. code-block:: python

   class TestGraphQLMutations(TestCase):
       def setUp(self):
           self.client = Client()
           self.graphql_url = reverse('graphql')
       
       def test_create_user_mutation(self):
           """Test creating a user via GraphQL mutation."""
           mutation = '''
           mutation CreateUser($input: CreateUserInput!) {
               createUser(input: $input) {
                   user {
                       id
                       username
                       email
                   }
                   errors {
                       field
                       messages
                   }
               }
           }
           '''
           
           variables = {
               'input': {
                   'username': 'newuser',
                   'email': 'newuser@example.com',
                   'password': 'securepassword123'
               }
           }
           
           result = self.execute_query(mutation, variables)
           
           assert 'errors' not in result
           user_data = result['data']['createUser']['user']
           assert user_data['username'] == 'newuser'
           assert user_data['email'] == 'newuser@example.com'
           
           # Verify user was created in database
           user = User.objects.get(username='newuser')
           assert user.email == 'newuser@example.com'

Database Testing
~~~~~~~~~~~~~~~~

**Testing Database Queries:**

.. code-block:: python

   from django.test import TestCase
   from django.test.utils import override_settings
   from django.db import connection
   from django.test.utils import override_settings
   
   class TestDatabaseQueries(TestCase):
       def test_query_optimization(self):
           """Test that queries are optimized to prevent N+1 problems."""
           # Create test data
           users = UserFactory.create_batch(5)
           for user in users:
               PostFactory.create_batch(3, author=user)
           
           query = '''
           query GetUsersWithPosts {
               users {
                   edges {
                       node {
                           username
                           posts {
                               edges {
                                   node {
                                       title
                                   }
                               }
                           }
                       }
                   }
               }
           }
           '''
           
           # Count database queries
           with self.assertNumQueries(3):  # Should be optimized
               result = self.execute_query(query)
           
           assert 'errors' not in result
           assert len(result['data']['users']['edges']) == 5

Performance Testing
-------------------

Load Testing
~~~~~~~~~~~~

**Testing Query Performance:**

.. code-block:: python

   import time
   import pytest
   from django.test import TestCase
   from tests.factories import UserFactory, PostFactory
   
   class TestPerformance(TestCase):
       def setUp(self):
           # Create large dataset for performance testing
           self.users = UserFactory.create_batch(100)
           for user in self.users:
               PostFactory.create_batch(10, author=user)
       
       def test_large_dataset_query_performance(self):
           """Test query performance with large dataset."""
           query = '''
           query GetAllUsers {
               users(first: 50) {
                   edges {
                       node {
                           username
                           posts(first: 5) {
                               edges {
                                   node {
                                       title
                                   }
                               }
                           }
                       }
                   }
               }
           }
           '''
           
           start_time = time.time()
           result = self.execute_query(query)
           end_time = time.time()
           
           query_time = end_time - start_time
           
           # Assert query completes within acceptable time
           assert query_time < 1.0  # Should complete within 1 second
           assert 'errors' not in result
       
       @pytest.mark.slow
       def test_concurrent_requests(self):
           """Test handling of concurrent requests."""
           import threading
           import queue
           
           results = queue.Queue()
           
           def make_request():
               query = '''
               query GetUsers {
                   users(first: 10) {
                       edges {
                           node {
                               username
                           }
                       }
                   }
               }
               '''
               result = self.execute_query(query)
               results.put(result)
           
           # Create multiple threads
           threads = []
           for _ in range(10):
               thread = threading.Thread(target=make_request)
               threads.append(thread)
               thread.start()
           
           # Wait for all threads to complete
           for thread in threads:
               thread.join()
           
           # Check all requests succeeded
           while not results.empty():
               result = results.get()
               assert 'errors' not in result

Memory Testing
~~~~~~~~~~~~~~

**Testing Memory Usage:**

.. code-block:: python

   import psutil
   import os
   from django.test import TestCase
   
   class TestMemoryUsage(TestCase):
       def test_memory_usage_with_large_queries(self):
           """Test memory usage doesn't grow excessively with large queries."""
           process = psutil.Process(os.getpid())
           initial_memory = process.memory_info().rss
           
           # Execute large query multiple times
           query = '''
           query GetLargeDataset {
               users(first: 1000) {
                   edges {
                       node {
                           username
                           email
                           posts {
                               edges {
                                   node {
                                       title
                                       content
                                   }
                               }
                           }
                       }
                   }
               }
           }
           '''
           
           for _ in range(10):
               result = self.execute_query(query)
               assert 'errors' not in result
           
           final_memory = process.memory_info().rss
           memory_increase = final_memory - initial_memory
           
           # Memory increase should be reasonable (less than 100MB)
           assert memory_increase < 100 * 1024 * 1024

End-to-End Testing
------------------

Browser Testing
~~~~~~~~~~~~~~~

**Using Selenium for E2E Tests:**

.. code-block:: python

   import pytest
   from selenium import webdriver
   from selenium.webdriver.common.by import By
   from selenium.webdriver.support.ui import WebDriverWait
   from selenium.webdriver.support import expected_conditions as EC
   from django.contrib.staticfiles.testing import StaticLiveServerTestCase
   
   class TestGraphQLPlayground(StaticLiveServerTestCase):
       @classmethod
       def setUpClass(cls):
           super().setUpClass()
           cls.selenium = webdriver.Chrome()  # Requires chromedriver
           cls.selenium.implicitly_wait(10)
       
       @classmethod
       def tearDownClass(cls):
           cls.selenium.quit()
           super().tearDownClass()
       
       def test_graphql_playground_loads(self):
           """Test that GraphQL playground loads correctly."""
           self.selenium.get(f'{self.live_server_url}/graphql/')
           
           # Wait for playground to load
           WebDriverWait(self.selenium, 10).until(
               EC.presence_of_element_located((By.CLASS_NAME, "graphiql-container"))
           )
           
           # Check if query editor is present
           query_editor = self.selenium.find_element(By.CLASS_NAME, "query-editor")
           assert query_editor.is_displayed()
       
       def test_execute_query_in_playground(self):
           """Test executing a query in the GraphQL playground."""
           self.selenium.get(f'{self.live_server_url}/graphql/')
           
           # Wait for playground to load
           WebDriverWait(self.selenium, 10).until(
               EC.presence_of_element_located((By.CLASS_NAME, "graphiql-container"))
           )
           
           # Enter query
           query_editor = self.selenium.find_element(By.CLASS_NAME, "query-editor")
           query_editor.send_keys('''
           query {
               users {
                   edges {
                       node {
                           username
                       }
                   }
               }
           }
           ''')
           
           # Execute query
           execute_button = self.selenium.find_element(By.CLASS_NAME, "execute-button")
           execute_button.click()
           
           # Wait for results
           WebDriverWait(self.selenium, 10).until(
               EC.presence_of_element_located((By.CLASS_NAME, "result-window"))
           )
           
           # Check results are displayed
           result_window = self.selenium.find_element(By.CLASS_NAME, "result-window")
           assert "users" in result_window.text

Test Factories and Fixtures
----------------------------

Factory Boy Integration
~~~~~~~~~~~~~~~~~~~~~~~

**Creating Test Factories:**

.. code-block:: python

   # tests/factories.py
   import factory
   from factory.django import DjangoModelFactory
   from faker import Faker
   from tests.models import User, Post, Category
   
   fake = Faker()
   
   class UserFactory(DjangoModelFactory):
       class Meta:
           model = User
       
       username = factory.Sequence(lambda n: f"user{n}")
       email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
       first_name = factory.Faker('first_name')
       last_name = factory.Faker('last_name')
       is_active = True
       
       @factory.post_generation
       def password(obj, create, extracted, **kwargs):
           if not create:
               return
           
           password = extracted or 'defaultpassword123'
           obj.set_password(password)
           obj.save()
   
   class CategoryFactory(DjangoModelFactory):
       class Meta:
           model = Category
       
       name = factory.Faker('word')
       slug = factory.LazyAttribute(lambda obj: obj.name.lower())
       description = factory.Faker('text', max_nb_chars=200)
   
   class PostFactory(DjangoModelFactory):
       class Meta:
           model = Post
       
       title = factory.Faker('sentence', nb_words=4)
       content = factory.Faker('text', max_nb_chars=1000)
       author = factory.SubFactory(UserFactory)
       category = factory.SubFactory(CategoryFactory)
       published = True
       
       @factory.lazy_attribute
       def slug(self):
           return self.title.lower().replace(' ', '-')

**Using Factories in Tests:**

.. code-block:: python

   class TestWithFactories(TestCase):
       def test_user_creation_with_factory(self):
           """Test creating users with factory."""
           user = UserFactory()
           
           assert user.username.startswith('user')
           assert '@example.com' in user.email
           assert user.is_active
       
       def test_post_with_relationships(self):
           """Test creating posts with related objects."""
           post = PostFactory()
           
           assert post.author is not None
           assert post.category is not None
           assert post.published is True
       
       def test_batch_creation(self):
           """Test creating multiple objects with factory."""
           users = UserFactory.create_batch(5)
           posts = PostFactory.create_batch(10, author=users[0])
           
           assert len(users) == 5
           assert len(posts) == 10
           assert all(post.author == users[0] for post in posts)

Pytest Fixtures
~~~~~~~~~~~~~~~~

**Creating Reusable Fixtures:**

.. code-block:: python

   # tests/conftest.py
   import pytest
   from tests.factories import UserFactory, PostFactory, CategoryFactory
   
   @pytest.fixture
   def user():
       """Fixture providing a test user."""
       return UserFactory()
   
   @pytest.fixture
   def admin_user():
       """Fixture providing an admin user."""
       return UserFactory(is_staff=True, is_superuser=True)
   
   @pytest.fixture
   def category():
       """Fixture providing a test category."""
       return CategoryFactory()
   
   @pytest.fixture
   def post(user, category):
       """Fixture providing a test post with relationships."""
       return PostFactory(author=user, category=category)
   
   @pytest.fixture
   def posts_with_users():
       """Fixture providing multiple posts with different users."""
       users = UserFactory.create_batch(3)
       posts = []
       for user in users:
           posts.extend(PostFactory.create_batch(2, author=user))
       return posts
   
   @pytest.fixture
   def graphql_client():
       """Fixture providing a GraphQL client."""
       from django.test import Client
       return Client()

**Using Fixtures in Tests:**

.. code-block:: python

   def test_user_posts(user, graphql_client):
       """Test querying user posts using fixtures."""
       # Create posts for the user
       PostFactory.create_batch(3, author=user)
       
       query = '''
       query GetUserPosts($userId: ID!) {
           user(id: $userId) {
               posts {
                   edges {
                       node {
                           title
                       }
                   }
               }
           }
       }
       '''
       
       response = graphql_client.post(
           '/graphql/',
           {'query': query, 'variables': {'userId': str(user.id)}},
           content_type='application/json'
       )
       
       data = response.json()
       assert len(data['data']['user']['posts']['edges']) == 3

Mocking and Patching
--------------------

External Service Mocking
~~~~~~~~~~~~~~~~~~~~~~~~

**Mocking External APIs:**

.. code-block:: python

   from unittest.mock import Mock, patch
   import pytest
   
   class TestExternalIntegrations:
       @patch('django_graphql_auto.services.external_api.requests.get')
       def test_external_api_success(self, mock_get):
           """Test successful external API call."""
           # Mock successful response
           mock_response = Mock()
           mock_response.status_code = 200
           mock_response.json.return_value = {
               'status': 'success',
               'data': {'id': 123, 'name': 'Test'}
           }
           mock_get.return_value = mock_response
           
           # Test the integration
           from django_graphql_auto.services import external_api
           result = external_api.fetch_data('test-id')
           
           assert result['status'] == 'success'
           assert result['data']['id'] == 123
           mock_get.assert_called_once_with('https://api.example.com/data/test-id')
       
       @patch('django_graphql_auto.services.external_api.requests.get')
       def test_external_api_failure(self, mock_get):
           """Test external API failure handling."""
           # Mock failed response
           mock_response = Mock()
           mock_response.status_code = 500
           mock_response.raise_for_status.side_effect = Exception("Server Error")
           mock_get.return_value = mock_response
           
           # Test error handling
           from django_graphql_auto.services import external_api
           with pytest.raises(Exception):
               external_api.fetch_data('test-id')

Database Mocking
~~~~~~~~~~~~~~~~

**Mocking Database Operations:**

.. code-block:: python

   from unittest.mock import patch, Mock
   
   class TestDatabaseMocking:
       @patch('django_graphql_auto.models.User.objects.get')
       def test_user_not_found_handling(self, mock_get):
           """Test handling of user not found scenarios."""
           # Mock User.DoesNotExist exception
           mock_get.side_effect = User.DoesNotExist("User not found")
           
           # Test resolver behavior
           from django_graphql_auto.resolvers import UserResolver
           resolver = UserResolver()
           
           with pytest.raises(User.DoesNotExist):
               resolver.resolve_user(Mock(), id=99999)
           
           mock_get.assert_called_once_with(id=99999)

Continuous Integration Testing
------------------------------

GitHub Actions Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**CI/CD Pipeline Configuration:**

.. code-block:: yaml

   # .github/workflows/test.yml
   name: Test Suite
   
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
   
       steps:
       - uses: actions/checkout@v3
       
       - name: Set up Python ${{ matrix.python-version }}
         uses: actions/setup-python@v3
         with:
           python-version: ${{ matrix.python-version }}
       
       - name: Install dependencies
         run: |
           python -m pip install --upgrade pip
           pip install Django==${{ matrix.django-version }}
           pip install -e ".[dev]"
       
       - name: Run linting
         run: |
           flake8 django_graphql_auto tests
           black --check django_graphql_auto tests
           isort --check-only django_graphql_auto tests
       
       - name: Run tests
         run: |
           pytest --cov=django_graphql_auto --cov-report=xml
         env:
           DATABASE_URL: postgres://postgres:postgres@localhost/test_db
       
       - name: Upload coverage to Codecov
         uses: codecov/codecov-action@v3
         with:
           file: ./coverage.xml

Test Coverage Reporting
~~~~~~~~~~~~~~~~~~~~~~~

**Coverage Configuration:**

.. code-block:: ini

   # .coveragerc
   [run]
   source = django_graphql_auto
   omit = 
       */migrations/*
       */tests/*
       */venv/*
       */env/*
       manage.py
       setup.py
   
   [report]
   exclude_lines =
       pragma: no cover
       def __repr__
       raise AssertionError
       raise NotImplementedError
       if __name__ == .__main__.:
   
   [html]
   directory = htmlcov

**Coverage Commands:**

.. code-block:: bash

   # Run tests with coverage
   coverage run -m pytest
   
   # Generate coverage report
   coverage report
   
   # Generate HTML coverage report
   coverage html
   
   # Check coverage threshold
   coverage report --fail-under=90

Testing Best Practices
-----------------------

Test Organization
~~~~~~~~~~~~~~~~~

**Directory Structure:**

.. code-block:: text

   tests/
   ├── __init__.py
   ├── conftest.py              # Pytest configuration and fixtures
   ├── settings.py              # Test settings
   ├── factories.py             # Factory Boy factories
   ├── models.py                # Test models
   ├── unit/                    # Unit tests
   │   ├── __init__.py
   │   ├── test_models.py
   │   ├── test_schema.py
   │   ├── test_resolvers.py
   │   └── test_utils.py
   ├── integration/             # Integration tests
   │   ├── __init__.py
   │   ├── test_api.py
   │   ├── test_database.py
   │   └── test_middleware.py
   ├── e2e/                     # End-to-end tests
   │   ├── __init__.py
   │   └── test_workflows.py
   └── performance/             # Performance tests
       ├── __init__.py
       ├── test_load.py
       └── test_memory.py

Test Naming Conventions
~~~~~~~~~~~~~~~~~~~~~~~

**Naming Guidelines:**

.. code-block:: python

   # Good test names - descriptive and specific
   def test_should_create_user_with_valid_data():
       pass
   
   def test_should_raise_validation_error_for_invalid_email():
       pass
   
   def test_should_return_empty_list_when_no_posts_exist():
       pass
   
   # Bad test names - vague and unclear
   def test_user():
       pass
   
   def test_validation():
       pass
   
   def test_posts():
       pass

Test Data Management
~~~~~~~~~~~~~~~~~~~~

**Test Data Best Practices:**

1. **Use Factories**: Create test data with Factory Boy
2. **Isolate Tests**: Each test should create its own data
3. **Clean Up**: Use database transactions or cleanup fixtures
4. **Realistic Data**: Use Faker for realistic test data
5. **Minimal Data**: Create only the data needed for each test

.. code-block:: python

   class TestDataManagement(TestCase):
       def setUp(self):
           """Set up test data for each test method."""
           self.user = UserFactory()
           self.category = CategoryFactory()
       
       def tearDown(self):
           """Clean up after each test method."""
           # Django TestCase handles database cleanup automatically
           pass
       
       def test_with_minimal_data(self):
           """Test with only the necessary data."""
           # Create only what's needed for this specific test
           post = PostFactory(author=self.user, category=self.category)
           
           # Test logic here
           assert post.author == self.user

Debugging Tests
---------------

Test Debugging Techniques
~~~~~~~~~~~~~~~~~~~~~~~~~

**Using pytest debugging:**

.. code-block:: bash

   # Run tests with verbose output
   pytest -v
   
   # Run specific test
   pytest tests/unit/test_models.py::TestUserModel::test_user_creation
   
   # Drop into debugger on failure
   pytest --pdb
   
   # Drop into debugger on first failure
   pytest -x --pdb
   
   # Show local variables in traceback
   pytest -l

**Using Django debugging:**

.. code-block:: python

   import pytest
   from django.test import TestCase
   from django.test.utils import override_settings
   
   class TestWithDebugging(TestCase):
       @override_settings(DEBUG=True)
       def test_with_debug_enabled(self):
           """Test with Django debug mode enabled."""
           # Test logic here
           pass
       
       def test_with_breakpoint(self):
           """Test with Python breakpoint for debugging."""
           user = UserFactory()
           
           # Set breakpoint for debugging
           breakpoint()  # Python 3.7+
           # or import pdb; pdb.set_trace()  # Older Python
           
           assert user.username is not None

Common Testing Patterns
-----------------------

Testing Async Code
~~~~~~~~~~~~~~~~~~

**Testing Async Resolvers:**

.. code-block:: python

   import pytest
   import asyncio
   from django_graphql_auto.resolvers import AsyncResolver
   
   class TestAsyncResolvers:
       @pytest.mark.asyncio
       async def test_async_user_resolver(self):
           """Test async user resolver."""
           resolver = AsyncResolver()
           user = UserFactory()
           
           result = await resolver.resolve_user_async(None, id=user.id)
           
           assert result == user
       
       @pytest.mark.asyncio
       async def test_concurrent_resolvers(self):
           """Test concurrent execution of async resolvers."""
           resolver = AsyncResolver()
           users = UserFactory.create_batch(5)
           
           # Execute resolvers concurrently
           tasks = [
               resolver.resolve_user_async(None, id=user.id)
               for user in users
           ]
           
           results = await asyncio.gather(*tasks)
           
           assert len(results) == 5
           assert all(result in users for result in results)

Testing Permissions
~~~~~~~~~~~~~~~~~~~

**Testing Access Control:**

.. code-block:: python

   from django.contrib.auth.models import Permission
   from django.contrib.contenttypes.models import ContentType
   
   class TestPermissions(TestCase):
       def setUp(self):
           self.user = UserFactory()
           self.admin_user = UserFactory(is_staff=True, is_superuser=True)
       
       def test_user_can_view_own_posts(self):
           """Test user can view their own posts."""
           post = PostFactory(author=self.user)
           
           # Test query with user context
           query = '''
           query GetPost($id: ID!) {
               post(id: $id) {
                   title
                   author {
                       username
                   }
               }
           }
           '''
           
           # Execute query as the post author
           result = self.execute_query_as_user(query, {'id': str(post.id)}, self.user)
           
           assert 'errors' not in result
           assert result['data']['post']['title'] == post.title
       
       def test_user_cannot_view_others_private_posts(self):
           """Test user cannot view other users' private posts."""
           other_user = UserFactory()
           private_post = PostFactory(author=other_user, is_private=True)
           
           query = '''
           query GetPost($id: ID!) {
               post(id: $id) {
                   title
               }
           }
           '''
           
           # Execute query as different user
           result = self.execute_query_as_user(query, {'id': str(private_post.id)}, self.user)
           
           assert 'errors' in result
           assert 'permission denied' in result['errors'][0]['message'].lower()

---

*This testing guide provides comprehensive coverage of testing strategies and best practices for Django GraphQL Auto. For more specific testing scenarios, refer to the test suite in the project repository.*