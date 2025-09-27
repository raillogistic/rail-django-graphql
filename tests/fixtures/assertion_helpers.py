"""
Helpers d'assertion pour les tests GraphQL.

Ce module fournit:
- Des assertions spécialisées pour GraphQL
- Des validateurs de données
- Des assertions de performance
- Des helpers de comparaison
"""

import pytest
from typing import Dict, List, Any, Optional, Union, Type, Callable
from decimal import Decimal
from datetime import datetime, date, timedelta
import json
import re
import math

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

import graphene
from graphql import GraphQLError
from graphene.test import Client

from tests.fixtures.test_utilities import TestResult, PerformanceMetrics


# ============================================================================
# ASSERTIONS GRAPHQL
# ============================================================================

class GraphQLAssertions:
    """Assertions spécialisées pour GraphQL."""
    
    @staticmethod
    def assert_query_success(result: TestResult, message: str = None):
        """Vérifie qu'une requête GraphQL a réussi."""
        error_msg = message or f"La requête GraphQL a échoué: {result.errors}"
        assert result.success, error_msg
        assert result.data is not None, "Les données de la requête sont None"
    
    @staticmethod
    def assert_query_failure(result: TestResult, message: str = None):
        """Vérifie qu'une requête GraphQL a échoué."""
        error_msg = message or "La requête GraphQL devrait avoir échoué"
        assert not result.success, error_msg
        assert len(result.errors) > 0, "Aucune erreur trouvée dans la requête échouée"
    
    @staticmethod
    def assert_error_count(result: TestResult, expected_count: int):
        """Vérifie le nombre d'erreurs GraphQL."""
        actual_count = len(result.errors) if result.errors else 0
        assert actual_count == expected_count, \
            f"Nombre d'erreurs incorrect: {actual_count} != {expected_count}"
    
    @staticmethod
    def assert_error_message_contains(result: TestResult, message: str):
        """Vérifie qu'une erreur contient un message spécifique."""
        assert not result.success, "La requête devrait avoir échoué"
        error_messages = ' '.join(result.errors)
        assert message in error_messages, \
            f"Message '{message}' non trouvé dans les erreurs: {result.errors}"
    
    @staticmethod
    def assert_error_type(result: TestResult, error_type: str):
        """Vérifie le type d'erreur GraphQL."""
        assert not result.success, "La requête devrait avoir échoué"
        
        # Rechercher le type d'erreur dans les messages
        error_messages = ' '.join(result.errors)
        assert error_type.lower() in error_messages.lower(), \
            f"Type d'erreur '{error_type}' non trouvé dans: {result.errors}"
    
    @staticmethod
    def assert_field_exists(result: TestResult, field_path: str):
        """Vérifie qu'un champ existe dans les données."""
        assert result.success, f"La requête a échoué: {result.errors}"
        
        current_data = result.data
        path_parts = field_path.split('.')
        
        for part in path_parts:
            assert isinstance(current_data, dict), \
                f"Données non-dict à '{part}' dans le chemin '{field_path}'"
            assert part in current_data, \
                f"Champ '{part}' manquant dans le chemin '{field_path}'"
            current_data = current_data[part]
    
    @staticmethod
    def assert_field_value(result: TestResult, field_path: str, expected_value: Any):
        """Vérifie la valeur d'un champ."""
        GraphQLAssertions.assert_field_exists(result, field_path)
        
        current_data = result.data
        path_parts = field_path.split('.')
        
        for part in path_parts:
            current_data = current_data[part]
        
        assert current_data == expected_value, \
            f"Valeur incorrecte pour '{field_path}': {current_data} != {expected_value}"
    
    @staticmethod
    def assert_field_type(result: TestResult, field_path: str, expected_type: Type):
        """Vérifie le type d'un champ."""
        GraphQLAssertions.assert_field_exists(result, field_path)
        
        current_data = result.data
        path_parts = field_path.split('.')
        
        for part in path_parts:
            current_data = current_data[part]
        
        assert isinstance(current_data, expected_type), \
            f"Type incorrect pour '{field_path}': {type(current_data)} != {expected_type}"
    
    @staticmethod
    def assert_list_length(result: TestResult, field_path: str, expected_length: int):
        """Vérifie la longueur d'une liste."""
        GraphQLAssertions.assert_field_type(result, field_path, list)
        
        current_data = result.data
        path_parts = field_path.split('.')
        
        for part in path_parts:
            current_data = current_data[part]
        
        actual_length = len(current_data)
        assert actual_length == expected_length, \
            f"Longueur incorrecte pour '{field_path}': {actual_length} != {expected_length}"
    
    @staticmethod
    def assert_list_contains(result: TestResult, field_path: str, expected_item: Any):
        """Vérifie qu'une liste contient un élément."""
        GraphQLAssertions.assert_field_type(result, field_path, list)
        
        current_data = result.data
        path_parts = field_path.split('.')
        
        for part in path_parts:
            current_data = current_data[part]
        
        assert expected_item in current_data, \
            f"Élément '{expected_item}' non trouvé dans '{field_path}': {current_data}"
    
    @staticmethod
    def assert_list_all_have_field(result: TestResult, field_path: str, required_field: str):
        """Vérifie que tous les éléments d'une liste ont un champ."""
        GraphQLAssertions.assert_field_type(result, field_path, list)
        
        current_data = result.data
        path_parts = field_path.split('.')
        
        for part in path_parts:
            current_data = current_data[part]
        
        for i, item in enumerate(current_data):
            assert isinstance(item, dict), \
                f"Élément {i} de '{field_path}' n'est pas un dict"
            assert required_field in item, \
                f"Champ '{required_field}' manquant dans l'élément {i} de '{field_path}'"
    
    @staticmethod
    def assert_pagination_info(result: TestResult, field_path: str):
        """Vérifie les informations de pagination."""
        pagination_path = f"{field_path}.pageInfo"
        GraphQLAssertions.assert_field_exists(result, pagination_path)
        
        # Vérifier les champs de pagination requis
        required_fields = ['hasNextPage', 'hasPreviousPage', 'startCursor', 'endCursor']
        for field in required_fields:
            GraphQLAssertions.assert_field_exists(result, f"{pagination_path}.{field}")
    
    @staticmethod
    def assert_connection_structure(result: TestResult, field_path: str):
        """Vérifie la structure d'une connexion GraphQL."""
        # Vérifier les champs de connexion
        GraphQLAssertions.assert_field_exists(result, f"{field_path}.edges")
        GraphQLAssertions.assert_field_exists(result, f"{field_path}.pageInfo")
        
        # Vérifier la structure des edges
        GraphQLAssertions.assert_field_type(result, f"{field_path}.edges", list)
        
        # Si il y a des edges, vérifier leur structure
        current_data = result.data
        path_parts = field_path.split('.')
        
        for part in path_parts:
            current_data = current_data[part]
        
        if current_data['edges']:
            first_edge = current_data['edges'][0]
            assert 'node' in first_edge, "Champ 'node' manquant dans l'edge"
            assert 'cursor' in first_edge, "Champ 'cursor' manquant dans l'edge"


