"""
Configuration des URLs pour les tests.

Ce module configure:
- Endpoints GraphQL pour les tests
- Vues de test
- URLs d'administration pour les tests
"""

from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

from tests.schema import schema

urlpatterns = [
    # Administration Django
    path('admin/', admin.site.urls),
    
    # Endpoint GraphQL principal
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
    
    # Endpoint GraphQL pour les tests (sans CSRF)
    path('graphql/test/', csrf_exempt(GraphQLView.as_view(schema=schema))),
    
    # Endpoint GraphQL avec authentification
    path('graphql/auth/', GraphQLView.as_view(graphiql=True, schema=schema)),
    
    # Endpoints pour les tests d'API
    path('api/test/', include([
        path('health/', lambda request: HttpResponse('OK'), name='health_check'),
        path('status/', lambda request: JsonResponse({'status': 'ok'}), name='status_check'),
    ])),
]

# Ajouter des URLs de debug en mode test
import os
if os.environ.get('TESTING'):
    from django.http import HttpResponse, JsonResponse
    
    def test_view(request):
        """Vue de test simple."""
        return HttpResponse('Test OK')
    
    def test_json_view(request):
        """Vue de test JSON."""
        return JsonResponse({'message': 'Test OK', 'status': 'success'})
    
    def test_error_view(request):
        """Vue de test pour les erreurs."""
        raise Exception('Test error')
    
    # Ajouter les vues de test
    urlpatterns += [
        path('test/', test_view, name='test_view'),
        path('test/json/', test_json_view, name='test_json_view'),
        path('test/error/', test_error_view, name='test_error_view'),
    ]
