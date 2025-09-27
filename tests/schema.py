"""
Schéma GraphQL pour les tests.

Ce module configure:
- Schéma GraphQL complet pour les tests
- Types de test
- Requêtes et mutations de test
- Configuration du schéma automatique
"""

import graphene
from graphene import ObjectType, Schema
from graphene_django import DjangoObjectType

from django_graphql_auto.core.schema import SchemaBuilder
from django_graphql_auto.generators.introspector import ModelIntrospector
from django_graphql_auto.generators.types import TypeGenerator
from django_graphql_auto.generators.queries import QueryGenerator
from django_graphql_auto.generators.mutations import MutationGenerator

from tests.fixtures.test_data_fixtures import (
    FixtureTestAuthor,
    FixtureTestBook,
    FixtureTestCategory,
    FixtureTestReview,
    FixtureTestPublisher
)


# ============================================================================
# TYPES PERSONNALISÉS
# ============================================================================

class BookStatistics(ObjectType):
    """Statistiques des livres."""
    
    total_books = graphene.Int()
    average_rating = graphene.Float()
    total_reviews = graphene.Int()
    recent_books = graphene.Int()
    
    def resolve_total_books(self, info):
        """Résout le nombre total de livres."""
        return FixtureTestBook.objects.count()
    
    def resolve_average_rating(self, info):
        """Résout la note moyenne de tous les livres."""
        from django.db.models import Avg
        result = FixtureTestReview.objects.aggregate(avg_rating=Avg('rating'))
        return result['avg_rating']
    
    def resolve_total_reviews(self, info):
        """Résout le nombre total de critiques."""
        return FixtureTestReview.objects.count()
    
    def resolve_recent_books(self, info):
        """Résout le nombre de livres récents."""
        from datetime import datetime, timedelta
        recent_date = datetime.now().date() - timedelta(days=365)
        return FixtureTestBook.objects.filter(publication_date__gte=recent_date).count()


# ============================================================================
# TYPES GRAPHQL DE TEST
# ============================================================================

class FixtureTestAuthorType(DjangoObjectType):
    """Type GraphQL pour FixtureTestAuthor."""
    
    class Meta:
        model = FixtureTestAuthor
        fields = '__all__'
    
    full_name = graphene.String()
    book_count = graphene.Int()
    
    def resolve_full_name(self, info):
        """Résout le nom complet de l'auteur."""
        return f"{self.first_name} {self.last_name}"
    
    def resolve_book_count(self, info):
        """Résout le nombre de livres de l'auteur."""
        return self.books.count()


class FixtureTestBookType(DjangoObjectType):
    """Type GraphQL pour FixtureTestBook."""
    
    class Meta:
        model = FixtureTestBook
        fields = '__all__'
    
    is_recent = graphene.Boolean()
    average_rating = graphene.Float()
    
    def resolve_is_recent(self, info):
        """Vérifie si le livre est récent."""
        from datetime import datetime, timedelta
        return self.publication_date and \
               self.publication_date > datetime.now().date() - timedelta(days=365)
    
    def resolve_average_rating(self, info):
        """Calcule la note moyenne du livre."""
        reviews = self.reviews.all()
        if not reviews:
            return None
        return sum(review.rating for review in reviews) / len(reviews)


class FixtureTestCategoryType(DjangoObjectType):
    """Type GraphQL pour FixtureTestCategory."""
    
    class Meta:
        model = FixtureTestCategory
        fields = '__all__'
    
    book_count = graphene.Int()
    
    def resolve_book_count(self, info):
        """Résout le nombre de livres dans la catégorie."""
        return self.books.count()


class FixtureTestReviewType(DjangoObjectType):
    """Type GraphQL pour FixtureTestReview."""
    
    class Meta:
        model = FixtureTestReview
        fields = '__all__'
    
    is_positive = graphene.Boolean()
    
    def resolve_is_positive(self, info):
        """Vérifie si la critique est positive."""
        return self.rating >= 4


class FixtureTestPublisherType(DjangoObjectType):
    """Type GraphQL pour FixtureTestPublisher."""
    
    class Meta:
        model = FixtureTestPublisher
        fields = '__all__'
    
    book_count = graphene.Int()
    
    def resolve_book_count(self, info):
        """Résout le nombre de livres de l'éditeur."""
        return self.books.count()


# ============================================================================
# REQUÊTES DE TEST
# ============================================================================

