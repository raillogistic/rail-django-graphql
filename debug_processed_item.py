# -*- coding: utf-8 -*-
"""
Debug script to see what data is being passed to handle_nested_create
"""

import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from rail_django_graphql.generators.nested_operations import NestedOperationHandler

# Monkey patch to add debug logging
original_handle_nested_create = NestedOperationHandler.handle_nested_create


def debug_handle_nested_create(self, model, data, parent_instance=None):
    print(f"=== handle_nested_create called ===")
    print(f"Model: {model}")
    print(f"Data: {data}")
    print(f"Data types: {[(k, type(v)) for k, v in data.items()]}")

    # Check if author field exists and its value
    if "author" in data:
        print(f"Author field: {data['author']} (type: {type(data['author'])})")

    try:
        result = original_handle_nested_create(self, model, data, parent_instance)
        print(f"Result: {result}")
        return result
    except Exception as e:
        print(f"ERROR in handle_nested_create: {e}")
        raise


NestedOperationHandler.handle_nested_create = debug_handle_nested_create

from rail_django_graphql.schema import schema


def test_debug():
    print("=== DEBUGGING PROCESSED ITEM ===")

    # Clean up
    Comment.objects.filter(content__contains="c2xx").delete()
    Post.objects.filter(title__contains="xxx").delete()
    User.objects.filter(username="test_debug_user").delete()
    Category.objects.filter(name="Test Debug Category").delete()

    # Create test data
    user = User.objects.create_user(
        username="test_debug_user", email="test_debug@test.com"
    )
    category = Category.objects.create(name="Test Debug Category")
    post = Post.objects.create(
        title="Test Debug Post", content="Test content", category=category
    )

    print(f"Created post {post.id}, user {user.id}")

    # Test the exact mutation that's failing
    mutation = f"""
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
    """

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
