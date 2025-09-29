# -*- coding: utf-8 -*-
"""
Simple test to verify nested update fix
"""

import uuid
from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from django_graphql_auto.schema import schema

def main():
    print("=== Testing Nested Update Fix ===")
    
    # Create test data
    user = User.objects.create_user(
        username=f'testuser_{uuid.uuid4().hex[:8]}', 
        email='test@example.com'
    )
    category = Category.objects.create(
        name='Test Category', 
        description='Test Description'
    )
    post = Post.objects.create(
        title='Test Post', 
        content='Test Content', 
        category=category, 
        is_published=True
    )
    
    print(f"Created post with ID: {post.id}")
    
    # Test the mutation that was failing
    mutation = f'''
    mutation {{
        updatePost(
            id: "{post.id}"
            input: {{
                title: "Updated Title"
                nested_comments: [{{
                    content: "New nested comment"
                    author: "{user.id}"
                }}]
            }}
        ) {{
            ok
            errors
            object {{
                id
                title
                comments {{
                    id
                    content
                    author {{
                        username
                    }}
                }}
            }}
        }}
    }}
    '''
    
    print("Executing mutation...")
    result = schema.execute(mutation)
    
    if result.errors:
        print(f"ERROR: GraphQL Errors: {result.errors}")
        return False
    
    if result.data and result.data.get('updatePost'):
        update_result = result.data['updatePost']
        
        if update_result.get('ok'):
            print("SUCCESS: Mutation executed successfully!")
            
            if update_result.get('errors'):
                print(f"WARNING: Mutation errors: {update_result['errors']}")
                return False
            
            obj = update_result.get('object')
            if obj:
                print(f"Updated post title: {obj.get('title')}")
                comments = obj.get('comments', [])
                print(f"Comments count: {len(comments)}")
                
                for comment in comments:
                    print(f"   - Comment {comment.get('id')}: {comment.get('content')}")
                    author = comment.get('author')
                    if author:
                        print(f"     Author: {author.get('username')}")
                
                return True
        else:
            print(f"ERROR: Mutation failed: {update_result.get('errors')}")
            return False
    
    print("ERROR: No data returned from mutation")
    return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\nSUCCESS: Test PASSED - Nested update fix is working!")
    else:
        print("\nFAILED: Test FAILED - Nested update fix needs more work")