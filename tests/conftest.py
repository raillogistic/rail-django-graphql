"""
Configuration pytest pour les tests GraphQL.

Ce module configure:
- Fixtures globales pour les tests
- Configuration de la base de données de test
- Utilitaires de test partagés
- Hooks pytest personnalisés
"""

import pytest
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line
from django.db import transaction
from django.contrib.auth.models import User
from django.core.cache import cache

import graphene
from graphene.test import Client
from graphene_django import DjangoObjectType

# Configuration Django pour les tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')

# Only setup Django if not already configured
if not settings.configured:
    django.setup()

from django_graphql_auto.core.schema import SchemaBuilder
from django_graphql_auto.generators.introspector import ModelIntrospector
from django_graphql_auto.generators.types import TypeGenerator
from django_graphql_auto.generators.queries import QueryGenerator
from django_graphql_auto.generators.mutations import MutationGenerator

from tests.fixtures.test_utilities import (
    GraphQLTestClient,
    DatabaseQueryCounter,
    PerformanceProfiler,
    TestResult,
    PerformanceMetrics
)
from tests.fixtures.test_data_fixtures import (
    create_sample_data,
)
# Note: Model imports removed to prevent conflicts during test collection


# ============================================================================
# CONFIGURATION PYTEST
# ============================================================================

def pytest_configure(config):
    """Configuration pytest au démarrage."""
    # Configurer Django
    if not settings.configured:
        settings.configure()
    
    # Marquer que nous sommes en mode test
    os.environ['TESTING'] = 'true'
    
    # Configurer le logging pour les tests
    import logging
    logging.getLogger('django.db.backends').setLevel(logging.WARNING)


def pytest_unconfigure(config):
    """Nettoyage après les tests."""
    # Nettoyer le cache
    cache.clear()
    
    # Nettoyer les variables d'environnement
    if 'TESTING' in os.environ:
        del os.environ['TESTING']


def pytest_runtest_setup(item):
    """Configuration avant chaque test."""
    # Nettoyer le cache avant chaque test
    cache.clear()


def pytest_runtest_teardown(item, nextitem):
    """Nettoyage après chaque test."""
    # Nettoyer le cache après chaque test
    cache.clear()


# ============================================================================
# FIXTURES DE BASE DE DONNÉES
# ============================================================================

# Django test environment is handled automatically by pytest-django
# No custom django_db_setup fixture needed


@pytest.fixture
def db_transaction():
    """Fixture pour les tests avec transaction de base de données."""
    with transaction.atomic():
        yield


@pytest.fixture
def clean_db(db):
    """Fixture pour nettoyer la base de données."""
    # La fixture 'db' de pytest-django nettoie automatiquement
    yield
    
    # Nettoyage supplémentaire si nécessaire
    from django.contrib.auth.models import User
    User.objects.all().delete()


# ============================================================================
# FIXTURES UTILISATEUR
# ============================================================================

@pytest.fixture
def test_user(db):
    """Crée un utilisateur de test."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def admin_user(db):
    """Crée un utilisateur administrateur de test."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123',
        first_name='Admin',
        last_name='User'
    )


@pytest.fixture
def authenticated_user(test_user):
    """Utilisateur authentifié pour les tests."""
    return test_user


# ============================================================================
# FIXTURES GRAPHQL
# ============================================================================

@pytest.fixture
def graphql_schema():
    """Crée un schéma GraphQL de test."""
    return SchemaBuilder().get_schema()


@pytest.fixture
def graphql_client(graphql_schema):
    """Client GraphQL pour les tests."""
    return GraphQLTestClient(graphql_schema)


@pytest.fixture
def graphene_client(graphql_schema):
    """Client Graphene pour les tests."""
    return Client(graphql_schema)


# ============================================================================
# FIXTURES DE GÉNÉRATEURS
# ============================================================================

@pytest.fixture
def model_introspector():
    """Introspecteur de modèles pour les tests."""
    return ModelIntrospector()


@pytest.fixture
def type_generator():
    """Générateur de types GraphQL pour les tests."""
    return TypeGenerator()


@pytest.fixture
def query_generator():
    """Générateur de requêtes GraphQL pour les tests."""
    return QueryGenerator()


@pytest.fixture
def mutation_generator():
    """Générateur de mutations GraphQL pour les tests."""
    return MutationGenerator()


# ============================================================================
# FIXTURES DE DONNÉES DE TEST
# ============================================================================
from tests.schema import TestMutation
@pytest.fixture
def test_author(db):
    """Crée un auteur de test."""
    return TestMutation.create_test_author()


