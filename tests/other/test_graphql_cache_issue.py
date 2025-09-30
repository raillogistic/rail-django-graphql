#!/usr/bin/env python3
"""
Test script pour démontrer et résoudre le problème de cache GraphQL.
Ce script simule le problème où les nouveaux objets créés via mutation
ne sont pas visibles dans les requêtes jusqu'au rafraîchissement de la page.
"""

import os
import sys
import django
import json
import time

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from test_app.models import Tag
from rail_django_graphql.extensions.caching import get_cache_manager
from django.core.cache import cache
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Définir les types GraphQL pour les tests
class TagType(DjangoObjectType):
    class Meta:
        model = Tag
        fields = "__all__"


class Query(graphene.ObjectType):
    """Requêtes GraphQL pour les tests."""

    all_tags = graphene.List(TagType)
    tags_by_color = graphene.List(TagType, color=graphene.String())

    def resolve_all_tags(self, info):
        """Résoudre la requête all_tags avec cache."""
        cache_key = "graphql_all_tags"

        # Vérifier le cache
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"🔄 Résultat depuis le cache: {len(cached_result)} tags")
            return cached_result

        # Requête à la base de données
        tags = list(Tag.objects.all())
        logger.info(f"🗄️  Requête à la DB: {len(tags)} tags trouvés")

        # Mettre en cache pour 5 minutes
        cache.set(cache_key, tags, 300)
        logger.info(f"💾 Résultat mis en cache")

        return tags

    def resolve_tags_by_color(self, info, color=None):
        """Résoudre la requête tags_by_color avec cache."""
        cache_key = f"graphql_tags_by_color_{color or 'all'}"

        # Vérifier le cache
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(
                f"🔄 Tags par couleur depuis le cache: {len(cached_result)} tags"
            )
            return cached_result

        # Requête à la base de données
        if color:
            tags = list(Tag.objects.filter(color=color))
        else:
            tags = list(Tag.objects.all())

        logger.info(f"🗄️  Tags par couleur depuis la DB: {len(tags)} tags")

        # Mettre en cache
        cache.set(cache_key, tags, 300)
        logger.info(f"💾 Tags par couleur mis en cache")

        return tags


class CreateTag(graphene.Mutation):
    """Mutation pour créer un tag."""

    class Arguments:
        name = graphene.String(required=True)
        color = graphene.String(required=True)

    tag = graphene.Field(TagType)
    success = graphene.Boolean()

    def mutate(self, info, name, color):
        """Créer un nouveau tag."""
        try:
            # Créer le tag
            tag = Tag.objects.create(name=name, color=color)
            logger.info(f"✅ Tag créé: {tag.name} (ID: {tag.pk})")

            # PROBLÈME: Le cache n'est pas invalidé automatiquement ici
            # Les requêtes suivantes retourneront les anciennes données du cache

            return CreateTag(tag=tag, success=True)
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création du tag: {e}")
            return CreateTag(tag=None, success=False)


class CreateTagWithCacheInvalidation(graphene.Mutation):
    """Mutation pour créer un tag avec invalidation du cache."""

    class Arguments:
        name = graphene.String(required=True)
        color = graphene.String(required=True)

    tag = graphene.Field(TagType)
    success = graphene.Boolean()

    def mutate(self, info, name, color):
        """Créer un nouveau tag avec invalidation du cache."""
        try:
            # Créer le tag
            tag = Tag.objects.create(name=name, color=color)
            logger.info(f"✅ Tag créé avec invalidation: {tag.name} (ID: {tag.pk})")

            # SOLUTION: Invalider le cache manuellement
            cache_keys_to_invalidate = [
                "graphql_all_tags",
                "graphql_tags_by_color_all",
                f"graphql_tags_by_color_{color}",
            ]

            for cache_key in cache_keys_to_invalidate:
                cache.delete(cache_key)
                logger.info(f"🗑️  Cache invalidé: {cache_key}")

            # Utiliser le gestionnaire de cache si disponible
            try:
                cache_manager = get_cache_manager()
                cache_manager.invalidate_model(Tag, tag.pk)
                logger.info(
                    f"🔄 Cache invalidé via le gestionnaire pour Tag ID: {tag.pk}"
                )
            except Exception as cache_error:
                logger.warning(
                    f"⚠️  Erreur d'invalidation du cache manager: {cache_error}"
                )

            return CreateTagWithCacheInvalidation(tag=tag, success=True)
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création du tag: {e}")
            return CreateTagWithCacheInvalidation(tag=None, success=False)


