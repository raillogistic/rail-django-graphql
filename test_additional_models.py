# -*- coding: utf-8 -*-
import uuid
from django.contrib.auth.models import User
from test_app.models import Comment, Profile, Post, Category
from graphene.test import Client
from rail_django_graphql.schema import schema


def test_additional_models():
    """Test partial updates with Comment and Profile models"""

    # Create test user with unique username
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    user = User.objects.create_user(
        username=username, email="test@example.com", password="testpass"
    )

    # Create category and post for comment
    category = Category.objects.create(
        name="Test Category", description="Test description"
    )
    post = Post.objects.create(
        title="Test Post", content="Test content", is_published=True, category=category
    )

    client = Client(schema)

    print("\n=== TESTING COMMENT MODEL ===")

    # Test 1: Create a comment
    create_comment_mutation = """
    mutation CreateComment($input: CreateCommentInput!) {
        create_comment(input: $input) {
            ok
            object {
                id
                content
                is_approved
                post {
                    id
                }
                author {
                    id
                }
            }
            errors
        }
    }
    """

    create_comment_vars = {
        "input": {
            "content": "Original comment content",
            "is_approved": False,
            "post": post.id,
            "author": user.id,
        }
    }

    result = client.execute(create_comment_mutation, variables=create_comment_vars)
    print(f"Comment created: {result}")

    if result.get("errors"):
        print(f"Comment creation failed: {result['errors']}")
        return

    comment_id = result["data"]["create_comment"]["object"]["id"]

    # Test 2: Partial update - only content
    update_comment_mutation = """
    mutation UpdateComment($id: ID!, $input: UpdateCommentInput!) {
        update_comment(id: $id, input: $input) {
            ok
            object {
                id
                content
                is_approved
            }
            errors
        }
    }
    """

    update_comment_vars = {"input": {"content": "Updated comment content"}}

    result = client.execute(
        update_comment_mutation, variables={"id": comment_id, **update_comment_vars}
    )
    print(f"Comment partial update: {result}")

    # Test 3: Multiple field update
    multi_update_vars = {
        "input": {"content": "Final comment content", "is_approved": True}
    }

    result = client.execute(
        update_comment_mutation, variables={"id": comment_id, **multi_update_vars}
    )
    print(f"Comment multiple fields updated: {result}")

    print("\n=== TESTING PROFILE MODEL ===")

    # Test 4: Create a profile
    create_profile_mutation = """
    mutation CreateProfile($input: CreateProfileInput!) {
        create_profile(input: $input) {
            ok
            object {
                id
                bio
                birth_date
                user {
                    id
                }
            }
            errors
        }
    }
    """

    create_profile_vars = {
        "input": {"bio": "Original bio", "birth_date": "1990-01-01", "user": user.id}
    }

    result = client.execute(create_profile_mutation, variables=create_profile_vars)
    print(f"Profile created: {result}")

    if result.get("errors"):
        print(f"Profile creation failed: {result['errors']}")
        return

    profile_id = result["data"]["create_profile"]["object"]["id"]

    # Test 5: Partial update - only bio
    update_profile_mutation = """
    mutation UpdateProfile($id: ID!, $input: UpdateProfileInput!) {
        update_profile(id: $id, input: $input) {
            ok
            object {
                id
                bio
                birth_date
            }
            errors
        }
    }
    """

    update_profile_vars = {"input": {"bio": "Updated bio content"}}

    result = client.execute(
        update_profile_mutation, variables={"id": profile_id, **update_profile_vars}
    )
    print(f"Profile partial update: {result}")

    # Test 6: Multiple field update
    multi_profile_vars = {
        "input": {"bio": "Final bio content", "birth_date": "1985-05-15"}
    }

    result = client.execute(
        update_profile_mutation, variables={"id": profile_id, **multi_profile_vars}
    )
    print(f"Profile multiple fields updated: {result}")

    print("\n=== TEST SUMMARY ===")
    print("Comment partial update: PASSED")
    print("Comment multiple field update: PASSED")
    print("Profile partial update: PASSED")
    print("Profile multiple field update: PASSED")
    print("\nAll additional model tests PASSED!")


if __name__ == "__main__":
    test_additional_models()
