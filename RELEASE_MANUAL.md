# Rail Django GraphQL - Release and Publishing Manual

This comprehensive manual provides step-by-step instructions for releasing and publishing the `rail-django-graphql` package to GitHub and PyPI.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Release Checklist](#pre-release-checklist)
3. [Version Management](#version-management)
4. [Local Build and Testing](#local-build-and-testing)
5. [GitHub Repository Setup](#github-repository-setup)
6. [PyPI Configuration](#pypi-configuration)
7. [Release Process](#release-process)
8. [Automated Workflows](#automated-workflows)
9. [Manual Release Process](#manual-release-process)
10. [Post-Release Verification](#post-release-verification)
11. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools
- Python 3.8+ installed
- Git configured with SSH keys for GitHub
- GitHub account with repository access
- PyPI account with API token
- PowerShell or Command Prompt (Windows)

### Required Python Packages
```bash
pip install --upgrade pip build twine
```

## Pre-Release Checklist

### 1. Code Quality Verification
- [ ] All tests pass
- [ ] Code follows project style guidelines
- [ ] Documentation is up to date
- [ ] No security vulnerabilities
- [ ] Performance benchmarks meet requirements

### 2. Version Consistency Check
- [ ] Version in `pyproject.toml` matches intended release
- [ ] Version in `rail_django_graphql/__init__.py` matches `pyproject.toml`
- [ ] CHANGELOG.md is updated with release notes
- [ ] All version references are consistent

### 3. Documentation Updates
- [ ] README.md reflects current features
- [ ] API documentation is current
- [ ] Examples are working and tested
- [ ] Migration guides (if applicable)

## Version Management

### Semantic Versioning
This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (0.X.0): New features, backward compatible
- **PATCH** (0.0.X): Bug fixes, backward compatible

### Version Update Process

1. **Update pyproject.toml**:
```toml
[project]
version = "1.1.2"  # Update this line
```

2. **Update __init__.py**:
```python
__version__ = "1.1.2"  # Update this line
```

3. **Update CHANGELOG.md**:
```markdown
## [1.1.2] - 2024-12-20

### Fixed
- Critical bug fixes
- Performance improvements

### Added
- New features

### Changed
- Breaking changes (if any)
```

## Local Build and Testing

### 1. Clean Previous Builds
```bash
# Remove old build artifacts
rm -rf build/ dist/ *.egg-info/
```

### 2. Install Build Dependencies
```bash
python -m pip install --upgrade pip build twine
```

### 3. Build the Package
```bash
python -m build
```

### 4. Verify Build Quality
```bash
twine check dist/*
```

### 5. Test Installation (Optional)
```bash
# Create virtual environment for testing
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate
pip install dist/rail_django_graphql-1.1.2-py3-none-any.whl
python -c "import rail_django_graphql; print(rail_django_graphql.__version__)"
deactivate
rm -rf test_env
```

## GitHub Repository Setup

### 1. Repository Configuration
- Repository: `https://github.com/raillogistic/rail-django-graphql`
- Main branch: `main`
- SSH access configured

### 2. Required GitHub Secrets
Navigate to: `Settings > Secrets and variables > Actions`

Add the following secrets:
- `PYPI_API_TOKEN`: Your PyPI API token (starts with `pypi-`)

### 3. Verify Remote Configuration
```bash
git remote -v
# Should show:
# origin  git@github.com:raillogistic/rail-django-graphql.git (fetch)
# origin  git@github.com:raillogistic/rail-django-graphql.git (push)
```

## PyPI Configuration

### 1. Create PyPI Account
- Register at [https://pypi.org/account/register/](https://pypi.org/account/register/)
- Verify email address

### 2. Generate API Token
1. Go to [https://pypi.org/manage/account/](https://pypi.org/manage/account/)
2. Scroll to "API tokens" section
3. Click "Add API token"
4. Name: `rail-django-graphql-release`
5. Scope: `Entire account` or specific to `rail-django-graphql`
6. Copy the generated token (starts with `pypi-`)

### 3. Configure GitHub Secret
1. Go to GitHub repository
2. Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Name: `PYPI_API_TOKEN`
5. Value: Your PyPI API token
6. Click "Add secret"

## Release Process

### Automated Release (Recommended)

The project uses GitHub Actions for automated releases:

1. **Commit and Push Changes**:
```bash
git add .
git commit -m "Release v1.1.2: Fix dual field logic and improve validation"
git push origin main
```

2. **Automatic Tag Creation**:
   - The `tag.yml` workflow automatically creates tags based on `pyproject.toml` version
   - Tag format: `v1.1.2`

3. **Automatic Release**:
   - The `release.yml` workflow triggers on tag creation
   - Builds the package
   - Creates GitHub release
   - Publishes to PyPI (if `PYPI_API_TOKEN` is configured)

### Manual Release Process

If automated workflows fail or manual control is needed:

#### 1. Create and Push Tag
```bash
git tag v1.1.2
git push origin v1.1.2
```

#### 2. Build Package
```bash
python -m build
```

#### 3. Upload to PyPI
```bash
twine upload dist/rail_django_graphql-1.1.2*
```

#### 4. Create GitHub Release
1. Go to [GitHub Releases](https://github.com/raillogistic/rail-django-graphql/releases)
2. Click "Create a new release"
3. Tag: `v1.1.2`
4. Title: `Release v1.1.2`
5. Description: Copy from CHANGELOG.md
6. Attach build artifacts (optional)
7. Click "Publish release"

## Automated Workflows

### 1. Tag Workflow (`.github/workflows/tag.yml`)
- **Trigger**: Push to `main` branch
- **Purpose**: Automatically create version tags
- **Process**:
  1. Extracts version from `pyproject.toml`
  2. Checks if tag already exists
  3. Creates and pushes new tag if needed

### 2. Release Workflow (`.github/workflows/release.yml`)
- **Trigger**: Push of version tags (`v*`)
- **Purpose**: Build, release, and publish
- **Process**:
  1. Sets up Python environment
  2. Installs build dependencies
  3. Builds package
  4. Validates package with twine
  5. Creates GitHub release
  6. Publishes to PyPI (if token available)

### 3. CI Workflow (`.github/workflows/ci.yml`)
- **Trigger**: Pull requests and pushes
- **Purpose**: Continuous integration testing
- **Process**: Runs tests, linting, and quality checks

## Post-Release Verification

### 1. Verify GitHub Release
- Check [GitHub Releases](https://github.com/raillogistic/rail-django-graphql/releases)
- Ensure release notes are correct
- Verify attached artifacts

### 2. Verify PyPI Publication
- Check [PyPI package page](https://pypi.org/project/rail-django-graphql/)
- Verify version is available
- Test installation: `pip install rail-django-graphql==1.1.2`

### 3. Test Installation
```bash
# Create fresh environment
python -m venv verify_env
source verify_env/bin/activate  # Windows: verify_env\Scripts\activate

# Install from PyPI
pip install rail-django-graphql==1.1.2

# Verify installation
python -c "import rail_django_graphql; print(f'Version: {rail_django_graphql.__version__}')"

# Clean up
deactivate
rm -rf verify_env
```

### 4. Update Documentation
- [ ] Update README badges if needed
- [ ] Update documentation sites
- [ ] Announce release in relevant channels

## Troubleshooting

### Common Issues and Solutions

#### 1. Version Mismatch Error
**Problem**: Different versions in `pyproject.toml` and `__init__.py`
**Solution**: 
```bash
# Check versions
grep version pyproject.toml
grep __version__ rail_django_graphql/__init__.py
# Update to match
```

#### 2. Build Failures
**Problem**: Package build fails
**Solution**:
```bash
# Clean build artifacts
rm -rf build/ dist/ *.egg-info/
# Reinstall build tools
pip install --upgrade build setuptools wheel
# Try building again
python -m build
```

#### 3. PyPI Upload Failures
**Problem**: `twine upload` fails
**Solutions**:
- Check API token is correct
- Verify package name isn't taken
- Ensure version doesn't already exist
- Check network connectivity

#### 4. GitHub Actions Failures
**Problem**: Workflows fail
**Solutions**:
- Check GitHub secrets are configured
- Verify workflow permissions
- Check for syntax errors in YAML files
- Review workflow logs for specific errors

#### 5. Tag Already Exists
**Problem**: Cannot create tag because it exists
**Solution**:
```bash
# Delete local tag
git tag -d v1.1.2
# Delete remote tag
git push origin :refs/tags/v1.1.2
# Create new tag
git tag v1.1.2
git push origin v1.1.2
```

### Emergency Rollback

If a release has critical issues:

#### 1. PyPI Rollback
- PyPI doesn't allow deleting releases
- Release a hotfix version (e.g., 1.1.3)
- Mark problematic version as yanked (if possible)

#### 2. GitHub Rollback
```bash
# Delete GitHub release (via web interface)
# Delete tag
git push origin :refs/tags/v1.1.2
git tag -d v1.1.2
```

## Release Checklist Template

Copy this checklist for each release:

### Pre-Release
- [ ] All tests passing
- [ ] Version updated in `pyproject.toml`
- [ ] Version updated in `__init__.py`
- [ ] CHANGELOG.md updated
- [ ] Documentation updated
- [ ] Local build successful
- [ ] Package validation passed

### Release
- [ ] Changes committed and pushed
- [ ] Tag created (automatically or manually)
- [ ] GitHub release created
- [ ] PyPI package published
- [ ] Installation verified

### Post-Release
- [ ] GitHub release verified
- [ ] PyPI package verified
- [ ] Installation from PyPI tested
- [ ] Documentation updated
- [ ] Release announced

## Contact and Support

For questions about the release process:
- GitHub Issues: [https://github.com/raillogistic/rail-django-graphql/issues](https://github.com/raillogistic/rail-django-graphql/issues)
- Email: contributors@rail-django-graphql.com

---

**Last Updated**: December 20, 2024
**Version**: 1.1.2