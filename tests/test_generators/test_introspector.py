"""
Tests complets pour le système d'introspection des modèles.

Ce module teste:
- L'analyse des champs de modèles Django
- La détection des relations entre modèles
- L'extraction des méthodes et propriétés
- La validation des métadonnées
- La gestion du cache d'introspection
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.db import models
from django.contrib.auth.models import User
from typing import Dict, List, Optional

from django_graphql_auto.generators.introspector import (
    ModelIntrospector,
    FieldInfo,
    RelationshipInfo
)


# Modèles de test pour l'introspection
class IntrospectorTestAuthor(models.Model):
    """Modèle auteur pour les tests d'introspection."""
    nom_utilisateur = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name="Nom d'utilisateur",
        help_text="Nom unique de l'auteur"
    )
    email_adresse = models.EmailField(
        verbose_name="Adresse e-mail",
        help_text="Adresse e-mail de l'auteur"
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    est_actif = models.BooleanField(
        default=True,
        verbose_name="Est actif"
    )
    
    class Meta:
        app_label = 'tests'
        verbose_name = "Auteur"
        verbose_name_plural = "Auteurs"
    
    def obtenir_nom_complet(self):
        """Méthode pour obtenir le nom complet."""
        return f"{self.nom_utilisateur}"
    
    @property
    def nombre_articles(self):
        """Propriété pour compter les articles."""
        return self.articles.count()


class IntrospectorTestArticle(models.Model):
    """Modèle article pour les tests d'introspection."""
    titre_article = models.CharField(
        max_length=200,
        verbose_name="Titre de l'article",
        help_text="Titre principal de l'article"
    )
    contenu_texte = models.TextField(
        verbose_name="Contenu textuel",
        help_text="Contenu principal de l'article"
    )
    auteur_principal = models.ForeignKey(
        IntrospectorTestAuthor,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name="Auteur principal"
    )
    categories_associees = models.ManyToManyField(
        'IntrospectorTestCategory',
        blank=True,
        related_name='articles',
        verbose_name="Catégories associées"
    )
    date_publication = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de publication"
    )
    est_publie = models.BooleanField(
        default=False,
        verbose_name="Est publié"
    )
    
    class Meta:
        app_label = 'tests'
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['-date_publication']


class IntrospectorTestCategory(models.Model):
    """Modèle catégorie pour les tests d'introspection."""
    nom_categorie = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom de la catégorie"
    )
    description_courte = models.TextField(
        blank=True,
        verbose_name="Description courte"
    )
    
    class Meta:
        app_label = 'tests'
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"


