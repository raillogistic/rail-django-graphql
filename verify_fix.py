# -*- coding: utf-8 -*-
"""
Verify the fix for the original failing mutation
"""

import uuid
from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from django_graphql_auto.schema import schema

def test_original_mutation():
    """Test the exact mutation that was failing for the user."""
    
    print("Testing original failing mutation...")
    
    # Create test data
    user = User.objects.create_user(
        username=f'testuser_{uuid.uuid4().hex[:8]}', 
        email='test@example.com'
    )
    category = Category.objects.create(
        name='Test Category', 
        description='Test Description'
    )
    
    # Create a post with ID 115 (or close to it)
    post = Post.objects.create(
        title='Original Post', 
        content='Original Content', 
        category=category, 
        is_published=True
    )
    
    print(f"Created post with ID: {post.id}")
    
    # Test the exact mutation that was failing
    mutation = f'''
    mutation {{
        updatePost(
            id: "{post.id}"
            input: {{
                nested_comments: [{{content: "dsd"}}]
                title: "xxx"
            }}
        ) {{
            ok
            errors
        }}
    }}
    '''
    
    print("Executing the original failing mutation...")
    result = schema.execute(mutation)
    
    print("=== RESULT ===")
    if result.errors:
        print(f"GraphQL Errors: {result.errors}")
        return False
    
    if result.data and result.data.get('updatePost'):
        update_result = result.data['updatePost']
        print(f"Success: {update_result.get('ok')}")
        print(f"Errors: {update_result.get('errors')}")
        
        if update_result.get('ok') and not update_result.get('errors'):
            print("SUCCESS: The original failing mutation now works!")
            return True
        else:
            print("FAILED: The mutation still has errors")
            return False
    
    print("FAILED: No data returned")
    return False

if __name__ == "__main__":
    success = test_original_mutation()
    print(f"\nFinal result: {'PASSED' if success else 'FAILED'}")