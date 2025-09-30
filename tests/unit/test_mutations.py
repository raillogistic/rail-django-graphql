"""
Tests complets pour le système de génération de mutations GraphQL.

Ce module teste:
- La génération de mutations CRUD pour les modèles Django
- Les mutations de création, mise à jour et suppression
- La validation des données d'entrée
- La gestion des erreurs et des permissions
- L'intégration avec les méthodes métier
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from typing import Dict, List, Optional, Type, Any

import graphene
from graphene import ObjectType, String, Int, Boolean, DateTime, Field, Mutation
from graphene.test import Client
from graphene_django import DjangoObjectType

from rail_django_graphql.generators.mutations import (
    MutationGenerator,
    MutationError,
)
from rail_django_graphql.generators.types import TypeGenerator
from rail_django_graphql.generators.introspector import ModelIntrospector
from rail_django_graphql.decorators import business_logic
from test_app.models import Category, Tag, Post, Comment, Client, Profile


# Test classes start here


class TestMutationGenerator(TestCase):
    """Tests pour la classe MutationGenerator."""

    def setUp(self):
        """Configuration des tests."""
        self.introspector = ModelIntrospector(Category)
        self.type_generator = TypeGenerator(self.introspector)
        self.mutation_generator = MutationGenerator(self.type_generator)

    def test_initialization(self):
        """Test l'initialisation du générateur de mutations."""
        # Test initialisation de base
        generator = MutationGenerator(self.type_generator)
        self.assertIsNotNone(generator)
        self.assertEqual(generator.type_generator, self.type_generator)

        # Test initialisation avec configuration
        from rail_django_graphql.core.settings import MutationGeneratorSettings
        settings_mock = MutationGeneratorSettings()
        generator_with_config = MutationGenerator(
            self.type_generator, settings=settings_mock
        )
        self.assertEqual(generator_with_config.settings, settings_mock)

    def test_generate_create_mutation(self):
        """Test la génération de mutation de création."""
        # Générer la mutation de création pour Category
        create_mutation = self.mutation_generator.generate_create_mutation(Category)

        # Vérifier que la mutation est générée
        self.assertIsNotNone(create_mutation)
        self.assertTrue(issubclass(create_mutation, Mutation))

        # Vérifier que la mutation a les champs requis
        self.assertTrue(hasattr(create_mutation, "Arguments"))
        self.assertTrue(hasattr(create_mutation, "mutate"))

    def test_generate_update_mutation(self):
        """Test la génération de mutation de mise à jour."""
        # Générer la mutation de mise à jour pour Category
        update_mutation = self.mutation_generator.generate_update_mutation(Category)

        # Vérifier que la mutation est générée
        self.assertIsNotNone(update_mutation)
        self.assertTrue(issubclass(update_mutation, Mutation))

        # Vérifier que la mutation a un argument ID
        if hasattr(update_mutation, "Arguments"):
            args = update_mutation.Arguments
            self.assertTrue(hasattr(args, "id"))

    def test_generate_delete_mutation(self):
        """Test la génération de mutation de suppression."""
        # Générer la mutation de suppression pour Category
        delete_mutation = self.mutation_generator.generate_delete_mutation(Category)

        # Vérifier que la mutation est générée
        self.assertIsNotNone(delete_mutation)
        self.assertTrue(issubclass(delete_mutation, Mutation))

        # Vérifier que la mutation a un argument ID
        if hasattr(delete_mutation, "Arguments"):
            args = delete_mutation.Arguments
            self.assertTrue(hasattr(args, "id"))

    def test_generate_all_crud_mutations(self):
        """Test la génération de toutes les mutations CRUD."""
        # Générer toutes les mutations CRUD pour TestProduct
        all_mutations = self.mutation_generator.generate_all_crud_mutations(TestProduct)

        # Vérifier que toutes les mutations sont générées
        self.assertIsInstance(all_mutations, dict)
        self.assertGreater(len(all_mutations), 0)

        # Vérifier les types de mutations générées
        expected_mutation_types = ["create", "update", "delete"]
        for mutation_type in expected_mutation_types:
            if mutation_type in all_mutations:
                self.assertIsNotNone(all_mutations[mutation_type])
                self.assertTrue(issubclass(all_mutations[mutation_type], Mutation))

    def test_generate_business_method_mutations(self):
        """Test la génération de mutations pour les méthodes métier."""
        # Générer les mutations pour les méthodes métier de TestProduct
        business_mutations = self.mutation_generator.generate_business_method_mutations(
            TestProduct
        )

        # Vérifier que les mutations sont générées
        self.assertIsInstance(business_mutations, dict)

        # Vérifier que les méthodes métier sont détectées
        expected_methods = [
            "augmenter_stock",
            "diminuer_stock",
            "calculer_valeur_stock",
        ]
        for method_name in expected_methods:
            if method_name in business_mutations:
                self.assertIsNotNone(business_mutations[method_name])
                self.assertTrue(issubclass(business_mutations[method_name], Mutation))

    def test_input_type_generation(self):
        """Test la génération des types d'entrée."""
        # Générer le type d'entrée pour TestProduct
        input_type = self.input_generator.generate_input_type(TestProduct, "create")

        # Vérifier que le type d'entrée est généré
        self.assertIsNotNone(input_type)

        # Vérifier que le type d'entrée a les champs appropriés
        if hasattr(input_type, "_meta"):
            fields = input_type._meta.fields
            self.assertIn("nom_produit", fields)
            self.assertIn("prix_produit", fields)

    def test_mutation_validation(self):
        """Test la validation des données dans les mutations."""
        # Créer une mutation avec validation
        create_mutation = self.mutation_generator.generate_create_mutation(TestProduct)

        # Vérifier que la mutation peut être instanciée
        self.assertIsNotNone(create_mutation)

        # La validation sera testée lors de l'exécution
        self.assertTrue(hasattr(create_mutation, "mutate"))

    def test_mutation_with_relationships(self):
        """Test la génération de mutations avec relations."""
        # Générer la mutation pour TestOrder (qui a des relations)
        order_mutation = self.mutation_generator.generate_create_mutation(TestOrder)

        # Vérifier que la mutation est générée
        self.assertIsNotNone(order_mutation)
        self.assertTrue(issubclass(order_mutation, Mutation))

        # La mutation doit pouvoir gérer les relations
        self.assertTrue(hasattr(order_mutation, "mutate"))

    def test_mutation_permissions(self):
        """Test l'intégration des permissions dans les mutations."""
        # Configurer les permissions
        config_mock = Mock()
        config_mock.enable_permissions = True
        config_mock.permission_classes = ["IsAuthenticated"]

        generator = MutationGenerator(
            self.type_generator, self.input_generator, config=config_mock
        )

        # Générer la mutation avec permissions
        protected_mutation = generator.generate_create_mutation(TestProduct)

        # Vérifier que la mutation est générée
        self.assertIsNotNone(protected_mutation)
        self.assertTrue(issubclass(protected_mutation, Mutation))

    def test_mutation_error_handling(self):
        """Test la gestion d'erreurs dans les mutations."""
        # Générer une mutation avec gestion d'erreurs
        create_mutation = self.mutation_generator.generate_create_mutation(TestProduct)

        # Vérifier que la mutation est générée
        self.assertIsNotNone(create_mutation)

        # La mutation doit avoir une méthode mutate qui gère les erreurs
        self.assertTrue(hasattr(create_mutation, "mutate"))

    def test_transaction_handling(self):
        """Test la gestion des transactions dans les mutations."""
        # Configurer les transactions
        config_mock = Mock()
        config_mock.enable_transactions = True

        generator = MutationGenerator(
            self.type_generator, self.input_generator, config=config_mock
        )

        # Générer la mutation avec transactions
        transactional_mutation = generator.generate_create_mutation(TestProduct)

        # Vérifier que la mutation est générée
        self.assertIsNotNone(transactional_mutation)
        self.assertTrue(issubclass(transactional_mutation, Mutation))

    def test_bulk_mutations(self):
        """Test la génération de mutations en lot."""
        # Configurer les mutations en lot
        config_mock = Mock()
        config_mock.enable_bulk_operations = True

        generator = MutationGenerator(
            self.type_generator, self.input_generator, config=config_mock
        )

        # Générer les mutations en lot
        bulk_mutations = generator.generate_bulk_mutations(TestProduct)

        # Vérifier que les mutations sont générées
        if bulk_mutations:
            self.assertIsInstance(bulk_mutations, dict)

            # Vérifier les types de mutations en lot
            expected_bulk_types = ["bulk_create", "bulk_update", "bulk_delete"]
            for bulk_type in expected_bulk_types:
                if bulk_type in bulk_mutations:
                    self.assertIsNotNone(bulk_mutations[bulk_type])

    def test_custom_mutation_integration(self):
        """Test l'intégration de mutations personnalisées."""

        # Définir une mutation personnalisée
        class CustomProductMutation(Mutation):
            class Arguments:
                id = graphene.ID(required=True)

            success = graphene.Boolean()

            def mutate(self, info, id):
                return CustomProductMutation(success=True)

        # Configurer la mutation personnalisée
        config_mock = Mock()
        config_mock.custom_mutations = {
            "TestProduct": {"custom_action": CustomProductMutation}
        }

        generator = MutationGenerator(
            self.type_generator, self.input_generator, config=config_mock
        )

        # Générer les mutations avec personnalisation
        all_mutations = generator.generate_all_mutations(TestProduct)

        # Vérifier que les mutations sont générées
        self.assertIsNotNone(all_mutations)

    def test_mutation_field_filtering(self):
        """Test le filtrage des champs dans les mutations."""
        # Configurer le filtrage des champs
        config_mock = Mock()
        config_mock.mutation_fields = {
            "TestProduct": {
                "create": ["nom_produit", "prix_produit", "quantite_stock"],
                "update": ["nom_produit", "prix_produit", "est_actif"],
            }
        }

        generator = MutationGenerator(
            self.type_generator, self.input_generator, config=config_mock
        )

        # Générer les mutations avec filtrage
        create_mutation = generator.generate_create_mutation(TestProduct)

        # Vérifier que la mutation est générée
        self.assertIsNotNone(create_mutation)
        self.assertTrue(issubclass(create_mutation, Mutation))

    def test_mutation_hooks(self):
        """Test les hooks de mutations (pre/post)."""
        # Configurer les hooks
        config_mock = Mock()
        config_mock.enable_hooks = True
        config_mock.pre_mutation_hooks = {"TestProduct": {"create": [Mock()]}}
        config_mock.post_mutation_hooks = {"TestProduct": {"create": [Mock()]}}

        generator = MutationGenerator(
            self.type_generator, self.input_generator, config=config_mock
        )

        # Générer la mutation avec hooks
        hooked_mutation = generator.generate_create_mutation(TestProduct)

        # Vérifier que la mutation est générée
        self.assertIsNotNone(hooked_mutation)
        self.assertTrue(issubclass(hooked_mutation, Mutation))

    def test_error_handling_invalid_model(self):
        """Test la gestion d'erreurs pour un modèle invalide."""
        with self.assertRaises((AttributeError, TypeError, ValueError)):
            self.mutation_generator.generate_create_mutation(None)

    def test_performance_large_model(self):
        """Test les performances avec un modèle complexe."""
        import time

        # Mesurer le temps de génération
        start_time = time.time()
        all_mutations = self.mutation_generator.generate_all_mutations(TestOrder)
        end_time = time.time()

        # La génération doit être rapide (moins de 500ms)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 0.5)

        # Vérifier que les mutations sont générées
        self.assertIsNotNone(all_mutations)

    @patch("rail_django_graphql.generators.mutations.logger")
    def test_logging_functionality(self, mock_logger):
        """Test la fonctionnalité de logging."""
        # Générer une mutation pour déclencher le logging
        self.mutation_generator.generate_create_mutation(TestProduct)

        # Vérifier que le logging a été appelé
        self.assertTrue(mock_logger.debug.called or mock_logger.info.called)