# ============================================================================
# ASSERTIONS DE DONNÉES
# ============================================================================

class DataAssertions:
    """Assertions pour la validation de données."""
    
    @staticmethod
    def assert_valid_id(value: Any, allow_none: bool = False):
        """Vérifie qu'une valeur est un ID valide."""
        if allow_none and value is None:
            return
        
        assert value is not None, "L'ID ne peut pas être None"
        
        # Accepter les strings et les entiers
        if isinstance(value, str):
            assert value.isdigit() or value.isalnum(), f"ID string invalide: {value}"
        elif isinstance(value, int):
            assert value > 0, f"ID entier invalide: {value}"
        else:
            pytest.fail(f"Type d'ID invalide: {type(value)}")
    
    @staticmethod
    def assert_valid_email(email: str):
        """Vérifie qu'un email est valide."""
        assert email is not None, "L'email ne peut pas être None"
        assert isinstance(email, str), f"L'email doit être une string: {type(email)}"
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        assert re.match(email_pattern, email), f"Format d'email invalide: {email}"
    
    @staticmethod
    def assert_valid_url(url: str):
        """Vérifie qu'une URL est valide."""
        assert url is not None, "L'URL ne peut pas être None"
        assert isinstance(url, str), f"L'URL doit être une string: {type(url)}"
        
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        assert re.match(url_pattern, url), f"Format d'URL invalide: {url}"
    
    @staticmethod
    def assert_valid_date(date_value: Any, date_format: str = None):
        """Vérifie qu'une date est valide."""
        if isinstance(date_value, str):
            if date_format:
                try:
                    datetime.strptime(date_value, date_format)
                except ValueError:
                    pytest.fail(f"Date invalide '{date_value}' pour le format '{date_format}'")
            else:
                # Essayer les formats ISO
                iso_patterns = [
                    r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
                    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO datetime
                ]
                
                valid = any(re.match(pattern, date_value) for pattern in iso_patterns)
                assert valid, f"Format de date invalide: {date_value}"
        
        elif isinstance(date_value, (date, datetime)):
            # Les objets date/datetime sont valides
            pass
        else:
            pytest.fail(f"Type de date invalide: {type(date_value)}")
    
    @staticmethod
    def assert_valid_decimal(decimal_value: Any, max_digits: int = None, decimal_places: int = None):
        """Vérifie qu'une valeur décimale est valide."""
        if isinstance(decimal_value, str):
            try:
                decimal_obj = Decimal(decimal_value)
            except (ValueError, TypeError):
                pytest.fail(f"Valeur décimale invalide: {decimal_value}")
        elif isinstance(decimal_value, (int, float)):
            decimal_obj = Decimal(str(decimal_value))
        elif isinstance(decimal_value, Decimal):
            decimal_obj = decimal_value
        else:
            pytest.fail(f"Type décimal invalide: {type(decimal_value)}")
        
        if max_digits is not None:
            # Vérifier le nombre total de chiffres
            sign, digits, exponent = decimal_obj.as_tuple()
            total_digits = len(digits)
            assert total_digits <= max_digits, \
                f"Trop de chiffres: {total_digits} > {max_digits}"
        
        if decimal_places is not None:
            # Vérifier le nombre de décimales
            sign, digits, exponent = decimal_obj.as_tuple()
            actual_places = -exponent if exponent < 0 else 0
            assert actual_places <= decimal_places, \
                f"Trop de décimales: {actual_places} > {decimal_places}"
    
    @staticmethod
    def assert_valid_choice(value: Any, choices: List[Any]):
        """Vérifie qu'une valeur est dans les choix valides."""
        assert value in choices, f"Valeur '{value}' non valide. Choix: {choices}"
    
    @staticmethod
    def assert_string_length(value: str, min_length: int = None, max_length: int = None):
        """Vérifie la longueur d'une string."""
        assert isinstance(value, str), f"Valeur doit être une string: {type(value)}"
        
        actual_length = len(value)
        
        if min_length is not None:
            assert actual_length >= min_length, \
                f"String trop courte: {actual_length} < {min_length}"
        
        if max_length is not None:
            assert actual_length <= max_length, \
                f"String trop longue: {actual_length} > {max_length}"
    
    @staticmethod
    def assert_numeric_range(value: Union[int, float, Decimal], min_value: Any = None, max_value: Any = None):
        """Vérifie qu'une valeur numérique est dans une plage."""
        if min_value is not None:
            assert value >= min_value, f"Valeur trop petite: {value} < {min_value}"
        
        if max_value is not None:
            assert value <= max_value, f"Valeur trop grande: {value} > {max_value}"
    
    @staticmethod
    def assert_list_unique(items: List[Any]):
        """Vérifie que tous les éléments d'une liste sont uniques."""
        assert isinstance(items, list), f"Doit être une liste: {type(items)}"
        
        unique_items = set(items)
        assert len(unique_items) == len(items), \
            f"Liste contient des doublons: {len(items)} éléments, {len(unique_items)} uniques"
    
    @staticmethod
    def assert_dict_has_keys(data: Dict[str, Any], required_keys: List[str]):
        """Vérifie qu'un dictionnaire a toutes les clés requises."""
        assert isinstance(data, dict), f"Doit être un dict: {type(data)}"
        
        missing_keys = set(required_keys) - set(data.keys())
        assert not missing_keys, f"Clés manquantes: {missing_keys}"
    
    @staticmethod
    def assert_dict_structure(data: Dict[str, Any], expected_structure: Dict[str, Type]):
        """Vérifie la structure d'un dictionnaire."""
        DataAssertions.assert_dict_has_keys(data, list(expected_structure.keys()))
        
        for key, expected_type in expected_structure.items():
            actual_value = data[key]
            assert isinstance(actual_value, expected_type), \
                f"Type incorrect pour '{key}': {type(actual_value)} != {expected_type}"


