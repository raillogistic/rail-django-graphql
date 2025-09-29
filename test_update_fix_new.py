"""
Test script to verify that nested update functionality works correctly
after fixing the reverse relationship handling.
"""

import uuid
from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from django_graphql_auto.schema import schema


def test_nested_update_fix():
    """Test that nested updates work correctly with the fixed reverse relationship handling."""
    
    print("=== TESTING NESTED UPDATE FIX ===")
    
    # Create test data
    unique_username = f"testuser_{uuid.uuid4().hex[:8]}"
    user = User.objects.create_user(username=unique_username, email="test@example.com")
    
    category = Category.objects.create(name="Test Category", description="Test Description")
    
    # Create a post with comments
    post = Post.objects.create(
        title="Test Post",
        content="Test Content",
        category=category,
        is_published=True
    )
    
    # Create some comments
    comment1 = Comment.objects.create(
        content="First comment",
        author=user,
        post=post
    )
    
    comment2 = Comment.objects.create(
        content="Second comment", 
        author=user,
        post=post
    )
    
    print(f"Created post with ID: {post.id}")
    print(f"Created comments with IDs: {comment1.id}, {comment2.id}")
    
    # Test 1: Update post with new nested comments (should create new comments)
    print("\n1. Testing creation of new nested comments during update...")
    
    mutation1 = f'''
    mutation {{
        updatePost(
            id: "{post.id}"
            input: {{
                title: "Updated Post Title"
                nested_comments: [
                    {{
                        content: "Brand new comment"
                        author: "{user.id}"
                    }}
                ]
            }}
        ) {{
            ok
            object {{
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
    '''
    
    result1 = schema.execute(mutation1)
    
    if result1.errors:
        print(f"GraphQL Errors: {result1.errors}")
    else:
        print("Mutation executed successfully!")
        if result1.data and result1.data.get('updatePost'):
            update_result = result1.data['updatePost']
            print(f"Success: {update_result.get('ok')}")
            print(f"Errors: {update_result.get('errors')}")
            
            if update_result.get('object'):
                post_data = update_result['object']
                print(f"Updated post title: {post_data.get('title')}")
                print(f"Comments: {post_data.get('comments')}")
    
    # Test 2: Update post with existing comment updates
    print("\n2. Testing update of existing nested comments...")
    
    mutation2 = f'''
    mutation {{
        updatePost(
            id: "{post.id}"
            input: {{
                title: "Post with Updated Comments"
                nested_comments: [
                    {{
                        id: "{comment1.id}"
                        content: "Updated first comment"
                    }}
                ]
            }}
        ) {{
            ok
            object {{
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
    '''
    
    result2 = schema.execute(mutation2)
    
    if result2.errors:
        print(f"GraphQL Errors: {result2.errors}")
    else:
        print("Mutation executed successfully!")
        if result2.data and result2.data.get('updatePost'):
            update_result = result2.data['updatePost']
            print(f"Success: {update_result.get('ok')}")
            print(f"Errors: {update_result.get('errors')}")
            
            if update_result.get('object'):
                post_data = update_result['object']
                print(f"Updated post title: {post_data.get('title')}")
                print(f"Comments: {post_data.get('comments')}")
    
    print("\n=== TEST COMPLETED ===")


if __name__ == "__main__":
    test_nested_update_fix()