"""
Fixtures de données de test pour les tests GraphQL.

Ce module fournit:
- Des fixtures de données réutilisables
- Des générateurs de données de test
- Des modèles de test standardisés
- Des données complexes pour les tests d'intégration
"""

import pytest
import factory
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory, LazyAttribute, Sequence
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Type
import random
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.db import models

from django_graphql_auto.decorators import business_logic

# Import models from tests.models to avoid conflicts during pytest collection
from tests.models import (
    BaseTestModel,
    FixtureTestAuthor,
    FixtureTestCategory,
    FixtureTestBook,
    FixtureTestReview,
    FixtureTestPublisher
)


# ============================================================================
# FACTORIES POUR LA GÉNÉRATION DE DONNÉES
# ============================================================================

class FixtureTestAuthorFactory(DjangoModelFactory):
    """Factory pour créer des auteurs de test."""
    
    class Meta:
        model = FixtureTestAuthor
    
    first_name = Faker('first_name', locale='fr_FR')
    last_name = Faker('last_name', locale='fr_FR')
    email = Faker('email')
    birth_date = Faker('date_between', start_date='-80y', end_date='-20y')
    biography = Faker('text', max_nb_chars=500)
    nationality = Faker('country', locale='fr_FR')
    website = Faker('url')


class FixtureTestCategoryFactory(DjangoModelFactory):
    """Factory pour créer des catégories de test."""
    
    class Meta:
        model = FixtureTestCategory
    
    name = Faker('word')
    description = Faker('text', max_nb_chars=200)
    slug = Faker('slug')


class FixtureTestPublisherFactory(DjangoModelFactory):
    """Factory pour créer des éditeurs de test."""
    
    class Meta:
        model = FixtureTestPublisher
    
    name = Faker('company', locale='fr_FR')
    address = Faker('address', locale='fr_FR')
    website = Faker('url')
    email = Faker('company_email')
    phone = Faker('phone_number', locale='fr_FR')
    founded_year = Faker('random_int', min=1800, max=2020)


class FixtureTestBookFactory(DjangoModelFactory):
    """Factory pour créer des livres de test."""
    
    class Meta:
        model = FixtureTestBook
    
    title = Faker('sentence', nb_words=4)
    author = SubFactory(FixtureTestAuthorFactory)
    publisher = SubFactory(FixtureTestPublisherFactory)
    isbn = Faker('isbn13')
    publication_date = Faker('date_between', start_date='-50y', end_date='today')
    pages = Faker('random_int', min=50, max=1000)
    price = Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    description = Faker('text', max_nb_chars=1000)
    language = Faker('random_element', elements=['fr', 'en', 'es', 'de', 'it'])
    format = Faker('random_element', elements=['paperback', 'hardcover', 'ebook', 'audiobook'])
    stock_quantity = Faker('random_int', min=0, max=100)
    rating = Faker('pydecimal', left_digits=1, right_digits=2, positive=True, max_value=5)


class FixtureTestReviewFactory(DjangoModelFactory):
    """Factory pour créer des avis de test."""
    
    class Meta:
        model = FixtureTestReview
    
    book = SubFactory(FixtureTestBookFactory)
    reviewer_name = Faker('name', locale='fr_FR')
    reviewer_email = Faker('email')
    rating = Faker('random_int', min=1, max=5)
    title = Faker('sentence', nb_words=6)
    content = Faker('text', max_nb_chars=500)
    is_verified = Faker('boolean', chance_of_getting_true=70)
    helpful_votes = Faker('random_int', min=0, max=50)


# ============================================================================
# FIXTURES PYTEST
# ============================================================================

@pytest.fixture
def test_author():
    """Fixture pour un auteur de test."""
    return FixtureTestAuthorFactory()


@pytest.fixture
def test_authors():
    """Fixture pour plusieurs auteurs de test."""
    return FixtureTestAuthorFactory.create_batch(5)


@pytest.fixture
def test_category():
    """Fixture pour une catégorie de test."""
    return FixtureTestCategoryFactory()


