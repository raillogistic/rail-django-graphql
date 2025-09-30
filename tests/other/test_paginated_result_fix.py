#!/usr/bin/env python
"""
Test script pour vérifier la correction du problème de sérialisation (pickle)
de la classe PaginatedResult dans les requêtes GraphQL paginées.

Ce script teste:
1. L'importation de la classe PaginatedResult au niveau du module
2. La sérialisation (pickle) de la classe PaginatedResult
3. La simulation d'une requête GraphQL paginée avec cache
"""

import os
import sys
import pickle
import json
from unittest.mock import Mock

# Ajouter le répertoire du projet au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_paginated_result_import():
    """Test l'importation de la classe PaginatedResult"""
    print("=== Test d'importation de PaginatedResult ===")

    try:
        from rail_django_graphql.generators.queries import PaginatedResult

        print("✓ PaginatedResult importée avec succès")
        return True
    except ImportError as e:
        print(f"✗ Erreur d'importation: {e}")
        return False


def test_paginated_result_pickle():
    """Test la sérialisation (pickle) de PaginatedResult"""
    print("\n=== Test de sérialisation (pickle) ===")

    try:
        from rail_django_graphql.generators.queries import PaginatedResult

        # Créer un objet PaginationInfo mock
        class MockPaginationInfo:
            def __init__(self):
                self.total_count = 100
                self.page_count = 10
                self.current_page = 1
                self.per_page = 10
                self.has_next_page = True
                self.has_previous_page = False

        # Créer des données de test
        mock_items = [
            {"id": 1, "name": "Test Item 1"},
            {"id": 2, "name": "Test Item 2"},
        ]
        mock_page_info = MockPaginationInfo()

        # Créer une instance de PaginatedResult
        paginated_result = PaginatedResult(items=mock_items, page_info=mock_page_info)

        # Tester la sérialisation
        serialized = pickle.dumps(paginated_result)
        print(f"✓ Sérialisation réussie, taille: {len(serialized)} bytes")

        # Tester la désérialisation
        deserialized = pickle.loads(serialized)
        print("✓ Désérialisation réussie")

        # Vérifier les données
        assert len(deserialized.items) == 2
        assert deserialized.items[0]["name"] == "Test Item 1"
        assert deserialized.page_info.total_count == 100
        print("✓ Données vérifiées après désérialisation")

        return True

    except Exception as e:
        print(f"✗ Erreur de sérialisation: {e}")
        return False


def test_cache_simulation():
    """Simule la mise en cache d'un résultat paginé"""
    print("\n=== Test de simulation de cache ===")

    try:
        from rail_django_graphql.generators.queries import PaginatedResult

        # Simuler un cache simple avec pickle
        cache_storage = {}

        def cache_set(key, value):
            cache_storage[key] = pickle.dumps(value)

        def cache_get(key):
            if key in cache_storage:
                return pickle.loads(cache_storage[key])
            return None

        # Créer un résultat paginé de test
        class MockPaginationInfo:
            def __init__(self):
                self.total_count = 50
                self.page_count = 5
                self.current_page = 2
                self.per_page = 10
                self.has_next_page = True
                self.has_previous_page = True

        test_items = [
            {"pk": 1, "name": "Tag 1"},
            {"pk": 2, "name": "Tag 2"},
            {"pk": 3, "name": "Tag 3"},
        ]
        test_page_info = MockPaginationInfo()

        paginated_result = PaginatedResult(items=test_items, page_info=test_page_info)

        # Tester la mise en cache
        cache_key = "tag_pages:page=2:per_page=10"
        cache_set(cache_key, paginated_result)
        print("✓ Résultat paginé mis en cache")

        # Tester la récupération du cache
        cached_result = cache_get(cache_key)
        assert cached_result is not None
        assert len(cached_result.items) == 3
        assert cached_result.items[0]["pk"] == 1
        assert cached_result.page_info.current_page == 2
        print("✓ Résultat paginé récupéré du cache")

        # Tester un cache miss
        missing_result = cache_get("nonexistent_key")
        assert missing_result is None
        print("✓ Cache miss géré correctement")

        return True

    except Exception as e:
        print(f"✗ Erreur de simulation de cache: {e}")
        return False


def test_graphql_query_simulation():
    """Simule une requête GraphQL tag_pages"""
    print("\n=== Test de simulation de requête GraphQL ===")

    try:
        from rail_django_graphql.generators.queries import PaginatedResult

        # Simuler une requête tag_pages
        def simulate_tag_pages_query(page=1, per_page=10):
            """Simule l'exécution d'une requête tag_pages"""

            # Données de test simulées
            all_tags = [
                {"pk": i, "name": f"Tag {i}"}
                for i in range(1, 101)  # 100 tags au total
            ]

            # Calculer la pagination
            total_count = len(all_tags)
            page_count = (total_count + per_page - 1) // per_page
            start = (page - 1) * per_page
            end = start + per_page
            items = all_tags[start:end]

            # Créer les informations de pagination
            class PaginationInfo:
                def __init__(self):
                    self.total_count = total_count
                    self.page_count = page_count
                    self.current_page = page
                    self.per_page = per_page
                    self.has_next_page = page < page_count
                    self.has_previous_page = page > 1

            page_info = PaginationInfo()

            # Retourner le résultat paginé
            return PaginatedResult(items=items, page_info=page_info)

        # Tester la requête
        result = simulate_tag_pages_query(page=1, per_page=5)

        # Vérifier le résultat
        assert len(result.items) == 5
        assert result.items[0]["pk"] == 1
        assert result.items[4]["pk"] == 5
        assert result.page_info.total_count == 100
        assert result.page_info.current_page == 1
        assert result.page_info.has_next_page == True
        assert result.page_info.has_previous_page == False
        print("✓ Requête tag_pages simulée avec succès")

        # Tester la sérialisation du résultat
        serialized = pickle.dumps(result)
        deserialized = pickle.loads(serialized)
        assert len(deserialized.items) == 5
        assert deserialized.page_info.total_count == 100
        print("✓ Résultat de requête sérialisable")

        return True

    except Exception as e:
        print(f"✗ Erreur de simulation de requête: {e}")
        return False


def main():
    """Fonction principale de test"""
    print("Test de correction du problème de sérialisation PaginatedResult")
    print("=" * 60)

    tests = [
        test_paginated_result_import,
        test_paginated_result_pickle,
        test_cache_simulation,
        test_graphql_query_simulation,
    ]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS:")
    print(f"✓ Tests réussis: {sum(results)}/{len(results)}")

    if all(results):
        print("\n🎉 Tous les tests sont passés!")
        print(
            "La classe PaginatedResult est maintenant sérialisable et peut être mise en cache."
        )
        print(
            "La requête GraphQL 'tag_pages' devrait maintenant fonctionner sans erreur de pickle."
        )
    else:
        print("\n❌ Certains tests ont échoué.")
        print("Vérifiez les erreurs ci-dessus.")

    return all(results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
