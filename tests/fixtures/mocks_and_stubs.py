"""
Mocks et stubs pour les tests GraphQL.

Ce module fournit:
- Des mocks pour les composants GraphQL
- Des stubs pour les opérations de base de données
- Des mocks pour les dépendances externes
- Des simulateurs de conditions d'erreur
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from typing import Dict, List, Any, Optional, Callable, Type, Union
from datetime import datetime, date
from decimal import Decimal
import json
import time
import random

from django.db import models
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import IntegrityError, DatabaseError, OperationalError

import graphene
from graphene.test import Client
from graphql import GraphQLError

from django_graphql_auto.core.schema import SchemaBuilder
from django_graphql_auto.generators.introspector import ModelIntrospector, FieldInfo, RelationshipInfo
from django_graphql_auto.generators.types import TypeGenerator
from django_graphql_auto.generators.queries import QueryGenerator
from django_graphql_auto.generators.mutations import MutationGenerator
from django_graphql_auto.decorators import business_logic


# ============================================================================
# MOCKS POUR LES COMPOSANTS GRAPHQL
# ============================================================================

class MockModelIntrospector:
    """Mock pour ModelIntrospector."""
    
    def __init__(self):
        self.model_class = None
        self.fields_info = {}
        self.relationships_info = {}
        self.methods_info = {}
        self.properties_info = {}
        self.meta_info = {}
        self.cache = {}
    
    def introspect_model(self, model_class: Type[models.Model]) -> Dict[str, Any]:
        """Mock de l'introspection de modèle."""
        self.model_class = model_class
        
        return {
            'model_name': model_class.__name__,
            'app_label': getattr(model_class._meta, 'app_label', 'tests'),
            'fields': self._mock_fields(),
            'relationships': self._mock_relationships(),
            'methods': self._mock_methods(),
            'properties': self._mock_properties(),
            'meta': self._mock_meta()
        }
    
    def _mock_fields(self) -> Dict[str, FieldInfo]:
        """Mock des informations de champs."""
        return {
            'id': FieldInfo(
                name='id',
                field_type='AutoField',
                graphql_type='ID',
                is_required=True,
                is_list=False,
                description='Identifiant unique'
            ),
            'name': FieldInfo(
                name='name',
                field_type='CharField',
                graphql_type='String',
                is_required=True,
                is_list=False,
                description='Nom'
            ),
            'created_at': FieldInfo(
                name='created_at',
                field_type='DateTimeField',
                graphql_type='DateTime',
                is_required=True,
                is_list=False,
                description='Date de création'
            )
        }
    
    def _mock_relationships(self) -> Dict[str, RelationshipInfo]:
        """Mock des informations de relations."""
        return {
            'author': RelationshipInfo(
                name='author',
                related_model='TestAuthor',
                relationship_type='ForeignKey',
                is_reverse=False,
                is_many=False,
                description='Auteur'
            )
        }
    
    def _mock_methods(self) -> Dict[str, Dict[str, Any]]:
        """Mock des méthodes business."""
        return {
            'get_full_name': {
                'name': 'get_full_name',
                'return_type': str,
                'parameters': [],
                'description': 'Retourne le nom complet'
            }
        }
    
    def _mock_properties(self) -> Dict[str, Dict[str, Any]]:
        """Mock des propriétés."""
        return {
            'display_name': {
                'name': 'display_name',
                'return_type': str,
                'description': 'Nom d\'affichage'
            }
        }
    
    def _mock_meta(self) -> Dict[str, Any]:
        """Mock des métadonnées."""
        return {
            'verbose_name': 'Objet de test',
            'verbose_name_plural': 'Objets de test',
            'ordering': ['name'],
            'permissions': []
        }


