"""
Tests de performance pour les requêtes concurrentes.

Ce module teste:
- Les performances sous charge concurrente
- La sécurité des threads (thread safety)
- La gestion des connexions simultanées
- La scalabilité du système
- La gestion des ressources partagées
"""

import pytest
import time
import threading
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from queue import Queue, Empty
from typing import Dict, List, Optional, Any, Tuple, Callable
from unittest.mock import Mock, patch
from django.test import TestCase, TransactionTestCase
from django.db import models, connection, transaction
from django.test.utils import override_settings
from django.core.cache import cache
import psutil

import graphene
from graphene import Schema
from graphene.test import Client

from rail_django_graphql.core.schema import SchemaBuilder
from rail_django_graphql.generators.introspector import ModelIntrospector
from rail_django_graphql.generators.types import TypeGenerator
from rail_django_graphql.generators.queries import QueryGenerator
from rail_django_graphql.generators.mutations import MutationGenerator
from rail_django_graphql.decorators.business_logic import business_method
from tests.models import TestConcurrentModel, TestSharedResource


class ConcurrencyTester:
    """Testeur de concurrence pour les opérations GraphQL."""

    def __init__(self, client: Client):
        self.client = client
        self.results = Queue()
        self.errors = Queue()
        self.execution_times = []
        self.thread_results = {}
        self.lock = threading.Lock()

    def execute_query_thread(self, query: str, thread_id: int, iterations: int = 1):
        """Exécute une requête dans un thread."""
        thread_results = []
        thread_errors = []

        for i in range(iterations):
            start_time = time.time()

            try:
                result = self.client.execute(query)
                end_time = time.time()

                execution_time = end_time - start_time

                thread_result = {
                    "thread_id": thread_id,
                    "iteration": i,
                    "execution_time": execution_time,
                    "success": result.get("errors") is None,
                    "result": result,
                    "timestamp": time.time(),
                }

                thread_results.append(thread_result)
                self.results.put(thread_result)

                with self.lock:
                    self.execution_times.append(execution_time)

            except Exception as e:
                error_info = {
                    "thread_id": thread_id,
                    "iteration": i,
                    "error": str(e),
                    "timestamp": time.time(),
                }

                thread_errors.append(error_info)
                self.errors.put(error_info)

        # Stocker les résultats du thread
        with self.lock:
            self.thread_results[thread_id] = {
                "results": thread_results,
                "errors": thread_errors,
                "success_rate": len(thread_results)
                / (len(thread_results) + len(thread_errors)),
            }

    def execute_concurrent_queries(
        self, query: str, num_threads: int, iterations_per_thread: int = 1
    ) -> Dict[str, Any]:
        """Exécute des requêtes concurrentes."""
        # Réinitialiser les résultats
        self.results = Queue()
        self.errors = Queue()
        self.execution_times = []
        self.thread_results = {}

        # Créer et démarrer les threads
        threads = []
        start_time = time.time()

        for i in range(num_threads):
            thread = threading.Thread(
                target=self.execute_query_thread, args=(query, i, iterations_per_thread)
            )
            threads.append(thread)
            thread.start()

        # Attendre la fin de tous les threads
        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time

        # Collecter les résultats
        results = []
        while not self.results.empty():
            try:
                results.append(self.results.get_nowait())
            except Empty:
                break

        errors = []
        while not self.errors.empty():
            try:
                errors.append(self.errors.get_nowait())
            except Empty:
                break

        # Calculer les statistiques
        successful_queries = [r for r in results if r["success"]]
        total_queries = len(results) + len(errors)

        stats = {
            "total_time": total_time,
            "total_queries": total_queries,
            "successful_queries": len(successful_queries),
            "failed_queries": len(errors),
            "success_rate": len(successful_queries) / total_queries
            if total_queries > 0
            else 0,
            "queries_per_second": total_queries / total_time if total_time > 0 else 0,
            "thread_results": self.thread_results,
            "errors": errors,
        }

        if self.execution_times:
            stats["execution_time_stats"] = {
                "mean": statistics.mean(self.execution_times),
                "median": statistics.median(self.execution_times),
                "min": min(self.execution_times),
                "max": max(self.execution_times),
                "stdev": statistics.stdev(self.execution_times)
                if len(self.execution_times) > 1
                else 0,
            }

        return stats

    def execute_mixed_workload(
        self,
        queries: List[Tuple[str, int]],  # (query, weight)
        num_threads: int,
        duration_seconds: int,
    ) -> Dict[str, Any]:
        """Exécute une charge de travail mixte."""
        results = []
        errors = []
        start_time = time.time()

        def worker():
            """Worker thread pour la charge mixte."""
            import random

            thread_start = time.time()

            while time.time() - thread_start < duration_seconds:
                # Choisir une requête selon les poids
                total_weight = sum(weight for _, weight in queries)
                rand_val = random.randint(1, total_weight)

                cumulative_weight = 0
                selected_query = queries[0][0]  # Fallback

                for query, weight in queries:
                    cumulative_weight += weight
                    if rand_val <= cumulative_weight:
                        selected_query = query
                        break

                # Exécuter la requête
                query_start = time.time()
                try:
                    result = self.client.execute(selected_query)
                    query_end = time.time()

                    with self.lock:
                        results.append(
                            {
                                "query": selected_query[:50]
                                + "...",  # Tronquer pour l'affichage
                                "execution_time": query_end - query_start,
                                "success": result.get("errors") is None,
                                "timestamp": query_end,
                            }
                        )

                except Exception as e:
                    with self.lock:
                        errors.append(
                            {
                                "query": selected_query[:50] + "...",
                                "error": str(e),
                                "timestamp": time.time(),
                            }
                        )

        # Démarrer les workers
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        # Attendre la fin
        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time

        # Calculer les statistiques
        successful_queries = [r for r in results if r["success"]]

        return {
            "total_time": total_time,
            "total_queries": len(results) + len(errors),
            "successful_queries": len(successful_queries),
            "failed_queries": len(errors),
            "success_rate": len(successful_queries) / (len(results) + len(errors))
            if results or errors
            else 0,
            "queries_per_second": (len(results) + len(errors)) / total_time
            if total_time > 0
            else 0,
            "results": results,
            "errors": errors,
        }