@pytest.fixture
def test_categories():
    """Fixture pour plusieurs catégories de test."""
    return FixtureTestCategoryFactory.create_batch(3)


@pytest.fixture
def test_publisher():
    """Fixture pour un éditeur de test."""
    return FixtureTestPublisherFactory()


@pytest.fixture
def test_publishers():
    """Fixture pour plusieurs éditeurs de test."""
    return FixtureTestPublisherFactory.create_batch(3)


@pytest.fixture
def test_book():
    """Fixture pour un livre de test."""
    return FixtureTestBookFactory()


@pytest.fixture
def test_books():
    """Fixture pour plusieurs livres de test."""
    return FixtureTestBookFactory.create_batch(10)


@pytest.fixture
def test_review():
    """Fixture pour un avis de test."""
    return FixtureTestReviewFactory()


@pytest.fixture
def test_reviews():
    """Fixture pour plusieurs avis de test."""
    return FixtureTestReviewFactory.create_batch(20)


@pytest.fixture
def complete_test_data():
    """Fixture pour un jeu de données complet."""
    # Créer des auteurs
    authors = FixtureTestAuthorFactory.create_batch(5)
    
    # Créer des catégories
    categories = FixtureTestCategoryFactory.create_batch(4)
    
    # Créer des éditeurs
    publishers = FixtureTestPublisherFactory.create_batch(3)
    
    # Créer des livres
    books = []
    for i in range(15):
        book = FixtureTestBookFactory(
            author=random.choice(authors),
            publisher=random.choice(publishers)
        )
        # Ajouter des catégories aléatoires
        book.categories.set(random.sample(categories, random.randint(1, 3)))
        books.append(book)
    
    # Créer des avis
    reviews = []
    for book in books:
        num_reviews = random.randint(0, 5)
        for _ in range(num_reviews):
            review = FixtureTestReviewFactory(book=book)
            reviews.append(review)
    
    return {
        'authors': authors,
        'categories': categories,
        'publishers': publishers,
        'books': books,
        'reviews': reviews
    }


# ============================================================================
# FONCTIONS UTILITAIRES POUR CRÉER DES DONNÉES
# ============================================================================

def create_test_models() -> List[Type[models.Model]]:
    """Retourne la liste des modèles de test."""
    return [
        FixtureTestAuthor,
        FixtureTestCategory,
        FixtureTestPublisher,
        FixtureTestBook,
        FixtureTestReview
    ]


def create_sample_data(num_authors: int = 5, num_books: int = 20) -> Dict[str, Any]:
    """Crée un échantillon de données de test."""
    # Créer des auteurs
    authors = FixtureTestAuthorFactory.create_batch(num_authors)
    
    # Créer des catégories
    categories = FixtureTestCategoryFactory.create_batch(6)
    
    # Créer des éditeurs
    publishers = FixtureTestPublisherFactory.create_batch(4)
    
    # Créer des livres
    books = []
    for _ in range(num_books):
        book = FixtureTestBookFactory(
            author=random.choice(authors),
            publisher=random.choice(publishers)
        )
        # Ajouter 1-3 catégories aléatoires
        selected_categories = random.sample(categories, random.randint(1, 3))
        book.categories.set(selected_categories)
        books.append(book)
    
    # Créer des avis (2-5 par livre)
    reviews = []
    for book in books:
        num_reviews = random.randint(2, 5)
        for _ in range(num_reviews):
            review = FixtureTestReviewFactory(book=book)
            reviews.append(review)
    
    return {
        'authors': authors,
        'categories': categories,
        'publishers': publishers,
        'books': books,
        'reviews': reviews,
        'total_objects': len(authors) + len(categories) + len(publishers) + len(books) + len(reviews)
    }


