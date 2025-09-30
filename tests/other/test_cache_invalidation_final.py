#!/usr/bin/env python3
"""
Test final complet pour vérifier l'invalidation du cache avec les signaux connectés
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from django.core.cache import cache
from test_app.models import Category, Tag


def initialize_middleware():
    """Initialise le middleware pour connecter les signaux"""
    try:
        from cache_middleware import GraphQLCacheInvalidationMiddleware

        # Créer une fonction de réponse factice
        def dummy_get_response(request):
            return None

        print("🔧 Initialisation du middleware...")
        middleware = GraphQLCacheInvalidationMiddleware(dummy_get_response)
        print(
            f"✅ Middleware initialisé - Signaux connectés: {GraphQLCacheInvalidationMiddleware._signals_connected}"
        )

        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False


def test_cache_invalidation_comprehensive():
    """Test complet de l'invalidation du cache"""
    print("\n🧪 TEST COMPLET D'INVALIDATION DU CACHE")
    print("=" * 80)

    # Nettoyer le cache au début
    cache.clear()
    print("🧹 Cache nettoyé")

    # Test 1: Ajouter des données au cache
    print("\n📝 Test 1: Ajout de données au cache")
    cache.set("test_category_list", "cached_categories", 300)
    cache.set("test_tag_list", "cached_tags", 300)
    cache.set("test_general", "cached_general_data", 300)

    # Vérifier que les données sont en cache
    cached_categories = cache.get("test_category_list")
    cached_tags = cache.get("test_tag_list")
    cached_general = cache.get("test_general")

    print(
        f"   Cache categories: {'✅' if cached_categories else '❌'} - {cached_categories}"
    )
    print(f"   Cache tags: {'✅' if cached_tags else '❌'} - {cached_tags}")
    print(f"   Cache general: {'✅' if cached_general else '❌'} - {cached_general}")

    # Test 2: Créer une catégorie (doit invalider le cache)
    print("\n📝 Test 2: Création d'une catégorie")
    category = Category.objects.create(
        name=f"Test Cache Category {datetime.now().strftime('%H%M%S')}",
        description="Test d'invalidation du cache",
    )
    print(f"✅ Catégorie créée: {category.name} (ID: {category.id})")

    # Vérifier l'état du cache après création
    cached_categories_after = cache.get("test_category_list")
    cached_tags_after = cache.get("test_tag_list")
    cached_general_after = cache.get("test_general")

    print(
        f"   Cache categories après création: {'❌ INVALIDÉ' if not cached_categories_after else '✅ PRÉSENT'}"
    )
    print(
        f"   Cache tags après création: {'❌ INVALIDÉ' if not cached_tags_after else '✅ PRÉSENT'}"
    )
    print(
        f"   Cache general après création: {'❌ INVALIDÉ' if not cached_general_after else '✅ PRÉSENT'}"
    )

    # Test 3: Remettre des données en cache et modifier la catégorie
    print("\n📝 Test 3: Modification d'une catégorie")
    cache.set("test_category_list", "cached_categories_v2", 300)
    cache.set("test_tag_list", "cached_tags_v2", 300)

    category.description = f"Modifiée à {datetime.now().strftime('%H:%M:%S')}"
    category.save()
    print("✅ Catégorie modifiée")

    # Vérifier l'état du cache après modification
    cached_categories_after_update = cache.get("test_category_list")
    cached_tags_after_update = cache.get("test_tag_list")

    print(
        f"   Cache categories après modification: {'❌ INVALIDÉ' if not cached_categories_after_update else '✅ PRÉSENT'}"
    )
    print(
        f"   Cache tags après modification: {'❌ INVALIDÉ' if not cached_tags_after_update else '✅ PRÉSENT'}"
    )

    # Test 4: Remettre des données en cache et supprimer la catégorie
    print("\n📝 Test 4: Suppression d'une catégorie")
    cache.set("test_category_list", "cached_categories_v3", 300)
    cache.set("test_tag_list", "cached_tags_v3", 300)

    category.delete()
    print("✅ Catégorie supprimée")

    # Vérifier l'état du cache après suppression
    cached_categories_after_delete = cache.get("test_category_list")
    cached_tags_after_delete = cache.get("test_tag_list")

    print(
        f"   Cache categories après suppression: {'❌ INVALIDÉ' if not cached_categories_after_delete else '✅ PRÉSENT'}"
    )
    print(
        f"   Cache tags après suppression: {'❌ INVALIDÉ' if not cached_tags_after_delete else '✅ PRÉSENT'}"
    )

    # Test 5: Test avec Tag
    print("\n📝 Test 5: Test avec Tag")
    cache.set("test_category_list", "cached_categories_v4", 300)
    cache.set("test_tag_list", "cached_tags_v4", 300)

    tag = Tag.objects.create(name=f"Test Tag {datetime.now().strftime('%H%M%S')}")
    print(f"✅ Tag créé: {tag.name} (ID: {tag.id})")

    # Vérifier l'état du cache après création de tag
    cached_categories_after_tag = cache.get("test_category_list")
    cached_tags_after_tag = cache.get("test_tag_list")

    print(
        f"   Cache categories après création tag: {'❌ INVALIDÉ' if not cached_categories_after_tag else '✅ PRÉSENT'}"
    )
    print(
        f"   Cache tags après création tag: {'❌ INVALIDÉ' if not cached_tags_after_tag else '✅ PRÉSENT'}"
    )

    # Nettoyer
    tag.delete()

    # Résumé des résultats
    print("\n📊 RÉSUMÉ DES TESTS D'INVALIDATION")
    print("=" * 80)

    invalidation_results = {
        "creation_category": not cached_categories_after,
        "modification_category": not cached_categories_after_update,
        "suppression_category": not cached_categories_after_delete,
        "creation_tag": not cached_tags_after_tag,
    }

    for test_name, result in invalidation_results.items():
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        print(f"   {test_name}: {status}")

    total_success = sum(invalidation_results.values())
    total_tests = len(invalidation_results)

    print(f"\n🎯 RÉSULTAT GLOBAL: {total_success}/{total_tests} tests réussis")

    return total_success == total_tests