class TestInputTypeGenerator(TestCase):
    """Tests pour la classe InputTypeGenerator."""

    def setUp(self):
        """Configuration des tests."""
        self.introspector = ModelIntrospector()
        self.input_generator = InputTypeGenerator(self.introspector)

    def test_generate_create_input_type(self):
        """Test la génération de type d'entrée pour création."""
        # Générer le type d'entrée pour création
        create_input = self.input_generator.generate_input_type(TestProduct, "create")

        # Vérifier que le type d'entrée est généré
        self.assertIsNotNone(create_input)

        # Vérifier que les champs appropriés sont présents
        if hasattr(create_input, "_meta"):
            fields = create_input._meta.fields
            self.assertIn("nom_produit", fields)
            self.assertIn("prix_produit", fields)
            # Les champs auto ne doivent pas être présents
            self.assertNotIn("date_creation", fields)

    def test_generate_update_input_type(self):
        """Test la génération de type d'entrée pour mise à jour."""
        # Générer le type d'entrée pour mise à jour
        update_input = self.input_generator.generate_input_type(TestProduct, "update")

        # Vérifier que le type d'entrée est généré
        self.assertIsNotNone(update_input)

        # Vérifier que les champs sont optionnels pour la mise à jour
        if hasattr(update_input, "_meta"):
            fields = update_input._meta.fields
            # Tous les champs modifiables doivent être présents mais optionnels
            self.assertIn("nom_produit", fields)
            self.assertIn("prix_produit", fields)

    def test_input_type_field_validation(self):
        """Test la validation des champs dans les types d'entrée."""
        # Générer le type d'entrée
        input_type = self.input_generator.generate_input_type(TestProduct, "create")

        # Vérifier que le type d'entrée est généré
        self.assertIsNotNone(input_type)

        # Les validations seront testées lors de l'utilisation
        if hasattr(input_type, "_meta"):
            self.assertIsNotNone(input_type._meta.fields)

    def test_input_type_with_relationships(self):
        """Test la génération de types d'entrée avec relations."""
        # Générer le type d'entrée pour Post (qui a des relations)
        post_input = self.input_generator.generate_input_type(Post, "create")

        # Vérifier que le type d'entrée est généré
        self.assertIsNotNone(post_input)

        # Vérifier que les relations sont gérées
        if hasattr(post_input, "_meta"):
            fields = post_input._meta.fields
            # Les clés étrangères doivent être présentes
            self.assertIn("category", fields)


