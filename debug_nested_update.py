# -*- coding: utf-8 -*-
"""
Debug the nested update behavior
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from django_graphql_auto.schema import schema

def run_debug():
    print("=== DEBUG NESTED UPDATE ===")
    
    # Clean up
    Comment.objects.filter(content__contains="Debug").delete()
    Post.objects.filter(title__contains="Debug").delete()
    User.objects.filter(username="debug_user").delete()
    Category.objects.filter(name="Debug Category").delete()
    
    # Create test data
    user = User.objects.create_user(username='debug_user', email='debug@test.com')
    category = Category.objects.create(name='Debug Category')
    post = Post.objects.create(title='Debug Test Post', content='Test content', category=category)
    
    # Create initial comments
    comment1 = Comment.objects.create(content='Debug Comment 1', author=user, post=post)
    comment2 = Comment.objects.create(content='Debug Comment 2', author=user, post=post)
    
    print(f"Created post {post.id}")
    print(f"Created comments: {comment1.id}, {comment2.id}")
    print(f"User ID: {user.id}")
    
    # Check initial state
    initial_comments = list(Comment.objects.filter(post=post).values('id', 'content', 'author_id'))
    print(f"Initial comments: {initial_comments}")
    
    # Test mutation - update one comment, keep the other
    mutation = f'''
    mutation {{
        update_post(id: {post.id}, input: {{
            nested_comments: [
                {{
                    content: "Updated Debug Comment 1",
                    author: "{user.id}",
                    id: "{comment1.id}"
                }},
                {{
                    content: "Debug Comment 2",
                    author: "{user.id}",
                    id: "{comment2.id}"
                }}
            ],
            title: "Updated Debug Post"
        }}) {{
            ok
            object {{
                id
                title
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
    print(f"Result data: {result.data}")
    
    # Check final state
    final_comments = list(Comment.objects.filter(post=post).values('id', 'content', 'author_id'))
    print(f"Final comments: {final_comments}")
    
    all_comments = list(Comment.objects.all().values('id', 'content', 'author_id', 'post_id'))
    print(f"All comments in DB: {all_comments}")
    
    print("=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    run_debug()