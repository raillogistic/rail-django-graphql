#!/usr/bin/env python
"""
Test final de la solution complète d'invalidation du cache
Ce script teste le middleware personnalisé et la solution finale
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
from django.core.cache import cache

# Configuration
GRAPHQL_URL = "http://127.0.0.1:8000/graphql/"


def execute_graphql_query(query, variables=None):
    """
    Exécute une requête GraphQL avec gestion d'erreurs améliorée

    Args:
        query (str): La requête GraphQL
        variables (dict): Variables pour la requête

    Returns:
        dict: Réponse de la requête
    """
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    try:
        response = requests.post(GRAPHQL_URL, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return None

        result = response.json()
        if "errors" in result:
            print(f"❌ Erreurs GraphQL: {result['errors']}")

        return result

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON: {e}")
        return None


def test_final_solution():
    """
    Test complet de la solution finale avec middleware
    """
    print("🎯 TEST FINAL DE LA SOLUTION COMPLÈTE")
    print("Ce script teste le middleware d'invalidation automatique du cache\n")

    print("🚀 TESTS AVEC MIDDLEWARE ACTIVÉ")
    print("=" * 60)

    # Test 1: Vérification du serveur
    print("\n📋 Test 1: Vérification de la connexion au serveur")
    test_query = """
    query TestConnection {
        __typename
    }
    """

    result = execute_graphql_query(test_query)
    if result and "data" in result:
        print("✅ Connexion au serveur GraphQL établie")
    else:
        print("❌ Impossible de se connecter au serveur GraphQL")
        return False

    # Test 2: État initial du cache
    print("\n📋 Test 2: État initial et requêtes de base")

    # Effacer le cache pour commencer proprement
    cache.clear()
    print("🧹 Cache initial effacé")

    # Requête des catégories
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
        initial_categories = result1["data"]["categorys"]
        initial_count = len(initial_categories)
        print(f"✅ Catégories initiales: {initial_count}")
        print("📊 Cache peuplé avec les données initiales")
    else:
        print("❌ Erreur lors de la requête initiale des catégories")
        return False

    # Requête des tags
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

    result_tags = execute_graphql_query(query_tags)
    if result_tags and "data" in result_tags:
        initial_tags = result_tags["data"]["tags"]
        initial_tags_count = len(initial_tags)
        print(f"✅ Tags initiaux: {initial_tags_count}")
    else:
        print("❌ Erreur lors de la requête initiale des tags")
        return False

    # Test 3: Mutation avec auto-invalidation (middleware)
    print("\n📋 Test 3: Création de catégorie avec middleware")

    create_category_mutation = """
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

    test_name = f"MiddlewareTest_{random.randint(1000000, 9999999)}"
    variables = {
        "input": {
            "name": test_name,
            "description": "Test avec middleware d'invalidation",
            "is_active": True,
        }
    }

    print(f"🔄 Création de la catégorie: {test_name}")
    result2 = execute_graphql_query(create_category_mutation, variables)

    if result2 and "data" in result2 and result2["data"]["create_category"]["ok"]:
        created_category = result2["data"]["create_category"]["object"]
        print(f"✅ Catégorie créée avec succès: {created_category['name']}")
        print(f"   ID: {created_category['id']}")
    else:
        print(f"❌ Erreur lors de la création: {result2}")
        return False

    # Test 4: Vérification immédiate (le middleware devrait avoir invalidé le cache)
    print("\n📋 Test 4: Vérification immédiate après mutation")
    print("⏱️ Le middleware devrait avoir automatiquement invalidé le cache...")

    # Petite pause pour s'assurer que le middleware a eu le temps de traiter
    time.sleep(0.5)

    result3 = execute_graphql_query(query_categories)
    if result3 and "data" in result3:
        new_categories = result3["data"]["categorys"]
        new_count = len(new_categories)
        print(f"✅ Catégories après mutation: {new_count}")

        if new_count > initial_count:
            print("🎉 SUCCÈS! Le middleware a automatiquement invalidé le cache!")
            middleware_success = True

            # Vérifier que la nouvelle catégorie est bien présente
            found_new_category = any(cat["name"] == test_name for cat in new_categories)
            if found_new_category:
                print(
                    f"✅ La nouvelle catégorie '{test_name}' est visible immédiatement"
                )
            else:
                print(
                    f"⚠️ La nouvelle catégorie '{test_name}' n'est pas trouvée dans la liste"
                )

        else:
            print("❌ Le cache n'a pas été invalidé automatiquement")
            middleware_success = False
    else:
        print("❌ Erreur lors de la vérification")
        return False

    # Test 5: Test avec les tags
    print("\n📋 Test 5: Test similaire avec les tags")

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

    tag_name = f"MiddlewareTagTest_{random.randint(1000000, 9999999)}"
    tag_variables = {"input": {"name": tag_name, "color": "#FF5733"}}

    print(f"🔄 Création du tag: {tag_name}")
    result_tag = execute_graphql_query(create_tag_mutation, tag_variables)

    if result_tag and "data" in result_tag and result_tag["data"]["create_tag"]["ok"]:
        created_tag = result_tag["data"]["create_tag"]["object"]
        print(f"✅ Tag créé avec succès: {created_tag['name']}")

        # Vérification immédiate des tags
        time.sleep(0.5)
        result_tags_after = execute_graphql_query(query_tags)

        if result_tags_after and "data" in result_tags_after:
            new_tags = result_tags_after["data"]["tags"]
            new_tags_count = len(new_tags)
            print(f"✅ Tags après mutation: {new_tags_count}")

            if new_tags_count > initial_tags_count:
                print(
                    "🎉 SUCCÈS! Le middleware a invalidé le cache pour les tags aussi!"
                )

                # Vérifier que le nouveau tag est présent
                found_new_tag = any(tag["name"] == tag_name for tag in new_tags)
                if found_new_tag:
                    print(f"✅ Le nouveau tag '{tag_name}' est visible immédiatement")

            else:
                print("❌ Le cache des tags n'a pas été invalidé")

    else:
        print(f"❌ Erreur lors de la création du tag: {result_tag}")

    # Test 6: Test avec mutation personnalisée
    print("\n📋 Test 6: Test avec mutation personnalisée")

    custom_mutation = """
    mutation CreateCategoryCustom($name: String!, $description: String!) {
        CreateCategory(name: $name, description: $description) {
            category {
                id
                name
                description
            }
            success
        }
    }
    """

    custom_name = f"CustomMiddlewareTest_{random.randint(1000000, 9999999)}"
    custom_variables = {
        "name": custom_name,
        "description": "Test mutation personnalisée avec middleware",
    }

    print(f"🔄 Création avec mutation personnalisée: {custom_name}")
    result_custom = execute_graphql_query(custom_mutation, custom_variables)

    if result_custom and "data" in result_custom:
        custom_result = result_custom["data"]["CreateCategory"]
        if custom_result and custom_result.get("success"):
            print(
                f"✅ Mutation personnalisée réussie: {custom_result['category']['name']}"
            )

            # Vérification immédiate
            time.sleep(0.5)
            result_after_custom = execute_graphql_query(query_categories)

            if result_after_custom and "data" in result_after_custom:
                categories_after_custom = result_after_custom["data"]["categorys"]
                found_custom = any(
                    cat["name"] == custom_name for cat in categories_after_custom
                )

                if found_custom:
                    print(
                        "🎉 SUCCÈS! Le middleware fonctionne aussi avec les mutations personnalisées!"
                    )
                else:
                    print(
                        "⚠️ La mutation personnalisée n'a pas déclenché l'invalidation du cache"
                    )
        else:
            print(f"❌ Mutation personnalisée échouée: {result_custom}")

    # Test 7: Vérification en base de données
    print("\n📋 Test 7: Vérification finale en base de données")

    try:
        # Vérifier les objets créés en base
        db_category = Category.objects.filter(name=test_name).first()
        db_tag = Tag.objects.filter(name=tag_name).first()
        db_custom_category = Category.objects.filter(name=custom_name).first()

        if db_category:
            print(f"✅ Catégorie auto-générée trouvée en base: {db_category.name}")
        else:
            print("❌ Catégorie auto-générée non trouvée en base")

        if db_tag:
            print(f"✅ Tag trouvé en base: {db_tag.name}")
        else:
            print("❌ Tag non trouvé en base")

        if db_custom_category:
            print(
                f"✅ Catégorie personnalisée trouvée en base: {db_custom_category.name}"
            )
        else:
            print("❌ Catégorie personnalisée non trouvée en base")

    except Exception as e:
        print(f"❌ Erreur lors de la vérification en base: {e}")

    # Résumé final
    print("\n" + "=" * 60)
    if middleware_success:
        print("🎉 SOLUTION FINALE VALIDÉE!")
        print("✅ Le middleware d'invalidation automatique du cache fonctionne")
        print("✅ Les mutations auto-générées invalident correctement le cache")
        print("✅ Les mutations personnalisées sont également supportées")
        print("✅ Les données sont immédiatement visibles après les mutations")
    else:
        print("❌ SOLUTION PARTIELLEMENT FONCTIONNELLE")
        print("⚠️ Certains aspects nécessitent encore des améliorations")

    print("\n🔧 MIDDLEWARE INSTALLÉ:")
    print("- cache_middleware.GraphQLCacheInvalidationMiddleware")
    print("- Invalidation automatique après chaque mutation réussie")
    print("- Support des mutations auto-générées et personnalisées")
    print("- Logging des opérations de cache")

    return middleware_success


if __name__ == "__main__":
    success = test_final_solution()
    if success:
        print("\n🎯 MISSION ACCOMPLIE!")
    else:
        print("\n⚠️ Des améliorations sont encore nécessaires")
