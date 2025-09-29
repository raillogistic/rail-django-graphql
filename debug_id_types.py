# -*- coding: utf-8 -*-
"""
Debug ID type handling in nested updates
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category

def debug_id_types():
    print("=== DEBUG ID TYPES ===")
    
    # Clean up
    Comment.objects.filter(content__contains="ID Debug").delete()
    Post.objects.filter(title__contains="ID Debug").delete()
    User.objects.filter(username="id_debug_user").delete()
    Category.objects.filter(name="ID Debug Category").delete()
    
    # Create test data
    user = User.objects.create_user(username='id_debug_user', email='id_debug@test.com')
    category = Category.objects.create(name='ID Debug Category')
    post = Post.objects.create(title='ID Debug Test Post', content='Test content', category=category)
    
    # Create initial comment
    comment = Comment.objects.create(content='ID Debug Comment', author=user, post=post)
    
    print(f"Comment ID: {comment.id} (type: {type(comment.id)})")
    print(f"Comment ID as string: '{comment.id}' (type: {type(str(comment.id))})")
    
    # Test ID comparison
    string_id = str(comment.id)
    int_id = comment.id
    
    print(f"String ID == Int ID: {string_id == int_id}")
    print(f"String ID in [Int ID]: {string_id in [int_id]}")
    print(f"Int ID in [String ID]: {int_id in [string_id]}")
    
    # Test set operations
    updated_ids = set()
    updated_ids.add(string_id)  # This is what happens in the code
    
    print(f"Updated IDs set: {updated_ids}")
    print(f"Comment ID in updated_ids: {comment.id in updated_ids}")
    print(f"String comment ID in updated_ids: {str(comment.id) in updated_ids}")
    
    print("=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    debug_id_types()