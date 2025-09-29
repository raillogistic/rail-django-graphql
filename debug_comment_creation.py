# -*- coding: utf-8 -*-
"""
Debug script to directly test Comment creation
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category

def test_direct_comment_creation():
    print("=== TESTING DIRECT COMMENT CREATION ===")
    
    # Clean up
    Comment.objects.filter(content__contains="c2xx").delete()
    Post.objects.filter(title__contains="xxx").delete()
    User.objects.filter(username="test_direct_user").delete()
    Category.objects.filter(name="Test Direct Category").delete()
    
    # Create test data
    user = User.objects.create_user(username='test_direct_user', email='test_direct@test.com')
    category = Category.objects.create(name='Test Direct Category')
    post = Post.objects.create(title='Test Direct Post', content='Test content', category=category)
    
    print(f"Created post {post.id}, user {user.id}")
    
    # Test direct creation with the same data that's failing
    print("Testing direct Comment.objects.create...")
    
    try:
        # This is what should work
        comment_data = {
            'content': 'c2xx',
            'author': user,  # Model instance
            'post': post     # Model instance
        }
        print(f"Creating comment with data: {comment_data}")
        comment = Comment.objects.create(**comment_data)
        print(f"SUCCESS: Created comment {comment.id}")
        
        # Test with string ID (this might fail)
        print("\nTesting with string ID...")
        comment_data_str = {
            'content': 'c2xx_str',
            'author_id': str(user.id),  # String ID
            'post_id': str(post.id)     # String ID
        }
        print(f"Creating comment with data: {comment_data_str}")
        comment2 = Comment.objects.create(**comment_data_str)
        print(f"SUCCESS: Created comment {comment2.id}")
        
        # Test with int ID
        print("\nTesting with int ID...")
        comment_data_int = {
            'content': 'c2xx_int',
            'author_id': user.id,  # Int ID
            'post_id': post.id     # Int ID
        }
        print(f"Creating comment with data: {comment_data_int}")
        comment3 = Comment.objects.create(**comment_data_int)
        print(f"SUCCESS: Created comment {comment3.id}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_direct_comment_creation()