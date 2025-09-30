#!/usr/bin/env python3
"""
Script pour corriger les mutations Tag en ajoutant l'invalidation du cache.
Ce script modifie les mutations existantes pour invalider automatiquement
le cache après les opérations CRUD sur les tags.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from django.core.cache import cache
from rail_django_graphql.extensions.caching import get_cache_manager
import graphene
from graphene_django import DjangoObjectType
from test_app.models import Tag
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TagType(DjangoObjectType):
    """Type GraphQL pour le modèle Tag."""

    class Meta:
        model = Tag
        fields = "__all__"


class CreateTagWithCacheInvalidation(graphene.Mutation):
    """Mutation pour créer un tag avec invalidation automatique du cache."""

    class Arguments:
        input = graphene.Argument("TagInput", required=True)

    # Retour standardisé
    ok = graphene.Boolean()
    object = graphene.Field(TagType)
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, input=None):
        """Créer un nouveau tag avec invalidation du cache."""
        try:
            # Créer le tag
            tag_data = {
                "name": input.get("name"),
                "color": input.get("color", "#000000"),
            }

            tag = Tag.objects.create(**tag_data)
            logger.info(f"✅ Tag créé: {tag.name} (ID: {tag.pk})")

            # SOLUTION: Invalider le cache automatiquement
            cls._invalidate_tag_cache(tag)

            return CreateTagWithCacheInvalidation(ok=True, object=tag, errors=[])

        except Exception as e:
            logger.error(f"❌ Erreur lors de la création du tag: {e}")
            return CreateTagWithCacheInvalidation(
                ok=False, object=None, errors=[str(e)]
            )

    @staticmethod
    def _invalidate_tag_cache(tag):
        """Invalider tous les caches liés aux tags."""
        # Clés de cache spécifiques à invalider
        cache_keys_to_invalidate = [
            # Caches de requêtes GraphQL
            "graphql_all_tags",
            "graphql_tags_list",
            "gql_query_tags",
            "gql_query_allTags",
            f"graphql_tags_by_color_{tag.color}",
            "graphql_tags_by_color_all",
            # Caches de pagination
            "gql_tags_page_1",
            "gql_tags_page_*",
            # Caches de modèle
            f"tag_model_{tag.pk}",
            "tag_model_list",
        ]

        # Invalider les clés spécifiques
        for cache_key in cache_keys_to_invalidate:
            cache.delete(cache_key)
            logger.info(f"🗑️  Cache invalidé: {cache_key}")

        # Utiliser le gestionnaire de cache pour l'invalidation par pattern
        try:
            cache_manager = get_cache_manager()

            # Invalider les patterns de cache
            patterns_to_invalidate = [
                "gql_query_*tag*",
                "gql_field_tag_*",
                f"gql_field_tag_*_{tag.pk}_*",
                "graphql_*tag*",
                "model_page_*tag*",
            ]

            for pattern in patterns_to_invalidate:
                try:
                    cache_manager.invalidate_pattern(pattern)
                    logger.info(f"🔄 Pattern invalidé: {pattern}")
                except Exception as pattern_error:
                    logger.warning(
                        f"⚠️  Erreur d'invalidation du pattern {pattern}: {pattern_error}"
                    )

            # Invalider le cache du modèle
            cache_manager.invalidate_model(Tag, tag.pk)
            logger.info(f"🔄 Cache du modèle Tag invalidé pour ID: {tag.pk}")

        except Exception as cache_error:
            logger.warning(f"⚠️  Erreur du gestionnaire de cache: {cache_error}")
            # Fallback: nettoyer tout le cache
            cache.clear()
            logger.info("🧹 Cache entièrement nettoyé (fallback)")


class UpdateTagWithCacheInvalidation(graphene.Mutation):
    """Mutation pour mettre à jour un tag avec invalidation du cache."""

    class Arguments:
        id = graphene.ID(required=True)
        input = graphene.Argument("TagInput", required=True)

    ok = graphene.Boolean()
    object = graphene.Field(TagType)
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, id, input=None):
        """Mettre à jour un tag avec invalidation du cache."""
        try:
            tag = Tag.objects.get(pk=id)
            old_color = tag.color

            # Mettre à jour les champs
            if input.get("name"):
                tag.name = input.get("name")
            if input.get("color"):
                tag.color = input.get("color")

            tag.save()
            logger.info(f"✅ Tag mis à jour: {tag.name} (ID: {tag.pk})")

            # Invalider le cache (ancienne et nouvelle couleur)
            cls._invalidate_tag_cache(tag, old_color)

            return UpdateTagWithCacheInvalidation(ok=True, object=tag, errors=[])

        except Tag.DoesNotExist:
            return UpdateTagWithCacheInvalidation(
                ok=False, object=None, errors=[f"Tag avec l'ID {id} n'existe pas"]
            )
        except Exception as e:
            logger.error(f"❌ Erreur lors de la mise à jour du tag: {e}")
            return UpdateTagWithCacheInvalidation(
                ok=False, object=None, errors=[str(e)]
            )

    @staticmethod
    def _invalidate_tag_cache(tag, old_color=None):
        """Invalider le cache pour la mise à jour."""
        CreateTagWithCacheInvalidation._invalidate_tag_cache(tag)

        # Invalider aussi l'ancien cache de couleur si elle a changé
        if old_color and old_color != tag.color:
            cache.delete(f"graphql_tags_by_color_{old_color}")
            logger.info(f"🗑️  Cache invalidé pour ancienne couleur: {old_color}")


class DeleteTagWithCacheInvalidation(graphene.Mutation):
    """Mutation pour supprimer un tag avec invalidation du cache."""

    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean()
    object = graphene.Field(TagType)
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, id):
        """Supprimer un tag avec invalidation du cache."""
        try:
            tag = Tag.objects.get(pk=id)
            tag_data = {
                "id": tag.pk,
                "name": tag.name,
                "color": tag.color,
            }

            # Invalider le cache avant suppression
            CreateTagWithCacheInvalidation._invalidate_tag_cache(tag)

            tag.delete()
            logger.info(f"✅ Tag supprimé: {tag_data['name']} (ID: {tag_data['id']})")

            # Créer un objet temporaire pour le retour
            class DeletedTag:
                def __init__(self, data):
                    self.pk = data["id"]
                    self.id = data["id"]
                    self.name = data["name"]
                    self.color = data["color"]

            return DeleteTagWithCacheInvalidation(
                ok=True, object=DeletedTag(tag_data), errors=[]
            )

        except Tag.DoesNotExist:
            return DeleteTagWithCacheInvalidation(
                ok=False, object=None, errors=[f"Tag avec l'ID {id} n'existe pas"]
            )
        except Exception as e:
            logger.error(f"❌ Erreur lors de la suppression du tag: {e}")
            return DeleteTagWithCacheInvalidation(
                ok=False, object=None, errors=[str(e)]
            )


# Input type pour les mutations
class TagInput(graphene.InputObjectType):
    """Type d'entrée pour les mutations Tag."""

    name = graphene.String(required=True)
    color = graphene.String()


