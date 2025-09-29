# -*- coding: utf-8 -*-
"""
Debug script to intercept the exact model.objects.create call
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category

# Monkey patch Comment.objects.create to see what's being passed
original_create = Comment.objects.create

def debug_create(**kwargs):
    print(f"=== Comment.objects.create called ===")
    print(f"Arguments: {kwargs}")
    print(f"Argument types: {[(k, type(v)) for k, v in kwargs.items()]}")
    
    # Check for author field specifically
    if 'author' in kwargs:
        print(f"Author field: {kwargs['author']} (type: {type(kwargs['author'])})")
    if 'author_id' in kwargs:
        print(f"Author_id field: {kwargs['author_id']} (type: {type(kwargs['author_id'])})")
    if 'post' in kwargs:
        print(f"Post field: {kwargs['post']} (type: {type(kwargs['post'])})")
    if 'post_id' in kwargs:
        print(f"Post_id field: {kwargs['post_id']} (type: {type(kwargs['post_id'])})")
    
    try:
        result = original_create(**kwargs)
        print(f"SUCCESS: Created {result}")
        return result
    except Exception as e:
        print(f"ERROR in create: {e}")
        raise

Comment.objects.create = debug_create

from django_graphql_auto.schema import schema

def test_debug():
    print("=== DEBUGGING EXACT CREATE CALL ===")
    
    # Clean up
    Comment.objects.filter(content__contains="c2xx").delete()
    Post.objects.filter(title__contains="xxx").delete()
    User.objects.filter(username="test_exact_user").delete()
    Category.objects.filter(name="Test Exact Category").delete()
    
    # Create test data
    user = User.objects.create_user(username='test_exact_user', email='test_exact@test.com')
    category = Category.objects.create(name='Test Exact Category')
    post = Post.objects.create(title='Test Exact Post', content='Test content', category=category)
    
    print(f"Created post {post.id}, user {user.id}")
    
    # Test the exact mutation that's failing
    mutation = f'''
    mutation {{
        update_post(id:"{post.id}",input:{{ 
            nested_comments:[ 
                {{content:"c2xx",author:"{user.id}"}}, 
            ], 
            title:"xxx", 
        }}){{ 
            ok 
            errors 
        }} 
    }}
    '''
    
    print("Executing mutation...")
    
    try:
        result = schema.execute(mutation)
        print(f"Result: {result.data}")
        if result.errors:
            print(f"Errors: {result.errors}")
    except Exception as e:
        print(f"Exception: {e}")
    
    print("=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    test_debug()