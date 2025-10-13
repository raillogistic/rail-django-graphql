"""
Package d'initialisation pour les vues de rail_django_graphql.

Ce module permet d'importer les vues pour différents composants du système.
"""

from .graphql_views import GraphQLPlaygroundView, MultiSchemaGraphQLView, SchemaListView

# Rendre les imports disponibles au niveau du package
from .health_views import (
    HealthAPIView,
    HealthDashboardView,
    HealthHistoryView,
    health_check_endpoint,
    health_components_endpoint,
    health_metrics_endpoint,
)

__all__ = [
    "HealthDashboardView",
    "HealthAPIView",
    "health_check_endpoint",
    "health_metrics_endpoint",
    "health_components_endpoint",
    "HealthHistoryView",
    "MultiSchemaGraphQLView",
    "SchemaListView",
    "GraphQLPlaygroundView",
]
