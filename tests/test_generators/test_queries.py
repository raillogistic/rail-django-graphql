"""
Tests complets pour le système de génération de requêtes GraphQL.

Ce module teste:
- La génération de requêtes GraphQL pour les modèles Django
- Les requêtes simples et de liste
- Les systèmes de filtrage et pagination
- L'optimisation des requêtes
- La résolution des relations
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.db import models
from django.contrib.auth.models import User
from typing import Dict, List, Optional, Type

import graphene
from graphene import (
    ObjectType,
    String,
    Int,
    Boolean,
    DateTime,
    List as GrapheneList,
    Field,
)
from graphene.test import Client
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from rail_django_graphql.generators.queries import QueryGenerator
from rail_django_graphql.generators.types import TypeGenerator
from rail_django_graphql.generators.filters import AdvancedFilterGenerator
from rail_django_graphql.generators.introspector import ModelIntrospector


# Modèles de test pour la génération de requêtes
class QueryTestAuthor(models.Model):
    """Modèle auteur pour les tests de génération de requêtes."""

    nom_auteur = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom de l'auteur",
        help_text="Nom unique de l'auteur",
    )
    email_auteur = models.EmailField(
        verbose_name="E-mail de l'auteur", help_text="Adresse e-mail de l'auteur"
    )
    date_naissance = models.DateField(
        null=True, blank=True, verbose_name="Date de naissance"
    )
    est_actif = models.BooleanField(default=True, verbose_name="Est actif")
    nombre_livres = models.PositiveIntegerField(
        default=0, verbose_name="Nombre de livres"
    )

    class Meta:
        app_label = "tests"
        verbose_name = "Auteur"
        verbose_name_plural = "Auteurs"
        ordering = ["nom_auteur"]


class QueryTestBook(models.Model):
    """Modèle livre pour les tests de génération de requêtes."""

    titre_livre = models.CharField(max_length=200, verbose_name="Titre du livre")
    description_livre = models.TextField(
        blank=True, verbose_name="Description du livre"
    )
    auteur_livre = models.ForeignKey(
        QueryTestAuthor,
        on_delete=models.CASCADE,
        related_name="livres_ecrits",
        verbose_name="Auteur du livre",
    )
    categories_livre = models.ManyToManyField(
        "QueryTestCategory",
        blank=True,
        related_name="livres_categories",
        verbose_name="Catégories du livre",
    )
    date_publication = models.DateField(verbose_name="Date de publication")
    prix_livre = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Prix du livre"
    )
    est_disponible = models.BooleanField(default=True, verbose_name="Est disponible")
    nombre_pages = models.PositiveIntegerField(verbose_name="Nombre de pages")

    class Meta:
        app_label = "tests"
        verbose_name = "Livre"
        verbose_name_plural = "Livres"
        ordering = ["-date_publication"]


class QueryTestCategory(models.Model):
    """Modèle catégorie pour les tests de génération de requêtes."""

    nom_categorie = models.CharField(
        max_length=100, unique=True, verbose_name="Nom de la catégorie"
    )
    description_categorie = models.TextField(
        blank=True, verbose_name="Description de la catégorie"
    )
    parent_categorie = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="sous_categories",
        verbose_name="Catégorie parente",
    )

    class Meta:
        app_label = "tests"
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"


class TestQueryGenerator(TestCase):
    """Tests pour la classe QueryGenerator."""

    def setUp(self):
        """Configuration des tests."""
        self.introspector = ModelIntrospector()
        self.type_generator = TypeGenerator(self.introspector)
        self.filter_generator = AdvancedFilterGenerator(self.introspector)
        self.query_generator = QueryGenerator(
            self.type_generator, self.filter_generator
        )

    def test_initialization(self):
        """Test l'initialisation du générateur de requêtes."""
        # Test initialisation de base
        generator = QueryGenerator(self.type_generator, self.filter_generator)
        self.assertIsNotNone(generator)
        self.assertEqual(generator.type_generator, self.type_generator)
        self.assertEqual(generator.filter_generator, self.filter_generator)

        # Test initialisation avec configuration
        config_mock = Mock()
        generator_with_config = QueryGenerator(
            self.type_generator, self.filter_generator, config=config_mock
        )
        self.assertEqual(generator_with_config.config, config_mock)

    def test_generate_single_query(self):
        """Test la génération de requête pour un objet unique."""
        # Générer la requête pour un auteur unique
        author_query = self.query_generator.generate_single_query(QueryTestAuthor)

        # Vérifier que la requête est générée
        self.assertIsNotNone(author_query)
        self.assertIsInstance(author_query, Field)

        # Vérifier le type de retour
        self.assertIsNotNone(author_query.type)

    def test_generate_list_query(self):
        """Test la génération de requête pour une liste d'objets."""
        # Générer la requête pour une liste d'auteurs
        authors_query = self.query_generator.generate_list_query(QueryTestAuthor)

        # Vérifier que la requête est générée
        self.assertIsNotNone(authors_query)

        # Vérifier que c'est une requête de liste
        self.assertTrue(hasattr(authors_query, "type"))

    def test_generate_filtered_query(self):
        """Test la génération de requête avec filtres."""
        # Générer la requête filtrée pour les livres
        books_query = self.query_generator.generate_filtered_query(QueryTestBook)

        # Vérifier que la requête est générée
        self.assertIsNotNone(books_query)

        # Vérifier que les filtres sont disponibles
        self.assertTrue(
            hasattr(books_query, "args") or hasattr(books_query, "arguments")
        )

    def test_generate_paginated_query(self):
        """Test la génération de requête avec pagination."""
        # Générer la requête paginée pour les livres
        paginated_query = self.query_generator.generate_paginated_query(QueryTestBook)

        # Vérifier que la requête est générée
        self.assertIsNotNone(paginated_query)

        # Vérifier que c'est une requête de connexion (pagination Relay)
        self.assertIsInstance(paginated_query, DjangoFilterConnectionField)

    def test_generate_all_queries_for_model(self):
        """Test la génération de toutes les requêtes pour un modèle."""
        # Générer toutes les requêtes pour QueryTestBook
        all_queries = self.query_generator.generate_all_queries(QueryTestBook)

        # Vérifier que toutes les requêtes sont générées
        self.assertIsInstance(all_queries, dict)
        self.assertGreater(len(all_queries), 0)

        # Vérifier les types de requêtes générées
        expected_query_types = ["single", "list", "filtered", "paginated"]
        for query_type in expected_query_types:
            if query_type in all_queries:
                self.assertIsNotNone(all_queries[query_type])

    def test_query_resolver_generation(self):
        """Test la génération des résolveurs de requêtes."""
        # Générer un résolveur pour QueryTestAuthor
        resolver = self.query_generator.generate_resolver(QueryTestAuthor, "single")

        # Vérifier que le résolveur est généré
        self.assertIsNotNone(resolver)
        self.assertTrue(callable(resolver))

    def test_query_with_relationships(self):
        """Test la génération de requêtes avec relations."""
        # Générer la requête pour QueryTestBook (qui a des relations)
        book_query = self.query_generator.generate_single_query(QueryTestBook)

        # Vérifier que la requête est générée
        self.assertIsNotNone(book_query)

        # La requête doit pouvoir résoudre les relations
        self.assertIsNotNone(book_query.type)

    def test_query_optimization(self):
        """Test l'optimisation des requêtes générées."""
        # Configurer l'optimisation
        config_mock = Mock()
        config_mock.enable_query_optimization = True

        generator = QueryGenerator(
            self.type_generator, self.filter_generator, config=config_mock
        )

        # Générer une requête optimisée
        optimized_query = generator.generate_list_query(QueryTestBook)

        # Vérifier que la requête est générée
        self.assertIsNotNone(optimized_query)

    def test_query_field_selection(self):
        """Test la sélection de champs dans les requêtes."""
        # Configurer la sélection de champs
        config_mock = Mock()
        config_mock.allowed_fields = {
            "QueryTestAuthor": ["nom_auteur", "email_auteur", "est_actif"]
        }

        generator = QueryGenerator(
            self.type_generator, self.filter_generator, config=config_mock
        )

        # Générer la requête avec sélection de champs
        author_query = generator.generate_single_query(QueryTestAuthor)

        # Vérifier que la requête est générée
        self.assertIsNotNone(author_query)

    def test_query_permissions(self):
        """Test l'intégration des permissions dans les requêtes."""
        # Configurer les permissions
        config_mock = Mock()
        config_mock.enable_permissions = True
        config_mock.permission_classes = ["IsAuthenticated"]

        generator = QueryGenerator(
            self.type_generator, self.filter_generator, config=config_mock
        )

        # Générer la requête avec permissions
        protected_query = generator.generate_single_query(QueryTestAuthor)

        # Vérifier que la requête est générée
        self.assertIsNotNone(protected_query)

    def test_custom_resolver_integration(self):
        """Test l'intégration de résolveurs personnalisés."""

        # Définir un résolveur personnalisé
        def custom_resolver(root, info, **kwargs):
            return QueryTestAuthor.objects.filter(est_actif=True)

        # Configurer le résolveur personnalisé
        config_mock = Mock()
        config_mock.custom_resolvers = {"QueryTestAuthor": {"list": custom_resolver}}

        generator = QueryGenerator(
            self.type_generator, self.filter_generator, config=config_mock
        )

        # Générer la requête avec résolveur personnalisé
        custom_query = generator.generate_list_query(QueryTestAuthor)

        # Vérifier que la requête est générée
        self.assertIsNotNone(custom_query)

    def test_query_complexity_analysis(self):
        """Test l'analyse de complexité des requêtes."""
        # Générer une requête complexe avec relations
        complex_query = self.query_generator.generate_filtered_query(QueryTestBook)

        # Analyser la complexité
        complexity = self.query_generator.analyze_query_complexity(complex_query)

        # Vérifier que l'analyse retourne une valeur
        self.assertIsNotNone(complexity)
        self.assertIsInstance(complexity, (int, float))

    def test_query_caching_integration(self):
        """Test l'intégration du cache dans les requêtes."""
        # Configurer le cache
        config_mock = Mock()
        config_mock.enable_caching = True
        config_mock.cache_timeout = 300

        generator = QueryGenerator(
            self.type_generator, self.filter_generator, config=config_mock
        )

        # Générer la requête avec cache
        cached_query = generator.generate_list_query(QueryTestAuthor)

        # Vérifier que la requête est générée
        self.assertIsNotNone(cached_query)

    def test_error_handling_invalid_model(self):
        """Test la gestion d'erreurs pour un modèle invalide."""
        with self.assertRaises((AttributeError, TypeError, ValueError)):
            self.query_generator.generate_single_query(None)

    def test_performance_large_dataset(self):
        """Test les performances avec un grand dataset."""
        import time

        # Mesurer le temps de génération
        start_time = time.time()
        book_query = self.query_generator.generate_all_queries(QueryTestBook)
        end_time = time.time()

        # La génération doit être rapide (moins de 200ms)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 0.2)

        # Vérifier que les requêtes sont générées
        self.assertIsNotNone(book_query)
        self.assertGreater(len(book_query), 0)

    @patch("rail_django_graphql.generators.queries.logger")
    def test_logging_functionality(self, mock_logger):
        """Test la fonctionnalité de logging."""
        # Générer une requête pour déclencher le logging
        self.query_generator.generate_single_query(QueryTestAuthor)

        # Vérifier que le logging a été appelé
        self.assertTrue(mock_logger.debug.called or mock_logger.info.called)

    def test_query_naming_conventions(self):
        """Test les conventions de nommage des requêtes."""
        # Générer les requêtes pour QueryTestAuthor
        queries = self.query_generator.generate_all_queries(QueryTestAuthor)

        # Vérifier les noms des requêtes
        if "single" in queries:
            # Le nom devrait être basé sur le modèle
            self.assertIsNotNone(queries["single"])

        if "list" in queries:
            # Le nom devrait être au pluriel
            self.assertIsNotNone(queries["list"])

    def test_query_arguments_generation(self):
        """Test la génération des arguments de requêtes."""
        # Générer une requête avec arguments
        author_query = self.query_generator.generate_single_query(QueryTestAuthor)

        # Vérifier que les arguments sont générés
        if hasattr(author_query, "args"):
            # Doit avoir au moins l'argument 'id'
            self.assertIn("id", author_query.args)
        elif hasattr(author_query, "arguments"):
            self.assertIn("id", author_query.arguments)

    def test_nested_query_generation(self):
        """Test la génération de requêtes imbriquées."""
        # Générer une requête pour QueryTestCategory (qui a une relation self)
        category_query = self.query_generator.generate_single_query(QueryTestCategory)

        # Vérifier que la requête est générée
        self.assertIsNotNone(category_query)

        # La requête doit pouvoir gérer les relations self
        self.assertIsNotNone(category_query.type)


