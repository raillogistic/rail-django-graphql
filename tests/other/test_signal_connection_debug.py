#!/usr/bin/env python3
"""
Test de diagnostic approfondi pour comprendre pourquoi les signaux ne sont pas détectés
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from test_app.models import Category, Tag

def debug_signal_receivers():
    """Debug détaillé des récepteurs de signaux"""
    print("🔍 ANALYSE DÉTAILLÉE DES RÉCEPTEURS DE SIGNAUX")
    print("=" * 80)
    
    # Analyser les récepteurs pour Category spécifiquement
    print(f"\n📡 RÉCEPTEURS POST_SAVE POUR CATEGORY:")
    try:
        category_post_save_receivers = post_save._live_receivers(sender=Category)
        print(f"   Récepteurs pour Category: {len(category_post_save_receivers)}")
        
        for i, receiver in enumerate(category_post_save_receivers):
            print(f"   [{i+1}] {receiver}")
            receiver_str = str(receiver)
            if 'cache' in receiver_str.lower() or 'middleware' in receiver_str.lower():
                print(f"       🎯 MIDDLEWARE POUR CATEGORY: {receiver_str}")
    except Exception as e:
        print(f"   ❌ Erreur lors de l'analyse des récepteurs Category post_save: {e}")
    
    # Analyser les récepteurs pour Tag spécifiquement
    print(f"\n📡 RÉCEPTEURS POST_SAVE POUR TAG:")
    try:
        tag_post_save_receivers = post_save._live_receivers(sender=Tag)
        print(f"   Récepteurs pour Tag: {len(tag_post_save_receivers)}")
        
        for i, receiver in enumerate(tag_post_save_receivers):
            print(f"   [{i+1}] {receiver}")
            receiver_str = str(receiver)
            if 'cache' in receiver_str.lower() or 'middleware' in receiver_str.lower():
                print(f"       🎯 MIDDLEWARE POUR TAG: {receiver_str}")
    except Exception as e:
        print(f"   ❌ Erreur lors de l'analyse des récepteurs Tag post_save: {e}")
    
    # Analyser les récepteurs pour Category spécifiquement
    print(f"\n📡 RÉCEPTEURS POST_DELETE POUR CATEGORY:")
    try:
        category_post_delete_receivers = post_delete._live_receivers(sender=Category)
        print(f"   Récepteurs pour Category: {len(category_post_delete_receivers)}")
        
        for i, receiver in enumerate(category_post_delete_receivers):
            print(f"   [{i+1}] {receiver}")
            receiver_str = str(receiver)
            if 'cache' in receiver_str.lower() or 'middleware' in receiver_str.lower():
                print(f"       🎯 MIDDLEWARE POUR CATEGORY: {receiver_str}")
    except Exception as e:
        print(f"   ❌ Erreur lors de l'analyse des récepteurs Category post_delete: {e}")
    
    # Analyser les récepteurs pour Tag spécifiquement
    print(f"\n📡 RÉCEPTEURS POST_DELETE POUR TAG:")
    try:
        tag_post_delete_receivers = post_delete._live_receivers(sender=Tag)
        print(f"   Récepteurs pour Tag: {len(tag_post_delete_receivers)}")
        
        for i, receiver in enumerate(tag_post_delete_receivers):
            print(f"   [{i+1}] {receiver}")
            receiver_str = str(receiver)
            if 'cache' in receiver_str.lower() or 'middleware' in receiver_str.lower():
                print(f"       🎯 MIDDLEWARE POUR TAG: {receiver_str}")
    except Exception as e:
        print(f"   ❌ Erreur lors de l'analyse des récepteurs Tag post_delete: {e}")
    
    # Analyser les récepteurs généraux (sans sender spécifique)
    print(f"\n📡 RÉCEPTEURS GÉNÉRAUX:")
    try:
        # Accéder directement aux récepteurs via l'attribut interne
        if hasattr(post_save, 'receivers'):
            print(f"   Récepteurs post_save généraux: {len(post_save.receivers)}")
            for i, (receiver_key, receiver) in enumerate(post_save.receivers):
                print(f"   [{i+1}] {receiver}")
                receiver_str = str(receiver)
                if 'cache' in receiver_str.lower() or 'middleware' in receiver_str.lower():
                    print(f"       🎯 MIDDLEWARE GÉNÉRAL: {receiver_str}")
        
        if hasattr(post_delete, 'receivers'):
            print(f"   Récepteurs post_delete généraux: {len(post_delete.receivers)}")
            for i, (receiver_key, receiver) in enumerate(post_delete.receivers):
                print(f"   [{i+1}] {receiver}")
                receiver_str = str(receiver)
                if 'cache' in receiver_str.lower() or 'middleware' in receiver_str.lower():
                    print(f"       🎯 MIDDLEWARE GÉNÉRAL: {receiver_str}")
    except Exception as e:
        print(f"   ❌ Erreur lors de l'analyse des récepteurs généraux: {e}")

def test_manual_signal_connection():
    """Test de connexion manuelle des signaux"""
    print("\n🔧 TEST DE CONNEXION MANUELLE DES SIGNAUX")
    print("=" * 80)
    
    # Importer et initialiser le middleware manuellement
    try:
        from cache_middleware import GraphQLCacheInvalidationMiddleware
        
        # Créer une fonction de réponse factice
        def dummy_get_response(request):
            return None
        
        print("📝 Initialisation du middleware...")
        middleware = GraphQLCacheInvalidationMiddleware(dummy_get_response)
        print("✅ Middleware initialisé")
        
        # Vérifier l'état des signaux connectés
        print(f"📊 Signaux connectés (flag): {GraphQLCacheInvalidationMiddleware._signals_connected}")
        
        # Forcer la reconnexion des signaux
        print("🔄 Forçage de la reconnexion des signaux...")
        GraphQLCacheInvalidationMiddleware._signals_connected = False
        middleware._connect_signals()
        GraphQLCacheInvalidationMiddleware._signals_connected = True
        print("✅ Signaux reconnectés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_signal_firing_with_debug():
    """Test du déclenchement des signaux avec debug"""
    print("\n🔥 TEST DU DÉCLENCHEMENT DES SIGNAUX")
    print("=" * 80)
    
    # Variables pour traquer les signaux
    signals_fired = []
    
    @receiver(post_save)
    def debug_receiver_save(sender, instance, created, **kwargs):
        signals_fired.append({
            'signal': 'post_save',
            'sender': sender.__name__,
            'instance': str(instance),
            'created': created,
            'time': datetime.now().strftime('%H:%M:%S.%f')
        })
        print(f"🔥 DEBUG POST_SAVE: {sender.__name__} - {instance} (created: {created})")
    
    @receiver(post_delete)
    def debug_receiver_delete(sender, instance, **kwargs):
        signals_fired.append({
            'signal': 'post_delete',
            'sender': sender.__name__,
            'instance': str(instance),
            'time': datetime.now().strftime('%H:%M:%S.%f')
        })
        print(f"🔥 DEBUG POST_DELETE: {sender.__name__} - {instance}")
    
    # Test avec Category
    print("📝 Création d'une catégorie de test...")
    category = Category.objects.create(
        name=f"Debug Signal Category {datetime.now().strftime('%H%M%S')}",
        description="Test de signaux"
    )
    print(f"✅ Catégorie créée: {category.name} (ID: {category.id})")
    
    print("📝 Modification de la catégorie...")
    category.description = f"Modifiée à {datetime.now().strftime('%H:%M:%S')}"
    category.save()
    print("✅ Catégorie modifiée")
    
    print("📝 Suppression de la catégorie...")
    category.delete()
    print("✅ Catégorie supprimée")
    
    print(f"\n📊 Signaux détectés: {len(signals_fired)}")
    for signal in signals_fired:
        print(f"   {signal['time']} - {signal['signal']} - {signal['sender']}")
    
    return len(signals_fired) > 0

def check_middleware_import():
    """Vérifier l'import et l'état du middleware"""
    print("\n🔍 VÉRIFICATION DE L'IMPORT DU MIDDLEWARE")
    print("=" * 80)
    
    try:
        from cache_middleware import GraphQLCacheInvalidationMiddleware
        print("✅ Import du middleware réussi")
        
        # Vérifier les attributs de classe
        print(f"📊 Classe: {GraphQLCacheInvalidationMiddleware}")
        print(f"📊 Signaux connectés (flag): {GraphQLCacheInvalidationMiddleware._signals_connected}")
        print(f"📊 Apps surveillées: {GraphQLCacheInvalidationMiddleware.MONITORED_APPS}")
        print(f"📊 Modèles exclus: {GraphQLCacheInvalidationMiddleware.EXCLUDED_MODELS}")
        
        # Vérifier les méthodes
        has_handle_model_change = hasattr(GraphQLCacheInvalidationMiddleware, '_handle_model_change')
        has_handle_m2m_change = hasattr(GraphQLCacheInvalidationMiddleware, '_handle_m2m_change')
        has_connect_signals = hasattr(GraphQLCacheInvalidationMiddleware, '_connect_signals')
        
        print(f"📊 Méthode _handle_model_change: {'✅' if has_handle_model_change else '❌'}")
        print(f"📊 Méthode _handle_m2m_change: {'✅' if has_handle_m2m_change else '❌'}")
        print(f"📊 Méthode _connect_signals: {'✅' if has_connect_signals else '❌'}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def run_comprehensive_debug():
    """Lance tous les tests de diagnostic"""
    print("🚀 DIAGNOSTIC COMPLET DES SIGNAUX DJANGO")
    print("=" * 100)
    
    # Test 1: Vérifier l'import du middleware
    middleware_ok = check_middleware_import()
    
    # Test 2: Analyser les récepteurs existants
    debug_signal_receivers()
    
    # Test 3: Test de connexion manuelle
    manual_connection_ok = test_manual_signal_connection()
    
    # Test 4: Analyser les récepteurs après connexion manuelle
    if manual_connection_ok:
        print("\n" + "=" * 80)
        print("📡 ANALYSE APRÈS CONNEXION MANUELLE")
        debug_signal_receivers()
    
    # Test 5: Test du déclenchement des signaux
    signals_firing = test_signal_firing_with_debug()
    
    # Résumé final
    print("\n" + "=" * 100)
    print("📊 RÉSUMÉ DU DIAGNOSTIC COMPLET")
    print("=" * 100)
    
    print(f"🔧 Import du middleware: {'✅ OK' if middleware_ok else '❌ ÉCHEC'}")
    print(f"🔧 Connexion manuelle: {'✅ OK' if manual_connection_ok else '❌ ÉCHEC'}")
    print(f"🔥 Signaux se déclenchent: {'✅ OUI' if signals_firing else '❌ NON'}")
    
    if middleware_ok and manual_connection_ok and signals_firing:
        print("\n🎉 DIAGNOSTIC RÉUSSI - Le système de signaux fonctionne")
    else:
        print("\n⚠️ PROBLÈMES DÉTECTÉS - Vérifiez la configuration")
    
    print("=" * 100)
    
    return middleware_ok and manual_connection_ok and signals_firing

if __name__ == "__main__":
    success = run_comprehensive_debug()
    sys.exit(0 if success else 1)