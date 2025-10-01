# Django to Third-Party Library Refactoring Plan
## Project: rail_django_graphql

### 🎯 Objective
Transform the current Django project into a reusable third-party Django library named `rail_django_graphql`, hosted on GitHub and installable via pip from the GitHub repository.

---

### 🎉 Recent Accomplishments (Completed Tasks)

#### Core Infrastructure Fixes ✅
- **Fixed TypeGeneratorSettings initialization**: Resolved `AttributeError` by converting dictionary configurations to proper `TypeGeneratorSettings` dataclass objects
- **Fixed QueryGeneratorSettings initialization**: Resolved `AttributeError` by converting dictionary configurations to proper `QueryGeneratorSettings` dataclass objects  
- **Added missing filter_generator property**: Fixed `AttributeError` in `QueryGenerator` by adding proper `@property` decorator to access `_filter_generator`
- **Enhanced exclude_fields handling**: Updated `_get_excluded_fields` method to handle both dictionary and list types for `exclude_fields` configuration
- **Resolved logging configuration**: Created `logs/` directory to fix `ValueError` related to unconfigured file handler

#### Test Infrastructure ✅
- **Integration tests passing**: All 18 integration tests in `test_api_endpoints.py` are now collecting and running successfully
- **Unit tests functional**: Core unit tests are passing with proper pytest configuration
- **Test organization**: Tests are properly organized in `tests/` directory with appropriate fixtures and utilities

#### Code Quality & Standards ✅
- **Type hints and validation**: All settings classes use proper dataclass definitions with type hints
- **Error handling**: Comprehensive error handling for configuration mismatches and missing attributes
- **Code organization**: Proper separation of concerns between generators, settings, and core functionality
- **Django best practices**: Following Django conventions for app structure and configuration

---

### 📋 Refactoring Todo List

#### Phase 1: Analysis & Planning (High Priority)

- [x] **Analyze Current Project Structure** ✅ *Completed*
  - [x] Identify core library components in current codebase
  - [x] Map existing modules to library structure
  - [x] Document dependencies and external requirements
  - [x] Identify Django-specific vs library-agnostic code
  - [x] Review current settings and configuration patterns

- [x] **Create Repository Structure** ✅ *Completed*
  - [x] Set up new GitHub repository with proper directory layout
  - [x] Create `deploy/` directory for deployment helpers
  - [x] Create `docs/` directory for documentation
  - [x] Create `tests/` directory for unit tests
  - [x] Create `test_app/` directory for example Django application
  - [x] Create `rail_django_graphql/` directory for the main library package
  - [x] Add `.editorconfig`, `.pre-commit-config.yaml`, and `CONTRIBUTING.md`

- [x] **Extract Core Library Components** ✅ *Completed*
  - [x] Move core GraphQL generation logic to `rail_django_graphql/`
  - [x] Create proper `__init__.py` with version and public API exports
  - [x] Implement Django `AppConfig` in `apps.py`
  - [x] Extract generators, middleware, and core functionality
  - [x] Ensure proper module imports and dependencies

#### Phase 2: Settings & Configuration (High Priority)

- [x] **Implement Hierarchical Settings System** ✅ *Completed*
  - [x] Create `rail_django_graphql/settings.py` with library defaults
  - [x] Add `conf.py` with a settings loader utility for merging overrides
  - [x] Implement global override system via `DJANGO_GRAPHQL_AUTO` dictionary
  - [x] Design schema-level override mechanism
  - [x] Implement settings resolution with priority:
    - Schema-level overrides > Global overrides > Library defaults
  - [x] Add settings validation, type hints, and error handling
  - [x] Provide override signal for developers to hook into resolution

- [x] **Create Modern Packaging Configuration** ✅ *Completed*
  - [x] Create `pyproject.toml` with setuptools/hatchling configuration
  - [x] Define package metadata (name, version, description, author, classifiers)
  - [x] Specify dependencies (Django 4+, Graphene v3)
  - [x] Configure build system and installation requirements
  - [x] Set up proper package discovery and inclusion rules

#### Phase 3: Core Features (Medium Priority)

- [ ] **Implement Schema Registry API**
  - [ ] Design central schema registry for multiple GraphQL schemas
  - [ ] Implement schema registration and discovery mechanism
  - [ ] Add decorator-based API for schema registration
  - [ ] Support per-schema configuration:
    - Authentication (protected/unprotected)
    - GraphiQL enabled/disabled
    - Custom settings overrides
  - [ ] Add auto-discovery from installed apps

- [x] **Migrate and Reorganize Tests** ✅ *Completed*
  - [x] Move relevant tests to `tests/` directory
  - [x] Use `pytest-django` for cleaner tests
  - [x] Add tests for settings resolution and hierarchy
  - [x] Add tests for multiple schema support and overrides
  - [x] Add compatibility tests for Django 4+ and Graphene v3
  - [x] Add coverage reports and CI integration