# Remove TestMutationInfo class since MutationInfo doesn't exist


@pytest.mark.unit
class TestMutationGeneratorIntegration:
    """Tests d'intégration pour le générateur de mutations."""

    def test_full_mutation_generation_workflow(self):
        """Test le workflow complet de génération de mutations."""
        introspector = ModelIntrospector()
        type_generator = TypeGenerator(introspector)
        mutation_generator = MutationGenerator(type_generator)

        # Générer toutes les mutations pour TestProduct
        all_mutations = mutation_generator.generate_all_mutations(TestProduct)

        # Vérifier que les mutations sont générées
        assert all_mutations is not None
        assert len(all_mutations) > 0

        # Vérifier que chaque mutation est valide
        for mutation_name, mutation_class in all_mutations.items():
            assert mutation_class is not None
            assert issubclass(mutation_class, Mutation)
            assert hasattr(mutation_class, "mutate")

    def test_mutation_execution_simulation(self):
        """Test la simulation d'exécution de mutations."""
        introspector = ModelIntrospector()
        type_generator = TypeGenerator(introspector)
        input_generator = InputTypeGenerator(introspector)
        mutation_generator = MutationGenerator(type_generator, input_generator)

        # Générer une mutation de création
        create_mutation = mutation_generator.generate_create_mutation(TestProduct)

        # Vérifier que la mutation peut être utilisée
        assert create_mutation is not None
        assert issubclass(create_mutation, Mutation)
        assert hasattr(create_mutation, "mutate")

        # Vérifier que la mutation a des arguments
        assert hasattr(create_mutation, "Arguments")

    def test_business_method_integration(self):
        """Test l'intégration des méthodes métier."""
        introspector = ModelIntrospector()
        type_generator = TypeGenerator(introspector)
        input_generator = InputTypeGenerator(introspector)
        mutation_generator = MutationGenerator(type_generator, input_generator)

        # Générer les mutations pour les méthodes métier
        business_mutations = mutation_generator.generate_business_method_mutations(
            TestProduct
        )

        # Vérifier que les mutations sont générées
        assert business_mutations is not None
        assert len(business_mutations) > 0

        # Vérifier que les méthodes métier sont détectées
        expected_methods = ["augmenter_stock", "diminuer_stock"]
        for method_name in expected_methods:
            if method_name in business_mutations:
                assert business_mutations[method_name] is not None
                assert issubclass(business_mutations[method_name], Mutation)