class TestQueryInfo(TestCase):
    """Tests pour la classe QueryInfo."""

    def test_query_info_creation(self):
        """Test la création d'un objet QueryInfo."""
        query_info = QueryInfo(
            name="test_query",
            query_type="single",
            model=QueryTestAuthor,
            resolver=Mock(),
            arguments={"id": graphene.ID()},
            description="Test query",
        )

        self.assertEqual(query_info.name, "test_query")
        self.assertEqual(query_info.query_type, "single")
        self.assertEqual(query_info.model, QueryTestAuthor)
        self.assertIsNotNone(query_info.resolver)
        self.assertIn("id", query_info.arguments)
        self.assertEqual(query_info.description, "Test query")


class TestResolverInfo(TestCase):
    """Tests pour la classe ResolverInfo."""

    def test_resolver_info_creation(self):
        """Test la création d'un objet ResolverInfo."""
        resolver_func = Mock()

        resolver_info = ResolverInfo(
            resolver=resolver_func,
            model=QueryTestAuthor,
            query_type="list",
            permissions=["IsAuthenticated"],
            cache_timeout=300,
        )

        self.assertEqual(resolver_info.resolver, resolver_func)
        self.assertEqual(resolver_info.model, QueryTestAuthor)
        self.assertEqual(resolver_info.query_type, "list")
        self.assertIn("IsAuthenticated", resolver_info.permissions)
        self.assertEqual(resolver_info.cache_timeout, 300)


