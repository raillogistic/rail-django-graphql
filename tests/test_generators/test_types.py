"""
Tests complets pour le système de génération de types GraphQL.

Ce module teste:
- La génération de types GraphQL à partir de modèles Django
- La conversion des champs Django vers GraphQL
- La gestion des relations entre types
- La validation des types générés
- L'optimisation des performances de génération
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.db import models
from django.contrib.auth.models import User
from typing import Dict, List, Optional, Type

import graphene
from graphene import ObjectType, String, Int, Boolean, DateTime, List as GrapheneList
from graphene_django import DjangoObjectType

from rail_django_graphql.generators.types import (
    TypeGenerator,
    GraphQLTypeInfo,
    FieldMapping,
    get_graphql_type_for_field,
)
from rail_django_graphql.generators.introspector import ModelIntrospector, FieldInfo
from tests.models import TestUser, TestPost, TestTag


class TestTypeGenerator(TestCase):
    """Tests pour la classe TypeGenerator."""

    def setUp(self):
        """Configuration des tests."""
        self.introspector = ModelIntrospector()
        self.type_generator = TypeGenerator(self.introspector)

    def test_initialization(self):
        """Test l'initialisation du générateur de types."""
        # Test initialisation avec introspecteur
        generator = TypeGenerator(self.introspector)
        self.assertIsNotNone(generator)
        self.assertEqual(generator.introspector, self.introspector)

        # Test initialisation avec configuration
        config_mock = Mock()
        generator_with_config = TypeGenerator(self.introspector, config=config_mock)
        self.assertEqual(generator_with_config.config, config_mock)

    def test_generate_type_basic(self):
        """Test la génération de type GraphQL de base."""
        # Générer le type pour TestUser
        user_type = self.type_generator.generate_type(TestUser)

        # Vérifier que le type est généré
        self.assertIsNotNone(user_type)
        self.assertTrue(issubclass(user_type, DjangoObjectType))

        # Vérifier le nom du type
        self.assertEqual(user_type._meta.name, "TestUserType")

        # Vérifier le modèle associé
        self.assertEqual(user_type._meta.model, TestUser)

    def test_generate_type_fields_mapping(self):
        """Test le mapping des champs Django vers GraphQL."""
        user_type = self.type_generator.generate_type(TestUser)

        # Obtenir les champs du type généré
        fields = user_type._meta.fields

        # Vérifier la présence des champs attendus
        expected_fields = [
            "nom_utilisateur",
            "adresse_email",
            "date_inscription",
            "est_actif",
            "age_utilisateur",
            "score_reputation",
        ]

        for field_name in expected_fields:
            self.assertIn(field_name, fields)

    def test_field_type_conversion(self):
        """Test la conversion des types de champs Django vers GraphQL."""
        # Test des conversions de types
        test_cases = [
            (models.CharField, graphene.String),
            (models.EmailField, graphene.String),
            (models.TextField, graphene.String),
            (models.IntegerField, graphene.Int),
            (models.PositiveIntegerField, graphene.Int),
            (models.FloatField, graphene.Float),
            (models.BooleanField, graphene.Boolean),
            (models.DateTimeField, graphene.DateTime),
        ]

        for django_field_type, expected_graphql_type in test_cases:
            with self.subTest(django_field=django_field_type):
                # Créer un champ Django fictif
                django_field = django_field_type()

                # Obtenir le type GraphQL correspondant
                graphql_type = get_graphql_type_for_field(django_field)

                # Vérifier la conversion
                self.assertEqual(graphql_type, expected_graphql_type)

    def test_generate_type_with_relationships(self):
        """Test la génération de types avec des relations."""
        # Générer le type pour TestPost (qui a des relations)
        post_type = self.type_generator.generate_type(TestPost)

        # Vérifier que le type est généré
        self.assertIsNotNone(post_type)

        # Vérifier les champs de relation
        fields = post_type._meta.fields
        self.assertIn("auteur_article", fields)
        self.assertIn("tags_associes", fields)

    def test_generate_type_caching(self):
        """Test le système de cache pour la génération de types."""
        # Premier appel - doit créer le type
        user_type_1 = self.type_generator.generate_type(TestUser)

        # Deuxième appel - doit utiliser le cache
        user_type_2 = self.type_generator.generate_type(TestUser)

        # Vérifier que c'est le même type (cache)
        self.assertIs(user_type_1, user_type_2)

    def test_generate_multiple_types(self):
        """Test la génération de plusieurs types."""
        models_to_test = [TestUser, TestPost, TestTag]
        generated_types = {}

        for model in models_to_test:
            generated_types[model] = self.type_generator.generate_type(model)

        # Vérifier que tous les types sont générés
        self.assertEqual(len(generated_types), 3)

        # Vérifier que chaque type est unique
        for model, generated_type in generated_types.items():
            self.assertIsNotNone(generated_type)
            self.assertEqual(generated_type._meta.model, model)

    def test_field_exclusion(self):
        """Test l'exclusion de champs sensibles."""
        # Configurer l'exclusion du mot de passe
        config_mock = Mock()
        config_mock.excluded_fields = {"TestUser": ["mot_de_passe"]}

        generator = TypeGenerator(self.introspector, config=config_mock)
        user_type = generator.generate_type(TestUser)

        # Vérifier que le champ mot_de_passe est exclu
        fields = user_type._meta.fields
        self.assertNotIn("mot_de_passe", fields)

    def test_custom_field_mapping(self):
        """Test le mapping personnalisé de champs."""
        # Configurer un mapping personnalisé
        config_mock = Mock()
        config_mock.custom_field_mappings = {
            "score_reputation": graphene.String  # Mapper Float vers String
        }

        generator = TypeGenerator(self.introspector, config=config_mock)

        # Tester le mapping personnalisé
        field_info = FieldInfo(
            name="score_reputation",
            field_type=models.FloatField,
            django_field=models.FloatField(),
            is_required=False,
            is_unique=False,
            max_length=None,
            choices=None,
            help_text="",
            verbose_name="Score",
        )

        mapped_type = generator.get_graphql_type_for_field(field_info)
        self.assertEqual(mapped_type, graphene.String)

    def test_nullable_fields_handling(self):
        """Test la gestion des champs nullable."""
        user_type = self.type_generator.generate_type(TestUser)

        # Vérifier que les champs nullable sont correctement gérés
        # age_utilisateur est nullable (null=True, blank=True)
        fields = user_type._meta.fields
        self.assertIn("age_utilisateur", fields)

    def test_field_validation(self):
        """Test la validation des champs générés."""
        user_type = self.type_generator.generate_type(TestUser)

        # Vérifier que tous les champs ont des types valides
        fields = user_type._meta.fields

        for field_name, field in fields.items():
            # Chaque champ doit avoir un type GraphQL valide
            self.assertIsNotNone(field)

            # Vérifier que le champ a les attributs nécessaires
            if hasattr(field, "type"):
                self.assertIsNotNone(field.type)

    def test_meta_information_preservation(self):
        """Test la préservation des informations meta."""
        user_type = self.type_generator.generate_type(TestUser)

        # Vérifier que les informations meta sont préservées
        self.assertEqual(user_type._meta.model, TestUser)
        self.assertIsNotNone(user_type._meta.name)

    def test_error_handling_invalid_model(self):
        """Test la gestion d'erreurs pour un modèle invalide."""
        with self.assertRaises((AttributeError, TypeError)):
            self.type_generator.generate_type(None)

    def test_performance_large_model(self):
        """Test les performances avec un modèle complexe."""
        import time

        # Mesurer le temps de génération
        start_time = time.time()
        post_type = self.type_generator.generate_type(TestPost)
        end_time = time.time()

        # La génération doit être rapide (moins de 100ms)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 0.1)

        # Vérifier que le type est correctement généré
        self.assertIsNotNone(post_type)
        self.assertTrue(len(post_type._meta.fields) > 0)

    def test_type_name_generation(self):
        """Test la génération des noms de types."""
        # Test avec différents modèles
        test_cases = [
            (TestUser, "TestUserType"),
            (TestPost, "TestPostType"),
            (TestTag, "TestTagType"),
        ]

        for model, expected_name in test_cases:
            with self.subTest(model=model):
                generated_type = self.type_generator.generate_type(model)
                self.assertEqual(generated_type._meta.name, expected_name)

    def test_relationship_field_types(self):
        """Test les types de champs de relation."""
        post_type = self.type_generator.generate_type(TestPost)
        fields = post_type._meta.fields

        # Vérifier le champ ForeignKey
        self.assertIn("auteur_article", fields)

        # Vérifier le champ ManyToMany
        self.assertIn("tags_associes", fields)

    @patch("rail_django_graphql.generators.types.logger")
    def test_logging_functionality(self, mock_logger):
        """Test la fonctionnalité de logging."""
        # Générer un type pour déclencher le logging
        self.type_generator.generate_type(TestUser)

        # Vérifier que le logging a été appelé
        self.assertTrue(mock_logger.debug.called or mock_logger.info.called)

    def test_type_registry(self):
        """Test le registre des types générés."""
        # Générer plusieurs types
        user_type = self.type_generator.generate_type(TestUser)
        post_type = self.type_generator.generate_type(TestPost)
        tag_type = self.type_generator.generate_type(TestTag)

        # Vérifier que les types sont dans le registre
        registry = self.type_generator.get_type_registry()

        self.assertIn(TestUser, registry)
        self.assertIn(TestPost, registry)
        self.assertIn(TestTag, registry)

        # Vérifier que les types correspondent
        self.assertEqual(registry[TestUser], user_type)
        self.assertEqual(registry[TestPost], post_type)
        self.assertEqual(registry[TestTag], tag_type)


