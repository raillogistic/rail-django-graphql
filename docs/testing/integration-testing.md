# Tests d'Intégration - Django GraphQL Auto

Ce guide détaille les stratégies et techniques de tests d'intégration pour les applications GraphQL Django, couvrant les tests end-to-end, l'intégration de base de données, et les services externes.

## 📋 Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Tests End-to-End](#tests-end-to-end)
- [Intégration Base de Données](#intégration-base-de-données)
- [Intégration Services Externes](#intégration-services-externes)
- [Tests de Workflow](#tests-de-workflow)
- [Tests d'API GraphQL](#tests-dapi-graphql)
- [Tests de Performance Intégrée](#tests-de-performance-intégrée)
- [Environnements de Test](#environnements-de-test)
- [Outils et Utilitaires](#outils-et-utilitaires)
- [Bonnes Pratiques](#bonnes-pratiques)

## 🎯 Vue d'Ensemble

### Architecture des Tests d'Intégration

```python
# tests/integration/base.py
"""Base pour les tests d'intégration."""

import pytest
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from django.test import TransactionTestCase
from django.db import transaction
from unittest.mock import Mock, patch
import requests_mock
import time


@dataclass
class IntegrationTestConfig:
    """Configuration pour les tests d'intégration."""
    
    use_real_database: bool = True
    use_external_services: bool = False
    cleanup_after_test: bool = True
    parallel_execution: bool = False
    timeout_seconds: int = 30
    retry_attempts: int = 3


class BaseIntegrationTest(TransactionTestCase):
    """Classe de base pour les tests d'intégration."""
    
    # Configuration par défaut
    config = IntegrationTestConfig()
    
    # Services externes mockés
    external_services = {}
    
    # Données de test partagées
    test_data = {}
    
    @classmethod
    def setUpClass(cls):
        """Configuration de classe pour les tests d'intégration."""
        super().setUpClass()
        
        # Initialiser les services externes si nécessaire
        if cls.config.use_external_services:
            cls._setup_external_services()
        else:
            cls._setup_service_mocks()
        
        # Préparer les données de test
        cls._setup_test_data()
    
    @classmethod
    def tearDownClass(cls):
        """Nettoyage après tous les tests."""
        super().tearDownClass()
        
        if cls.config.cleanup_after_test:
            cls._cleanup_test_data()
    
    def setUp(self):
        """Configuration avant chaque test."""
        super().setUp()
        
        # Démarrer une transaction pour l'isolation
        if self.config.use_real_database:
            transaction.set_autocommit(False)
        
        # Initialiser les métriques de test
        self.test_metrics = {
            'start_time': time.time(),
            'database_queries': 0,
            'external_calls': 0,
            'memory_usage': 0
        }
    
    def tearDown(self):
        """Nettoyage après chaque test."""
        super().tearDown()
        
        # Rollback de la transaction
        if self.config.use_real_database:
            transaction.rollback()
            transaction.set_autocommit(True)
        
        # Enregistrer les métriques
        self.test_metrics['duration'] = time.time() - self.test_metrics['start_time']
        self._record_test_metrics()
    
    @classmethod
    def _setup_external_services(cls):
        """Configure les services externes réels."""
        
        # Configuration pour les services réels
        cls.external_services = {
            'email_service': {
                'url': 'https://api.emailservice.com',
                'api_key': 'test_api_key'
            },
            'payment_service': {
                'url': 'https://api.paymentservice.com',
                'api_key': 'test_payment_key'
            },
            'storage_service': {
                'url': 'https://api.storageservice.com',
                'bucket': 'test-bucket'
            }
        }
    
    @classmethod
    def _setup_service_mocks(cls):
        """Configure les mocks pour les services externes."""
        
        cls.service_mocks = {
            'email_service': Mock(),
            'payment_service': Mock(),
            'storage_service': Mock()
        }
        
        # Configuration des réponses mockées
        cls.service_mocks['email_service'].send_email.return_value = {
            'status': 'sent',
            'message_id': 'mock_message_id'
        }
        
        cls.service_mocks['payment_service'].process_payment.return_value = {
            'status': 'success',
            'transaction_id': 'mock_transaction_id'
        }
        
        cls.service_mocks['storage_service'].upload_file.return_value = {
            'status': 'uploaded',
            'file_url': 'https://mock.storage.com/file.jpg'
        }
    
    @classmethod
    def _setup_test_data(cls):
        """Prépare les données de test partagées."""
        
        from tests.factories import UserFactory, AuthorFactory, BookFactory
        
        # Créer des données de base
        cls.test_data = {
            'users': UserFactory.create_batch(5),
            'authors': AuthorFactory.create_batch(3),
            'books': BookFactory.create_batch(10),
            'admin_user': UserFactory.create(is_staff=True, is_superuser=True)
        }
    
    @classmethod
    def _cleanup_test_data(cls):
        """Nettoie les données de test."""
        
        # Supprimer les données créées
        for data_type, objects in cls.test_data.items():
            if isinstance(objects, list):
                for obj in objects:
                    try:
                        obj.delete()
                    except Exception as e:
                        print(f"Erreur lors de la suppression de {obj}: {e}")
            else:
                try:
                    objects.delete()
                except Exception as e:
                    print(f"Erreur lors de la suppression de {objects}: {e}")
    
    def _record_test_metrics(self):
        """Enregistre les métriques de test."""
        
        # Enregistrer dans un fichier ou une base de données
        # pour analyse ultérieure
        pass
    
    def execute_graphql_query(self, query: str, variables: Dict[str, Any] = None,
                             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Exécute une requête GraphQL avec gestion d'erreurs."""
        
        from graphene.test import Client
        from tests.schema import schema
        
        client = Client(schema)
        
        try:
            result = client.execute(
                query,
                variables=variables or {},
                context=context or {}
            )
            
            # Compter les requêtes de base de données
            from django.db import connection
            self.test_metrics['database_queries'] += len(connection.queries)
            
            return result
            
        except Exception as e:
            return {
                'errors': [{'message': str(e)}]
            }
    
    def assert_graphql_success(self, response: Dict[str, Any]):
        """Vérifie qu'une réponse GraphQL est réussie."""
        
        assert 'errors' not in response or len(response.get('errors', [])) == 0, \
            f"GraphQL errors: {response.get('errors', [])}"
        
        assert 'data' in response, "No data in GraphQL response"
    
    def assert_graphql_error(self, response: Dict[str, Any], 
                           expected_error: str = None):
        """Vérifie qu'une réponse GraphQL contient une erreur."""
        
        assert 'errors' in response and len(response['errors']) > 0, \
            "Expected GraphQL errors but none found"
        
        if expected_error:
            error_messages = [error['message'] for error in response['errors']]
            assert any(expected_error in msg for msg in error_messages), \
                f"Expected error '{expected_error}' not found in {error_messages}"


class DatabaseIntegrationTest(BaseIntegrationTest):
    """Tests d'intégration avec la base de données."""
    
    def test_database_transaction_integrity(self):
        """Test de l'intégrité des transactions."""
        
        from tests.models import TestAuthor, TestBook
        
        # Créer un auteur
        author_data = {
            'first_name': 'Test',
            'last_name': 'Author',
            'email': 'test@example.com'
        }
        
        query = '''
            mutation CreateAuthor($input: AuthorInput!) {
                createAuthor(input: $input) {
                    author {
                        id
                        firstName
                        lastName
                        email
                    }
                }
            }
        '''
        
        response = self.execute_graphql_query(query, {'input': author_data})
        self.assert_graphql_success(response)
        
        author_id = response['data']['createAuthor']['author']['id']
        
        # Vérifier que l'auteur existe en base
        author = TestAuthor.objects.get(id=author_id)
        assert author.first_name == 'Test'
        assert author.last_name == 'Author'
        assert author.email == 'test@example.com'
    
    def test_database_constraint_enforcement(self):
        """Test de l'application des contraintes de base de données."""
        
        # Tenter de créer un auteur avec un email dupliqué
        author_data = {
            'first_name': 'Duplicate',
            'last_name': 'Email',
            'email': 'duplicate@example.com'
        }
        
        query = '''
            mutation CreateAuthor($input: AuthorInput!) {
                createAuthor(input: $input) {
                    author {
                        id
                        email
                    }
                }
            }
        '''
        
        # Première création - doit réussir
        response1 = self.execute_graphql_query(query, {'input': author_data})
        self.assert_graphql_success(response1)
        
        # Deuxième création - doit échouer
        response2 = self.execute_graphql_query(query, {'input': author_data})
        self.assert_graphql_error(response2, 'already exists')
    
    def test_complex_database_relationships(self):
        """Test des relations complexes en base de données."""
        
        # Créer un auteur avec plusieurs livres
        query = '''
            mutation CreateAuthorWithBooks($authorInput: AuthorInput!, $bookInputs: [BookInput!]!) {
                createAuthor(input: $authorInput) {
                    author {
                        id
                        firstName
                        lastName
                    }
                }
                createBooks(inputs: $bookInputs) {
                    books {
                        id
                        title
                        author {
                            id
                            firstName
                        }
                    }
                }
            }
        '''
        
        variables = {
            'authorInput': {
                'firstName': 'Prolific',
                'lastName': 'Writer',
                'email': 'prolific@example.com'
            },
            'bookInputs': [
                {
                    'title': 'First Book',
                    'isbn': '1111111111111',
                    'pages': 200
                },
                {
                    'title': 'Second Book',
                    'isbn': '2222222222222',
                    'pages': 300
                }
            ]
        }
        
        response = self.execute_graphql_query(query, variables)
        self.assert_graphql_success(response)
        
        # Vérifier les relations en base
        from tests.models import TestAuthor, TestBook
        
        author = TestAuthor.objects.get(email='prolific@example.com')
        books = TestBook.objects.filter(author=author)
        
        assert books.count() == 2
        assert set(book.title for book in books) == {'First Book', 'Second Book'}
    
    def test_database_performance_with_large_dataset(self):
        """Test de performance avec un grand jeu de données."""
        
        # Créer beaucoup de données
        from tests.factories import AuthorFactory, BookFactory
        
        authors = AuthorFactory.create_batch(100)
        books = []
        
        for author in authors:
            author_books = BookFactory.create_batch(5, author=author)
            books.extend(author_books)
        
        # Requête complexe avec jointures
        query = '''
            query GetAuthorsWithBooks {
                authors {
                    id
                    firstName
                    lastName
                    books {
                        id
                        title
                        pages
                        category {
                            id
                            name
                        }
                    }
                }
            }
        '''
        
        start_time = time.time()
        response = self.execute_graphql_query(query)
        execution_time = time.time() - start_time
        
        self.assert_graphql_success(response)
        
        # Vérifier les performances
        assert execution_time < 5.0, f"Query took too long: {execution_time}s"
        assert len(response['data']['authors']) == 100
        
        # Vérifier le nombre de requêtes SQL (éviter N+1)
        assert self.test_metrics['database_queries'] < 10, \
            f"Too many database queries: {self.test_metrics['database_queries']}"


class ExternalServiceIntegrationTest(BaseIntegrationTest):
    """Tests d'intégration avec les services externes."""
    
    def setUp(self):
        """Configuration spécifique aux services externes."""
        super().setUp()
        
        # Configurer les mocks pour les services externes
        self.email_service_mock = Mock()
        self.payment_service_mock = Mock()
        self.storage_service_mock = Mock()
    
    @patch('services.email_service.EmailService')
    def test_email_service_integration(self, mock_email_service):
        """Test d'intégration avec le service d'email."""
        
        # Configurer le mock
        mock_email_service.return_value.send_email.return_value = {
            'status': 'sent',
            'message_id': 'test_message_123'
        }
        
        # Mutation qui déclenche l'envoi d'email
        query = '''
            mutation SendWelcomeEmail($userId: ID!) {
                sendWelcomeEmail(userId: $userId) {
                    success
                    messageId
                }
            }
        '''
        
        user = self.test_data['users'][0]
        response = self.execute_graphql_query(query, {'userId': str(user.id)})
        
        self.assert_graphql_success(response)
        assert response['data']['sendWelcomeEmail']['success'] is True
        assert response['data']['sendWelcomeEmail']['messageId'] == 'test_message_123'
        
        # Vérifier que le service a été appelé
        mock_email_service.return_value.send_email.assert_called_once()
    
    @patch('services.payment_service.PaymentService')
    def test_payment_service_integration(self, mock_payment_service):
        """Test d'intégration avec le service de paiement."""
        
        # Configurer le mock pour un paiement réussi
        mock_payment_service.return_value.process_payment.return_value = {
            'status': 'success',
            'transaction_id': 'txn_123456',
            'amount': 29.99
        }
        
        query = '''
            mutation ProcessPayment($input: PaymentInput!) {
                processPayment(input: $input) {
                    success
                    transactionId
                    amount
                }
            }
        '''
        
        payment_data = {
            'amount': 29.99,
            'currency': 'EUR',
            'cardToken': 'card_token_123',
            'description': 'Test payment'
        }
        
        response = self.execute_graphql_query(query, {'input': payment_data})
        
        self.assert_graphql_success(response)
        assert response['data']['processPayment']['success'] is True
        assert response['data']['processPayment']['transactionId'] == 'txn_123456'
        
        # Vérifier l'appel au service
        mock_payment_service.return_value.process_payment.assert_called_once_with(
            amount=29.99,
            currency='EUR',
            card_token='card_token_123',
            description='Test payment'
        )
    
    @patch('services.storage_service.StorageService')
    def test_file_upload_integration(self, mock_storage_service):
        """Test d'intégration avec le service de stockage."""
        
        # Configurer le mock
        mock_storage_service.return_value.upload_file.return_value = {
            'status': 'uploaded',
            'file_url': 'https://storage.example.com/files/test.jpg',
            'file_size': 1024
        }
        
        query = '''
            mutation UploadFile($file: Upload!) {
                uploadFile(file: $file) {
                    success
                    fileUrl
                    fileSize
                }
            }
        '''
        
        # Simuler un fichier uploadé
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        test_file = SimpleUploadedFile(
            "test.jpg",
            b"fake image content",
            content_type="image/jpeg"
        )
        
        response = self.execute_graphql_query(
            query,
            {'file': test_file}
        )
        
        self.assert_graphql_success(response)
        assert response['data']['uploadFile']['success'] is True
        assert 'storage.example.com' in response['data']['uploadFile']['fileUrl']
        
        # Vérifier l'appel au service
        mock_storage_service.return_value.upload_file.assert_called_once()
    
    def test_external_service_failure_handling(self):
        """Test de gestion des échecs de services externes."""
        
        with patch('services.email_service.EmailService') as mock_email:
            # Simuler un échec du service
            mock_email.return_value.send_email.side_effect = Exception("Service unavailable")
            
            query = '''
                mutation SendWelcomeEmail($userId: ID!) {
                    sendWelcomeEmail(userId: $userId) {
                        success
                        error
                    }
                }
            '''
            
            user = self.test_data['users'][0]
            response = self.execute_graphql_query(query, {'userId': str(user.id)})
            
            # Le système doit gérer l'erreur gracieusement
            self.assert_graphql_success(response)
            assert response['data']['sendWelcomeEmail']['success'] is False
            assert 'Service unavailable' in response['data']['sendWelcomeEmail']['error']
    
    @requests_mock.Mocker()
    def test_http_api_integration(self, m):
        """Test d'intégration avec des APIs HTTP externes."""
        
        # Mocker une API externe
        m.get('https://api.external-service.com/data', json={
            'status': 'success',
            'data': {
                'id': 123,
                'name': 'External Data',
                'value': 'test_value'
            }
        })
        
        query = '''
            query GetExternalData($id: ID!) {
                externalData(id: $id) {
                    id
                    name
                    value
                }
            }
        '''
        
        response = self.execute_graphql_query(query, {'id': '123'})
        
        self.assert_graphql_success(response)
        assert response['data']['externalData']['name'] == 'External Data'
        assert response['data']['externalData']['value'] == 'test_value'
        
        # Vérifier que l'API a été appelée
        assert m.called
        assert m.call_count == 1


class WorkflowIntegrationTest(BaseIntegrationTest):
    """Tests d'intégration de workflows complets."""
    
    def test_complete_user_registration_workflow(self):
        """Test du workflow complet d'inscription utilisateur."""
        
        # Étape 1: Créer un compte utilisateur
        registration_query = '''
            mutation RegisterUser($input: RegistrationInput!) {
                registerUser(input: $input) {
                    user {
                        id
                        username
                        email
                        isActive
                    }
                    token
                }
            }
        '''
        
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'firstName': 'New',
            'lastName': 'User'
        }
        
        with patch('services.email_service.EmailService') as mock_email:
            mock_email.return_value.send_email.return_value = {'status': 'sent'}
            
            response = self.execute_graphql_query(
                registration_query,
                {'input': registration_data}
            )
        
        self.assert_graphql_success(response)
        user_data = response['data']['registerUser']['user']
        token = response['data']['registerUser']['token']
        
        assert user_data['username'] == 'newuser'
        assert user_data['email'] == 'newuser@example.com'
        assert user_data['isActive'] is False  # En attente de vérification
        
        # Étape 2: Vérifier l'email
        verification_query = '''
            mutation VerifyEmail($token: String!) {
                verifyEmail(token: $token) {
                    success
                    user {
                        isActive
                    }
                }
            }
        '''
        
        response = self.execute_graphql_query(
            verification_query,
            {'token': token}
        )
        
        self.assert_graphql_success(response)
        assert response['data']['verifyEmail']['success'] is True
        assert response['data']['verifyEmail']['user']['isActive'] is True
        
        # Étape 3: Connexion
        login_query = '''
            mutation Login($input: LoginInput!) {
                login(input: $input) {
                    success
                    token
                    user {
                        id
                        username
                    }
                }
            }
        '''
        
        login_data = {
            'username': 'newuser',
            'password': 'securepassword123'
        }
        
        response = self.execute_graphql_query(
            login_query,
            {'input': login_data}
        )
        
        self.assert_graphql_success(response)
        assert response['data']['login']['success'] is True
        assert response['data']['login']['user']['username'] == 'newuser'
        
        # Étape 4: Accès aux données utilisateur
        profile_query = '''
            query {
                me {
                    id
                    username
                    email
                    profile {
                        firstName
                        lastName
                    }
                }
            }
        '''
        
        auth_token = response['data']['login']['token']
        response = self.execute_graphql_query(
            profile_query,
            context={'token': auth_token}
        )
        
        self.assert_graphql_success(response)
        assert response['data']['me']['username'] == 'newuser'
        assert response['data']['me']['profile']['firstName'] == 'New'
    
    def test_book_publication_workflow(self):
        """Test du workflow complet de publication de livre."""
        
        # Étape 1: Créer un auteur
        author_query = '''
            mutation CreateAuthor($input: AuthorInput!) {
                createAuthor(input: $input) {
                    author {
                        id
                        firstName
                        lastName
                    }
                }
            }
        '''
        
        author_data = {
            'firstName': 'Jane',
            'lastName': 'Doe',
            'email': 'jane.doe@example.com',
            'bio': 'Acclaimed author'
        }
        
        response = self.execute_graphql_query(author_query, {'input': author_data})
        self.assert_graphql_success(response)
        
        author_id = response['data']['createAuthor']['author']['id']
        
        # Étape 2: Créer une catégorie
        category_query = '''
            mutation CreateCategory($input: CategoryInput!) {
                createCategory(input: $input) {
                    category {
                        id
                        name
                    }
                }
            }
        '''
        
        category_data = {
            'name': 'Fiction',
            'description': 'Fictional works'
        }
        
        response = self.execute_graphql_query(category_query, {'input': category_data})
        self.assert_graphql_success(response)
        
        category_id = response['data']['createCategory']['category']['id']
        
        # Étape 3: Créer le livre
        book_query = '''
            mutation CreateBook($input: BookInput!) {
                createBook(input: $input) {
                    book {
                        id
                        title
                        isbn
                        author {
                            firstName
                            lastName
                        }
                        category {
                            name
                        }
                        status
                    }
                }
            }
        '''
        
        book_data = {
            'title': 'The Great Novel',
            'isbn': '9781234567890',
            'pages': 350,
            'authorId': author_id,
            'categoryId': category_id,
            'description': 'A masterpiece of modern literature'
        }
        
        response = self.execute_graphql_query(book_query, {'input': book_data})
        self.assert_graphql_success(response)
        
        book_id = response['data']['createBook']['book']['id']
        assert response['data']['createBook']['book']['status'] == 'DRAFT'
        
        # Étape 4: Publier le livre
        publish_query = '''
            mutation PublishBook($id: ID!) {
                publishBook(id: $id) {
                    book {
                        id
                        status
                        publicationDate
                    }
                }
            }
        '''
        
        with patch('services.notification_service.NotificationService') as mock_notify:
            mock_notify.return_value.send_notification.return_value = {'status': 'sent'}
            
            response = self.execute_graphql_query(publish_query, {'id': book_id})
        
        self.assert_graphql_success(response)
        assert response['data']['publishBook']['book']['status'] == 'PUBLISHED'
        assert response['data']['publishBook']['book']['publicationDate'] is not None
        
        # Étape 5: Vérifier la visibilité publique
        public_query = '''
            query GetPublishedBooks {
                publishedBooks {
                    id
                    title
                    author {
                        firstName
                        lastName
                    }
                    status
                }
            }
        '''
        
        response = self.execute_graphql_query(public_query)
        self.assert_graphql_success(response)
        
        published_books = response['data']['publishedBooks']
        book_titles = [book['title'] for book in published_books]
        assert 'The Great Novel' in book_titles
    
    def test_error_recovery_workflow(self):
        """Test de récupération d'erreurs dans un workflow."""
        
        # Simuler un workflow qui échoue à mi-parcours
        query = '''
            mutation ComplexWorkflow($input: WorkflowInput!) {
                executeWorkflow(input: $input) {
                    success
                    steps {
                        name
                        status
                        error
                    }
                    rollbackPerformed
                }
            }
        '''
        
        workflow_data = {
            'steps': [
                {'name': 'create_user', 'data': {'username': 'testuser'}},
                {'name': 'send_email', 'data': {'email': 'invalid-email'}},  # Ceci va échouer
                {'name': 'create_profile', 'data': {'bio': 'Test bio'}}
            ]
        }
        
        with patch('services.email_service.EmailService') as mock_email:
            # Simuler un échec d'email
            mock_email.return_value.send_email.side_effect = Exception("Invalid email")
            
            response = self.execute_graphql_query(query, {'input': workflow_data})
        
        self.assert_graphql_success(response)
        
        workflow_result = response['data']['executeWorkflow']
        assert workflow_result['success'] is False
        assert workflow_result['rollbackPerformed'] is True
        
        # Vérifier les statuts des étapes
        steps = workflow_result['steps']
        assert steps[0]['status'] == 'COMPLETED'  # create_user réussi
        assert steps[1]['status'] == 'FAILED'     # send_email échoué
        assert steps[2]['status'] == 'SKIPPED'    # create_profile ignoré
        
        # Vérifier que le rollback a été effectué
        from django.contrib.auth.models import User
        assert not User.objects.filter(username='testuser').exists()


class PerformanceIntegrationTest(BaseIntegrationTest):
    """Tests de performance intégrée."""
    
    def test_concurrent_requests_handling(self):
        """Test de gestion des requêtes concurrentes."""
        
        import threading
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        query = '''
            query GetBooks {
                books {
                    id
                    title
                    author {
                        firstName
                        lastName
                    }
                }
            }
        '''
        
        def execute_query():
            start_time = time.time()
            response = self.execute_graphql_query(query)
            execution_time = time.time() - start_time
            
            return {
                'response': response,
                'execution_time': execution_time,
                'success': 'errors' not in response
            }
        
        # Exécuter 20 requêtes concurrentes
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(execute_query) for _ in range(20)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyser les résultats
        successful_requests = sum(1 for result in results if result['success'])
        average_time = sum(result['execution_time'] for result in results) / len(results)
        max_time = max(result['execution_time'] for result in results)
        
        # Assertions
        assert successful_requests == 20, f"Only {successful_requests}/20 requests succeeded"
        assert average_time < 1.0, f"Average response time too high: {average_time}s"
        assert max_time < 3.0, f"Maximum response time too high: {max_time}s"
    
    def test_large_dataset_pagination(self):
        """Test de pagination avec de gros volumes de données."""
        
        # Créer beaucoup de données
        from tests.factories import BookFactory
        BookFactory.create_batch(1000)
        
        query = '''
            query GetBooksPaginated($first: Int!, $after: String) {
                books(first: $first, after: $after) {
                    edges {
                        node {
                            id
                            title
                        }
                        cursor
                    }
                    pageInfo {
                        hasNextPage
                        endCursor
                    }
                }
            }
        '''
        
        # Tester la pagination
        all_books = []
        cursor = None
        page_count = 0
        
        while True:
            variables = {'first': 50}
            if cursor:
                variables['after'] = cursor
            
            start_time = time.time()
            response = self.execute_graphql_query(query, variables)
            execution_time = time.time() - start_time
            
            self.assert_graphql_success(response)
            
            # Vérifier les performances de chaque page
            assert execution_time < 2.0, f"Page {page_count} took too long: {execution_time}s"
            
            books_page = response['data']['books']
            all_books.extend([edge['node'] for edge in books_page['edges']])
            
            page_count += 1
            
            if not books_page['pageInfo']['hasNextPage']:
                break
            
            cursor = books_page['pageInfo']['endCursor']
            
            # Éviter les boucles infinies
            if page_count > 25:  # 1000 / 50 = 20 pages maximum
                break
        
        # Vérifications finales
        assert len(all_books) >= 1000, f"Expected at least 1000 books, got {len(all_books)}"
        assert page_count <= 25, f"Too many pages: {page_count}"
        
        # Vérifier l'unicité des IDs
        book_ids = [book['id'] for book in all_books]
        assert len(book_ids) == len(set(book_ids)), "Duplicate books found in pagination"


# Utilitaires pour les tests d'intégration
class IntegrationTestUtils:
    """Utilitaires pour les tests d'intégration."""
    
    @staticmethod
    def wait_for_condition(condition_func, timeout=10, interval=0.1):
        """Attend qu'une condition soit remplie."""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        
        return False
    
    @staticmethod
    def assert_eventually(assertion_func, timeout=5, message="Condition not met"):
        """Vérifie qu'une assertion devient vraie dans un délai donné."""
        
        def condition():
            try:
                assertion_func()
                return True
            except AssertionError:
                return False
        
        if not IntegrationTestUtils.wait_for_condition(condition, timeout):
            raise AssertionError(f"{message} (timeout after {timeout}s)")
    
    @staticmethod
    def create_test_environment():
        """Crée un environnement de test complet."""
        
        from tests.factories import UserFactory, AuthorFactory, BookFactory, CategoryFactory
        
        # Créer des utilisateurs
        admin_user = UserFactory.create(is_staff=True, is_superuser=True)
        regular_users = UserFactory.create_batch(5)
        
        # Créer des catégories
        categories = CategoryFactory.create_batch(5)
        
        # Créer des auteurs
        authors = AuthorFactory.create_batch(10)
        
        # Créer des livres
        books = []
        for author in authors:
            author_books = BookFactory.create_batch(
                3,
                author=author,
                category=lambda: random.choice(categories)
            )
            books.extend(author_books)
        
        return {
            'admin_user': admin_user,
            'regular_users': regular_users,
            'categories': categories,
            'authors': authors,
            'books': books
        }
    
    @staticmethod
    def cleanup_test_environment(test_data):
        """Nettoie l'environnement de test."""
        
        for data_type, objects in test_data.items():
            if isinstance(objects, list):
                for obj in objects:
                    try:
                        obj.delete()
                    except Exception:
                        pass
            else:
                try:
                    objects.delete()
                except Exception:
                    pass
```

Ce guide de tests d'intégration fournit une base complète pour tester les interactions complexes entre les différents composants du système Django GraphQL Auto, garantissant la fiabilité et les performances de l'application dans son ensemble.