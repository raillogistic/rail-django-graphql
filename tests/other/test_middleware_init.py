#!/usr/bin/env python3
"""
Test pour initialiser correctement le middleware et tester l'invalidation du cache
"""

import os
import sys
import django
import time
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
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

def initialize_middleware():
    """Initialise le middleware manuellement pour connecter les signaux"""
    try:
        from cache_middleware import GraphQLCacheInvalidationMiddleware
        
        # Créer une fonction de réponse factice
        def dummy_get_response(request):
            return None
        
        # Initialiser le middleware
        middleware = GraphQLCacheInvalidationMiddleware(dummy_get_response)
        
        log_test_step("Middleware initialisé", "Signaux Django connectés")
        return middleware
        
    except Exception as e:
        log_test_step("Erreur d'initialisation du middleware", str(e))
        return None

def test_cache_invalidation_with_middleware():
    """Test l'invalidation du cache avec le middleware initialisé"""
    log_test_step("Test d'invalidation du cache avec middleware")
    
    # 1. Initialiser le middleware
    middleware = initialize_middleware()
    if not middleware:
        print("   ❌ Impossible d'initialiser le middleware")
        return False
    
    # 2. Effacer le cache et ajouter une clé de test
    cache.clear()
    test_key = "test_middleware_key"
    test_value = "test_middleware_value"
    cache.set(test_key, test_value, 300)  # 5 minutes
    
    # Vérifier que la clé est en cache
    cached_value = cache.get(test_key)
    print(f"   📊 Valeur initiale en cache: {cached_value}")
    
    if cached_value != test_value:
        print("   ❌ Erreur: la valeur n'a pas été mise en cache correctement")
        return False
    
    # 3. Créer une catégorie (doit déclencher l'invalidation via signal)
    log_test_step("Création d'une catégorie pour déclencher l'invalidation")
    
    with transaction.atomic():
        new_category = Category.objects.create(
            name=f"Test Middleware Category {datetime.now().strftime('%H%M%S')}",
            description="Test d'invalidation par middleware"
        )
        print(f"   ✅ Catégorie créée: {new_category.name} (ID: {new_category.id})")
    
    # 4. Attendre un peu pour que les signaux se déclenchent
    time.sleep(0.5)
    
    # 5. Vérifier que le cache a été invalidé
    log_test_step("Vérification de l'invalidation du cache")
    cached_value_after = cache.get(test_key)
    print(f"   📊 Valeur après création: {cached_value_after}")
    
    if cached_value_after is None:
        print("   ✅ Cache invalidé correctement - clé supprimée")
        cache_invalidated_create = True
    else:
        print("   ❌ Cache non invalidé - clé toujours présente")
        cache_invalidated_create = False
    
    # 6. Test de modification
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
    
    # 7. Test de suppression
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
    
    return cache_invalidated_create and cache_invalidated_update and cache_invalidated_delete

def test_bulk_operations_with_middleware():
    """Test les opérations en lot avec le middleware"""
    log_test_step("Test des opérations en lot avec middleware")
    
    # Mettre une valeur en cache
    test_key = "bulk_middleware_key"
    cache.set(test_key, "bulk_middleware_value", 300)
    
    # Créer plusieurs catégories en lot
    categories_to_create = [
        Category(name=f"Bulk Middleware Category {i}", description=f"Catégorie en lot {i}")
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
    Category.objects.filter(name__startswith="Bulk Middleware Category").delete()
    
    if cached_value is None:
        print("   ✅ Cache invalidé correctement pour les opérations en lot")
        return True
    else:
        print("   ❌ Cache non invalidé pour les opérations en lot")
        return False

def test_different_models_with_middleware():
    """Test avec différents modèles et le middleware"""
    log_test_step("Test avec différents modèles et middleware")
    
    # Test avec Tag
    test_key = "tag_middleware_key"
    cache.set(test_key, "tag_middleware_value", 300)
    
    tag = Tag.objects.create(name=f"Test Middleware Tag {datetime.now().strftime('%H%M%S')}")
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

def check_signal_connections():
    """Vérifier que les signaux sont bien connectés après initialisation du middleware"""
    log_test_step("Vérification des connexions de signaux")
    
    from django.db.models.signals import post_save, post_delete
    
    # Vérifier les connexions pour Category
    post_save_receivers = post_save._live_receivers(sender=Category)
    post_delete_receivers = post_delete._live_receivers(sender=Category)
    
    print(f"   📡 Récepteurs post_save pour Category: {len(post_save_receivers)}")
    print(f"   📡 Récepteurs post_delete pour Category: {len(post_delete_receivers)}")
    
    # Chercher les récepteurs du middleware
    middleware_receivers = 0
    for receiver in post_save_receivers:
        if 'cache_invalidation' in str(receiver) or 'GraphQLCacheInvalidationMiddleware' in str(receiver):
            middleware_receivers += 1
    
    for receiver in post_delete_receivers:
        if 'cache_invalidation' in str(receiver) or 'GraphQLCacheInvalidationMiddleware' in str(receiver):
            middleware_receivers += 1
    
    print(f"   🔧 Récepteurs du middleware: {middleware_receivers}")
    
    return middleware_receivers > 0

def run_middleware_test():
    """Lance tous les tests avec le middleware"""
    print("🚀 TEST D'INVALIDATION DU CACHE AVEC MIDDLEWARE INITIALISÉ")
    print("=" * 80)
    
    # Vérifier les connexions de signaux
    signals_connected = check_signal_connections()
    
    # Tests
    results = []
    
    try:
        # Test 1: Opérations CRUD de base
        results.append(("Opérations CRUD avec middleware", test_cache_invalidation_with_middleware()))
        
        # Test 2: Opérations en lot
        results.append(("Opérations en lot avec middleware", test_bulk_operations_with_middleware()))
        
        # Test 3: Différents modèles
        results.append(("Différents modèles avec middleware", test_different_models_with_middleware()))
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Résumé des résultats
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DES TESTS AVEC MIDDLEWARE")
    print("=" * 80)
    
    print(f"🔧 Signaux connectés: {'✅ OUI' if signals_connected else '❌ NON'}")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"   {test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed and signals_connected:
        print("🎉 TOUS LES TESTS AVEC MIDDLEWARE SONT RÉUSSIS!")
        print("✅ Le middleware avec signaux Django fonctionne correctement")
        print("✅ Toutes les opérations CRUD déclenchent l'invalidation du cache")
    else:
        print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ OU SIGNAUX NON CONNECTÉS")
        if not signals_connected:
            print("❌ Les signaux du middleware ne sont pas connectés")
        print("❌ Vérifiez la configuration du middleware et des signaux")
    
    print("=" * 80)
    return all_passed and signals_connected

if __name__ == "__main__":
    success = run_middleware_test()
    sys.exit(0 if success else 1)