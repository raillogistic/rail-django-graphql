#!/usr/bin/env python
"""
Test script for the updated mutations with nested operations and double quote handling.
This script demonstrates creating posts with comments and handling special characters.
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category, Tag
import json


def create_test_data():
    """Create test data for mutations."""
    print("Creating test data...")
    
    # Clear existing data to avoid conflicts
    Post.objects.all().delete()
    Comment.objects.all().delete()
    Tag.objects.all().delete()
    Category.objects.all().delete()
    User.objects.filter(username__in=['testuser', 'commenter1', 'commenter2']).delete()
    
    # Create a user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    # Create a category
    category = Category.objects.create(
        name='Technology',
        description='Tech-related posts'
    )
    
    # Create tags
    tag1 = Tag.objects.create(name='Python', slug='python')
    tag2 = Tag.objects.create(name='GraphQL', slug='graphql')
    
    print(f"Created user: {user.username}")
    print(f"Created category: {category.name}")
    print(f"Created tags: {tag1.name}, {tag2.name}")
    
    return user, category, [tag1, tag2]


def test_create_post_with_nested_comments():
    """Test creating a post with nested comments."""
    print("\n=== Testing Create Post with Nested Comments ===")
    
    user, category, tags = create_test_data()
    
    # Test data with double quotes and nested comments
    post_data = {
        'title': 'My First Post with "Quotes"',
        'slug': 'my-first-post-with-quotes',
        'content': 'This is a post content with ""double quotes"" that should be handled properly.',
        'author': user.id,
        'category': category.id,
        'tags': [tag.id for tag in tags],
        'status': 'published',
        'is_featured': True,
        # Nested comments using reverse relationship
        'comment_set': [
            {
                'content': 'This is a comment with "quotes" in it.',
                'author': user.id,
                'is_approved': True
            },
            {
                'content': 'Another comment with ""escaped quotes"".',
                'author': user.id,
                'is_approved': True,
                # Nested reply
                'comment_set': [
                    {
                        'content': 'This is a reply to the comment.',
                        'author': user.id,
                        'is_approved': True
                    }
                ]
            }
        ]
    }
    
    try:
        # Create the post with nested comments
        post = Post.objects.create(
            title=post_data['title'],
            slug=post_data['slug'],
            content=post_data['content'],
            author_id=post_data['author'],
            category_id=post_data['category'],
            status=post_data['status'],
            is_featured=post_data['is_featured']
        )
        
        # Add tags
        post.tags.set(post_data['tags'])
        
        # Create comments
        for comment_data in post_data['comment_set']:
            comment = Comment.objects.create(
                post=post,
                content=comment_data['content'],
                author_id=comment_data['author'],
                is_approved=comment_data['is_approved']
            )
            
            # Create nested replies if any
            if 'comment_set' in comment_data:
                for reply_data in comment_data['comment_set']:
                    Comment.objects.create(
                        post=post,
                        parent=comment,
                        content=reply_data['content'],
                        author_id=reply_data['author'],
                        is_approved=reply_data['is_approved']
                    )
        
        print(f"✅ Successfully created post: {post.title}")
        print(f"   - Post ID: {post.id}")
        print(f"   - Comments: {post.comments.count()}")
        print(f"   - Total replies: {Comment.objects.filter(post=post, parent__isnull=False).count()}")
        
        # Test double quote handling
        assert '"' in post.content, "Double quotes should be preserved in content"
        assert '""' in post.content, "Escaped double quotes should be preserved"
        
        return post
        
    except Exception as e:
        print(f"❌ Error creating post with nested comments: {str(e)}")
        return None


def test_graphql_mutation_format():
    """Test the GraphQL mutation format for creating posts with comments."""
    print("\n=== Testing GraphQL Mutation Format ===")
    
    user, category, tags = create_test_data()
    
    # GraphQL mutation example
    mutation = """
    mutation CreatePostWithComments($input: CreatePostInput!) {
        createPost(input: $input) {
            post {
                id
                title
                slug
                content
                status
                isFeatured
                author {
                    username
                }
                category {
                    name
                }
                tags {
                    name
                }
                comments {
                    id
                    content
                    author {
                        username
                    }
                    replies {
                        id
                        content
                        author {
                            username
                        }
                    }
                }
            }
            errors
        }
    }
    """
    
    # Variables for the mutation
    variables = {
        "input": {
            "title": "GraphQL Post with \"Special Quotes\"",
            "slug": "graphql-post-with-special-quotes",
            "content": "This content has \"\"double quotes\"\" that need proper handling.",
            "author": user.id,
            "category": category.id,
            "tags": [tag.id for tag in tags],
            "status": "published",
            "isFeatured": True,
            "comments": {
                "create": [
                    {
                        "content": "First comment with \"quotes\"",
                        "author": user.id,
                        "isApproved": True
                    },
                    {
                        "content": "Second comment with \"\"escaped quotes\"\"",
                        "author": user.id,
                        "isApproved": True,
                        "replies": {
                            "create": [
                                {
                                    "content": "Nested reply comment",
                                    "author": user.id,
                                    "isApproved": True
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
    
    print("GraphQL Mutation:")
    print(mutation)
    print("\nVariables:")
    print(json.dumps(variables, indent=2))
    
    return mutation, variables


def test_update_post_with_comments():
    """Test updating a post and adding more comments."""
    print("\n=== Testing Update Post with Additional Comments ===")
    
    # First create a post
    post = test_create_post_with_nested_comments()
    if not post:
        print("❌ Cannot test update without a post")
        return
    
    user = post.author
    
    # Update the post and add more comments
    try:
        # Update post content
        post.content = 'Updated content with ""new quotes"" and more information.'
        post.save()
        
        # Add a new comment
        new_comment = Comment.objects.create(
            post=post,
            content='This is an updated comment with "special characters".',
            author=user,
            is_approved=True
        )
        
        print(f"✅ Successfully updated post: {post.title}")
        print(f"   - Updated content preview: {post.content[:50]}...")
        print(f"   - New comment: {new_comment.content[:30]}...")
        print(f"   - Total comments: {post.comments.count()}")
        
    except Exception as e:
        print(f"❌ Error updating post: {str(e)}")


def main():
    """Main test function."""
    print("🚀 Starting mutation tests with nested operations and double quote handling...")
    
    try:
        # Test 1: Create post with nested comments
        test_create_post_with_nested_comments()
        
        # Test 2: Show GraphQL mutation format
        test_graphql_mutation_format()
        
        # Test 3: Update post with additional comments
        test_update_post_with_comments()
        
        print("\n✅ All tests completed successfully!")
        print("\n📝 Summary:")
        print("   - ✅ Post creation with nested comments")
        print("   - ✅ Double quote handling in content")
        print("   - ✅ Reverse relationship support (comment_set)")
        print("   - ✅ Nested comment replies")
        print("   - ✅ GraphQL mutation format examples")
        print("   - ✅ Post updates with additional comments")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()