class MockTypeGenerator:
    """Mock pour TypeGenerator."""
    
    def __init__(self):
        self.generated_types = {}
        self.field_mappings = {}
    
    def generate_type(self, model_class: Type[models.Model]) -> Dict[str, Any]:
        """Mock de la génération de type."""
        type_name = f"{model_class.__name__}Type"
        
        mock_type = type(type_name, (graphene.ObjectType,), {
            'id': graphene.ID(required=True, description="Identifiant unique"),
            'name': graphene.String(required=True, description="Nom"),
            'created_at': graphene.DateTime(required=True, description="Date de création")
        })
        
        type_info = {
            'name': type_name,
            'graphql_type': mock_type,
            'model_class': model_class,
            'fields': {
                'id': {'type': 'ID', 'required': True},
                'name': {'type': 'String', 'required': True},
                'created_at': {'type': 'DateTime', 'required': True}
            },
            'relationships': {},
            'methods': {}
        }
        
        self.generated_types[model_class] = type_info
        return type_info
    
    def get_field_mapping(self, django_field: models.Field) -> Dict[str, Any]:
        """Mock du mapping de champ."""
        field_mappings = {
            models.CharField: {'type': 'String', 'required': True},
            models.TextField: {'type': 'String', 'required': False},
            models.IntegerField: {'type': 'Int', 'required': True},
            models.BooleanField: {'type': 'Boolean', 'required': True},
            models.DateTimeField: {'type': 'DateTime', 'required': True},
            models.DateField: {'type': 'Date', 'required': True},
            models.DecimalField: {'type': 'Decimal', 'required': True},
            models.EmailField: {'type': 'String', 'required': True},
            models.URLField: {'type': 'String', 'required': True},
        }
        
        return field_mappings.get(type(django_field), {'type': 'String', 'required': False})


class MockQueryGenerator:
    """Mock pour QueryGenerator."""
    
    def __init__(self):
        self.generated_queries = {}
        self.resolvers = {}
    
    def generate_queries(self, model_class: Type[models.Model]) -> Dict[str, Any]:
        """Mock de la génération de requêtes."""
        model_name = model_class.__name__.lower()
        
        queries = {
            f"{model_name}": graphene.Field(
                graphene.String,  # Type simplifié pour le mock
                id=graphene.ID(required=True),
                description=f"Récupère un {model_class.__name__} par ID"
            ),
            f"{model_name}_list": graphene.List(
                graphene.String,  # Type simplifié pour le mock
                limit=graphene.Int(),
                offset=graphene.Int(),
                description=f"Liste des {model_class.__name__}s"
            )
        }
        
        self.generated_queries[model_class] = queries
        return queries
    
    def generate_resolver(self, model_class: Type[models.Model], query_type: str) -> Callable:
        """Mock de la génération de resolver."""
        def mock_resolver(root, info, **kwargs):
            if query_type == 'single':
                return f"Mock {model_class.__name__} object"
            else:
                return [f"Mock {model_class.__name__} object {i}" for i in range(3)]
        
        return mock_resolver


class MockMutationGenerator:
    """Mock pour MutationGenerator."""
    
    def __init__(self):
        self.generated_mutations = {}
        self.input_types = {}
    
    def generate_mutations(self, model_class: Type[models.Model]) -> Dict[str, Any]:
        """Mock de la génération de mutations."""
        model_name = model_class.__name__.lower()
        
        mutations = {
            f"create_{model_name}": graphene.Field(
                graphene.String,  # Type simplifié pour le mock
                input=graphene.Argument(graphene.String),
                description=f"Crée un {model_class.__name__}"
            ),
            f"update_{model_name}": graphene.Field(
                graphene.String,  # Type simplifié pour le mock
                id=graphene.ID(required=True),
                input=graphene.Argument(graphene.String),
                description=f"Met à jour un {model_class.__name__}"
            ),
            f"delete_{model_name}": graphene.Field(
                graphene.Boolean,
                id=graphene.ID(required=True),
                description=f"Supprime un {model_class.__name__}"
            )
        }
        
        self.generated_mutations[model_class] = mutations
        return mutations
    
    def generate_input_type(self, model_class: Type[models.Model]) -> Type[graphene.InputObjectType]:
        """Mock de la génération de type d'entrée."""
        input_type_name = f"{model_class.__name__}Input"
        
        input_type = type(input_type_name, (graphene.InputObjectType,), {
            'name': graphene.String(required=True, description="Nom"),
            'description': graphene.String(description="Description")
        })
        
        self.input_types[model_class] = input_type
        return input_type


# ============================================================================
# MOCKS POUR LES OPÉRATIONS DE BASE DE DONNÉES
# ============================================================================