# ============================================================================
# ASSERTIONS DE PERFORMANCE
# ============================================================================

class PerformanceAssertions:
    """Assertions pour la performance."""
    
    @staticmethod
    def assert_execution_time(result: TestResult, max_time: float, message: str = None):
        """Vérifie le temps d'exécution."""
        error_msg = message or f"Temps d'exécution trop long: {result.execution_time:.3f}s > {max_time}s"
        assert result.execution_time <= max_time, error_msg
    
    @staticmethod
    def assert_memory_usage(result: TestResult, max_memory: int, message: str = None):
        """Vérifie l'utilisation mémoire."""
        error_msg = message or f"Utilisation mémoire excessive: {result.memory_usage} bytes > {max_memory} bytes"
        assert result.memory_usage <= max_memory, error_msg
    
    @staticmethod
    def assert_performance_metrics(
        metrics: PerformanceMetrics,
        max_time: float = None,
        max_memory_delta: int = None,
        max_db_queries: int = None,
        min_cache_hit_ratio: float = None
    ):
        """Vérifie plusieurs métriques de performance."""
        if max_time is not None:
            assert metrics.execution_time <= max_time, \
                f"Temps d'exécution trop long: {metrics.execution_time:.3f}s > {max_time}s"
        
        if max_memory_delta is not None:
            assert metrics.memory_delta <= max_memory_delta, \
                f"Delta mémoire trop élevé: {metrics.memory_delta} bytes > {max_memory_delta} bytes"
        
        if max_db_queries is not None:
            assert metrics.db_queries_count <= max_db_queries, \
                f"Trop de requêtes DB: {metrics.db_queries_count} > {max_db_queries}"
        
        if min_cache_hit_ratio is not None:
            assert metrics.cache_hit_ratio >= min_cache_hit_ratio, \
                f"Ratio de cache trop faible: {metrics.cache_hit_ratio:.2f} < {min_cache_hit_ratio}"
    
    @staticmethod
    def assert_query_count(actual_count: int, expected_count: int, tolerance: int = 0):
        """Vérifie le nombre de requêtes de base de données."""
        min_count = expected_count - tolerance
        max_count = expected_count + tolerance
        
        assert min_count <= actual_count <= max_count, \
            f"Nombre de requêtes incorrect: {actual_count} (attendu: {expected_count} ±{tolerance})"
    
    @staticmethod
    def assert_no_n_plus_one(query_counts: List[int]):
        """Vérifie l'absence de problème N+1."""
        if len(query_counts) < 2:
            return  # Pas assez de données pour vérifier
        
        # Le nombre de requêtes ne devrait pas augmenter linéairement
        # avec le nombre d'éléments
        first_count = query_counts[0]
        
        for i, count in enumerate(query_counts[1:], 1):
            # Tolérance: le nombre de requêtes peut augmenter légèrement
            # mais pas proportionnellement au nombre d'éléments
            max_expected = first_count + (i * 2)  # Tolérance de 2 requêtes par élément
            
            assert count <= max_expected, \
                f"Problème N+1 détecté: {count} requêtes pour {i+1} éléments (max attendu: {max_expected})"