class TestQuery(ObjectType):
    """Requêtes GraphQL de test."""
    
    # Requêtes simples
    test_author = graphene.Field(FixtureTestAuthorType, id=graphene.ID())
    test_authors = graphene.List(FixtureTestAuthorType)
    
    test_book = graphene.Field(FixtureTestBookType, id=graphene.ID())
    test_books = graphene.List(FixtureTestBookType)
    
    test_category = graphene.Field(FixtureTestCategoryType, id=graphene.ID())
    test_categories = graphene.List(FixtureTestCategoryType)
    
    test_review = graphene.Field(FixtureTestReviewType, id=graphene.ID())
    test_reviews = graphene.List(FixtureTestReviewType)
    
    test_publisher = graphene.Field(FixtureTestPublisherType, id=graphene.ID())
    test_publishers = graphene.List(FixtureTestPublisherType)
    
    # Requêtes avec filtres
    books_by_author = graphene.List(FixtureTestBookType, author_id=graphene.ID())
    books_by_category = graphene.List(FixtureTestBookType, category_id=graphene.ID())
    books_by_rating = graphene.List(FixtureTestBookType, min_rating=graphene.Float())
    
    # Requêtes de recherche
    search_books = graphene.List(
        FixtureTestBookType,
        query=graphene.String(),
        limit=graphene.Int(default_value=10)
    )
    
    # Requêtes d'agrégation
    book_statistics = graphene.Field(
        BookStatistics,
        category_id=graphene.ID()
    )
    
    # Résolveurs
    def resolve_test_author(self, info, id):
        """Résout un auteur par ID."""
        try:
            return FixtureTestAuthor.objects.get(pk=id)
        except FixtureTestAuthor.DoesNotExist:
            return None
    
    def resolve_test_authors(self, info):
        """Résout tous les auteurs."""
        return FixtureTestAuthor.objects.all()
    
    def resolve_test_book(self, info, id):
        """Résout un livre par ID."""
        try:
            return FixtureTestBook.objects.get(pk=id)
        except FixtureTestBook.DoesNotExist:
            return None
    
    def resolve_test_books(self, info):
        """Résout tous les livres."""
        return FixtureTestBook.objects.all()
    
    def resolve_test_category(self, info, id):
        """Résout une catégorie par ID."""
        try:
            return FixtureTestCategory.objects.get(pk=id)
        except FixtureTestCategory.DoesNotExist:
            return None
    
    def resolve_test_categories(self, info):
        """Résout toutes les catégories."""
        return FixtureTestCategory.objects.all()
    
    def resolve_test_review(self, info, id):
        """Résout une critique par ID."""
        try:
            return FixtureTestReview.objects.get(pk=id)
        except FixtureTestReview.DoesNotExist:
            return None
    
    def resolve_test_reviews(self, info):
        """Résout toutes les critiques."""
        return FixtureTestReview.objects.all()
    
    def resolve_test_publisher(self, info, id):
        """Résout un éditeur par ID."""
        try:
            return FixtureTestPublisher.objects.get(pk=id)
        except FixtureTestPublisher.DoesNotExist:
            return None
    
    def resolve_test_publishers(self, info):
        """Résout tous les éditeurs."""
        return FixtureTestPublisher.objects.all()
    
    def resolve_books_by_author(self, info, author_id):
        """Résout les livres par auteur."""
        return FixtureTestBook.objects.filter(author_id=author_id)
    
    def resolve_books_by_category(self, info, category_id):
        """Résout les livres par catégorie."""
        return FixtureTestBook.objects.filter(category_id=category_id)
    
    def resolve_books_by_rating(self, info, min_rating):
        """Résout les livres par note minimale."""
        from django.db.models import Avg
        return FixtureTestBook.objects.annotate(
            avg_rating=Avg('reviews__rating')
        ).filter(avg_rating__gte=min_rating)
    
    def resolve_search_books(self, info, query, limit=10):
        """Recherche de livres."""
        from django.db.models import Q
        return FixtureTestBook.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(author__first_name__icontains=query) |
            Q(author__last_name__icontains=query)
        )[:limit]


# ============================================================================
# MUTATIONS DE TEST
# ============================================================================

class CreateFixtureTestAuthor(graphene.Mutation):
    """Mutation pour créer un auteur de test."""
    
    class Arguments:
        first_name = graphene.String(required=True)
        last_name = graphene.String(required=True)
        email = graphene.String()
        bio = graphene.String()
    
    author = graphene.Field(FixtureTestAuthorType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, first_name, last_name, email=None, bio=None):
        """Crée un nouvel auteur."""
        try:
            author = FixtureTestAuthor.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                bio=bio
            )
            return CreateFixtureTestAuthor(
                author=author,
                success=True,
                errors=[]
            )
        except Exception as e:
            return CreateFixtureTestAuthor(
                author=None,
                success=False,
                errors=[str(e)]
            )


