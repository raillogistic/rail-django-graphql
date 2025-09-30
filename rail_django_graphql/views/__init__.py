"""
Package d'initialisation pour les vues de rail_django_graphql.

Ce module permet d'importer les vues pour différents composants du système.
"""

# Rendre les imports disponibles au niveau du package
from .health_views import (
    HealthDashboardView,
    HealthAPIView,
    health_check_endpoint,
    health_metrics_endpoint,
    health_components_endpoint,
    HealthHistoryView,
)

__all__ = [
    "HealthDashboardView",
    "HealthAPIView",
    "health_check_endpoint",
    "health_metrics_endpoint",
    "health_components_endpoint",
    "HealthHistoryView",
]
