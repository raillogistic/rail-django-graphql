#!/usr/bin/env python3
"""
Test de diagnostic pour vérifier la connexion et le déclenchement des signaux Django
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from test_app.models import Category, Tag

# Variables globales pour traquer les signaux
signal_fired = {"post_save": False, "post_delete": False, "m2m_changed": False}

signal_details = []


@receiver(post_save)
def debug_post_save(sender, instance, created, **kwargs):
    """Récepteur de debug pour post_save"""
    global signal_fired, signal_details
    signal_fired["post_save"] = True
    signal_details.append(
        {
            "signal": "post_save",
            "sender": sender.__name__,
            "instance": str(instance),
            "created": created,
            "time": datetime.now().strftime("%H:%M:%S.%f"),
        }
    )
    print(
        f"🔥 POST_SAVE signal fired: {sender.__name__} - {instance} (created: {created})"
    )


@receiver(post_delete)
def debug_post_delete(sender, instance, **kwargs):
    """Récepteur de debug pour post_delete"""
    global signal_fired, signal_details
    signal_fired["post_delete"] = True
    signal_details.append(
        {
            "signal": "post_delete",
            "sender": sender.__name__,
            "instance": str(instance),
            "time": datetime.now().strftime("%H:%M:%S.%f"),
        }
    )
    print(f"🔥 POST_DELETE signal fired: {sender.__name__} - {instance}")


@receiver(m2m_changed)
def debug_m2m_changed(sender, instance, action, pk_set, **kwargs):
    """Récepteur de debug pour m2m_changed"""
    global signal_fired, signal_details
    signal_fired["m2m_changed"] = True
    signal_details.append(
        {
            "signal": "m2m_changed",
            "sender": sender.__name__,
            "instance": str(instance),
            "action": action,
            "pk_set": pk_set,
            "time": datetime.now().strftime("%H:%M:%S.%f"),
        }
    )
    print(
        f"🔥 M2M_CHANGED signal fired: {sender.__name__} - {instance} (action: {action})"
    )


def test_signal_connections():
    """Test si les signaux sont connectés"""
    print("🔍 VÉRIFICATION DES CONNEXIONS DE SIGNAUX")
    print("=" * 60)

    # Vérifier les connexions post_save
    post_save_receivers = post_save._live_receivers(sender=Category)
    print(f"📡 Récepteurs post_save pour Category: {len(post_save_receivers)}")
    for receiver in post_save_receivers:
        print(f"   - {receiver}")

    # Vérifier les connexions post_delete
    post_delete_receivers = post_delete._live_receivers(sender=Category)
    print(f"📡 Récepteurs post_delete pour Category: {len(post_delete_receivers)}")
    for receiver in post_delete_receivers:
        print(f"   - {receiver}")

    print()


def test_manual_signals():
    """Test manuel des signaux"""
    print("🧪 TEST MANUEL DES SIGNAUX DJANGO")
    print("=" * 60)

    # Réinitialiser les trackers
    global signal_fired, signal_details
    signal_fired = {"post_save": False, "post_delete": False, "m2m_changed": False}
    signal_details = []

    print("📝 Création d'une catégorie...")
    category = Category.objects.create(
        name=f"Debug Category {datetime.now().strftime('%H%M%S')}",
        description="Test de signaux",
    )
    print(f"✅ Catégorie créée: {category.name} (ID: {category.id})")

    print("\n📝 Modification de la catégorie...")
    category.description = f"Modifiée à {datetime.now().strftime('%H:%M:%S')}"
    category.save()
    print("✅ Catégorie modifiée")

    print("\n📝 Suppression de la catégorie...")
    category_id = category.id
    category.delete()
    print(f"✅ Catégorie supprimée (ID: {category_id})")

    # Test avec Tag et relation M2M
    print("\n📝 Test avec Tag et relation M2M...")
    tag1 = Tag.objects.create(name=f"Debug Tag 1 {datetime.now().strftime('%H%M%S')}")
    tag2 = Tag.objects.create(name=f"Debug Tag 2 {datetime.now().strftime('%H%M%S')}")

    category2 = Category.objects.create(
        name=f"Debug Category M2M {datetime.now().strftime('%H%M%S')}",
        description="Test M2M",
    )

    print("📝 Ajout de tags à la catégorie...")
    category2.tags.add(tag1, tag2)
    print("✅ Tags ajoutés")

    print("📝 Suppression d'un tag de la catégorie...")
    category2.tags.remove(tag1)
    print("✅ Tag supprimé")

    # Nettoyage
    category2.delete()
    tag1.delete()
    tag2.delete()

    return signal_fired, signal_details


def check_middleware_signals():
    """Vérifier si le middleware a connecté ses signaux"""
    print("🔍 VÉRIFICATION DES SIGNAUX DU MIDDLEWARE")
    print("=" * 60)

    try:
        from cache_middleware import GraphQLCacheInvalidationMiddleware

        # Vérifier si les signaux sont connectés
        middleware_receivers = []

        # Chercher les récepteurs du middleware dans post_save
        for receiver in post_save._live_receivers(sender=Category):
            if "GraphQLCacheInvalidationMiddleware" in str(
                receiver
            ) or "cache_invalidation" in str(receiver):
                middleware_receivers.append(("post_save", receiver))

        # Chercher les récepteurs du middleware dans post_delete
        for receiver in post_delete._live_receivers(sender=Category):
            if "GraphQLCacheInvalidationMiddleware" in str(
                receiver
            ) or "cache_invalidation" in str(receiver):
                middleware_receivers.append(("post_delete", receiver))

        print(f"📡 Récepteurs du middleware trouvés: {len(middleware_receivers)}")
        for signal_type, receiver in middleware_receivers:
            print(f"   - {signal_type}: {receiver}")

        return len(middleware_receivers) > 0

    except ImportError as e:
        print(f"❌ Erreur d'import du middleware: {e}")
        return False


def run_debug_test():
    """Lance tous les tests de diagnostic"""
    print("🚀 DIAGNOSTIC DES SIGNAUX DJANGO")
    print("=" * 80)

    # Test 1: Vérifier les connexions
    test_signal_connections()

    # Test 2: Vérifier les signaux du middleware
    middleware_connected = check_middleware_signals()

    # Test 3: Test manuel des signaux
    signals_fired, details = test_manual_signals()

    # Résumé
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DU DIAGNOSTIC")
    print("=" * 80)

    print(f"🔧 Middleware connecté: {'✅ OUI' if middleware_connected else '❌ NON'}")
    print(
        f"🔥 post_save déclenché: {'✅ OUI' if signals_fired['post_save'] else '❌ NON'}"
    )
    print(
        f"🔥 post_delete déclenché: {'✅ OUI' if signals_fired['post_delete'] else '❌ NON'}"
    )
    print(
        f"🔥 m2m_changed déclenché: {'✅ OUI' if signals_fired['m2m_changed'] else '❌ NON'}"
    )

    if details:
        print("\n📋 DÉTAILS DES SIGNAUX DÉCLENCHÉS:")
        for detail in details:
            print(
                f"   {detail['time']} - {detail['signal']} - {detail['sender']} - {detail.get('action', 'N/A')}"
            )

    print("\n" + "=" * 80)

    if (
        middleware_connected
        and signals_fired["post_save"]
        and signals_fired["post_delete"]
    ):
        print("🎉 DIAGNOSTIC RÉUSSI - Les signaux fonctionnent correctement")
    else:
        print("⚠️ PROBLÈME DÉTECTÉ - Vérifiez la configuration des signaux")

    print("=" * 80)


if __name__ == "__main__":
    run_debug_test()
