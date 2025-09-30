#!/usr/bin/env python3
"""
Test du système de cache intégré avec django-graphql-auto.

Ce script teste si les mutations personnalisées utilisent correctement
le système d'invalidation de cache intégré de django-graphql-auto.
"""

import os
import sys
import django
import requests
import json
import time

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialiser Django
django.setup()

from django.core.cache import cache
from rail_django_graphql.extensions.caching import get_cache_manager
from test_app.models import Category, Tag, Post, Comment


def make_graphql_request(query, variables=None):
    """Effectue une requête GraphQL vers le serveur local."""
    url = "http://127.0.0.1:8000/graphql/"
    payload = {"query": query, "variables": variables or {}}

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de requête: {e}")
        return None


def test_integrated_cache_system():
    """Test complet du système de cache intégré."""
    print("🚀 TEST DU SYSTÈME DE CACHE INTÉGRÉ DJANGO-GRAPHQL-AUTO")
    print("=" * 70)

    # Vider le cache au début
    cache.clear()
    print("🧹 Cache initial vidé")

    # Test 1: Vérifier que le cache manager est disponible
    print("\n📋 Test 1: Vérification du cache manager")
    try:
        cache_manager = get_cache_manager()
        print(f"✅ Cache manager disponible: {type(cache_manager).__name__}")

        # Vérifier les statistiques
        stats = cache_manager.get_stats()
        print(f"📊 Statistiques initiales: hits={stats.hits}, misses={stats.misses}")
    except Exception as e:
        print(f"❌ Erreur avec le cache manager: {e}")
        return False

    # Test 2: Tester les requêtes de base
    print("\n📋 Test 2: Requêtes de base")

    # Requête initiale des catégories
    categories_query = """
    query {
        categorys {
            id
            name
            description
            is_active
            created_at
        }
    }
    """

    initial_result = make_graphql_request(categories_query)
    if not initial_result or "errors" in initial_result:
        print(f"❌ Erreur dans la requête initiale: {initial_result}")
        return False

    initial_count = len(initial_result["data"]["categorys"])
    print(f"✅ Requête initiale réussie: {initial_count} catégories trouvées")

    # Test 3: Créer une nouvelle catégorie avec mutation personnalisée
    print("\n📋 Test 3: Création avec mutation personnalisée")

    create_mutation = """
    mutation CreateCategory($input: CategoryInput!) {
        createCategory(input: $input) {
            category {
                id
                name
                description
                is_active
                created_at
            }
        }
    }
    """

    variables = {
        "input": {
            "name": f"TestIntegratedCache_{int(time.time())}",
            "description": "Test du cache intégré",
        }
    }

    create_result = make_graphql_request(create_mutation, variables)
    if not create_result or "errors" in create_result:
        print(f"❌ Erreur lors de la création: {create_result}")
        return False

    new_category = create_result["data"]["createCategory"]["category"]
    print(f"✅ Catégorie créée: {new_category['name']} (ID: {new_category['id']})")

    # Test 4: Vérifier l'invalidation immédiate du cache
    print("\n📋 Test 4: Vérification de l'invalidation du cache")

    # Attendre un peu pour que l'invalidation soit traitée
    time.sleep(0.2)

    # Re-requête immédiate
    immediate_result = make_graphql_request(categories_query)
    if not immediate_result or "errors" in immediate_result:
        print(f"❌ Erreur dans la re-requête: {immediate_result}")
        return False

    immediate_count = len(immediate_result["data"]["categorys"])
    print(f"📊 Nombre de catégories après création: {immediate_count}")

    # Vérifier que la nouvelle catégorie est présente
    found_new_category = any(
        cat["id"] == new_category["id"] for cat in immediate_result["data"]["categorys"]
    )

    if found_new_category:
        print("✅ SUCCÈS: La nouvelle catégorie apparaît immédiatement!")
        print("✅ Le cache a été correctement invalidé par le système intégré")
    else:
        print("❌ ÉCHEC: La nouvelle catégorie n'apparaît pas immédiatement")
        print("❌ Le cache n'a pas été invalidé correctement")
        return False

    # Test 5: Tester avec les tags
    print("\n📋 Test 5: Test avec les tags")

    tags_query = """
    query {
        tags {
            id
            name
            color
            is_active
            created_at
        }
    }
    """

    initial_tags = make_graphql_request(tags_query)
    if not initial_tags or "errors" in initial_tags:
        print(f"❌ Erreur dans la requête tags: {initial_tags}")
        return False

    initial_tags_count = len(initial_tags["data"]["tags"])
    print(f"✅ Tags initiaux: {initial_tags_count}")

    # Créer un tag avec mutation personnalisée
    create_tag_mutation = """
    mutation CreateTag($input: TagInput!) {
        createTag(input: $input) {
            tag {
                id
                name
                color
                is_active
                created_at
            }
        }
    }
    """

    tag_variables = {
        "input": {"name": f"TestIntegratedTag_{int(time.time())}", "color": "#FF6B35"}
    }

    create_tag_result = make_graphql_request(create_tag_mutation, tag_variables)
    if not create_tag_result or "errors" in create_tag_result:
        print(f"❌ Erreur lors de la création du tag: {create_tag_result}")
        return False

    new_tag = create_tag_result["data"]["createTag"]["tag"]
    print(f"✅ Tag créé: {new_tag['name']} (ID: {new_tag['id']})")

    # Vérifier l'invalidation pour les tags
    time.sleep(0.2)

    immediate_tags = make_graphql_request(tags_query)
    if not immediate_tags or "errors" in immediate_tags:
        print(f"❌ Erreur dans la re-requête tags: {immediate_tags}")
        return False

    immediate_tags_count = len(immediate_tags["data"]["tags"])
    found_new_tag = any(
        tag["id"] == new_tag["id"] for tag in immediate_tags["data"]["tags"]
    )

    if found_new_tag:
        print("✅ SUCCÈS: Le nouveau tag apparaît immédiatement!")
        print("✅ Le cache des tags a été correctement invalidé")
    else:
        print("❌ ÉCHEC: Le nouveau tag n'apparaît pas immédiatement")
        return False

    # Test 6: Vérifier les statistiques du cache
    print("\n📋 Test 6: Statistiques du cache")
    try:
        final_stats = cache_manager.get_stats()
        print(f"📊 Statistiques finales:")
        print(f"   - Hits: {final_stats.hits}")
        print(f"   - Misses: {final_stats.misses}")
        print(f"   - Sets: {final_stats.sets}")
        print(f"   - Invalidations: {final_stats.invalidations}")
        print(f"   - Deletes: {final_stats.deletes}")
    except Exception as e:
        print(f"⚠️ Impossible de récupérer les statistiques: {e}")

    # Nettoyage
    print("\n🧹 Nettoyage des données de test")
    try:
        Category.objects.filter(name__startswith="TestIntegratedCache_").delete()
        Tag.objects.filter(name__startswith="TestIntegratedTag_").delete()
        print("✅ Données de test supprimées")
    except Exception as e:
        print(f"⚠️ Erreur lors du nettoyage: {e}")

    return True


def main():
    """Fonction principale."""
    print("🎯 TEST DU SYSTÈME DE CACHE INTÉGRÉ")
    print("Ce script teste l'intégration avec django-graphql-auto")
    print()

    success = test_integrated_cache_system()

    print("\n" + "=" * 70)
    if success:
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("✅ Le système de cache intégré fonctionne correctement")
        print("✅ Les mutations personnalisées invalident le cache automatiquement")
        print("✅ Les nouvelles données apparaissent immédiatement dans GraphiQL")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("⚠️ Le système de cache intégré nécessite des ajustements")

    print("\n🔧 PROCHAINES ÉTAPES:")
    print("1. Tester manuellement dans GraphiQL")
    print("2. Vérifier les logs Django pour les messages d'invalidation")
    print("3. Redémarrer le serveur si nécessaire")


if __name__ == "__main__":
    main()
