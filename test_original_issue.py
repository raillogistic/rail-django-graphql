# -*- coding: utf-8 -*-
"""
Test the original issue that was reported
"""

import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from rail_django_graphql.schema import schema


def test_original_issue():
    print("=== TESTING ORIGINAL ISSUE ===")

    # Clean up
    Comment.objects.filter(content__contains="c2xx").delete()
    Post.objects.filter(title__contains="xxx").delete()

    # Get or create test data (using existing IDs from the original issue)
    try:
        user = User.objects.get(pk=57)
    except User.DoesNotExist:
        user = User.objects.create_user(
            username="test_user_57", email="test57@test.com"
        )
        user.pk = 57
        user.save()

    try:
        post = Post.objects.get(pk=115)
    except Post.DoesNotExist:
        category = Category.objects.create(name="Test Category")
        post = Post.objects.create(
            title="Test Post", content="Test content", category=category
        )
        post.pk = 115
        post.save()

    try:
        comment = Comment.objects.get(pk=82)
    except Comment.DoesNotExist:
        comment = Comment.objects.create(
            content="Original comment", author=user, post=post
        )
        comment.pk = 82
        comment.save()

    print(f"Using post {post.id}, comment {comment.id}, user {user.id}")

    # Test the exact mutation from the original issue
    mutation = """
    mutation {
        update_post(id:"115",input:{ 
            nested_comments:[ 
                {content:"c2xx",author:"57",id:"82"}, 
            ], 
            title:"xxx", 
        }){ 
            ok 
            object{ 
                comments{ 
                    pk 
                    content 
                    author{ 
                        pk 
                    } 
                } 
            } 
            errors 
        } 
    }
    """

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

    print("SUCCESS: Original issue is now fixed!")
    print(f"Result: {result.data}")

    # Verify the comment was updated
    updated_comment = Comment.objects.get(pk=82)
    print(f"Updated comment content: {updated_comment.content}")
    print(f"Comment author ID: {updated_comment.author.id}")

    if updated_comment.content == "c2xx" and updated_comment.author.id == 57:
        print("✅ VERIFICATION PASSED: Comment was properly updated with foreign key!")
    else:
        print("❌ VERIFICATION FAILED: Comment was not updated correctly")

    print("=== TEST COMPLETE ===")


if __name__ == "__main__":
    test_original_issue()
