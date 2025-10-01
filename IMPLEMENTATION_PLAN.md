# Implementation Plan - Project Separation

## 📋 Overview

This document outlines the detailed implementation plan for separating the current monolithic project into two distinct projects:

1. **`rail-django-graphql`** - Standalone library
2. **`django-graphql-boilerplate`** - Boilerplate project using the library

## 🎯 Implementation Strategy

### Phase 1: Library Creation (High Priority)
**Estimated Time**: 2-3 days

#### Step 1.1: Create Library Repository Structure
```bash
# Create new directory for the library
mkdir ../rail-django-graphql
cd ../rail-django-graphql

# Initialize git repository
git init
git remote add origin https://github.com/raillogistic/rail-django-graphql.git

# Create basic structure
mkdir -p rail_django_graphql/{core,generators,middleware,permissions,extensions,plugins}
mkdir -p rail_django_graphql/{introspection,validation,debugging,management/commands}
mkdir -p rail_django_graphql/{api,templates,static,views}
mkdir -p tests/{unit,integration,performance,e2e,fixtures}
mkdir -p docs/{source,requirements}
mkdir -p examples/{basic,advanced,integration}
mkdir -p scripts
mkdir -p requirements
mkdir -p .github/workflows
```

#### Step 1.2: Copy Core Library Files
```bash
# Copy main library package
cp -r rail_django_graphql/* ../rail-django-graphql/rail_django_graphql/

# Copy configuration files
cp pyproject.toml ../rail-django-graphql/
cp setup.py ../rail-django-graphql/
cp MANIFEST.in ../rail-django-graphql/
cp requirements.txt ../rail-django-graphql/requirements/base.txt

# Copy documentation
cp README.md ../rail-django-graphql/
cp LICENSE ../rail-django-graphql/
cp CONTRIBUTING.md ../rail-django-graphql/
cp CODE_OF_CONDUCT.md ../rail-django-graphql/

# Copy tests related to library
cp -r tests/test_rail_django_graphql/* ../rail-django-graphql/tests/
```

#### Step 1.3: Update Library Configuration
- [ ] Update `pyproject.toml` with library-specific configuration
- [ ] Update `setup.py` for library packaging
- [ ] Create library-specific `__init__.py` with proper exports
- [ ] Update `MANIFEST.in` for library files only
- [ ] Create library-specific requirements files

#### Step 1.4: Create Library Documentation
- [ ] Create library-specific README.md
- [ ] Set up Sphinx documentation structure
- [ ] Create API reference documentation
- [ ] Create usage examples
- [ ] Create installation guide

#### Step 1.5: Set Up Library Testing
- [ ] Configure pytest for library testing
- [ ] Create test fixtures for library
- [ ] Set up coverage reporting
- [ ] Create CI/CD pipeline for library testing

### Phase 2: Boilerplate Creation (High Priority)
**Estimated Time**: 2-3 days

#### Step 2.1: Create Boilerplate Repository Structure
```bash
# Create new directory for the boilerplate
mkdir ../django-graphql-boilerplate
cd ../django-graphql-boilerplate

# Initialize git repository
git init
git remote add origin https://github.com/raillogistic/django-graphql-boilerplate.git

# Create Django project structure
mkdir -p apps/{core,users,blog,ecommerce}
mkdir -p config/settings
mkdir -p templates/{admin,registration,graphql,errors}
mkdir -p static/{css,js,images,fonts}
mkdir -p media/uploads/{images,documents,avatars}
mkdir -p locale/{en,fr}/LC_MESSAGES
mkdir -p tests/{integration,e2e,performance,fixtures}
mkdir -p deploy/{docker,kubernetes,nginx,scripts}
mkdir -p docs
mkdir -p scripts
mkdir -p requirements
mkdir -p .github/workflows
```