def create_complex_relationships() -> Dict[str, Any]:
    """Crée des données avec des relations complexes."""
    # Créer une hiérarchie de catégories
    parent_categories = FixtureTestCategoryFactory.create_batch(3)
    child_categories = []
    
    for parent in parent_categories:
        children = FixtureTestCategoryFactory.create_batch(2, parent=parent)
        child_categories.extend(children)
    
    all_categories = parent_categories + child_categories
    
    # Créer des auteurs avec différents profils
    prolific_authors = FixtureTestAuthorFactory.create_batch(2)  # Auteurs prolifiques
    regular_authors = FixtureTestAuthorFactory.create_batch(5)   # Auteurs réguliers
    new_authors = FixtureTestAuthorFactory.create_batch(3)       # Nouveaux auteurs
    
    all_authors = prolific_authors + regular_authors + new_authors
    
    # Créer des éditeurs
    publishers = FixtureTestPublisherFactory.create_batch(4)
    
    # Créer des livres avec distribution réaliste
    books = []
    
    # Livres des auteurs prolifiques (5-10 livres chacun)
    for author in prolific_authors:
        num_books = random.randint(5, 10)
        for _ in range(num_books):
            book = FixtureTestBookFactory(
                author=author,
                publisher=random.choice(publishers)
            )
            book.categories.set(random.sample(all_categories, random.randint(1, 2)))
            books.append(book)
    
    # Livres des auteurs réguliers (2-4 livres chacun)
    for author in regular_authors:
        num_books = random.randint(2, 4)
        for _ in range(num_books):
            book = FixtureTestBookFactory(
                author=author,
                publisher=random.choice(publishers)
            )
            book.categories.set(random.sample(all_categories, random.randint(1, 3)))
            books.append(book)
    
    # Livres des nouveaux auteurs (1 livre chacun)
    for author in new_authors:
        book = FixtureTestBookFactory(
            author=author,
            publisher=random.choice(publishers)
        )
        book.categories.set(random.sample(all_categories, random.randint(1, 2)))
        books.append(book)
    
    # Créer des avis avec distribution réaliste
    reviews = []
    for book in books:
        # Les livres populaires ont plus d'avis
        if book.author in prolific_authors:
            num_reviews = random.randint(5, 15)
        elif book.author in regular_authors:
            num_reviews = random.randint(2, 8)
        else:
            num_reviews = random.randint(0, 3)
        
        for _ in range(num_reviews):
            review = FixtureTestReviewFactory(book=book)
            reviews.append(review)
    
    return {
        'parent_categories': parent_categories,
        'child_categories': child_categories,
        'all_categories': all_categories,
        'prolific_authors': prolific_authors,
        'regular_authors': regular_authors,
        'new_authors': new_authors,
        'all_authors': all_authors,
        'publishers': publishers,
        'books': books,
        'reviews': reviews,
        'stats': {
            'total_categories': len(all_categories),
            'total_authors': len(all_authors),
            'total_publishers': len(publishers),
            'total_books': len(books),
            'total_reviews': len(reviews)
        }
    }


def create_performance_data(scale: str = 'medium') -> Dict[str, Any]:
    """Crée des données pour les tests de performance."""
    scales = {
        'small': {'authors': 10, 'books': 50, 'reviews': 200},
        'medium': {'authors': 50, 'books': 200, 'reviews': 1000},
        'large': {'authors': 100, 'books': 500, 'reviews': 2500},
        'xlarge': {'authors': 200, 'books': 1000, 'reviews': 5000}
    }
    
    config = scales.get(scale, scales['medium'])
    
    # Créer les données selon la configuration
    authors = FixtureTestAuthorFactory.create_batch(config['authors'])
    categories = FixtureTestCategoryFactory.create_batch(20)  # Nombre fixe de catégories
    publishers = FixtureTestPublisherFactory.create_batch(10)  # Nombre fixe d'éditeurs
    
    # Créer les livres
    books = []
    for _ in range(config['books']):
        book = FixtureTestBookFactory(
            author=random.choice(authors),
            publisher=random.choice(publishers)
        )
        # Ajouter des catégories
        num_categories = random.randint(1, 4)
        selected_categories = random.sample(categories, num_categories)
        book.categories.set(selected_categories)
        books.append(book)
    
    # Créer les avis
    reviews = []
    reviews_per_book = config['reviews'] // config['books']
    
    for book in books:
        num_reviews = random.randint(
            max(1, reviews_per_book - 2),
            reviews_per_book + 2
        )
        for _ in range(num_reviews):
            review = FixtureTestReviewFactory(book=book)
            reviews.append(review)
    
    return {
        'scale': scale,
        'config': config,
        'authors': authors,
        'categories': categories,
        'publishers': publishers,
        'books': books,
        'reviews': reviews,
        'actual_counts': {
            'authors': len(authors),
            'categories': len(categories),
            'publishers': len(publishers),
            'books': len(books),
            'reviews': len(reviews)
        }
    }


