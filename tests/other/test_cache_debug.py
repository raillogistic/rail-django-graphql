#!/usr/bin/env python
"""
Script de débogage complet pour tester le comportement du cache GraphQL.
Ce script teste les opérations CRUD et vérifie l'invalidation du cache.
"""

import os
import sys
import django
import time
import json
from typing import Dict, Any

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.core.cache import cache
from django.contrib.auth.models import User
from test_app.models import Category, Tag, Post, Comment
from graphene.test import Client
from test_app.schema import test_app_schema as schema

def clear_all_data():
    """Nettoie toutes les données de test."""
    print("🧹 Nettoyage des données existantes...")
    Comment.objects.all().delete()
    Post.objects.all().delete()
    Tag.objects.all().delete()
    Category.objects.all().delete()
    User.objects.filter(username__startswith='test_').delete()
    cache.clear()
    print("✅ Données nettoyées")

def create_test_user():
    """Crée un utilisateur de test."""
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    return user

def test_cache_behavior():
    """Teste le comportement du cache avec des opérations CRUD."""
    print("\n🔍 DÉBOGAGE DU CACHE GRAPHQL")
    print("=" * 50)
    
    client = Client(schema)
    
    # Test 1: Vérifier l'état initial du cache
    print("\n1️⃣ État initial du cache")
    print("-" * 30)
    
    # Requête initiale pour lister les catégories
    query_categories = """
    query {
        categories {
            id
            name
            description
        }
    }
    """
    
    result1 = client.execute(query_categories)
    print(f"Première requête - Catégories trouvées: {len(result1.get('data', {}).get('categories', []))}")
    
    # Test 2: Créer une nouvelle catégorie
    print("\n2️⃣ Création d'une nouvelle catégorie")
    print("-" * 30)
    
    mutation_create_category = """
    mutation {
        createCategory(input: {
            name: "Catégorie Test Cache"
            description: "Test d'invalidation du cache"
        }) {
            category {
                id
                name
                description
            }
        }
    }
    """
    
    create_result = client.execute(mutation_create_category)
    if create_result.get('errors'):
        print(f"❌ Erreur lors de la création: {create_result['errors']}")
        return False
    
    created_category = create_result['data']['createCategory']['category']
    print(f"✅ Catégorie créée: {created_category['name']} (ID: {created_category['id']})")
    
    # Test 3: Vérifier immédiatement si la nouvelle catégorie apparaît
    print("\n3️⃣ Vérification immédiate (cache invalidé ?)")
    print("-" * 30)
    
    result2 = client.execute(query_categories)
    categories_after_create = result2.get('data', {}).get('categories', [])
    print(f"Requête après création - Catégories trouvées: {len(categories_after_create)}")
    
    # Vérifier si la nouvelle catégorie est présente
    new_category_found = any(
        cat['name'] == "Catégorie Test Cache" 
        for cat in categories_after_create
    )
    
    if new_category_found:
        print("✅ SUCCÈS: La nouvelle catégorie apparaît immédiatement")
        cache_working = True
    else:
        print("❌ ÉCHEC: La nouvelle catégorie n'apparaît pas (cache non invalidé)")
        cache_working = False
    
    # Test 4: Attendre et tester à nouveau
    print("\n4️⃣ Test après délai (5 secondes)")
    print("-" * 30)
    
    time.sleep(5)
    result3 = client.execute(query_categories)
    categories_after_delay = result3.get('data', {}).get('categories', [])
    print(f"Requête après délai - Catégories trouvées: {len(categories_after_delay)}")
    
    new_category_found_after_delay = any(
        cat['name'] == "Catégorie Test Cache" 
        for cat in categories_after_delay
    )
    
    if new_category_found_after_delay:
        print("✅ La nouvelle catégorie apparaît après délai")
    else:
        print("❌ La nouvelle catégorie n'apparaît toujours pas")
    
    # Test 5: Vider le cache manuellement et tester
    print("\n5️⃣ Test après vidage manuel du cache")
    print("-" * 30)
    
    cache.clear()
    print("🧹 Cache vidé manuellement")
    
    result4 = client.execute(query_categories)
    categories_after_clear = result4.get('data', {}).get('categories', [])
    print(f"Requête après vidage - Catégories trouvées: {len(categories_after_clear)}")
    
    new_category_found_after_clear = any(
        cat['name'] == "Catégorie Test Cache" 
        for cat in categories_after_clear
    )
    
    if new_category_found_after_clear:
        print("✅ La nouvelle catégorie apparaît après vidage manuel")
    else:
        print("❌ La nouvelle catégorie n'apparaît pas même après vidage manuel")
    
    return cache_working

