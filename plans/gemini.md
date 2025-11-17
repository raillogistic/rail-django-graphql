# Performance Upgrade Guide for rail-django-graphql

This guide provides recommendations and best practices for optimizing the performance of your `rail-django-graphql` library.

## 1. Introduction

Performance is a critical aspect of any GraphQL API. A slow API can lead to a poor user experience and high server costs. This guide will walk you through the performance features of `rail-django-graphql` and how to use them to build a fast and efficient API.

## 2. Performance Monitoring

The first step to improving performance is to measure it. `rail-django-graphql` comes with a built-in performance monitoring middleware.

### Enabling Performance Monitoring

To enable performance monitoring, add the `GraphQLPerformanceMiddleware` to your `MIDDLEWARE` settings in `settings.py`:

```python
# settings.py

MIDDLEWARE = [
    # ... other middlewares
    "rail_django_graphql.middleware.performance.GraphQLPerformanceMiddleware",
    # ... other middlewares
]
```

You also need to enable it in your `RAIL_DJANGO_GRAPHQL` settings:

```python
# settings.py

RAIL_DJANGO_GRAPHQL = {
    "PERFORMANCE": {
        "PERFORMANCE_MONITORING": True,
    }
}
```

### How it Works

The `GraphQLPerformanceMiddleware` collects metrics for each GraphQL request, such as:
- **Execution time**: Total time taken to resolve the query.
- **Database queries**: Number of database queries executed.
- **Database time**: Total time spent on database queries.
- **Query complexity and depth**: Measures to prevent overly complex queries.

### Viewing Performance Metrics

The library provides a view to expose these metrics. You can add it to your `urls.py`:

```python
# urls.py

from rail_django_graphql.middleware.performance import GraphQLPerformanceView

urlpatterns = [
    # ... other urls
    path('graphql/performance/', GraphQLPerformanceView.as_view(), name='graphql-performance'),
]
```

This will expose an endpoint at `/graphql/performance/` that you can use to get aggregated performance statistics.

## 3. Query Optimization

`rail-django-graphql` includes a `QueryOptimizer` that helps prevent common performance issues like the N+1 query problem.

### Automatic Query Optimization

The `QueryOptimizer` automatically applies `select_related` and `prefetch_related` to your querysets based on the fields requested in the GraphQL query. This is enabled by default.

You can configure it in your `settings.py`:

```python
# settings.py

RAIL_DJANGO_GRAPHQL = {
    "PERFORMANCE_SETTINGS": {
        "enable_query_optimization": True,
        "enable_select_related": True,
        "enable_prefetch_related": True,
    }
}
```

### Using `graphene-django-optimizer`

For more advanced optimizations, this library is designed to work well with `graphene-django-optimizer`. You can use its `optimizer` hook to apply optimizations.

Example:
```python
import graphene
from graphene_django.types import DjangoObjectType
import graphene_django_optimizer as gql_optimizer

from .models import MyModel

class MyModelType(DjangoObjectType):
    class Meta:
        model = MyModel

class Query(graphene.ObjectType):
    my_models = graphene.List(MyModelType)

    def resolve_my_models(self, info, **kwargs):
        return gql_optimizer.query(MyModel.objects.all(), info)
```

## 4. Dataloaders

Dataloaders are a powerful pattern for batching database queries, especially for nested resolvers. `rail-django-graphql` has built-in support for dataloaders.

To enable dataloaders, set `enable_dataloader` to `True` in your performance settings:

```python
# settings.py

RAIL_DJANGO_GRAPHQL = {
    "PERFORMANCE_SETTINGS": {
        "enable_dataloader": True,
        "dataloader_batch_size": 100, # optional
    }
}
```

The library will automatically use dataloaders for resolving related fields, which can significantly reduce the number of database queries.

## 5. Query Complexity and Depth Limiting

To protect your API from overly complex or deep queries that could be used for denial-of-service attacks, you can set limits on query complexity and depth.

### Configuration

You can configure these limits in your `settings.py`:

```python
# settings.py

RAIL_DJANGO_GRAPHQL = {
    "PERFORMANCE_SETTINGS": {
        "max_query_depth": 10,
        "max_query_complexity": 1000,
        "enable_query_cost_analysis": True, # To enable complexity checking
    }
}
```

- `max_query_depth`: The maximum nesting level of a query.
- `max_query_complexity`: A score calculated based on the number of fields and their nesting.

The `QueryComplexityAnalyzer` is used to perform these checks. If a query exceeds these limits, it will be rejected.

## 6. Performance Settings Summary

Here is a summary of performance-related settings you can configure in your `RAIL_DJANGO_GRAPHQL` settings:

```python
# settings.py

RAIL_DJANGO_GRAPHQL = {
    "PERFORMANCE_SETTINGS": {
        # Query Optimization
        "enable_query_optimization": True,
        "enable_select_related": True,
        "enable_prefetch_related": True,
        "enable_only_fields": True,
        "enable_defer_fields": False,

        # Dataloaders
        "enable_dataloader": True,
        "dataloader_batch_size": 100,

        # Query Limits
        "max_query_depth": 10,
        "max_query_complexity": 1000,
        "enable_query_cost_analysis": True,
        "query_timeout": 30,  # in seconds
    },
    "PERFORMANCE": {
        # Performance Monitoring
        "PERFORMANCE_MONITORING": True,
        "SLOW_QUERY_THRESHOLD": 1000, # in milliseconds
    }
}
```

## 7. Best Practices

- **Enable Monitoring in Development**: Use the performance monitoring tools during development to identify bottlenecks early.
- **Use `graphene-django-optimizer`**: For complex queries, `graphene-django-optimizer` can provide more fine-grained control over query optimization.
- **Analyze your Queries**: Regularly check the complexity and depth of your queries, especially those used in production.
- **Tune your Settings**: Adjust `max_query_depth` and `max_query_complexity` based on the needs of your application.
- **Use Dataloaders**: Ensure dataloaders are enabled to avoid N+1 query problems in nested resolvers.
- **Selective Fields**: Always encourage clients to request only the fields they need.

By following this guide, you can significantly improve the performance and reliability of your GraphQL API built with `rail-django-graphql`.