class TestModelIntrospector(TestCase):
    """Tests pour la classe ModelIntrospector."""
    
    def setUp(self):
        """Configuration des tests."""
        self.introspector = ModelIntrospector()
    
    def test_initialization(self):
        """Test l'initialisation de l'introspecteur."""
        # Test initialisation par défaut
        introspector = ModelIntrospector()
        self.assertIsNotNone(introspector)
        self.assertEqual(introspector._cache, {})
        
        # Test avec configuration personnalisée
        config_mock = Mock()
        introspector_with_config = ModelIntrospector(config=config_mock)
        self.assertEqual(introspector_with_config.config, config_mock)
    
    def test_get_model_fields_basic(self):
        """Test l'extraction des champs de base d'un modèle."""
        fields = self.introspector.get_model_fields(IntrospectorTestAuthor)
        
        # Vérifier la présence des champs attendus
        field_names = [field.name for field in fields]
        self.assertIn('nom_utilisateur', field_names)
        self.assertIn('email_adresse', field_names)
        self.assertIn('date_creation', field_names)
        self.assertIn('est_actif', field_names)
        
        # Vérifier les propriétés des champs
        nom_utilisateur_field = next(f for f in fields if f.name == 'nom_utilisateur')
        self.assertEqual(nom_utilisateur_field.max_length, 100)
        self.assertTrue(nom_utilisateur_field.is_unique)
        self.assertTrue(nom_utilisateur_field.is_required)
        self.assertEqual(nom_utilisateur_field.verbose_name, "Nom d'utilisateur")
        self.assertEqual(nom_utilisateur_field.help_text, "Nom unique de l'auteur")
    
    def test_get_model_fields_types(self):
        """Test la détection correcte des types de champs."""
        fields = self.introspector.get_model_fields(IntrospectorTestAuthor)
        field_dict = {field.name: field for field in fields}
        
        # CharField
        self.assertEqual(field_dict['nom_utilisateur'].field_type, models.CharField)
        
        # EmailField
        self.assertEqual(field_dict['email_adresse'].field_type, models.EmailField)
        
        # DateTimeField
        self.assertEqual(field_dict['date_creation'].field_type, models.DateTimeField)
        
        # BooleanField
        self.assertEqual(field_dict['est_actif'].field_type, models.BooleanField)
    
    def test_get_model_relationships_foreign_key(self):
        """Test la détection des relations ForeignKey."""
        relationships = self.introspector.get_model_relationships(IntrospectorTestArticle)
        
        # Vérifier la relation ForeignKey
        self.assertIn('auteur_principal', relationships)
        auteur_rel = relationships['auteur_principal']
        
        self.assertEqual(auteur_rel.relationship_type, 'ForeignKey')
        self.assertEqual(auteur_rel.related_model, IntrospectorTestAuthor)
        self.assertEqual(auteur_rel.reverse_name, 'articles')
    
    def test_get_model_relationships_many_to_many(self):
        """Test la détection des relations ManyToMany."""
        relationships = self.introspector.get_model_relationships(IntrospectorTestArticle)
        
        # Vérifier la relation ManyToMany
        self.assertIn('categories_associees', relationships)
        categories_rel = relationships['categories_associees']
        
        self.assertEqual(categories_rel.relationship_type, 'ManyToManyField')
        self.assertEqual(categories_rel.related_model, IntrospectorTestCategory)
        self.assertEqual(categories_rel.reverse_name, 'articles')
    
    def test_get_model_methods(self):
        """Test l'extraction des méthodes du modèle."""
        methods = self.introspector.get_model_methods(IntrospectorTestAuthor)
        
        # Vérifier la présence de la méthode personnalisée
        method_names = list(methods.keys())
        self.assertIn('obtenir_nom_complet', method_names)
        
        # Vérifier les détails de la méthode
        method_info = methods['obtenir_nom_complet']
        self.assertEqual(method_info['name'], 'obtenir_nom_complet')
        self.assertIsNotNone(method_info['callable'])
        self.assertIn('Méthode pour obtenir le nom complet', method_info.get('docstring', ''))
    
    def test_get_model_properties(self):
        """Test l'extraction des propriétés du modèle."""
        properties = self.introspector.get_model_properties(IntrospectorTestAuthor)
        
        # Vérifier la présence de la propriété personnalisée
        property_names = list(properties.keys())
        self.assertIn('nombre_articles', property_names)
        
        # Vérifier les détails de la propriété
        property_info = properties['nombre_articles']
        self.assertEqual(property_info['name'], 'nombre_articles')
        self.assertIsNotNone(property_info['getter'])
    
    def test_analyze_model_complete(self):
        """Test l'analyse complète d'un modèle."""
        analysis = self.introspector.analyze_model(IntrospectorTestArticle)
        
        # Vérifier le type de retour
        self.assertIsInstance(analysis, ModelAnalysis)
        
        # Vérifier les informations de base
        self.assertEqual(analysis.model, IntrospectorTestArticle)
        self.assertEqual(analysis.model_name, 'IntrospectorTestArticle')
        
        # Vérifier la présence des champs
        self.assertIn('titre_article', analysis.fields)
        self.assertIn('contenu_texte', analysis.fields)
        self.assertIn('date_publication', analysis.fields)
        
        # Vérifier la présence des relations
        self.assertIn('auteur_principal', analysis.relationships)
        self.assertIn('categories_associees', analysis.relationships)
        
        # Vérifier les métadonnées
        self.assertEqual(analysis.meta['verbose_name'], 'Article')
        self.assertEqual(analysis.meta['verbose_name_plural'], 'Articles')
    
    def test_cache_functionality(self):
        """Test le système de cache de l'introspecteur."""
        # Premier appel - doit créer le cache
        analysis1 = self.introspector.analyze_model(IntrospectorTestAuthor)
        self.assertIn(IntrospectorTestAuthor, self.introspector._cache)
        
        # Deuxième appel - doit utiliser le cache
        analysis2 = self.introspector.analyze_model(IntrospectorTestAuthor)
        self.assertIs(analysis1, analysis2)  # Même objet en mémoire
    
    def test_field_validation(self):
        """Test la validation des champs extraits."""
        fields = self.introspector.get_model_fields(IntrospectorTestAuthor)
        
        for field in fields:
            # Vérifier que tous les champs ont les attributs requis
            self.assertIsInstance(field, FieldInfo)
            self.assertIsNotNone(field.name)
            self.assertIsNotNone(field.field_type)
            self.assertIsNotNone(field.django_field)
            self.assertIsInstance(field.is_required, bool)
            self.assertIsInstance(field.is_unique, bool)
    
    def test_relationship_validation(self):
        """Test la validation des relations extraites."""
        relationships = self.introspector.get_model_relationships(IntrospectorTestArticle)
        
        for rel_name, rel_info in relationships.items():
            # Vérifier que toutes les relations ont les attributs requis
            self.assertIsInstance(rel_info, RelationshipInfo)
            self.assertIsNotNone(rel_info.name)
            self.assertIsNotNone(rel_info.related_model)
            self.assertIsNotNone(rel_info.relationship_type)
            self.assertIn(rel_info.relationship_type, ['ForeignKey', 'ManyToManyField', 'OneToOneField'])
    
    def test_error_handling_invalid_model(self):
        """Test la gestion d'erreurs pour un modèle invalide."""
        with self.assertRaises(AttributeError):
            self.introspector.analyze_model(None)
    
    def test_field_choices_detection(self):
        """Test la détection des choix de champs."""
        # Créer un modèle avec des choix
        class TestModelWithChoices(models.Model):
            STATUS_CHOICES = [
                ('draft', 'Brouillon'),
                ('published', 'Publié'),
                ('archived', 'Archivé'),
            ]
            statut = models.CharField(
                max_length=20,
                choices=STATUS_CHOICES,
                default='draft',
                verbose_name="Statut"
            )
            
            class Meta:
                app_label = 'tests'
        
        fields = self.introspector.get_model_fields(TestModelWithChoices)
        statut_field = next(f for f in fields if f.name == 'statut')
        
        self.assertIsNotNone(statut_field.choices)
        self.assertEqual(len(statut_field.choices), 3)
        self.assertIn(('draft', 'Brouillon'), statut_field.choices)
    
    def test_performance_with_large_model(self):
        """Test les performances avec un modèle complexe."""
        import time
        
        # Mesurer le temps d'analyse
        start_time = time.time()
        analysis = self.introspector.analyze_model(IntrospectorTestArticle)
        end_time = time.time()
        
        # L'analyse doit être rapide (moins de 100ms)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 0.1)
        
        # Vérifier que l'analyse est complète
        self.assertIsNotNone(analysis)
        self.assertGreater(len(analysis.fields), 0)
        self.assertGreater(len(analysis.relationships), 0)
    
    @patch('django_graphql_auto.generators.introspector.logger')
    def test_logging_functionality(self, mock_logger):
        """Test la fonctionnalité de logging."""
        # Analyser un modèle pour déclencher le logging
        self.introspector.analyze_model(IntrospectorTestAuthor)
        
        # Vérifier que le logging a été appelé
        self.assertTrue(mock_logger.debug.called or mock_logger.info.called)
    
    def test_meta_information_extraction(self):
        """Test l'extraction des informations meta du modèle."""
        analysis = self.introspector.analyze_model(IntrospectorTestArticle)
        
        # Vérifier les informations meta
        self.assertIn('verbose_name', analysis.meta)
        self.assertIn('verbose_name_plural', analysis.meta)
        self.assertIn('ordering', analysis.meta)
        
        self.assertEqual(analysis.meta['verbose_name'], 'Article')
        self.assertEqual(analysis.meta['verbose_name_plural'], 'Articles')
        self.assertEqual(analysis.meta['ordering'], ['-date_publication'])
    
    def test_field_constraints_detection(self):
        """Test la détection des contraintes de champs."""
        fields = self.introspector.get_model_fields(IntrospectorTestAuthor)
        field_dict = {field.name: field for field in fields}
        
        # Vérifier les contraintes de longueur
        nom_field = field_dict['nom_utilisateur']
        self.assertEqual(nom_field.max_length, 100)
        
        # Vérifier les contraintes d'unicité
        self.assertTrue(nom_field.is_unique)
        
        # Vérifier les champs requis
        self.assertTrue(nom_field.is_required)
        
        # Vérifier les champs optionnels
        description_fields = self.introspector.get_model_fields(IntrospectorTestCategory)
        description_field = next(f for f in description_fields if f.name == 'description_courte')
        self.assertFalse(description_field.is_required)


