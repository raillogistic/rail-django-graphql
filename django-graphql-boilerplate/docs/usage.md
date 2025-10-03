# Usage

## Accessing GraphiQL
With development settings, GraphiQL is enabled at `/graphql`.

## Example Query
```
query {
  posts(page: 1, pageSize: 10) {
    edges { node { id title author { username } } }
    pageInfo { hasNextPage }
  }
}
```

## Adding Models
Add Django models under `apps/` and list them in `RAIL_DJANGO_GRAPHQL.SCHEMAS.default.MODELS`.

## Custom Resolvers
You can add custom fields or resolvers in a local schema module and combine with auto-generated schema.