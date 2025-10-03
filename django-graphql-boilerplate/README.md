# Django GraphQL Boilerplate

Ready-to-use Django project that integrates the `rail-django-graphql` library installed directly from GitHub.

## Features

- Django 4.2 project structure with development and production settings
- GraphQL endpoint via Graphene-Django
- Automatic schema generation using `rail-django-graphql`
- Example apps: `users` and `blog` with minimal models

## Quick Start

1. Create a virtual environment:
   - Windows PowerShell:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```

2. Install dependencies:
   ```powershell
   pip install -r requirements\development.txt
   ```

3. Apply migrations and run the server:
   ```powershell
   python manage.py migrate
   python manage.py runserver
   ```

4. Visit the app:
   - Home: http://127.0.0.1:8000/
   - GraphQL: http://127.0.0.1:8000/graphql/

## Configuration

- Update environment variables in `.env` or operating system environment
- For production, set `DEBUG=False` and configure a PostgreSQL database
- Adjust `RAIL_DJANGO_GRAPHQL` settings in `config/settings/base.py`

## Library Usage

See `LIBRARY_USAGE_GUIDE.md` for advanced integration patterns.