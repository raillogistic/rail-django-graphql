#!/usr/bin/env python3
"""
Test simple pour vérifier l'invalidation du cache via les signaux Django
Ce test se concentre sur les opérations directes sur les modèles
"""

import os
import sys
import django
import time
from datetime import datetime

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from django.core.cache import cache
from django.db import transaction
from test_app.models import Category, Tag


def log_test_step(step_name, details=""):
    """Log une étape de test avec timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{timestamp}] 🧪 {step_name}")
    if details:
        print(f"   📝 {details}")


def test_cache_invalidation_on_model_operations():
    """Test l'invalidation du cache lors d'opérations sur les modèles"""
    log_test_step("Test d'invalidation du cache avec signaux Django")

    # 1. Effacer le cache et ajouter une clé de test
    cache.clear()
    test_key = "test_cache_key"
    test_value = "test_value_initial"
    cache.set(test_key, test_value, 300)  # 5 minutes

    # Vérifier que la clé est en cache
    cached_value = cache.get(test_key)
    print(f"   📊 Valeur initiale en cache: {cached_value}")

    if cached_value != test_value:
        print("   ❌ Erreur: la valeur n'a pas été mise en cache correctement")
        return False

    # 2. Créer une catégorie (doit déclencher l'invalidation)
    log_test_step("Création d'une catégorie pour déclencher l'invalidation")

    with transaction.atomic():
        new_category = Category.objects.create(
            name=f"Test Signal Category {datetime.now().strftime('%H%M%S')}",
            description="Test d'invalidation par signal",
        )
        print(f"   ✅ Catégorie créée: {new_category.name} (ID: {new_category.id})")

    # 3. Attendre un peu pour que les signaux se déclenchent
    time.sleep(0.5)

    # 4. Vérifier que le cache a été invalidé
    log_test_step("Vérification de l'invalidation du cache")
    cached_value_after = cache.get(test_key)
    print(f"   📊 Valeur après création: {cached_value_after}")

    if cached_value_after is None:
        print("   ✅ Cache invalidé correctement - clé supprimée")
        cache_invalidated_create = True
    else:
        print("   ❌ Cache non invalidé - clé toujours présente")
        cache_invalidated_create = False

    # 5. Remettre une valeur en cache et tester la modification
    cache.set(test_key, "test_value_after_create", 300)

    log_test_step("Modification de la catégorie")
    new_category.description = f"Modifiée à {datetime.now().strftime('%H:%M:%S')}"
    new_category.save()
    print(f"   ✅ Catégorie modifiée")

    time.sleep(0.5)

    cached_value_after_update = cache.get(test_key)
    print(f"   📊 Valeur après modification: {cached_value_after_update}")

    if cached_value_after_update is None:
        print("   ✅ Cache invalidé correctement après modification")
        cache_invalidated_update = True
    else:
        print("   ❌ Cache non invalidé après modification")
        cache_invalidated_update = False

    # 6. Remettre une valeur en cache et tester la suppression
    cache.set(test_key, "test_value_after_update", 300)

    log_test_step("Suppression de la catégorie")
    category_id = new_category.id
    new_category.delete()
    print(f"   ✅ Catégorie supprimée (ID: {category_id})")

    time.sleep(0.5)

    cached_value_after_delete = cache.get(test_key)
    print(f"   📊 Valeur après suppression: {cached_value_after_delete}")

    if cached_value_after_delete is None:
        print("   ✅ Cache invalidé correctement après suppression")
        cache_invalidated_delete = True
    else:
        print("   ❌ Cache non invalidé après suppression")
        cache_invalidated_delete = False

    return (
        cache_invalidated_create
        and cache_invalidated_update
        and cache_invalidated_delete
    )


def test_bulk_operations():
    """Test l'invalidation du cache avec les opérations en lot"""
    log_test_step("Test des opérations en lot")

    # Mettre une valeur en cache
    test_key = "bulk_test_key"
    cache.set(test_key, "bulk_test_value", 300)

    # Créer plusieurs catégories en lot
    categories_to_create = [
        Category(name=f"Bulk Category {i}", description=f"Catégorie en lot {i}")
        for i in range(3)
    ]

    with transaction.atomic():
        Category.objects.bulk_create(categories_to_create)
        print(f"   ✅ {len(categories_to_create)} catégories créées en lot")

    time.sleep(0.5)

    # Vérifier l'invalidation
    cached_value = cache.get(test_key)
    print(f"   📊 Valeur après création en lot: {cached_value}")

    # Nettoyer
    Category.objects.filter(name__startswith="Bulk Category").delete()

    if cached_value is None:
        print("   ✅ Cache invalidé correctement pour les opérations en lot")
        return True
    else:
        print("   ❌ Cache non invalidé pour les opérations en lot")
        return False


def test_different_models():
    """Test l'invalidation avec différents modèles"""
    log_test_step("Test avec différents modèles")

    # Test avec Tag
    test_key = "tag_test_key"
    cache.set(test_key, "tag_test_value", 300)

    tag = Tag.objects.create(name=f"Test Tag {datetime.now().strftime('%H%M%S')}")
    print(f"   ✅ Tag créé: {tag.name}")

    time.sleep(0.5)

    cached_value = cache.get(test_key)
    print(f"   📊 Valeur après création de tag: {cached_value}")

    # Nettoyer
    tag.delete()

    if cached_value is None:
        print("   ✅ Cache invalidé correctement pour Tag")
        return True
    else:
        print("   ❌ Cache non invalidé pour Tag")
        return False


def run_simple_test():
    """Lance tous les tests simples"""
    print("🚀 DÉBUT DES TESTS SIMPLES D'INVALIDATION DU CACHE VIA SIGNAUX")
    print("=" * 80)

    # Tests
    results = []

    try:
        # Test 1: Opérations CRUD de base
        results.append(
            ("Opérations CRUD", test_cache_invalidation_on_model_operations())
        )

        # Test 2: Opérations en lot
        results.append(("Opérations en lot", test_bulk_operations()))

        # Test 3: Différents modèles
        results.append(("Différents modèles", test_different_models()))

    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Résumé des résultats
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DES TESTS SIMPLES")
    print("=" * 80)

    all_passed = True
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"   {test_name}: {status}")
        if not result:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 TOUS LES TESTS SIMPLES SONT RÉUSSIS!")
        print("✅ Le middleware avec signaux Django fonctionne correctement")
        print("✅ Toutes les opérations CRUD déclenchent l'invalidation du cache")
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        print("❌ Vérifiez la configuration du middleware et des signaux")

    print("=" * 80)
    return all_passed


if __name__ == "__main__":
    success = run_simple_test()
    sys.exit(0 if success else 1)