class Mutation(graphene.ObjectType):
    """Mutations GraphQL pour les tests."""

    create_tag = CreateTag.Field()
    create_tag_with_cache_invalidation = CreateTagWithCacheInvalidation.Field()


# Schéma GraphQL pour les tests
test_schema = graphene.Schema(query=Query, mutation=Mutation)


def demonstrate_cache_issue():
    """Démontre le problème de cache avec les mutations GraphQL."""
    print("\n" + "=" * 70)
    print("🔍 DÉMONSTRATION DU PROBLÈME DE CACHE GRAPHQL")
    print("=" * 70)

    # Nettoyer le cache
    cache.clear()
    print("🧹 Cache nettoyé")

    # 1. Première requête - va en base de données et met en cache
    print("\n📋 Étape 1: Première requête all_tags")
    query1 = """
    query {
        allTags {
            id
            name
            color
        }
    }
    """

    result1 = test_schema.execute(query1)
    tags_before = result1.data["allTags"]
    print(f"   Résultat: {len(tags_before)} tags trouvés")

    # 2. Créer un nouveau tag SANS invalidation du cache
    print("\n📋 Étape 2: Création d'un tag SANS invalidation du cache")
    mutation_without_invalidation = """
    mutation {
        createTag(name: "TestCacheIssue", color: "#FF0000") {
            tag {
                id
                name
                color
            }
            success
        }
    }
    """

    result2 = test_schema.execute(mutation_without_invalidation)
    if result2.data["createTag"]["success"]:
        new_tag = result2.data["createTag"]["tag"]
        print(f"   ✅ Tag créé: {new_tag['name']} (ID: {new_tag['id']})")

    # 3. Requête immédiate après création - devrait montrer le problème
    print("\n📋 Étape 3: Requête immédiate après création (problème de cache)")
    result3 = test_schema.execute(query1)
    tags_after_without_invalidation = result3.data["allTags"]
    print(f"   Résultat: {len(tags_after_without_invalidation)} tags trouvés")

    if len(tags_after_without_invalidation) == len(tags_before):
        print("   ❌ PROBLÈME CONFIRMÉ: Le nouveau tag n'apparaît pas!")
        print("   🔄 Les données viennent du cache, pas de la base de données")
    else:
        print("   ✅ Le nouveau tag apparaît (cache non utilisé)")

    # 4. Vérification directe en base de données
    print("\n📋 Étape 4: Vérification directe en base de données")
    db_count = Tag.objects.count()
    print(f"   Nombre de tags en DB: {db_count}")

    # 5. Créer un autre tag AVEC invalidation du cache
    print("\n📋 Étape 5: Création d'un tag AVEC invalidation du cache")
    mutation_with_invalidation = """
    mutation {
        createTagWithCacheInvalidation(name: "TestCacheFixed", color: "#00FF00") {
            tag {
                id
                name
                color
            }
            success
        }
    }
    """

    result5 = test_schema.execute(mutation_with_invalidation)
    if result5.data["createTagWithCacheInvalidation"]["success"]:
        new_tag2 = result5.data["createTagWithCacheInvalidation"]["tag"]
        print(
            f"   ✅ Tag créé avec invalidation: {new_tag2['name']} (ID: {new_tag2['id']})"
        )

    # 6. Requête après création avec invalidation
    print("\n📋 Étape 6: Requête après création avec invalidation")
    result6 = test_schema.execute(query1)
    tags_after_with_invalidation = result6.data["allTags"]
    print(f"   Résultat: {len(tags_after_with_invalidation)} tags trouvés")

    if len(tags_after_with_invalidation) > len(tags_before):
        print("   ✅ SOLUTION CONFIRMÉE: Les nouveaux tags apparaissent!")
        print("   🔄 Le cache a été invalidé et les données viennent de la DB")

    # Résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DU PROBLÈME ET DE LA SOLUTION")
    print("=" * 70)
    print(f"Tags initiaux: {len(tags_before)}")
    print(
        f"Tags après création sans invalidation: {len(tags_after_without_invalidation)}"
    )
    print(f"Tags après création avec invalidation: {len(tags_after_with_invalidation)}")
    print(f"Tags réels en base de données: {db_count}")

    print("\n🔍 ANALYSE:")
    if len(tags_after_without_invalidation) == len(tags_before):
        print("❌ PROBLÈME CONFIRMÉ: Le cache empêche de voir les nouveaux objets")
        print(
            "   → Les mutations ne déclenchent pas l'invalidation automatique du cache"
        )
        print("   → Les requêtes suivantes retournent les anciennes données du cache")

    if len(tags_after_with_invalidation) > len(tags_before):
        print("✅ SOLUTION CONFIRMÉE: L'invalidation manuelle du cache fonctionne")
        print("   → Invalider le cache après les mutations résout le problème")
        print("   → Les requêtes suivantes vont chercher les nouvelles données en DB")


