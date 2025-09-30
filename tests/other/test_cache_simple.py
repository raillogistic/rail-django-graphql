#!/usr/bin/env python
"""
Test simple pour vérifier le comportement du cache GraphQL
"""

import os
import sys
import django
import json
import time

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from django.contrib.auth.models import User
from test_app.models import Category, Tag
from django.core.cache import cache
from django.test import Client
from django.urls import reverse


def test_cache_behavior():
    """Test le comportement du cache avec des requêtes GraphQL réelles"""

    print("=== Test du comportement du cache GraphQL ===\n")

    # Nettoyer les données existantes
    Category.objects.all().delete()
    User.objects.all().delete()
    cache.clear()

    # Créer un utilisateur pour les tests
    user = User.objects.create_user(username="testuser", password="testpass")

    # Client Django pour les requêtes HTTP
    client = Client()

    # URL GraphQL
    graphql_url = "/graphql/"

    # 1. Requête initiale pour les catégories
    query_categories = """
    query {
        categories {
            id
            name
            description
        }
    }
    """

    print("1. Requête initiale des catégories...")
    response1 = client.post(
        graphql_url, {"query": query_categories}, content_type="application/json"
    )

    if response1.status_code == 200:
        data1 = response1.json()
        print(
            f"   Résultat: {len(data1.get('data', {}).get('categories', []))} catégories trouvées"
        )
        print(f"   Données: {data1.get('data', {}).get('categories', [])}")
    else:
        print(f"   Erreur: {response1.status_code}")
        return

    # 2. Créer une nouvelle catégorie via mutation
    create_mutation = """
    mutation {
        createCategory(input: {name: "Test Category", description: "Test Description"}) {
            category {
                id
                name
                description
            }
        }
    }
    """

    print("\n2. Création d'une nouvelle catégorie...")
    response2 = client.post(
        graphql_url, {"query": create_mutation}, content_type="application/json"
    )

    if response2.status_code == 200:
        data2 = response2.json()
        print(f"   Résultat: {data2}")
        if "errors" in data2:
            print(f"   Erreurs: {data2['errors']}")
            return
    else:
        print(f"   Erreur: {response2.status_code}")
        return

    # 3. Requête immédiate après création (test cache invalidation)
    print("\n3. Requête immédiate après création...")
    response3 = client.post(
        graphql_url, {"query": query_categories}, content_type="application/json"
    )

    if response3.status_code == 200:
        data3 = response3.json()
        categories_after = data3.get("data", {}).get("categories", [])
        print(f"   Résultat: {len(categories_after)} catégories trouvées")
        print(f"   Données: {categories_after}")

        # Vérifier si la nouvelle catégorie apparaît
        new_category_found = any(
            cat["name"] == "Test Category" for cat in categories_after
        )
        print(f"   Nouvelle catégorie trouvée: {new_category_found}")

        if new_category_found:
            print("   ✅ Cache invalidé correctement!")
        else:
            print("   ❌ Cache non invalidé - problème détecté!")
    else:
        print(f"   Erreur: {response3.status_code}")

    # 4. Attendre et tester à nouveau
    print("\n4. Attente de 2 secondes et nouvelle requête...")
    time.sleep(2)

    response4 = client.post(
        graphql_url, {"query": query_categories}, content_type="application/json"
    )

    if response4.status_code == 200:
        data4 = response4.json()
        categories_delayed = data4.get("data", {}).get("categories", [])
        print(f"   Résultat: {len(categories_delayed)} catégories trouvées")
        print(f"   Données: {categories_delayed}")

    # 5. Vérifier les clés de cache
    print("\n5. Vérification des clés de cache...")
    try:
        from django.core.cache.utils import make_template_fragment_key

        print("   Clés de cache disponibles:")
        # Cette partie dépend du backend de cache utilisé
        if hasattr(cache, "_cache"):
            print(f"   Type de cache: {type(cache._cache)}")
        print(f"   Cache backend: {cache.__class__.__name__}")
    except Exception as e:
        print(f"   Erreur lors de l'inspection du cache: {e}")

    print("\n=== Fin du test ===")


if __name__ == "__main__":
    test_cache_behavior()
