# Stratégies de Mocking - Django GraphQL Auto

Ce guide détaille les stratégies et techniques de mocking pour les tests Django GraphQL, couvrant les mocks de services externes, de base de données, et de composants internes.

## 📋 Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Types de Mocks](#types-de-mocks)
- [Mocking des Services Externes](#mocking-des-services-externes)
- [Mocking de Base de Données](#mocking-de-base-de-données)
- [Mocking GraphQL](#mocking-graphql)
- [Patterns de Mocking](#patterns-de-mocking)
- [Outils et Bibliothèques](#outils-et-bibliothèques)
- [Bonnes Pratiques](#bonnes-pratiques)
- [Exemples Avancés](#exemples-avancés)

## 🎯 Vue d'Ensemble

### Philosophie du Mocking

```python
# tests/mocking/base.py
"""Base pour les stratégies de mocking."""

from typing import Any, Dict, List, Optional, Callable, Union
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from dataclasses import dataclass
from contextlib import contextmanager
import functools
import time
import random


@dataclass
class MockConfig:
    """Configuration pour les mocks."""
    
    # Comportement général
    strict_mode: bool = True
    auto_spec: bool = True
    return_value: Any = None
    side_effect: Optional[Union[Exception, Callable]] = None
    
    # Simulation de latence
    simulate_latency: bool = False
    min_latency_ms: int = 10
    max_latency_ms: int = 100
    
    # Simulation d'erreurs
    error_rate: float = 0.0  # 0.0 à 1.0
    error_types: List[Exception] = None
    
    # Logging et debugging
    log_calls: bool = False
    call_history: bool = True


class BaseMockManager:
    """Gestionnaire de base pour les mocks."""
    
    def __init__(self, config: MockConfig = None):
        self.config = config or MockConfig()
        self.active_mocks = {}
        self.call_history = []
        self.mock_registry = {}
    
    def create_mock(self, name: str, spec: Any = None, **kwargs) -> Mock:
        """Crée un mock avec la configuration par défaut."""
        
        mock_kwargs = {
            'spec': spec if spec else self.config.auto_spec,
            'return_value': self.config.return_value,
            'side_effect': self._create_side_effect()
        }
        mock_kwargs.update(kwargs)
        
        mock = Mock(**mock_kwargs)
        
        # Ajouter le logging si activé
        if self.config.log_calls:
            mock.side_effect = self._wrap_with_logging(mock.side_effect, name)
        
        self.active_mocks[name] = mock
        return mock
    
    def _create_side_effect(self) -> Optional[Callable]:
        """Crée un side_effect avec simulation de latence et d'erreurs."""
        
        if not (self.config.simulate_latency or self.config.error_rate > 0):
            return self.config.side_effect
        
        def side_effect(*args, **kwargs):
            # Simuler la latence
            if self.config.simulate_latency:
                latency = random.randint(
                    self.config.min_latency_ms,
                    self.config.max_latency_ms
                ) / 1000.0
                time.sleep(latency)
            
            # Simuler les erreurs
            if self.config.error_rate > 0 and random.random() < self.config.error_rate:
                error_types = self.config.error_types or [Exception]
                error_class = random.choice(error_types)
                raise error_class("Simulated error")
            
            # Appeler le side_effect original si défini
            if callable(self.config.side_effect):
                return self.config.side_effect(*args, **kwargs)
            elif self.config.side_effect is not None:
                raise self.config.side_effect
            
            return self.config.return_value
        
        return side_effect
    
    def _wrap_with_logging(self, original_side_effect: Callable, name: str) -> Callable:
        """Enveloppe un side_effect avec du logging."""
        
        def logged_side_effect(*args, **kwargs):
            call_info = {
                'mock_name': name,
                'timestamp': time.time(),
                'args': args,
                'kwargs': kwargs
            }
            
            try:
                if original_side_effect:
                    result = original_side_effect(*args, **kwargs)
                else:
                    result = None
                
                call_info['result'] = result
                call_info['success'] = True
                
                return result
                
            except Exception as e:
                call_info['error'] = str(e)
                call_info['success'] = False
                raise
            
            finally:
                if self.config.call_history:
                    self.call_history.append(call_info)
    
    def reset_all_mocks(self):
        """Remet à zéro tous les mocks actifs."""
        
        for mock in self.active_mocks.values():
            mock.reset_mock()
        
        self.call_history.clear()
    
    def get_call_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques d'appels."""
        
        stats = {
            'total_calls': len(self.call_history),
            'successful_calls': sum(1 for call in self.call_history if call['success']),
            'failed_calls': sum(1 for call in self.call_history if not call['success']),
            'mocks_used': len(set(call['mock_name'] for call in self.call_history)),
            'average_latency': 0
        }
        
        if self.call_history:
            # Calculer la latence moyenne si disponible
            latencies = []
            for i in range(1, len(self.call_history)):
                prev_call = self.call_history[i-1]
                curr_call = self.call_history[i]
                latency = curr_call['timestamp'] - prev_call['timestamp']
                latencies.append(latency)
            
            if latencies:
                stats['average_latency'] = sum(latencies) / len(latencies)
        
        return stats


# Décorateurs pour le mocking
def mock_external_service(service_name: str, config: MockConfig = None):
    """Décorateur pour mocker un service externe."""
    
    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            mock_manager = BaseMockManager(config)
            
            with patch(f'services.{service_name}') as mock_service:
                mock_manager.active_mocks[service_name] = mock_service
                
                # Passer le mock_manager au test
                if 'mock_manager' in test_func.__code__.co_varnames:
                    kwargs['mock_manager'] = mock_manager
                
                return test_func(*args, **kwargs)
        
        return wrapper
    return decorator


def mock_database_queries(query_limit: int = 10):
    """Décorateur pour limiter et mocker les requêtes de base de données."""
    
    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            from django.test.utils import override_settings
            from django.db import connection
            
            with override_settings(DEBUG=True):
                # Réinitialiser les requêtes
                connection.queries_log.clear()
                
                result = test_func(*args, **kwargs)
                
                # Vérifier le nombre de requêtes
                query_count = len(connection.queries)
                if query_count > query_limit:
                    raise AssertionError(
                        f"Too many database queries: {query_count} > {query_limit}"
                    )
                
                return result
        
        return wrapper
    return decorator


class MockFactory:
    """Factory pour créer différents types de mocks."""
    
    @staticmethod
    def create_service_mock(service_class: type, methods: Dict[str, Any] = None) -> Mock:
        """Crée un mock pour un service."""
        
        mock = Mock(spec=service_class)
        
        if methods:
            for method_name, return_value in methods.items():
                setattr(mock, method_name, Mock(return_value=return_value))
        
        return mock
    
    @staticmethod
    def create_model_mock(model_class: type, **field_values) -> Mock:
        """Crée un mock pour un modèle Django."""
        
        mock = Mock(spec=model_class)
        
        # Définir les valeurs des champs
        for field_name, value in field_values.items():
            setattr(mock, field_name, value)
        
        # Ajouter les méthodes communes des modèles
        mock.save = Mock()
        mock.delete = Mock()
        mock.refresh_from_db = Mock()
        mock.pk = field_values.get('id', 1)
        
        return mock
    
    @staticmethod
    def create_queryset_mock(model_class: type, objects: List[Any] = None) -> Mock:
        """Crée un mock pour un QuerySet."""
        
        objects = objects or []
        
        mock_queryset = Mock()
        mock_queryset.all.return_value = objects
        mock_queryset.filter.return_value = mock_queryset
        mock_queryset.exclude.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset
        mock_queryset.distinct.return_value = mock_queryset
        mock_queryset.count.return_value = len(objects)
        mock_queryset.exists.return_value = len(objects) > 0
        mock_queryset.first.return_value = objects[0] if objects else None
        mock_queryset.last.return_value = objects[-1] if objects else None
        mock_queryset.__iter__ = Mock(return_value=iter(objects))
        mock_queryset.__len__ = Mock(return_value=len(objects))
        
        return mock_queryset
    
    @staticmethod
    def create_graphql_context_mock(user=None, request=None) -> Mock:
        """Crée un mock pour le contexte GraphQL."""
        
        context = Mock()
        context.user = user
        context.request = request
        
        return context


class ExternalServiceMocker:
    """Mocker spécialisé pour les services externes."""
    
    def __init__(self):
        self.service_mocks = {}
        self.response_templates = {}
    
    def mock_email_service(self, responses: Dict[str, Any] = None):
        """Mock le service d'email."""
        
        default_responses = {
            'send_email': {
                'status': 'sent',
                'message_id': 'mock_message_123',
                'timestamp': time.time()
            },
            'send_bulk_email': {
                'status': 'sent',
                'sent_count': 10,
                'failed_count': 0
            },
            'get_delivery_status': {
                'status': 'delivered',
                'delivered_at': time.time()
            }
        }
        
        responses = responses or default_responses
        
        mock_service = Mock()
        for method, response in responses.items():
            getattr(mock_service, method).return_value = response
        
        self.service_mocks['email'] = mock_service
        return mock_service
    
    def mock_payment_service(self, responses: Dict[str, Any] = None):
        """Mock le service de paiement."""
        
        default_responses = {
            'process_payment': {
                'status': 'success',
                'transaction_id': 'txn_mock_123',
                'amount': 29.99,
                'currency': 'EUR',
                'timestamp': time.time()
            },
            'refund_payment': {
                'status': 'success',
                'refund_id': 'ref_mock_123',
                'amount': 29.99
            },
            'get_payment_status': {
                'status': 'completed',
                'payment_method': 'card'
            }
        }
        
        responses = responses or default_responses
        
        mock_service = Mock()
        for method, response in responses.items():
            getattr(mock_service, method).return_value = response
        
        self.service_mocks['payment'] = mock_service
        return mock_service
    
    def mock_storage_service(self, responses: Dict[str, Any] = None):
        """Mock le service de stockage."""
        
        default_responses = {
            'upload_file': {
                'status': 'uploaded',
                'file_url': 'https://mock-storage.com/files/test.jpg',
                'file_size': 1024,
                'file_type': 'image/jpeg'
            },
            'delete_file': {
                'status': 'deleted',
                'file_url': 'https://mock-storage.com/files/test.jpg'
            },
            'get_file_info': {
                'exists': True,
                'size': 1024,
                'last_modified': time.time()
            }
        }
        
        responses = responses or default_responses
        
        mock_service = Mock()
        for method, response in responses.items():
            getattr(mock_service, method).return_value = response
        
        self.service_mocks['storage'] = mock_service
        return mock_service
    
    def mock_notification_service(self, responses: Dict[str, Any] = None):
        """Mock le service de notifications."""
        
        default_responses = {
            'send_notification': {
                'status': 'sent',
                'notification_id': 'notif_mock_123',
                'recipients': ['user@example.com']
            },
            'send_push_notification': {
                'status': 'sent',
                'device_count': 5,
                'success_count': 5
            },
            'get_notification_status': {
                'status': 'delivered',
                'read': False
            }
        }
        
        responses = responses or default_responses
        
        mock_service = Mock()
        for method, response in responses.items():
            getattr(mock_service, method).return_value = response
        
        self.service_mocks['notification'] = mock_service
        return mock_service
    
    @contextmanager
    def patch_all_services(self):
        """Context manager pour patcher tous les services."""
        
        patches = []
        
        try:
            # Créer les patches pour tous les services
            for service_name, mock_service in self.service_mocks.items():
                patch_path = f'services.{service_name}_service.{service_name.title()}Service'
                patcher = patch(patch_path, return_value=mock_service)
                patches.append(patcher)
                patcher.start()
            
            yield self.service_mocks
            
        finally:
            # Arrêter tous les patches
            for patcher in patches:
                patcher.stop()


class DatabaseMocker:
    """Mocker spécialisé pour les opérations de base de données."""
    
    def __init__(self):
        self.model_mocks = {}
        self.queryset_mocks = {}
    
    def mock_model_manager(self, model_class: type, objects: List[Any] = None):
        """Mock le manager d'un modèle."""
        
        objects = objects or []
        
        # Créer un mock pour le manager
        manager_mock = Mock()
        
        # Mock des méthodes de base
        manager_mock.all.return_value = objects
        manager_mock.count.return_value = len(objects)
        manager_mock.exists.return_value = len(objects) > 0
        
        # Mock de filter avec logique simple
        def filter_mock(**kwargs):
            filtered_objects = []
            for obj in objects:
                match = True
                for key, value in kwargs.items():
                    if hasattr(obj, key) and getattr(obj, key) != value:
                        match = False
                        break
                if match:
                    filtered_objects.append(obj)
            
            return MockFactory.create_queryset_mock(model_class, filtered_objects)
        
        manager_mock.filter = filter_mock
        
        # Mock de get
        def get_mock(**kwargs):
            filtered = filter_mock(**kwargs)
            if len(filtered) == 0:
                raise model_class.DoesNotExist()
            elif len(filtered) > 1:
                raise model_class.MultipleObjectsReturned()
            return filtered[0]
        
        manager_mock.get = get_mock
        
        # Mock de create
        def create_mock(**kwargs):
            new_obj = MockFactory.create_model_mock(model_class, **kwargs)
            objects.append(new_obj)
            return new_obj
        
        manager_mock.create = create_mock
        
        self.model_mocks[model_class.__name__] = manager_mock
        return manager_mock
    
    @contextmanager
    def patch_model_managers(self, models: List[type]):
        """Context manager pour patcher les managers de modèles."""
        
        patches = []
        
        try:
            for model_class in models:
                if model_class.__name__ not in self.model_mocks:
                    self.mock_model_manager(model_class)
                
                patcher = patch.object(
                    model_class,
                    'objects',
                    self.model_mocks[model_class.__name__]
                )
                patches.append(patcher)
                patcher.start()
            
            yield self.model_mocks
            
        finally:
            for patcher in patches:
                patcher.stop()
    
    def mock_database_connection(self, query_results: Dict[str, Any] = None):
        """Mock la connexion à la base de données."""
        
        query_results = query_results or {}
        
        connection_mock = Mock()
        
        def execute_mock(query, params=None):
            # Simuler l'exécution de requêtes
            query_key = query.strip().split()[0].upper()  # SELECT, INSERT, etc.
            return query_results.get(query_key, [])
        
        connection_mock.execute = execute_mock
        connection_mock.fetchall = Mock(return_value=[])
        connection_mock.fetchone = Mock(return_value=None)
        
        return connection_mock


class GraphQLMocker:
    """Mocker spécialisé pour GraphQL."""
    
    def __init__(self):
        self.schema_mocks = {}
        self.resolver_mocks = {}
    
    def mock_resolver(self, field_name: str, return_value: Any = None, 
                     side_effect: Callable = None):
        """Mock un resolver GraphQL."""
        
        resolver_mock = Mock()
        
        if side_effect:
            resolver_mock.side_effect = side_effect
        else:
            resolver_mock.return_value = return_value
        
        self.resolver_mocks[field_name] = resolver_mock
        return resolver_mock
    
    def mock_schema_execution(self, query_responses: Dict[str, Any] = None):
        """Mock l'exécution du schéma GraphQL."""
        
        query_responses = query_responses or {}
        
        def execute_mock(query, variables=None, context=None):
            # Analyser la requête pour déterminer la réponse
            query_name = self._extract_query_name(query)
            
            if query_name in query_responses:
                return {
                    'data': query_responses[query_name],
                    'errors': None
                }
            else:
                return {
                    'data': None,
                    'errors': [{'message': f'Mock not found for query: {query_name}'}]
                }
        
        schema_mock = Mock()
        schema_mock.execute = execute_mock
        
        return schema_mock
    
    def _extract_query_name(self, query: str) -> str:
        """Extrait le nom de la requête GraphQL."""
        
        import re
        
        # Rechercher le nom de la requête ou mutation
        match = re.search(r'(query|mutation)\s+(\w+)', query)
        if match:
            return match.group(2)
        
        # Rechercher le premier champ de la requête
        match = re.search(r'{\s*(\w+)', query)
        if match:
            return match.group(1)
        
        return 'unknown'
    
    def create_mock_info(self, context=None, field_name: str = None):
        """Crée un mock pour l'objet info GraphQL."""
        
        info_mock = Mock()
        info_mock.context = context or Mock()
        info_mock.field_name = field_name or 'mock_field'
        info_mock.return_type = Mock()
        info_mock.parent_type = Mock()
        
        return info_mock


class ResponseMocker:
    """Mocker pour les réponses HTTP et API."""
    
    def __init__(self):
        self.response_templates = {}
    
    def create_http_response_mock(self, status_code: int = 200, 
                                 json_data: Dict[str, Any] = None,
                                 headers: Dict[str, str] = None):
        """Crée un mock de réponse HTTP."""
        
        response_mock = Mock()
        response_mock.status_code = status_code
        response_mock.json.return_value = json_data or {}
        response_mock.headers = headers or {}
        response_mock.text = str(json_data) if json_data else ''
        response_mock.content = response_mock.text.encode('utf-8')
        
        return response_mock
    
    def create_api_error_mock(self, error_code: str, error_message: str, 
                             status_code: int = 400):
        """Crée un mock d'erreur API."""
        
        error_data = {
            'error': {
                'code': error_code,
                'message': error_message
            }
        }
        
        return self.create_http_response_mock(status_code, error_data)
    
    @contextmanager
    def mock_requests(self, url_responses: Dict[str, Any]):
        """Context manager pour mocker les requêtes HTTP."""
        
        import requests_mock
        
        with requests_mock.Mocker() as m:
            for url, response_config in url_responses.items():
                method = response_config.get('method', 'GET')
                status_code = response_config.get('status_code', 200)
                json_data = response_config.get('json', {})
                
                m.register_uri(method, url, json=json_data, status_code=status_code)
            
            yield m


# Utilitaires pour les tests avec mocks
class MockTestUtils:
    """Utilitaires pour les tests avec mocks."""
    
    @staticmethod
    def assert_mock_called_with_pattern(mock_obj: Mock, pattern: Dict[str, Any]):
        """Vérifie qu'un mock a été appelé avec un pattern spécifique."""
        
        assert mock_obj.called, "Mock was not called"
        
        call_args = mock_obj.call_args
        if call_args is None:
            raise AssertionError("Mock was called but no call args found")
        
        args, kwargs = call_args
        
        for key, expected_value in pattern.items():
            if key in kwargs:
                actual_value = kwargs[key]
                if callable(expected_value):
                    assert expected_value(actual_value), \
                        f"Pattern check failed for {key}: {actual_value}"
                else:
                    assert actual_value == expected_value, \
                        f"Expected {key}={expected_value}, got {actual_value}"
            else:
                raise AssertionError(f"Expected argument {key} not found in call")
    
    @staticmethod
    def assert_mock_call_count(mock_obj: Mock, expected_count: int):
        """Vérifie le nombre d'appels d'un mock."""
        
        actual_count = mock_obj.call_count
        assert actual_count == expected_count, \
            f"Expected {expected_count} calls, got {actual_count}"
    
    @staticmethod
    def assert_mock_not_called_with(mock_obj: Mock, **kwargs):
        """Vérifie qu'un mock n'a pas été appelé avec certains arguments."""
        
        for call in mock_obj.call_args_list:
            call_kwargs = call[1]
            if all(call_kwargs.get(k) == v for k, v in kwargs.items()):
                raise AssertionError(f"Mock was called with forbidden args: {kwargs}")
    
    @staticmethod
    def get_mock_call_history(mock_obj: Mock) -> List[Dict[str, Any]]:
        """Retourne l'historique des appels d'un mock."""
        
        history = []
        
        for call in mock_obj.call_args_list:
            args, kwargs = call
            history.append({
                'args': args,
                'kwargs': kwargs,
                'timestamp': time.time()  # Approximatif
            })
        
        return history
    
    @staticmethod
    def create_mock_chain(chain_spec: List[Dict[str, Any]]) -> Mock:
        """Crée une chaîne de mocks pour des appels en cascade."""
        
        root_mock = Mock()
        current_mock = root_mock
        
        for spec in chain_spec:
            method_name = spec['method']
            return_value = spec.get('return_value')
            side_effect = spec.get('side_effect')
            
            next_mock = Mock()
            
            if side_effect:
                next_mock.side_effect = side_effect
            elif return_value is not None:
                next_mock.return_value = return_value
            
            setattr(current_mock, method_name, next_mock)
            current_mock = next_mock
        
        return root_mock


# Exemples d'utilisation
class ExampleMockUsage:
    """Exemples d'utilisation des stratégies de mocking."""
    
    def example_service_mocking(self):
        """Exemple de mocking de service externe."""
        
        # Configuration du mock
        config = MockConfig(
            simulate_latency=True,
            min_latency_ms=50,
            max_latency_ms=200,
            error_rate=0.1
        )
        
        # Créer le mocker
        service_mocker = ExternalServiceMocker()
        email_mock = service_mocker.mock_email_service()
        
        # Utiliser dans un test
        with service_mocker.patch_all_services():
            # Le service est maintenant mocké
            from services.email_service import EmailService
            
            service = EmailService()
            result = service.send_email(
                to='test@example.com',
                subject='Test',
                body='Test message'
            )
            
            assert result['status'] == 'sent'
            assert 'message_id' in result
    
    def example_database_mocking(self):
        """Exemple de mocking de base de données."""
        
        from tests.models import TestAuthor, TestBook
        
        # Créer des données de test
        test_authors = [
            MockFactory.create_model_mock(TestAuthor, id=1, name='Author 1'),
            MockFactory.create_model_mock(TestAuthor, id=2, name='Author 2')
        ]
        
        # Créer le mocker
        db_mocker = DatabaseMocker()
        db_mocker.mock_model_manager(TestAuthor, test_authors)
        
        # Utiliser dans un test
        with db_mocker.patch_model_managers([TestAuthor]):
            authors = TestAuthor.objects.all()
            assert len(authors) == 2
            
            author = TestAuthor.objects.get(id=1)
            assert author.name == 'Author 1'
    
    def example_graphql_mocking(self):
        """Exemple de mocking GraphQL."""
        
        # Créer le mocker
        graphql_mocker = GraphQLMocker()
        
        # Définir les réponses mockées
        query_responses = {
            'getAuthors': {
                'authors': [
                    {'id': '1', 'name': 'Author 1'},
                    {'id': '2', 'name': 'Author 2'}
                ]
            }
        }
        
        schema_mock = graphql_mocker.mock_schema_execution(query_responses)
        
        # Utiliser dans un test
        query = '''
            query getAuthors {
                authors {
                    id
                    name
                }
            }
        '''
        
        result = schema_mock.execute(query)
        assert result['data']['authors'][0]['name'] == 'Author 1'
```

Ce guide de stratégies de mocking fournit une approche complète et structurée pour créer des mocks efficaces dans les tests Django GraphQL, permettant d'isoler les composants et de tester de manière fiable et reproductible.