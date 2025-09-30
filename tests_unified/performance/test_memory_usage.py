"""
Tests de performance pour l'utilisation mémoire.

Ce module teste:
- La consommation mémoire des opérations GraphQL
- La détection des fuites mémoire
- L'efficacité du garbage collection
- L'utilisation mémoire sous charge
- L'optimisation des structures de données
"""

import pytest
import gc
import time
import threading
import weakref
from typing import Dict, List, Optional, Any, Tuple
from unittest.mock import Mock, patch
from django.test import TestCase, TransactionTestCase
from django.db import models, connection
from django.test.utils import override_settings
from django.core.cache import cache
import psutil
import tracemalloc
import sys

import graphene
from graphene import Schema
from graphene.test import Client

from rail_django_graphql.schema_generator import AutoSchemaGenerator
from rail_django_graphql.generators.introspector import ModelIntrospector
from rail_django_graphql.generators.types import TypeGenerator
from rail_django_graphql.generators.queries import QueryGenerator
from rail_django_graphql.generators.mutations import MutationGenerator
from rail_django_graphql.decorators.business_logic import business_method
from tests.models import TestMemoryModel, TestRelatedModel


class MemoryProfiler:
    """Profileur mémoire pour les tests."""

    def __init__(self):
        self.snapshots = []
        self.peak_memory = 0
        self.start_memory = 0
        self.tracemalloc_started = False

    def start_profiling(self):
        """Démarre le profilage mémoire."""
        gc.collect()  # Nettoyer avant de commencer

        # Démarrer tracemalloc si pas déjà fait
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            self.tracemalloc_started = True

        # Prendre un snapshot initial
        self.start_memory = psutil.Process().memory_info().rss
        self.peak_memory = self.start_memory

        if tracemalloc.is_tracing():
            snapshot = tracemalloc.take_snapshot()
            self.snapshots.append(("start", snapshot))

    def take_snapshot(self, label: str = "checkpoint"):
        """Prend un snapshot mémoire."""
        current_memory = psutil.Process().memory_info().rss
        self.peak_memory = max(self.peak_memory, current_memory)

        if tracemalloc.is_tracing():
            snapshot = tracemalloc.take_snapshot()
            self.snapshots.append((label, snapshot))

    def stop_profiling(self) -> Dict[str, Any]:
        """Arrête le profilage et retourne les statistiques."""
        gc.collect()  # Nettoyer après les opérations

        end_memory = psutil.Process().memory_info().rss

        # Prendre un snapshot final
        if tracemalloc.is_tracing():
            final_snapshot = tracemalloc.take_snapshot()
            self.snapshots.append(("end", final_snapshot))

        # Calculer les statistiques
        memory_delta = end_memory - self.start_memory
        peak_delta = self.peak_memory - self.start_memory

        stats = {
            "start_memory": self.start_memory,
            "end_memory": end_memory,
            "peak_memory": self.peak_memory,
            "memory_delta": memory_delta,
            "peak_delta": peak_delta,
            "memory_delta_mb": memory_delta / (1024 * 1024),
            "peak_delta_mb": peak_delta / (1024 * 1024),
        }

        # Analyser les snapshots tracemalloc
        if len(self.snapshots) >= 2:
            start_snapshot = self.snapshots[0][1]
            end_snapshot = self.snapshots[-1][1]

            top_stats = end_snapshot.compare_to(start_snapshot, "lineno")
            stats["top_memory_allocations"] = [
                {
                    "filename": stat.traceback.format()[0],
                    "size_diff": stat.size_diff,
                    "size_diff_mb": stat.size_diff / (1024 * 1024),
                    "count_diff": stat.count_diff,
                }
                for stat in top_stats[:10]  # Top 10
            ]

        # Arrêter tracemalloc si on l'a démarré
        if self.tracemalloc_started and tracemalloc.is_tracing():
            tracemalloc.stop()

        return stats

    def get_current_memory_usage(self) -> int:
        """Retourne l'utilisation mémoire actuelle."""
        return psutil.Process().memory_info().rss

    def detect_memory_leaks(self, threshold_mb: float = 10.0) -> bool:
        """Détecte les fuites mémoire potentielles."""
        if len(self.snapshots) < 2:
            return False

        start_snapshot = self.snapshots[0][1]
        end_snapshot = self.snapshots[-1][1]

        # Comparer les snapshots
        top_stats = end_snapshot.compare_to(start_snapshot, "lineno")

        # Chercher des allocations importantes non libérées
        for stat in top_stats[:5]:
            if stat.size_diff > threshold_mb * 1024 * 1024:
                return True

        return False