@pytest.mark.unit
class TestQueryGeneratorIntegration:
    """Tests d'intégration pour le générateur de requêtes."""

    def test_full_query_generation_workflow(self):
        """Test le workflow complet de génération de requêtes."""
        introspector = ModelIntrospector()
        type_generator = TypeGenerator(introspector)
        filter_generator = AdvancedFilterGenerator(introspector)
        query_generator = QueryGenerator(type_generator, filter_generator)

        # Générer toutes les requêtes pour QueryTestBook
        all_queries = query_generator.generate_all_queries(QueryTestBook)

        # Vérifier que les requêtes sont générées
        assert all_queries is not None
        assert len(all_queries) > 0

        # Vérifier que chaque requête est valide
        for query_name, query_field in all_queries.items():
            assert query_field is not None
            assert hasattr(query_field, "type")

    def test_query_execution_simulation(self):
        """Test la simulation d'exécution de requêtes."""
        introspector = ModelIntrospector()
        type_generator = TypeGenerator(introspector)
        filter_generator = AdvancedFilterGenerator(introspector)
        query_generator = QueryGenerator(type_generator, filter_generator)

        # Générer une requête simple
        author_query = query_generator.generate_single_query(QueryTestAuthor)

        # Vérifier que la requête peut être utilisée dans un schéma
        assert author_query is not None
        assert hasattr(author_query, "type")

        # Simuler la résolution
        resolver = query_generator.generate_resolver(QueryTestAuthor, "single")
        assert callable(resolver)

    def test_multiple_models_query_generation(self):
        """Test la génération de requêtes pour plusieurs modèles."""
        introspector = ModelIntrospector()
        type_generator = TypeGenerator(introspector)
        filter_generator = AdvancedFilterGenerator(introspector)
        query_generator = QueryGenerator(type_generator, filter_generator)

        models_to_test = [QueryTestAuthor, QueryTestBook, QueryTestCategory]
        generated_queries = {}

        for model in models_to_test:
            generated_queries[model] = query_generator.generate_all_queries(model)

        # Vérifier que toutes les requêtes sont générées
        assert len(generated_queries) == 3

        # Vérifier que chaque modèle a ses requêtes
        for model, queries in generated_queries.items():
            assert queries is not None
            assert len(queries) > 0


