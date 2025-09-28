import graphene
from graphene_django import DjangoObjectType
from django.core.cache import cache
from django_graphql_auto.extensions.caching import get_cache_manager
from .models import Category, Tag, Post, Comment
import logging

logger = logging.getLogger(__name__)

# Cache invalidation helper function using django-graphql-auto integrated system
def invalidate_model_cache_integrated(model_instance=None, model_class=None):
    """
    Invalide le cache en utilisant le système intégré de django-graphql-auto.
    
    Args:
        model_instance: Instance du modèle créé/modifié (optionnel)
        model_class: Classe du modèle à invalider (optionnel)
    """
    # Déterminer le modèle et l'instance
    if model_instance:
        model_class = model_instance.__class__
        instance_id = model_instance.pk
        model_name = model_class.__name__.lower()
    elif model_class:
        instance_id = None
        model_name = model_class.__name__.lower()
    else:
        logger.warning("⚠️ Aucun modèle spécifié pour l'invalidation du cache")
        return
    
    logger.info(f"🔄 Invalidation du cache pour le modèle: {model_name} (ID: {instance_id})")
    
    try:
        # Utiliser le gestionnaire de cache intégré de django-graphql-auto
        cache_manager = get_cache_manager()
        
        # Invalider le cache pour ce modèle spécifique
        cache_manager.invalidate_model(model_class, instance_id)
        logger.info(f"✅ Cache invalidé via django-graphql-auto pour {model_name}")
        
        # Fallback: vider tout le cache si nécessaire
        # (le système django-graphql-auto fait déjà cela automatiquement si les patterns ne sont pas supportés)
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'invalidation du cache via django-graphql-auto: {e}")
        # Fallback ultime: vider tout le cache
        try:
            cache.clear()
            logger.info("✅ Cache vidé en fallback")
        except Exception as fallback_error:
            logger.error(f"❌ Erreur lors du fallback de vidage du cache: {fallback_error}")
    
    logger.info(f"🎉 Invalidation du cache terminée pour {model_name}")

# Fonction spécifique pour les tags (rétrocompatibilité)
def invalidate_tag_cache(tag_instance=None):
    """
    Invalide le cache lié aux tags en utilisant le système intégré.
    
    Args:
        tag_instance: Instance du tag créé/modifié (optionnel)
    """
    invalidate_model_cache_integrated(model_instance=tag_instance, model_class=Tag)

# Define GraphQL types for our models
class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = "__all__"

class TagType(DjangoObjectType):
    class Meta:
        model = Tag
        fields = "__all__"

class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = "__all__"

class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = "__all__"

# Define Query class
class Query(graphene.ObjectType):
    # Single object queries
    category = graphene.Field(CategoryType, id=graphene.ID())
    tag = graphene.Field(TagType, id=graphene.ID())
    post = graphene.Field(PostType, id=graphene.ID())
    comment = graphene.Field(CommentType, id=graphene.ID())
    
    # List queries
    categories = graphene.List(CategoryType)
    tags = graphene.List(TagType)
    posts = graphene.List(PostType)
    comments = graphene.List(CommentType)
    
    def resolve_category(self, info, id):
        try:
            return Category.objects.get(pk=id)
        except Category.DoesNotExist:
            return None
    
    def resolve_tag(self, info, id):
        try:
            return Tag.objects.get(pk=id)
        except Tag.DoesNotExist:
            return None
    
    def resolve_post(self, info, id):
        try:
            return Post.objects.get(pk=id)
        except Post.DoesNotExist:
            return None
    
    def resolve_comment(self, info, id):
        try:
            return Comment.objects.get(pk=id)
        except Comment.DoesNotExist:
            return None
    
    def resolve_categories(self, info):
        return Category.objects.all()
    
    def resolve_tags(self, info):
        return Tag.objects.all()
    
    def resolve_posts(self, info):
        return Post.objects.all()
    
    def resolve_comments(self, info):
        return Comment.objects.all()

# Define input types for mutations
class CategoryInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    description = graphene.String()

class TagInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    color = graphene.String()

class PostInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    content = graphene.String(required=True)
    category_id = graphene.ID()
    tag_ids = graphene.List(graphene.ID)
    status = graphene.String()

class CommentInput(graphene.InputObjectType):
    content = graphene.String(required=True)
    post_id = graphene.ID(required=True)
    author_name = graphene.String(required=True)
    author_email = graphene.String(required=True)

# Define mutations
class CreateCategory(graphene.Mutation):
    class Arguments:
        input = CategoryInput(required=True)
    
    category = graphene.Field(CategoryType)
    
    def mutate(self, info, input):
        category = Category.objects.create(**input)
        
        # Invalider le cache pour les catégories
        invalidate_model_cache_integrated(model_instance=category)
        
        return CreateCategory(category=category)

class CreateTag(graphene.Mutation):
    class Arguments:
        input = TagInput(required=True)
    
    tag = graphene.Field(TagType)
    
    def mutate(self, info, input):
        tag = Tag.objects.create(**input)
        
        # SOLUTION: Invalider le cache automatiquement après création
        invalidate_tag_cache(tag)
        logger.info(f"Tag créé et cache invalidé: {tag.name} (ID: {tag.pk})")
        
        return CreateTag(tag=tag)

class UpdateTag(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = TagInput(required=True)
    
    tag = graphene.Field(TagType)
    
    def mutate(self, info, id, input):
        try:
            tag = Tag.objects.get(pk=id)
            
            # Sauvegarder l'ancienne couleur pour l'invalidation
            old_color = tag.color
            
            # Mettre à jour les champs
            if hasattr(input, 'name') and input.name:
                tag.name = input.name
            if hasattr(input, 'color') and input.color:
                tag.color = input.color
            
            tag.save()
            
            # Invalider le cache avec la fonction intégrée
            invalidate_model_cache_integrated(model_instance=tag)
            if old_color != tag.color:
                cache.delete(f"graphql_tags_by_color_{old_color}")
                logger.info(f"Cache invalidé pour ancienne couleur: {old_color}")
            
            logger.info(f"Tag mis à jour et cache invalidé: {tag.name} (ID: {tag.pk})")
            
            return UpdateTag(tag=tag)
        except Tag.DoesNotExist:
            return UpdateTag(tag=None)

class DeleteTag(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    
    def mutate(self, info, id):
        try:
            tag = Tag.objects.get(pk=id)
            tag_name = tag.name
            tag_pk = tag.pk
            
            # Invalider le cache avec la fonction intégrée avant suppression
            invalidate_model_cache_integrated(model_instance=tag)
            
            tag.delete()
            
            logger.info(f"Tag supprimé et cache invalidé: {tag_name} (ID: {tag_pk})")
            
            return DeleteTag(success=True)
        except Tag.DoesNotExist:
            return DeleteTag(success=False)

class CreatePost(graphene.Mutation):
    class Arguments:
        input = PostInput(required=True)
    
    post = graphene.Field(PostType)
    
    def mutate(self, info, input):
        tag_ids = input.pop('tag_ids', [])
        post = Post.objects.create(**input)
        if tag_ids:
            post.tags.set(tag_ids)
        
        # Invalider le cache pour les posts
        invalidate_model_cache_integrated(model_instance=post)
        
        return CreatePost(post=post)

class CreateComment(graphene.Mutation):
    class Arguments:
        input = CommentInput(required=True)
    
    comment = graphene.Field(CommentType)
    
    def mutate(self, info, input):
        comment = Comment.objects.create(**input)
        
        # Invalider le cache pour les commentaires
        invalidate_model_cache_integrated(model_instance=comment)
        
        return CreateComment(comment=comment)

# Define Mutation class
class Mutation(graphene.ObjectType):
    create_category = CreateCategory.Field()
    create_tag = CreateTag.Field()
    update_tag = UpdateTag.Field()
    delete_tag = DeleteTag.Field()
    create_post = CreatePost.Field()
    create_comment = CreateComment.Field()

# Create schema
test_app_schema = graphene.Schema(query=Query, mutation=Mutation)