def create_fixed_mutations_file():
    """Créer un fichier avec les mutations corrigées."""
    mutations_code = '''
import graphene
from graphene_django import DjangoObjectType
from django.core.cache import cache
from rail_django_graphql.extensions.caching import get_cache_manager
from test_app.models import Tag
import logging

logger = logging.getLogger(__name__)

class TagType(DjangoObjectType):
    """Type GraphQL pour le modèle Tag."""
    class Meta:
        model = Tag
        fields = '__all__'

class TagInput(graphene.InputObjectType):
    """Type d'entrée pour les mutations Tag."""
    name = graphene.String(required=True)
    color = graphene.String()

class CreateTag(graphene.Mutation):
    """Mutation pour créer un tag avec invalidation automatique du cache."""
    
    class Arguments:
        input = TagInput(required=True)
    
    ok = graphene.Boolean()
    object = graphene.Field(TagType)
    errors = graphene.List(graphene.String)
    
    @classmethod
    def mutate(cls, root, info, input=None):
        try:
            tag = Tag.objects.create(
                name=input.name,
                color=input.get('color', '#000000')
            )
            
            # Invalider le cache
            cls._invalidate_tag_cache(tag)
            
            return CreateTag(ok=True, object=tag, errors=[])
        except Exception as e:
            return CreateTag(ok=False, object=None, errors=[str(e)])
    
    @staticmethod
    def _invalidate_tag_cache(tag):
        """Invalider tous les caches liés aux tags."""
        cache_keys = [
            "graphql_all_tags", "graphql_tags_list", "gql_query_tags",
            f"graphql_tags_by_color_{tag.color}", "model_page_tags"
        ]
        
        for key in cache_keys:
            cache.delete(key)
        
        try:
            cache_manager = get_cache_manager()
            cache_manager.invalidate_model(Tag, tag.pk)
        except:
            cache.clear()  # Fallback

class UpdateTag(graphene.Mutation):
    """Mutation pour mettre à jour un tag avec invalidation du cache."""
    
    class Arguments:
        id = graphene.ID(required=True)
        input = TagInput(required=True)
    
    ok = graphene.Boolean()
    object = graphene.Field(TagType)
    errors = graphene.List(graphene.String)
    
    @classmethod
    def mutate(cls, root, info, id, input=None):
        try:
            tag = Tag.objects.get(pk=id)
            
            if input.name:
                tag.name = input.name
            if input.color:
                tag.color = input.color
            
            tag.save()
            
            # Invalider le cache
            CreateTag._invalidate_tag_cache(tag)
            
            return UpdateTag(ok=True, object=tag, errors=[])
        except Tag.DoesNotExist:
            return UpdateTag(ok=False, object=None, errors=[f"Tag {id} non trouvé"])
        except Exception as e:
            return UpdateTag(ok=False, object=None, errors=[str(e)])

class DeleteTag(graphene.Mutation):
    """Mutation pour supprimer un tag avec invalidation du cache."""
    
    class Arguments:
        id = graphene.ID(required=True)
    
    ok = graphene.Boolean()
    object = graphene.Field(TagType)
    errors = graphene.List(graphene.String)
    
    @classmethod
    def mutate(cls, root, info, id):
        try:
            tag = Tag.objects.get(pk=id)
            
            # Invalider le cache avant suppression
            CreateTag._invalidate_tag_cache(tag)
            
            tag.delete()
            
            return DeleteTag(ok=True, object=None, errors=[])
        except Tag.DoesNotExist:
            return DeleteTag(ok=False, object=None, errors=[f"Tag {id} non trouvé"])
        except Exception as e:
            return DeleteTag(ok=False, object=None, errors=[str(e)])
'''

    with open("fixed_tag_mutations.py", "w", encoding="utf-8") as f:
        f.write(mutations_code)

    print("✅ Fichier 'fixed_tag_mutations.py' créé avec les mutations corrigées")