# ============================================================================
# ASSERTIONS DE MODÈLES DJANGO
# ============================================================================

class ModelAssertions:
    """Assertions pour les modèles Django."""
    
    @staticmethod
    def assert_model_exists(model_class: Type[models.Model], **lookup_kwargs):
        """Vérifie qu'un objet modèle existe."""
        try:
            obj = model_class.objects.get(**lookup_kwargs)
            return obj
        except model_class.DoesNotExist:
            pytest.fail(f"{model_class.__name__} avec {lookup_kwargs} n'existe pas")
        except model_class.MultipleObjectsReturned:
            pytest.fail(f"Plusieurs {model_class.__name__} trouvés avec {lookup_kwargs}")
    
    @staticmethod
    def assert_model_count(model_class: Type[models.Model], expected_count: int, **filter_kwargs):
        """Vérifie le nombre d'objets d'un modèle."""
        actual_count = model_class.objects.filter(**filter_kwargs).count()
        assert actual_count == expected_count, \
            f"Nombre d'objets incorrect pour {model_class.__name__}: {actual_count} != {expected_count}"
    
    @staticmethod
    def assert_field_value(obj: models.Model, field_name: str, expected_value: Any):
        """Vérifie la valeur d'un champ de modèle."""
        assert hasattr(obj, field_name), f"Champ '{field_name}' n'existe pas sur {obj.__class__.__name__}"
        
        actual_value = getattr(obj, field_name)
        assert actual_value == expected_value, \
            f"Valeur incorrecte pour {obj.__class__.__name__}.{field_name}: {actual_value} != {expected_value}"
    
    @staticmethod
    def assert_field_not_none(obj: models.Model, field_name: str):
        """Vérifie qu'un champ n'est pas None."""
        assert hasattr(obj, field_name), f"Champ '{field_name}' n'existe pas sur {obj.__class__.__name__}"
        
        actual_value = getattr(obj, field_name)
        assert actual_value is not None, \
            f"Champ {obj.__class__.__name__}.{field_name} ne devrait pas être None"
    
    @staticmethod
    def assert_relationship_exists(obj: models.Model, relation_name: str):
        """Vérifie qu'une relation existe."""
        assert hasattr(obj, relation_name), \
            f"Relation '{relation_name}' n'existe pas sur {obj.__class__.__name__}"
        
        related_manager = getattr(obj, relation_name)
        
        # Vérifier selon le type de relation
        if hasattr(related_manager, 'all'):
            # Relation many-to-many ou reverse foreign key
            assert related_manager.exists(), \
                f"Aucun objet lié trouvé pour {obj.__class__.__name__}.{relation_name}"
        else:
            # Relation foreign key
            assert related_manager is not None, \
                f"Objet lié None pour {obj.__class__.__name__}.{relation_name}"
    
    @staticmethod
    def assert_model_validation(obj: models.Model, should_be_valid: bool = True):
        """Vérifie la validation d'un modèle."""
        try:
            obj.full_clean()
            if not should_be_valid:
                pytest.fail(f"{obj.__class__.__name__} devrait être invalide mais la validation a réussi")
        except ValidationError as e:
            if should_be_valid:
                pytest.fail(f"{obj.__class__.__name__} devrait être valide mais la validation a échoué: {e}")
    
    @staticmethod
    def assert_model_save_success(obj: models.Model):
        """Vérifie qu'un modèle peut être sauvegardé."""
        try:
            obj.save()
            assert obj.pk is not None, f"{obj.__class__.__name__} n'a pas reçu de clé primaire après sauvegarde"
        except Exception as e:
            pytest.fail(f"Échec de sauvegarde de {obj.__class__.__name__}: {e}")
    
    @staticmethod
    def assert_model_delete_success(obj: models.Model):
        """Vérifie qu'un modèle peut être supprimé."""
        model_class = obj.__class__
        obj_id = obj.pk
        
        try:
            obj.delete()
            
            # Vérifier que l'objet n'existe plus
            with pytest.raises(model_class.DoesNotExist):
                model_class.objects.get(pk=obj_id)
        
        except Exception as e:
            pytest.fail(f"Échec de suppression de {model_class.__name__}: {e}")


