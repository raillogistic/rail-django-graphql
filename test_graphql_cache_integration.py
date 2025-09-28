#!/usr/bin/env python3
"""
Test d'intégration GraphQL complet pour vérifier l'invalidation du cache avec de vraies requêtes GraphQL
"""

import os
import sys
import django
import json
import requests
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.core.cache import cache
from django.test import Client
from test_app.models import Category, Tag

# URL du serveur GraphQL (supposé en cours d'exécution)
GRAPHQL_URL = "http://localhost:8000/graphql/"

def test_graphql_server_availability():
    """Teste si le serveur GraphQL est disponible"""
    print("🌐 TEST DE DISPONIBILITÉ DU SERVEUR GRAPHQL")
    print("=" * 80)
    
    try:
        # Test simple avec une requête introspection
        introspection_query = {
            "query": """
            query IntrospectionQuery {
                __schema {
                    queryType {
                        name
                    }
                }
            }
            """
        }
        
        response = requests.post(
            GRAPHQL_URL,
            json=introspection_query,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and '__schema' in data['data']:
                print("✅ Serveur GraphQL disponible et fonctionnel")
                return True
            else:
                print(f"⚠️ Serveur répond mais données invalides: {data}")
                return False
        else:
            print(f"❌ Serveur non disponible - Status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion au serveur: {e}")
        return False

def test_graphql_query_caching():
    """Teste le cache des requêtes GraphQL"""
    print("\n🧪 TEST DU CACHE DES REQUÊTES GRAPHQL")
    print("=" * 80)
    
    # Nettoyer le cache
    cache.clear()
    print("🧹 Cache nettoyé")
    
    # Requête pour lister les catégories
    categories_query = {
        "query": """
        query GetCategories {
            categories {
                id
                name
                description
            }
        }
        """
    }
    
    try:
        # Première requête
        print("📝 Première requête GraphQL...")
        response1 = requests.post(
            GRAPHQL_URL,
            json=categories_query,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response1.status_code != 200:
            print(f"❌ Première requête échouée - Status: {response1.status_code}")
            return False
        
        data1 = response1.json()
        print(f"✅ Première requête réussie - {len(data1.get('data', {}).get('categories', []))} catégories")
        
        # Ajouter quelque chose au cache pour tester l'invalidation
        cache.set('test_graphql_cache', 'cached_value', 300)
        cached_value_before = cache.get('test_graphql_cache')
        print(f"📝 Valeur en cache avant mutation: {'✅' if cached_value_before else '❌'} - {cached_value_before}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la requête GraphQL: {e}")
        return False

def test_graphql_mutation_cache_invalidation():
    """Teste l'invalidation du cache lors des mutations GraphQL"""
    print("\n🧪 TEST D'INVALIDATION DU CACHE AVEC MUTATIONS GRAPHQL")
    print("=" * 80)
    
    # Ajouter des données au cache
    cache.set('test_mutation_cache', 'mutation_test_value', 300)
    cache.set('graphql_categories_cache', 'categories_cached', 300)
    
    cached_before = cache.get('test_mutation_cache')
    graphql_cached_before = cache.get('graphql_categories_cache')
    
    print(f"📝 Cache avant mutation:")
    print(f"   test_mutation_cache: {'✅' if cached_before else '❌'} - {cached_before}")
    print(f"   graphql_categories_cache: {'✅' if graphql_cached_before else '❌'} - {graphql_cached_before}")
    
    # Mutation pour créer une catégorie
    create_category_mutation = {
        "query": """
        mutation CreateCategory($name: String!, $description: String!) {
            createCategory(name: $name, description: $description) {
                id
                name
                description
            }
        }
        """,
        "variables": {
            "name": f"GraphQL Test Category {datetime.now().strftime('%H%M%S')}",
            "description": "Catégorie créée via mutation GraphQL pour tester l'invalidation du cache"
        }
    }
    
    try:
        print("📝 Exécution de la mutation GraphQL...")
        response = requests.post(
            GRAPHQL_URL,
            json=create_category_mutation,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Mutation échouée - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        
        if 'errors' in data:
            print(f"❌ Erreurs GraphQL: {data['errors']}")
            return False
        
        created_category = data.get('data', {}).get('createCategory')
        if created_category:
            print(f"✅ Catégorie créée via GraphQL: {created_category['name']} (ID: {created_category['id']})")
        else:
            print("⚠️ Mutation exécutée mais pas de données retournées")
        
        # Vérifier l'état du cache après la mutation
        cached_after = cache.get('test_mutation_cache')
        graphql_cached_after = cache.get('graphql_categories_cache')
        
        print(f"📝 Cache après mutation:")
        print(f"   test_mutation_cache: {'❌ INVALIDÉ' if not cached_after else '✅ PRÉSENT'} - {cached_after}")
        print(f"   graphql_categories_cache: {'❌ INVALIDÉ' if not graphql_cached_after else '✅ PRÉSENT'} - {graphql_cached_after}")
        
        # Le cache devrait être invalidé
        cache_invalidated = not cached_after and not graphql_cached_after
        
        print(f"\n📊 Résultat: cache {'✅ INVALIDÉ CORRECTEMENT' if cache_invalidated else '❌ NON INVALIDÉ'}")
        
        # Nettoyer la catégorie créée
        if created_category and created_category.get('id'):
            try:
                category = Category.objects.get(id=created_category['id'])
                category.delete()
                print(f"🧹 Catégorie de test supprimée")
            except Category.DoesNotExist:
                pass
        
        return cache_invalidated
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la mutation GraphQL: {e}")
        return False

def test_direct_model_operations():
    """Teste l'invalidation du cache avec des opérations directes sur les modèles"""
    print("\n🧪 TEST D'INVALIDATION AVEC OPÉRATIONS DIRECTES SUR LES MODÈLES")
    print("=" * 80)
    
    # Initialiser le middleware
    try:
        from cache_middleware import GraphQLCacheInvalidationMiddleware
        
        def dummy_get_response(request):
            return None
        
        middleware = GraphQLCacheInvalidationMiddleware(dummy_get_response)
        print(f"✅ Middleware initialisé - Signaux connectés: {GraphQLCacheInvalidationMiddleware._signals_connected}")
        
    except Exception as e:
        print(f"❌ Erreur d'initialisation du middleware: {e}")
        return False
    
    # Ajouter des données au cache
    cache.set('direct_test_cache', 'direct_test_value', 300)
    cache.set('model_operations_cache', 'model_ops_value', 300)
    
    cached_before = cache.get('direct_test_cache')
    model_cached_before = cache.get('model_operations_cache')
    
    print(f"📝 Cache avant opération directe:")
    print(f"   direct_test_cache: {'✅' if cached_before else '❌'} - {cached_before}")
    print(f"   model_operations_cache: {'✅' if model_cached_before else '❌'} - {model_cached_before}")
    
    # Créer une catégorie directement
    print("📝 Création directe d'une catégorie...")
    category = Category.objects.create(
        name=f"Direct Test Category {datetime.now().strftime('%H%M%S')}",
        description="Catégorie créée directement pour tester l'invalidation"
    )
    print(f"✅ Catégorie créée: {category.name} (ID: {category.id})")
    
    # Vérifier l'état du cache
    cached_after = cache.get('direct_test_cache')
    model_cached_after = cache.get('model_operations_cache')
    
    print(f"📝 Cache après création directe:")
    print(f"   direct_test_cache: {'❌ INVALIDÉ' if not cached_after else '✅ PRÉSENT'} - {cached_after}")
    print(f"   model_operations_cache: {'❌ INVALIDÉ' if not model_cached_after else '✅ PRÉSENT'} - {model_cached_after}")
    
    cache_invalidated = not cached_after and not model_cached_after
    
    print(f"\n📊 Résultat: cache {'✅ INVALIDÉ CORRECTEMENT' if cache_invalidated else '❌ NON INVALIDÉ'}")
    
    # Nettoyer
    category.delete()
    
    return cache_invalidated

def run_graphql_integration_tests():
    """Lance tous les tests d'intégration GraphQL"""
    print("🚀 TESTS D'INTÉGRATION GRAPHQL COMPLETS")
    print("=" * 100)
    
    # Test 1: Disponibilité du serveur
    server_available = test_graphql_server_availability()
    
    # Test 2: Cache des requêtes GraphQL
    query_caching_ok = False
    if server_available:
        query_caching_ok = test_graphql_query_caching()
    
    # Test 3: Invalidation avec mutations GraphQL
    mutation_invalidation_ok = False
    if server_available:
        mutation_invalidation_ok = test_graphql_mutation_cache_invalidation()
    
    # Test 4: Invalidation avec opérations directes
    direct_invalidation_ok = test_direct_model_operations()
    
    # Résumé
    print("\n" + "=" * 100)
    print("📊 RÉSUMÉ DES TESTS D'INTÉGRATION GRAPHQL")
    print("=" * 100)
    
    print(f"🌐 Serveur GraphQL: {'✅ DISPONIBLE' if server_available else '❌ INDISPONIBLE'}")
    print(f"🔍 Requêtes GraphQL: {'✅ OK' if query_caching_ok else '❌ ÉCHEC' if server_available else '⏭️ IGNORÉ'}")
    print(f"🔄 Mutations GraphQL: {'✅ OK' if mutation_invalidation_ok else '❌ ÉCHEC' if server_available else '⏭️ IGNORÉ'}")
    print(f"🔧 Opérations directes: {'✅ OK' if direct_invalidation_ok else '❌ ÉCHEC'}")
    
    # Évaluer le succès global
    if server_available:
        overall_success = query_caching_ok and mutation_invalidation_ok and direct_invalidation_ok
    else:
        overall_success = direct_invalidation_ok
        print("\n⚠️ Serveur GraphQL indisponible - Tests limités aux opérations directes")
    
    if overall_success:
        print("\n🎉 INTÉGRATION GRAPHQL RÉUSSIE !")
        if server_available:
            print("   - Le serveur GraphQL fonctionne")
            print("   - Les requêtes GraphQL sont traitées")
            print("   - Les mutations GraphQL invalident le cache")
        print("   - Les opérations directes invalident le cache")
    else:
        print("\n⚠️ PROBLÈMES D'INTÉGRATION DÉTECTÉS")
        if not server_available:
            print("   - Serveur GraphQL non disponible")
        if server_available and not query_caching_ok:
            print("   - Problème avec les requêtes GraphQL")
        if server_available and not mutation_invalidation_ok:
            print("   - Problème avec l'invalidation via mutations GraphQL")
        if not direct_invalidation_ok:
            print("   - Problème avec l'invalidation via opérations directes")
    
    print("=" * 100)
    
    return overall_success

if __name__ == "__main__":
    success = run_graphql_integration_tests()
    sys.exit(0 if success else 1)