class MockQuerySet:
    """Mock pour QuerySet Django."""
    
    def __init__(self, model_class: Type[models.Model], objects: List[Any] = None):
        self.model = model_class
        self._objects = objects or []
        self._filters = {}
        self._ordering = []
        self._limit = None
        self._offset = None
    
    def all(self):
        """Retourne tous les objets."""
        return MockQuerySet(self.model, self._objects[:])
    
    def filter(self, **kwargs):
        """Filtre les objets."""
        new_qs = MockQuerySet(self.model, self._objects[:])
        new_qs._filters.update(kwargs)
        
        # Simulation simple du filtrage
        filtered_objects = []
        for obj in self._objects:
            match = True
            for key, value in kwargs.items():
                if hasattr(obj, key) and getattr(obj, key) != value:
                    match = False
                    break
            if match:
                filtered_objects.append(obj)
        
        new_qs._objects = filtered_objects
        return new_qs
    
    def exclude(self, **kwargs):
        """Exclut les objets."""
        new_qs = MockQuerySet(self.model, self._objects[:])
        
        # Simulation simple de l'exclusion
        filtered_objects = []
        for obj in self._objects:
            match = False
            for key, value in kwargs.items():
                if hasattr(obj, key) and getattr(obj, key) == value:
                    match = True
                    break
            if not match:
                filtered_objects.append(obj)
        
        new_qs._objects = filtered_objects
        return new_qs
    
    def order_by(self, *fields):
        """Ordonne les objets."""
        new_qs = MockQuerySet(self.model, self._objects[:])
        new_qs._ordering = list(fields)
        
        # Simulation simple de l'ordonnancement
        if fields:
            field = fields[0].lstrip('-')
            reverse = fields[0].startswith('-')
            
            try:
                new_qs._objects.sort(
                    key=lambda obj: getattr(obj, field, ''),
                    reverse=reverse
                )
            except (AttributeError, TypeError):
                pass  # Ignorer les erreurs de tri
        
        return new_qs
    
    def distinct(self):
        """Retourne les objets distincts."""
        new_qs = MockQuerySet(self.model, list(set(self._objects)))
        return new_qs
    
    def count(self):
        """Retourne le nombre d'objets."""
        return len(self._objects)
    
    def exists(self):
        """Vérifie si des objets existent."""
        return len(self._objects) > 0
    
    def first(self):
        """Retourne le premier objet."""
        return self._objects[0] if self._objects else None
    
    def last(self):
        """Retourne le dernier objet."""
        return self._objects[-1] if self._objects else None
    
    def get(self, **kwargs):
        """Récupère un objet unique."""
        filtered = self.filter(**kwargs)
        
        if not filtered._objects:
            raise ObjectDoesNotExist(f"{self.model.__name__} matching query does not exist.")
        
        if len(filtered._objects) > 1:
            raise self.model.MultipleObjectsReturned(
                f"get() returned more than one {self.model.__name__}"
            )
        
        return filtered._objects[0]
    
    def create(self, **kwargs):
        """Crée un nouvel objet."""
        obj = Mock()
        obj._meta = Mock()
        obj._meta.model = self.model
        
        for key, value in kwargs.items():
            setattr(obj, key, value)
        
        # Ajouter un ID si pas présent
        if not hasattr(obj, 'id') or obj.id is None:
            obj.id = len(self._objects) + 1
        
        self._objects.append(obj)
        return obj
    
    def get_or_create(self, defaults=None, **kwargs):
        """Récupère ou crée un objet."""
        try:
            obj = self.get(**kwargs)
            return obj, False
        except ObjectDoesNotExist:
            create_kwargs = kwargs.copy()
            if defaults:
                create_kwargs.update(defaults)
            obj = self.create(**create_kwargs)
            return obj, True
    
    def update(self, **kwargs):
        """Met à jour les objets."""
        count = 0
        for obj in self._objects:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            count += 1
        return count
    
    def delete(self):
        """Supprime les objets."""
        count = len(self._objects)
        self._objects.clear()
        return count, {self.model._meta.label: count}
    
    def __iter__(self):
        """Itère sur les objets."""
        start = self._offset or 0
        end = start + self._limit if self._limit else None
        return iter(self._objects[start:end])
    
    def __len__(self):
        """Retourne la longueur."""
        return len(self._objects)
    
    def __getitem__(self, key):
        """Accès par index ou slice."""
        if isinstance(key, slice):
            new_qs = MockQuerySet(self.model, self._objects[key])
            return new_qs
        else:
            return self._objects[key]


