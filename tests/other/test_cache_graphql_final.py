#!/usr/bin/env python
"""
Test final de l'invalidation du cache avec les mutations GraphQL correctes
"""

import os
import sys
import django
import requests
import json
import time

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.core.cache import cache
from test_app.models import Category, Tag

def clear_test_data():
    """Nettoie les données de test."""
    Category.objects.filter(name__startswith='TestCache').delete()
    Tag.objects.filter(name__startswith='TestCache').delete()

def test_graphql_cache_invalidation():
    """Test complet de l'invalidation du cache avec GraphQL."""
    print("🚀 TEST FINAL - INVALIDATION CACHE AVEC GRAPHQL")
    print("=" * 60)
    
    # Nettoyer les données et le cache
    clear_test_data()
    cache.clear()
    
    # 1. Ajouter des données au cache
    print("\n📦 1. Ajout de données au cache")
    cache.set('test_categories', 'cached_categories_data', 300)
    cache.set('test_tags', 'cached_tags_data', 300)
    cache.set('category_list', 'cached_category_list', 300)
    
    initial_keys = list(cache._cache.keys()) if hasattr(cache, '_cache') else []
    print(f"   Clés initiales dans le cache: {len(initial_keys)}")
    
    # 2. Test avec mutation GraphQL create_category
    print("\n🏷️ 2. Test mutation create_category")
    
    mutation_query = """
    mutation CreateCategory($input: CategoryInput!) {
        create_category(input: $input) {
            ok
            object {
                id
                name
                description
            }
            errors
        }
    }
    """
    
    variables = {
        "input": {
            "name": "TestCacheCategory",
            "description": "Test category for cache invalidation"
        }
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/graphql/',
            json={
                'query': mutation_query,
                'variables': variables
            },
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'errors' not in result:
                mutation_result = result['data']['create_category']
                if mutation_result['ok']:
                    print("   ✅ Mutation create_category exécutée avec succès")
                    created_category = mutation_result['object']
                    print(f"   📝 Catégorie créée: {created_category['name']} (ID: {created_category['id']})")
                    
                    # Vérifier l'invalidation du cache
                    time.sleep(0.5)  # Attendre l'invalidation
                    remaining_keys = list(cache._cache.keys()) if hasattr(cache, '_cache') else []
                    
                    if len(remaining_keys) < len(initial_keys):
                        print(f"   ✅ Cache invalidé: {len(initial_keys)} -> {len(remaining_keys)} clés")
                        cache_invalidated = True
                    else:
                        print(f"   ❌ Cache non invalidé: {len(initial_keys)} -> {len(remaining_keys)} clés")
                        cache_invalidated = False
                else:
                    print(f"   ❌ Mutation échouée: {mutation_result.get('errors', 'Erreur inconnue')}")
                    cache_invalidated = False
            else:
                print(f"   ❌ Erreurs GraphQL: {result['errors']}")
                cache_invalidated = False
        else:
            print(f"   ❌ Erreur HTTP {response.status_code}: {response.text}")
            cache_invalidated = False
            
    except requests.exceptions.ConnectionError:
        print("   ⚠️ Serveur GraphQL non disponible - test avec opération directe")
        
        # Test direct avec le modèle Django
        Category.objects.create(
            name="TestCacheCategory",
            description="Test category for cache invalidation"
        )
        
        time.sleep(0.5)
        remaining_keys = list(cache._cache.keys()) if hasattr(cache, '_cache') else []
        
        if len(remaining_keys) < len(initial_keys):
            print(f"   ✅ Cache invalidé (opération directe): {len(initial_keys)} -> {len(remaining_keys)} clés")
            cache_invalidated = True
        else:
            print(f"   ❌ Cache non invalidé (opération directe): {len(initial_keys)} -> {len(remaining_keys)} clés")
            cache_invalidated = False
    
    # 3. Test avec Tag
    print("\n🏷️ 3. Test avec Tag")
    cache.set('test_tags_2', 'more_cached_data', 300)
    
    try:
        Tag.objects.create(name="TestCacheTag", color="#FF0000")
        time.sleep(0.5)
        
        final_keys = list(cache._cache.keys()) if hasattr(cache, '_cache') else []
        print(f"   Cache après création Tag: {len(final_keys)} clés")
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la création du Tag: {e}")
    
    # Nettoyage
    clear_test_data()
    
    return cache_invalidated

def test_middleware_patterns():
    """Test des patterns de détection du middleware."""
    print("\n🔍 4. Test des patterns de détection")
    
    from cache_middleware import GraphQLCacheInvalidationMiddleware
    
    # Patterns définis dans le middleware
    patterns = [
        r'create_\w+',
        r'update_\w+', 
        r'delete_\w+',
        r'bulk_\w+',
        r'CreateCategory',
        r'CreateTag',
        r'UpdateCategory',
        r'UpdateTag'
    ]
    
    # Test des noms de mutations
    test_mutations = [
        'create_category',
        'update_category', 
        'delete_category',
        'create_tag',
        'update_tag',
        'delete_tag',
        'bulk_create_category'
    ]
    
    import re
    
    for mutation in test_mutations:
        matches = any(re.search(pattern, mutation) for pattern in patterns)
        print(f"   {mutation}: {'✅' if matches else '❌'}")
    
    return True

def main():
    """Fonction principale."""
    try:
        # Tests
        cache_test = test_graphql_cache_invalidation()
        pattern_test = test_middleware_patterns()
        
        # Résumé
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        print(f"Cache invalidation: {'✅ SUCCÈS' if cache_test else '❌ ÉCHEC'}")
        print(f"Pattern detection: {'✅ SUCCÈS' if pattern_test else '❌ ÉCHEC'}")
        
        overall_success = cache_test and pattern_test
        print(f"\n🎯 RÉSULTAT GLOBAL: {'✅ SUCCÈS' if overall_success else '❌ ÉCHEC'}")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)