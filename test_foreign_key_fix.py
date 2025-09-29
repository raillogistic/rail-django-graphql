# -*- coding: utf-8 -*-
"""
Test the foreign key fix for nested updates
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from django_graphql_auto.schema import schema

def run_test():
    print("=== FOREIGN KEY FIX TEST ===")
    
    # Clean up
    Comment.objects.filter(content__contains="FK Test").delete()
    Post.objects.filter(title__contains="FK Test").delete()
    User.objects.filter(username="fk_user").delete()
    Category.objects.filter(name="FK Category").delete()
    
    # Create test data
    user = User.objects.create_user(username='fk_user', email='fk@test.com')
    category = Category.objects.create(name='FK Category')
    post = Post.objects.create(title='FK Test Post', content='Test content', category=category)
    
    # Create initial comment
    comment = Comment.objects.create(content='FK Test Comment', author=user, post=post)
    
    print(f"Created post {post.id} with comment {comment.id}")
    print(f"User ID: {user.id}")
    
    # Test the exact mutation that was failing
    mutation = f'''
    mutation {{
        update_post(id: {post.id}, input: {{
            nested_comments: [
                {{
                    content: "c2xx",
                    author: "{user.id}",
                    id: "{comment.id}"
                }}
            ],
            title: "xxx"
        }}) {{
            ok
            object {{
                comments {{
                    pk
                    content
                    author {{
                        pk
                    }}
                }}
            }}
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
    
    print("SUCCESS: Mutation executed without errors!")
    
    # Check the updated comment
    updated_comment = Comment.objects.get(id=comment.id)
    print(f"Updated comment content: {updated_comment.content}")
    print(f"Comment author ID: {updated_comment.author.id}")
    
    if updated_comment.content == "c2xx" and updated_comment.author.id == user.id:
        print("SUCCESS: Foreign key field was properly updated!")
    else:
        print("FAIL: Foreign key field was not updated correctly")
    
    print("=== TEST COMPLETE ===")

if __name__ == "__main__":
    run_test()