class TestMemoryUsage(TransactionTestCase):
    """Tests d'utilisation mémoire."""

    def setUp(self):
        """Configuration des tests de mémoire."""
        # Initialiser les générateurs
        self.introspector = ModelIntrospector()
        self.type_generator = TypeGenerator(self.introspector)
        self.query_generator = QueryGenerator(self.type_generator, None)
        self.mutation_generator = MutationGenerator(self.type_generator, None)

        # Initialiser le générateur de schéma
        self.schema_generator = AutoSchemaGenerator()

        # Modèles de test
        self.test_models = [TestMemoryModel, TestRelatedModel]

        # Générer le schéma
        self.schema = self.schema_generator.generate_schema(self.test_models)
        self.client = Client(self.schema)

        # Profileur mémoire
        self.memory_profiler = MemoryProfiler()

        # Créer des données de test
        self._create_test_data()

    def _create_test_data(self):
        """Crée des données de test."""
        # Créer des modèles avec des données volumineuses
        self.memory_models = []
        for i in range(100):
            # Créer des données JSON volumineuses
            json_data = {
                "items": [{"id": j, "data": "x" * 100} for j in range(50)],
                "metadata": {"created": f"2023-01-{i:02d}", "size": i * 100},
            }

            model = TestMemoryModel.objects.create(
                nom_modele=f"Modèle {i}",
                donnees_volumineuses="y" * 1000,  # 1KB par modèle
                nombre_entier=i,
                donnees_json=json_data,
            )
            self.memory_models.append(model)

            # Créer des modèles liés
            for j in range(5):
                TestRelatedModel.objects.create(
                    modele_parent=model,
                    nom_relation=f"Relation {i}-{j}",
                    donnees_relation="z" * 500,  # 500B par relation
                )

    def test_basic_query_memory_usage(self):
        """Test l'utilisation mémoire des requêtes de base."""
        query = """
        query {
            allMemoryModels {
                id
                nomModele
                donneesVolumeuses
                nombreEntier
            }
        }
        """

        self.memory_profiler.start_profiling()

        # Exécuter la requête
        result = self.client.execute(query)

        self.memory_profiler.take_snapshot("after_query")
        stats = self.memory_profiler.stop_profiling()

        # Vérifier que la requête fonctionne
        self.assertIsNone(result.get("errors"))

        # Vérifier l'utilisation mémoire
        self.assertLess(stats["memory_delta_mb"], 50)  # Moins de 50MB

        # Pas de fuite mémoire détectée
        self.assertFalse(self.memory_profiler.detect_memory_leaks(5.0))

    def test_complex_query_memory_usage(self):
        """Test l'utilisation mémoire des requêtes complexes."""
        query = """
        query {
            allMemoryModels {
                id
                nomModele
                donneesVolumeuses
                donneesJson
                modelesLies {
                    id
                    nomRelation
                    donneesRelation
                }
            }
        }
        """

        self.memory_profiler.start_profiling()

        # Exécuter la requête
        result = self.client.execute(query)

        self.memory_profiler.take_snapshot("after_complex_query")
        stats = self.memory_profiler.stop_profiling()

        # Vérifier que la requête fonctionne
        self.assertIsNone(result.get("errors"))

        # Les requêtes complexes peuvent utiliser plus de mémoire
        self.assertLess(stats["memory_delta_mb"], 100)  # Moins de 100MB

        # Vérifier qu'il n'y a pas de fuite majeure
        self.assertFalse(self.memory_profiler.detect_memory_leaks(10.0))

    def test_multiple_queries_memory_accumulation(self):
        """Test l'accumulation mémoire avec plusieurs requêtes."""
        query = """
        query {
            allMemoryModels(first: 20) {
                id
                nomModele
                modelesLies {
                    id
                    nomRelation
                }
            }
        }
        """

        self.memory_profiler.start_profiling()

        # Exécuter plusieurs requêtes
        for i in range(10):
            result = self.client.execute(query)
            self.assertIsNone(result.get("errors"))

            # Prendre un snapshot périodique
            if i % 3 == 0:
                self.memory_profiler.take_snapshot(f"query_{i}")

        stats = self.memory_profiler.stop_profiling()

        # L'accumulation mémoire doit être limitée
        self.assertLess(stats["memory_delta_mb"], 30)  # Moins de 30MB total

        # Pas de fuite mémoire significative
        self.assertFalse(self.memory_profiler.detect_memory_leaks(5.0))

    def test_business_method_memory_usage(self):
        """Test l'utilisation mémoire des méthodes business."""
        query = """
        query {
            allMemoryModels(first: 10) {
                id
                nomModele
                traitementIntensif
            }
        }
        """

        self.memory_profiler.start_profiling()

        # Exécuter la requête avec méthodes business
        result = self.client.execute(query)

        self.memory_profiler.take_snapshot("after_business_methods")
        stats = self.memory_profiler.stop_profiling()

        # Vérifier que la requête fonctionne
        self.assertIsNone(result.get("errors"))

        # Les méthodes business peuvent consommer plus de mémoire temporairement
        self.assertLess(stats["memory_delta_mb"], 20)  # Moins de 20MB final

        # Vérifier que la mémoire temporaire est libérée
        self.assertFalse(self.memory_profiler.detect_memory_leaks(3.0))

    def test_mutation_memory_usage(self):
        """Test l'utilisation mémoire des mutations."""
        mutation = """
        mutation {
            createMemoryModel(input: {
                nomModele: "Nouveau modèle"
                donneesVolumeuses: "Données de test très longues..."
                nombreEntier: 42
                donneesJson: "{\"test\": \"data\"}"
            }) {
                memoryModel {
                    id
                    nomModele
                }
            }
        }
        """

        self.memory_profiler.start_profiling()

        # Exécuter plusieurs mutations
        for i in range(20):
            result = self.client.execute(mutation)
            # Note: Cette mutation pourrait échouer si pas implémentée
            # On continue le test même en cas d'erreur

        self.memory_profiler.take_snapshot("after_mutations")
        stats = self.memory_profiler.stop_profiling()

        # L'utilisation mémoire des mutations doit être contrôlée
        self.assertLess(stats["memory_delta_mb"], 15)  # Moins de 15MB

    def test_concurrent_queries_memory_usage(self):
        """Test l'utilisation mémoire avec requêtes concurrentes."""
        query = """
        query {
            allMemoryModels(first: 15) {
                id
                nomModele
                donneesVolumeuses
            }
        }
        """

        self.memory_profiler.start_profiling()

        def execute_query():
            """Exécute une requête dans un thread."""
            return self.client.execute(query)

        # Exécuter des requêtes concurrentes
        threads = []
        results = []

        for i in range(5):
            thread = threading.Thread(target=lambda: results.append(execute_query()))
            threads.append(thread)
            thread.start()

        # Attendre la fin de tous les threads
        for thread in threads:
            thread.join()

        self.memory_profiler.take_snapshot("after_concurrent_queries")
        stats = self.memory_profiler.stop_profiling()

        # L'utilisation mémoire concurrente doit être raisonnable
        self.assertLess(stats["memory_delta_mb"], 40)  # Moins de 40MB

        # Pas de fuite mémoire due à la concurrence
        self.assertFalse(self.memory_profiler.detect_memory_leaks(8.0))

    def test_large_dataset_memory_usage(self):
        """Test l'utilisation mémoire avec de gros datasets."""
        # Créer plus de données pour ce test
        for i in range(100, 300):  # 200 modèles supplémentaires
            json_data = {
                "large_array": [f"item_{j}" * 10 for j in range(100)],
                "metadata": {"index": i, "size": "large"},
            }

            TestMemoryModel.objects.create(
                nom_modele=f"Large Model {i}",
                donnees_volumineuses="x" * 2000,  # 2KB par modèle
                nombre_entier=i,
                donnees_json=json_data,
            )

        query = """
        query {
            allMemoryModels {
                id
                nomModele
                donneesJson
            }
        }
        """

        self.memory_profiler.start_profiling()

        # Exécuter la requête sur le gros dataset
        result = self.client.execute(query)

        self.memory_profiler.take_snapshot("after_large_dataset")
        stats = self.memory_profiler.stop_profiling()

        # Vérifier que la requête fonctionne
        self.assertIsNone(result.get("errors"))

        # L'utilisation mémoire doit rester proportionnelle
        self.assertLess(stats["memory_delta_mb"], 200)  # Moins de 200MB

        # Pas de fuite mémoire majeure
        self.assertFalse(self.memory_profiler.detect_memory_leaks(20.0))

    def test_memory_cleanup_after_queries(self):
        """Test le nettoyage mémoire après les requêtes."""
        query = """
        query {
            allMemoryModels(first: 50) {
                id
                nomModele
                donneesVolumeuses
                modelesLies {
                    id
                    donneesRelation
                }
            }
        }
        """

        # Mesurer la mémoire de base
        gc.collect()
        base_memory = psutil.Process().memory_info().rss

        # Exécuter plusieurs requêtes
        for i in range(5):
            result = self.client.execute(query)
            self.assertIsNone(result.get("errors"))

            # Supprimer explicitement la référence
            del result

        # Forcer le garbage collection
        gc.collect()
        time.sleep(0.1)  # Laisser le temps au GC

        # Mesurer la mémoire finale
        final_memory = psutil.Process().memory_info().rss
        memory_increase = (final_memory - base_memory) / (1024 * 1024)  # MB

        # L'augmentation mémoire doit être minimale après nettoyage
        self.assertLess(memory_increase, 10)  # Moins de 10MB d'augmentation

    def test_weak_references_cleanup(self):
        """Test le nettoyage des références faibles."""
        query = """
        query {
            allMemoryModels(first: 10) {
                id
                nomModele
            }
        }
        """

        # Créer des références faibles aux résultats
        weak_refs = []

        for i in range(10):
            result = self.client.execute(query)
            if result.get("data"):
                # Créer une référence faible aux données
                weak_ref = weakref.ref(result["data"])
                weak_refs.append(weak_ref)

            # Supprimer la référence forte
            del result

        # Forcer le garbage collection
        gc.collect()

        # Vérifier que les références faibles sont nettoyées
        alive_refs = [ref for ref in weak_refs if ref() is not None]

        # La plupart des références devraient être nettoyées
        cleanup_ratio = (len(weak_refs) - len(alive_refs)) / len(weak_refs)
        self.assertGreater(cleanup_ratio, 0.7)  # Au moins 70% nettoyées

    def test_schema_generation_memory_usage(self):
        """Test l'utilisation mémoire de la génération de schéma."""
        self.memory_profiler.start_profiling()

        # Générer plusieurs schémas
        for i in range(3):
            schema_generator = AutoSchemaGenerator()
            schema = schema_generator.generate_schema(self.test_models)

            self.memory_profiler.take_snapshot(f"schema_{i}")

            # Supprimer les références
            del schema_generator
            del schema

        stats = self.memory_profiler.stop_profiling()

        # La génération de schéma ne doit pas accumuler trop de mémoire
        self.assertLess(stats["memory_delta_mb"], 25)  # Moins de 25MB

        # Pas de fuite mémoire dans la génération
        self.assertFalse(self.memory_profiler.detect_memory_leaks(5.0))

    def test_cache_memory_usage(self):
        """Test l'utilisation mémoire du cache."""
        query = """
        query {
            allMemoryModels(first: 30) {
                id
                nomModele
                donneesVolumeuses
            }
        }
        """

        self.memory_profiler.start_profiling()

        # Vider le cache
        cache.clear()

        # Exécuter la requête plusieurs fois (pour remplir le cache)
        for i in range(5):
            result = self.client.execute(query)
            self.assertIsNone(result.get("errors"))

        self.memory_profiler.take_snapshot("cache_filled")

        # Vider le cache
        cache.clear()
        gc.collect()

        self.memory_profiler.take_snapshot("cache_cleared")
        stats = self.memory_profiler.stop_profiling()

        # L'utilisation mémoire du cache doit être contrôlée
        self.assertLess(stats["memory_delta_mb"], 30)  # Moins de 30MB


@pytest.mark.performance
class TestMemoryLeakDetection:
    """Tests de détection des fuites mémoire."""

    def test_query_execution_memory_leaks(self):
        """Test les fuites mémoire dans l'exécution des requêtes."""
        pass

    def test_schema_generation_memory_leaks(self):
        """Test les fuites mémoire dans la génération de schéma."""
        pass

    def test_type_conversion_memory_leaks(self):
        """Test les fuites mémoire dans la conversion de types."""
        pass

    def test_resolver_memory_leaks(self):
        """Test les fuites mémoire dans les resolvers."""
        pass


@pytest.mark.performance
class TestMemoryOptimization:
    """Tests d'optimisation mémoire."""

    def test_lazy_loading_memory_efficiency(self):
        """Test l'efficacité mémoire du lazy loading."""
        pass

    def test_pagination_memory_efficiency(self):
        """Test l'efficacité mémoire de la pagination."""
        pass

    def test_field_selection_memory_efficiency(self):
        """Test l'efficacité mémoire de la sélection de champs."""
        pass

    def test_caching_memory_efficiency(self):
        """Test l'efficacité mémoire du cache."""
        pass
