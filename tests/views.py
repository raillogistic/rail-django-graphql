"""
Vues Django pour les tests.

Ce module fournit:
- Vues de test pour les endpoints
- Utilitaires de test via HTTP
- Vues de débogage pour les tests
"""

import json
import time
from datetime import datetime
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from django.core.cache import cache
from django.db import connection

from .models import TestLogEntry, TestPerformanceModel


def health_check(request):
    """Endpoint de vérification de santé pour les tests."""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': _check_database(),
        'cache': _check_cache(),
        'settings': {
            'debug': settings.DEBUG,
            'testing': getattr(settings, 'TESTING', False),
        }
    })


def status_check(request):
    """Endpoint de vérification de statut détaillé."""
    return JsonResponse({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'environment': 'test',
        'components': {
            'database': _check_database_detailed(),
            'cache': _check_cache_detailed(),
            'graphql': _check_graphql(),
        },
        'metrics': _get_test_metrics(),
    })


@csrf_exempt
@require_http_methods(["POST"])
def log_test_result(request):
    """Endpoint pour enregistrer les résultats de test."""
    try:
        data = json.loads(request.body)
        
        log_entry = TestLogEntry.objects.create(
            test_name=data.get('test_name', ''),
            test_type=data.get('test_type', 'unknown'),
            status=data.get('status', 'unknown'),
            duration=data.get('duration'),
            error_message=data.get('error_message', ''),
            traceback=data.get('traceback', ''),
            metadata=data.get('metadata', {})
        )
        
        return JsonResponse({
            'success': True,
            'log_id': log_entry.id,
            'message': 'Résultat de test enregistré'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def record_performance(request):
    """Endpoint pour enregistrer les métriques de performance."""
    try:
        data = json.loads(request.body)
        
        perf_record = TestPerformanceModel.objects.create(
            name=data.get('name', ''),
            description=data.get('description', ''),
            execution_time=data.get('execution_time'),
            memory_usage=data.get('memory_usage')
        )
        
        return JsonResponse({
            'success': True,
            'record_id': perf_record.id,
            'message': 'Métriques de performance enregistrées'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


class DebugView(View):
    """Vue de débogage pour les tests."""
    
    def get(self, request):
        """Affiche les informations de débogage."""
        debug_info = {
            'request_info': {
                'method': request.method,
                'path': request.path,
                'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
                'headers': dict(request.headers),
                'get_params': dict(request.GET),
            },
            'django_info': {
                'debug': settings.DEBUG,
                'testing': getattr(settings, 'TESTING', False),
                'databases': list(settings.DATABASES.keys()),
                'installed_apps': settings.INSTALLED_APPS,
            },
            'system_info': {
                'timestamp': datetime.now().isoformat(),
                'database_queries': len(connection.queries),
            }
        }
        
        return JsonResponse(debug_info, indent=2)


class SlowView(View):
    """Vue lente pour tester les timeouts."""
    
    def get(self, request):
        """Répond lentement pour tester les timeouts."""
        delay = int(request.GET.get('delay', 5))  # Délai en secondes
        
        time.sleep(delay)
        
        return JsonResponse({
            'message': f'Réponse après {delay} secondes',
            'timestamp': datetime.now().isoformat(),
        })


class ErrorView(View):
    """Vue qui génère des erreurs pour les tests."""
    
    def get(self, request):
        """Génère différents types d'erreurs."""
        error_type = request.GET.get('type', 'generic')
        
        if error_type == 'server_error':
            raise Exception("Erreur serveur simulée")
        elif error_type == 'value_error':
            raise ValueError("Erreur de valeur simulée")
        elif error_type == 'key_error':
            raise KeyError("Clé manquante simulée")
        elif error_type == 'type_error':
            raise TypeError("Erreur de type simulée")
        else:
            raise RuntimeError("Erreur générique simulée")


@csrf_exempt
def echo_view(request):
    """Vue qui renvoie les données reçues (utile pour les tests)."""
    response_data = {
        'method': request.method,
        'path': request.path,
        'timestamp': datetime.now().isoformat(),
    }
    
    if request.method == 'GET':
        response_data['query_params'] = dict(request.GET)
    
    elif request.method == 'POST':
        try:
            if request.content_type == 'application/json':
                response_data['json_data'] = json.loads(request.body)
            else:
                response_data['post_data'] = dict(request.POST)
        except json.JSONDecodeError:
            response_data['raw_body'] = request.body.decode('utf-8', errors='ignore')
    
    return JsonResponse(response_data)


def cache_test_view(request):
    """Vue pour tester les opérations de cache."""
    action = request.GET.get('action', 'get')
    key = request.GET.get('key', 'test_key')
    
    if action == 'set':
        value = request.GET.get('value', 'test_value')
        timeout = int(request.GET.get('timeout', 300))
        cache.set(key, value, timeout)
        
        return JsonResponse({
            'action': 'set',
            'key': key,
            'value': value,
            'timeout': timeout,
            'success': True
        })
    
    elif action == 'get':
        value = cache.get(key)
        
        return JsonResponse({
            'action': 'get',
            'key': key,
            'value': value,
            'found': value is not None
        })
    
    elif action == 'delete':
        cache.delete(key)
        
        return JsonResponse({
            'action': 'delete',
            'key': key,
            'success': True
        })
    
    elif action == 'clear':
        cache.clear()
        
        return JsonResponse({
            'action': 'clear',
            'success': True
        })
    
    else:
        return JsonResponse({
            'error': 'Action non supportée',
            'supported_actions': ['get', 'set', 'delete', 'clear']
        }, status=400)


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def _check_database():
    """Vérifie la connexion à la base de données."""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return True
    except Exception:
        return False


def _check_database_detailed():
    """Vérification détaillée de la base de données."""
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            
        return {
            'status': 'connected',
            'vendor': connection.vendor,
            'queries_count': len(connection.queries),
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


def _check_cache():
    """Vérifie la connexion au cache."""
    try:
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        cache.delete('health_check')
        return result == 'ok'
    except Exception:
        return False


def _check_cache_detailed():
    """Vérification détaillée du cache."""
    try:
        test_key = 'health_check_detailed'
        test_value = 'test_value'
        
        # Test d'écriture
        cache.set(test_key, test_value, 10)
        
        # Test de lecture
        retrieved_value = cache.get(test_key)
        
        # Nettoyage
        cache.delete(test_key)
        
        return {
            'status': 'working',
            'write_success': True,
            'read_success': retrieved_value == test_value,
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


def _check_graphql():
    """Vérifie la disponibilité de GraphQL."""
    try:
        from graphene.test import Client
        from tests.schema import schema
        
        client = Client(schema)
        result = client.execute('{ __schema { types { name } } }')
        
        return {
            'status': 'available',
            'schema_types_count': len(result.data['__schema']['types']) if result.data else 0,
            'has_errors': bool(result.errors)
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


def _get_test_metrics():
    """Récupère les métriques de test."""
    try:
        from django.db.models import Count, Avg
        
        # Statistiques des logs de test
        log_stats = TestLogEntry.objects.aggregate(
            total_tests=Count('id'),
            avg_duration=Avg('duration')
        )
        
        # Statistiques par statut
        status_stats = TestLogEntry.objects.values('status').annotate(
            count=Count('id')
        )
        
        # Statistiques de performance
        perf_stats = TestPerformanceModel.objects.aggregate(
            total_performance_tests=Count('id'),
            avg_execution_time=Avg('execution_time'),
            avg_memory_usage=Avg('memory_usage')
        )
        
        return {
            'test_logs': log_stats,
            'status_distribution': {stat['status']: stat['count'] for stat in status_stats},
            'performance': perf_stats,
        }
    except Exception as e:
        return {
            'error': str(e)
        }
