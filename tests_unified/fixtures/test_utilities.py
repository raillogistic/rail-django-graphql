"""
Utilitaires de test pour les tests GraphQL.

Ce module fournit:
- Des fonctions utilitaires réutilisables
- Des helpers d'assertion
- Des décorateurs de test
- Des gestionnaires de contexte
- Des outils de validation
"""

import pytest
import time
import json
import logging
import functools
import contextlib
from typing import Dict, List, Any, Optional, Callable, Union, Type
from decimal import Decimal
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
import threading
import queue
import gc
import psutil
import os

from django.test import TestCase, TransactionTestCase
from django.db import transaction, connection
from django.core.management import call_command
from django.conf import settings
from django.contrib.auth.models import User
from django.test.utils import override_settings

import graphene
from graphene.test import Client
from graphql import GraphQLError

from rail_django_graphql.core.schema import SchemaBuilder
from rail_django_graphql.generators.introspector import ModelIntrospector
from rail_django_graphql.generators.types import TypeGenerator
from rail_django_graphql.generators.queries import QueryGenerator
from rail_django_graphql.generators.mutations import MutationGenerator


# ============================================================================
# CLASSES UTILITAIRES
# ============================================================================


@dataclass
class TestResult:
    """Résultat d'un test avec métadonnées."""

    success: bool
    data: Any = None
    errors: List[str] = None
    execution_time: float = 0.0
    memory_usage: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PerformanceMetrics:
    """Métriques de performance pour les tests."""

    execution_time: float
    memory_before: int
    memory_after: int
    memory_peak: int
    cpu_percent: float
    db_queries_count: int
    cache_hits: int = 0
    cache_misses: int = 0

    @property
    def memory_delta(self) -> int:
        """Différence de mémoire."""
        return self.memory_after - self.memory_before

    @property
    def cache_hit_ratio(self) -> float:
        """Ratio de succès du cache."""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0


