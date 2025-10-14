# Rail Django GraphQL - Automation Guide

This guide explains how to use the automated upload and build script (`upload_and_build.ps1`) for releasing new versions of the `rail-django-graphql` package.

## Overview

The `upload_and_build.ps1` script automates the entire release process, including:
- Version number synchronization
- Package building and validation
- Git tagging and pushing
- Triggering automated GitHub workflows
- CHANGELOG.md updates

## Prerequisites

### Required Software
- **PowerShell 5.0+** (Windows PowerShell or PowerShell Core)
- **Python 3.8+** with pip
- **Git** configured with GitHub access
- **pytest** for running tests

### Required Python Packages
```bash
pip install build twine pytest
```

### GitHub Configuration
- Repository must have `PYPI_API_TOKEN` secret configured
- GitHub Actions workflows must be enabled
- Push access to the main branch

## Usage

### Basic Usage

```powershell
# Release a new version
.\upload_and_build.ps1 -Version "1.2.3"

# Release with custom message
.\upload_and_build.ps1 -Version "1.2.3" -Message "Fix critical bug in dual field logic"
```

### Advanced Usage

```powershell
# Skip tests (not recommended for production)
.\upload_and_build.ps1 -Version "1.2.3" -SkipTests

# Dry run (preview changes without executing)
.\upload_and_build.ps1 -Version "1.2.3" -DryRun

# Force release despite warnings
.\upload_and_build.ps1 -Version "1.2.3" -Force

# Combine options
.\upload_and_build.ps1 -Version "1.2.3" -Message "Emergency hotfix" -SkipTests -Force
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `-Version` | String | ✅ Yes | Semantic version number (e.g., "1.2.3") |
| `-Message` | String | ❌ No | Custom release message for commit and changelog |
| `-SkipTests` | Switch | ❌ No | Skip running tests before release |
| `-DryRun` | Switch | ❌ No | Preview changes without executing them |
| `-Force` | Switch | ❌ No | Continue despite warnings or test failures |

## Process Flow

The script follows this automated process:

### 1. **Pre-flight Checks** 🔍
- Validates version format (semantic versioning)
- Checks if running from correct directory
- Verifies Git repository status

### 2. **Version Updates** 📝
- Updates `pyproject.toml` version
- Updates `rail_django_graphql/__init__.py` version
- Synchronizes all version references

### 3. **Quality Assurance** 🧪
- Runs full test suite (unless `-SkipTests`)
- Validates code quality
- Ensures no regressions

### 4. **Package Building** 📦
- Cleans previous build artifacts
- Installs/updates build dependencies
- Builds source distribution and wheel
- Validates package integrity

### 5. **Documentation Updates** 📚
- Updates `CHANGELOG.md` with new release
- Adds release date and version info
- Includes custom message if provided

### 6. **Git Operations** 🔄
- Commits all changes with descriptive message
- Creates annotated Git tag
- Pushes changes and tag to GitHub

### 7. **Automation Trigger** 🚀
- Triggers GitHub Actions workflows
- Initiates automated PyPI publishing
- Creates GitHub release

## Examples

### Standard Release
```powershell
# Standard patch release
.\upload_and_build.ps1 -Version "1.1.3"
```

### Feature Release
```powershell
# Minor version with new features
.\upload_and_build.ps1 -Version "1.2.0" -Message "Add new GraphQL schema validation features"
```

### Hotfix Release
```powershell
# Emergency hotfix
.\upload_and_build.ps1 -Version "1.1.4" -Message "Critical security fix" -Force
```

### Development Testing
```powershell
# Test the process without making changes
.\upload_and_build.ps1 -Version "1.2.0" -DryRun
```

## Output Examples

### Successful Release
```
ℹ️  Starting automated upload and build process for rail-django-graphql v1.2.3
🔄 Checking Git repository status...
✅ Git repository status checked
🔄 Updating version numbers to 1.2.3...
✅ Version numbers updated to 1.2.3
🔄 Running tests...
✅ All tests passed
🔄 Building package...
✅ Package built successfully
🔄 Validating package...
✅ Package validation passed
🔄 Updating CHANGELOG.md...
✅ CHANGELOG.md updated
🔄 Committing changes...
✅ Changes committed
🔄 Creating and pushing tag v1.2.3...
✅ Tag v1.2.3 created and pushed
🎉 Release process completed successfully!
```

### Dry Run Output
```
⚠️  DRY RUN MODE - No changes will be committed or pushed
ℹ️  The following would be done:
ℹ️  - Commit changes with message: 'Release v1.2.3: Add new features'
ℹ️  - Create and push tag: v1.2.3
ℹ️  - Push to origin/main
```

## Error Handling

The script includes comprehensive error handling:

### Common Issues and Solutions

#### **Dirty Working Directory**
```
⚠️  Working directory is not clean. Uncommitted changes found:
Continue anyway? (y/N)
```
**Solution**: Commit or stash changes, or use `-Force` flag

#### **Test Failures**
```
❌ Tests failed. Fix issues before releasing.
```
**Solution**: Fix failing tests, or use `-SkipTests` (not recommended)

#### **Invalid Version Format**
```
❌ Invalid version format. Use semantic versioning (e.g., 1.2.3)
```
**Solution**: Use proper semantic versioning format

#### **Build Failures**
```
❌ Build failed - no files generated in dist/
```
**Solution**: Check Python environment and dependencies

## Best Practices

### 🎯 **Version Strategy**
- **Patch** (1.1.1 → 1.1.2): Bug fixes, security patches
- **Minor** (1.1.0 → 1.2.0): New features, backwards compatible
- **Major** (1.0.0 → 2.0.0): Breaking changes

### 🧪 **Testing Strategy**
- Always run tests before release (avoid `-SkipTests`)
- Use `-DryRun` to preview changes
- Test in development environment first

### 📝 **Documentation**
- Provide meaningful commit messages
- Update CHANGELOG.md with detailed changes
- Document breaking changes clearly

### 🔒 **Security**
- Never commit secrets or API keys
- Verify GitHub secrets are properly configured
- Review changes before pushing

## Troubleshooting

### Script Won't Run
```powershell
# Check execution policy
Get-ExecutionPolicy