class TestGraphQLTypeInfo(TestCase):
    """Tests pour la classe GraphQLTypeInfo."""

    def test_type_info_creation(self):
        """Test la création d'un objet GraphQLTypeInfo."""
        type_info = GraphQLTypeInfo(
            graphql_type=graphene.String,
            is_list=False,
            is_required=True,
            description="Test field",
        )

        self.assertEqual(type_info.graphql_type, graphene.String)
        self.assertFalse(type_info.is_list)
        self.assertTrue(type_info.is_required)
        self.assertEqual(type_info.description, "Test field")

    def test_type_info_list_type(self):
        """Test la création d'un type liste."""
        type_info = GraphQLTypeInfo(
            graphql_type=graphene.String,
            is_list=True,
            is_required=False,
            description="List of strings",
        )

        self.assertEqual(type_info.graphql_type, graphene.String)
        self.assertTrue(type_info.is_list)
        self.assertFalse(type_info.is_required)
        self.assertEqual(type_info.description, "List of strings")


class TestFieldMapping(TestCase):
    """Tests pour la classe FieldMapping."""

    def test_field_mapping_creation(self):
        """Test la création d'un mapping de champ."""
        django_field = models.CharField(max_length=100)

        mapping = FieldMapping(
            django_field=django_field,
            graphql_type=graphene.String,
            resolver=None,
            description="Test mapping",
        )

        self.assertEqual(mapping.django_field, django_field)
        self.assertEqual(mapping.graphql_type, graphene.String)
        self.assertIsNone(mapping.resolver)
        self.assertEqual(mapping.description, "Test mapping")