@pytest.fixture
def test_authors(db):
    """Crée plusieurs auteurs de test."""
    return [TestMutation.create_test_author(name=f"Auteur {i}") for i in range(1, 6)]


@pytest.fixture
def test_category(db):
    """Crée une catégorie de test."""
    return create_test_category()


@pytest.fixture
def test_categories(db):
    """Crée plusieurs catégories de test."""
    return [create_test_category(name=f"Catégorie {i}") for i in range(1, 4)]


@pytest.fixture
def test_book(db, test_author, test_category):
    """Crée un livre de test."""
    return create_test_book(author=test_author, category=test_category)


@pytest.fixture
def test_books(db, test_authors, test_categories):
    """Crée plusieurs livres de test."""
    books = []
    for i in range(10):
        author = test_authors[i % len(test_authors)]
        category = test_categories[i % len(test_categories)]
        book = create_test_book(
            title=f"Livre {i+1}",
            author=author,
            category=category
        )
        books.append(book)
    return books


@pytest.fixture
def sample_data(db):
    """Crée un jeu de données d'exemple complet."""
    return create_sample_data()


# ============================================================================
# FIXTURES DE PERFORMANCE
# ============================================================================

@pytest.fixture
def query_counter():
    """Compteur de requêtes de base de données."""
    return DatabaseQueryCounter()


@pytest.fixture
def performance_profiler():
    """Profileur de performance."""
    return PerformanceProfiler()


@pytest.fixture
def performance_test(query_counter, performance_profiler):
    """Fixture combinée pour les tests de performance."""
    def _performance_test(func, *args, **kwargs):
        with query_counter:
            with performance_profiler:
                result = func(*args, **kwargs)
        
        return TestResult(
            success=True,
            data=result,
            errors=[],
            execution_time=performance_profiler.get_execution_time(),
            memory_usage=performance_profiler.get_memory_usage(),
            db_queries_count=query_counter.get_query_count()
        )
    
    return _performance_test


# ============================================================================
# FIXTURES DE CACHE
# ============================================================================