class TestFieldInfo(TestCase):
    """Tests pour la classe FieldInfo."""
    
    def test_field_info_creation(self):
        """Test la création d'un objet FieldInfo."""
        django_field = models.CharField(max_length=100)
        
        field_info = FieldInfo(
            name='test_field',
            field_type=models.CharField,
            django_field=django_field,
            is_required=True,
            is_unique=False,
            max_length=100,
            choices=None,
            help_text='Test help text',
            verbose_name='Test Field'
        )
        
        self.assertEqual(field_info.name, 'test_field')
        self.assertEqual(field_info.field_type, models.CharField)
        self.assertEqual(field_info.django_field, django_field)
        self.assertTrue(field_info.is_required)
        self.assertFalse(field_info.is_unique)
        self.assertEqual(field_info.max_length, 100)
        self.assertIsNone(field_info.choices)
        self.assertEqual(field_info.help_text, 'Test help text')
        self.assertEqual(field_info.verbose_name, 'Test Field')


class TestRelationshipInfo(TestCase):
    """Tests pour la classe RelationshipInfo."""
    
    def test_relationship_info_creation(self):
        """Test la création d'un objet RelationshipInfo."""
        relationship_info = RelationshipInfo(
            name='test_relation',
            related_model=IntrospectorTestAuthor,
            relationship_type='ForeignKey',
            reverse_name='test_reverse',
            through_model=None
        )
        
        self.assertEqual(relationship_info.name, 'test_relation')
        self.assertEqual(relationship_info.related_model, IntrospectorTestAuthor)
        self.assertEqual(relationship_info.relationship_type, 'ForeignKey')
        self.assertEqual(relationship_info.reverse_name, 'test_reverse')
        self.assertIsNone(relationship_info.through_model)