class MockManager:
    """Mock pour Manager Django."""
    
    def __init__(self, model_class: Type[models.Model]):
        self.model = model_class
        self._objects = []
    
    def get_queryset(self):
        """Retourne le QuerySet."""
        return MockQuerySet(self.model, self._objects)
    
    def all(self):
        """Retourne tous les objets."""
        return self.get_queryset().all()
    
    def filter(self, **kwargs):
        """Filtre les objets."""
        return self.get_queryset().filter(**kwargs)
    
    def exclude(self, **kwargs):
        """Exclut les objets."""
        return self.get_queryset().exclude(**kwargs)
    
    def get(self, **kwargs):
        """Récupère un objet."""
        return self.get_queryset().get(**kwargs)
    
    def create(self, **kwargs):
        """Crée un objet."""
        return self.get_queryset().create(**kwargs)
    
    def get_or_create(self, defaults=None, **kwargs):
        """Récupère ou crée un objet."""
        return self.get_queryset().get_or_create(defaults=defaults, **kwargs)
    
    def count(self):
        """Compte les objets."""
        return self.get_queryset().count()
    
    def exists(self):
        """Vérifie l'existence."""
        return self.get_queryset().exists()
    
    def add_object(self, obj):
        """Ajoute un objet au manager (pour les tests)."""
        self._objects.append(obj)
    
    def clear_objects(self):
        """Vide le manager (pour les tests)."""
        self._objects.clear()


# ============================================================================
# MOCKS POUR LES MODÈLES
# ============================================================================

def create_mock_model(
    model_name: str,
    fields: Dict[str, Any] = None,
    methods: Dict[str, Callable] = None,
    properties: Dict[str, Any] = None
) -> Type[Mock]:
    """Crée un mock de modèle Django."""
    
    # Champs par défaut
    default_fields = {
        'id': 1,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'is_active': True
    }
    
    if fields:
        default_fields.update(fields)
    
    # Créer la classe mock
    mock_model = type(f"Mock{model_name}", (Mock,), {})
    
    # Ajouter les métadonnées
    mock_model._meta = Mock()
    mock_model._meta.model = mock_model
    mock_model._meta.app_label = 'tests'
    mock_model._meta.model_name = model_name.lower()
    mock_model._meta.verbose_name = model_name
    mock_model._meta.verbose_name_plural = f"{model_name}s"
    mock_model._meta.get_fields = Mock(return_value=[])
    
    # Ajouter le manager
    mock_model.objects = MockManager(mock_model)
    
    # Créer une instance mock
    instance = mock_model()
    
    # Ajouter les champs
    for field_name, field_value in default_fields.items():
        setattr(instance, field_name, field_value)
    
    # Ajouter les méthodes
    if methods:
        for method_name, method_func in methods.items():
            setattr(instance, method_name, method_func)
    
    # Ajouter les propriétés
    if properties:
        for prop_name, prop_value in properties.items():
            setattr(type(instance), prop_name, PropertyMock(return_value=prop_value))
    
    # Méthodes standard
    instance.save = Mock()
    instance.delete = Mock(return_value=(1, {f'tests.{model_name}': 1}))
    instance.refresh_from_db = Mock()
    instance.clean = Mock()
    instance.full_clean = Mock()
    
    # Méthodes de sérialisation
    instance.__str__ = Mock(return_value=f"Mock {model_name}")
    instance.__repr__ = Mock(return_value=f"<Mock{model_name}: {instance.id}>")
    
    return instance