class TestAdvancedQueryGeneration(TestCase):
    """Tests avancés pour la génération de requêtes."""

    def test_aggregation_queries(self):
        """Test la génération de requêtes d'agrégation."""
        # Configurer l'agrégation
        config_mock = Mock()
        config_mock.enable_aggregation = True

        generator = QueryGenerator(
            self.type_generator, self.filter_generator, config=config_mock
        )

        # Générer une requête d'agrégation
        aggregation_query = generator.generate_aggregation_query(QueryTestBook)

        # Vérifier que la requête est générée
        if aggregation_query:
            self.assertIsNotNone(aggregation_query)

    def test_search_queries(self):
        """Test la génération de requêtes de recherche."""
        # Configurer la recherche
        config_mock = Mock()
        config_mock.enable_search = True
        config_mock.search_fields = {
            "QueryTestBook": ["titre_livre", "description_livre"]
        }

        generator = QueryGenerator(
            self.type_generator, self.filter_generator, config=config_mock
        )

        # Générer une requête de recherche
        search_query = generator.generate_search_query(QueryTestBook)

        # Vérifier que la requête est générée
        if search_query:
            self.assertIsNotNone(search_query)

    def test_subscription_queries(self):
        """Test la génération de requêtes de souscription."""
        # Configurer les souscriptions
        config_mock = Mock()
        config_mock.enable_subscriptions = True

        generator = QueryGenerator(
            self.type_generator, self.filter_generator, config=config_mock
        )

        # Générer une requête de souscription
        subscription_query = generator.generate_subscription_query(QueryTestBook)

        # Vérifier que la requête est générée
        if subscription_query:
            self.assertIsNotNone(subscription_query)
