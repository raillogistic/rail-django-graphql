# -*- coding: utf-8 -*-
"""Simple test for nested CRUD operations"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from django_graphql_auto.schema import schema
from graphql import graphql_sync

def run_test():
    print("=== NESTED CRUD TEST ===")
    
    # Clean up
    Comment.objects.filter(content__contains="CRUD Test").delete()
    Post.objects.filter(title__contains="CRUD Test").delete()
    User.objects.filter(username="crud_user").delete()
    Category.objects.filter(name="CRUD Category").delete()
    
    # Create test data
    user = User.objects.create_user(username='crud_user', email='crud@test.com')
    category = Category.objects.create(name='CRUD Category')
    post = Post.objects.create(title='CRUD Test Post', content='Test content', category=category)
    
    # Create initial comments
    c1 = Comment.objects.create(content='CRUD Test Comment 1', author=user, post=post)
    c2 = Comment.objects.create(content='CRUD Test Comment 2', author=user, post=post)
    c3 = Comment.objects.create(content='CRUD Test Comment 3 - DELETE ME', author=user, post=post)
    
    print(f"Created post {post.id} with comments {c1.id}, {c2.id}, {c3.id}")
    
    # Test mutation using the schema's execute method
    mutation = f'''
    mutation {{
        update_post(id: {post.id}, input: {{
            title: "CRUD Test Post - UPDATED",
            nested_comments: [
                {{ id: {c1.id}, content: "CRUD Test Comment 1 - UPDATED" }},
                {{ id: {c2.id}, content: "CRUD Test Comment 2 - UPDATED" }},
                {{ content: "CRUD Test Comment 4 - NEW", author: {user.id} }}
            ]
        }}) {{
            ok
            object {{ id title }}
            errors
        }}
    }}
    '''
    
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
    
    if result.data['update_post']['errors']:
        print("UPDATE ERRORS:")
        for error in result.data['update_post']['errors']:
            print(f"  {error}")
        return
    
    # Check results
    remaining_comments = Comment.objects.filter(post=post)
    print(f"Comments after update: {remaining_comments.count()}")
    
    # Verify c3 was deleted
    if not Comment.objects.filter(id=c3.id).exists():
        print("SUCCESS: Comment 3 was deleted")
    else:
        print("FAIL: Comment 3 still exists")
    
    # Verify c1 and c2 were updated
    c1_updated = Comment.objects.get(id=c1.id)
    if "UPDATED" in c1_updated.content:
        print("SUCCESS: Comment 1 was updated")
    else:
        print("FAIL: Comment 1 was not updated")
    
    # Verify new comment was created
    new_comment = Comment.objects.filter(content__contains="NEW").first()
    if new_comment:
        print("SUCCESS: New comment was created")
    else:
        print("FAIL: New comment was not created")
    
    print("=== TEST COMPLETE ===")

if __name__ == "__main__":
    run_test()