@pytest.fixture
def clean_cache():
    """Nettoie le cache avant et après le test."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def cache_with_data(clean_cache):
    """Cache avec des données de test."""
    test_data = {
        'test_key_1': 'test_value_1',
        'test_key_2': {'nested': 'data'},
        'test_key_3': [1, 2, 3, 4, 5]
    }
    
    for key, value in test_data.items():
        cache.set(key, value, timeout=300)
    
    yield test_data


# ============================================================================
# FIXTURES DE CONTEXTE
# ============================================================================

@pytest.fixture
def graphql_context(test_user):
    """Contexte GraphQL avec utilisateur authentifié."""
    class MockRequest:
        def __init__(self, user):
            self.user = user
            self.META = {}
            self.session = {}
    
    return MockRequest(test_user)


@pytest.fixture
def anonymous_context():
    """Contexte GraphQL avec utilisateur anonyme."""
    class MockRequest:
        def __init__(self):
            self.user = None
            self.META = {}
            self.session = {}
    
    return MockRequest()


# ============================================================================
# FIXTURES DE VALIDATION
# ============================================================================

@pytest.fixture
def validation_test_data():
    """Données pour les tests de validation."""
    return {
        'valid_data': {
            'name': 'Test Name',
            'email': 'test@example.com',
            'age': 25,
            'is_active': True
        },
        'invalid_data': {
            'name': '',  # Nom vide
            'email': 'invalid-email',  # Email invalide
            'age': -5,  # Âge négatif
            'is_active': 'not_boolean'  # Pas un booléen
        },
        'edge_cases': {
            'name': 'A' * 1000,  # Nom très long
            'email': 'test+tag@sub.domain.com',  # Email complexe
            'age': 0,  # Âge zéro
            'is_active': None  # Valeur None
        }
    }


# ============================================================================
# FIXTURES DE SÉCURITÉ
# ============================================================================

@pytest.fixture
def security_test_data():
    """Données pour les tests de sécurité."""
    return {
        'sql_injection_attempts': [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ],
        'xss_attempts': [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//\";alert(String.fromCharCode(88,83,83))//\";alert(String.fromCharCode(88,83,83))//--></SCRIPT>\">'><SCRIPT>alert(String.fromCharCode(88,83,83))</SCRIPT>"
        ],
        'csrf_tokens': [
            'invalid_token',
            '',
            None,
            'expired_token'
        ]
    }


# ============================================================================
# FIXTURES DE CONCURRENCE
# ============================================================================

@pytest.fixture
def concurrency_test_setup():
    """Configuration pour les tests de concurrence."""
    import threading
    import queue
    
    class ConcurrencyTestSetup:
        def __init__(self):
            self.results = queue.Queue()
            self.errors = queue.Queue()
            self.threads = []
            self.lock = threading.Lock()
        
        def add_thread(self, target, *args, **kwargs):
            thread = threading.Thread(target=target, args=args, kwargs=kwargs)
            self.threads.append(thread)
            return thread
        
        def start_all(self):
            for thread in self.threads:
                thread.start()
        
        def join_all(self, timeout=30):
            for thread in self.threads:
                thread.join(timeout=timeout)
        
        def get_results(self):
            results = []
            while not self.results.empty():
                results.append(self.results.get())
            return results
        
        def get_errors(self):
            errors = []
            while not self.errors.empty():
                errors.append(self.errors.get())
            return errors
    
    return ConcurrencyTestSetup()


# ============================================================================
# MARQUEURS PYTEST PERSONNALISÉS
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """Modifie la collection de tests pour ajouter des marqueurs automatiques."""
    for item in items:
        # Ajouter le marqueur 'slow' aux tests qui prennent du temps
        if 'performance' in item.nodeid or 'benchmark' in item.nodeid:
            item.add_marker(pytest.mark.slow)
        
        # Ajouter le marqueur 'database' aux tests qui utilisent la DB
        if 'db' in item.fixturenames or 'django_db' in item.keywords:
            item.add_marker(pytest.mark.database)
        
        # Ajouter le marqueur 'integration' aux tests d'intégration
        if 'test_integration' in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Ajouter le marqueur 'unit' aux tests unitaires
        if 'test_generators' in item.nodeid:
            item.add_marker(pytest.mark.unit)


# ============================================================================
# HOOKS PYTEST PERSONNALISÉS
# ============================================================================

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Crée un rapport personnalisé pour chaque test."""
    if call.when == 'call':
        # Ajouter des informations de performance si disponible
        if hasattr(item, 'performance_data'):
            call.result.performance_data = item.performance_data


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Résumé personnalisé affiché à la fin des tests."""
    if hasattr(terminalreporter.config, 'performance_summary'):
        terminalreporter.write_sep('=', 'RÉSUMÉ DE PERFORMANCE')
        for test_name, metrics in terminalreporter.config.performance_summary.items():
            terminalreporter.write_line(f"{test_name}: {metrics}")


# ============================================================================
# UTILITAIRES DE TEST
# ============================================================================

@pytest.fixture
def assert_graphql_success():
    """Utilitaire pour vérifier le succès d'une requête GraphQL."""
    def _assert_success(result):
        assert not result.errors, f"Erreurs GraphQL: {result.errors}"
        assert result.data is not None, "Données GraphQL manquantes"
        return result.data
    
    return _assert_success


@pytest.fixture
def assert_graphql_error():
    """Utilitaire pour vérifier l'échec d'une requête GraphQL."""
    def _assert_error(result, expected_message=None):
        assert result.errors, "Aucune erreur GraphQL trouvée"
        if expected_message:
            error_messages = ' '.join(str(error) for error in result.errors)
            assert expected_message in error_messages, \
                f"Message d'erreur attendu '{expected_message}' non trouvé dans: {error_messages}"
        return result.errors
    
    return _assert_error


@pytest.fixture
def create_test_query():
    """Utilitaire pour créer des requêtes de test."""
    def _create_query(query_type, fields, filters=None, pagination=None):
        query_parts = [f"{query_type} {{"]
        
        if filters:
            filter_str = ', '.join(f"{k}: {v}" for k, v in filters.items())
            query_parts.append(f"  {query_type}({filter_str}) {{")
        else:
            query_parts.append(f"  {query_type} {{")
        
        for field in fields:
            query_parts.append(f"    {field}")
        
        query_parts.append("  }")
        query_parts.append("}")
        
        return '\n'.join(query_parts)
    
    return _create_query


# ============================================================================
# CONFIGURATION FINALE
# ============================================================================

# Enregistrer les fixtures personnalisées
pytest_plugins = [
    'tests.fixtures.test_data_fixtures',
    'tests.fixtures.test_utilities',
    'tests.fixtures.mocks_and_stubs',
]