# ============================================================================
# ASSERTIONS DE COMPARAISON
# ============================================================================

class ComparisonAssertions:
    """Assertions pour la comparaison de données."""
    
    @staticmethod
    def assert_deep_equal(actual: Any, expected: Any, ignore_keys: List[str] = None):
        """Compare deux structures de données en profondeur."""
        if ignore_keys is None:
            ignore_keys = []
        
        def clean_data(data):
            if isinstance(data, dict):
                return {k: clean_data(v) for k, v in data.items() if k not in ignore_keys}
            elif isinstance(data, list):
                return [clean_data(item) for item in data]
            else:
                return data
        
        cleaned_actual = clean_data(actual)
        cleaned_expected = clean_data(expected)
        
        assert cleaned_actual == cleaned_expected, \
            f"Structures différentes:\nActuel: {cleaned_actual}\nAttendu: {cleaned_expected}"
    
    @staticmethod
    def assert_approximately_equal(actual: float, expected: float, tolerance: float = 0.001):
        """Compare deux nombres flottants avec une tolérance."""
        difference = abs(actual - expected)
        assert difference <= tolerance, \
            f"Nombres pas assez proches: |{actual} - {expected}| = {difference} > {tolerance}"
    
    @staticmethod
    def assert_date_approximately_equal(
        actual: datetime,
        expected: datetime,
        tolerance: timedelta = timedelta(seconds=1)
    ):
        """Compare deux dates avec une tolérance."""
        difference = abs(actual - expected)
        assert difference <= tolerance, \
            f"Dates pas assez proches: |{actual} - {expected}| = {difference} > {tolerance}"
    
    @staticmethod
    def assert_list_contains_subset(actual_list: List[Any], expected_subset: List[Any]):
        """Vérifie qu'une liste contient tous les éléments d'un sous-ensemble."""
        missing_items = set(expected_subset) - set(actual_list)
        assert not missing_items, \
            f"Éléments manquants dans la liste: {missing_items}"
    
    @staticmethod
    def assert_dict_contains_subset(actual_dict: Dict[str, Any], expected_subset: Dict[str, Any]):
        """Vérifie qu'un dictionnaire contient tous les éléments d'un sous-ensemble."""
        for key, expected_value in expected_subset.items():
            assert key in actual_dict, f"Clé manquante: {key}"
            assert actual_dict[key] == expected_value, \
                f"Valeur incorrecte pour '{key}': {actual_dict[key]} != {expected_value}"
    
    @staticmethod
    def assert_json_equal(actual_json: str, expected_json: str):
        """Compare deux chaînes JSON."""
        try:
            actual_data = json.loads(actual_json)
            expected_data = json.loads(expected_json)
            
            assert actual_data == expected_data, \
                f"JSON différent:\nActuel: {actual_data}\nAttendu: {expected_data}"
        
        except json.JSONDecodeError as e:
            pytest.fail(f"JSON invalide: {e}")


