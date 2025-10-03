# Django GraphQL Boilerplate

Ready-to-use Django project that integrates the `rail-django-graphql` library installed directly from GitHub.

## Features

- Django 4.2 project structure with development and production settings
- GraphQL endpoint via Graphene-Django
- Automatic schema generation using `rail-django-graphql`
- Example apps: `users` and `blog` with minimal models
 - Configurable security and performance via `RAIL_DJANGO_GRAPHQL`

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
   - GraphiQL is enabled in development.

## Configuration

- Update environment variables in `.env` or operating system environment
- For production, set `DEBUG=False` and configure a PostgreSQL database
- Adjust `RAIL_DJANGO_GRAPHQL` settings in `config/settings/base.py`
 - `GRAPHENE.MIDDLEWARE` includes `graphene_django.debug.DjangoDebugMiddleware` and `rail_django_graphql.middleware.GraphQLPerformanceMiddleware`

## Documentation

See `docs/` for installation, configuration, and usage guides. To serve docs locally:

```bash
pip install mkdocs mkdocs-material
cd django-graphql-boilerplate
mkdocs serve
```

## Tests

Install testing dependencies and run the test suite:

```powershell
pip install -r requirements\testing.txt
cd django-graphql-boilerplate
pytest
```