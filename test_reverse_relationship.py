"""
Test for reverse relationship handling in nested operations.
This test verifies that creating a post with comments using IDs works correctly.
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth.models import User

from test_app.models import Post, Comment, Category
from django_graphql_auto.generators.nested_operations import NestedOperationHandler


class TestReverseRelationshipHandler(TestCase):
    def setUp(self):
        """Set up test data."""
        # Generate unique identifiers for this test run
        unique_id = str(uuid.uuid4())[:8]
        
        # Create test user
        self.user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name=f'Test Category {unique_id}',
            slug=f'test-category-{unique_id}'
        )
        
        # Create a temporary post for the test comments
        self.temp_post = Post.objects.create(
            title=f'Temp Post {unique_id}',
            content='Temporary post content',
            author=self.user,
            category=self.category,
            slug=f'temp-post-{unique_id}'
        )
        
        # Create test comments (with temporary post)
        self.comment1 = Comment.objects.create(
            content='First test comment',
            author=self.user,
            post=self.temp_post
        )
        
        self.comment2 = Comment.objects.create(
            content='Second test comment',
            author=self.user,
            post=self.temp_post
        )
        
        # Initialize the nested operations handler
        self.handler = NestedOperationHandler()
    
    def tearDown(self):
        """Clean up test data."""
        # Clean up all test data to ensure isolation between tests
        Comment.objects.all().delete()
        Post.objects.all().delete()
        Category.objects.all().delete()
        User.objects.all().delete()

    def test_create_post_with_existing_comments(self):
        """Test creating a post with existing comments using their IDs."""
        # Test data with comments as list of IDs
        post_data = {
            'title': 'Test Post with Comments',
            'content': 'This is a test post content',
            'author': self.user.id,
            'category': self.category.id,
            'comments': [str(self.comment1.id), str(self.comment2.id)]
        }
        
        # Create the post using nested operations
        post = self.handler.handle_nested_create(Post, post_data)
        
        # Verify the post was created
        self.assertIsNotNone(post)
        self.assertEqual(post.title, 'Test Post with Comments')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.category, self.category)
        
        # Verify the comments are associated with the post
        post_comments = post.comments.all()
        self.assertEqual(post_comments.count(), 2)
        self.assertIn(self.comment1, post_comments)
        self.assertIn(self.comment2, post_comments)
        
        # Verify the comments' post field is set correctly
        self.comment1.refresh_from_db()
        self.comment2.refresh_from_db()
        self.assertEqual(self.comment1.post, post)
        self.assertEqual(self.comment2.post, post)

    def test_create_post_with_new_comments(self):
        """Test creating a post with new comments using nested creation."""
        # Test data with comments as list of dictionaries
        post_data = {
            'title': 'Test Post with New Comments',
            'content': 'This is another test post content',
            'author': self.user.id,
            'category': self.category.id,
            'comments': [
                {
                    'content': 'New comment 1',
                    'author': self.user.id
                },
                {
                    'content': 'New comment 2',
                    'author': self.user.id
                }
            ]
        }
        
        # Create the post using nested operations
        post = self.handler.handle_nested_create(Post, post_data)
        
        # Verify the post was created
        self.assertIsNotNone(post)
        self.assertEqual(post.title, 'Test Post with New Comments')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.category, self.category)
        
        # Verify the new comments were created and associated with the post
        post_comments = post.comments.all()
        self.assertEqual(post_comments.count(), 2)
        
        # Check comment contents
        comment_contents = [comment.content for comment in post_comments]
        self.assertIn('New comment 1', comment_contents)
        self.assertIn('New comment 2', comment_contents)
        
        # Verify all comments belong to the post
        for comment in post_comments:
            self.assertEqual(comment.post, post)
            self.assertEqual(comment.author, self.user)

    def test_create_post_with_mixed_comments(self):
        """Test creating a post with both existing and new comments."""
        # Test data with mixed comments
        post_data = {
            'title': 'Test Post with Mixed Comments',
            'content': 'This is a test post with mixed comments',
            'author': self.user.id,
            'category': self.category.id,
            'comments': [
                str(self.comment1.id),  # Existing comment
                {
                    'content': 'Brand new comment',
                    'author': self.user.id
                }  # New comment
            ]
        }
        
        # Create the post using nested operations
        post = self.handler.handle_nested_create(Post, post_data)
        
        # Verify the post was created
        self.assertIsNotNone(post)
        self.assertEqual(post.title, 'Test Post with Mixed Comments')
        
        # Verify we have 2 comments total
        post_comments = post.comments.all()
        self.assertEqual(post_comments.count(), 2)
        
        # Verify the existing comment is associated
        self.comment1.refresh_from_db()
        self.assertEqual(self.comment1.post, post)
        
        # Verify the new comment was created
        new_comment = post_comments.exclude(id=self.comment1.id).first()
        self.assertIsNotNone(new_comment)
        self.assertEqual(new_comment.content, 'Brand new comment')
        self.assertEqual(new_comment.post, post)


if __name__ == '__main__':
    import unittest
    unittest.main()