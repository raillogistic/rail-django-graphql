# -*- coding: utf-8 -*-
"""
Test creating new comments without IDs in nested updates
"""

import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from rail_django_graphql.schema import schema


def test_new_comment_creation():
    print("=== TESTING NEW COMMENT CREATION ===")

    # Clean up
    Comment.objects.filter(content__contains="c2xx").delete()
    Post.objects.filter(title__contains="xxx").delete()
    User.objects.filter(username="test_new_user").delete()
    Category.objects.filter(name="Test New Category").delete()

    # Create test data
    user = User.objects.create_user(username="test_new_user", email="test_new@test.com")
    category = Category.objects.create(name="Test New Category")
    post = Post.objects.create(
        title="Test New Post", content="Test content", category=category
    )

    print(f"Created post {post.id}, user {user.id}")

    # Test the exact mutation that's failing - creating a new comment without ID
    mutation = f"""
    mutation {{
        update_post(id:"{post.id}",input:{{ 
            nested_comments:[ 
                {{content:"c2xx",author:"{user.id}"}}, 
            ], 
            title:"xxx", 
        }}){{ 
            ok 
            object{{ 
                comments{{ 
                    pk 
                    content 
                    author{{ 
                        pk 
                    }} 
                }} 
            }} 
            errors 
        }} 
    }}
    """

    print("Executing mutation...")
    print(f"Mutation: {mutation}")

    try:
        result = schema.execute(mutation)
    except Exception as e:
        print(f"Schema execution error: {e}")
        return

    if result.errors:
        print("MUTATION ERRORS:")
        for error in result.errors:
            print(f"  {error}")
        return

    if result.data["update_post"]["errors"]:
        print("UPDATE ERRORS:")
        for error in result.data["update_post"]["errors"]:
            print(f"  {error}")
        return

    print("SUCCESS: New comment created successfully!")
    print(f"Result: {result.data}")

    # Check the created comment
    comments = Comment.objects.filter(post=post)
    print(f"Comments in DB: {list(comments.values('id', 'content', 'author_id'))}")

    print("=== TEST COMPLETE ===")


if __name__ == "__main__":
    test_new_comment_creation()
