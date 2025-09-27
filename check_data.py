#!/usr/bin/env python3
"""
Check what data exists in the database.
"""

import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from tests.fixtures.test_data_fixtures import TestAuthor, TestBook, TestCategory, TestReview, TestPublisher
from django.contrib.auth.models import User

def check_database_data():
    """Check what data exists in the database."""
    
    print("=== Database Data Check ===\n")
    
    # Check users
    users = User.objects.all()
    print(f"Users ({users.count()}):")
    for user in users:
        print(f"  ID: {user.id}, Username: {user.username}")
    print()
    
    # Check posts
    posts = Post.objects.all()
    print(f"Posts ({posts.count()}):")
    for post in posts:
        print(f"  ID: {post.id}, Title: {post.title}, Author: {post.author.username}")
    print()
    
    # Check comments
    comments = Comment.objects.all()
    print(f"Comments ({comments.count()}):")
    for comment in comments[:10]:  # Show first 10
        print(f"  ID: {comment.id}, Post: {comment.post.id}, Author: {comment.author.username}, Approved: {comment.is_approved}")
    if comments.count() > 10:
        print(f"  ... and {comments.count() - 10} more")
    print()

if __name__ == '__main__':
    check_database_data()
