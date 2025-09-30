#!/usr/bin/env python
"""
Test du comportement du cache avec les mutations auto-générées
Ce script teste si les mutations auto-générées invalident correctement le cache
"""

import os
import django
import requests
import json
import time
import random

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from test_app.models import Category, Tag

# Configuration
GRAPHQL_URL = "http://127.0.0.1:8000/graphql/"


def execute_graphql_query(query, variables=None):
    """
    Exécute une requête GraphQL

    Args:
        query (str): La requête GraphQL
        variables (dict): Variables pour la requête

    Returns:
        dict: Réponse de la requête
    """
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(GRAPHQL_URL, json=payload)
    if response.status_code != 200:
        print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
        return None

    return response.json()


def test_cache_behavior():
    """
    Test principal du comportement du cache
    """
    print("🎯 TEST DU COMPORTEMENT DU CACHE")
    print("Ce script teste l'invalidation automatique du cache\n")

    print("🚀 ANALYSE DU COMPORTEMENT DU CACHE")
    print("=" * 50)

    # Test 1: Requête initiale
    print("\n📋 Test 1: Requête initiale des catégories")
    query_categories = """
    query GetCategories {
        categorys {
            id
            name
            description
            is_active
            created_at
        }
    }
    """

    result1 = execute_graphql_query(query_categories)
    if result1 and "data" in result1:
        initial_count = len(result1["data"]["categorys"])
        print(f"✅ Requête initiale: {initial_count} catégories trouvées")
    else:
        print("❌ Erreur lors de la requête initiale")
        return False

    # Test 2: Création avec mutation auto-générée
    print("\n📋 Test 2: Création avec mutation auto-générée")
    create_mutation = """
    mutation CreateCategory($input: CategoryInput!) {
        create_category(input: $input) {
            ok
            object {
                id
                name
                description
                is_active
            }
            errors
        }
    }
    """

    test_name = f"CacheTest_{random.randint(1000000, 9999999)}"
    variables = {
        "input": {
            "name": test_name,
            "description": "Test de cache automatique",
            "is_active": True,
        }
    }

    result2 = execute_graphql_query(create_mutation, variables)
    if result2 and "data" in result2 and result2["data"]["create_category"]["ok"]:
        created_category = result2["data"]["create_category"]["object"]
        print(
            f"✅ Catégorie créée: {created_category['name']} (ID: {created_category['id']})"
        )
    else:
        print(f"❌ Erreur création: {result2}")
        return False

    # Test 3: Vérification immédiate (cache invalidé?)
    print("\n📋 Test 3: Vérification immédiate de l'invalidation")
    result3 = execute_graphql_query(query_categories)
    if result3 and "data" in result3:
        new_count = len(result3["data"]["categorys"])
        print(f"✅ Nouvelle requête: {new_count} catégories trouvées")

        if new_count > initial_count:
            print("🎉 CACHE INVALIDÉ AUTOMATIQUEMENT!")
            cache_working = True
        else:
            print("⚠️ Cache non invalidé - la nouvelle catégorie n'apparaît pas")
            cache_working = False
    else:
        print("❌ Erreur lors de la vérification")
        return False

    # Test 4: Attendre et re-vérifier
    print("\n📋 Test 4: Attendre 2 secondes et re-vérifier")
    time.sleep(2)
    result4 = execute_graphql_query(query_categories)
    if result4 and "data" in result4:
        final_count = len(result4["data"]["categorys"])
        print(f"✅ Requête après attente: {final_count} catégories trouvées")

        if final_count > initial_count:
            print("✅ La nouvelle catégorie est maintenant visible")
        else:
            print("❌ La nouvelle catégorie n'est toujours pas visible")

    # Test 5: Vérification en base de données
    print("\n📋 Test 5: Vérification directe en base de données")
    try:
        db_categories = Category.objects.filter(name=test_name)
        if db_categories.exists():
            print(f"✅ Catégorie trouvée en base: {db_categories.first().name}")
        else:
            print("❌ Catégorie non trouvée en base")
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")

    # Test 6: Test avec les tags
    print("\n📋 Test 6: Test similaire avec les tags")
    query_tags = """
    query GetTags {
        tags {
            id
            name
            color
            created_at
        }
    }
    """

    result_tags1 = execute_graphql_query(query_tags)
    if result_tags1 and "data" in result_tags1:
        initial_tags_count = len(result_tags1["data"]["tags"])
        print(f"✅ Tags initiaux: {initial_tags_count}")

    create_tag_mutation = """
    mutation CreateTag($input: TagInput!) {
        create_tag(input: $input) {
            ok
            object {
                id
                name
                color
            }
            errors
        }
    }
    """

    tag_name = f"TagTest_{random.randint(1000000, 9999999)}"
    tag_variables = {"input": {"name": tag_name, "color": "#FF5733"}}

    result_tag_create = execute_graphql_query(create_tag_mutation, tag_variables)
    if (
        result_tag_create
        and "data" in result_tag_create
        and result_tag_create["data"]["create_tag"]["ok"]
    ):
        created_tag = result_tag_create["data"]["create_tag"]["object"]
        print(f"✅ Tag créé: {created_tag['name']} (ID: {created_tag['id']})")

        # Vérification immédiate
        result_tags2 = execute_graphql_query(query_tags)
        if result_tags2 and "data" in result_tags2:
            new_tags_count = len(result_tags2["data"]["tags"])
            if new_tags_count > initial_tags_count:
                print("🎉 CACHE TAGS INVALIDÉ AUTOMATIQUEMENT!")
            else:
                print("⚠️ Cache tags non invalidé")

    print("\n" + "=" * 50)
    if cache_working:
        print("✅ TEST RÉUSSI")
        print("🎉 Le cache fonctionne correctement avec les mutations auto-générées")
    else:
        print("❌ TEST ÉCHOUÉ")
        print("⚠️ Problèmes d'invalidation du cache détectés")

    print("\n🔧 ANALYSE:")
    print("1. Les mutations auto-générées créent correctement les objets")
    print("2. L'invalidation du cache peut être différée")
    print(
        "3. Le système de cache de django-graphql-auto fonctionne via les signaux Django"
    )

    return cache_working


if __name__ == "__main__":
    test_cache_behavior()