def test_tag_cache():
    """Teste spécifiquement le cache des tags."""
    print("\n🏷️ TEST SPÉCIFIQUE DES TAGS")
    print("=" * 50)
    
    client = Client(schema)
    
    # Requête initiale
    query_tags = """
    query {
        tags {
            id
            name
            color
        }
    }
    """
    
    result1 = client.execute(query_tags)
    initial_count = len(result1.get('data', {}).get('tags', []))
    print(f"Tags initiaux: {initial_count}")
    
    # Créer un nouveau tag
    mutation_create_tag = """
    mutation {
        createTag(input: {
            name: "Tag Test Cache"
            color: "#FF0000"
        }) {
            tag {
                id
                name
                color
            }
        }
    }
    """
    
    create_result = client.execute(mutation_create_tag)
    if create_result.get('errors'):
        print(f"❌ Erreur lors de la création du tag: {create_result['errors']}")
        return False
    
    print("✅ Tag créé avec succès")
    
    # Vérifier immédiatement
    result2 = client.execute(query_tags)
    after_count = len(result2.get('data', {}).get('tags', []))
    print(f"Tags après création: {after_count}")
    
    if after_count > initial_count:
        print("✅ SUCCÈS: Le nouveau tag apparaît immédiatement")
        return True
    else:
        print("❌ ÉCHEC: Le nouveau tag n'apparaît pas")
        return False

def debug_cache_keys():
    """Débogue les clés de cache utilisées."""
    print("\n🔑 DÉBOGAGE DES CLÉS DE CACHE")
    print("=" * 50)
    
    # Essayer d'accéder aux clés de cache si possible
    try:
        from django.core.cache.backends.locmem import LocMemCache
        if isinstance(cache, LocMemCache):
            print("Backend de cache: LocMemCache (mémoire locale)")
            # LocMemCache stocke les données dans _cache
            if hasattr(cache, '_cache'):
                cache_keys = list(cache._cache.keys())
                print(f"Clés de cache actuelles ({len(cache_keys)}):")
                for key in cache_keys[:10]:  # Afficher les 10 premières
                    print(f"  - {key}")
                if len(cache_keys) > 10:
                    print(f"  ... et {len(cache_keys) - 10} autres")
            else:
                print("Impossible d'accéder aux clés de cache")
        else:
            print(f"Backend de cache: {type(cache).__name__}")
            print("Impossible de lister les clés pour ce backend")
    except Exception as e:
        print(f"Erreur lors du débogage des clés: {e}")

def main():
    """Fonction principale de test."""
    print("🚀 DÉMARRAGE DU DÉBOGAGE DU CACHE")
    print("=" * 60)
    
    # Nettoyer les données
    clear_all_data()
    
    # Créer un utilisateur de test
    user = create_test_user()
    print(f"👤 Utilisateur de test créé: {user.username}")
    
    # Déboguer les clés de cache
    debug_cache_keys()
    
    # Tester le comportement du cache
    cache_working = test_cache_behavior()
    
    # Tester spécifiquement les tags
    tag_cache_working = test_tag_cache()
    
    # Résumé final
    print("\n📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    print(f"Cache des catégories: {'✅ Fonctionne' if cache_working else '❌ Ne fonctionne pas'}")
    print(f"Cache des tags: {'✅ Fonctionne' if tag_cache_working else '❌ Ne fonctionne pas'}")
    
    if not cache_working or not tag_cache_working:
        print("\n🔧 PROBLÈMES IDENTIFIÉS:")
        print("- L'invalidation du cache ne fonctionne pas correctement")
        print("- Les nouvelles données n'apparaissent pas immédiatement")
        print("- La fonction invalidate_universal_cache() pourrait avoir des problèmes")
        
        print("\n💡 SOLUTIONS POSSIBLES:")
        print("1. Vérifier que la fonction d'invalidation est bien appelée")
        print("2. Ajouter des logs dans la fonction d'invalidation")
        print("3. Utiliser une approche différente pour l'invalidation")
        print("4. Vérifier la configuration du cache Django")
    else:
        print("\n🎉 Tous les tests sont réussis!")
    
    return cache_working and tag_cache_working

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)