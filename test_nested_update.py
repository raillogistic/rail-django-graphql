"""
Test script to verify that nested update functionality works correctly
after adding reverse relationship fields to update input types.
"""

import uuid
from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from django_graphql_auto.schema import schema


def test_nested_update_functionality():
    """Test that nested updates work correctly with the new input type structure."""
    
    print("=== TESTING NESTED UPDATE FUNCTIONALITY ===")
    
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
    
    # Test 1: Update post with nested comment updates
    print("\n1. Testing nested comment updates...")
    
    mutation = f'''
    mutation {{
        updatePost(
            id: "{post.id}"
            input: {{
                title: "Updated Post Title"
                nested_comments: [
                    {{
                        id: "{comment1.id}"
                        content: "Updated first comment"
                    }},
                    {{
                        id: "{comment2.id}"
                        content: "Updated second comment"
                    }}
                ]
            }}
        ) {{
            post {{
                id
                title
                comments {{
                    id
                    content
                }}
            }}
            success
            errors
        }}
    }}
    '''
    
    result = schema.execute(mutation)
    
    if result.errors:
        print(f"GraphQL Errors: {result.errors}")
    else:
        print("Mutation executed successfully!")
        if result.data and result.data.get('updatePost'):
            update_result = result.data['updatePost']
            print(f"Success: {update_result.get('success')}")
            print(f"Errors: {update_result.get('errors')}")
            
            if update_result.get('post'):
                post_data = update_result['post']
                print(f"Updated post title: {post_data.get('title')}")
                print(f"Comments: {post_data.get('comments')}")
    
    # Test 2: Update post with new nested comments
    print("\n2. Testing creation of new nested comments during update...")
    
    mutation2 = f'''
    mutation {{
        updatePost(
            id: "{post.id}"
            input: {{
                title: "Post with New Comments"
                nested_comments: [
                    {{
                        content: "Brand new comment"
                        author: "{user.id}"
                    }}
                ]
            }}
        ) {{
            post {{
                id
                title
                comments {{
                    id
                    content
                }}
            }}
            success
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
            print(f"Success: {update_result.get('success')}")
            print(f"Errors: {update_result.get('errors')}")
            
            if update_result.get('post'):
                post_data = update_result['post']
                print(f"Updated post title: {post_data.get('title')}")
                print(f"Comments: {post_data.get('comments')}")
    
    # Test 3: Verify the input type structure
    print("\n3. Verifying input type structure...")
    
    introspection_query = '''
    {
        __schema {
            mutationType {
                fields {
                    name
                    args {
                        name
                        type {
                            name
                            inputFields {
                                name
                                type {
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    '''
    
    result3 = schema.execute(introspection_query)
    
    if result3.errors:
        print(f"Introspection Errors: {result3.errors}")
    else:
        # Find updatePost mutation
        mutations = result3.data['__schema']['mutationType']['fields']
        update_post_mutation = next((m for m in mutations if m['name'] == 'updatePost'), None)
        
        if update_post_mutation:
            input_arg = next((arg for arg in update_post_mutation['args'] if arg['name'] == 'input'), None)
            if input_arg and input_arg['type']['inputFields']:
                print("UpdatePostInput fields:")
                for field in input_arg['type']['inputFields']:
                    print(f"  - {field['name']}: {field['type']['name']}")
                    
                # Check for nested_comments field
                nested_comments = next((f for f in input_arg['type']['inputFields'] if f['name'] == 'nested_comments'), None)
                if nested_comments:
                    print("✓ nested_comments field found in UpdatePostInput!")
                else:
                    print("✗ nested_comments field NOT found in UpdatePostInput")
    
    print("\n=== NESTED UPDATE FUNCTIONALITY TEST COMPLETE ===")


if __name__ == "__main__":
    test_nested_update_functionality()