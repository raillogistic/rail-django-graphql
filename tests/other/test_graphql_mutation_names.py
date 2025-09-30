#!/usr/bin/env python3
"""
Test GraphQL Mutation Field Names and Cache Invalidation
========================================================

This test verifies:
1. The correct GraphQL mutation field names (snake_case vs camelCase)
2. Cache invalidation with proper mutation names
3. Integration between GraphQL mutations and cache middleware

Author: AI Assistant
Date: 2025-01-27
"""

import os
import sys
import django
from django.test import RequestFactory
from django.core.cache import cache
from django.conf import settings
import json
import requests

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from test_app.models import Category, Tag
from rail_django_graphql.schema import schema
from graphene.test import Client


def test_graphql_mutation_field_names():
    """Test que les noms des mutations GraphQL utilisent la convention snake_case."""
    print("🔍 VÉRIFICATION DES NOMS DE MUTATIONS GRAPHQL")
    print("=" * 60)

    # Vérifier les champs de mutation disponibles
    mutation_type = schema.mutation
    if not mutation_type:
        print("❌ Type Mutation non trouvé dans le schéma")
        return False

    mutation_fields = mutation_type._meta.fields
    print(f"📋 Mutations disponibles: {len(mutation_fields)} trouvées")

    # Rechercher les mutations Category et Tag
    category_mutations = [
        name for name in mutation_fields.keys() if "category" in name.lower()
    ]
    tag_mutations = [name for name in mutation_fields.keys() if "tag" in name.lower()]

    print(f"🏷️  Mutations Category: {category_mutations}")
    print(f"🏷️  Mutations Tag: {tag_mutations}")

    # Vérifier la convention de nommage
    expected_category_mutations = [
        "create_category",
        "update_category",
        "delete_category",
    ]
    expected_tag_mutations = ["create_tag", "update_tag", "delete_tag"]

    category_check = all(
        mutation in category_mutations for mutation in expected_category_mutations
    )
    tag_check = all(mutation in tag_mutations for mutation in expected_tag_mutations)

    print(f"✅ Mutations Category correctes: {category_check}")
    print(f"✅ Mutations Tag correctes: {tag_check}")

    return category_check and tag_check


