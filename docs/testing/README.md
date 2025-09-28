# Testing Guide - Django GraphQL Auto

This guide provides comprehensive documentation for running and maintaining tests for the Django GraphQL Auto project.

## 📋 Table of Contents

- [Overview](#overview)
- [Configuration](#configuration)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Types](#test-types)
- [Fixtures and Utilities](#fixtures-and-utilities)
- [Reports and Metrics](#reports-and-metrics)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The Django GraphQL Auto test suite is designed to ensure quality, performance, and reliability of the automatic GraphQL schema generation system.

### Test Objectives

- **Code Quality**: Validation of business logic and functionality
- **Performance**: Measurement of execution times and memory usage
- **Reliability**: Concurrency and error handling tests
- **Security**: Validation of protection mechanisms
- **Regression**: Prevention of regressions during modifications

### Test Coverage

- ✅ **Unit Tests**: Individual components
- ✅ **Integration Tests**: Complete workflow
- ✅ **Performance Tests**: Optimization and scalability
- ✅ **Security Tests**: Vulnerabilities and protections
- ✅ **Regression Tests**: Feature stability

## ⚙️ Configuration

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-django pytest-cov pytest-xdist
pip install factory-boy faker
pip install coverage[toml]
```

### Environment Variables

```bash
# Basic configuration
export DJANGO_SETTINGS_MODULE=tests.settings
export TESTING=True

# Optional configuration
export DEBUG=False
export DATABASE_URL=sqlite:///test.db
```

### Django Configuration

The `tests/settings.py` file contains test-specific configuration:

```python
# In-memory database for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Local cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
```

## 🏗️ Test Structure

```
tests/
├── __init__.py                 # Test package configuration
├── settings.py                 # Django configuration for tests
├── conftest.py                 # Global pytest configuration
├── urls.py                     # Test URLs
├── schema.py                   # Test GraphQL schema
├── models.py                   # Test models
├── apps.py                     # Test app configuration
├── admin.py                    # Admin interface for tests
├── views.py                    # Test views and utilities
│
├── fixtures/                   # Fixtures and utilities
│   ├── __init__.py
│   ├── test_data_fixtures.py   # Test data
│   ├── test_utilities.py       # Test utilities
│   ├── mocks_and_stubs.py      # Mocks and stubs
│   └── assertion_helpers.py    # Assertion helpers
│
├── test_core/                  # Core component tests
│   ├── __init__.py
│   ├── test_model_introspector.py
│   ├── test_type_generator.py
│   ├── test_query_generator.py
│   └── test_mutation_generator.py
│
├── test_generators/            # Generator tests
│   ├── __init__.py
│   ├── test_schema_generator.py
│   ├── test_field_resolver.py
│   └── test_relationship_handler.py
│
├── test_integration/           # Integration tests
│   ├── __init__.py
│   ├── test_complete_workflow.py
│   ├── test_django_integration.py
│   └── test_graphql_execution.py
│
├── test_business_methods/      # Business method tests
│   ├── __init__.py
│   ├── test_method_detection.py
│   ├── test_method_integration.py
│   └── test_custom_resolvers.py
│
├── test_edge_cases/            # Edge case tests
│   ├── __init__.py
│   ├── test_error_handling.py
│   ├── test_invalid_models.py
│   └── test_complex_relationships.py
│
├── test_performance/           # Performance tests
│   ├── __init__.py
│   ├── test_memory_usage.py
│   ├── test_query_optimization.py
│   └── test_concurrent_requests.py
│
└── management/                 # Management commands
    └── commands/
        └── run_test_suite.py   # Complete execution command
```

## 🚀 Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Tests with coverage
pytest --cov=django_graphql_auto --cov-report=html

# Parallel tests
pytest -n auto

# Tests with detailed report
pytest -v --tb=short

# Tests for a specific module
pytest tests/test_core/

# Tests with tags
pytest -m "unit"
pytest -m "not slow"
```

### Django Management Command

```bash
# Complete execution with reports
python manage.py run_test_suite --coverage --performance

# Tests with custom configuration
python manage.py run_test_suite \
    --parallel 4 \
    --output-dir reports \
    --exclude-tags slow
```

### pytest.ini Configuration

```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = tests.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = tests
addopts = 
    --reuse-db
    --nomigrations
    --cov=django_graphql_auto
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --maxfail=5
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow tests
    database: Tests requiring database
```

## 🧪 Test Types

### Unit Tests

Tests of individual components in isolation.

```python
@pytest.mark.unit
def test_model_introspector_get_fields():
    """Test for retrieving model fields."""
    introspector = ModelIntrospector()
    fields = introspector.get_fields(TestModel)
    
    assert 'name' in fields
    assert fields['name']['type'] == 'CharField'
```

### Integration Tests

Tests of the complete schema generation workflow.

```python
@pytest.mark.integration
def test_complete_schema_generation():
    """Test for complete schema generation."""
    generator = AutoSchemaGenerator()
    schema = generator.generate_schema([TestModel])
    
    assert schema is not None
    assert_schema_has_type(schema, 'TestModelType')
```

### Performance Tests

Measurement of performance and resource usage.

```python
@pytest.mark.performance
def test_schema_generation_performance():
    """Test for schema generation performance."""
    with PerformanceProfiler() as profiler:
        generator = AutoSchemaGenerator()
        schema = generator.generate_schema(large_model_list)
    
    assert profiler.execution_time < 5.0  # 5 seconds max
    assert profiler.memory_usage < 100 * 1024 * 1024  # 100MB max
```

### Security Tests

Validation of security mechanisms.

```python
@pytest.mark.security
def test_sql_injection_protection():
    """Test for SQL injection protection."""
    malicious_query = "'; DROP TABLE users; --"
    
    with pytest.raises(ValidationError):
        execute_graphql_query(malicious_query)
```

## 🔧 Fixtures and Utilities

### Data Fixtures

```python
@pytest.fixture
def sample_authors():
    """Creates test authors."""
    return AuthorFactory.create_batch(5)

@pytest.fixture
def complete_dataset():
    """Creates a complete dataset."""
    return create_complete_test_dataset()
```

### Test Utilities

```python
# GraphQL test client
client = GraphQLTestClient(schema)
result = client.execute(query, variables)

# GraphQL assertions
assert_graphql_success(result)
assert_graphql_error(result, "Field not found")

# Performance profiling
with PerformanceProfiler() as profiler:
    # Code to profile
    pass
```

### Mocks and Stubs

```python
@pytest.fixture
def mock_model_introspector():
    """Mock for ModelIntrospector."""
    with patch('django_graphql_auto.core.ModelIntrospector') as mock:
        mock.return_value.get_fields.return_value = {}
        yield mock
```

## 📊 Reports and Metrics

### Coverage Report

```bash
# Generate HTML report
pytest --cov=django_graphql_auto --cov-report=html

# Terminal report
pytest --cov=django_graphql_auto --cov-report=term-missing

# XML report (for CI/CD)
pytest --cov=django_graphql_auto --cov-report=xml
```

### Performance Metrics

Performance tests generate detailed metrics:

- **Execution time**: Duration of operations
- **Memory usage**: RAM consumption
- **DB queries**: Number and optimization
- **Concurrency**: Performance under load

### Custom Reports

```bash
# Generate complete reports
python manage.py run_test_suite \
    --coverage \
    --performance \
    --output-dir reports/$(date +%Y%m%d_%H%M%S)
```

## ✅ Best Practices

### Writing Tests

1. **Descriptive Naming**
   ```python
   def test_model_introspector_handles_foreign_key_relationships():
       """Specific and descriptive test."""
   ```

2. **AAA Structure (Arrange, Act, Assert)**
   ```python
   def test_example():
       # Arrange
       model = TestModel.objects.create(name="test")
       
       # Act
       result = introspector.analyze(model)
       
       # Assert
       assert result.is_valid
   ```

3. **Independent Tests**
   - Each test must be independent
   - Use fixtures for isolation
   - Clean up after each test

4. **Clear Assertions**
   ```python
   # Good
   assert user.is_active is True
   assert len(results) == 3
   
   # Avoid
   assert user
   assert results
   ```

### Test Performance

1. **Fast Tests**
   - Use mocks for external dependencies
   - In-memory database
   - Avoid unnecessary sleep()

2. **Parallelization**
   ```bash
   pytest -n auto  # Uses all available CPUs
   ```

3. **DB Reuse**
   ```bash
   pytest --reuse-db  # Reuses DB between executions
   ```

### Organization

1. **Logical Grouping**
   - Tests by component
   - Tests by functionality
   - Tests by level (unit/integration)

2. **Tags and Markers**
   ```python
   @pytest.mark.slow
   @pytest.mark.database
   def test_complex_operation():
       pass
   ```

3. **Documentation**
   - Explanatory docstrings
   - Comments for complex logic
   - README for each test module

## 🔍 Troubleshooting

### Common Issues

#### Slow Tests

```bash
# Identify slow tests
pytest --durations=10

# Exclude slow tests
pytest -m "not slow"
```

#### Database Errors

```python
# Force creation of new DB
pytest --create-db

# Reset migrations
pytest --nomigrations
```

#### Memory Issues

```python
# Profile memory usage
pytest --memprof

# Limit parallel tests
pytest -n 2  # Instead of -n auto
```

#### Concurrency Errors

```python
# Sequential tests for debugging
pytest --forked

# Test isolation
pytest --lf  # Last failures only
```

### Debugging

```python
# Debug mode
pytest -s --pdb

# Detailed logs
pytest --log-cli-level=DEBUG

# Stop at first failure
pytest -x
```

### Diagnostic Tools

```bash
# System information
python manage.py run_test_suite --debug-mode

# Health check
curl http://localhost:8000/test/health/

# Real-time metrics
curl http://localhost:8000/test/status/
```

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [GraphQL Testing Best Practices](https://graphql.org/learn/testing/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)

## 🤝 Contributing

To contribute to tests:

1. Follow naming conventions
2. Add tests for new features
3. Maintain coverage > 80%
4. Document complex tests
5. Run complete suite before commit

```bash
# Pre-commit verification
python manage.py run_test_suite --coverage --performance
```