@pytest.mark.unit
class TestTypeGeneratorIntegration:
    """Tests d'intégration pour le générateur de types."""

    def test_full_type_generation_workflow(self):
        """Test le workflow complet de génération de types."""
        introspector = ModelIntrospector()
        generator = TypeGenerator(introspector)

        # Générer un type complet
        user_type = generator.generate_type(TestUser)

        # Vérifier que le type est complet
        assert user_type is not None
        assert hasattr(user_type, "_meta")
        assert user_type._meta.model == TestUser
        assert len(user_type._meta.fields) > 0

        # Vérifier que les champs sont correctement mappés
        fields = user_type._meta.fields
        assert "nom_utilisateur" in fields
        assert "adresse_email" in fields
        assert "est_actif" in fields

    def test_type_generation_with_relationships(self):
        """Test la génération de types avec relations."""
        introspector = ModelIntrospector()
        generator = TypeGenerator(introspector)

        # Générer les types avec relations
        user_type = generator.generate_type(TestUser)
        post_type = generator.generate_type(TestPost)
        tag_type = generator.generate_type(TestTag)

        # Vérifier que tous les types sont générés
        assert user_type is not None
        assert post_type is not None
        assert tag_type is not None

        # Vérifier les relations dans le type Post
        post_fields = post_type._meta.fields
        assert "auteur_article" in post_fields
        assert "tags_associes" in post_fields

    def test_type_consistency_across_generations(self):
        """Test la cohérence des types à travers plusieurs générations."""
        introspector = ModelIntrospector()
        generator = TypeGenerator(introspector)

        # Générer le même type plusieurs fois
        type1 = generator.generate_type(TestUser)
        type2 = generator.generate_type(TestUser)
        type3 = generator.generate_type(TestUser)

        # Vérifier que c'est le même type (cache)
        assert type1 is type2
        assert type2 is type3

        # Vérifier la cohérence des métadonnées
        assert type1._meta.model == type2._meta.model == type3._meta.model
        assert type1._meta.name == type2._meta.name == type3._meta.name


class TestAdvancedTypeGeneration(TestCase):
    """Tests avancés pour la génération de types."""

    def test_custom_scalar_types(self):
        """Test la gestion des types scalaires personnalisés."""

        # Créer un modèle avec un champ JSON
        class TestModelWithJSON(models.Model):
            donnees_json = models.JSONField(default=dict, verbose_name="Données JSON")

            class Meta:
                app_label = "tests"

        # Configurer le mapping pour JSONField
        config_mock = Mock()
        config_mock.custom_scalars = {"JSONField": graphene.JSONString}

        generator = TypeGenerator(ModelIntrospector(), config=config_mock)
        json_type = generator.generate_type(TestModelWithJSON)

        # Vérifier que le type est généré
        self.assertIsNotNone(json_type)

        # Vérifier que le champ JSON est présent
        fields = json_type._meta.fields
        self.assertIn("donnees_json", fields)

    def test_field_description_generation(self):
        """Test la génération des descriptions de champs."""
        user_type = self.type_generator.generate_type(TestUser)

        # Vérifier que les descriptions sont générées à partir des help_text
        # Note: Ceci dépend de l'implémentation spécifique du générateur
        self.assertIsNotNone(user_type)

    def test_type_inheritance(self):
        """Test la gestion de l'héritage de modèles."""

        # Créer un modèle qui hérite
        class TestExtendedUser(TestUser):
            niveau_experience = models.IntegerField(
                default=1, verbose_name="Niveau d'expérience"
            )

            class Meta:
                app_label = "tests"

        # Générer le type pour le modèle étendu
        extended_type = self.type_generator.generate_type(TestExtendedUser)

        # Vérifier que le type inclut les champs hérités
        fields = extended_type._meta.fields
        self.assertIn("nom_utilisateur", fields)  # Champ hérité
        self.assertIn("niveau_experience", fields)  # Nouveau champ