def test_cache_invalidation_with_correct_names():
    """Test l'invalidation du cache avec les noms de mutations corrects."""
    print("\n🧪 TEST D'INVALIDATION DU CACHE AVEC NOMS CORRECTS")
    print("=" * 60)

    # Nettoyer le cache
    cache.clear()
    print("🧹 Cache nettoyé")

    # Créer un client GraphQL
    client = Client(schema)

    # Test 1: Créer une catégorie avec create_category (snake_case)
    print("\n📝 Test 1: Création de catégorie avec create_category")

    create_category_mutation = """
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

    category_variables = {
        "input": {
            "name": "Test Category Snake Case",
            "description": "Test avec snake_case",
        }
    }

    # Ajouter des données au cache avant la mutation
    cache_key = "test_category_list"
    cache.set(cache_key, ["cached_data"], 300)
    print(f"📦 Données ajoutées au cache: {cache.get(cache_key)}")

    # Exécuter la mutation
    result = client.execute(create_category_mutation, variables=category_variables)

    if result.get("errors"):
        print(f"❌ Erreurs GraphQL: {result['errors']}")
        return False

    if result["data"]["create_category"]["ok"]:
        created_category = result["data"]["create_category"]["object"]
        print(
            f"✅ Catégorie créée: {created_category['name']} (ID: {created_category['id']})"
        )

        # Vérifier l'invalidation du cache
        cached_data_after = cache.get(cache_key)
        if cached_data_after is None:
            print("✅ Cache invalidé avec succès après create_category")
            cache_invalidated = True
        else:
            print(f"❌ Cache non invalidé: {cached_data_after}")
            cache_invalidated = False
    else:
        print(
            f"❌ Échec création catégorie: {result['data']['create_category']['errors']}"
        )
        return False

    # Test 2: Créer un tag avec create_tag (snake_case)
    print("\n📝 Test 2: Création de tag avec create_tag")

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

    tag_variables = {"input": {"name": "Test Tag Snake Case", "color": "#FF5733"}}

    # Ajouter des données au cache avant la mutation
    tag_cache_key = "test_tag_list"
    cache.set(tag_cache_key, ["cached_tag_data"], 300)
    print(f"📦 Données tag ajoutées au cache: {cache.get(tag_cache_key)}")

    # Exécuter la mutation
    tag_result = client.execute(create_tag_mutation, variables=tag_variables)

    if tag_result.get("errors"):
        print(f"❌ Erreurs GraphQL tag: {tag_result['errors']}")
        return False

    if tag_result["data"]["create_tag"]["ok"]:
        created_tag = tag_result["data"]["create_tag"]["object"]
        print(f"✅ Tag créé: {created_tag['name']} (ID: {created_tag['id']})")

        # Vérifier l'invalidation du cache
        tag_cached_data_after = cache.get(tag_cache_key)
        if tag_cached_data_after is None:
            print("✅ Cache tag invalidé avec succès après create_tag")
            tag_cache_invalidated = True
        else:
            print(f"❌ Cache tag non invalidé: {tag_cached_data_after}")
            tag_cache_invalidated = False
    else:
        print(f"❌ Échec création tag: {tag_result['data']['create_tag']['errors']}")
        return False

    return cache_invalidated and tag_cache_invalidated


def test_http_graphql_integration():
    """Test l'intégration GraphQL via HTTP avec le serveur Django."""
    print("\n🌐 TEST D'INTÉGRATION HTTP GRAPHQL")
    print("=" * 60)

    # URL du serveur GraphQL
    graphql_url = "http://localhost:8000/graphql/"

    # Test de disponibilité du serveur
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"✅ Serveur Django accessible (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Serveur Django non accessible: {e}")
        return False

    # Test de mutation via HTTP
    create_category_http = {
        "query": """
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
        """,
        "variables": {
            "input": {
                "name": "HTTP Test Category",
                "description": "Créé via HTTP GraphQL",
            }
        },
    }

    try:
        response = requests.post(
            graphql_url,
            json=create_category_http,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("data", {}).get("create_category", {}).get("ok"):
                created_category = data["data"]["create_category"]["object"]
                print(f"✅ Catégorie créée via HTTP: {created_category['name']}")
                return True
            else:
                print(f"❌ Échec mutation HTTP: {data}")
                return False
        else:
            print(f"❌ Erreur HTTP: {response.status_code} - {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur requête HTTP: {e}")
        return False


def main():
    """Fonction principale pour exécuter tous les tests."""
    print("🚀 TESTS DE NOMS DE MUTATIONS GRAPHQL ET INVALIDATION CACHE")
    print("=" * 80)

    # Test 1: Vérification des noms de mutations
    names_correct = test_graphql_mutation_field_names()

    # Test 2: Test d'invalidation avec noms corrects
    cache_working = test_cache_invalidation_with_correct_names()

    # Test 3: Test d'intégration HTTP
    http_working = test_http_graphql_integration()

    # Résumé final
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 80)
    print(f"✅ Noms de mutations corrects: {'✅ OUI' if names_correct else '❌ NON'}")
    print(
        f"✅ Invalidation cache fonctionne: {'✅ OUI' if cache_working else '❌ NON'}"
    )
    print(f"✅ Intégration HTTP fonctionne: {'✅ OUI' if http_working else '❌ NON'}")

    if names_correct and cache_working and http_working:
        print("\n🎉 TOUS LES TESTS RÉUSSIS!")
        print(
            "Le middleware d'invalidation cache fonctionne parfaitement avec les noms de mutations corrects."
        )
        return True
    else:
        print("\n⚠️  CERTAINS TESTS ONT ÉCHOUÉ")
        if not names_correct:
            print("- Vérifier les noms de mutations dans le schéma GraphQL")
        if not cache_working:
            print("- Vérifier la configuration du middleware d'invalidation")
        if not http_working:
            print("- Vérifier que le serveur Django fonctionne sur localhost:8000")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
