#!/usr/bin/env python3
"""
Test direct pour vérifier si cache.clear() fonctionne et si les gestionnaires de signaux sont appelés
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rail_django_graphql.settings')
django.setup()

from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from test_app.models import Category, Tag

# Variables globales pour traquer les appels
signal_calls = []

def track_signal_call(signal_type, sender, instance):
    """Fonction pour traquer les appels de signaux"""
    signal_calls.append({
        'signal': signal_type,
        'sender': sender.__name__,
        'instance_id': getattr(instance, 'pk', None),
        'instance_str': str(instance),
        'time': datetime.now().strftime('%H:%M:%S.%f')
    })
    print(f"🔥 SIGNAL TRACKÉ: {signal_type} - {sender.__name__} - {instance}")

def test_cache_clear_direct():
    """Test direct de cache.clear()"""
    print("🧪 TEST DIRECT DE CACHE.CLEAR()")
    print("=" * 80)
    
    # Nettoyer le cache
    cache.clear()
    print("🧹 Cache nettoyé")
    
    # Ajouter des données
    test_data = {
        'key1': 'value1',
        'key2': 'value2',
        'key3': 'value3'
    }
    
    print("📝 Ajout de données au cache...")
    for key, value in test_data.items():
        cache.set(key, value, 300)
        print(f"   ✅ {key} = {value}")
    
    # Vérifier que les données sont présentes
    print("\n🔍 Vérification des données...")
    all_present_before = True
    for key, expected_value in test_data.items():
        actual_value = cache.get(key)
        is_present = actual_value == expected_value
        all_present_before = all_present_before and is_present
        print(f"   {key}: {'✅' if is_present else '❌'} - {actual_value}")
    
    # Appeler cache.clear()
    print("\n🗑️ Appel de cache.clear()...")
    cache.clear()
    print("✅ cache.clear() exécuté")
    
    # Vérifier que les données ont été supprimées
    print("\n🔍 Vérification après cache.clear()...")
    all_cleared = True
    for key in test_data.keys():
        value = cache.get(key)
        is_cleared = value is None
        all_cleared = all_cleared and is_cleared
        print(f"   {key}: {'✅ SUPPRIMÉ' if is_cleared else '❌ PRÉSENT'} - {value}")
    
    print(f"\n📊 Résultat: cache.clear() {'✅ FONCTIONNE' if all_cleared else '❌ NE FONCTIONNE PAS'}")
    return all_cleared

def test_signal_handlers_direct():
    """Test direct des gestionnaires de signaux"""
    print("\n🧪 TEST DIRECT DES GESTIONNAIRES DE SIGNAUX")
    print("=" * 80)
    
    # Réinitialiser le tracking
    global signal_calls
    signal_calls = []
    
    # Connecter nos propres gestionnaires pour traquer
    def track_post_save(sender, instance, created, **kwargs):
        track_signal_call('post_save', sender, instance)
    
    def track_post_delete(sender, instance, **kwargs):
        track_signal_call('post_delete', sender, instance)
    
    # Connecter les signaux
    post_save.connect(track_post_save, sender=Category)
    post_delete.connect(track_post_delete, sender=Category)
    
    print("📡 Signaux de tracking connectés")
    
    # Test avec Category
    print("\n📝 Test avec Category...")
    
    # Créer
    category = Category.objects.create(
        name=f"Direct Test Category {datetime.now().strftime('%H%M%S')}",
        description="Test direct des signaux"
    )
    print(f"✅ Catégorie créée: {category.name} (ID: {category.id})")
    
    # Modifier
    category.description = f"Modifiée à {datetime.now().strftime('%H:%M:%S')}"
    category.save()
    print("✅ Catégorie modifiée")
    
    # Supprimer
    category.delete()
    print("✅ Catégorie supprimée")
    
    # Déconnecter nos signaux
    post_save.disconnect(track_post_save, sender=Category)
    post_delete.disconnect(track_post_delete, sender=Category)
    
    # Analyser les résultats
    print(f"\n📊 Signaux détectés: {len(signal_calls)}")
    for call in signal_calls:
        print(f"   {call['time']} - {call['signal']} - {call['sender']} - ID:{call['instance_id']}")
    
    expected_signals = 3  # 2 post_save (create, update) + 1 post_delete
    signals_working = len(signal_calls) >= expected_signals
    
    print(f"\n📊 Résultat: signaux {'✅ FONCTIONNENT' if signals_working else '❌ NE FONCTIONNENT PAS'}")
    return signals_working

def test_middleware_handlers():
    """Test des gestionnaires du middleware"""
    print("\n🧪 TEST DES GESTIONNAIRES DU MIDDLEWARE")
    print("=" * 80)
    
    # Initialiser le middleware
    try:
        from cache_middleware import GraphQLCacheInvalidationMiddleware
        
        def dummy_get_response(request):
            return None
        
        print("🔧 Initialisation du middleware...")
        middleware = GraphQLCacheInvalidationMiddleware(dummy_get_response)
        print(f"✅ Middleware initialisé - Signaux connectés: {GraphQLCacheInvalidationMiddleware._signals_connected}")
        
        # Ajouter des données au cache
        cache.clear()
        cache.set('test_middleware', 'middleware_test_value', 300)
        
        # Vérifier que la donnée est présente
        value_before = cache.get('test_middleware')
        print(f"📝 Valeur avant création: {'✅' if value_before else '❌'} - {value_before}")
        
        # Créer une catégorie (doit déclencher l'invalidation)
        print("📝 Création d'une catégorie...")
        category = Category.objects.create(
            name=f"Middleware Test Category {datetime.now().strftime('%H%M%S')}",
            description="Test des gestionnaires du middleware"
        )
        print(f"✅ Catégorie créée: {category.name} (ID: {category.id})")
        
        # Vérifier si le cache a été invalidé
        value_after = cache.get('test_middleware')
        cache_invalidated = value_after is None
        
        print(f"📝 Valeur après création: {'❌ INVALIDÉ' if cache_invalidated else '✅ PRÉSENT'} - {value_after}")
        
        # Nettoyer
        category.delete()
        
        print(f"\n📊 Résultat: middleware {'✅ FONCTIONNE' if cache_invalidated else '❌ NE FONCTIONNE PAS'}")
        return cache_invalidated
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_direct_debug_tests():
    """Lance tous les tests de debug direct"""
    print("🚀 TESTS DE DEBUG DIRECT")
    print("=" * 100)
    
    # Test 1: cache.clear()
    cache_clear_ok = test_cache_clear_direct()
    
    # Test 2: Signaux Django
    signals_ok = test_signal_handlers_direct()
    
    # Test 3: Gestionnaires du middleware
    middleware_ok = test_middleware_handlers()
    
    # Résumé
    print("\n" + "=" * 100)
    print("📊 RÉSUMÉ DES TESTS DIRECTS")
    print("=" * 100)
    
    print(f"🗑️ cache.clear(): {'✅ OK' if cache_clear_ok else '❌ ÉCHEC'}")
    print(f"📡 Signaux Django: {'✅ OK' if signals_ok else '❌ ÉCHEC'}")
    print(f"🔧 Middleware: {'✅ OK' if middleware_ok else '❌ ÉCHEC'}")
    
    overall_success = cache_clear_ok and signals_ok and middleware_ok
    
    if overall_success:
        print("\n🎉 TOUS LES TESTS DIRECTS RÉUSSIS !")
    else:
        print("\n⚠️ PROBLÈMES DÉTECTÉS DANS LES TESTS DIRECTS")
        
        if not cache_clear_ok:
            print("   - cache.clear() ne fonctionne pas correctement")
        if not signals_ok:
            print("   - Les signaux Django ne se déclenchent pas")
        if not middleware_ok:
            print("   - Les gestionnaires du middleware ne fonctionnent pas")
    
    print("=" * 100)
    
    return overall_success

if __name__ == "__main__":
    success = run_direct_debug_tests()
    sys.exit(0 if success else 1)