def cleanup_test_data():
    """Nettoie toutes les données de test."""
    models_to_clean = [
        FixtureTestReview,
        FixtureTestBook,
        FixtureTestCategory,
        FixtureTestPublisher,
        FixtureTestAuthor
    ]
    
    for model in models_to_clean:
        model.objects.all().delete()


# ============================================================================
# FIXTURES SPÉCIALISÉES
# ============================================================================

@pytest.fixture
def minimal_test_data():
    """Fixture pour un jeu de données minimal."""
    author = FixtureTestAuthorFactory()
    category = FixtureTestCategoryFactory()
    publisher = FixtureTestPublisherFactory()
    book = FixtureTestBookFactory(author=author, publisher=publisher)
    book.categories.add(category)
    review = FixtureTestReviewFactory(book=book)
    
    return {
        'author': author,
        'category': category,
        'publisher': publisher,
        'book': book,
        'review': review
    }


@pytest.fixture
def hierarchical_categories():
    """Fixture pour des catégories hiérarchiques."""
    # Catégories racines
    fiction = FixtureTestCategoryFactory(name="Fiction", slug="fiction")
    non_fiction = FixtureTestCategoryFactory(name="Non-Fiction", slug="non-fiction")
    
    # Sous-catégories de Fiction
    romance = FixtureTestCategoryFactory(name="Romance", slug="romance", parent=fiction)
    mystery = FixtureTestCategoryFactory(name="Mystère", slug="mystery", parent=fiction)
    sci_fi = FixtureTestCategoryFactory(name="Science-Fiction", slug="sci-fi", parent=fiction)
    
    # Sous-catégories de Non-Fiction
    biography = FixtureTestCategoryFactory(name="Biographie", slug="biography", parent=non_fiction)
    history = FixtureTestCategoryFactory(name="Histoire", slug="history", parent=non_fiction)
    science = FixtureTestCategoryFactory(name="Science", slug="science", parent=non_fiction)
    
    return {
        'roots': [fiction, non_fiction],
        'fiction_children': [romance, mystery, sci_fi],
        'non_fiction_children': [biography, history, science],
        'all': [fiction, non_fiction, romance, mystery, sci_fi, biography, history, science]
    }


@pytest.fixture
def books_with_varied_ratings():
    """Fixture pour des livres avec des notes variées."""
    author = FixtureTestAuthorFactory()
    publisher = FixtureTestPublisherFactory()
    
    # Créer des livres avec différentes notes
    excellent_book = FixtureTestBookFactory(author=author, publisher=publisher, rating=Decimal('4.8'))
    good_book = FixtureTestBookFactory(author=author, publisher=publisher, rating=Decimal('4.2'))
    average_book = FixtureTestBookFactory(author=author, publisher=publisher, rating=Decimal('3.5'))
    poor_book = FixtureTestBookFactory(author=author, publisher=publisher, rating=Decimal('2.1'))
    
    # Créer des avis correspondants
    for book, rating_range in [
        (excellent_book, (4, 5)),
        (good_book, (3, 5)),
        (average_book, (2, 4)),
        (poor_book, (1, 3))
    ]:
        for _ in range(5):
            FixtureTestReviewFactory(
                book=book,
                rating=random.randint(*rating_range)
            )
    
    return {
        'excellent': excellent_book,
        'good': good_book,
        'average': average_book,
        'poor': poor_book,
        'all': [excellent_book, good_book, average_book, poor_book]
    }