# ============================================================================
# ASSERTIONS PERSONNALISÉES
# ============================================================================

def assert_graphql_schema_valid(schema: graphene.Schema):
    """Vérifie qu'un schéma GraphQL est valide."""
    try:
        # Tenter d'exécuter une requête d'introspection
        introspection_query = """
        query IntrospectionQuery {
            __schema {
                types {
                    name
                    kind
                }
            }
        }
        """
        
        client = Client(schema)
        result = client.execute(introspection_query)
        
        assert not result.errors, f"Erreurs dans le schéma: {result.errors}"
        assert result.data is not None, "Données d'introspection manquantes"
        assert '__schema' in result.data, "Schéma d'introspection manquant"
    
    except Exception as e:
        pytest.fail(f"Schéma GraphQL invalide: {e}")


def assert_business_method_result(obj: models.Model, method_name: str, expected_result: Any):
    """Vérifie le résultat d'une méthode business."""
    assert hasattr(obj, method_name), f"Méthode '{method_name}' n'existe pas sur {obj.__class__.__name__}"
    
    method = getattr(obj, method_name)
    assert callable(method), f"'{method_name}' n'est pas une méthode"
    
    try:
        actual_result = method()
        assert actual_result == expected_result, \
            f"Résultat incorrect pour {obj.__class__.__name__}.{method_name}(): {actual_result} != {expected_result}"
    
    except Exception as e:
        pytest.fail(f"Erreur lors de l'exécution de {obj.__class__.__name__}.{method_name}(): {e}")


