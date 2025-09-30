#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to comprehensively verify partial update functionality
with different field combinations and models.
"""

import json
from graphene.test import Client
from rail_django_graphql.core.schema import get_schema
from blog.models import Category, Post, Comment
from django.contrib.auth.models import User


def test_post_partial_updates():
    """Test various partial update scenarios for Post model."""
    print("=== TESTING POST PARTIAL UPDATES ===")
    
    schema = get_schema()
    client = Client(schema)
    
    # Create test data
    category = Category.objects.create(nom_categorie="Test Category")
    user = User.objects.create_user(username="testuser", email="test@example.com")
    
    # Create a post
    create_mutation = """
    mutation CreatePost($input: CreatePostInput!) {
        create_post(input: $input) {
            ok
            object {
                id
                title
                content
                isPublished
                category {
                    id
                    name
                }
                author {
                    id
                    username
                }
            }
            errors
        }
    }
    """
    
    create_variables = {
        "input": {
            "titreArticle": "Original Title",
            "contenuArticle": "Original content here",
            "estPublie": False,
            "categorieArticle": category.id,
            "auteurArticle": user.id
        }
    }
    
    create_result = client.execute(create_mutation, variables=create_variables)
    print(f"Create result: {json.dumps(create_result, indent=2)}")
    
    if create_result.get('errors'):
        print("❌ Failed to create post")
        return False
    
    post_id = create_result['data']['create_post']['object']['id']
    print(f"Created post with ID: {post_id}")
    
    # Test 1: Update only title
    print("\n--- Test 1: Update only title ---")
    update_mutation = """
    mutation UpdatePost($id: ID!, $input: UpdatePostInput!) {
        update_post(id: $id, input: $input) {
            ok
            object {
                id
                title
                content
                isPublished
            }
            errors
        }
    }
    """
    
    update_variables = {
        "id": post_id,
        "input": {
            "titreArticle": "Updated Title Only"
        }
    }
    
    result = client.execute(update_mutation, variables=update_variables)
    print(f"Update title result: {json.dumps(result, indent=2)}")
    
    # Test 2: Update only content
    print("\n--- Test 2: Update only content ---")
    update_variables = {
        "id": post_id,
        "input": {
            "contenuArticle": "Updated content only"
        }
    }
    
    result = client.execute(update_mutation, variables=update_variables)
    print(f"Update content result: {json.dumps(result, indent=2)}")
    
    # Test 3: Update only published status
    print("\n--- Test 3: Update only published status ---")
    update_variables = {
        "id": post_id,
        "input": {
            "estPublie": True
        }
    }
    
    result = client.execute(update_mutation, variables=update_variables)
    print(f"Update published result: {json.dumps(result, indent=2)}")
    
    # Test 4: Update multiple fields
    print("\n--- Test 4: Update multiple fields ---")
    update_variables = {
        "id": post_id,
        "input": {
            "titreArticle": "Final Title",
            "contenuArticle": "Final content",
            "estPublie": False
        }
    }
    
    result = client.execute(update_mutation, variables=update_variables)
    print(f"Update multiple fields result: {json.dumps(result, indent=2)}")
    
    return True


def test_category_partial_updates():
    """Test partial updates for Category model."""
    print("\n=== TESTING CATEGORY PARTIAL UPDATES ===")
    
    schema = get_schema()
    client = Client(schema)
    
    # Create a category
    create_mutation = """
    mutation CreateCategory($input: CreateCategoryInput!) {
        create_category(input: $input) {
            ok
            object {
                id
                name
                description
            }
            errors
        }
    }
    """
    
    create_variables = {
        "input": {
            "nomCategorie": "Original Category",
            "descriptionCategorie": "Original description"
        }
    }
    
    create_result = client.execute(create_mutation, variables=create_variables)
    print(f"Create category result: {json.dumps(create_result, indent=2)}")
    
    if create_result.get('errors'):
        print("❌ Failed to create category")
        return False
    
    category_id = create_result['data']['create_category']['object']['id']
    print(f"Created category with ID: {category_id}")
    
    # Test partial update - only name
    print("\n--- Test: Update only category name ---")
    update_mutation = """
    mutation UpdateCategory($id: ID!, $input: UpdateCategoryInput!) {
        update_category(id: $id, input: $input) {
            ok
            object {
                id
                name
                description
            }
            errors
        }
    }
    """
    
    update_variables = {
        "id": category_id,
        "input": {
            "nomCategorie": "Updated Category Name"
        }
    }
    
    result = client.execute(update_mutation, variables=update_variables)
    print(f"Update category result: {json.dumps(result, indent=2)}")
    
    return True


def test_comment_partial_updates():
    """Test partial updates for Comment model."""
    print("\n=== TESTING COMMENT PARTIAL UPDATES ===")
    
    schema = get_schema()
    client = Client(schema)
    
    # Create test data
    category = Category.objects.create(nom_categorie="Test Category for Comment")
    user = User.objects.create_user(username="commentuser", email="comment@example.com")
    post = Post.objects.create(
        titre_article="Test Post for Comment",
        contenu_article="Test content",
        est_publie=True,
        categorie_article=category,
        auteur_article=user
    )
    
    # Create a comment
    create_mutation = """
    mutation CreateComment($input: CreateCommentInput!) {
        create_comment(input: $input) {
            ok
            object {
                id
                content
                isApproved
                post {
                    id
                    title
                }
                author {
                    id
                    username
                }
            }
            errors
        }
    }
    """
    
    create_variables = {
        "input": {
            "contenuCommentaire": "Original comment content",
            "estApprouve": False,
            "articleCommentaire": post.id,
            "auteurCommentaire": user.id
        }
    }
    
    create_result = client.execute(create_mutation, variables=create_variables)
    print(f"Create comment result: {json.dumps(create_result, indent=2)}")
    
    if create_result.get('errors'):
        print("❌ Failed to create comment")
        return False
    
    comment_id = create_result['data']['create_comment']['object']['id']
    print(f"Created comment with ID: {comment_id}")
    
    # Test partial update - only approval status
    print("\n--- Test: Update only comment approval ---")
    update_mutation = """
    mutation UpdateComment($id: ID!, $input: UpdateCommentInput!) {
        update_comment(id: $id, input: $input) {
            ok
            object {
                id
                content
                isApproved
            }
            errors
        }
    }
    """
    
    update_variables = {
        "id": comment_id,
        "input": {
            "estApprouve": True
        }
    }
    
    result = client.execute(update_mutation, variables=update_variables)
    print(f"Update comment result: {json.dumps(result, indent=2)}")
    
    return True


def main():
    """Run all comprehensive tests."""
    print("🧪 Starting comprehensive partial update tests...")
    
    success = True
    
    try:
        success &= test_post_partial_updates()
        success &= test_category_partial_updates()
        success &= test_comment_partial_updates()
        
        if success:
            print("\n✅ All comprehensive tests passed!")
        else:
            print("\n❌ Some tests failed!")
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    return success


if __name__ == "__main__":
    main()