#### Step 2.2: Copy Boilerplate Files
```bash
# Copy Django project files
cp manage.py ../django-graphql-boilerplate/
cp -r test_app/* ../django-graphql-boilerplate/apps/

# Copy configuration
cp -r config/* ../django-graphql-boilerplate/config/
cp docker-compose.yml ../django-graphql-boilerplate/
cp Dockerfile ../django-graphql-boilerplate/
cp .env.example ../django-graphql-boilerplate/

# Copy deployment files
cp -r deploy/* ../django-graphql-boilerplate/deploy/

# Copy templates and static files
cp -r templates/* ../django-graphql-boilerplate/templates/
cp -r static/* ../django-graphql-boilerplate/static/
```

#### Step 2.3: Update Boilerplate Configuration
- [ ] Update Django settings to use `rail-django-graphql` library
- [ ] Configure GraphQL schema using the library
- [ ] Update URL configurations
- [ ] Update Docker configurations
- [ ] Create environment configuration examples

#### Step 2.4: Transform test_app to Example Apps
- [ ] Rename `test_app` to `apps/blog`
- [ ] Create `apps/users` for user management
- [ ] Create `apps/ecommerce` for e-commerce example
- [ ] Create `apps/core` for shared functionality
- [ ] Update models with GraphQL decorators

#### Step 2.5: Create Boilerplate Documentation
- [ ] Create boilerplate-specific README.md
- [ ] Create installation guide
- [ ] Create configuration guide
- [ ] Create deployment guide
- [ ] Create customization guide

### Phase 3: Integration & Testing (High Priority)
**Estimated Time**: 1-2 days

#### Step 3.1: Library Integration Testing
- [ ] Install library in boilerplate project
- [ ] Test all GraphQL functionality
- [ ] Test authentication and permissions
- [ ] Test filtering and pagination
- [ ] Test mutations and subscriptions

#### Step 3.2: End-to-End Testing
- [ ] Test complete user workflows
- [ ] Test admin functionality
- [ ] Test API endpoints
- [ ] Test Docker deployment
- [ ] Test production configuration

#### Step 3.3: Performance Testing
- [ ] Test query performance
- [ ] Test memory usage
- [ ] Test concurrent requests
- [ ] Test database optimization

### Phase 4: Documentation & Finalization (Medium Priority)
**Estimated Time**: 1-2 days

#### Step 4.1: Complete Documentation
- [ ] Finalize library documentation
- [ ] Finalize boilerplate documentation
- [ ] Create migration guide
- [ ] Create troubleshooting guide
- [ ] Create contribution guidelines

#### Step 4.2: CI/CD Setup
- [ ] Set up GitHub Actions for library
- [ ] Set up GitHub Actions for boilerplate
- [ ] Configure PyPI publishing
- [ ] Configure automated testing
- [ ] Configure security scanning

#### Step 4.3: Release Preparation
- [ ] Create CHANGELOG.md for both projects
- [ ] Tag initial releases
- [ ] Publish library to PyPI
- [ ] Create GitHub releases
- [ ] Update project URLs and links

## 📁 File Mapping

### Library Files (rail-django-graphql)
```
Current Location → New Location
rail_django_graphql/ → rail_django_graphql/
setup.py → setup.py (updated)
pyproject.toml → pyproject.toml (updated)
requirements.txt → requirements/base.txt
tests/test_rail_django_graphql/ → tests/
docs/library/ → docs/
examples/library/ → examples/
.github/workflows/library.yml → .github/workflows/test.yml
```

### Boilerplate Files (django-graphql-boilerplate)
```
Current Location → New Location
test_app/ → apps/blog/
manage.py → manage.py
config/ → config/
templates/ → templates/
static/ → static/
docker-compose.yml → docker-compose.yml
Dockerfile → Dockerfile
deploy/ → deploy/
tests/integration/ → tests/integration/
docs/boilerplate/ → docs/
.github/workflows/boilerplate.yml → .github/workflows/test.yml
```

## 🔧 Configuration Updates