def assert_pagination_valid(page_info: Dict[str, Any], edges: List[Dict[str, Any]]):
    """Vérifie la validité des informations de pagination."""
    # Vérifier la structure de pageInfo
    required_fields = ['hasNextPage', 'hasPreviousPage', 'startCursor', 'endCursor']
    for field in required_fields:
        assert field in page_info, f"Champ manquant dans pageInfo: {field}"
    
    # Vérifier les types
    assert isinstance(page_info['hasNextPage'], bool), "hasNextPage doit être un booléen"
    assert isinstance(page_info['hasPreviousPage'], bool), "hasPreviousPage doit être un booléen"
    
    # Vérifier la cohérence des curseurs
    if edges:
        assert page_info['startCursor'] is not None, "startCursor ne peut pas être None avec des edges"
        assert page_info['endCursor'] is not None, "endCursor ne peut pas être None avec des edges"
        
        # Vérifier que chaque edge a un cursor
        for i, edge in enumerate(edges):
            assert 'cursor' in edge, f"Cursor manquant dans l'edge {i}"
            assert 'node' in edge, f"Node manquant dans l'edge {i}"
    else:
        # Pas d'edges, les curseurs peuvent être None
        pass


# ============================================================================
# FONCTIONS UTILITAIRES D'ASSERTION
# ============================================================================

def create_assertion_context(test_name: str = None):
    """Crée un contexte d'assertion avec des informations de debug."""
    context = {
        'test_name': test_name,
        'assertions_count': 0,
        'failed_assertions': [],
        'start_time': datetime.now()
    }
    
    return context


def log_assertion_failure(context: Dict[str, Any], assertion_error: AssertionError):
    """Log une assertion échouée dans le contexte."""
    if context:
        context['failed_assertions'].append({
            'error': str(assertion_error),
            'timestamp': datetime.now()
        })


def get_assertion_summary(context: Dict[str, Any]) -> Dict[str, Any]:
    """Retourne un résumé des assertions."""
    if not context:
        return {}
    
    end_time = datetime.now()
    duration = end_time - context['start_time']
    
    return {
        'test_name': context.get('test_name'),
        'total_assertions': context.get('assertions_count', 0),
        'failed_assertions': len(context.get('failed_assertions', [])),
        'success_rate': (context.get('assertions_count', 0) - len(context.get('failed_assertions', []))) / max(1, context.get('assertions_count', 1)),
        'duration': duration.total_seconds(),
        'failures': context.get('failed_assertions', [])
    }
