# Implementation Plan - Full Project Separation

## 📋 Overview

This document outlines the detailed implementation plan for completely separating the current monolithic project into two distinct, independent projects:

1.  **`rail-django-graphql`** - A standalone library hosted on GitHub.
2.  **`django-graphql-boilerplate`** - A boilerplate project that installs the library directly from GitHub.

This plan is structured in independent phases. Each phase builds upon the deliverables of the previous one, ensuring a clear and modular workflow.

---

## Phase 1: Library Creation & GitHub Setup

**Goal**: Create a fully independent, installable, and tested Python library from the existing codebase, hosted in its own GitHub repository.

**Estimated Time**: 2-3 days

### Step 1.1: Create Library Repository on GitHub ✅

-   **Action**: Create a new public GitHub repository named `rail-django-auto-gql`. ✅
-   **Details**:
    -   Description: "Automatic GraphQL schema generation for Django with advanced features." ✅
    -   License: MIT License. ✅
    -   Clone the new repository locally. ✅

### Step 1.2: Isolate and Copy Library Code ✅

-   **Action**: Copy all library-specific code, configuration, and documentation into the new repository. ✅
-   **Details**:
    -   Copy `rail_django_graphql/` source directory. ✅
    -   Copy relevant configuration files: `pyproject.toml`, `setup.py`, `MANIFEST.in`. ✅
    -   Copy legal and contribution files: `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`. ✅
    -   Copy library-specific tests (`tests/unit/`, `tests/integration/`). ✅
    -   **Crucially, remove all boilerplate-specific code**: `test_app`, `manage.py`, Django project settings (`config/`), etc. ✅

### Step 1.3: Configure for Standalone Distribution ✅

-   **Action**: Update configuration files to make the library a distributable package. ✅
-   **Details**:
    -   `pyproject.toml`: Define project metadata, dependencies, and repository URLs. ✅
    -   `setup.py`: Ensure it's configured for standalone packaging. ✅
    -   `MANIFEST.in`: Ensure all necessary files (like templates or static files) are included in the package. ✅
    -   `requirements/`: Create `base.txt` with only the core library dependencies. ✅

### Step 1.4: Create Library-Specific Documentation ✅

-   **Action**: Develop documentation focused solely on the library's usage and development. ✅
-   **Details**:
    -   Create a comprehensive `README.md` with installation instructions pointing to the GitHub repository. ✅
    -   Set up GitHub Pages for formal documentation. ✅
    -   Generate API reference documentation. ✅

### Step 1.5: Set Up CI/CD and Automation ✅

-   **Action**: Implement GitHub Actions for automated quality assurance and release management. ✅
-   **Details**:
    -   Configure workflows for automated testing (on push/PR across multiple Python versions), linting, and security scanning. ✅
    -   Set up a workflow for automated documentation generation and deployment to GitHub Pages.
    -   Configure release automation (e.g., using semantic-release).

### Step 1.6: Publish and Test Initial Release

-   **Action**: Tag and publish the first official version of the library.
-   **Details**:
    -   Commit all changes to the `main` branch.
    -   Create and publish the `v1.0.0` release on GitHub.
    -   **Verification**: Test the installation from GitHub in a clean environment using `pip install git+https://github.com/raillogistic/rail-django-graphql.git@v1.0.0`.

**✅ Result of this Phase**:

-   A public GitHub repository at `https://github.com/raillogistic/rail-django-graphql`.
-   The repository contains a complete, standalone Python library.
-   An official `v1.0.0` release is published on GitHub.
-   The library is installable via `pip` directly from the GitHub repository URL.

---

## Phase 2: Boilerplate Creation with GitHub Integration

**Goal**: Create a new Django boilerplate project that uses the `rail-django-graphql` library as a remote dependency installed from GitHub.

**Context from Previous Phase**:

-   **Required**: A stable `v1.0.0` release of the `rail-django-graphql` library available on GitHub.
-   **Input**: The installation URL: `git+https://github.com/raillogistic/rail-django-graphql.git@v1.0.0#egg=rail-django-graphql`.

**Estimated Time**: 2-3 days

### Step 2.1: Create Boilerplate Repository on GitHub

-   **Action**: Create a new public GitHub repository named `django-graphql-boilerplate`.
-   **Details**:
    -   Description: "Ready-to-use Django boilerplate with rail-django-graphql integration."
    -   License: MIT License.
    -   Clone the new repository locally.

### Step 2.2: Isolate and Adapt Boilerplate Files

-   **Action**: Copy all project-specific files from the original monolithic repository.
-   **Details**:
    -   Copy Django project files: `manage.py`, `config/`, `test_app/` (to be refactored), `templates/`, `static/`.
    -   Copy deployment and environment files: `docker-compose.yml`, `Dockerfile`, `.env.example`, `deploy/`.
    -   **Crucially, do not copy any library code that now belongs in the other repository.**

### Step 2.3: Configure GitHub-Based Library Installation

-   **Action**: Modify the boilerplate's requirements to install the library from GitHub.
-   **Details**:
    -   In `requirements/base.txt`, add the line:
        ```
        # Install rail-django-graphql directly from GitHub
        git+https://github.com/raillogistic/rail-django-graphql.git@v1.0.0#egg=rail-django-graphql
        ```
    -   Add other Django and application-specific dependencies.

### Step 2.4: Update Django Settings and Refactor Apps

-   **Action**: Ensure the Django project correctly integrates the installed library.
-   **Details**:
    -   Verify `rail_django_graphql` is in `INSTALLED_APPS` in `config/settings/base.py`.
    -   Refactor the old `test_app` into meaningful example applications (e.g., `apps/blog`, `apps/users`).
    -   Ensure all models, views, and schema definitions correctly import and use the `rail_django_graphql` library.

