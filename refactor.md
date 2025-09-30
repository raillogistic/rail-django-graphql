# Django to Third-Party Library Refactoring Plan
## Project: rail_django_graphql

### 🎯 Objective
Transform the current Django project into a reusable third-party Django library named `rail_django_graphql`, hosted on GitHub and installable via pip from the GitHub repository.

---

### 📋 Refactoring Todo List

#### Phase 1: Analysis & Planning (High Priority)

- [ ] **Analyze Current Project Structure**
  - [ ] Identify core library components in current codebase
  - [ ] Map existing modules to library structure
  - [ ] Document dependencies and external requirements
  - [ ] Identify Django-specific vs library-agnostic code
  - [ ] Review current settings and configuration patterns

- [ ] **Create Repository Structure**
  - [ ] Set up new GitHub repository with proper directory layout
  - [ ] Create `deploy/` directory for deployment helpers
  - [ ] Create `docs/` directory for documentation
  - [ ] Create `tests/` directory for unit tests
  - [ ] Create `test_app/` directory for example Django application
  - [ ] Create `rail_django_graphql/` directory for the main library package
  - [ ] Add `.editorconfig`, `.pre-commit-config.yaml`, and `CONTRIBUTING.md`

- [ ] **Extract Core Library Components**
  - [ ] Move core GraphQL generation logic to `rail_django_graphql/`
  - [ ] Create proper `__init__.py` with version and public API exports
  - [ ] Implement Django `AppConfig` in `apps.py`
  - [ ] Extract generators, middleware, and core functionality
  - [ ] Ensure proper module imports and dependencies

#### Phase 2: Settings & Configuration (High Priority)

- [ ] **Implement Hierarchical Settings System**
  - [ ] Create `rail_django_graphql/settings.py` with library defaults
  - [ ] Add `conf.py` with a settings loader utility for merging overrides
  - [ ] Implement global override system via `DJANGO_GRAPHQL_AUTO` dictionary
  - [ ] Design schema-level override mechanism
  - [ ] Implement settings resolution with priority:
    - Schema-level overrides > Global overrides > Library defaults
  - [ ] Add settings validation, type hints, and error handling
  - [ ] Provide override signal for developers to hook into resolution

- [ ] **Create Modern Packaging Configuration**
  - [ ] Create `pyproject.toml` with setuptools/hatchling configuration
  - [ ] Define package metadata (name, version, description, author, classifiers)
  - [ ] Specify dependencies (Django 4+, Graphene v3)
  - [ ] Configure build system and installation requirements
  - [ ] Set up proper package discovery and inclusion rules

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

- [ ] **Migrate and Reorganize Tests**
  - [ ] Move relevant tests to `tests/` directory
  - [ ] Use `pytest-django` for cleaner tests
  - [ ] Add tests for settings resolution and hierarchy
  - [ ] Add tests for multiple schema support and overrides
  - [ ] Add compatibility tests for Django 4+ and Graphene v3
  - [ ] Add coverage reports and CI integration

- [ ] **Create Example Application**
  - [ ] Set up `test_app/` as a complete Django project
  - [ ] Create `manage.py` and project configuration
  - [ ] Add example models demonstrating library usage
  - [ ] Configure multiple GraphQL schemas with different settings
  - [ ] Demonstrate authentication and GraphiQL configuration
  - [ ] Include comprehensive usage examples

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

- [ ] Library can be installed via pip from GitHub
- [ ] Multiple GraphQL schemas work independently
- [ ] Settings hierarchy functions correctly
- [ ] All tests pass on Django 4+ and Graphene v3
- [ ] Documentation is comprehensive and clear
- [ ] Example application demonstrates all features
- [ ] Code follows Django and Python best practices
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

