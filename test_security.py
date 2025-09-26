#!/usr/bin/env python
"""
Test script for security features in Django GraphQL Auto-Generation

This script tests authentication, permissions, validation, and rate limiting.
"""

import os
import sys
import django

# Setup Django BEFORE importing any Django modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from graphene.test import Client
import json

from django_graphql_auto.schema import schema
from django_graphql_auto.extensions.auth import JWTManager
from django_graphql_auto.extensions.permissions import PermissionManager
from django_graphql_auto.extensions.validation import InputValidator
from django_graphql_auto.extensions.rate_limiting import RateLimiter


class SecurityTestCase:
    """Test case for security features"""
    
    def __init__(self):
        self.client = Client(schema)
        self.factory = RequestFactory()
        self.jwt_manager = JWTManager()
        self.permission_manager = PermissionManager()
        self.input_validator = InputValidator()
        self.rate_limiter = RateLimiter()
        
    def setUp(self):
        """Set up test data"""
        # Create test user (check if exists first)
        try:
            self.test_user = User.objects.get(username='testuser')
        except User.DoesNotExist:
            self.test_user = User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpass123'
            )
        
    def test_authentication_queries(self):
        """Test authentication-related queries and mutations"""
        print("Testing Authentication System...")
        
        # Test registration
        register_mutation = '''
        mutation {
            register(username: "newuser", email: "new@example.com", password: "newpass123") {
                success
                errors
                token
                refreshToken
                user {
                    id
                    username
                    email
                }
            }
        }
        '''
        
        result = self.client.execute(register_mutation)
        print(f"Registration result: {result}")
        
        # Test login
        login_mutation = '''
        mutation {
            login(username: "testuser", password: "testpass123") {
                success
                errors
                token
                refreshToken
                user {
                    id
                    username
                    email
                }
            }
        }
        '''
        
        result = self.client.execute(login_mutation)
        print(f"Login result: {result}")
        
        # Test me query (requires authentication)
        me_query = '''
        query {
            me {
                id
                username
                email
                is_active
                date_joined
            }
        }
        '''
        
        # Create mock request with authentication
        request = self.factory.get('/')
        token = self.jwt_manager.generate_token(self.test_user)
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        
        result = self.client.execute(me_query, context={'request': request})
        print(f"Me query result: {result}")
        
    def test_permission_system(self):
        """Test permission system"""
        print("\nTesting Permission System...")
        
        # Test permission queries
        permissions_query = '''
        query {
            my_permissions {
                permissions
                groups
                is_superuser
                is_staff
            }
        }
        '''
        
        request = self.factory.get('/')
        request.user = self.test_user
        
        result = self.client.execute(permissions_query, context={'request': request})
        print(f"Permissions query result: {result}")
        
    def test_validation_system(self):
        """Test input validation"""
        print("\nTesting Validation System...")
        
        # Test validation query
        validation_query = '''
        query {
            validate_field(field_name: "email", value: "invalid-email") {
                field_name
                is_valid
                error_message
                sanitized_value
            }
        }
        '''
        
        result = self.client.execute(validation_query)
        print(f"Validation query result: {result}")
        
        # Test with valid email
        validation_query_valid = '''
        query {
            validate_field(field_name: "email", value: "valid@example.com") {
                field_name
                is_valid
                error_message
                sanitized_value
            }
        }
        '''
        
        result = self.client.execute(validation_query_valid)
        print(f"Valid validation query result: {result}")
        
    def test_security_info(self):
        """Test security information queries"""
        print("\nTesting Security Information...")
        
        # Test security info query
        security_query = '''
        query {
            security_info {
                remaining_requests
                window_reset_time
                current_complexity_limit
                current_depth_limit
            }
        }
        '''
        
        result = self.client.execute(security_query)
        print(f"Security info result: {result}")
        
        # Test query stats
        stats_query = '''
        query {
            query_stats {
                total_queries
                avg_complexity
                avg_depth
                avg_execution_time
                success_rate
            }
        }
        '''
        
        result = self.client.execute(stats_query)
        print(f"Query stats result: {result}")
        
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\nTesting Rate Limiting...")
        
        # Test rate limiting
        rate_limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        for i in range(5):
            try:
                allowed, wait_time = rate_limiter.check_rate_limit("test_user")
                print(f"Request {i+1}: {'Allowed' if allowed else f'Rate limited (wait {wait_time}s)'}")
            except Exception as e:
                print(f"Request {i+1}: Rate limited - {e}")
                
    def test_query_complexity(self):
        """Test query complexity analysis"""
        print("\nTesting Query Complexity...")
        
        # Simple query
        simple_query = '''
        query {
            me {
                id
                username
            }
        }
        '''
        
        # Complex nested query
        complex_query = '''
        query {
            me {
                id
                username
                email
                groups {
                    id
                    name
                    permissions {
                        id
                        name
                        contentType {
                            id
                            appLabel
                            model
                        }
                    }
                }
            }
        }
        '''
        
        from django_graphql_auto.extensions.rate_limiting import QueryComplexityAnalyzer
        analyzer = QueryComplexityAnalyzer(max_complexity=10)
        
        # Parse queries
        from graphql import parse
        simple_parsed = parse(simple_query)
        complex_parsed = parse(complex_query)
        
        try:
            simple_complexity = analyzer.analyze_complexity(simple_parsed)
            print(f"Simple query complexity: {simple_complexity}")
            
            complex_complexity = analyzer.analyze_complexity(complex_parsed)
            print(f"Complex query complexity: {complex_complexity}")
        except Exception as e:
            print(f"Complexity analysis error: {e}")
            
    def run_all_tests(self):
        """Run all security tests"""
        print("=== Django GraphQL Auto Security Tests ===\n")
        
        try:
            self.setUp()
            self.test_authentication_queries()
            self.test_permission_system()
            self.test_validation_system()
            self.test_security_info()
            self.test_rate_limiting()
            self.test_query_complexity()
            
            print("\n=== All Security Tests Completed ===")
            
        except Exception as e:
            print(f"Test error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    test_case = SecurityTestCase()
    test_case.run_all_tests()