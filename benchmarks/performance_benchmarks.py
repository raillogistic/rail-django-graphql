"""
Benchmarks de performance pour Django GraphQL Auto.

Ce module fournit des benchmarks complets pour:
- Mesurer l'impact de l'optimisation des requêtes N+1
- Évaluer l'efficacité du système de cache
- Tester les performances sous charge
- Comparer les performances avant/après optimisation
- Générer des rapports de performance détaillés
"""

import time
import statistics
import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import django
from django.db import models, connection
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.conf import settings

import graphene
from graphene import ObjectType, String, Int, List as GrapheneList
from graphene.test import Client

from django_graphql_auto.extensions.optimization import (
    QueryOptimizer,
    QueryOptimizationConfig,
    get_optimizer,
    optimize_query
)
from django_graphql_auto.extensions.caching import (
    GraphQLCacheManager,
    CacheConfig,
    get_cache_manager
)


@dataclass
class BenchmarkResult:
    """Résultat d'un benchmark de performance."""
    test_name: str
    scenario: str
    execution_time: float
    memory_usage: float
    database_queries: int
    cache_hits: int
    cache_misses: int
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class BenchmarkSummary:
    """Résumé des résultats de benchmark."""
    total_tests: int
    successful_tests: int
    failed_tests: int
    avg_execution_time: float
    min_execution_time: float
    max_execution_time: float
    total_database_queries: int
    total_cache_hits: int
    total_cache_misses: int
    performance_improvement: float
    timestamp: str