class GraphQLTestClient:
    """Client de test GraphQL personnalisé."""

    def __init__(self, schema: graphene.Schema):
        self.schema = schema
        self.client = Client(schema)
        self.context = {}
        self.user = None

    def set_user(self, user: User):
        """Définit l'utilisateur pour les requêtes."""
        self.user = user
        self.context["user"] = user

    def execute(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> TestResult:
        """Exécute une requête GraphQL et retourne un TestResult."""
        start_time = time.time()
        memory_before = self._get_memory_usage()

        # Fusionner les contextes
        final_context = {**self.context}
        if context:
            final_context.update(context)

        try:
            result = self.client.execute(
                query, variables=variables, context=final_context
            )

            execution_time = time.time() - start_time
            memory_after = self._get_memory_usage()

            return TestResult(
                success=not result.errors,
                data=result.data,
                errors=[str(error) for error in (result.errors or [])],
                execution_time=execution_time,
                memory_usage=memory_after - memory_before,
                metadata={
                    "variables": variables,
                    "context_keys": list(final_context.keys()),
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            memory_after = self._get_memory_usage()

            return TestResult(
                success=False,
                errors=[str(e)],
                execution_time=execution_time,
                memory_usage=memory_after - memory_before,
            )

    def _get_memory_usage(self) -> int:
        """Obtient l'utilisation mémoire actuelle."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss


class DatabaseQueryCounter:
    """Compteur de requêtes de base de données."""

    def __init__(self):
        self.query_count = 0
        self.queries = []
        self.original_execute = None

    def __enter__(self):
        self.query_count = 0
        self.queries = []

        # Intercepter les requêtes
        from django.db import connection

        self.original_execute = connection.ops.execute

        def counting_execute(self_inner, cursor, sql, params=None):
            self.query_count += 1
            self.queries.append({"sql": sql, "params": params, "time": time.time()})
            return self.original_execute(cursor, sql, params)

        connection.ops.execute = counting_execute
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_execute:
            from django.db import connection

            connection.ops.execute = self.original_execute


class PerformanceProfiler:
    """Profileur de performance pour les tests."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.memory_before = None
        self.memory_after = None
        self.memory_peak = None
        self.cpu_percent = None
        self.db_counter = None

    def __enter__(self) -> "PerformanceProfiler":
        self.start_time = time.time()
        self.memory_before = self._get_memory_usage()
        self.memory_peak = self.memory_before
        self.db_counter = DatabaseQueryCounter()
        self.db_counter.__enter__()

        # Démarrer le monitoring CPU
        self._start_cpu_monitoring()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.memory_after = self._get_memory_usage()
        self.memory_peak = max(self.memory_peak, self.memory_after)

        self.db_counter.__exit__(exc_type, exc_val, exc_tb)
        self._stop_cpu_monitoring()

    def get_metrics(self) -> PerformanceMetrics:
        """Retourne les métriques de performance."""
        return PerformanceMetrics(
            execution_time=self.end_time - self.start_time,
            memory_before=self.memory_before,
            memory_after=self.memory_after,
            memory_peak=self.memory_peak,
            cpu_percent=self.cpu_percent or 0.0,
            db_queries_count=self.db_counter.query_count,
        )

    def _get_memory_usage(self) -> int:
        """Obtient l'utilisation mémoire actuelle."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss

    def _start_cpu_monitoring(self):
        """Démarre le monitoring CPU."""
        self.cpu_percent = psutil.cpu_percent(interval=None)

    def _stop_cpu_monitoring(self):
        """Arrête le monitoring CPU."""
        self.cpu_percent = psutil.cpu_percent(interval=None)


# ============================================================================
# DÉCORATEURS DE TEST
# ============================================================================


def performance_test(
    max_execution_time: float = None,
    max_memory_usage: int = None,
    max_db_queries: int = None,
):
    """Décorateur pour les tests de performance."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with PerformanceProfiler() as profiler:
                result = func(*args, **kwargs)

            metrics = profiler.get_metrics()

            # Vérifier les limites
            if max_execution_time and metrics.execution_time > max_execution_time:
                pytest.fail(
                    f"Test trop lent: {metrics.execution_time:.3f}s > {max_execution_time}s"
                )

            if max_memory_usage and metrics.memory_delta > max_memory_usage:
                pytest.fail(
                    f"Utilisation mémoire excessive: {metrics.memory_delta} bytes > {max_memory_usage} bytes"
                )

            if max_db_queries and metrics.db_queries_count > max_db_queries:
                pytest.fail(
                    f"Trop de requêtes DB: {metrics.db_queries_count} > {max_db_queries}"
                )

            return result

        return wrapper

    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 0.1):
    """Décorateur pour réessayer les tests en cas d'échec."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay)
                        continue
                    raise

            raise last_exception

        return wrapper

    return decorator


def skip_if_db_unavailable(func):
    """Décorateur pour ignorer le test si la DB n'est pas disponible."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            from django.db import connection

            connection.ensure_connection()
            return func(*args, **kwargs)
        except Exception:
            pytest.skip("Base de données non disponible")

    return wrapper


def requires_models(*model_classes):
    """Décorateur pour s'assurer que les modèles sont disponibles."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for model_class in model_classes:
                try:
                    model_class._meta.get_field("id")
                except Exception:
                    pytest.skip(f"Modèle {model_class.__name__} non disponible")

            return func(*args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# HELPERS D'ASSERTION
# ============================================================================


class GraphQLAssertions:
    """Helpers d'assertion pour GraphQL."""

    @staticmethod
    def assert_no_errors(result: TestResult):
        """Vérifie qu'il n'y a pas d'erreurs."""
        assert result.success, f"Erreurs GraphQL: {result.errors}"

    @staticmethod
    def assert_has_errors(result: TestResult, expected_count: int = None):
        """Vérifie qu'il y a des erreurs."""
        assert not result.success, "Aucune erreur trouvée"
        if expected_count is not None:
            assert (
                len(result.errors) == expected_count
            ), f"Nombre d'erreurs incorrect: {len(result.errors)} != {expected_count}"

    @staticmethod
    def assert_error_contains(result: TestResult, message: str):
        """Vérifie qu'une erreur contient un message."""
        assert not result.success, "Aucune erreur trouvée"
        error_messages = " ".join(result.errors)
        assert (
            message in error_messages
        ), f"Message '{message}' non trouvé dans les erreurs: {result.errors}"

    @staticmethod
    def assert_data_equals(result: TestResult, expected_data: Dict[str, Any]):
        """Vérifie que les données correspondent."""
        assert result.success, f"Erreurs GraphQL: {result.errors}"
        assert (
            result.data == expected_data
        ), f"Données incorrectes:\nAttendu: {expected_data}\nObtenu: {result.data}"

    @staticmethod
    def assert_data_contains(result: TestResult, key: str, expected_value: Any = None):
        """Vérifie que les données contiennent une clé."""
        assert result.success, f"Erreurs GraphQL: {result.errors}"
        assert key in result.data, f"Clé '{key}' non trouvée dans les données"

        if expected_value is not None:
            actual_value = result.data[key]
            assert (
                actual_value == expected_value
            ), f"Valeur incorrecte pour '{key}': {actual_value} != {expected_value}"

    @staticmethod
    def assert_list_length(result: TestResult, key: str, expected_length: int):
        """Vérifie la longueur d'une liste dans les données."""
        assert result.success, f"Erreurs GraphQL: {result.errors}"
        assert key in result.data, f"Clé '{key}' non trouvée dans les données"

        actual_list = result.data[key]
        assert isinstance(actual_list, list), f"'{key}' n'est pas une liste"
        assert (
            len(actual_list) == expected_length
        ), f"Longueur incorrecte pour '{key}': {len(actual_list)} != {expected_length}"

    @staticmethod
    def assert_performance(
        result: TestResult, max_time: float = None, max_memory: int = None
    ):
        """Vérifie les performances."""
        if max_time is not None:
            assert (
                result.execution_time <= max_time
            ), f"Temps d'exécution trop long: {result.execution_time:.3f}s > {max_time}s"

        if max_memory is not None:
            assert (
                result.memory_usage <= max_memory
            ), f"Utilisation mémoire excessive: {result.memory_usage} bytes > {max_memory} bytes"


# ============================================================================
# UTILITAIRES DE VALIDATION
# ============================================================================


def validate_graphql_schema(schema: graphene.Schema) -> List[str]:
    """Valide un schéma GraphQL et retourne les erreurs."""
    errors = []

    try:
        # Vérifier que le schéma peut être construit
        schema_dict = schema.execute("{ __schema { types { name } } }")

        if schema_dict.errors:
            errors.extend([str(error) for error in schema_dict.errors])

        # Vérifier les types de base
        if schema_dict.data:
            type_names = [t["name"] for t in schema_dict.data["__schema"]["types"]]

            required_types = ["Query", "String", "Int", "Boolean"]
            for required_type in required_types:
                if required_type not in type_names:
                    errors.append(f"Type requis manquant: {required_type}")

    except Exception as e:
        errors.append(f"Erreur de validation du schéma: {str(e)}")

    return errors


def validate_query_syntax(query: str) -> List[str]:
    """Valide la syntaxe d'une requête GraphQL."""
    errors = []

    try:
        from graphql import parse

        parse(query)
    except Exception as e:
        errors.append(f"Erreur de syntaxe GraphQL: {str(e)}")

    return errors


def validate_model_fields(model_class, expected_fields: List[str]) -> List[str]:
    """Valide que le modèle a les champs attendus."""
    errors = []

    try:
        model_fields = [field.name for field in model_class._meta.get_fields()]

        for expected_field in expected_fields:
            if expected_field not in model_fields:
                errors.append(
                    f"Champ manquant dans {model_class.__name__}: {expected_field}"
                )

    except Exception as e:
        errors.append(f"Erreur de validation du modèle: {str(e)}")

    return errors


# ============================================================================
# UTILITAIRES DE MOCK
# ============================================================================


class MockGraphQLContext:
    """Mock pour le contexte GraphQL."""

    def __init__(self, user: User = None, **kwargs):
        self.user = user
        self.META = {}
        self.session = {}

        for key, value in kwargs.items():
            setattr(self, key, value)


def create_mock_request(user: User = None, **kwargs):
    """Crée une requête mock pour les tests."""
    request = Mock()
    request.user = user
    request.META = kwargs.get("META", {})
    request.session = kwargs.get("session", {})
    request.method = kwargs.get("method", "POST")
    request.content_type = kwargs.get("content_type", "application/json")

    return request


def mock_business_method(return_value: Any = None, side_effect: Exception = None):
    """Crée un mock pour une méthode business."""
    mock = Mock()

    if side_effect:
        mock.side_effect = side_effect
    else:
        mock.return_value = return_value

    return mock


# ============================================================================
# UTILITAIRES DE DONNÉES
# ============================================================================


def generate_test_data(data_type: str, count: int = 1) -> Union[Any, List[Any]]:
    """Génère des données de test selon le type."""
    generators = {
        "string": lambda: f"test_string_{time.time()}",
        "int": lambda: int(time.time() % 1000),
        "float": lambda: float(time.time() % 100),
        "bool": lambda: bool(int(time.time()) % 2),
        "email": lambda: f"test_{int(time.time())}@example.com",
        "url": lambda: f"https://example.com/test_{int(time.time())}",
        "date": lambda: date.today(),
        "datetime": lambda: datetime.now(),
        "decimal": lambda: Decimal(str(time.time() % 100)),
    }

    generator = generators.get(data_type, lambda: f"unknown_type_{data_type}")

    if count == 1:
        return generator()
    else:
        return [generator() for _ in range(count)]


def compare_data_structures(
    data1: Any, data2: Any, ignore_keys: List[str] = None
) -> bool:
    """Compare deux structures de données en ignorant certaines clés."""
    if ignore_keys is None:
        ignore_keys = []

    def clean_data(data):
        if isinstance(data, dict):
            return {k: clean_data(v) for k, v in data.items() if k not in ignore_keys}
        elif isinstance(data, list):
            return [clean_data(item) for item in data]
        else:
            return data

    return clean_data(data1) == clean_data(data2)


# ============================================================================
# UTILITAIRES DE LOGGING
# ============================================================================


class TestLogCapture:
    """Capture les logs pendant les tests."""

    def __init__(self, logger_name: str = None, level: int = logging.DEBUG):
        self.logger_name = logger_name or "rail_django_graphql"
        self.level = level
        self.logs = []
        self.handler = None
        self.logger = None

    def __enter__(self):
        self.logger = logging.getLogger(self.logger_name)
        self.original_level = self.logger.level

        # Créer un handler personnalisé
        self.handler = logging.Handler()
        self.handler.emit = self._capture_log

        self.logger.addHandler(self.handler)
        self.logger.setLevel(self.level)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handler and self.logger:
            self.logger.removeHandler(self.handler)
            self.logger.setLevel(self.original_level)

    def _capture_log(self, record):
        """Capture un enregistrement de log."""
        self.logs.append(
            {
                "level": record.levelname,
                "message": record.getMessage(),
                "timestamp": record.created,
                "module": record.module,
                "funcName": record.funcName,
                "lineno": record.lineno,
            }
        )

    def get_logs(self, level: str = None) -> List[Dict[str, Any]]:
        """Retourne les logs capturés."""
        if level:
            return [log for log in self.logs if log["level"] == level.upper()]
        return self.logs

    def assert_log_contains(self, message: str, level: str = None):
        """Vérifie qu'un log contient un message."""
        logs = self.get_logs(level)
        log_messages = [log["message"] for log in logs]

        assert any(
            message in msg for msg in log_messages
        ), f"Message '{message}' non trouvé dans les logs: {log_messages}"


# ============================================================================
# UTILITAIRES DE CONCURRENCE
# ============================================================================


class ConcurrentTestRunner:
    """Exécuteur de tests concurrents."""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.results = queue.Queue()
        self.errors = queue.Queue()

    def run_concurrent_tests(
        self, test_func: Callable, test_args_list: List[tuple], timeout: float = 30.0
    ) -> List[Any]:
        """Exécute des tests en parallèle."""
        threads = []

        def worker(args):
            try:
                result = test_func(*args)
                self.results.put(result)
            except Exception as e:
                self.errors.put(e)

        # Démarrer les threads
        for args in test_args_list[: self.max_workers]:
            thread = threading.Thread(target=worker, args=(args,))
            thread.start()
            threads.append(thread)

        # Attendre la fin
        for thread in threads:
            thread.join(timeout=timeout)

        # Collecter les résultats
        results = []
        while not self.results.empty():
            results.append(self.results.get())

        # Vérifier les erreurs
        errors = []
        while not self.errors.empty():
            errors.append(self.errors.get())

        if errors:
            raise Exception(f"Erreurs dans les tests concurrents: {errors}")

        return results


# ============================================================================
# UTILITAIRES DE NETTOYAGE
# ============================================================================


@contextlib.contextmanager
def temporary_settings(**settings_dict):
    """Gestionnaire de contexte pour des paramètres temporaires."""
    with override_settings(**settings_dict):
        yield


@contextlib.contextmanager
def clean_database():
    """Gestionnaire de contexte pour nettoyer la base de données."""
    try:
        yield
    finally:
        # Nettoyer toutes les tables de test
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

            # Obtenir toutes les tables de test
            cursor.execute("SHOW TABLES LIKE 'test_%'")
            tables = cursor.fetchall()

            for table in tables:
                cursor.execute(f"TRUNCATE TABLE {table[0]}")

            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")


def force_garbage_collection():
    """Force le garbage collection."""
    gc.collect()
    gc.collect()  # Deux fois pour être sûr
    gc.collect()


# ============================================================================
# FONCTIONS UTILITAIRES GLOBALES
# ============================================================================


def setup_test_environment():
    """Configure l'environnement de test."""
    # Configurer les logs
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Désactiver les migrations pour les tests
    settings.MIGRATION_MODULES = {
        "rail_django_graphql": None,
    }


def teardown_test_environment():
    """Nettoie l'environnement de test."""
    force_garbage_collection()


def get_test_database_name() -> str:
    """Retourne le nom de la base de données de test."""
    from django.conf import settings

    db_config = settings.DATABASES["default"]
    return db_config.get("TEST", {}).get("NAME", "test_" + db_config["NAME"])


def is_test_environment() -> bool:
    """Vérifie si on est dans un environnement de test."""
    return "test" in get_test_database_name().lower()
