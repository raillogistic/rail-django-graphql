# Rail Django GraphQL - Automated Upload and Build Script
# This script automates the process of releasing new versions to GitHub and PyPI

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [string]$Message = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipTests,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun,
    
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

# Color functions for better output
function Write-Success { param($msg) Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }
function Write-Warning { param($msg) Write-Host "[WARNING] $msg" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Step { param($msg) Write-Host "[STEP] $msg" -ForegroundColor Blue }

# Project configuration
$ProjectRoot = Get-Location
$PackageName = "rail-django-graphql"

Write-Info "Starting automated upload and build process for $PackageName v$Version"

# Validate version format
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Error "Invalid version format. Use semantic versioning (e.g. 1.2.3)"
    exit 1
}

# Check if we're in the correct directory
if (-not (Test-Path "$ProjectRoot\pyproject.toml")) {
    Write-Error "pyproject.toml not found. Make sure you're running this script from the project root."
    exit 1
}

try {
    # Step 1: Check Git status
    Write-Step "Checking Git repository status..."
    $gitStatus = git status --porcelain
    if ($gitStatus -and -not $Force) {
        Write-Warning "Working directory is not clean. Uncommitted changes found:"
        git status --short
        $continue = Read-Host "Continue anyway? (y/N)"
        if ($continue -ne "y" -and $continue -ne "Y") {
            Write-Info "Aborted by user."
            exit 0
        }
    }
    Write-Success "Git repository status checked"

    # Step 2: Update version numbers
    Write-Step "Updating version numbers to $Version..."
    
    # Update pyproject.toml
    $pyprojectContent = Get-Content "$ProjectRoot\pyproject.toml" -Raw
    $pyprojectContent = $pyprojectContent -replace 'version = "[^"]*"', "version = `"$Version`""
    Set-Content "$ProjectRoot\pyproject.toml" -Value $pyprojectContent -NoNewline
    
    # Update __init__.py
    $initPath = "$ProjectRoot\rail_django_graphql\__init__.py"
    $initContent = Get-Content $initPath -Raw
    $initContent = $initContent -replace '__version__ = "[^"]*"', "__version__ = `"$Version`""
    Set-Content $initPath -Value $initContent -NoNewline
    
    Write-Success "Version numbers updated to $Version"

    # Step 3: Run tests (unless skipped)
    if (-not $SkipTests) {
        Write-Step "Running tests..."
        $testResult = python -m pytest
        if ($LASTEXITCODE -ne 0 -and -not $Force) {
            Write-Error "Tests failed. Fix issues before releasing."
            Write-Info "Use -SkipTests to bypass (not recommended) or -Force to continue anyway."
            exit 1
        }
        Write-Success "All tests passed"
    } else {
        Write-Warning "Tests skipped as requested"
    }

    # Step 4: Clean and build package
    Write-Step "Building package..."
    
    # Clean previous builds
    if (Test-Path "dist") {
        Remove-Item "dist" -Recurse -Force
    }
    if (Test-Path "build") {
        Remove-Item "build" -Recurse -Force
    }
    if (Test-Path "*.egg-info") {
        Remove-Item "*.egg-info" -Recurse -Force
    }
    
    # Install/upgrade build dependencies
    python -m pip install --upgrade pip build twine
    
    # Build the package
    python -m build
    
    # Verify build files were created
    $builtFiles = Get-ChildItem "dist" -Name
    if (-not $builtFiles) {
        Write-Error "Build failed - no files generated in dist/"
        exit 1
    }
    
    Write-Success "Package built successfully"
    $fileList = $builtFiles -join "; "
    Write-Info "Built files: $fileList"

    # Step 5: Validate package
    Write-Step "Validating package..."
    $validateResult = python -m twine check dist/*
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Package validation failed"
        exit 1
    }
    Write-Success "Package validation passed"

    # Step 6: Update CHANGELOG.md
    Write-Step "Updating CHANGELOG.md..."
    $changelogPath = "$ProjectRoot\CHANGELOG.md"
    if (Test-Path $changelogPath) {
        $changelogContent = Get-Content $changelogPath -Raw
        $releaseDate = Get-Date -Format "yyyy-MM-dd"
        $releaseMessage = if ($Message) { $Message } else { "Automated version bump and build" }
        
        $newEntry = @"
## [$Version] - $releaseDate

### Changed
- $releaseMessage

"@
        
        # Insert after the first line (usually "# Changelog")
        $lines = $changelogContent -split "`n"
        if ($lines.Count -gt 1) {
            $newContent = $lines[0] + "`n`n" + $newEntry + "`n" + ($lines[1..($lines.Count-1)] -join "`n")
            Set-Content $changelogPath -Value $newContent -NoNewline
        } else {
            # If changelog is empty or has only one line, create basic structure
            $newContent = "# Changelog`n`n" + $newEntry
            Set-Content $changelogPath -Value $newContent -NoNewline
        }
        
        Write-Success "CHANGELOG.md updated"
    } else {
        Write-Warning "CHANGELOG.md not found, skipping update"
    }

    if ($DryRun) {
        Write-Warning "DRY RUN MODE - No changes will be committed or pushed"
        Write-Info "The following would be done:"
        $releaseMessage = if ($Message) { $Message } else { "Automated version bump and build" }
        $commitMsg = "Release v$Version" + ": " + $releaseMessage
        Write-Info "- Commit changes with message: $commitMsg"
        Write-Info "- Create and push tag: v$Version"
        Write-Info "- Push to origin/main"
        Write-Info "- Trigger GitHub Actions workflow"
        return
    }

    # Step 7: Commit changes
    Write-Step "Committing changes..."
    git add .
    
    $commitMessage = if ($Message) {
        "Release v$Version" + ": " + $Message
    } else {
        "Release v$Version" + ": " + "Automated version bump and build"
    }
    
    git commit -m $commitMessage
    Write-Success "Changes committed"

    # Step 8: Create and push tag
    Write-Step "Creating and pushing tag v$Version..."
    
    # Delete existing tag if it exists
    git tag -d "v$Version" 2>$null
    git push origin ":refs/tags/v$Version" 2>$null
    
    # Create new tag
    $tagMessage = "Release v$Version" + ": " + $commitMessage
    git tag -a "v$Version" -m $tagMessage
    
    # Push changes and tag
    git push origin main
    git push origin "v$Version"
    
    Write-Success "Tag v$Version created and pushed"

    # Step 9: Monitor GitHub Actions (optional)
    Write-Step "Release process initiated..."
    Write-Info "GitHub Actions workflow should now be running automatically"
    Write-Info "Monitor progress at: https://github.com/raillogistic/rail-django-graphql/actions"
    Write-Info "Check release at: https://github.com/raillogistic/rail-django-graphql/releases"
    Write-Info "Verify PyPI at: https://pypi.org/project/rail-django-graphql/"

    # Step 10: Summary
    Write-Success "Release process completed successfully!"
    Write-Info "Summary:"
    Write-Info "  - Version: $Version"
    Write-Info "  - Commit: $commitMessage"
    Write-Info "  - Tag: v$Version"
    $fileList2 = $builtFiles -join "; "
    Write-Info "  - Built files: $fileList2"
    
    Write-Info ""
    Write-Info "Next steps:"
    Write-Info "1. Monitor GitHub Actions for successful completion"
    Write-Info "2. Verify GitHub release creation"
    Write-Info "3. Confirm PyPI package publication"
    Write-Info "4. Test installation: pip install rail-django-graphql==$Version"

} catch {
    Write-Error "An error occurred during the release process:"
    Write-Error $_.Exception.Message
    Write-Error "Stack trace: $($_.ScriptStackTrace)"
    exit 1
}

Write-Success "Script completed successfully!"