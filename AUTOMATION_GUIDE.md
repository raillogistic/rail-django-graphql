# Rail Django GraphQL - Automation Guide

This guide explains the automated release system for the `rail-django-graphql` package, including both the manual upload script and the new auto-tagging workflow.

## 🚀 Auto-Tagging Workflow (Recommended)

The auto-tagging workflow automatically creates Git tags and triggers releases when you update the version in `pyproject.toml`. This is the **recommended approach** for most releases.

### How It Works

1. **Update Version**: Modify the version in `pyproject.toml`
2. **Commit & Push**: Push changes to the `main` branch
3. **Auto-Tag**: Workflow detects version change and creates a tag
4. **Auto-Release**: Release workflow builds and publishes to PyPI

### Quick Start

```bash
# 1. Update version in pyproject.toml
sed -i 's/version = "1.1.3"/version = "1.2.0"/' pyproject.toml

# 2. Commit and push
git add pyproject.toml
git commit -m "Bump version to 1.2.0"
git push origin main

# 3. Auto-tagging workflow runs automatically
# 4. Release workflow publishes to PyPI
```

### Auto-Tagging Features

- ✅ **Semantic Version Validation**: Ensures versions follow semver format
- ✅ **Version Comparison**: Only creates tags for version increases
- ✅ **Duplicate Prevention**: Skips if tag already exists
- ✅ **Draft Releases**: Creates GitHub draft releases for review
- ✅ **Detailed Logging**: Provides comprehensive workflow summaries

### Workflow Triggers

The auto-tagging workflow triggers on:
- Changes to `pyproject.toml` on the `main` branch
- Changes to `rail_django_graphql/__init__.py` on the `main` branch

### Workflow Outputs

When successful, the workflow:
1. Creates an annotated Git tag (e.g., `v1.2.0`)
2. Creates a GitHub draft release with auto-generated notes
3. Triggers the release workflow for PyPI publishing

## 📦 Manual Upload Script (Legacy)

The `upload_and_build.ps1` script provides manual control over the release process. Use this for complex releases or when you need custom control.

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

### Auto-Tagging Workflow Issues

#### Workflow Not Triggering
1. **Check file paths**: Ensure changes are made to `pyproject.toml` or `rail_django_graphql/__init__.py`
2. **Verify branch**: Auto-tagging only works on the `main` branch
3. **Check workflow status**: Visit GitHub Actions tab to see workflow runs

#### Version Not Detected
```bash
# Verify version format in pyproject.toml
grep "version" pyproject.toml

# Should show: version = "1.2.3" (semantic versioning)
```

#### Tag Already Exists Error
```bash
# Check existing tags
git tag -l "v*"

# Delete local tag if needed
git tag -d v1.2.3

# Delete remote tag if needed (use with caution)
git push origin --delete v1.2.3
```

#### Semantic Versioning Validation Fails
- Ensure version follows format: `MAJOR.MINOR.PATCH` (e.g., `1.2.3`)
- Pre-release versions: `1.2.3-alpha.1`
- Build metadata: `1.2.3+build.1`
- Invalid formats: `v1.2.3`, `1.2`, `1.2.3.4`

#### Version Comparison Issues
The workflow only creates tags when version increases:
```bash
# ✅ Valid increases
1.0.0 → 1.0.1 (patch)
1.0.1 → 1.1.0 (minor)
1.1.0 → 2.0.0 (major)

# ❌ Invalid (no tag created)
1.1.0 → 1.1.0 (unchanged)
1.1.0 → 1.0.9 (decrease)
```

### Manual Script Issues

#### Script Won't Run
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

## Workflow Comparison

### Auto-Tagging vs Manual Script

| Feature | Auto-Tagging Workflow | Manual Script |
|---------|----------------------|---------------|
| **Ease of Use** | ✅ Simple version bump + push | ⚠️ Requires script execution |
| **Automation** | ✅ Fully automated | ⚠️ Semi-automated |
| **Error Prevention** | ✅ Built-in validation | ⚠️ Manual validation needed |
| **Rollback** | ✅ Easy (delete tag) | ❌ Complex |
| **Customization** | ❌ Limited | ✅ Highly customizable |
| **Local Testing** | ❌ Not available | ✅ Dry-run mode |
| **Complex Releases** | ❌ Basic releases only | ✅ Full control |

### When to Use Each Approach

**Use Auto-Tagging When:**
- Standard version releases (patch, minor, major)
- Following semantic versioning
- Want maximum automation
- Team-based development
- Regular release cadence

**Use Manual Script When:**
- Complex release requirements
- Custom release notes needed
- Local testing required
- Emergency hotfixes
- Pre-release versions

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