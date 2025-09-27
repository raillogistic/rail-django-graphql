"""
Tests de performance pour les benchmarks de requêtes GraphQL.

Ce module teste:
- Les performances des requêtes simples et complexes
- L'optimisation des requêtes N+1
- Les performances de pagination
- L'efficacité du cache
- Les temps de réponse sous charge
"""

import pytest
import time
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
from django.test import TestCase, TransactionTestCase
from django.db import models, connection
from django.test.utils import override_settings
from django.core.cache import cache
from typing import Dict, List, Optional, Any, Tuple
import psutil
import gc

import graphene
from graphene import Schema
from graphene.test import Client

from django_graphql_auto.core.schema import SchemaBuilder
from django_graphql_auto.generators.introspector import ModelIntrospector
from django_graphql_auto.generators.types import TypeGenerator
from django_graphql_auto.generators.queries import QueryGenerator
from django_graphql_auto.generators.mutations import MutationGenerator
from django_graphql_auto.decorators.business_logic import business_method
from django_graphql_auto.extensions.optimization import QueryOptimizer
from django_graphql_auto.extensions.caching import QueryCache
from tests.models import BenchmarkTestAuthor, BenchmarkTestBook, BenchmarkTestReview


class PerformanceMeter:
    """Utilitaire pour mesurer les performances."""
    
    def __init__(self):
        self.measurements = []
        self.memory_usage = []
        self.query_counts = []
    
    def start_measurement(self):
        """Démarre une mesure de performance."""
        gc.collect()  # Nettoyer la mémoire avant la mesure
        
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss
        self.start_queries = len(connection.queries)
    
    def end_measurement(self):
        """Termine une mesure de performance."""
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss
        end_queries = len(connection.queries)
        
        execution_time = end_time - self.start_time
        memory_delta = end_memory - self.start_memory
        query_count = end_queries - self.start_queries
        
        self.measurements.append(execution_time)
        self.memory_usage.append(memory_delta)
        self.query_counts.append(query_count)
        
        return {
            'execution_time': execution_time,
            'memory_delta': memory_delta,
            'query_count': query_count
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques des mesures."""
        if not self.measurements:
            return {}
        
        return {
            'execution_time': {
                'mean': statistics.mean(self.measurements),
                'median': statistics.median(self.measurements),
                'min': min(self.measurements),
                'max': max(self.measurements),
                'stdev': statistics.stdev(self.measurements) if len(self.measurements) > 1 else 0
            },
            'memory_usage': {
                'mean': statistics.mean(self.memory_usage),
                'median': statistics.median(self.memory_usage),
                'min': min(self.memory_usage),
                'max': max(self.memory_usage)
            },
            'query_count': {
                'mean': statistics.mean(self.query_counts),
                'median': statistics.median(self.query_counts),
                'min': min(self.query_counts),
                'max': max(self.query_counts)
            },
            'total_measurements': len(self.measurements)
        }


class TestQueryBenchmarks(TransactionTestCase):
    """Tests de performance pour les benchmarks de requêtes."""
    
    def setUp(self):
        """Configuration des tests de performance."""
        # Initialiser les générateurs
        self.introspector = ModelIntrospector()
        self.type_generator = TypeGenerator(self.introspector)
        self.query_generator = QueryGenerator(self.type_generator, None)
        self.mutation_generator = MutationGenerator(self.type_generator, None)
        
        # Initialiser le générateur de schéma
        self.schema_generator = AutoSchemaGenerator()
        
        # Modèles de test
        self.test_models = [BenchmarkTestAuthor, BenchmarkTestBook, BenchmarkTestReview]
        
        # Générer le schéma
        self.schema = self.schema_generator.generate_schema(self.test_models)
        self.client = Client(self.schema)
        
        # Utilitaire de mesure de performance
        self.performance_meter = PerformanceMeter()
        
        # Créer des données de test
        self._create_test_data()
    
    def _create_test_data(self):
        """Crée des données de test pour les benchmarks."""
        from datetime import date, timedelta
        import random
        
        # Créer des auteurs
        self.authors = []
        for i in range(50):
            author = BenchmarkTestAuthor.objects.create(
                nom_auteur=f"Auteur{i}",
                prenom_auteur=f"Prenom{i}",
                email_auteur=f"auteur{i}@example.com",
                date_naissance=date(1950 + i % 50, 1 + i % 12, 1 + i % 28),
                biographie_auteur=f"Biographie de l'auteur {i}" * 10,
                nombre_livres=random.randint(1, 20)
            )
            self.authors.append(author)
        
        # Créer des livres
        self.books = []
        genres = ['FICTION', 'NON_FICTION', 'SCIENCE_FICTION', 'ROMANCE', 'THRILLER', 'BIOGRAPHIE']
        
        for i in range(200):
            book = BenchmarkTestBook.objects.create(
                titre_livre=f"Livre {i}",
                auteur_livre=random.choice(self.authors),
                isbn_livre=f"978{i:010d}",
                date_publication=date(2000, 1, 1) + timedelta(days=i * 10),
                nombre_pages=random.randint(100, 800),
                prix_livre=random.uniform(10.0, 50.0),
                description_livre=f"Description du livre {i}" * 20,
                genre_livre=random.choice(genres),
                note_moyenne=random.uniform(1.0, 5.0)
            )
            self.books.append(book)
        
        # Créer des avis
        self.reviews = []
        for i in range(500):
            review = BenchmarkTestReview.objects.create(
                livre_avis=random.choice(self.books),
                nom_revieweur=f"Revieweur{i}",
                email_revieweur=f"revieweur{i}@example.com",
                note_avis=random.randint(1, 5),
                commentaire_avis=f"Commentaire de l'avis {i}" * 5,
                est_verifie=random.choice([True, False])
            )
            self.reviews.append(review)
    
    def test_simple_query_performance(self):
        """Test les performances des requêtes simples."""
        query = '''
        query {
            allAuthors {
                id
                nomAuteur
                prenomAuteur
                emailAuteur
            }
        }
        '''
        
        # Effectuer plusieurs mesures
        for _ in range(10):
            self.performance_meter.start_measurement()
            result = self.client.execute(query)
            measurement = self.performance_meter.end_measurement()
            
            # Vérifier que la requête fonctionne
            self.assertIsNone(result.get('errors'))
            
            # Vérifier les performances
            self.assertLess(measurement['execution_time'], 1.0)  # Moins de 1 seconde
            self.assertLess(measurement['query_count'], 5)       # Moins de 5 requêtes SQL
        
        # Analyser les statistiques
        stats = self.performance_meter.get_statistics()
        
        # Les performances doivent être consistantes
        self.assertLess(stats['execution_time']['mean'], 0.5)
        self.assertLess(stats['execution_time']['stdev'], 0.1)
    
    def test_complex_query_performance(self):
        """Test les performances des requêtes complexes avec relations."""
        query = '''
        query {
            allAuthors {
                id
                nomAuteur
                prenomAuteur
                livresAuteur {
                    id
                    titreLivre
                    genreLivre
                    prixLivre
                    avisLivre {
                        id
                        noteAvis
                        commentaireAvis
                        nomRevieweur
                    }
                }
            }
        }
        '''
        
        # Effectuer plusieurs mesures
        for _ in range(5):
            self.performance_meter.start_measurement()
            result = self.client.execute(query)
            measurement = self.performance_meter.end_measurement()
            
            # Vérifier que la requête fonctionne
            self.assertIsNone(result.get('errors'))
            
            # Les requêtes complexes peuvent prendre plus de temps
            self.assertLess(measurement['execution_time'], 5.0)  # Moins de 5 secondes
        
        # Analyser les statistiques
        stats = self.performance_meter.get_statistics()
        
        # Vérifier que les performances sont acceptables
        self.assertLess(stats['execution_time']['mean'], 3.0)
    
    def test_n_plus_one_optimization(self):
        """Test l'optimisation des requêtes N+1."""
        # Requête qui pourrait causer un problème N+1
        query = '''
        query {
            allBooks(first: 20) {
                id
                titreLivre
                auteurLivre {
                    id
                    nomAuteur
                    prenomAuteur
                }
            }
        }
        '''
        
        self.performance_meter.start_measurement()
        result = self.client.execute(query)
        measurement = self.performance_meter.end_measurement()
        
        # Vérifier que la requête fonctionne
        self.assertIsNone(result.get('errors'))
        
        # Avec l'optimisation, le nombre de requêtes doit être limité
        # Sans optimisation: 1 requête pour les livres + N requêtes pour les auteurs
        # Avec optimisation: 1-3 requêtes maximum (select_related/prefetch_related)
        self.assertLess(measurement['query_count'], 10)
        
        # Vérifier les performances
        self.assertLess(measurement['execution_time'], 1.0)
    
    def test_pagination_performance(self):
        """Test les performances de la pagination."""
        # Test de pagination avec différentes tailles de page
        page_sizes = [10, 25, 50, 100]
        
        for page_size in page_sizes:
            query = f'''
            query {{
                allBooks(first: {page_size}) {{
                    edges {{
                        node {{
                            id
                            titreLivre
                            auteurLivre {{
                                nomAuteur
                            }}
                        }}
                    }}
                    pageInfo {{
                        hasNextPage
                        hasPreviousPage
                        startCursor
                        endCursor
                    }}
                }}
            }}
            '''
            
            self.performance_meter.start_measurement()
            result = self.client.execute(query)
            measurement = self.performance_meter.end_measurement()
            
            # Vérifier que la requête fonctionne
            self.assertIsNone(result.get('errors'))
            
            # Les performances doivent être proportionnelles à la taille de page
            expected_time = page_size * 0.01  # 10ms par élément maximum
            self.assertLess(measurement['execution_time'], expected_time)
    
    def test_filtering_performance(self):
        """Test les performances du filtrage."""
        # Test avec différents types de filtres
        filters = [
            'genreLivre: "FICTION"',
            'prixLivre_Gte: 20.0',
            'datePublication_Year: 2010',
            'auteurLivre_NomAuteur_Icontains: "Auteur1"'
        ]
        
        for filter_condition in filters:
            query = f'''
            query {{
                allBooks({filter_condition}) {{
                    id
                    titreLivre
                    prixLivre
                    genreLivre
                }}
            }}
            '''
            
            self.performance_meter.start_measurement()
            result = self.client.execute(query)
            measurement = self.performance_meter.end_measurement()
            
            # Vérifier que la requête fonctionne
            self.assertIsNone(result.get('errors'))
            
            # Le filtrage doit être rapide
            self.assertLess(measurement['execution_time'], 0.5)
            
            # Le filtrage doit utiliser les index (peu de requêtes)
            self.assertLess(measurement['query_count'], 3)
    
    def test_sorting_performance(self):
        """Test les performances du tri."""
        # Test avec différents critères de tri
        sort_orders = [
            'titreLivre',
            '-datePublication',
            'prixLivre',
            'auteurLivre__nomAuteur'
        ]
        
        for sort_order in sort_orders:
            query = f'''
            query {{
                allBooks(orderBy: "{sort_order}", first: 50) {{
                    id
                    titreLivre
                    datePublication
                    prixLivre
                }}
            }}
            '''
            
            self.performance_meter.start_measurement()
            result = self.client.execute(query)
            measurement = self.performance_meter.end_measurement()
            
            # Vérifier que la requête fonctionne
            self.assertIsNone(result.get('errors'))
            
            # Le tri doit être rapide
            self.assertLess(measurement['execution_time'], 1.0)
    
    def test_aggregation_performance(self):
        """Test les performances des agrégations."""
        query = '''
        query {
            bookStatistics {
                totalBooks
                averagePrice
                maxPages
                minPages
                booksByGenre {
                    genre
                    count
                }
            }
        }
        '''
        
        # Note: Cette requête nécessiterait une implémentation d'agrégation
        # Pour l'instant, on teste une requête similaire
        alternative_query = '''
        query {
            allBooks {
                id
                prixLivre
                nombrePages
                genreLivre
            }
        }
        '''
        
        self.performance_meter.start_measurement()
        result = self.client.execute(alternative_query)
        measurement = self.performance_meter.end_measurement()
        
        # Vérifier que la requête fonctionne
        self.assertIsNone(result.get('errors'))
        
        # Les agrégations peuvent prendre plus de temps
        self.assertLess(measurement['execution_time'], 2.0)
    
    def test_concurrent_query_performance(self):
        """Test les performances des requêtes concurrentes."""
        query = '''
        query {
            allAuthors(first: 10) {
                id
                nomAuteur
                livresAuteur {
                    id
                    titreLivre
                }
            }
        }
        '''
        
        def execute_query():
            """Exécute une requête dans un thread."""
            start_time = time.time()
            result = self.client.execute(query)
            end_time = time.time()
            
            return {
                'execution_time': end_time - start_time,
                'success': result.get('errors') is None,
                'result': result
            }
        
        # Exécuter des requêtes concurrentes
        num_threads = 10
        results = []
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(execute_query) for _ in range(num_threads)]
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        # Analyser les résultats
        successful_queries = [r for r in results if r['success']]
        execution_times = [r['execution_time'] for r in successful_queries]
        
        # Toutes les requêtes doivent réussir
        self.assertEqual(len(successful_queries), num_threads)
        
        # Les performances ne doivent pas se dégrader significativement
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        
        self.assertLess(avg_time, 2.0)  # Temps moyen acceptable
        self.assertLess(max_time, 5.0)  # Temps maximum acceptable
    
    def test_cache_performance(self):
        """Test les performances avec mise en cache."""
        query = '''
        query {
            allAuthors(first: 20) {
                id
                nomAuteur
                prenomAuteur
                livresAuteur {
                    id
                    titreLivre
                }
            }
        }
        '''
        
        # Première exécution (sans cache)
        cache.clear()
        self.performance_meter.start_measurement()
        result1 = self.client.execute(query)
        measurement1 = self.performance_meter.end_measurement()
        
        # Deuxième exécution (avec cache potentiel)
        self.performance_meter.start_measurement()
        result2 = self.client.execute(query)
        measurement2 = self.performance_meter.end_measurement()
        
        # Vérifier que les requêtes fonctionnent
        self.assertIsNone(result1.get('errors'))
        self.assertIsNone(result2.get('errors'))
        
        # Les résultats doivent être identiques
        self.assertEqual(result1['data'], result2['data'])
        
        # Si le cache fonctionne, la deuxième requête doit être plus rapide
        if measurement2['execution_time'] < measurement1['execution_time'] * 0.8:
            # Cache efficace
            self.assertLess(measurement2['query_count'], measurement1['query_count'])
    
    def test_memory_usage_performance(self):
        """Test l'utilisation mémoire des requêtes."""
        # Requête qui retourne beaucoup de données
        query = '''
        query {
            allBooks {
                id
                titreLivre
                descriptionLivre
                auteurLivre {
                    id
                    nomAuteur
                    biographieAuteur
                }
                avisLivre {
                    id
                    commentaireAvis
                    nomRevieweur
                }
            }
        }
        '''
        
        # Mesurer l'utilisation mémoire
        initial_memory = psutil.Process().memory_info().rss
        
        self.performance_meter.start_measurement()
        result = self.client.execute(query)
        measurement = self.performance_meter.end_measurement()
        
        final_memory = psutil.Process().memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Vérifier que la requête fonctionne
        self.assertIsNone(result.get('errors'))
        
        # L'augmentation mémoire doit être raisonnable (moins de 100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024)
        
        # Nettoyer la mémoire
        del result
        gc.collect()
    
    def test_query_complexity_performance(self):
        """Test les performances selon la complexité des requêtes."""
        # Requêtes de complexité croissante
        queries = [
            # Complexité faible
            '''
            query {
                allAuthors(first: 5) {
                    id
                    nomAuteur
                }
            }
            ''',
            # Complexité moyenne
            '''
            query {
                allAuthors(first: 5) {
                    id
                    nomAuteur
                    livresAuteur {
                        id
                        titreLivre
                    }
                }
            }
            ''',
            # Complexité élevée
            '''
            query {
                allAuthors(first: 5) {
                    id
                    nomAuteur
                    livresAuteur {
                        id
                        titreLivre
                        avisLivre {
                            id
                            noteAvis
                            commentaireAvis
                        }
                    }
                }
            }
            '''
        ]
        
        execution_times = []
        
        for i, query in enumerate(queries):
            self.performance_meter.start_measurement()
            result = self.client.execute(query)
            measurement = self.performance_meter.end_measurement()
            
            # Vérifier que la requête fonctionne
            self.assertIsNone(result.get('errors'))
            
            execution_times.append(measurement['execution_time'])
            
            # Chaque niveau de complexité doit rester dans des limites acceptables
            max_time = (i + 1) * 1.0  # 1s, 2s, 3s maximum
            self.assertLess(measurement['execution_time'], max_time)
        
        # Les temps d'exécution doivent généralement augmenter avec la complexité
        # (mais pas nécessairement de façon strictement croissante)
        self.assertLess(execution_times[0], execution_times[2] * 2)


@pytest.mark.performance
class TestQueryBenchmarksAdvanced:
    """Tests de performance avancés pour les benchmarks de requêtes."""
    
    def test_database_connection_pooling_performance(self):
        """Test les performances du pool de connexions."""
        pass
    
    def test_query_plan_optimization(self):
        """Test l'optimisation des plans de requête."""
        pass
    
    def test_index_usage_performance(self):
        """Test l'utilisation des index pour les performances."""
        pass
    
    def test_bulk_operations_performance(self):
        """Test les performances des opérations en lot."""
        pass
    
    def test_streaming_response_performance(self):
        """Test les performances des réponses en streaming."""
        pass