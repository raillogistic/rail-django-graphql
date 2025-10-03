# Configuration

## Django Settings
Key settings in `config/settings/base.py`:

- `INSTALLED_APPS` includes `rail_django_graphql`.
- `GRAPHENE`:
  - `SCHEMA`: `config.schema.schema`
  - `MIDDLEWARE` includes `graphene_django.debug.DjangoDebugMiddleware` and `rail_django_graphql.middleware.GraphQLPerformanceMiddleware`.

## Rail Django GraphQL
`RAIL_DJANGO_GRAPHQL` configuration:
- `SCHEMAS.default.MODELS` lists models to expose.
- `ENABLE_MUTATIONS`, `ENABLE_FILTERS`, `ENABLE_PAGINATION` control features.
- `SECURITY` controls introspection and GraphiQL.
- `PERFORMANCE` enables caching and DataLoader.