# Guide de Tests de Performance - Django GraphQL Auto

Ce guide détaille les stratégies et outils pour tester et optimiser les performances du système Django GraphQL Auto.

## 📋 Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Métriques de Performance](#métriques-de-performance)
- [Outils de Mesure](#outils-de-mesure)
- [Tests de Charge](#tests-de-charge)
- [Profiling et Analyse](#profiling-et-analyse)
- [Optimisation](#optimisation)
- [Monitoring Continu](#monitoring-continu)
- [Exemples Pratiques](#exemples-pratiques)

## 🎯 Vue d'Ensemble

### Objectifs de Performance

Les tests de performance visent à garantir que le système maintient des performances acceptables sous différentes conditions de charge.

#### Critères de Performance Cibles

```python
# Configuration des seuils de performance
PERFORMANCE_THRESHOLDS = {
    'schema_generation': {
        'max_time_seconds': 5.0,
        'max_memory_mb': 100,
        'max_models': 1000,
    },
    'query_execution': {
        'simple_query_ms': 100,
        'complex_query_ms': 500,
        'max_db_queries': 10,
    },
    'mutation_execution': {
        'create_mutation_ms': 200,
        'update_mutation_ms': 150,
        'delete_mutation_ms': 100,
    },
    'concurrent_operations': {
        'max_concurrent_users': 100,
        'response_time_95th_percentile_ms': 1000,
        'error_rate_threshold': 0.01,  # 1%
    }
}
```

### Types de Tests de Performance

1. **Tests de Charge** : Performance sous charge normale
2. **Tests de Stress** : Comportement aux limites
3. **Tests de Volume** : Gestion de grandes quantités de données
4. **Tests de Concurrence** : Accès simultané
5. **Tests d'Endurance** : Stabilité sur la durée

## 📊 Métriques de Performance

### Métriques Principales

```python
from dataclasses import dataclass
from typing import Dict, List, Optional
import time
import psutil
import threading


@dataclass
class PerformanceMetrics:
    """Métriques de performance collectées."""

    # Temps d'exécution
    execution_time_seconds: float
    cpu_time_seconds: float

    # Utilisation mémoire
    memory_usage_mb: float
    peak_memory_mb: float
    memory_growth_mb: float

    # Base de données
    db_query_count: int
    db_query_time_ms: float

    # Concurrence
    concurrent_operations: int
    thread_count: int

    # Erreurs
    error_count: int
    error_rate: float

    # Métadonnées
    timestamp: float
    test_name: str
    context: Dict[str, any]


class PerformanceCollector:
    """Collecteur de métriques de performance."""

    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.peak_memory = 0
        self.db_queries = []
        self.errors = []
        self.context = {}

    def start_collection(self, test_name: str, context: Dict = None):
        """Démarre la collecte de métriques."""
        self.test_name = test_name
        self.context = context or {}
        self.start_time = time.time()

        process = psutil.Process()
        self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory

        # Hook pour capturer les requêtes DB
        self._setup_db_monitoring()

    def stop_collection(self) -> PerformanceMetrics:
        """Arrête la collecte et retourne les métriques."""
        end_time = time.time()
        execution_time = end_time - self.start_time

        process = psutil.Process()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB

        return PerformanceMetrics(
            execution_time_seconds=execution_time,
            cpu_time_seconds=sum(process.cpu_times()),
            memory_usage_mb=end_memory,
            peak_memory_mb=self.peak_memory,
            memory_growth_mb=end_memory - self.start_memory,
            db_query_count=len(self.db_queries),
            db_query_time_ms=sum(q['duration'] for q in self.db_queries),
            concurrent_operations=threading.active_count(),
            thread_count=threading.active_count(),
            error_count=len(self.errors),
            error_rate=len(self.errors) / max(1, len(self.db_queries)),
            timestamp=end_time,
            test_name=self.test_name,
            context=self.context
        )

    def _setup_db_monitoring(self):
        """Configure le monitoring des requêtes DB."""
        from django.db import connection

        original_execute = connection.cursor().execute

        def monitored_execute(sql, params=None):
            start_time = time.time()
            try:
                result = original_execute(sql, params)
                duration = (time.time() - start_time) * 1000  # ms
                self.db_queries.append({
                    'sql': sql,
                    'params': params,
                    'duration': duration,
                    'timestamp': start_time
                })
                return result
            except Exception as e:
                self.errors.append({
                    'type': 'database',
                    'error': str(e),
                    'sql': sql,
                    'timestamp': time.time()
                })
                raise

        connection.cursor().execute = monitored_execute
```

### Métriques GraphQL Spécifiques

```python
class GraphQLPerformanceMetrics:
    """Métriques spécifiques aux opérations GraphQL."""

    @staticmethod
    def measure_schema_generation(models: List, iterations: int = 10):
        """Mesure les performances de génération de schéma."""
        from rail_django_graphql.core.generator import AutoSchemaGenerator

        metrics = []

        for i in range(iterations):
            collector = PerformanceCollector()
            collector.start_collection(
                f"schema_generation_iteration_{i}",
                {'model_count': len(models), 'iteration': i}
            )

            try:
                generator = AutoSchemaGenerator()
                schema = generator.generate_schema(models)

                # Vérifier la validité du schéma
                assert schema is not None
                assert len(schema.type_map) > 0

            except Exception as e:
                collector.errors.append({
                    'type': 'schema_generation',
                    'error': str(e),
                    'timestamp': time.time()
                })

            metrics.append(collector.stop_collection())

        return metrics

    @staticmethod
    def measure_query_execution(schema, query: str, variables: Dict = None, iterations: int = 100):
        """Mesure les performances d'exécution de requêtes."""
        from graphene.test import Client

        client = Client(schema)
        metrics = []

        for i in range(iterations):
            collector = PerformanceCollector()
            collector.start_collection(
                f"query_execution_iteration_{i}",
                {'query_length': len(query), 'has_variables': bool(variables)}
            )

            try:
                result = client.execute(query, variables=variables)

                # Vérifier le succès de la requête
                if result.errors:
                    collector.errors.extend([
                        {'type': 'graphql', 'error': str(error), 'timestamp': time.time()}
                        for error in result.errors
                    ])

            except Exception as e:
                collector.errors.append({
                    'type': 'query_execution',
                    'error': str(e),
                    'timestamp': time.time()
                })

            metrics.append(collector.stop_collection())

        return metrics
```

## 🔧 Outils de Mesure

### Décorateurs de Performance

```python
import functools
from typing import Callable, Any


def measure_performance(
    max_time_seconds: Optional[float] = None,
    max_memory_mb: Optional[float] = None,
    max_db_queries: Optional[int] = None
):
    """Décorateur pour mesurer automatiquement les performances."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            collector = PerformanceCollector()
            collector.start_collection(
                func.__name__,
                {'args_count': len(args), 'kwargs_count': len(kwargs)}
            )

            try:
                result = func(*args, **kwargs)
                metrics = collector.stop_collection()

                # Vérifications des seuils
                if max_time_seconds and metrics.execution_time_seconds > max_time_seconds:
                    raise AssertionError(
                        f"Temps d'exécution dépassé: {metrics.execution_time_seconds:.2f}s > {max_time_seconds}s"
                    )

                if max_memory_mb and metrics.memory_growth_mb > max_memory_mb:
                    raise AssertionError(
                        f"Croissance mémoire dépassée: {metrics.memory_growth_mb:.2f}MB > {max_memory_mb}MB"
                    )

                if max_db_queries and metrics.db_query_count > max_db_queries:
                    raise AssertionError(
                        f"Nombre de requêtes DB dépassé: {metrics.db_query_count} > {max_db_queries}"
                    )

                # Enregistrer les métriques pour analyse
                PerformanceReporter.record_metrics(metrics)

                return result

            except Exception as e:
                metrics = collector.stop_collection()
                PerformanceReporter.record_metrics(metrics)
                raise

        return wrapper
    return decorator


# Utilisation
@measure_performance(max_time_seconds=2.0, max_memory_mb=50, max_db_queries=5)
def test_schema_generation_performance():
    """Test de performance avec limites automatiques."""
    generator = AutoSchemaGenerator()
    return generator.generate_schema([TestAuthor, TestBook])
```

### Context Manager pour Profiling

```python
import cProfile
import pstats
from contextlib import contextmanager


@contextmanager
def performance_profiler(output_file: Optional[str] = None):
    """Context manager pour profiler les performances."""

    profiler = cProfile.Profile()
    profiler.enable()

    collector = PerformanceCollector()
    collector.start_collection("profiled_operation")

    try:
        yield collector
    finally:
        profiler.disable()
        metrics = collector.stop_collection()

        # Sauvegarder le profil
        if output_file:
            profiler.dump_stats(output_file)

        # Analyser les statistiques
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')

        # Ajouter les stats au contexte des métriques
        metrics.context['profiling_stats'] = {
            'total_calls': stats.total_calls,
            'primitive_calls': stats.prim_calls,
            'total_time': stats.total_tt,
        }

        PerformanceReporter.record_metrics(metrics)


# Utilisation
def test_with_profiling():
    """Test avec profiling détaillé."""
    with performance_profiler("schema_generation_profile.prof") as profiler:
        generator = AutoSchemaGenerator()
        schema = generator.generate_schema([TestAuthor, TestBook])

        # Ajouter des informations contextuelles
        profiler.context['schema_types'] = len(schema.type_map)
```

## 🚀 Tests de Charge

### Simulation de Charge

```python
import concurrent.futures
import threading
from queue import Queue
import random


class LoadTestRunner:
    """Exécuteur de tests de charge."""

    def __init__(self, schema):
        self.schema = schema
        self.results_queue = Queue()
        self.error_queue = Queue()

    def run_concurrent_queries(
        self,
        queries: List[str],
        concurrent_users: int = 10,
        requests_per_user: int = 100,
        ramp_up_seconds: int = 10
    ):
        """Exécute des requêtes concurrentes."""

        def user_simulation(user_id: int):
            """Simule un utilisateur effectuant des requêtes."""
            from graphene.test import Client

            client = Client(self.schema)
            user_metrics = []

            # Délai de montée en charge
            delay = (user_id / concurrent_users) * ramp_up_seconds
            time.sleep(delay)

            for request_id in range(requests_per_user):
                query = random.choice(queries)

                collector = PerformanceCollector()
                collector.start_collection(
                    f"user_{user_id}_request_{request_id}",
                    {'user_id': user_id, 'request_id': request_id}
                )

                try:
                    start_time = time.time()
                    result = client.execute(query)
                    response_time = (time.time() - start_time) * 1000  # ms

                    metrics = collector.stop_collection()
                    metrics.context['response_time_ms'] = response_time
                    metrics.context['has_errors'] = bool(result.errors)

                    user_metrics.append(metrics)

                    if result.errors:
                        self.error_queue.put({
                            'user_id': user_id,
                            'request_id': request_id,
                            'errors': [str(e) for e in result.errors],
                            'timestamp': time.time()
                        })

                except Exception as e:
                    self.error_queue.put({
                        'user_id': user_id,
                        'request_id': request_id,
                        'exception': str(e),
                        'timestamp': time.time()
                    })

                # Pause entre les requêtes (simulation réaliste)
                time.sleep(random.uniform(0.1, 0.5))

            self.results_queue.put(user_metrics)

        # Lancer les utilisateurs concurrents
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [
                executor.submit(user_simulation, user_id)
                for user_id in range(concurrent_users)
            ]

            # Attendre la completion
            concurrent.futures.wait(futures)

        # Collecter les résultats
        all_metrics = []
        while not self.results_queue.empty():
            user_metrics = self.results_queue.get()
            all_metrics.extend(user_metrics)

        errors = []
        while not self.error_queue.empty():
            errors.append(self.error_queue.get())

        return self.analyze_load_test_results(all_metrics, errors)

    def analyze_load_test_results(self, metrics: List[PerformanceMetrics], errors: List[Dict]):
        """Analyse les résultats du test de charge."""

        if not metrics:
            return {'error': 'Aucune métrique collectée'}

        response_times = [m.context.get('response_time_ms', 0) for m in metrics]
        execution_times = [m.execution_time_seconds * 1000 for m in metrics]  # ms
        memory_usage = [m.memory_usage_mb for m in metrics]
        db_queries = [m.db_query_count for m in metrics]

        return {
            'total_requests': len(metrics),
            'total_errors': len(errors),
            'error_rate': len(errors) / len(metrics) if metrics else 0,

            'response_time_stats': {
                'min_ms': min(response_times),
                'max_ms': max(response_times),
                'avg_ms': sum(response_times) / len(response_times),
                'p95_ms': self._percentile(response_times, 95),
                'p99_ms': self._percentile(response_times, 99),
            },

            'execution_time_stats': {
                'min_ms': min(execution_times),
                'max_ms': max(execution_times),
                'avg_ms': sum(execution_times) / len(execution_times),
            },

            'memory_stats': {
                'min_mb': min(memory_usage),
                'max_mb': max(memory_usage),
                'avg_mb': sum(memory_usage) / len(memory_usage),
            },

            'database_stats': {
                'min_queries': min(db_queries),
                'max_queries': max(db_queries),
                'avg_queries': sum(db_queries) / len(db_queries),
                'total_queries': sum(db_queries),
            },

            'errors': errors[:10],  # Premiers 10 erreurs pour analyse
        }

    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calcule le percentile d'une liste de valeurs."""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]


# Test de charge complet
@pytest.mark.performance
@pytest.mark.slow
def test_concurrent_graphql_operations():
    """Test de charge avec opérations GraphQL concurrentes."""

    # Préparer les données de test
    TestAuthorFactory.create_batch(100)
    TestBookFactory.create_batch(500)

    # Définir les requêtes de test
    queries = [
        """
        query {
            authors(first: 10) {
                edges {
                    node {
                        id
                        firstName
                        lastName
                    }
                }
            }
        }
        """,
        """
        query {
            books(first: 20) {
                edges {
                    node {
                        title
                        author {
                            firstName
                            lastName
                        }
                    }
                }
            }
        }
        """,
        """
        query {
            authors {
                id
                books {
                    title
                    isbn
                }
            }
        }
        """
    ]

    # Exécuter le test de charge
    from tests.schema import schema
    runner = LoadTestRunner(schema)

    results = runner.run_concurrent_queries(
        queries=queries,
        concurrent_users=20,
        requests_per_user=50,
        ramp_up_seconds=5
    )

    # Assertions de performance
    assert results['error_rate'] < 0.05, f"Taux d'erreur trop élevé: {results['error_rate']:.2%}"
    assert results['response_time_stats']['p95_ms'] < 1000, \
        f"P95 trop élevé: {results['response_time_stats']['p95_ms']:.2f}ms"
    assert results['database_stats']['avg_queries'] < 10, \
        f"Trop de requêtes DB en moyenne: {results['database_stats']['avg_queries']:.1f}"

    # Enregistrer les résultats pour analyse
    PerformanceReporter.record_load_test_results(results)
```

## 📈 Profiling et Analyse

### Analyse des Goulots d'Étranglement

```python
import line_profiler
import memory_profiler
from django.db import connection


class PerformanceAnalyzer:
    """Analyseur de performance pour identifier les goulots d'étranglement."""

    @staticmethod
    def profile_schema_generation(models: List):
        """Profile la génération de schéma ligne par ligne."""

        @line_profiler.profile
        def generate_schema():
            from rail_django_graphql.core.generator import AutoSchemaGenerator
            generator = AutoSchemaGenerator()
            return generator.generate_schema(models)

        # Exécuter avec profiling
        schema = generate_schema()

        # Les résultats sont automatiquement affichés par line_profiler
        return schema

    @staticmethod
    def profile_memory_usage():
        """Profile l'utilisation mémoire."""

        @memory_profiler.profile
        def memory_intensive_operation():
            # Créer beaucoup de données
            authors = TestAuthorFactory.create_batch(1000)
            books = TestBookFactory.create_batch(5000)

            # Générer le schéma
            from rail_django_graphql.core.generator import AutoSchemaGenerator
            generator = AutoSchemaGenerator()
            schema = generator.generate_schema([TestAuthor, TestBook])

            return schema, authors, books

        return memory_intensive_operation()

    @staticmethod
    def analyze_database_queries():
        """Analyse les requêtes de base de données."""

        # Activer le logging des requêtes
        from django.conf import settings
        original_debug = settings.DEBUG
        settings.DEBUG = True

        try:
            # Réinitialiser les requêtes
            connection.queries_log.clear()

            # Exécuter une opération
            query = """
            query {
                authors {
                    id
                    firstName
                    books {
                        title
                        category {
                            name
                        }
                    }
                }
            }
            """

            from tests.schema import schema
            from graphene.test import Client

            client = Client(schema)
            result = client.execute(query)

            # Analyser les requêtes
            queries = connection.queries

            analysis = {
                'total_queries': len(queries),
                'total_time': sum(float(q['time']) for q in queries),
                'slow_queries': [
                    q for q in queries
                    if float(q['time']) > 0.1  # Plus de 100ms
                ],
                'duplicate_queries': PerformanceAnalyzer._find_duplicate_queries(queries),
                'n_plus_one_patterns': PerformanceAnalyzer._detect_n_plus_one(queries),
            }

            return analysis, result

        finally:
            settings.DEBUG = original_debug

    @staticmethod
    def _find_duplicate_queries(queries: List[Dict]) -> List[Dict]:
        """Trouve les requêtes dupliquées."""
        query_counts = {}

        for query in queries:
            sql = query['sql']
            if sql in query_counts:
                query_counts[sql] += 1
            else:
                query_counts[sql] = 1

        return [
            {'sql': sql, 'count': count}
            for sql, count in query_counts.items()
            if count > 1
        ]

    @staticmethod
    def _detect_n_plus_one(queries: List[Dict]) -> List[str]:
        """Détecte les patterns N+1."""
        patterns = []

        # Rechercher des patterns de requêtes similaires répétées
        for i, query in enumerate(queries[:-1]):
            similar_count = 1
            base_sql = query['sql']

            # Compter les requêtes similaires qui suivent
            for j in range(i + 1, len(queries)):
                if PerformanceAnalyzer._queries_similar(base_sql, queries[j]['sql']):
                    similar_count += 1
                else:
                    break

            # Si plus de 3 requêtes similaires consécutives, c'est probablement du N+1
            if similar_count > 3:
                patterns.append(f"Possible N+1 pattern: {similar_count} requêtes similaires à partir de l'index {i}")

        return patterns

    @staticmethod
    def _queries_similar(sql1: str, sql2: str) -> bool:
        """Détermine si deux requêtes SQL sont similaires (même structure)."""
        # Simplification: remplacer les valeurs par des placeholders
        import re

        # Remplacer les nombres et chaînes par des placeholders
        normalized1 = re.sub(r'\d+', 'N', sql1)
        normalized1 = re.sub(r"'[^']*'", "'X'", normalized1)

        normalized2 = re.sub(r'\d+', 'N', sql2)
        normalized2 = re.sub(r"'[^']*'", "'X'", normalized2)

        return normalized1 == normalized2
```

## 🎯 Optimisation

### Stratégies d'Optimisation

```python
class PerformanceOptimizer:
    """Optimiseur de performance pour Django GraphQL Auto."""

    @staticmethod
    def optimize_schema_generation():
        """Optimisations pour la génération de schéma."""

        # 1. Cache des métadonnées de modèles
        model_cache = {}

        def cached_model_introspection(model_class):
            if model_class not in model_cache:
                introspector = ModelIntrospector()
                model_cache[model_class] = introspector.analyze_model(model_class)
            return model_cache[model_class]

        # 2. Génération paresseuse des types
        type_registry = {}

        def lazy_type_generation(model_class):
            if model_class not in type_registry:
                generator = TypeGenerator()
                type_registry[model_class] = generator.generate_type(model_class)
            return type_registry[model_class]

        return {
            'cached_introspection': cached_model_introspection,
            'lazy_type_generation': lazy_type_generation,
        }

    @staticmethod
    def optimize_query_execution():
        """Optimisations pour l'exécution de requêtes."""

        # 1. Prefetch automatique des relations
        def auto_prefetch_resolver(model_class, field_name):
            def resolver(root, info, **kwargs):
                # Analyser la requête GraphQL pour déterminer les prefetch nécessaires
                selections = info.field_nodes[0].selection_set.selections
                prefetch_fields = []

                for selection in selections:
                    if hasattr(model_class, selection.name.value):
                        field = model_class._meta.get_field(selection.name.value)
                        if field.is_relation:
                            prefetch_fields.append(selection.name.value)

                # Exécuter la requête avec prefetch
                queryset = model_class.objects.all()
                if prefetch_fields:
                    queryset = queryset.prefetch_related(*prefetch_fields)

                return queryset

            return resolver

        # 2. Cache de requêtes
        query_cache = {}

        def cached_query_resolver(cache_key_func):
            def decorator(resolver_func):
                def wrapper(root, info, **kwargs):
                    cache_key = cache_key_func(root, info, **kwargs)

                    if cache_key in query_cache:
                        return query_cache[cache_key]

                    result = resolver_func(root, info, **kwargs)
                    query_cache[cache_key] = result
                    return result

                return wrapper
            return decorator

        return {
            'auto_prefetch_resolver': auto_prefetch_resolver,
            'cached_query_resolver': cached_query_resolver,
        }

    @staticmethod
    def optimize_database_access():
        """Optimisations pour l'accès à la base de données."""

        # 1. Détection automatique des select_related
        def smart_select_related(queryset, info):
            """Ajoute automatiquement select_related basé sur la requête GraphQL."""
            selections = info.field_nodes[0].selection_set.selections
            select_fields = []

            for selection in selections:
                field_name = selection.name.value
                if hasattr(queryset.model, field_name):
                    field = queryset.model._meta.get_field(field_name)
                    if field.many_to_one or field.one_to_one:
                        select_fields.append(field_name)

            if select_fields:
                queryset = queryset.select_related(*select_fields)

            return queryset

        # 2. Pagination optimisée
        def optimized_pagination(queryset, first=None, after=None):
            """Pagination optimisée avec curseurs."""
            if after:
                # Décoder le curseur
                cursor_value = base64.b64decode(after).decode()
                queryset = queryset.filter(id__gt=cursor_value)

            if first:
                queryset = queryset[:first + 1]  # +1 pour détecter s'il y a une page suivante

            return queryset

        return {
            'smart_select_related': smart_select_related,
            'optimized_pagination': optimized_pagination,
        }


# Tests d'optimisation
@pytest.mark.performance
class TestOptimizations:
    """Tests des optimisations de performance."""

    def test_cached_schema_generation_performance(self):
        """Test de performance avec cache de schéma."""
        models = [TestAuthor, TestBook, TestCategory]

        # Première génération (sans cache)
        start_time = time.time()
        generator1 = AutoSchemaGenerator()
        schema1 = generator1.generate_schema(models)
        first_generation_time = time.time() - start_time

        # Deuxième génération (avec cache)
        optimizer = PerformanceOptimizer()
        optimizations = optimizer.optimize_schema_generation()

        start_time = time.time()
        generator2 = AutoSchemaGenerator()
        # Appliquer les optimisations
        schema2 = generator2.generate_schema(models)
        second_generation_time = time.time() - start_time

        # La deuxième génération devrait être plus rapide
        assert second_generation_time < first_generation_time * 0.8, \
            f"Optimisation insuffisante: {second_generation_time:.3f}s vs {first_generation_time:.3f}s"

    def test_query_optimization_reduces_db_calls(self):
        """Test que les optimisations réduisent les appels DB."""
        # Créer des données avec relations
        authors = TestAuthorFactory.create_batch(10)
        for author in authors:
            TestBookFactory.create_batch(5, author=author)

        query = """
        query {
            authors {
                id
                firstName
                books {
                    title
                    isbn
                }
            }
        }
        """

        # Exécution sans optimisation
        connection.queries_log.clear()
        from tests.schema import schema
        from graphene.test import Client

        client = Client(schema)
        result1 = client.execute(query)
        queries_without_optimization = len(connection.queries)

        # Exécution avec optimisation
        connection.queries_log.clear()
        optimizer = PerformanceOptimizer()
        optimizations = optimizer.optimize_query_execution()

        # Appliquer les optimisations au schéma
        # (Ceci nécessiterait une intégration plus profonde dans le générateur)

        result2 = client.execute(query)
        queries_with_optimization = len(connection.queries)

        # Vérifier que l'optimisation réduit les requêtes
        assert queries_with_optimization < queries_without_optimization, \
            f"Optimisation inefficace: {queries_with_optimization} vs {queries_without_optimization} requêtes"
```

## 📊 Monitoring Continu

### Collecte de Métriques en Production

```python
class ProductionPerformanceMonitor:
    """Moniteur de performance pour l'environnement de production."""

    def __init__(self):
        self.metrics_storage = []
        self.alert_thresholds = PERFORMANCE_THRESHOLDS

    def monitor_graphql_operation(self, operation_type: str):
        """Décorateur pour monitorer les opérations GraphQL."""

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                collector = PerformanceCollector()
                collector.start_collection(
                    f"{operation_type}_{func.__name__}",
                    {'operation_type': operation_type}
                )

                try:
                    result = func(*args, **kwargs)
                    metrics = collector.stop_collection()

                    # Vérifier les seuils d'alerte
                    self._check_alert_thresholds(metrics)

                    # Stocker les métriques
                    self._store_metrics(metrics)

                    return result

                except Exception as e:
                    metrics = collector.stop_collection()
                    metrics.context['exception'] = str(e)
                    self._store_metrics(metrics)
                    raise

            return wrapper
        return decorator

    def _check_alert_thresholds(self, metrics: PerformanceMetrics):
        """Vérifie les seuils d'alerte et envoie des notifications."""

        alerts = []

        # Vérifier le temps d'exécution
        if 'query_execution' in metrics.test_name:
            threshold = self.alert_thresholds['query_execution']['complex_query_ms'] / 1000
            if metrics.execution_time_seconds > threshold:
                alerts.append(f"Requête lente détectée: {metrics.execution_time_seconds:.2f}s")

        # Vérifier l'utilisation mémoire
        if metrics.memory_growth_mb > 100:  # Plus de 100MB de croissance
            alerts.append(f"Croissance mémoire excessive: {metrics.memory_growth_mb:.2f}MB")

        # Vérifier les requêtes DB
        if metrics.db_query_count > 20:
            alerts.append(f"Trop de requêtes DB: {metrics.db_query_count}")

        # Envoyer les alertes
        for alert in alerts:
            self._send_alert(alert, metrics)

    def _send_alert(self, message: str, metrics: PerformanceMetrics):
        """Envoie une alerte de performance."""
        # Intégration avec système d'alertes (Slack, email, etc.)
        import logging

        logger = logging.getLogger('performance_alerts')
        logger.warning(f"ALERTE PERFORMANCE: {message}", extra={
            'test_name': metrics.test_name,
            'execution_time': metrics.execution_time_seconds,
            'memory_usage': metrics.memory_usage_mb,
            'db_queries': metrics.db_query_count,
            'timestamp': metrics.timestamp,
        })

    def _store_metrics(self, metrics: PerformanceMetrics):
        """Stocke les métriques pour analyse historique."""
        # Intégration avec système de métriques (InfluxDB, Prometheus, etc.)
        self.metrics_storage.append(metrics)

        # Nettoyer les anciennes métriques (garder seulement les 1000 dernières)
        if len(self.metrics_storage) > 1000:
            self.metrics_storage = self.metrics_storage[-1000:]

    def generate_performance_report(self, time_range_hours: int = 24):
        """Génère un rapport de performance."""

        cutoff_time = time.time() - (time_range_hours * 3600)
        recent_metrics = [
            m for m in self.metrics_storage
            if m.timestamp > cutoff_time
        ]

        if not recent_metrics:
            return {'error': 'Aucune métrique disponible'}

        return {
            'time_range_hours': time_range_hours,
            'total_operations': len(recent_metrics),
            'avg_execution_time': sum(m.execution_time_seconds for m in recent_metrics) / len(recent_metrics),
            'avg_memory_usage': sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics),
            'total_db_queries': sum(m.db_query_count for m in recent_metrics),
            'error_rate': sum(1 for m in recent_metrics if m.error_count > 0) / len(recent_metrics),
            'slowest_operations': sorted(
                recent_metrics,
                key=lambda m: m.execution_time_seconds,
                reverse=True
            )[:10],
        }


# Intégration avec Django
monitor = ProductionPerformanceMonitor()

@monitor.monitor_graphql_operation('query')
def execute_graphql_query(schema, query, variables=None):
    """Exécution monitorée de requêtes GraphQL."""
    from graphene.test import Client

    client = Client(schema)
    return client.execute(query, variables=variables)
```

Ce guide fournit une approche complète pour tester et optimiser les performances du système Django GraphQL Auto. Adaptez ces techniques selon vos besoins spécifiques et votre environnement de production.