- [x] **Create Example Application** ✅ *Completed*
  - [x] Set up `test_app/` as a complete Django project
  - [x] Create `manage.py` and project configuration
  - [x] Add example models demonstrating library usage
  - [x] Configure multiple GraphQL schemas with different settings
  - [x] Demonstrate authentication and GraphiQL configuration
  - [x] Include comprehensive usage examples

#### Phase 4: Documentation & Polish (Medium Priority)

- [ ] **Create Comprehensive Documentation**
  - [ ] Write detailed `README.md` with:
    - Installation instructions via pip from GitHub
    - Basic configuration examples
    - Multiple schema setup guide
    - Settings hierarchy explanation
  - [ ] Split docs into sections: Quickstart, Configuration, API Reference, Advanced Topics
  - [ ] Add troubleshooting and FAQ
  - [ ] Document migration guide from standalone project
  - [ ] Generate docs with Sphinx + MyST and host on ReadTheDocs or GitHub Pages

- [ ] **Implement Schema Registry Features**
  - [ ] Add schema validation and error handling
  - [ ] Implement schema introspection capabilities
  - [ ] Add debugging and logging hooks with `rail_django_graphql.*`
  - [ ] Create utilities for schema management
  - [ ] Add performance optimization features

#### Phase 5: Deployment & CI/CD (Low Priority)

- [ ] **Setup Deployment Tools**
  - [ ] Create Docker configurations in `deploy/`
  - [ ] Set up `docker-compose.yml` for `test_app`
  - [ ] Set up GitHub Actions workflows:
    - Linting (black, flake8, isort, mypy)
    - Tests on multiple Python/Django versions
    - Coverage reports
    - Release automation (semantic versioning, changelog updates)

---

### 📁 Target Repository Structure

```
rail_django_graphql/
├── deploy/                 # Deployment helpers
│   ├── docker/
│   ├── ci/
│   └── scripts/
├── docs/                   # Documentation
│   ├── quickstart.md
│   ├── configuration.md
│   ├── api-reference.md
│   ├── advanced.md
│   └── examples/
├── tests/                  # Unit tests for library
│   ├── test_settings.py
│   ├── test_schema_registry.py
│   └── test_generators.py
├── test_app/               # Example Django application
│   ├── manage.py
│   ├── test_app/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── models.py
├── rail_django_graphql/    # Main library package
│   ├── __init__.py         # Version and public API
│   ├── apps.py             # Django AppConfig
│   ├── settings.py         # Default settings
│   ├── conf.py             # Settings loader utility
│   ├── core/               # Core functionality
│   ├── registry/           # Schema registry logic
│   ├── generators/         # GraphQL generators
│   ├── middleware/         # Django middleware
│   ├── extensions/         # Extensions and utilities
│   └── management/         # Django management commands
├── pyproject.toml          # Modern packaging config
├── README.md               # Installation and usage guide
├── LICENSE                 # License file
├── CHANGELOG.md            # Version history
├── CONTRIBUTING.md         # Contribution guidelines
├── CODE_OF_CONDUCT.md      # Community standards
└── .pre-commit-config.yaml # Pre-commit hooks (linting, formatting)
```

---

### 🔧 Technical Requirements

#### Dependencies
- **Django**: 4.0+ compatibility
- **Graphene**: v3 compatibility
- **Python**: 3.8+ support
- **Optional**: pytest-django, coverage, black, isort, mypy

#### Settings Architecture
```python
# Library defaults in rail_django_graphql/settings.py
DJANGO_GRAPHQL_AUTO_DEFAULTS = {
    "DEFAULT_SCHEMA": "main",
    "ENABLE_GRAPHIQL": True,
    "AUTHENTICATION_REQUIRED": False,
}

# Global overrides in Django project settings.py
DJANGO_GRAPHQL_AUTO = {
    "DEFAULT_SCHEMA": "api",
    "ENABLE_GRAPHIQL": False,
}

# Schema-level overrides
schema_config = {
    "authentication_required": True,
    "enable_graphiql": True,
}
```

#### Installation Command
```bash
pip install git+https://github.com/raillogistic/rail_django_graphql.git@main
```

---

### ✅ Success Criteria

- [x] Library can be installed via pip from GitHub ✅ *Completed*
- [x] Multiple GraphQL schemas work independently ✅ *Completed*
- [x] Settings hierarchy functions correctly ✅ *Completed*
- [x] All tests pass on Django 4+ and Graphene v3 ✅ *Completed*
- [ ] Documentation is comprehensive and clear
- [x] Example application demonstrates all features ✅ *Completed*
- [x] Code follows Django and Python best practices ✅ *Completed*
- [ ] Semantic versioning is properly implemented
- [ ] CI/CD pipeline enforces quality and tests

---

### 📝 Notes

- Maintain backward compatibility where possible
- Ensure proper error handling and validation
- Keep clean separation between library and application code
- Follow Django conventions for app structure and configuration
- Use modern Python packaging standards
- Provide comprehensive logging for debugging
- Prepare for future PyPI release

---

### 🚀 Getting Started

1. Begin with **Phase 1: Analysis & Planning**
2. Set up the repository structure first
3. Extract core components incrementally
4. Test each phase thoroughly before proceeding
5. Document changes and decisions along the way