class UpdateFixtureTestAuthor(graphene.Mutation):
    """Mutation pour mettre à jour un auteur de test."""
    
    class Arguments:
        id = graphene.ID(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
        email = graphene.String()
        bio = graphene.String()
    
    author = graphene.Field(FixtureTestAuthorType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, id, **kwargs):
        """Met à jour un auteur existant."""
        try:
            author = FixtureTestAuthor.objects.get(pk=id)
            
            for field, value in kwargs.items():
                if value is not None:
                    setattr(author, field, value)
            
            author.save()
            
            return UpdateFixtureTestAuthor(
                author=author,
                success=True,
                errors=[]
            )
        except FixtureTestAuthor.DoesNotExist:
            return UpdateFixtureTestAuthor(
                author=None,
                success=False,
                errors=['Auteur non trouvé']
            )
        except Exception as e:
            return UpdateFixtureTestAuthor(
                author=None,
                success=False,
                errors=[str(e)]
            )


class DeleteFixtureTestAuthor(graphene.Mutation):
    """Mutation pour supprimer un auteur de test."""
    
    class Arguments:
        id = graphene.ID(required=True)
    
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, id):
        """Supprime un auteur."""
        try:
            author = FixtureTestAuthor.objects.get(pk=id)
            author.delete()
            
            return DeleteFixtureTestAuthor(
                success=True,
                errors=[]
            )
        except FixtureTestAuthor.DoesNotExist:
            return DeleteFixtureTestAuthor(
                success=False,
                errors=['Auteur non trouvé']
            )
        except Exception as e:
            return DeleteFixtureTestAuthor(
                success=False,
                errors=[str(e)]
            )


class CreateFixtureTestBook(graphene.Mutation):
    """Mutation pour créer un livre de test."""
    
    class Arguments:
        title = graphene.String(required=True)
        author_id = graphene.ID(required=True)
        category_id = graphene.ID()
        publisher_id = graphene.ID()
        isbn = graphene.String()
        description = graphene.String()
        publication_date = graphene.Date()
        price = graphene.Decimal()
    
    book = graphene.Field(FixtureTestBookType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)
    
    def mutate(self, info, title, author_id, **kwargs):
        """Crée un nouveau livre."""
        try:
            author = FixtureTestAuthor.objects.get(pk=author_id)
            
            # Récupérer les objets liés si fournis
            category = None
            if kwargs.get('category_id'):
                category = FixtureTestCategory.objects.get(pk=kwargs['category_id'])
            
            publisher = None
            if kwargs.get('publisher_id'):
                publisher = FixtureTestPublisher.objects.get(pk=kwargs['publisher_id'])
            
            book = FixtureTestBook.objects.create(
                title=title,
                author=author,
                category=category,
                publisher=publisher,
                isbn=kwargs.get('isbn'),
                description=kwargs.get('description'),
                publication_date=kwargs.get('publication_date'),
                price=kwargs.get('price')
            )
            
            return CreateFixtureTestBook(
                book=book,
                success=True,
                errors=[]
            )
        except Exception as e:
            return CreateFixtureTestBook(
                book=None,
                success=False,
                errors=[str(e)]
            )


class TestMutation(ObjectType):
    """Mutations GraphQL de test."""
    
    create_test_author = CreateFixtureTestAuthor.Field()
    update_test_author = UpdateFixtureTestAuthor.Field()
    delete_test_author = DeleteFixtureTestAuthor.Field()
    create_test_book = CreateFixtureTestBook.Field()


# ============================================================================
# SCHÉMA PRINCIPAL
# ============================================================================

# Schéma de test manuel
test_schema = Schema(
    query=TestQuery,
    mutation=TestMutation
)

# Schéma automatique (utilise le générateur automatique)
try:
    auto_schema_generator = SchemaBuilder()
    auto_schema = auto_schema_generator.build_schema()
except Exception as e:
    # Fallback vers le schéma de test si le schéma automatique échoue
    print(f"Erreur lors de la génération du schéma automatique: {e}")
    auto_schema = test_schema

# Schéma principal utilisé par les tests
schema = auto_schema


# ============================================================================
# UTILITAIRES DE SCHÉMA
# ============================================================================

def get_test_schema():
    """Retourne le schéma de test."""
    return test_schema


def get_auto_schema():
    """Retourne le schéma automatique."""
    return auto_schema


def validate_schema(schema_to_validate=None):
    """Valide un schéma GraphQL."""
    if schema_to_validate is None:
        schema_to_validate = schema
    
    try:
        # Tenter une requête d'introspection
        introspection_query = """
        query IntrospectionQuery {
            __schema {
                types {
                    name
                    kind
                }
            }
        }
        """
        
        from graphene.test import Client
        client = Client(schema_to_validate)
        result = client.execute(introspection_query)
        
        if result.errors:
            return False, result.errors
        
        return True, None
    
    except Exception as e:
        return False, [str(e)]


def get_schema_types():
    """Retourne les types du schéma."""
    return {
        'FixtureTestAuthor': FixtureTestAuthorType,
        'FixtureTestBook': FixtureTestBookType,
        'FixtureTestCategory': FixtureTestCategoryType,
        'FixtureTestReview': FixtureTestReviewType,
        'FixtureTestPublisher': FixtureTestPublisherType,
        'BookStatistics': BookStatistics,
    }


def get_schema_queries():
    """Retourne les requêtes du schéma."""
    return TestQuery


def get_schema_mutations():
    """Retourne les mutations du schéma."""
    return TestMutation
