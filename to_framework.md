# Transformation to Framework Guide: `rail-django-graphql`

This guide details the steps to transform the `rail-django-graphql` library into a standalone framework (e.g., `rail-framework`) with its own CLI tool (`rail-admin`), allowing for minimal setup similar to Django itself.

## 1. Vision & Goal

**Current State:** A Django app installed via `INSTALLED_APPS` requiring manual configuration in a standard Django project.
**Target State:** A framework where users run `rail-admin startproject myapp` and get a pre-configured, ready-to-run GraphQL API server.

## 2. Implementation Steps

### Phase 1: Create the CLI Entry Point (`rail-admin`)

We need a console script that acts like `django-admin` but carries our framework's context.

1.  **Create `rail_django_graphql/bin/rail_admin.py`:**
    This script will be the entry point. It will act as a wrapper around Django's management utility.

    ```python
    #!/usr/bin/env python
    import os
    import sys
    from django.core.management import execute_from_command_line

    def main():
        """Run administrative tasks."""
        # Set default settings if not configured (useful for commands like startproject)
        # We might point to a default settings module within the library for bootstrapping
        # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rail_django_graphql.conf.default_settings')
        
        execute_from_command_line(sys.argv)

    if __name__ == "__main__":
        main()
    ```

2.  **Register the Script in `pyproject.toml`:**
    Add the `[project.scripts]` section to expose `rail-admin`.

    ```toml
    [project.scripts]
    rail-admin = "rail_django_graphql.bin.rail_admin:main"
    ```

    *Note: If keeping `setup.py`, add `entry_points={'console_scripts': ['rail-admin=rail_django_graphql.bin.rail_admin:main']}`.*

### Phase 2: Custom Project Template (`startproject`)

To ensure "minimal setup", we need a custom template that `startproject` uses. This template will have the `settings.py` pre-filled with `rail-django-graphql` configurations.

1.  **Create Template Structure:**
    Create a directory `rail_django_graphql/conf/project_template/` mirroring a standard Django project structure but optimized for this framework.

    ```text
    rail_django_graphql/conf/project_template/
    ├── project_name/
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py  <-- Pre-configured
    │   ├── urls.py      <-- Pre-wired with GraphQL
    │   └── wsgi.py
    ├── manage.py
    └── requirements.txt
    ```

2.  **Customize `settings.py` in Template:**
    Instead of the standard Django settings, it should look like this:

    ```python
    from pathlib import Path
    from rail_django_graphql.conf.defaults import *  # Import framework defaults

    # Overrides
    BASE_DIR = Path(__file__).resolve().parent.parent
    SECRET_KEY = '{{ secret_key }}'
    DEBUG = True
    ALLOWED_HOSTS = []

    # The framework's apps are already in defaults, just add local ones
    INSTALLED_APPS += [
        '{{ project_name }}',
    ]
    
    # ... other overrides ...
    ```

3.  **Inject Template via CLI Wrapper:**
    Instead of subclassing the management command (which requires settings to be loaded), we inject the template path directly in `rail-admin`.
    
    Inside `rail_django_graphql/bin/rail_admin.py`:

    ```python
    def main():
        argv = sys.argv[:]
        if len(argv) > 1 and argv[1] == 'startproject':
            # Check if template is already provided
            has_template = any(arg.startswith('--template') for arg in argv)
            if not has_template:
                import rail_django_graphql
                # Point to our custom template
                template_path = os.path.join(
                    os.path.dirname(rail_django_graphql.__file__),
                    'conf', 'project_template'
                )
                argv.append(f'--template={template_path}')
        
        execute_from_command_line(argv)
    ```

### Phase 3: Configuration Abstraction

Reduce the boilerplate in the user's `settings.py` by centralizing the heavy configuration.

1.  **Create `rail_django_graphql/conf/framework_settings.py`:**
    This file acts as the base settings module. It imports standard Django defaults and the library's internal configuration.

    ```python
    # rail_django_graphql/conf/framework_settings.py
    from rail_django_graphql.defaults import LIBRARY_DEFAULTS
    
    # ... Standard Django Settings (INSTALLED_APPS, MIDDLEWARE, etc.) ...
    
    INSTALLED_APPS = [
        "django.contrib.admin",
        # ...
        "rail_django_graphql",
    ]

    # Load library defaults into Django settings
    RAIL_DJANGO_GRAPHQL = LIBRARY_DEFAULTS
    ```

### Phase 4: Execution Plan

1.  **Update `pyproject.toml`** to include the `[project.scripts]` entry.
2.  **Create `rail_django_graphql/bin/`** directory and the `rail_admin.py` file.
3.  **Create `rail_django_graphql/conf/project_template/`** and populate it with the starter files.
4.  **Create `rail_django_graphql/management/commands/startproject.py`** to force the use of the custom template.
5.  **Refactor `rail_django_graphql/conf/defaults.py`** (or `settings.py`) to serve as a base configuration module that users can import `*` from.

## Usage after Transformation

The user workflow will become:

```bash
# 1. Install the framework
pip install rail-django-graphql

# 2. Create a new project (uses custom template automatically)
rail-admin startproject my_api

# 3. Run it
cd my_api
python manage.py runserver
```

This achieves the goal of a "ready-to-go" framework wrapper around the library.
