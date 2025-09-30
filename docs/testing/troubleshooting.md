# Guide de Dépannage - Tests Django GraphQL Auto

Ce guide aide à diagnostiquer et résoudre les problèmes courants rencontrés lors des tests du projet Django GraphQL Auto.

## 📋 Table des Matières

- [Problèmes Courants](#problèmes-courants)
- [Erreurs de Configuration](#erreurs-de-configuration)
- [Problèmes de Base de Données](#problèmes-de-base-de-données)
- [Erreurs GraphQL](#erreurs-graphql)
- [Problèmes de Performance](#problèmes-de-performance)
- [Debugging Avancé](#debugging-avancé)
- [Outils de Diagnostic](#outils-de-diagnostic)
- [Solutions Spécifiques](#solutions-spécifiques)

## 🚨 Problèmes Courants

### 1. Tests qui Échouent de Manière Intermittente

**Symptômes :**

- Tests qui passent parfois et échouent parfois
- Résultats différents selon l'ordre d'exécution
- Échecs lors de l'exécution en parallèle

**Causes Possibles :**

```python
# Problème : État partagé entre les tests
class ProblematicTest:
    shared_data = []  # ❌ État partagé

    def test_one(self):
        self.shared_data.append("test1")
        assert len(self.shared_data) == 1  # Peut échouer si test_two s'exécute avant

    def test_two(self):
        self.shared_data.append("test2")
        assert len(self.shared_data) == 1  # Peut échouer si test_one s'exécute avant
```

**Solutions :**

```python
# Solution 1 : Isolation des données
class FixedTest:
    def setup_method(self):
        """Réinitialiser l'état avant chaque test."""
        self.test_data = []

    def test_one(self):
        self.test_data.append("test1")
        assert len(self.test_data) == 1

    def test_two(self):
        self.test_data.append("test2")
        assert len(self.test_data) == 1


# Solution 2 : Fixtures isolées
@pytest.fixture
def clean_test_data():
    """Fixture qui garantit des données propres."""
    data = []
    yield data
    data.clear()  # Nettoyage après le test


def test_with_clean_data(clean_test_data):
    clean_test_data.append("test")
    assert len(clean_test_data) == 1


# Solution 3 : Transactions de base de données
@pytest.mark.django_db(transaction=True)
def test_with_transaction_isolation():
    """Test avec isolation transactionnelle."""
    # Chaque test s'exécute dans sa propre transaction
    author = TestAuthor.objects.create(name="Test Author")
    assert TestAuthor.objects.count() == 1
    # La transaction est automatiquement annulée après le test
```

### 2. Erreurs de Timeout

**Symptômes :**

```
TimeoutError: Test took longer than 30 seconds
```

**Diagnostic :**

```python
import time
import functools


def timeout_debugger(timeout_seconds=30):
    """Décorateur pour diagnostiquer les timeouts."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import signal

            def timeout_handler(signum, frame):
                import traceback
                print(f"TIMEOUT dans {func.__name__} après {timeout_seconds}s")
                print("Stack trace au moment du timeout:")
                traceback.print_stack(frame)
                raise TimeoutError(f"Test timeout après {timeout_seconds}s")

            # Configurer le timeout
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)

            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                print(f"{func.__name__} terminé en {execution_time:.2f}s")
                return result
            finally:
                signal.alarm(0)  # Annuler le timeout
                signal.signal(signal.SIGALRM, old_handler)

        return wrapper
    return decorator


@timeout_debugger(timeout_seconds=10)
def test_potentially_slow_operation():
    """Test avec diagnostic de timeout."""
    # Opération potentiellement lente
    pass
```

**Solutions :**

```python
# Solution 1 : Optimiser les requêtes lentes
def test_optimized_query():
    """Test avec requête optimisée."""
    # ❌ Lent - N+1 queries
    # authors = TestAuthor.objects.all()
    # for author in authors:
    #     books = author.books.all()

    # ✅ Rapide - Prefetch
    authors = TestAuthor.objects.prefetch_related('books').all()
    for author in authors:
        books = author.books.all()  # Pas de requête supplémentaire


# Solution 2 : Utiliser des mocks pour les opérations lentes
@patch('external_service.slow_api_call')
def test_with_mocked_slow_operation(mock_api):
    """Test avec mock d'opération lente."""
    mock_api.return_value = {'status': 'success'}

    # Le test s'exécute rapidement car l'API est mockée
    result = my_function_that_calls_api()
    assert result['status'] == 'success'


# Solution 3 : Réduire la taille des données de test
def test_with_minimal_data():
    """Test avec données minimales."""
    # ❌ Trop de données
    # TestAuthorFactory.create_batch(10000)

    # ✅ Données minimales suffisantes
    TestAuthorFactory.create_batch(10)
```

### 3. Fuites Mémoire dans les Tests

**Diagnostic :**

```python
import psutil
import gc


class MemoryLeakDetector:
    """Détecteur de fuites mémoire."""

    def __init__(self):
        self.initial_memory = None
        self.memory_threshold_mb = 100

    def start_monitoring(self):
        """Démarre le monitoring mémoire."""
        gc.collect()  # Force garbage collection
        process = psutil.Process()
        self.initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    def check_memory_leak(self, test_name: str):
        """Vérifie s'il y a une fuite mémoire."""
        gc.collect()
        process = psutil.Process()
        current_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_growth = current_memory - self.initial_memory

        if memory_growth > self.memory_threshold_mb:
            # Analyser les objets en mémoire
            import objgraph

            print(f"FUITE MÉMOIRE détectée dans {test_name}")
            print(f"Croissance: {memory_growth:.2f}MB")
            print("Top 10 des types d'objets les plus fréquents:")
            objgraph.show_most_common_types(limit=10)

            # Chercher les références circulaires
            print("Références circulaires:")
            objgraph.show_backrefs([gc.garbage], max_depth=3)

            raise AssertionError(f"Fuite mémoire: {memory_growth:.2f}MB > {self.memory_threshold_mb}MB")


# Utilisation
@pytest.fixture(autouse=True)
def memory_leak_detection():
    """Fixture pour détecter les fuites mémoire."""
    detector = MemoryLeakDetector()
    detector.start_monitoring()

    yield

    # Vérifier après le test
    import inspect
    test_name = inspect.stack()[1].function
    detector.check_memory_leak(test_name)
```

## ⚙️ Erreurs de Configuration

### 1. Problèmes de Settings Django

**Erreur Courante :**

```
django.core.exceptions.ImproperlyConfigured: Requested setting DATABASES, but settings are not configured.
```

**Solution :**

```python
# tests/conftest.py
import os
import django
from django.conf import settings


def pytest_configure():
    """Configuration pytest pour Django."""

    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
        django.setup()


# tests/settings.py - Configuration complète
import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # Base de données en mémoire pour les tests
        'OPTIONS': {
            'timeout': 20,
        }
    }
}

# Applications installées
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'graphene_django',
    'rail_django_graphql',
    'tests',  # Application de test
]

# Middleware minimal pour les tests
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
]

# Configuration GraphQL
GRAPHENE = {
    'SCHEMA': 'tests.schema.schema',
    'MIDDLEWARE': [],
}

# Désactiver les migrations pour les tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Configuration de test
SECRET_KEY = 'test-secret-key-not-for-production'
DEBUG = True
USE_TZ = True
```

### 2. Problèmes d'Import

**Erreur :**

```
ModuleNotFoundError: No module named 'rail_django_graphql'
```

**Solutions :**

```python
# Solution 1 : Vérifier PYTHONPATH
import sys
import os

# Ajouter le répertoire racine au PYTHONPATH
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Solution 2 : Installation en mode développement
# Dans le terminal :
# pip install -e .


# Solution 3 : Configuration pytest.ini
# [pytest.ini]
# python_paths = .
# testpaths = tests
```

## 🗄️ Problèmes de Base de Données

### 1. Erreurs de Migration

**Diagnostic :**

```python
from django.core.management import execute_from_command_line
from django.db import connection


def diagnose_database_issues():
    """Diagnostique les problèmes de base de données."""

    try:
        # Vérifier la connexion
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Connexion à la base de données OK")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return

    # Vérifier les tables
    table_names = connection.introspection.table_names()
    print(f"📊 Tables disponibles: {table_names}")

    # Vérifier les migrations
    try:
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())

        if plan:
            print(f"⚠️  Migrations en attente: {len(plan)}")
            for migration, backwards in plan:
                print(f"  - {migration}")
        else:
            print("✅ Toutes les migrations sont appliquées")

    except Exception as e:
        print(f"❌ Erreur lors de la vérification des migrations: {e}")


# Fixture pour diagnostiquer les problèmes DB
@pytest.fixture(scope="session", autouse=True)
def database_diagnostics():
    """Diagnostique automatique de la base de données."""
    diagnose_database_issues()
```

### 2. Problèmes de Transactions

**Erreur :**

```
TransactionManagementError: An error occurred in the current transaction. You can't execute queries until the end of the 'atomic' block.
```

**Solutions :**

```python
# Solution 1 : Gestion explicite des transactions
from django.db import transaction


@pytest.mark.django_db(transaction=True)
def test_with_transaction_management():
    """Test avec gestion explicite des transactions."""

    try:
        with transaction.atomic():
            author = TestAuthor.objects.create(name="Test")
            # Opération qui peut échouer
            risky_operation()

    except Exception as e:
        # La transaction est automatiquement annulée
        print(f"Transaction annulée: {e}")

    # Vérifier l'état après l'exception
    assert TestAuthor.objects.filter(name="Test").count() == 0


# Solution 2 : Rollback manuel
def test_with_manual_rollback():
    """Test avec rollback manuel."""

    sid = transaction.savepoint()

    try:
        author = TestAuthor.objects.create(name="Test")
        # Opération qui peut échouer
        risky_operation()
        transaction.savepoint_commit(sid)

    except Exception:
        transaction.savepoint_rollback(sid)
        raise


# Solution 3 : Isolation des tests
@pytest.fixture(autouse=True)
def isolate_database_tests():
    """Isole chaque test dans sa propre transaction."""

    with transaction.atomic():
        sid = transaction.savepoint()
        yield
        transaction.savepoint_rollback(sid)
```

## 🔍 Erreurs GraphQL

### 1. Erreurs de Schéma

**Diagnostic :**

```python
from graphql import validate_schema, build_schema
from graphene import Schema


def validate_graphql_schema(schema):
    """Valide un schéma GraphQL."""

    try:
        # Vérifier que le schéma est valide
        errors = validate_schema(schema.graphql_schema)

        if errors:
            print("❌ Erreurs de schéma détectées:")
            for error in errors:
                print(f"  - {error}")
            return False

        print("✅ Schéma GraphQL valide")

        # Vérifier les types principaux
        type_map = schema.graphql_schema.type_map

        required_types = ['Query']
        for type_name in required_types:
            if type_name not in type_map:
                print(f"⚠️  Type manquant: {type_name}")
            else:
                print(f"✅ Type trouvé: {type_name}")

        return True

    except Exception as e:
        print(f"❌ Erreur lors de la validation: {e}")
        return False


# Test de validation automatique
@pytest.fixture(scope="session")
def validated_schema():
    """Fixture qui valide le schéma avant les tests."""
    from tests.schema import schema

    if not validate_graphql_schema(schema):
        pytest.fail("Schéma GraphQL invalide")

    return schema
```

### 2. Erreurs de Résolution

**Diagnostic :**

```python
class GraphQLDebugger:
    """Débogueur pour les requêtes GraphQL."""

    @staticmethod
    def debug_query_execution(schema, query, variables=None):
        """Débogue l'exécution d'une requête."""

        print(f"🔍 Débogage de la requête:")
        print(f"Query: {query}")
        print(f"Variables: {variables}")

        try:
            from graphene.test import Client
            client = Client(schema)

            # Exécuter avec capture des erreurs détaillées
            result = client.execute(query, variables=variables)

            if result.errors:
                print("❌ Erreurs GraphQL:")
                for i, error in enumerate(result.errors):
                    print(f"  Erreur {i+1}:")
                    print(f"    Message: {error}")
                    print(f"    Locations: {getattr(error, 'locations', 'N/A')}")
                    print(f"    Path: {getattr(error, 'path', 'N/A')}")

                    # Stack trace si disponible
                    if hasattr(error, 'original_error'):
                        import traceback
                        print(f"    Stack trace:")
                        traceback.print_exception(
                            type(error.original_error),
                            error.original_error,
                            error.original_error.__traceback__
                        )
            else:
                print("✅ Requête exécutée avec succès")
                print(f"Données: {result.data}")

            return result

        except Exception as e:
            print(f"❌ Exception lors de l'exécution: {e}")
            import traceback
            traceback.print_exc()
            raise


# Utilisation dans les tests
def test_debug_graphql_query():
    """Test avec débogage GraphQL."""

    query = """
    query {
        authors {
            id
            nonExistentField  # Erreur intentionnelle
        }
    }
    """

    from tests.schema import schema
    result = GraphQLDebugger.debug_query_execution(schema, query)

    # Le débogueur affichera les détails de l'erreur
    assert result.errors  # On s'attend à une erreur
```

### 3. Problèmes de Performance GraphQL

**Diagnostic :**

```python
class GraphQLPerformanceDebugger:
    """Débogueur de performance pour GraphQL."""

    @staticmethod
    def analyze_query_complexity(schema, query):
        """Analyse la complexité d'une requête."""

        from graphql import parse, validate
        from graphql.execution import execute

        # Parser la requête
        document = parse(query)

        # Analyser la profondeur
        def get_query_depth(selection_set, depth=0):
            max_depth = depth

            for selection in selection_set.selections:
                if hasattr(selection, 'selection_set') and selection.selection_set:
                    field_depth = get_query_depth(selection.selection_set, depth + 1)
                    max_depth = max(max_depth, field_depth)

            return max_depth

        # Analyser la largeur (nombre de champs)
        def count_fields(selection_set):
            count = 0

            for selection in selection_set.selections:
                count += 1
                if hasattr(selection, 'selection_set') and selection.selection_set:
                    count += count_fields(selection.selection_set)

            return count

        query_def = document.definitions[0]
        depth = get_query_depth(query_def.selection_set)
        field_count = count_fields(query_def.selection_set)

        complexity_score = depth * field_count

        print(f"📊 Analyse de complexité:")
        print(f"  Profondeur: {depth}")
        print(f"  Nombre de champs: {field_count}")
        print(f"  Score de complexité: {complexity_score}")

        # Alertes
        if depth > 10:
            print("⚠️  Requête très profonde (risque de N+1)")

        if field_count > 50:
            print("⚠️  Beaucoup de champs (risque de performance)")

        if complexity_score > 100:
            print("⚠️  Complexité élevée (optimisation recommandée)")

        return {
            'depth': depth,
            'field_count': field_count,
            'complexity_score': complexity_score
        }


# Test de performance avec analyse
def test_query_performance_analysis():
    """Test avec analyse de performance."""

    complex_query = """
    query {
        authors {
            id
            firstName
            lastName
            books {
                title
                isbn
                category {
                    name
                    description
                    books {
                        title
                        author {
                            firstName
                        }
                    }
                }
            }
        }
    }
    """

    from tests.schema import schema

    # Analyser la complexité
    analysis = GraphQLPerformanceDebugger.analyze_query_complexity(schema, complex_query)

    # Mesurer l'exécution
    import time
    from django.db import connection

    connection.queries_log.clear()
    start_time = time.time()

    result = GraphQLDebugger.debug_query_execution(schema, complex_query)

    execution_time = time.time() - start_time
    db_queries = len(connection.queries)

    print(f"⏱️  Temps d'exécution: {execution_time:.3f}s")
    print(f"🗄️  Requêtes DB: {db_queries}")

    # Assertions de performance
    assert execution_time < 1.0, f"Requête trop lente: {execution_time:.3f}s"
    assert db_queries < 20, f"Trop de requêtes DB: {db_queries}"
```

## 🛠️ Outils de Diagnostic

### 1. Collecteur d'Informations Système

```python
import platform
import sys
import django
import graphene
from django.db import connection


class SystemDiagnostics:
    """Collecteur d'informations système pour le diagnostic."""

    @staticmethod
    def collect_system_info():
        """Collecte les informations système."""

        info = {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
            },
            'python': {
                'version': sys.version,
                'executable': sys.executable,
                'path': sys.path[:5],  # Premiers 5 éléments du path
            },
            'django': {
                'version': django.get_version(),
                'settings_module': os.environ.get('DJANGO_SETTINGS_MODULE'),
            },
            'graphene': {
                'version': graphene.__version__,
            },
            'database': {
                'engine': connection.settings_dict['ENGINE'],
                'name': connection.settings_dict['NAME'],
            },
            'environment': {
                'testing': os.environ.get('TESTING', 'False'),
                'debug': os.environ.get('DEBUG', 'False'),
            }
        }

        return info

    @staticmethod
    def print_diagnostics():
        """Affiche les informations de diagnostic."""

        info = SystemDiagnostics.collect_system_info()

        print("🔧 INFORMATIONS SYSTÈME")
        print("=" * 50)

        for category, details in info.items():
            print(f"\n📋 {category.upper()}:")
            for key, value in details.items():
                print(f"  {key}: {value}")

    @staticmethod
    def check_dependencies():
        """Vérifie les dépendances requises."""

        required_packages = [
            'django',
            'graphene',
            'graphene_django',
            'pytest',
            'pytest_django',
        ]

        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package}")
            except ImportError:
                print(f"❌ {package} - MANQUANT")
                missing_packages.append(package)

        if missing_packages:
            print(f"\n⚠️  Packages manquants: {', '.join(missing_packages)}")
            print("Installez-les avec: pip install " + " ".join(missing_packages))
        else:
            print("\n✅ Toutes les dépendances sont installées")


# Fixture de diagnostic automatique
@pytest.fixture(scope="session", autouse=True)
def system_diagnostics():
    """Diagnostic système automatique."""

    print("\n" + "="*60)
    print("🔍 DIAGNOSTIC SYSTÈME AUTOMATIQUE")
    print("="*60)

    SystemDiagnostics.print_diagnostics()
    print("\n" + "="*60)
    print("📦 VÉRIFICATION DES DÉPENDANCES")
    print("="*60)
    SystemDiagnostics.check_dependencies()
    print("="*60 + "\n")
```

### 2. Générateur de Rapports d'Erreur

```python
class ErrorReporter:
    """Générateur de rapports d'erreur détaillés."""

    @staticmethod
    def generate_error_report(test_name, exception, context=None):
        """Génère un rapport d'erreur détaillé."""

        import traceback
        import datetime

        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'test_name': test_name,
            'exception': {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': traceback.format_exc(),
            },
            'context': context or {},
            'system_info': SystemDiagnostics.collect_system_info(),
        }

        # Ajouter des informations spécifiques selon le type d'erreur
        if 'database' in str(exception).lower():
            report['database_info'] = ErrorReporter._get_database_info()

        if 'graphql' in str(exception).lower():
            report['graphql_info'] = ErrorReporter._get_graphql_info()

        return report

    @staticmethod
    def _get_database_info():
        """Collecte les informations de base de données."""

        try:
            from django.db import connection

            return {
                'connection_settings': {
                    'ENGINE': connection.settings_dict['ENGINE'],
                    'NAME': connection.settings_dict['NAME'],
                },
                'queries_count': len(connection.queries),
                'last_queries': connection.queries[-5:] if connection.queries else [],
            }
        except Exception as e:
            return {'error': f"Impossible de collecter les infos DB: {e}"}

    @staticmethod
    def _get_graphql_info():
        """Collecte les informations GraphQL."""

        try:
            from tests.schema import schema

            return {
                'schema_types': list(schema.graphql_schema.type_map.keys())[:10],
                'schema_valid': True,  # Simplifié
            }
        except Exception as e:
            return {'error': f"Impossible de collecter les infos GraphQL: {e}"}

    @staticmethod
    def save_error_report(report, filename=None):
        """Sauvegarde le rapport d'erreur."""

        import json

        if not filename:
            timestamp = report['timestamp'].replace(':', '-').replace('.', '-')
            filename = f"error_report_{timestamp}.json"

        filepath = os.path.join('test_reports', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📄 Rapport d'erreur sauvegardé: {filepath}")
        return filepath


# Hook pytest pour capturer les erreurs
def pytest_runtest_call(pyfuncitem):
    """Hook pytest pour capturer les erreurs de test."""

    try:
        # Exécution normale du test
        pass
    except Exception as e:
        # Générer un rapport d'erreur
        context = {
            'test_file': pyfuncitem.fspath.basename,
            'test_function': pyfuncitem.name,
            'test_markers': [marker.name for marker in pyfuncitem.iter_markers()],
        }

        report = ErrorReporter.generate_error_report(
            pyfuncitem.name,
            e,
            context
        )

        ErrorReporter.save_error_report(report)

        # Re-lever l'exception
        raise
```

Ce guide de dépannage fournit les outils et techniques nécessaires pour diagnostiquer et résoudre efficacement les problèmes de test. Utilisez ces ressources pour maintenir une suite de tests robuste et fiable.