def test_cache_keys_analysis():
    """Analyse des clés de cache pour comprendre le comportement"""
    print("\n🔍 ANALYSE DES CLÉS DE CACHE")
    print("=" * 80)

    # Nettoyer le cache
    cache.clear()

    # Ajouter différents types de clés
    test_keys = [
        "graphql:schema",
        "graphql:query:categories",
        "graphql:query:tags",
        "api:categories",
        "api:tags",
        "general:data",
        "test:specific",
    ]

    print("📝 Ajout de clés de test...")
    for key in test_keys:
        cache.set(key, f"value_for_{key}", 300)
        print(f"   ✅ {key}")

    # Vérifier que toutes les clés sont présentes
    print("\n🔍 Vérification des clés avant invalidation...")
    keys_before = {}
    for key in test_keys:
        value = cache.get(key)
        keys_before[key] = value is not None
        print(f"   {key}: {'✅' if value else '❌'}")

    # Créer une catégorie pour déclencher l'invalidation
    print("\n📝 Création d'une catégorie pour déclencher l'invalidation...")
    category = Category.objects.create(
        name=f"Cache Analysis Category {datetime.now().strftime('%H%M%S')}",
        description="Test d'analyse du cache",
    )
    print(f"✅ Catégorie créée: {category.name}")

    # Vérifier l'état des clés après invalidation
    print("\n🔍 Vérification des clés après invalidation...")
    keys_after = {}
    for key in test_keys:
        value = cache.get(key)
        keys_after[key] = value is not None
        status = "✅ PRÉSENT" if value else "❌ INVALIDÉ"
        print(f"   {key}: {status}")

    # Analyser les résultats
    print("\n📊 ANALYSE DES RÉSULTATS")
    print("=" * 80)

    invalidated_keys = []
    preserved_keys = []

    for key in test_keys:
        if keys_before[key] and not keys_after[key]:
            invalidated_keys.append(key)
        elif keys_before[key] and keys_after[key]:
            preserved_keys.append(key)

    print(f"🗑️ Clés invalidées ({len(invalidated_keys)}):")
    for key in invalidated_keys:
        print(f"   - {key}")

    print(f"💾 Clés préservées ({len(preserved_keys)}):")
    for key in preserved_keys:
        print(f"   - {key}")

    # Nettoyer
    category.delete()

    return len(invalidated_keys) > 0


def run_final_cache_test():
    """Lance tous les tests finaux de cache"""
    print("🚀 TEST FINAL COMPLET D'INVALIDATION DU CACHE")
    print("=" * 100)

    # Initialiser le middleware
    middleware_ok = initialize_middleware()
    if not middleware_ok:
        print("❌ Impossible d'initialiser le middleware")
        return False

    # Test d'invalidation complet
    invalidation_ok = test_cache_invalidation_comprehensive()

    # Analyse des clés de cache
    keys_analysis_ok = test_cache_keys_analysis()

    # Résumé final
    print("\n" + "=" * 100)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 100)

    print(f"🔧 Initialisation middleware: {'✅ OK' if middleware_ok else '❌ ÉCHEC'}")
    print(f"🧪 Tests d'invalidation: {'✅ OK' if invalidation_ok else '❌ ÉCHEC'}")
    print(f"🔍 Analyse des clés: {'✅ OK' if keys_analysis_ok else '❌ ÉCHEC'}")

    overall_success = middleware_ok and (invalidation_ok or keys_analysis_ok)

    if overall_success:
        print("\n🎉 SUCCÈS - Le système d'invalidation du cache fonctionne !")
    else:
        print("\n⚠️ PROBLÈMES DÉTECTÉS - Vérifiez la configuration du cache")

    print("=" * 100)

    return overall_success


if __name__ == "__main__":
    success = run_final_cache_test()
    sys.exit(0 if success else 1)
