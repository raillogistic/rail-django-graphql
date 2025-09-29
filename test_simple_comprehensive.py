#!/usr/bin/env python
"""
Simple comprehensive test for partial update functionality.
"""

import json
from graphene.test import Client
from django_graphql_auto.core.schema import get_schema
from test_app.models import Category, Post
from django.contrib.auth.models import User


def test_multiple_models():
    """Test partial updates across different models."""
    print("=== COMPREHENSIVE PARTIAL UPDATE TEST ===")
    
    schema = get_schema()
    client = Client(schema)
    
    # Test 1: Category partial update
    print("\n--- Testing Category Updates ---")
    
    # Create category
    create_cat = """
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
    
    cat_vars = {
        "input": {
            "name": "Original Category",
            "description": "Original description"
        }
    }
    
    cat_result = client.execute(create_cat, variables=cat_vars)
    print(f"Category created: {json.dumps(cat_result, indent=2)}")
    
    if cat_result.get('errors') or not cat_result['data']['create_category']['ok']:
        print("Failed to create category")
        return False
    
    cat_id = cat_result['data']['create_category']['object']['id']
    
    # Update only category name
    update_cat = """
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
    
    update_cat_vars = {
        "id": cat_id,
        "input": {
            "name": "Updated Category Name"
        }
    }
    
    cat_update_result = client.execute(update_cat, variables=update_cat_vars)
    print(f"Category updated: {json.dumps(cat_update_result, indent=2)}")
    
    # Test 2: Post partial update
    print("\n--- Testing Post Updates ---")
    
    # Create user first
    import uuid
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    user = User.objects.create_user(username=username, email=f"{username}@example.com")
    category = Category.objects.filter(name="Updated Category Name").first()
    if not category:
        print("Category not found, using first available category")
        category = Category.objects.first()
    
    # Create post
    create_post = """
    mutation CreatePost($input: CreatePostInput!) {
        create_post(input: $input) {
            ok
            object {
                id
                title
                content
                is_published
            }
            errors
        }
    }
    """
    
    post_vars = {
        "input": {
            "title": "Original Post Title",
            "content": "Original post content",
            "is_published": False,
            "category": category.id
        }
    }
    
    post_result = client.execute(create_post, variables=post_vars)
    print(f"Post created: {json.dumps(post_result, indent=2)}")
    
    if post_result.get('errors') or not post_result['data']['create_post']['ok']:
        print("Failed to create post")
        return False
    
    post_id = post_result['data']['create_post']['object']['id']
    
    # Update only post title
    update_post = """
    mutation UpdatePost($id: ID!, $input: UpdatePostInput!) {
        update_post(id: $id, input: $input) {
            ok
            object {
                id
                title
                content
                is_published
            }
            errors
        }
    }
    """
    
    update_post_vars = {
        "id": post_id,
        "input": {
            "title": "Updated Post Title Only"
        }
    }
    
    post_update_result = client.execute(update_post, variables=update_post_vars)
    print(f"Post updated: {json.dumps(post_update_result, indent=2)}")
    
    # Test 3: Update multiple fields
    print("\n--- Testing Multiple Field Updates ---")
    
    multi_update_vars = {
        "id": post_id,
        "input": {
            "title": "Final Title",
            "is_published": True
        }
    }
    
    multi_result = client.execute(update_post, variables=multi_update_vars)
    print(f"Multiple fields updated: {json.dumps(multi_result, indent=2)}")
    
    print("\n=== TEST SUMMARY ===")
    
    # Check if all updates were successful
    success = True
    
    if cat_update_result.get('errors') or not cat_update_result['data']['update_category']['ok']:
        print("Category update failed")
        success = False
    else:
        print("Category partial update: PASSED")
    
    if post_update_result.get('errors') or not post_update_result['data']['update_post']['ok']:
        print("Post update failed")
        success = False
    else:
        print("Post partial update: PASSED")
    
    if multi_result.get('errors') or not multi_result['data']['update_post']['ok']:
        print("Multiple field update failed")
        success = False
    else:
        print("Multiple field update: PASSED")
    
    if success:
        print("\nAll comprehensive tests PASSED!")
    else:
        print("\nSome tests FAILED!")
    
    return success


if __name__ == "__main__":
    test_multiple_models()