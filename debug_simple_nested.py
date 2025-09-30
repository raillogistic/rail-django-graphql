# -*- coding: utf-8 -*-
"""
Simple debug script to trace nested operations
"""

import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from rail_django_graphql.generators.nested_operations import NestedOperationHandler

# Monkey patch handle_nested_create to add logging
original_handle_nested_create = NestedOperationHandler.handle_nested_create


def debug_handle_nested_create(self, model, data, parent_instance=None):
    print(f"\n=== handle_nested_create called ===")
    print(f"Model: {model}")
    print(f"Data: {data}")
    print(f"Data types: {[(k, type(v)) for k, v in data.items()]}")
    print(f"Parent instance: {parent_instance}")

    # Check specifically for author field
    if "author" in data:
        print(f"Author field: {data['author']} (type: {type(data['author'])})")
        if hasattr(data["author"], "pk"):
            print(f"Author pk: {data['author'].pk}")

    if "author_id" in data:
        print(f"Author_id field: {data['author_id']} (type: {type(data['author_id'])})")

    try:
        result = original_handle_nested_create(self, model, data, parent_instance)
        print(f"SUCCESS: Created {result}")
        return result
    except Exception as e:
        print(f"ERROR in handle_nested_create: {e}")
        raise


NestedOperationHandler.handle_nested_create = debug_handle_nested_create

# Also patch handle_nested_update
original_handle_nested_update = NestedOperationHandler.handle_nested_update


def debug_handle_nested_update(self, model, input_data, instance):
    print(f"\n=== handle_nested_update called ===")
    print(f"Model: {model}")
    print(f"Instance: {instance}")
    print(f"Input data: {input_data}")

    try:
        result = original_handle_nested_update(self, model, input_data, instance)
        print(f"Update result: {result}")
        return result
    except Exception as e:
        print(f"ERROR in handle_nested_update: {e}")
        raise


NestedOperationHandler.handle_nested_update = debug_handle_nested_update

from rail_django_graphql.schema import schema


def test_debug():
    print("=== SIMPLE NESTED DEBUG ===")

    # Clean up
    Comment.objects.filter(content__contains="simple_test").delete()
    Post.objects.filter(title__contains="Simple Test").delete()
    User.objects.filter(username="simple_user").delete()
    Category.objects.filter(name="Simple Category").delete()

    # Create test data
    user = User.objects.create_user(username="simple_user", email="simple@test.com")
    category = Category.objects.create(name="Simple Category")
    post = Post.objects.create(
        title="Simple Test Post", content="Test content", category=category
    )

    print(f"Created post {post.id}, user {user.id}")

    # Test the mutation
    mutation = f"""
    mutation {{
        update_post(id:"{post.id}",input:{{ 
            nested_comments:[ 
                {{content:"simple_test",author:"{user.id}"}}, 
            ], 
            title:"Simple Test Updated", 
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
        import traceback

        traceback.print_exc()

    print("=== DEBUG COMPLETE ===")


if __name__ == "__main__":
    test_debug()