### Step 2.5: Create Boilerplate-Specific Documentation

-   **Action**: Write documentation explaining how to use the boilerplate.
-   **Details**:
    -   Create a `README.md` with clear setup instructions.
    -   Document the project structure, available apps, and configuration variables.
    -   Provide a guide on how to customize and extend the boilerplate.

**✅ Result of this Phase**:

-   A public GitHub repository at `https://github.com/raillogistic/django-graphql-boilerplate`.
-   The repository contains a complete Django project.
-   The project successfully installs and uses the `rail-django-graphql` library from GitHub as a dependency.

---

## Phase 3: Integration & End-to-End Testing

**Goal**: Verify that the separated library and boilerplate work together perfectly in a clean, production-like environment.

**Context from Previous Phase**:

-   **Required**: Two independent GitHub repositories:
    1. `rail-django-graphql` (library).
    2. `django-graphql-boilerplate` (project using the library).

**Estimated Time**: 1-2 days

### Step 3.1: Test Boilerplate Installation and Setup

-   **Action**: Perform a fresh clone and setup of the boilerplate repository.
-   **Details**:
    -   Clone `django-graphql-boilerplate`.
    -   Create a virtual environment and run `pip install -r requirements/base.txt`.
    -   Verify the `rail-django-graphql` library is installed correctly from GitHub.
    -   Run database migrations and start the development server.

### Step 3.2: Full-System Functional Testing

-   **Action**: Test all features of the example applications.
-   **Details**:
    -   Execute GraphQL queries and mutations to ensure the schema generated by the library works as expected.
    -   Test user authentication, data retrieval, and other core functionalities.
    -   Run the boilerplate's test suite (`python manage.py test`).

### Step 3.3: Cross-Platform and Docker Validation

-   **Action**: Ensure the setup works across different environments.
-   **Details**:
    -   Test the installation and setup process on Windows, macOS, and Linux.
    -   Build and run the Docker containers using `docker-compose up`.
    -   Execute health checks against the running Docker containers to confirm the application is stable.

### Step 3.4: Performance and Security Checks

-   **Action**: Run initial benchmarks and security scans.
-   **Details**:
    -   Run performance benchmarks on key GraphQL endpoints.
    -   Use security scanning tools to check for vulnerabilities in both repositories.

**✅ Result of this Phase**:

-   Confirmation that the `django-graphql-boilerplate` can be set up from scratch and runs correctly.
-   A full test suite that passes, validating the integration between the boilerplate and the remote library.
-   Successful validation of the Docker setup.

---

## Phase 4: Finalizing Documentation & Automation

**Goal**: Polish documentation, set up robust CI/CD pipelines for both repositories, and create a clear migration path for existing users.

**Context from Previous Phase**:

-   **Required**: Two fully functional and integrated repositories for the library and boilerplate.

**Estimated Time**: 2-3 days

### Step 4.1: Complete All Documentation

-   **Action**: Finalize and publish comprehensive documentation for both projects.
-   **Details**:
    -   **Library**: Publish API references, feature guides, and contribution guidelines to GitHub Pages.
    -   **Boilerplate**: Create detailed guides for setup, configuration, deployment, and customization.

### Step 4.2: Set Up Boilerplate CI/CD

-   **Action**: Implement GitHub Actions for the boilerplate repository.
-   **Details**:
    -   Create a CI workflow that installs dependencies (including the library from GitHub), runs tests, and builds Docker images.
    -   This ensures that any changes to the boilerplate are compatible with the specified library version.

### Step 4.3: Create Migration Guide

-   **Action**: Write a step-by-step guide for users migrating from the old monolithic structure.
-   **Details**:
    -   Document breaking changes (e.g., installation method).
    -   Provide clear instructions on how to replace the local library code with the new GitHub dependency.
    -   Create an FAQ for common migration issues.

**✅ Result of this Phase**:

-   Polished, user-friendly documentation for both repositories.
-   Fully automated CI/CD pipelines for both the library and the boilerplate.
-   A clear and helpful migration guide for existing users.

---

## Phase 5: Release & Community Engagement

**Goal**: Officially launch the new separated projects and establish channels for community support and contributions.

**Context from Previous Phase**:

-   **Required**: Two fully documented, tested, and automated repositories.

**Estimated Time**: 1-2 days

### Step 5.1: Publish Official Releases

-   **Action**: Tag and publish the initial official releases for both repositories on GitHub.
-   **Details**:
    -   Create detailed release notes for `rail-django-graphql` v1.0.0.
    -   Create release notes for the first stable version of `django-graphql-boilerplate`.

### Step 5.2: Configure Community Support Channels

-   **Action**: Set up GitHub features to encourage community interaction.
-   **Details**:
    -   Enable GitHub Discussions for questions and support.
    -   Create high-quality `ISSUE_TEMPLATE` and `PULL_REQUEST_TEMPLATE.md` files.
    -   Add repository topics and a clear description to enhance discoverability.

### Step 5.3: Announce the Launch

-   **Action**: Inform the community about the new repositories.
-   **Details**:
    -   Post announcements on relevant social media platforms or developer forums.
    -   Archive the old monolithic repository with a clear notice pointing to the new projects.

**✅ Result of this Phase**:

-   Official, stable releases of both the library and boilerplate are available on GitHub.
-   The projects are discoverable and welcoming to new contributors.
-   A clear communication plan is executed to guide users to the new ecosystem.