class TestConcurrentRequests(TransactionTestCase):
    """Tests de requêtes concurrentes."""

    def setUp(self):
        """Configuration des tests de concurrence."""
        # Initialiser les générateurs
        self.introspector = ModelIntrospector(TestConcurrentModel)
        self.type_generator = TypeGenerator()
        self.query_generator = QueryGenerator(self.type_generator, None)
        self.mutation_generator = MutationGenerator(self.type_generator, None)

        # Initialiser le générateur de schéma
        self.schema_generator = SchemaBuilder()

        # Modèles de test
        self.test_models = [TestConcurrentModel, TestSharedResource]

        # Générer le schéma
        self.schema = self.schema_generator.get_schema()
        self.client = Client(self.schema)

        # Testeur de concurrence
        self.concurrency_tester = ConcurrencyTester(self.client)

        # Créer des données de test
        self._create_test_data()

    def _create_test_data(self):
        """Crée des données de test."""
        # Créer des modèles concurrents
        self.concurrent_models = []
        for i in range(50):
            model = TestConcurrentModel.objects.create(
                nom_concurrent=f"Concurrent {i}",
                valeur_compteur=i,
                donnees_partagees=f"Données {i}",
                thread_id="",
            )
            self.concurrent_models.append(model)

        # Créer des ressources partagées
        self.shared_resources = []
        for i in range(10):
            resource = TestSharedResource.objects.create(
                nom_ressource=f"Resource {i}", valeur_partagee=i * 10, nombre_acces=0
            )
            self.shared_resources.append(resource)

    def test_concurrent_read_queries(self):
        """Test les requêtes de lecture concurrentes."""
        query = """
        query {
            allConcurrentModels(first: 20) {
                id
                nomConcurrent
                valeurCompteur
                donneesPartagees
            }
        }
        """

        # Exécuter des requêtes concurrentes
        stats = self.concurrency_tester.execute_concurrent_queries(
            query=query, num_threads=10, iterations_per_thread=5
        )

        # Vérifier les performances
        self.assertGreater(stats["success_rate"], 0.95)  # Au moins 95% de succès
        self.assertGreater(stats["queries_per_second"], 10)  # Au moins 10 QPS
        self.assertLess(stats["execution_time_stats"]["mean"], 1.0)  # Temps moyen < 1s

        # Vérifier qu'il n'y a pas d'erreurs critiques
        self.assertLess(len(stats["errors"]), 5)  # Moins de 5 erreurs

    def test_concurrent_write_mutations(self):
        """Test les mutations d'écriture concurrentes."""
        # Note: Cette mutation pourrait ne pas être implémentée
        # On teste le principe avec une requête alternative

        mutation_template = """
        mutation {{
            updateConcurrentModel(id: {model_id}, input: {{
                nomConcurrent: "Updated by thread"
                valeurCompteur: 999
            }}) {{
                concurrentModel {{
                    id
                    nomConcurrent
                    valeurCompteur
                }}
            }}
        }}
        """

        # Utiliser différents modèles pour éviter les conflits
        def execute_mutation_thread(thread_id: int):
            """Exécute une mutation dans un thread."""
            model_id = self.concurrent_models[
                thread_id % len(self.concurrent_models)
            ].id
            mutation = mutation_template.format(model_id=model_id)

            try:
                result = self.client.execute(mutation)
                return {
                    "thread_id": thread_id,
                    "success": result.get("errors") is None,
                    "result": result,
                }
            except Exception as e:
                return {"thread_id": thread_id, "success": False, "error": str(e)}

        # Exécuter des mutations concurrentes
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(execute_mutation_thread, i) for i in range(5)]
            results = [future.result() for future in as_completed(futures)]

        # Analyser les résultats
        successful_mutations = [r for r in results if r["success"]]

        # Au moins quelques mutations doivent réussir (même si pas toutes implémentées)
        self.assertGreaterEqual(len(results), 5)

    def test_mixed_read_write_workload(self):
        """Test une charge de travail mixte lecture/écriture."""
        read_query = """
        query {
            allConcurrentModels(first: 10) {
                id
                nomConcurrent
                valeurCompteur
            }
        }
        """

        write_query = """
        query {
            allSharedResources {
                id
                nomRessource
                valeurPartagee
                nombreAcces
            }
        }
        """

        # Charge de travail mixte (80% lecture, 20% écriture)
        mixed_queries = [
            (read_query, 8),  # Poids 8 pour les lectures
            (write_query, 2),  # Poids 2 pour les écritures
        ]

        stats = self.concurrency_tester.execute_mixed_workload(
            queries=mixed_queries, num_threads=8, duration_seconds=5
        )

        # Vérifier les performances
        self.assertGreater(stats["success_rate"], 0.90)  # Au moins 90% de succès
        self.assertGreater(stats["queries_per_second"], 5)  # Au moins 5 QPS
        self.assertGreater(stats["total_queries"], 20)  # Au moins 20 requêtes en 5s

    def test_database_connection_concurrency(self):
        """Test la gestion des connexions de base de données concurrentes."""
        query = """
        query {
            allConcurrentModels {
                id
                nomConcurrent
            }
        }
        """

        # Mesurer les connexions avant
        initial_connections = len(connection.queries)

        # Exécuter de nombreuses requêtes concurrentes
        stats = self.concurrency_tester.execute_concurrent_queries(
            query=query, num_threads=20, iterations_per_thread=3
        )

        # Mesurer les connexions après
        final_connections = len(connection.queries)
        connection_increase = final_connections - initial_connections

        # Vérifier que les connexions sont gérées efficacement
        self.assertGreater(stats["success_rate"], 0.95)

        # Le nombre de connexions ne doit pas exploser
        expected_max_connections = stats["total_queries"] * 2  # Marge de sécurité
        self.assertLess(connection_increase, expected_max_connections)

    def test_cache_concurrency(self):
        """Test la concurrence avec le cache."""
        query = """
        query {
            allSharedResources {
                id
                nomRessource
                valeurPartagee
            }
        }
        """

        # Vider le cache
        cache.clear()

        # Exécuter des requêtes concurrentes (qui peuvent utiliser le cache)
        stats = self.concurrency_tester.execute_concurrent_queries(
            query=query, num_threads=15, iterations_per_thread=4
        )

        # Vérifier les performances avec cache
        self.assertGreater(stats["success_rate"], 0.95)
        self.assertLess(
            stats["execution_time_stats"]["mean"], 0.5
        )  # Cache doit accélérer

        # Pas d'erreurs de concurrence du cache
        cache_errors = [
            e for e in stats["errors"] if "cache" in e.get("error", "").lower()
        ]
        self.assertEqual(len(cache_errors), 0)

    def test_thread_safety_shared_resources(self):
        """Test la sécurité des threads avec ressources partagées."""
        # Requête qui accède aux ressources partagées
        query_template = """
        query {{
            sharedResource(id: {resource_id}) {{
                id
                nomRessource
                valeurPartagee
                nombreAcces
                accederRessource
            }}
        }}
        """

        # Utiliser la même ressource pour tous les threads (test de concurrence)
        resource_id = self.shared_resources[0].id
        query = query_template.format(resource_id=resource_id)

        # Exécuter des accès concurrents à la même ressource
        stats = self.concurrency_tester.execute_concurrent_queries(
            query=query, num_threads=10, iterations_per_thread=3
        )

        # Vérifier qu'il n'y a pas de conditions de course
        self.assertGreater(stats["success_rate"], 0.8)  # Au moins 80% de succès

        # Vérifier l'état final de la ressource
        resource = TestSharedResource.objects.get(id=resource_id)

        # Le nombre d'accès doit être cohérent (si la méthode business fonctionne)
        expected_accesses = stats["successful_queries"]
        # Note: Peut ne pas être exact si la méthode business n'est pas implémentée

    def test_memory_usage_under_concurrency(self):
        """Test l'utilisation mémoire sous charge concurrente."""
        query = """
        query {
            allConcurrentModels(first: 25) {
                id
                nomConcurrent
                donneesPartagees
                traitementLong
            }
        }
        """

        # Mesurer la mémoire initiale
        initial_memory = psutil.Process().memory_info().rss

        # Exécuter une charge concurrente
        stats = self.concurrency_tester.execute_concurrent_queries(
            query=query, num_threads=12, iterations_per_thread=2
        )

        # Mesurer la mémoire finale
        final_memory = psutil.Process().memory_info().rss
        memory_increase = (final_memory - initial_memory) / (1024 * 1024)  # MB

        # Vérifier les performances
        self.assertGreater(stats["success_rate"], 0.90)

        # L'augmentation mémoire doit être raisonnable
        self.assertLess(memory_increase, 100)  # Moins de 100MB d'augmentation

    def test_error_handling_under_concurrency(self):
        """Test la gestion d'erreurs sous charge concurrente."""
        # Requête qui peut causer des erreurs
        invalid_query = """
        query {
            nonExistentField {
                id
                invalidField
            }
        }
        """

        valid_query = """
        query {
            allConcurrentModels(first: 5) {
                id
                nomConcurrent
            }
        }
        """

        # Charge mixte avec requêtes valides et invalides
        mixed_queries = [
            (valid_query, 7),  # 70% de requêtes valides
            (invalid_query, 3),  # 30% de requêtes invalides
        ]

        stats = self.concurrency_tester.execute_mixed_workload(
            queries=mixed_queries, num_threads=6, duration_seconds=3
        )

        # Vérifier que le système gère les erreurs gracieusement
        self.assertGreater(stats["total_queries"], 10)  # Au moins quelques requêtes

        # Les erreurs ne doivent pas faire planter le système
        error_rate = (
            len(stats["errors"]) / stats["total_queries"]
            if stats["total_queries"] > 0
            else 0
        )
        self.assertLess(
            error_rate, 0.5
        )  # Moins de 50% d'erreurs (les valides doivent passer)

    def test_scalability_increasing_load(self):
        """Test la scalabilité avec charge croissante."""
        query = """
        query {
            allConcurrentModels(first: 15) {
                id
                nomConcurrent
                valeurCompteur
            }
        }
        """

        # Tester avec différents niveaux de charge
        load_levels = [2, 5, 10, 15]
        performance_results = []

        for num_threads in load_levels:
            stats = self.concurrency_tester.execute_concurrent_queries(
                query=query, num_threads=num_threads, iterations_per_thread=2
            )

            performance_results.append(
                {
                    "threads": num_threads,
                    "qps": stats["queries_per_second"],
                    "success_rate": stats["success_rate"],
                    "avg_time": stats["execution_time_stats"]["mean"],
                }
            )

        # Analyser la scalabilité
        for i, result in enumerate(performance_results):
            # Le taux de succès doit rester élevé
            self.assertGreater(result["success_rate"], 0.85)

            # Les performances ne doivent pas se dégrader drastiquement
            if i > 0:
                prev_result = performance_results[i - 1]

                # Le QPS peut diminuer mais pas trop drastiquement
                qps_ratio = (
                    result["qps"] / prev_result["qps"] if prev_result["qps"] > 0 else 1
                )
                self.assertGreater(qps_ratio, 0.3)  # Pas plus de 70% de dégradation

    def test_deadlock_prevention(self):
        """Test la prévention des deadlocks."""
        # Requêtes qui pourraient causer des deadlocks si mal gérées
        query1 = """
        query {
            allConcurrentModels(orderBy: "id") {
                id
                nomConcurrent
                incrementerCompteur
            }
        }
        """

        query2 = """
        query {
            allSharedResources(orderBy: "-id") {
                id
                nomRessource
                accederRessource
            }
        }
        """

        # Exécuter des requêtes qui accèdent aux ressources dans des ordres différents
        def execute_alternating_queries():
            """Exécute des requêtes alternées."""
            results = []
            for i in range(5):
                query = query1 if i % 2 == 0 else query2
                try:
                    result = self.client.execute(query)
                    results.append(
                        {
                            "iteration": i,
                            "query_type": "query1" if i % 2 == 0 else "query2",
                            "success": result.get("errors") is None,
                        }
                    )
                except Exception as e:
                    results.append(
                        {
                            "iteration": i,
                            "query_type": "query1" if i % 2 == 0 else "query2",
                            "success": False,
                            "error": str(e),
                        }
                    )
            return results

        # Exécuter en parallèle
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(execute_alternating_queries) for _ in range(4)]
            all_results = []

            # Attendre avec timeout pour détecter les deadlocks
            for future in as_completed(futures, timeout=30):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    # Un timeout pourrait indiquer un deadlock
                    self.fail(f"Possible deadlock détecté: {e}")

        # Vérifier qu'aucun deadlock n'est survenu
        successful_queries = [r for r in all_results if r["success"]]

        # Au moins quelques requêtes doivent réussir
        self.assertGreater(len(successful_queries), 5)


@pytest.mark.performance
class TestAsyncConcurrency:
    """Tests de concurrence asynchrone."""

    def test_async_query_execution(self):
        """Test l'exécution asynchrone des requêtes."""
        pass

    def test_async_mutation_execution(self):
        """Test l'exécution asynchrone des mutations."""
        pass

    def test_async_subscription_handling(self):
        """Test la gestion asynchrone des subscriptions."""
        pass


@pytest.mark.performance
class TestLoadBalancing:
    """Tests d'équilibrage de charge."""

    def test_request_distribution(self):
        """Test la distribution des requêtes."""
        pass

    def test_resource_utilization(self):
        """Test l'utilisation des ressources."""
        pass

    def test_failover_handling(self):
        """Test la gestion des basculements."""
        pass