# Allow script execution (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### GitHub Actions Not Triggering
1. Check if workflows are enabled in repository settings
2. Verify tag was pushed successfully: `git ls-remote --tags origin`
3. Check GitHub Actions tab for workflow runs

### PyPI Publishing Fails
1. Verify `PYPI_API_TOKEN` secret is configured
2. Check token permissions and expiration
3. Ensure package name is available on PyPI

### Build Issues
```powershell
# Clean environment and reinstall dependencies
pip install --upgrade pip build twine
python -m build --clean
```

## Integration with CI/CD

### GitHub Actions Integration
The script works seamlessly with existing GitHub Actions:

```yaml
# .github/workflows/manual-release.yml
name: Manual Release
on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to release'
        required: true
        type: string

jobs:
  release:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Release Script
        run: .\upload_and_build.ps1 -Version "${{ inputs.version }}"
```

### Local Development Workflow
```powershell
# 1. Development
git checkout -b feature/new-feature
# ... make changes ...
git commit -m "Add new feature"
git push origin feature/new-feature

# 2. Testing
.\upload_and_build.ps1 -Version "1.2.0" -DryRun

# 3. Release
git checkout main
git pull origin main
.\upload_and_build.ps1 -Version "1.2.0" -Message "Add new GraphQL features"
```

## Monitoring and Verification

After running the script, monitor these locations:

1. **GitHub Actions**: `https://github.com/raillogistic/rail-django-graphql/actions`
2. **GitHub Releases**: `https://github.com/raillogistic/rail-django-graphql/releases`
3. **PyPI Package**: `https://pypi.org/project/rail-django-graphql/`

### Verification Commands
```powershell
# Check if tag was created
git tag -l | Select-String "v1.2.3"

# Verify package installation
pip install rail-django-graphql==1.2.3

# Test import
python -c "import rail_django_graphql; print(rail_django_graphql.__version__)"
```

## Support

For issues with the automation script:

1. Check this guide for common solutions
2. Review the `RELEASE_MANUAL.md` for manual processes
3. Check GitHub repository issues
4. Contact the development team

---

**Happy Releasing! 🚀**