def create_mock_user(
    username: str = "testuser",
    email: str = "test@example.com",
    is_staff: bool = False,
    is_superuser: bool = False,
    **kwargs
) -> Mock:
    """Crée un mock d'utilisateur Django."""
    user = Mock(spec=User)
    user.id = kwargs.get('id', 1)
    user.username = username
    user.email = email
    user.first_name = kwargs.get('first_name', 'Test')
    user.last_name = kwargs.get('last_name', 'User')
    user.is_staff = is_staff
    user.is_superuser = is_superuser
    user.is_active = kwargs.get('is_active', True)
    user.date_joined = kwargs.get('date_joined', datetime.now())
    user.last_login = kwargs.get('last_login', datetime.now())
    
    # Méthodes
    user.get_full_name = Mock(return_value=f"{user.first_name} {user.last_name}")
    user.get_short_name = Mock(return_value=user.first_name)
    user.has_perm = Mock(return_value=is_superuser)
    user.has_perms = Mock(return_value=is_superuser)
    user.has_module_perms = Mock(return_value=is_superuser)
    user.check_password = Mock(return_value=True)
    user.set_password = Mock()
    user.save = Mock()
    
    return user


# ============================================================================
# SIMULATEURS D'ERREURS
# ============================================================================

class DatabaseErrorSimulator:
    """Simulateur d'erreurs de base de données."""
    
    @staticmethod
    def simulate_connection_error():
        """Simule une erreur de connexion."""
        raise OperationalError("Database connection failed")
    
    @staticmethod
    def simulate_integrity_error():
        """Simule une erreur d'intégrité."""
        raise IntegrityError("UNIQUE constraint failed")
    
    @staticmethod
    def simulate_validation_error():
        """Simule une erreur de validation."""
        raise ValidationError("Invalid data provided")
    
    @staticmethod
    def simulate_timeout_error():
        """Simule un timeout."""
        raise DatabaseError("Query timeout")
    
    @staticmethod
    def simulate_permission_error():
        """Simule une erreur de permission."""
        raise DatabaseError("Permission denied")


class GraphQLErrorSimulator:
    """Simulateur d'erreurs GraphQL."""
    
    @staticmethod
    def simulate_syntax_error():
        """Simule une erreur de syntaxe."""
        raise GraphQLError("Syntax Error: Expected Name, found }")
    
    @staticmethod
    def simulate_validation_error():
        """Simule une erreur de validation."""
        raise GraphQLError("Cannot query field 'nonexistent' on type 'Query'")
    
    @staticmethod
    def simulate_execution_error():
        """Simule une erreur d'exécution."""
        raise GraphQLError("Field 'test' of type 'String!' must not be null")
    
    @staticmethod
    def simulate_permission_error():
        """Simule une erreur de permission."""
        raise GraphQLError("You do not have permission to perform this action")


# ============================================================================
# MOCKS POUR LES DÉPENDANCES EXTERNES
# ============================================================================