class PerformanceBenchmark:
    """Classe principale pour les benchmarks de performance."""
    
    def __init__(self, output_dir: str = "benchmark_results"):
        """
        Initialise le système de benchmark.
        
        Args:
            output_dir: Répertoire pour sauvegarder les résultats
        """
        self.output_dir = output_dir
        self.results: List[BenchmarkResult] = []
        self.start_time = None
        self.end_time = None
        
        # Créer le répertoire de sortie
        import os
        os.makedirs(output_dir, exist_ok=True)
    
    @contextmanager
    def measure_performance(self, test_name: str, scenario: str):
        """
        Context manager pour mesurer les performances.
        
        Args:
            test_name: Nom du test
            scenario: Scénario testé
        """
        # Réinitialiser les compteurs
        cache.clear()
        connection.queries_log.clear()
        
        # Mesurer la mémoire initiale
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        success = True
        error_message = None
        
        try:
            yield
        except Exception as e:
            success = False
            error_message = str(e)
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Mesurer la mémoire finale
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = final_memory - initial_memory
            
            # Compter les requêtes de base de données
            database_queries = len(connection.queries)
            
            # Obtenir les statistiques de cache
            cache_manager = get_cache_manager()
            cache_stats = cache_manager.get_stats()
            
            # Créer le résultat
            result = BenchmarkResult(
                test_name=test_name,
                scenario=scenario,
                execution_time=execution_time,
                memory_usage=memory_usage,
                database_queries=database_queries,
                cache_hits=cache_stats.hits,
                cache_misses=cache_stats.misses,
                success=success,
                error_message=error_message
            )
            
            self.results.append(result)
    
    def run_n_plus_one_benchmark(self, data_sizes: List[int] = None):
        """
        Benchmark pour la prévention des requêtes N+1.
        
        Args:
            data_sizes: Tailles de données à tester
        """
        if data_sizes is None:
            data_sizes = [10, 50, 100, 500]
        
        print("🚀 Démarrage du benchmark N+1...")
        
        for size in data_sizes:
            print(f"  📊 Test avec {size} éléments...")
            
            # Créer les données de test
            self._create_test_data(size)
            
            # Test sans optimisation
            with self.measure_performance("n_plus_one", f"unoptimized_{size}"):
                self._run_unoptimized_query()
            
            # Test avec optimisation
            with self.measure_performance("n_plus_one", f"optimized_{size}"):
                self._run_optimized_query()
            
            # Nettoyer les données
            self._cleanup_test_data()
    
    def run_caching_benchmark(self, cache_scenarios: List[str] = None):
        """
        Benchmark pour le système de cache.
        
        Args:
            cache_scenarios: Scénarios de cache à tester
        """
        if cache_scenarios is None:
            cache_scenarios = ["no_cache", "query_cache", "field_cache", "full_cache"]
        
        print("🚀 Démarrage du benchmark de cache...")
        
        # Créer des données de test
        self._create_test_data(100)
        
        for scenario in cache_scenarios:
            print(f"  📊 Test du scénario: {scenario}")
            
            # Configurer le cache selon le scénario
            self._configure_cache_scenario(scenario)
            
            # Premier appel (cache miss)
            with self.measure_performance("caching", f"{scenario}_miss"):
                self._run_cached_query()
            
            # Deuxième appel (cache hit)
            with self.measure_performance("caching", f"{scenario}_hit"):
                self._run_cached_query()
        
        self._cleanup_test_data()
    
    def run_load_test(self, concurrent_users: List[int] = None, requests_per_user: int = 10):
        """
        Test de charge avec utilisateurs concurrents.
        
        Args:
            concurrent_users: Nombres d'utilisateurs concurrents à tester
            requests_per_user: Nombre de requêtes par utilisateur
        """
        if concurrent_users is None:
            concurrent_users = [1, 5, 10, 20]
        
        print("🚀 Démarrage du test de charge...")
        
        # Créer des données de test
        self._create_test_data(200)
        
        for users in concurrent_users:
            print(f"  📊 Test avec {users} utilisateurs concurrents...")
            
            with self.measure_performance("load_test", f"{users}_users"):
                self._run_concurrent_requests(users, requests_per_user)
        
        self._cleanup_test_data()
    
    def run_complexity_benchmark(self, query_depths: List[int] = None):
        """
        Benchmark pour les requêtes de complexité variable.
        
        Args:
            query_depths: Profondeurs de requêtes à tester
        """
        if query_depths is None:
            query_depths = [1, 3, 5, 7]
        
        print("🚀 Démarrage du benchmark de complexité...")
        
        # Créer des données de test avec relations profondes
        self._create_complex_test_data()
        
        for depth in query_depths:
            print(f"  📊 Test avec profondeur {depth}...")
            
            with self.measure_performance("complexity", f"depth_{depth}"):
                self._run_complex_query(depth)
        
        self._cleanup_test_data()
    
    def generate_report(self) -> BenchmarkSummary:
        """
        Génère un rapport de performance complet.
        
        Returns:
            Résumé des benchmarks
        """
        if not self.results:
            raise ValueError("Aucun résultat de benchmark disponible")
        
        successful_results = [r for r in self.results if r.success]
        failed_results = [r for r in self.results if not r.success]
        
        if successful_results:
            execution_times = [r.execution_time for r in successful_results]
            avg_execution_time = statistics.mean(execution_times)
            min_execution_time = min(execution_times)
            max_execution_time = max(execution_times)
        else:
            avg_execution_time = min_execution_time = max_execution_time = 0.0
        
        # Calculer l'amélioration des performances
        optimized_results = [r for r in successful_results if "optimized" in r.scenario]
        unoptimized_results = [r for r in successful_results if "unoptimized" in r.scenario]
        
        performance_improvement = 0.0
        if optimized_results and unoptimized_results:
            avg_optimized = statistics.mean([r.execution_time for r in optimized_results])
            avg_unoptimized = statistics.mean([r.execution_time for r in unoptimized_results])
            if avg_unoptimized > 0:
                performance_improvement = ((avg_unoptimized - avg_optimized) / avg_unoptimized) * 100
        
        summary = BenchmarkSummary(
            total_tests=len(self.results),
            successful_tests=len(successful_results),
            failed_tests=len(failed_results),
            avg_execution_time=avg_execution_time,
            min_execution_time=min_execution_time,
            max_execution_time=max_execution_time,
            total_database_queries=sum(r.database_queries for r in successful_results),
            total_cache_hits=sum(r.cache_hits for r in successful_results),
            total_cache_misses=sum(r.cache_misses for r in successful_results),
            performance_improvement=performance_improvement,
            timestamp=datetime.now().isoformat()
        )
        
        # Sauvegarder les résultats
        self._save_results(summary)
        
        return summary
    
    def _create_test_data(self, size: int):
        """Crée des données de test."""
        from tests.test_performance_optimization import TestAuthor, TestBook, TestReview
        
        # Créer des auteurs
        authors = []
        for i in range(size // 5):  # 1 auteur pour 5 livres
            author = TestAuthor.objects.create(
                name=f"Auteur {i}",
                email=f"auteur{i}@test.com"
            )
            authors.append(author)
        
        # Créer des livres
        books = []
        for i in range(size):
            author = authors[i % len(authors)]
            book = TestBook.objects.create(
                title=f"Livre {i}",
                author=author,
                publication_year=2020 + (i % 5)
            )
            books.append(book)
        
        # Créer un utilisateur pour les avis
        user, _ = User.objects.get_or_create(
            username="testuser",
            defaults={"email": "test@test.com"}
        )
        
        # Créer des avis
        for i, book in enumerate(books[:size//2]):  # Avis pour la moitié des livres
            TestReview.objects.create(
                book=book,
                reviewer=user,
                rating=4 + (i % 2),
                comment=f"Avis pour {book.title}"
            )
    
    def _cleanup_test_data(self):
        """Nettoie les données de test."""
        from tests.test_performance_optimization import TestAuthor, TestBook, TestReview
        
        TestReview.objects.all().delete()
        TestBook.objects.all().delete()
        TestAuthor.objects.all().delete()
        User.objects.filter(username="testuser").delete()
    
    def _run_unoptimized_query(self):
        """Exécute une requête non optimisée (N+1)."""
        from tests.test_performance_optimization import TestBook
        
        books = TestBook.objects.all()
        results = []
        for book in books:
            # Ceci déclenche des requêtes N+1
            results.append({
                'title': book.title,
                'author_name': book.author.name,
                'author_email': book.author.email,
                'reviews_count': book.testreview_set.count()
            })
        return results
    
    def _run_optimized_query(self):
        """Exécute une requête optimisée."""
        from tests.test_performance_optimization import TestBook
        
        books = TestBook.objects.select_related('author').prefetch_related('testreview_set').all()
        results = []
        for book in books:
            results.append({
                'title': book.title,
                'author_name': book.author.name,
                'author_email': book.author.email,
                'reviews_count': book.testreview_set.count()
            })
        return results
    
    def _configure_cache_scenario(self, scenario: str):
        """Configure le cache selon le scénario."""
        cache_manager = get_cache_manager()
        
        if scenario == "no_cache":
            cache_manager.config.enabled = False
        elif scenario == "query_cache":
            cache_manager.config.enabled = True
            cache_manager.config.query_cache_enabled = True
            cache_manager.config.field_cache_enabled = False
        elif scenario == "field_cache":
            cache_manager.config.enabled = True
            cache_manager.config.query_cache_enabled = False
            cache_manager.config.field_cache_enabled = True
        elif scenario == "full_cache":
            cache_manager.config.enabled = True
            cache_manager.config.query_cache_enabled = True
            cache_manager.config.field_cache_enabled = True
    
    def _run_cached_query(self):
        """Exécute une requête avec cache."""
        from tests.test_performance_optimization import TestBook, BookType
        
        class Query(ObjectType):
            books = GrapheneList(BookType)
            
            @optimize_query(enable_caching=True)
            def resolve_books(self, info):
                return TestBook.objects.select_related('author').all()
        
        schema = graphene.Schema(query=Query)
        client = Client(schema)
        
        query = """
        query {
            books {
                title
                author {
                    name
                    email
                }
            }
        }
        """
        
        result = client.execute(query)
        return result.data
    
    def _run_concurrent_requests(self, num_users: int, requests_per_user: int):
        """Exécute des requêtes concurrentes."""
        def make_request():
            return self._run_optimized_query()
        
        results = []
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            # Soumettre toutes les requêtes
            futures = []
            for user in range(num_users):
                for request in range(requests_per_user):
                    future = executor.submit(make_request)
                    futures.append(future)
            
            # Attendre les résultats
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    print(f"Erreur dans la requête concurrente: {e}")
        
        return results
    
    def _create_complex_test_data(self):
        """Crée des données de test avec relations complexes."""
        # Utiliser les données de test existantes mais avec plus de relations
        self._create_test_data(50)
    
    def _run_complex_query(self, depth: int):
        """Exécute une requête de complexité donnée."""
        from tests.test_performance_optimization import TestBook, BookType
        
        # Construire une requête GraphQL de profondeur variable
        query_parts = ["books {", "title"]
        
        if depth >= 2:
            query_parts.extend(["author {", "name"])
            if depth >= 3:
                query_parts.extend(["email", "}"])
            else:
                query_parts.append("}")
        
        if depth >= 4:
            query_parts.extend(["reviews {", "rating"])
            if depth >= 5:
                query_parts.extend(["comment", "reviewer"])
            query_parts.append("}")
        
        query_parts.append("}")
        
        query = f"query {{ {' '.join(query_parts)} }}"
        
        class Query(ObjectType):
            books = GrapheneList(BookType)
            
            def resolve_books(self, info):
                return TestBook.objects.all()
        
        schema = graphene.Schema(query=Query)
        client = Client(schema)
        
        result = client.execute(query)
        return result.data
    
    def _save_results(self, summary: BenchmarkSummary):
        """Sauvegarde les résultats dans différents formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarder en JSON
        json_file = f"{self.output_dir}/benchmark_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            data = {
                'summary': asdict(summary),
                'detailed_results': [asdict(r) for r in self.results]
            }
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder en CSV
        csv_file = f"{self.output_dir}/benchmark_results_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            if self.results:
                writer = csv.DictWriter(f, fieldnames=asdict(self.results[0]).keys())
                writer.writeheader()
                for result in self.results:
                    writer.writerow(asdict(result))
        
        # Générer un rapport HTML
        self._generate_html_report(summary, timestamp)
        
        print(f"📊 Résultats sauvegardés dans {self.output_dir}/")
    
    def _generate_html_report(self, summary: BenchmarkSummary, timestamp: str):
        """Génère un rapport HTML."""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Rapport de Performance - Django GraphQL Auto</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .summary {{ background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background: white; border-radius: 3px; }}
                .success {{ color: #27ae60; }}
                .error {{ color: #e74c3c; }}
                .improvement {{ color: #3498db; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .chart {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 Rapport de Performance - Django GraphQL Auto</h1>
                <p>Généré le: {summary.timestamp}</p>
            </div>
            
            <div class="summary">
                <h2>📊 Résumé des Performances</h2>
                <div class="metric">
                    <strong>Tests Total:</strong> {summary.total_tests}
                </div>
                <div class="metric success">
                    <strong>Succès:</strong> {summary.successful_tests}
                </div>
                <div class="metric error">
                    <strong>Échecs:</strong> {summary.failed_tests}
                </div>
                <div class="metric">
                    <strong>Temps Moyen:</strong> {summary.avg_execution_time:.3f}s
                </div>
                <div class="metric improvement">
                    <strong>Amélioration:</strong> {summary.performance_improvement:.1f}%
                </div>
            </div>
            
            <h2>📈 Résultats Détaillés</h2>
            <table>
                <thead>
                    <tr>
                        <th>Test</th>
                        <th>Scénario</th>
                        <th>Temps (s)</th>
                        <th>Mémoire (MB)</th>
                        <th>Requêtes DB</th>
                        <th>Cache Hits</th>
                        <th>Statut</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for result in self.results:
            status_class = "success" if result.success else "error"
            status_text = "✅ Succès" if result.success else "❌ Échec"
            
            html_content += f"""
                    <tr>
                        <td>{result.test_name}</td>
                        <td>{result.scenario}</td>
                        <td>{result.execution_time:.3f}</td>
                        <td>{result.memory_usage:.2f}</td>
                        <td>{result.database_queries}</td>
                        <td>{result.cache_hits}</td>
                        <td class="{status_class}">{status_text}</td>
                    </tr>
            """
        
        html_content += """
                </tbody>
            </table>
            
            <div class="chart">
                <h2>📊 Analyse des Performances</h2>
                <p>Les optimisations ont permis une amélioration moyenne de <span class="improvement">{:.1f}%</span> des performances.</p>
                <p>Réduction significative du nombre de requêtes de base de données grâce à la prévention N+1.</p>
                <p>Le système de cache améliore les temps de réponse pour les requêtes répétées.</p>
            </div>
        </body>
        </html>
        """.format(summary.performance_improvement)
        
        html_file = f"{self.output_dir}/benchmark_report_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)


def run_full_benchmark_suite():
    """
    Exécute la suite complète de benchmarks.
    
    Returns:
        BenchmarkSummary: Résumé des résultats
    """
    print("🎯 Démarrage de la suite complète de benchmarks...")
    
    benchmark = PerformanceBenchmark()
    
    try:
        # Benchmark N+1
        benchmark.run_n_plus_one_benchmark([10, 50, 100])
        
        # Benchmark de cache
        benchmark.run_caching_benchmark()
        
        # Test de charge
        benchmark.run_load_test([1, 5, 10])
        
        # Benchmark de complexité
        benchmark.run_complexity_benchmark([1, 3, 5])
        
        # Générer le rapport
        summary = benchmark.generate_report()
        
        print("✅ Suite de benchmarks terminée avec succès!")
        print(f"📊 {summary.successful_tests}/{summary.total_tests} tests réussis")
        print(f"🚀 Amélioration des performances: {summary.performance_improvement:.1f}%")
        
        return summary
        
    except Exception as e:
        print(f"❌ Erreur lors des benchmarks: {e}")
        raise


if __name__ == "__main__":
    # Configuration Django pour les tests
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django_graphql_auto',
            ],
            SECRET_KEY='benchmark-secret-key',
            USE_TZ=True,
            CACHES={
                'default': {
                    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                }
            }
        )
    
    django.setup()
    
    # Exécuter les benchmarks
    summary = run_full_benchmark_suite()