@pytest.mark.unit
class TestIntrospectorIntegration:
    """Tests d'intégration pour l'introspecteur."""
    
    def test_full_workflow(self):
        """Test le workflow complet d'introspection."""
        introspector = ModelIntrospector()
        
        # Analyser le modèle
        analysis = introspector.analyze_model(IntrospectorTestArticle)
        
        # Vérifier que l'analyse est complète
        assert analysis is not None
        assert len(analysis.fields) > 0
        assert len(analysis.relationships) > 0
        assert analysis.model_name == 'IntrospectorTestArticle'
        
        # Vérifier la cohérence des données
        for field_name, field_info in analysis.fields.items():
            assert field_info.name == field_name
            assert field_info.field_type is not None
        
        for rel_name, rel_info in analysis.relationships.items():
            assert rel_info.name == rel_name
            assert rel_info.related_model is not None
    
    def test_multiple_models_analysis(self):
        """Test l'analyse de plusieurs modèles."""
        introspector = ModelIntrospector()
        
        models_to_analyze = [IntrospectorTestAuthor, IntrospectorTestArticle, IntrospectorTestCategory]
        analyses = {}
        
        for model in models_to_analyze:
            analyses[model] = introspector.analyze_model(model)
        
        # Vérifier que tous les modèles ont été analysés
        assert len(analyses) == 3
        
        # Vérifier que chaque analyse est unique
        for model, analysis in analyses.items():
            assert analysis.model == model
            assert analysis.model_name == model.__name__