class MockCache:
    """Mock pour le cache Django."""
    
    def __init__(self):
        self._cache = {}
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, key, default=None):
        """Récupère une valeur du cache."""
        if key in self._cache:
            self.hit_count += 1
            return self._cache[key]
        else:
            self.miss_count += 1
            return default
    
    def set(self, key, value, timeout=None):
        """Définit une valeur dans le cache."""
        self._cache[key] = value
    
    def delete(self, key):
        """Supprime une clé du cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self):
        """Vide le cache."""
        self._cache.clear()
        self.hit_count = 0
        self.miss_count = 0
    
    def get_many(self, keys):
        """Récupère plusieurs valeurs."""
        result = {}
        for key in keys:
            if key in self._cache:
                result[key] = self._cache[key]
                self.hit_count += 1
            else:
                self.miss_count += 1
        return result
    
    def set_many(self, data, timeout=None):
        """Définit plusieurs valeurs."""
        self._cache.update(data)


class MockLogger:
    """Mock pour le logger."""
    
    def __init__(self):
        self.logs = []
    
    def debug(self, message, *args, **kwargs):
        """Log debug."""
        self.logs.append(('DEBUG', message % args if args else message))
    
    def info(self, message, *args, **kwargs):
        """Log info."""
        self.logs.append(('INFO', message % args if args else message))
    
    def warning(self, message, *args, **kwargs):
        """Log warning."""
        self.logs.append(('WARNING', message % args if args else message))
    
    def error(self, message, *args, **kwargs):
        """Log error."""
        self.logs.append(('ERROR', message % args if args else message))
    
    def critical(self, message, *args, **kwargs):
        """Log critical."""
        self.logs.append(('CRITICAL', message % args if args else message))
    
    def exception(self, message, *args, **kwargs):
        """Log exception."""
        self.logs.append(('EXCEPTION', message % args if args else message))
    
    def get_logs(self, level=None):
        """Récupère les logs."""
        if level:
            return [log for log in self.logs if log[0] == level]
        return self.logs
    
    def clear(self):
        """Vide les logs."""
        self.logs.clear()


# ============================================================================
# FIXTURES PYTEST POUR LES MOCKS
# ============================================================================

@pytest.fixture
def mock_model_introspector():
    """Fixture pour MockModelIntrospector."""
    return MockModelIntrospector()


@pytest.fixture
def mock_type_generator():
    """Fixture pour MockTypeGenerator."""
    return MockTypeGenerator()


@pytest.fixture
def mock_query_generator():
    """Fixture pour MockQueryGenerator."""
    return MockQueryGenerator()


@pytest.fixture
def mock_mutation_generator():
    """Fixture pour MockMutationGenerator."""
    return MockMutationGenerator()


@pytest.fixture
def mock_cache():
    """Fixture pour MockCache."""
    return MockCache()


@pytest.fixture
def mock_logger():
    """Fixture pour MockLogger."""
    return MockLogger()


@pytest.fixture
def mock_user():
    """Fixture pour un utilisateur mock."""
    return create_mock_user()


@pytest.fixture
def mock_admin_user():
    """Fixture pour un administrateur mock."""
    return create_mock_user(
        username="admin",
        email="admin@example.com",
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def mock_database_error():
    """Fixture pour simuler des erreurs de base de données."""
    return DatabaseErrorSimulator()


@pytest.fixture
def mock_graphql_error():
    """Fixture pour simuler des erreurs GraphQL."""
    return GraphQLErrorSimulator()


# ============================================================================
# DÉCORATEURS POUR LES MOCKS
# ============================================================================

def mock_database_operations(func):
    """Décorateur pour mocker les opérations de base de données."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with patch('django.db.models.QuerySet', MockQuerySet), \
             patch('django.db.models.Manager', MockManager):
            return func(*args, **kwargs)
    
    return wrapper


def mock_cache_operations(func):
    """Décorateur pour mocker les opérations de cache."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        mock_cache = MockCache()
        with patch('django.core.cache.cache', mock_cache):
            return func(*args, **kwargs)
    
    return wrapper

import functools
def mock_logging(func):
    """Décorateur pour mocker le logging."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        mock_logger = MockLogger()
        with patch('logging.getLogger', return_value=mock_logger):
            return func(*args, **kwargs)
    
    return wrapper


# ============================================================================
# UTILITAIRES POUR LES MOCKS
# ============================================================================

def create_mock_request_factory():
    """Crée une factory de requêtes mock."""
    factory = RequestFactory()
    
    def create_request(method='GET', path='/', user=None, **kwargs):
        request = getattr(factory, method.lower())(path, **kwargs)
        request.user = user or create_mock_user()
        return request
    
    return create_request


def setup_mock_environment():
    """Configure un environnement de test avec des mocks."""
    mocks = {
        'cache': MockCache(),
        'logger': MockLogger(),
        'user': create_mock_user(),
        'admin_user': create_mock_user(is_staff=True, is_superuser=True)
    }
    
    return mocks


def teardown_mock_environment(mocks):
    """Nettoie l'environnement de mocks."""
    for mock in mocks.values():
        if hasattr(mock, 'clear'):
            mock.clear()
        elif hasattr(mock, 'reset_mock'):
            mock.reset_mock()


def assert_mock_called_with_pattern(mock_obj, pattern):
    """Vérifie qu'un mock a été appelé avec un pattern."""
    calls = mock_obj.call_args_list
    
    for call in calls:
        args, kwargs = call
        call_str = str(args) + str(kwargs)
        if pattern in call_str:
            return True
    
    raise AssertionError(f"Mock not called with pattern '{pattern}'. Calls: {calls}")


def get_mock_call_count(mock_obj):
    """Retourne le nombre d'appels d'un mock."""
    return mock_obj.call_count if hasattr(mock_obj, 'call_count') else 0