def test_automatic_cache_invalidation():
    """Test l'invalidation automatique du cache via les signaux Django."""
    print("\n" + "=" * 70)
    print("🔧 TEST DE L'INVALIDATION AUTOMATIQUE DU CACHE")
    print("=" * 70)

    # Nettoyer le cache
    cache.clear()
    print("🧹 Cache nettoyé")

    # Ajouter des données au cache
    cache.set("graphql_all_tags", ["cached_data"], 300)
    cache.set("gql_query_tags_list", ["cached_query"], 300)
    print("💾 Données de test ajoutées au cache")

    # Créer un tag directement (devrait déclencher les signaux)
    print("\n📋 Création d'un tag via Django ORM (signaux automatiques)")
    tag = Tag.objects.create(name="AutoInvalidationTest", color="#0000FF")
    print(f"✅ Tag créé: {tag.name} (ID: {tag.pk})")

    # Vérifier si le cache a été invalidé
    time.sleep(0.1)  # Attendre que les signaux soient traités

    cached_data = cache.get("graphql_all_tags")
    cached_query = cache.get("gql_query_tags_list")

    print("\n🔍 Vérification de l'invalidation automatique:")
    if cached_data is None:
        print("✅ Cache 'graphql_all_tags' invalidé automatiquement")
    else:
        print("❌ Cache 'graphql_all_tags' toujours présent")

    if cached_query is None:
        print("✅ Cache 'gql_query_tags_list' invalidé automatiquement")
    else:
        print("❌ Cache 'gql_query_tags_list' toujours présent")

    # Nettoyer
    tag.delete()
    print(f"🗑️  Tag de test supprimé")


def main():
    """Fonction principale."""
    print("🚀 DIAGNOSTIC DU PROBLÈME DE CACHE GRAPHQL")
    print("Ce script démontre pourquoi les nouveaux objets n'apparaissent pas")
    print("immédiatement après les mutations GraphQL")

    try:
        # Démontrer le problème
        demonstrate_cache_issue()

        # Tester l'invalidation automatique
        test_automatic_cache_invalidation()

        print("\n" + "=" * 70)
        print("🎯 CONCLUSION ET RECOMMANDATIONS")
        print("=" * 70)
        print("Le problème que vous rencontrez est dû au cache GraphQL qui n'est pas")
        print("invalidé automatiquement après les mutations.")
        print()
        print("💡 SOLUTIONS:")
        print("1. ✅ Invalider manuellement le cache dans les mutations")
        print("2. ✅ Configurer l'invalidation automatique via les signaux Django")
        print("3. ✅ Utiliser le gestionnaire de cache intégré")
        print("4. ⚙️  Configurer des patterns d'invalidation spécifiques")
        print()
        print("🔧 PROCHAINES ÉTAPES:")
        print("1. Redémarrer le serveur Django pour appliquer les signaux")
        print("2. Tester les mutations dans GraphiQL")
        print("3. Vérifier que les nouveaux objets apparaissent immédiatement")

    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
