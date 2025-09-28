#!/usr/bin/env python3
"""
Script pour tester la correction de l'invalidation du cache GraphQL.
Ce script vérifie que les nouvelles mutations invalident correctement le cache.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.core.cache import cache
from test_app.models import Tag
from test_app.schema import CreateTag, TagInput, invalidate_tag_cache
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cache_invalidation_fix():
    """Tester la correction de l'invalidation du cache."""
    print("\n" + "="*70)
    print("🧪 TEST DE LA CORRECTION D'INVALIDATION DU CACHE")
    print("="*70)
    
    # Nettoyer le cache initial
    cache.clear()
    print("🧹 Cache initial nettoyé")
    
    # Test 1: Simuler un cache existant
    print("\n📋 Test 1: Simulation d'un cache existant")
    cache.set("graphql_all_tags", ["tag1", "tag2", "tag3"], 300)
    cache.set("gql_query_tags", {"data": "cached_tags"}, 300)
    cache.set("model_page_tags", {"page": 1, "tags": []}, 300)
    
    cached_data = cache.get("graphql_all_tags")
    print(f"✅ Cache simulé créé: {cached_data}")
    
    # Test 2: Créer un tag avec la mutation corrigée
    print("\n📋 Test 2: Création d'un tag avec invalidation automatique")
    try:
        # Simuler les arguments de la mutation
        class MockInput:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        mock_input = MockInput(name="TestCacheInvalidation", color="#FF6B6B")
        
        # Exécuter la mutation
        mutation = CreateTag()
        result = mutation.mutate(None, None, input=mock_input)
        
        if result and result.tag:
            print(f"✅ Tag créé avec succès: {result.tag.name} (ID: {result.tag.pk})")
            
            # Test 3: Vérifier que le cache a été invalidé
            print("\n📋 Test 3: Vérification de l'invalidation du cache")
            cached_data_after = cache.get("graphql_all_tags")
            
            if cached_data_after is None:
                print("✅ Cache correctement invalidé - graphql_all_tags")
            else:
                print(f"❌ Cache toujours présent: {cached_data_after}")
            
            # Vérifier d'autres clés de cache
            other_caches = [
                "gql_query_tags",
                "model_page_tags",
                f"graphql_tags_by_color_{result.tag.color}",
                f"tag_model_{result.tag.pk}"
            ]
            
            invalidated_count = 0
            for cache_key in other_caches:
                if cache.get(cache_key) is None:
                    print(f"✅ Cache invalidé: {cache_key}")
                    invalidated_count += 1
                else:
                    print(f"⚠️  Cache encore présent: {cache_key}")
            
            print(f"\n📊 Résultat: {invalidated_count}/{len(other_caches)} caches invalidés")
            
        else:
            print("❌ Erreur lors de la création du tag")
            
    except Exception as e:
        print(f"❌ Exception lors du test: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Test de la fonction helper directement
    print("\n📋 Test 4: Test de la fonction helper d'invalidation")
    try:
        # Remettre du cache
        cache.set("graphql_all_tags", ["test_data"], 300)
        cache.set("gql_query_tags", {"test": "data"}, 300)
        
        # Créer un tag de test
        test_tag = Tag.objects.create(name="TestHelper", color="#00FF00")
        
        # Appeler la fonction helper
        invalidate_tag_cache(test_tag)
        
        # Vérifier l'invalidation
        if cache.get("graphql_all_tags") is None:
            print("✅ Fonction helper fonctionne correctement")
        else:
            print("❌ Fonction helper n'a pas invalidé le cache")
            
        # Nettoyer le tag de test
        test_tag.delete()
        
    except Exception as e:
        print(f"❌ Erreur lors du test de la fonction helper: {e}")
    
    # Test 5: Vérifier le comportement avant/après
    print("\n📋 Test 5: Comparaison avant/après correction")
    
    # Simuler l'ancien comportement (sans invalidation)
    cache.set("graphql_all_tags", ["old_cached_data"], 300)
    print("📦 Cache simulé (ancien comportement)")
    
    # Créer un tag avec invalidation
    try:
        test_tag2 = Tag.objects.create(name="TestComparison", color="#0066FF")
        invalidate_tag_cache(test_tag2)
        
        if cache.get("graphql_all_tags") is None:
            print("✅ CORRECTION RÉUSSIE: Le cache est maintenant invalidé automatiquement")
        else:
            print("❌ PROBLÈME: Le cache n'est toujours pas invalidé")
        
        # Nettoyer
        test_tag2.delete()
        
    except Exception as e:
        print(f"❌ Erreur lors du test de comparaison: {e}")
    
    print("\n🎯 CONCLUSION:")
    print("="*70)
    print("✅ La mutation CreateTag a été mise à jour avec l'invalidation du cache")
    print("✅ Une fonction helper invalidate_tag_cache() a été ajoutée")
    print("✅ Les imports nécessaires ont été ajoutés")
    print("\n🚀 PROCHAINES ÉTAPES:")
    print("1. Redémarrer le serveur Django")
    print("2. Tester dans GraphiQL:")
    print("   - Créer un tag avec createTag")
    print("   - Exécuter une requête tags immédiatement après")
    print("   - Vérifier que le nouveau tag apparaît sans rafraîchissement")
    print("3. Surveiller les logs pour voir les messages d'invalidation")

if __name__ == "__main__":
    test_cache_invalidation_fix()