### Library pyproject.toml
```toml
[project]
name = "rail-django-graphql"
version = "1.0.0"
description = "Automatic GraphQL schema generation for Django with advanced features"
dependencies = [
    "Django>=4.2.0",
    "graphene>=3.4.0",
    "graphene-django>=3.2.0",
    "django-filter>=24.0.0",
]
```

### Boilerplate requirements.txt
```txt
# Core library
rail-django-graphql>=1.0.0

# Django
Django>=4.2.0
djangorestframework>=3.14.0

# Database
psycopg2-binary>=2.9.0

# Additional features
Pillow>=10.0.0
redis>=4.0.0
celery>=5.3.0
```

## 🧪 Testing Strategy

### Library Testing
```python
# tests/conftest.py
import pytest
import django
from django.conf import settings
from django.test.utils import get_runner

def pytest_configure():
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'rail_django_graphql',
            'graphene_django',
        ],
        SECRET_KEY='test-secret-key',
    )
    django.setup()
```

### Boilerplate Testing
```python
# tests/conftest.py
import pytest
from django.contrib.auth import get_user_model
from apps.blog.models import Post, Category
from apps.ecommerce.models import Product

User = get_user_model()

@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def blog_post(user):
    category = Category.objects.create(name='Test Category')
    return Post.objects.create(
        title='Test Post',
        content='Test content',
        author=user,
        category=category,
        status='published'
    )
```

## 📚 Documentation Structure

### Library Documentation
```
docs/
├── source/
│   ├── index.rst
│   ├── installation.rst
│   ├── quickstart.rst
│   ├── api/
│   ├── features/
│   └── advanced/
├── requirements.txt
└── Makefile
```

### Boilerplate Documentation
```
docs/
├── installation.md
├── configuration.md
├── deployment.md
├── api-examples.md
├── customization.md
└── troubleshooting.md
```

## 🚀 Deployment Strategy

### Library Deployment
1. **PyPI Publishing**: Automated via GitHub Actions
2. **Documentation**: Read the Docs integration
3. **Versioning**: Semantic versioning with git tags
4. **Testing**: Multi-version Django testing with tox

### Boilerplate Deployment
1. **Docker Images**: Multi-stage builds for production
2. **Kubernetes**: Complete K8s manifests
3. **Cloud Deployment**: AWS, GCP, Azure guides
4. **CI/CD**: Automated testing and deployment

## ⚠️ Migration Considerations

### Breaking Changes
- Import paths will change for library users
- Configuration structure may change
- Some internal APIs may be removed

### Migration Path
1. **Deprecation Warnings**: Add warnings for old import paths
2. **Compatibility Layer**: Maintain backward compatibility for one version
3. **Migration Guide**: Detailed step-by-step migration instructions
4. **Support**: Provide migration support for existing users

## 📊 Success Metrics

### Library Success
- [ ] Successfully published to PyPI
- [ ] All tests passing
- [ ] Documentation complete and accessible
- [ ] Example usage working
- [ ] Performance benchmarks met

### Boilerplate Success
- [ ] Quick setup (< 5 minutes)
- [ ] All example apps working
- [ ] Docker deployment successful
- [ ] Production-ready configuration
- [ ] Comprehensive documentation

### Integration Success
- [ ] Library installs correctly in boilerplate
- [ ] All GraphQL features working
- [ ] Performance requirements met
- [ ] Security requirements met
- [ ] User experience improved

## 🔄 Timeline

### Week 1: Library Creation
- Days 1-2: Repository setup and file migration
- Days 3-4: Configuration updates and testing
- Day 5: Documentation and CI/CD setup

### Week 2: Boilerplate Creation
- Days 1-2: Repository setup and app restructuring
- Days 3-4: Configuration and integration
- Day 5: Testing and documentation

### Week 3: Integration & Finalization
- Days 1-2: End-to-end testing
- Days 3-4: Documentation completion
- Day 5: Release preparation and publishing

---

This implementation plan provides a comprehensive roadmap for successfully separating the project into two distinct, well-structured repositories while maintaining functionality and improving maintainability.