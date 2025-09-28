#!/usr/bin/env python3
"""
Script de test complet pour vérifier la solution d'invalidation du cache GraphQL.
Ce script teste toutes les mutations Tag avec invalidation automatique du cache.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.core.cache import cache
from test_app.models import Tag
from test_app.schema import CreateTag, UpdateTag, DeleteTag, TagInput, invalidate_tag_cache
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_complete_solution():
    """Test complet de la solution d'invalidation du cache."""
    print("\n" + "="*80)
    print("🚀 TEST COMPLET DE LA SOLUTION D'INVALIDATION DU CACHE GRAPHQL")
    print("="*80)
    
    # Nettoyer le cache et la base de données
    cache.clear()
    Tag.objects.filter(name__startswith="TestComplete").delete()
    print("🧹 Cache et données de test nettoyés")
    
    test_results = {
        "create_mutation": False,
        "update_mutation": False,
        "delete_mutation": False,
        "cache_invalidation": False,
        "helper_function": False
    }
    
    # Test 1: Mutation CreateTag avec invalidation
    print("\n" + "="*50)
    print("📋 TEST 1: MUTATION CREATE_TAG")
    print("="*50)
    
    try:
        # Simuler un cache existant
        cache.set("graphql_all_tags", ["cached_tag1", "cached_tag2"], 300)
        cache.set("gql_query_tags", {"cached": "data"}, 300)
        
        print("📦 Cache simulé créé")
        
        # Créer un tag avec la mutation
        class MockInput:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        create_input = MockInput(name="TestCompleteCreate", color="#FF5733")
        create_mutation = CreateTag()
        create_result = create_mutation.mutate(None, None, input=create_input)
        
        if create_result and create_result.tag:
            print(f"✅ Tag créé: {create_result.tag.name} (ID: {create_result.tag.pk})")
            
            # Vérifier l'invalidation du cache
            if cache.get("graphql_all_tags") is None:
                print("✅ Cache invalidé automatiquement après création")
                test_results["create_mutation"] = True
                test_results["cache_invalidation"] = True
            else:
                print("❌ Cache non invalidé après création")
        else:
            print("❌ Échec de la création du tag")
            
    except Exception as e:
        print(f"❌ Erreur lors du test de création: {e}")
    
    # Test 2: Mutation UpdateTag avec invalidation
    print("\n" + "="*50)
    print("📋 TEST 2: MUTATION UPDATE_TAG")
    print("="*50)
    
    try:
        # Créer un tag à modifier
        test_tag = Tag.objects.create(name="TestCompleteUpdate", color="#00FF00")
        print(f"📝 Tag créé pour test de mise à jour: {test_tag.name}")
        
        # Simuler un cache
        cache.set("graphql_all_tags", ["cached_data"], 300)
        cache.set(f"graphql_tags_by_color_{test_tag.color}", ["green_tags"], 300)
        
        # Mettre à jour le tag
        update_input = MockInput(name="TestCompleteUpdated", color="#0066FF")
        update_mutation = UpdateTag()
        update_result = update_mutation.mutate(None, None, id=test_tag.pk, input=update_input)
        
        if update_result and update_result.tag:
            print(f"✅ Tag mis à jour: {update_result.tag.name} -> {update_result.tag.color}")
            
            # Vérifier l'invalidation du cache
            if cache.get("graphql_all_tags") is None:
                print("✅ Cache invalidé automatiquement après mise à jour")
                test_results["update_mutation"] = True
            else:
                print("❌ Cache non invalidé après mise à jour")
                
            # Vérifier l'invalidation de l'ancienne couleur
            if cache.get("graphql_tags_by_color_#00FF00") is None:
                print("✅ Cache de l'ancienne couleur invalidé")
            else:
                print("⚠️  Cache de l'ancienne couleur toujours présent")
        else:
            print("❌ Échec de la mise à jour du tag")
            
    except Exception as e:
        print(f"❌ Erreur lors du test de mise à jour: {e}")
    
    # Test 3: Mutation DeleteTag avec invalidation
    print("\n" + "="*50)
    print("📋 TEST 3: MUTATION DELETE_TAG")
    print("="*50)
    
    try:
        # Créer un tag à supprimer
        test_tag_delete = Tag.objects.create(name="TestCompleteDelete", color="#FF00FF")
        tag_id = test_tag_delete.pk
        print(f"🗑️  Tag créé pour test de suppression: {test_tag_delete.name}")
        
        # Simuler un cache
        cache.set("graphql_all_tags", ["cached_data"], 300)
        cache.set(f"tag_model_{tag_id}", {"tag": "data"}, 300)
        
        # Supprimer le tag
        delete_mutation = DeleteTag()
        delete_result = delete_mutation.mutate(None, None, id=tag_id)
        
        if delete_result and delete_result.success:
            print("✅ Tag supprimé avec succès")
            
            # Vérifier l'invalidation du cache
            if cache.get("graphql_all_tags") is None:
                print("✅ Cache invalidé automatiquement après suppression")
                test_results["delete_mutation"] = True
            else:
                print("❌ Cache non invalidé après suppression")
                
            # Vérifier que le tag n'existe plus
            if not Tag.objects.filter(pk=tag_id).exists():
                print("✅ Tag correctement supprimé de la base de données")
            else:
                print("❌ Tag toujours présent dans la base de données")
        else:
            print("❌ Échec de la suppression du tag")
            
    except Exception as e:
        print(f"❌ Erreur lors du test de suppression: {e}")
    
    # Test 4: Fonction helper d'invalidation
    print("\n" + "="*50)
    print("📋 TEST 4: FONCTION HELPER D'INVALIDATION")
    print("="*50)
    
    try:
        # Créer un tag pour tester la fonction helper
        helper_tag = Tag.objects.create(name="TestCompleteHelper", color="#FFFF00")
        
        # Simuler un cache
        cache.set("graphql_all_tags", ["helper_test"], 300)
        cache.set("gql_query_tags", {"helper": "data"}, 300)
        
        # Appeler la fonction helper
        invalidate_tag_cache(helper_tag)
        
        # Vérifier l'invalidation
        if cache.get("graphql_all_tags") is None and cache.get("gql_query_tags") is None:
            print("✅ Fonction helper fonctionne correctement")
            test_results["helper_function"] = True
        else:
            print("❌ Fonction helper n'invalide pas correctement le cache")
        
        # Nettoyer
        helper_tag.delete()
        
    except Exception as e:
        print(f"❌ Erreur lors du test de la fonction helper: {e}")
    
    # Test 5: Simulation du problème original et vérification de la solution
    print("\n" + "="*50)
    print("📋 TEST 5: SIMULATION DU PROBLÈME ORIGINAL")
    print("="*50)
    
    try:
        print("🔍 Simulation: Utilisateur crée un tag via GraphiQL...")
        
        # Simuler une requête tags qui met en cache les résultats
        initial_tags = list(Tag.objects.filter(name__startswith="TestComplete"))
        cache.set("graphql_all_tags", [tag.name for tag in initial_tags], 300)
        print(f"📦 Cache initial: {len(initial_tags)} tags")
        
        # Créer un nouveau tag (comme dans GraphiQL)
        new_tag_input = MockInput(name="TestCompleteNewTag", color="#00FFFF")
        create_mutation = CreateTag()
        new_tag_result = create_mutation.mutate(None, None, input=new_tag_input)
        
        if new_tag_result and new_tag_result.tag:
            print(f"✅ Nouveau tag créé: {new_tag_result.tag.name}")
            
            # Simuler une nouvelle requête tags (comme après création dans GraphiQL)
            cached_tags = cache.get("graphql_all_tags")
            
            if cached_tags is None:
                # Le cache a été invalidé, donc une nouvelle requête récupérera les données fraîches
                fresh_tags = list(Tag.objects.filter(name__startswith="TestComplete"))
                print(f"✅ SOLUTION FONCTIONNE: Cache invalidé, {len(fresh_tags)} tags récupérés")
                print("✅ Le nouveau tag sera visible immédiatement sans rafraîchissement!")
            else:
                print("❌ PROBLÈME PERSISTE: Cache non invalidé, ancien résultat retourné")
                print("❌ L'utilisateur devra rafraîchir la page pour voir le nouveau tag")
        
    except Exception as e:
        print(f"❌ Erreur lors de la simulation: {e}")
    
    # Résumé des résultats
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*80)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n🎯 SCORE GLOBAL: {passed_tests}/{total_tests} tests réussis")
    
    if passed_tests == total_tests:
        print("\n🎉 FÉLICITATIONS! SOLUTION COMPLÈTEMENT FONCTIONNELLE!")
        print("✅ Toutes les mutations Tag invalident automatiquement le cache")
        print("✅ Les nouveaux objets apparaîtront immédiatement dans GraphiQL")
        print("✅ Plus besoin de rafraîchir la page!")
    else:
        print(f"\n⚠️  ATTENTION: {total_tests - passed_tests} test(s) ont échoué")
        print("🔧 Vérifiez les erreurs ci-dessus et corrigez les problèmes")
    
    print("\n🚀 PROCHAINES ÉTAPES POUR L'UTILISATEUR:")
    print("1. Redémarrer le serveur Django: python manage.py runserver")
    print("2. Aller sur http://localhost:8000/graphql/")
    print("3. Tester la création d'un tag:")
    print("   mutation { createTag(input: {name: \"Test\", color: \"#FF0000\"}) { tag { id name color } } }")
    print("4. Immédiatement après, exécuter:")
    print("   query { tags { id name color } }")
    print("5. Vérifier que le nouveau tag apparaît sans rafraîchissement!")
    
    # Nettoyer les données de test
    Tag.objects.filter(name__startswith="TestComplete").delete()
    cache.clear()
    print("\n🧹 Données de test nettoyées")

if __name__ == "__main__":
    test_complete_solution()