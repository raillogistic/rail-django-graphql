
import graphene
from graphene_django import DjangoObjectType
from django.core.cache import cache
from django_graphql_auto.extensions.caching import get_cache_manager
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
