#!/usr/bin/env python
"""
Test script for JWT-protected export endpoints.

This script tests the export functionality with and without valid JWT tokens
to ensure proper authentication is enforced.
"""

import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

from django.contrib.auth.models import User
from rail_django_graphql.extensions.auth import JWTManager


class ExportJWTTester:
    """Test JWT authentication for export endpoints."""
    
    def __init__(self, base_url="http://localhost:8000"):
        """
        Initialize the tester.
        
        Args:
            base_url: Base URL of the Django application
        """
        self.base_url = base_url
        self.export_url = f"{base_url}/api/export/"
        self.jwt_manager = JWTManager()
        
    def create_test_user(self):
        """Create a test user for JWT token generation."""
        try:
            user = User.objects.get(username='test_export_user')
        except User.DoesNotExist:
            user = User.objects.create_user(
                username='test_export_user',
                email='test@example.com',
                password='testpassword123'
            )
        return user
    
    def generate_jwt_token(self, user):
        """Generate a valid JWT token for the test user."""
        return self.jwt_manager.generate_token(user)
    
    def generate_expired_token(self, user):
        """Generate an expired JWT token for testing."""
        # Create a token that expired 1 hour ago
        expired_payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() - timedelta(hours=1),
            'iat': datetime.utcnow() - timedelta(hours=2)
        }
        return self.jwt_manager._encode_token(expired_payload)
    
    def test_export_without_token(self):
        """Test export endpoint without JWT token (should fail)."""
        print("🔒 Testing export without JWT token...")
        
        payload = {
            "model": "auth.User",
            "fields": ["username", "email", "date_joined"],
            "format": "csv"
        }
        
        try:
            response = requests.post(self.export_url, json=payload)
            
            if response.status_code == 401:
                print("✅ PASS: Export correctly rejected without JWT token")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.json()}")
            else:
                print("❌ FAIL: Export should have been rejected without JWT token")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: Request failed - {e}")
    
    def test_export_with_invalid_token(self):
        """Test export endpoint with invalid JWT token (should fail)."""
        print("\n🔒 Testing export with invalid JWT token...")
        
        headers = {
            "Authorization": "Bearer invalid_token_here",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "auth.User", 
            "fields": ["username", "email"],
            "format": "csv"
        }
        
        try:
            response = requests.post(self.export_url, json=payload, headers=headers)
            
            if response.status_code == 401:
                print("✅ PASS: Export correctly rejected with invalid JWT token")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.json()}")
            else:
                print("❌ FAIL: Export should have been rejected with invalid JWT token")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: Request failed - {e}")
    
    def test_export_with_expired_token(self):
        """Test export endpoint with expired JWT token (should fail)."""
        print("\n🔒 Testing export with expired JWT token...")
        
        user = self.create_test_user()
        expired_token = self.generate_expired_token(user)
        
        headers = {
            "Authorization": f"Bearer {expired_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "auth.User",
            "fields": ["username", "email"],
            "format": "csv"
        }
        
        try:
            response = requests.post(self.export_url, json=payload, headers=headers)
            
            if response.status_code == 401:
                print("✅ PASS: Export correctly rejected with expired JWT token")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.json()}")
            else:
                print("❌ FAIL: Export should have been rejected with expired JWT token")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: Request failed - {e}")
    
    def test_export_with_valid_token(self):
        """Test export endpoint with valid JWT token (should succeed)."""
        print("\n🔓 Testing export with valid JWT token...")
        
        user = self.create_test_user()
        valid_token = self.generate_jwt_token(user)
        
        headers = {
            "Authorization": f"Bearer {valid_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "auth.User",
            "fields": ["username", "email", "date_joined"],
            "format": "csv",
            "filters": {
                "quick_search": {
                    "query": "test",
                    "fields": ["username", "email"]
                }
            }
        }
        
        try:
            response = requests.post(self.export_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                print("✅ PASS: Export succeeded with valid JWT token")
                print(f"   Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('Content-Type')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                
                # Check if it's a CSV file
                if 'text/csv' in response.headers.get('Content-Type', ''):
                    print("   ✅ Correct CSV content type")
                    # Show first few lines of CSV
                    csv_content = response.content.decode('utf-8')
                    lines = csv_content.split('\n')[:3]
                    print(f"   CSV Preview: {lines}")
                    
            else:
                print("❌ FAIL: Export should have succeeded with valid JWT token")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: Request failed - {e}")
    
    def test_get_endpoint_without_token(self):
        """Test GET endpoint (API docs) without JWT token (should fail)."""
        print("\n📖 Testing GET endpoint without JWT token...")
        
        try:
            response = requests.get(self.export_url)
            
            if response.status_code == 401:
                print("✅ PASS: GET endpoint correctly rejected without JWT token")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.json()}")
            else:
                print("❌ FAIL: GET endpoint should have been rejected without JWT token")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: Request failed - {e}")
    
    def test_get_endpoint_with_valid_token(self):
        """Test GET endpoint (API docs) with valid JWT token (should succeed)."""
        print("\n📖 Testing GET endpoint with valid JWT token...")
        
        user = self.create_test_user()
        valid_token = self.generate_jwt_token(user)
        
        headers = {
            "Authorization": f"Bearer {valid_token}"
        }
        
        try:
            response = requests.get(self.export_url, headers=headers)
            
            if response.status_code == 200:
                print("✅ PASS: GET endpoint succeeded with valid JWT token")
                print(f"   Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('Content-Type')}")
                
                # Check if it returns API documentation
                if 'application/json' in response.headers.get('Content-Type', ''):
                    docs = response.json()
                    if 'description' in docs and 'parameters' in docs:
                        print("   ✅ Correct API documentation structure")
                    else:
                        print("   ⚠️  Unexpected API documentation format")
                        
            else:
                print("❌ FAIL: GET endpoint should have succeeded with valid JWT token")
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ ERROR: Request failed - {e}")
    
    def run_all_tests(self):
        """Run all JWT authentication tests."""
        print("🚀 Starting JWT Export Authentication Tests")
        print("=" * 50)
        
        # Test cases without authentication
        self.test_export_without_token()
        self.test_export_with_invalid_token()
        self.test_export_with_expired_token()
        self.test_get_endpoint_without_token()
        
        # Test cases with valid authentication
        self.test_export_with_valid_token()
        self.test_get_endpoint_with_valid_token()
        
        print("\n" + "=" * 50)
        print("🏁 JWT Export Authentication Tests Completed")


def main():
    """Main function to run the tests."""
    print("JWT Export Authentication Test Suite")
    print("This script tests JWT protection on export endpoints")
    print()
    
    # Check if Django server is running
    tester = ExportJWTTester()
    
    try:
        # Quick connectivity test
        response = requests.get(tester.base_url, timeout=5)
        print(f"✅ Django server is accessible at {tester.base_url}")
    except requests.exceptions.RequestException:
        print(f"❌ Cannot connect to Django server at {tester.base_url}")
        print("Please ensure your Django development server is running:")
        print("   python manage.py runserver")
        return
    
    # Run the tests
    tester.run_all_tests()


if __name__ == "__main__":
    main()