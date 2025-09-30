"""URL Configuration for Django GraphQL Auto-Generation

This module defines the URL patterns for the Django GraphQL Auto-Generation system.
"""

from django.urls import path, include
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from .schema import schema
from .views.health_views import HealthDashboardView
from rail_django_graphql.middleware.performance import GraphQLPerformanceView

def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({"status": "healthy", "service": "rail_django_graphql"})


# Create GraphQL view with the auto-generated schema
graphql_view = GraphQLView.as_view(schema=schema, graphiql=True)

# Main URL patterns for the rail_django_graphql app
urlpatterns = [
    path("graphql/", csrf_exempt(graphql_view), name="graphql"),
    path("playground/", csrf_exempt(graphql_view), name="graphql_playground"),
    path("health/", health_check, name="health_check"),
    path("health/dashboard/", HealthDashboardView.as_view(), name="health_dashboard"),
    path('graphql/performance/', GraphQLPerformanceView.as_view()),
]