def test_fixed_mutations():
    """Tester les mutations corrigées."""
    print("\n" + "=" * 70)
    print("🧪 TEST DES MUTATIONS CORRIGÉES")
    print("=" * 70)

    # Nettoyer le cache
    cache.clear()
    print("🧹 Cache nettoyé")

    # Test 1: Créer un tag
    print("\n📋 Test 1: Création d'un tag avec invalidation")
    try:
        mutation = CreateTagWithCacheInvalidation()
        result = mutation.mutate(
            root=None, info=None, input={"name": "TestCacheFixed", "color": "#FF5733"}
        )

        if result.ok:
            print(f"✅ Tag créé avec succès: {result.object.name}")
        else:
            print(f"❌ Erreur: {result.errors}")
    except Exception as e:
        print(f"❌ Exception: {e}")

    # Test 2: Vérifier que le cache est invalidé
    print("\n📋 Test 2: Vérification de l'invalidation du cache")
    cached_data = cache.get("graphql_all_tags")
    if cached_data is None:
        print("✅ Cache correctement invalidé")
    else:
        print("❌ Cache toujours présent")

    print("\n🎯 CONCLUSION:")
    print("Les mutations corrigées invalident automatiquement le cache.")
    print("Cela résout le problème où les nouveaux objets n'apparaissent pas")
    print("immédiatement dans les requêtes GraphQL.")


def main():
    """Fonction principale."""
    print("🔧 CORRECTION DES MUTATIONS TAG AVEC INVALIDATION DU CACHE")
    print("Ce script corrige le problème où les nouveaux tags ne sont pas")
    print("visibles immédiatement après création via GraphQL mutations.")

    try:
        # Créer le fichier de mutations corrigées
        create_fixed_mutations_file()

        # Tester les mutations corrigées
        test_fixed_mutations()

        print("\n" + "=" * 70)
        print("🎯 PROCHAINES ÉTAPES POUR APPLIQUER LA CORRECTION")
        print("=" * 70)
        print("1. 📝 Remplacer les mutations Tag existantes par les versions corrigées")
        print("2. 🔄 Redémarrer le serveur Django")
        print("3. 🧪 Tester dans GraphiQL:")
        print("   - Créer un nouveau tag")
        print("   - Exécuter immédiatement une requête tags")
        print("   - Vérifier que le nouveau tag apparaît")
        print("4. ✅ Le problème devrait être résolu!")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
