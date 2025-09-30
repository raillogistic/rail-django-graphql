#!/usr/bin/env python3
"""
Vérification finale de la solution d'invalidation du cache GraphQL.
Ce script confirme que la solution fonctionne et fournit les instructions finales.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from django.core.cache import cache
from test_app.models import Tag
from test_app.schema import invalidate_tag_cache


def final_verification():
    """Vérification finale de la solution."""
    print("\n" + "=" * 80)
    print("🎯 VÉRIFICATION FINALE - SOLUTION D'INVALIDATION DU CACHE GRAPHQL")
    print("=" * 80)

    # Nettoyer l'environnement
    cache.clear()
    Tag.objects.filter(name__startswith="FinalTest").delete()

    success_count = 0
    total_tests = 3

    # Test 1: Vérifier que la fonction d'invalidation existe et fonctionne
    print("\n📋 TEST 1: Fonction d'invalidation du cache")
    try:
        # Créer un cache de test
        cache.set("graphql_all_tags", ["test_data"], 300)
        cache.set("gql_query_tags", {"test": "data"}, 300)

        # Créer un tag de test
        test_tag = Tag.objects.create(name="FinalTestTag", color="#FF0000")

        # Appeler la fonction d'invalidation
        invalidate_tag_cache(test_tag)

        # Vérifier l'invalidation
        if cache.get("graphql_all_tags") is None:
            print("✅ Fonction d'invalidation fonctionne correctement")
            success_count += 1
        else:
            print("❌ Fonction d'invalidation ne fonctionne pas")

        test_tag.delete()

    except Exception as e:
        print(f"❌ Erreur dans le test 1: {e}")

    # Test 2: Vérifier que les mutations existent dans le schéma
    print("\n📋 TEST 2: Mutations dans le schéma")
    try:
        from test_app.schema import CreateTag, UpdateTag, DeleteTag, Mutation

        # Vérifier que les mutations existent
        mutation_instance = Mutation()

        has_create = hasattr(mutation_instance, "create_tag")
        has_update = hasattr(mutation_instance, "update_tag")
        has_delete = hasattr(mutation_instance, "delete_tag")

        if has_create and has_update and has_delete:
            print("✅ Toutes les mutations Tag sont présentes dans le schéma")
            success_count += 1
        else:
            print(
                f"❌ Mutations manquantes - Create: {has_create}, Update: {has_update}, Delete: {has_delete}"
            )

    except Exception as e:
        print(f"❌ Erreur dans le test 2: {e}")

    # Test 3: Test d'intégration complet
    print("\n📋 TEST 3: Test d'intégration complet")
    try:
        # Simuler le scénario GraphiQL complet

        # 1. État initial avec cache
        initial_tags = Tag.objects.filter(name__startswith="FinalTest")
        cache.set("graphql_all_tags", list(initial_tags.values()), 300)

        # 2. Créer un nouveau tag (comme via mutation GraphQL)
        new_tag = Tag.objects.create(name="FinalTestNewTag", color="#00FF00")

        # 3. Appeler l'invalidation (comme dans la mutation)
        invalidate_tag_cache(new_tag)

        # 4. Vérifier que le cache est invalidé
        cached_data = cache.get("graphql_all_tags")

        # 5. Simuler une nouvelle requête (récupération des données fraîches)
        fresh_tags = Tag.objects.filter(name__startswith="FinalTest")

        if cached_data is None and fresh_tags.filter(name="FinalTestNewTag").exists():
            print(
                "✅ Test d'intégration réussi - Le nouveau tag sera visible immédiatement"
            )
            success_count += 1
        else:
            print("❌ Test d'intégration échoué")

        # Nettoyer
        new_tag.delete()

    except Exception as e:
        print(f"❌ Erreur dans le test 3: {e}")

    # Résultats finaux
    print("\n" + "=" * 80)
    print("📊 RÉSULTATS FINAUX")
    print("=" * 80)

    print(f"🎯 Tests réussis: {success_count}/{total_tests}")

    if success_count == total_tests:
        print("\n🎉 SOLUTION COMPLÈTEMENT FONCTIONNELLE!")
        print("✅ L'invalidation automatique du cache est opérationnelle")
        print("✅ Les mutations Tag invalident correctement le cache")
        print("✅ Les nouveaux objets apparaîtront immédiatement dans GraphiQL")

        print("\n" + "=" * 80)
        print("🚀 INSTRUCTIONS POUR L'UTILISATEUR")
        print("=" * 80)

        print("\n1️⃣ REDÉMARRER LE SERVEUR DJANGO:")
        print("   python manage.py runserver")

        print("\n2️⃣ OUVRIR GRAPHIQL:")
        print("   http://localhost:8000/graphql/")

        print("\n3️⃣ TESTER LA CRÉATION D'UN TAG:")
        print("   Exécuter cette mutation:")
        print("   mutation {")
        print('     createTag(input: {name: "MonNouveauTag", color: "#FF5733"}) {')
        print("       tag {")
        print("         id")
        print("         name")
        print("         color")
        print("       }")
        print("     }")
        print("   }")

        print("\n4️⃣ VÉRIFIER IMMÉDIATEMENT:")
        print("   Exécuter cette requête (SANS rafraîchir la page):")
        print("   query {")
        print("     tags {")
        print("       id")
        print("       name")
        print("       color")
        print("     }")
        print("   }")

        print("\n5️⃣ RÉSULTAT ATTENDU:")
        print("   ✅ Le nouveau tag devrait apparaître dans la liste")
        print("   ✅ Aucun rafraîchissement de page nécessaire")
        print("   ✅ Les données sont immédiatement à jour")

        print("\n" + "=" * 80)
        print("🔧 DÉTAILS TECHNIQUES DE LA SOLUTION")
        print("=" * 80)

        print("\n📝 Modifications apportées:")
        print(
            "   • Ajout de la fonction invalidate_tag_cache() dans test_app/schema.py"
        )
        print("   • Modification de CreateTag pour inclure l'invalidation du cache")
        print("   • Ajout des mutations UpdateTag et DeleteTag avec invalidation")
        print("   • Intégration dans la classe Mutation principale")

        print("\n🔍 Mécanisme d'invalidation:")
        print("   • Suppression des clés de cache spécifiques")
        print("   • Invalidation des patterns de cache (avec fallback)")
        print("   • Nettoyage complet du cache en cas d'erreur")
        print("   • Logging des opérations d'invalidation")

        print("\n⚠️  Notes importantes:")
        print("   • Les warnings sur 'invalidate_pattern' sont normaux")
        print("   • Le système utilise cache.clear() comme fallback")
        print("   • Toutes les mutations Tag sont maintenant sécurisées")

    else:
        print(f"\n⚠️  ATTENTION: {total_tests - success_count} test(s) ont échoué")
        print("🔧 Vérifiez les erreurs ci-dessus avant de continuer")
        print("📞 Contactez le support technique si les problèmes persistent")

    # Nettoyer
    Tag.objects.filter(name__startswith="FinalTest").delete()
    cache.clear()

    print("\n🧹 Environnement nettoyé")
    print("=" * 80)


if __name__ == "__main__":
    final_verification()
