# -*- coding: utf-8 -*-
"""
Test script for nested field CRUD operations (Create, Update, Delete)
Tests the new behavior where:
- Items with ID are updated
- Items without ID are created
- Old items not present in the new data are deleted
"""

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from django_graphql_auto.schema import schema
from graphql import graphql_sync

def test_nested_crud_operations():
    """Test create, update, and delete operations for nested fields"""
    
    print("Starting nested CRUD test...")
    
    # Clean up any existing test data
    Comment.objects.filter(content__contains="Test comment").delete()
    Post.objects.filter(title__contains="Test Post").delete()
    User.objects.filter(username__startswith="testuser").delete()
    Category.objects.filter(name__contains="Test Category").delete()
    
    # Create test user and category
    user = User.objects.create_user(username='testuser_crud', email='test@example.com')
    category = Category.objects.create(name='Test Category CRUD')
    
    # Create initial post with comments
    post = Post.objects.create(
        title='Test Post CRUD',
        content='Initial content',
        author=user,
        category=category
    )
    
    # Create initial comments
    comment1 = Comment.objects.create(
        content='Test comment 1 - original',
        author=user,
        post=post
    )
    comment2 = Comment.objects.create(
        content='Test comment 2 - original',
        author=user,
        post=post
    )
    comment3 = Comment.objects.create(
        content='Test comment 3 - to be deleted',
        author=user,
        post=post
    )
    
    print(f"Created post with ID: {post.id}")
    print(f"Created comments with IDs: {comment1.id}, {comment2.id}, {comment3.id}")
    
    # Test mutation: Update post with nested comments
    # - Update comment1 (has ID)
    # - Update comment2 (has ID) 
    # - Create new comment4 (no ID)
    # - Delete comment3 (not included in the update)
    mutation = f"""
    mutation {{
        updatePost(id: {post.id}, input: {{
            title: "Updated Test Post CRUD",
            nested_comments: [
                {{
                    id: {comment1.id},
                    content: "Test comment 1 - UPDATED"
                }},
                {{
                    id: {comment2.id},
                    content: "Test comment 2 - UPDATED"
                }},
                {{
                    content: "Test comment 4 - NEW COMMENT",
                    author: {user.id}
                }}
            ]
        }}) {{
            post {{
                id
                title
                comments {{
                    id
                    content
                }}
            }}
            errors
        }}
    }}
    """
    
    print("Executing mutation...")
    result = graphql_sync(schema, mutation)
    
    if result.errors:
        print("ERROR - Mutation failed:")
        for error in result.errors:
            print(f"  {error}")
        return False
    
    # Check results
    data = result.data['updatePost']
    if data['errors']:
        print("ERROR - Update failed:")
        for error in data['errors']:
            print(f"  {error}")
        return False
    
    print("SUCCESS - Mutation executed successfully")
    
    # Verify the results
    updated_post = Post.objects.get(id=post.id)
    updated_comments = list(Comment.objects.filter(post=updated_post).order_by('id'))
    
    print(f"Updated post title: {updated_post.title}")
    print(f"Number of comments after update: {len(updated_comments)}")
    
    # Verify specific changes
    success = True
    
    # Check that comment3 was deleted
    if Comment.objects.filter(id=comment3.id).exists():
        print("ERROR - Comment 3 should have been deleted but still exists")
        success = False
    else:
        print("SUCCESS - Comment 3 was deleted as expected")
    
    # Check that comment1 and comment2 were updated
    try:
        updated_comment1 = Comment.objects.get(id=comment1.id)
        if updated_comment1.content == "Test comment 1 - UPDATED":
            print("SUCCESS - Comment 1 was updated correctly")
        else:
            print(f"ERROR - Comment 1 content is '{updated_comment1.content}', expected 'Test comment 1 - UPDATED'")
            success = False
    except Comment.DoesNotExist:
        print("ERROR - Comment 1 was deleted but should have been updated")
        success = False
    
    try:
        updated_comment2 = Comment.objects.get(id=comment2.id)
        if updated_comment2.content == "Test comment 2 - UPDATED":
            print("SUCCESS - Comment 2 was updated correctly")
        else:
            print(f"ERROR - Comment 2 content is '{updated_comment2.content}', expected 'Test comment 2 - UPDATED'")
            success = False
    except Comment.DoesNotExist:
        print("ERROR - Comment 2 was deleted but should have been updated")
        success = False
    
    # Check that a new comment was created
    new_comments = Comment.objects.filter(content="Test comment 4 - NEW COMMENT")
    if new_comments.exists():
        print("SUCCESS - New comment was created")
    else:
        print("ERROR - New comment was not created")
        success = False
    
    # Final verification: should have exactly 3 comments (2 updated + 1 new)
    final_comment_count = Comment.objects.filter(post=updated_post).count()
    if final_comment_count == 3:
        print("SUCCESS - Final comment count is correct (3)")
    else:
        print(f"ERROR - Expected 3 comments, but found {final_comment_count}")
        success = False
    
    return success

if __name__ == "__main__":
    try:
        success = test_nested_crud_operations()
        if success:
            print("\nALL TESTS PASSED - Nested CRUD operations work correctly!")
        else:
            print("\nSOME TESTS FAILED - Please check the errors above")
    except Exception as e:
        print(f"EXCEPTION occurred during testing: {e}")
        import traceback
        traceback.print_exc()