"""URL Configuration for Django GraphQL Auto-Generation

This module defines the URL patterns for the Django GraphQL Auto-Generation system.
"""

from django.urls import path, include
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from .schema import schema
from .views.health_views import HealthDashboardView

def health_check(request):
    """Simple health check endpoint."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'django_graphql_auto'
    })

# Create GraphQL view with the auto-generated schema
graphql_view = GraphQLView.as_view(schema=schema, graphiql=True)

# Main URL patterns for the django_graphql_auto app
urlpatterns = [
    path('graphql/', csrf_exempt(graphql_view), name='graphql'),
    path('playground/', csrf_exempt(graphql_view), name='graphql_playground'),
    path('health/', health_check, name='health_check'),
    path('health/dashboard/', HealthDashboardView.as_view(), name='health_dashboard'),
]
