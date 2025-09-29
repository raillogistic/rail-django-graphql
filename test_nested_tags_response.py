#!/usr/bin/env python3
"""
Test script to examine GraphQL response structure for nested tags.
This will help us understand what's happening with nested fields in responses.
"""

import os
import sys
import django
from django.conf import settings

# Configure Django settings
settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    INSTALLED_APPS=[
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'test_app',
        'django_graphql_auto',
    ],
    SECRET_KEY='test-secret-key',
    USE_TZ=True,
)

django.setup()

import requests
import json
import time
from test_app.models import Post, Tag, Category

def test_graphql_response():
    """Test the actual GraphQL response structure."""
    
    # GraphQL endpoint
    url = "http://127.0.0.1:8000/graphql/"
    
    # First, create some test data via GraphQL
    create_mutation = """
    mutation CreatePost($input: CreatePostInput!) {
        create_post(input: $input) {
            ok
            object {
                id
                title
                tags {
                    id
                    name
                }
            }
            errors
        }
    }
    """
    
    create_variables = {
        "input": {
            "title": "Test Post with Tags",
            "content": "This is a test post",
            "category": "132",  # Use existing Technology category
            "nested_tags": [
                {"name": "GraphQL-Test-" + str(int(time.time()))},
                {"name": "Django-Test-" + str(int(time.time()))},
                {"name": "Python-Test-" + str(int(time.time()))}
            ]
        }
    }
    
    print("=== CREATING POST WITH NESTED TAGS ===")
    try:
        response = requests.post(url, json={
            'query': create_mutation,
            'variables': create_variables
        })
        
        if response.status_code == 200:
            data = response.json()
            print("Create Response:")
            print(json.dumps(data, indent=2))
            
            if data.get('data', {}).get('create_post', {}).get('ok'):
                post_id = data['data']['create_post']['object']['id']
                print(f"\nPost created successfully with ID: {post_id}")
                
                # Now test update with nested tags
                test_update_response(url, post_id)
            else:
                print("Failed to create post")
                print("Errors:", data.get('data', {}).get('create_post', {}).get('errors', []))
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error creating post: {e}")

def test_update_response(url, post_id):
    """Test update mutation response structure."""
    
    update_mutation = """
    mutation UpdatePost($id: ID!, $input: UpdatePostInput!) {
        update_post(id: $id, input: $input) {
            ok
            object {
                id
                title
                tags {
                    id
                    name
                }
            }
            errors
        }
    }
    """
    
    update_variables = {
            "id": post_id,
            "input": {
                "title": "Updated Post with More Tags",
                "nested_tags": [
                    {"name": "Updated-Tag-1-" + str(int(time.time()))},
                    {"name": "Updated-Tag-2-" + str(int(time.time()))}
                ]
            }
        }
    
    print("\n=== UPDATING POST WITH NESTED TAGS ===")
    try:
        response = requests.post(url, json={
            'query': update_mutation,
            'variables': update_variables
        })
        
        if response.status_code == 200:
            data = response.json()
            print("Update Response:")
            print(json.dumps(data, indent=2))
            
            # Check if tags were actually created/updated
            if data.get('data', {}).get('update_post', {}).get('ok'):
                tags = data['data']['update_post']['object']['tags']
                print(f"\nTags in response: {len(tags)}")
                for tag in tags:
                    print(f"  - {tag['name']} (ID: {tag['id']})")
            else:
                print("Update failed")
                print("Errors:", data.get('data', {}).get('update_post', {}).get('errors', []))
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error updating post: {e}")

def test_introspection():
    """Test GraphQL schema introspection to see available fields."""
    
    url = "http://127.0.0.1:8000/graphql/"
    
    introspection_query = """
    query {
        __schema {
            mutationType {
                fields {
                    name
                    args {
                        name
                        type {
                            name
                            inputFields {
                                name
                                type {
                                    name
                                    ofType {
                                        name
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    print("\n=== SCHEMA INTROSPECTION ===")
    try:
        response = requests.post(url, json={'query': introspection_query})
        
        if response.status_code == 200:
            data = response.json()
            
            # Find update_post mutation
            mutations = data['data']['__schema']['mutationType']['fields']
            update_post_mutation = None
            
            for mutation in mutations:
                if mutation['name'] == 'update_post':
                    update_post_mutation = mutation
                    break
            
            if update_post_mutation:
                print("UpdatePost mutation found:")
                for arg in update_post_mutation['args']:
                    if arg['name'] == 'input':
                        input_fields = arg['type']['inputFields']
                        print("Available input fields:")
                        for field in input_fields:
                            print(f"  - {field['name']}: {field['type']['name'] or field['type']['ofType']['name']}")
            else:
                print("UpdatePost mutation not found")
                print("Available mutations:")
                for mutation in mutations:
                    print(f"  - {mutation['name']}")
        else:
            print(f"HTTP Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error in introspection: {e}")

if __name__ == "__main__":
    print("Testing GraphQL Response Structure for Nested Tags")
    print("=" * 60)
    
    # First check if server is running with a simple introspection query
    try:
        simple_query = """
        query {
            __schema {
                queryType {
                    name
                }
            }
        }
        """
        response = requests.post("http://127.0.0.1:8000/graphql/", json={'query': simple_query})
        if response.status_code == 200:
            print("GraphQL server is running")
            test_introspection()
            test_graphql_response()
        else:
            print(f"GraphQL server not accessible: {response.status_code}")
            print(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print("GraphQL server is not running. Please start it with: python manage.py runserver")
    except Exception as e:
        print(f"Error connecting to GraphQL server: {e}")