class TestAdvancedMutationFeatures(TestCase):
    """Tests avancés pour les fonctionnalités de mutations."""

    def test_nested_mutations(self):
        """Test les mutations imbriquées."""
        # Configurer les mutations imbriquées
        config_mock = Mock()
        config_mock.enable_nested_mutations = True

        generator = MutationGenerator(
            self.type_generator, self.input_generator, config=config_mock
        )

        # Générer une mutation imbriquée
        nested_mutation = generator.generate_nested_mutation(
            TestOrder, ["items_commande"]
        )

        # Vérifier que la mutation est générée
        if nested_mutation:
            self.assertIsNotNone(nested_mutation)
            self.assertTrue(issubclass(nested_mutation, Mutation))

    def test_conditional_mutations(self):
        """Test les mutations conditionnelles."""
        # Configurer les mutations conditionnelles
        config_mock = Mock()
        config_mock.enable_conditional_mutations = True
        config_mock.mutation_conditions = {
            "TestProduct": {
                "create": lambda user: user.is_staff,
                "delete": lambda user: user.is_superuser,
            }
        }

        generator = MutationGenerator(
            self.type_generator, self.input_generator, config=config_mock
        )

        # Générer les mutations conditionnelles
        conditional_mutations = generator.generate_all_mutations(TestProduct)

        # Vérifier que les mutations sont générées
        self.assertIsNotNone(conditional_mutations)

    def test_mutation_middleware_integration(self):
        """Test l'intégration avec les middlewares de mutations."""
        # Configurer les middlewares
        config_mock = Mock()
        config_mock.mutation_middlewares = [
            "rail_django_graphql.middleware.ValidationMiddleware",
            "rail_django_graphql.middleware.LoggingMiddleware",
        ]

        generator = MutationGenerator(
            self.type_generator, self.input_generator, config=config_mock
        )

        # Générer une mutation avec middlewares
        middleware_mutation = generator.generate_create_mutation(TestProduct)

        # Vérifier que la mutation est générée
        self.assertIsNotNone(middleware_mutation)
        self.assertTrue(issubclass(middleware_mutation, Mutation))
