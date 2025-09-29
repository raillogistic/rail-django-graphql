# -*- coding: utf-8 -*-
"""
Quick test to verify the NOT NULL constraint fix
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from django_graphql_auto.schema import schema

def main():
    print("=== QUICK FIX VERIFICATION ===")
    
    # Clean up
    Comment.objects.filter(content__contains="quick_test").delete()
    Post.objects.filter(title__contains="Quick Test").delete()
    User.objects.filter(username="quick_test_user").delete()
    Category.objects.filter(name="Quick Test Category").delete()
    
    # Create test data
    user = User.objects.create_user(username='quick_test_user', email='quick_test@test.com')
    category = Category.objects.create(name='Quick Test Category')
    post = Post.objects.create(title='Quick Test Post', content='Test content', category=category)
    
    print(f"Created user: {user.username} (ID: {user.id})")
    print(f"Created post: {post.title} (ID: {post.id})")
    
    # Test the fix - create nested comment
    mutation = f'''
    mutation {{
        update_post(id:"{post.id}",input:{{ 
            nested_comments:[ 
                {{content:"quick_test_comment",author:"{user.id}"}}, 
            ], 
            title:"Quick Test Updated", 
        }}){{ 
            ok 
            errors 
            object {{
                title
                comments {{
                    pk
                    content
                    author {{
                        username
                    }}
                }}
            }}
        }} 
    }}
    '''
    
    print("Executing GraphQL mutation...")
    result = schema.execute(mutation)
    
    if result.errors:
        print(f"GraphQL errors: {result.errors}")
        return False
    
    data = result.data['update_post']
    
    if data['ok']:
        print("✓ SUCCESS: Nested comment created successfully!")
        print(f"Post title: {data['object']['title']}")
        if data['object']['comments']:
            comment = data['object']['comments'][0]
            print(f"Comment: {comment['content']} by {comment['author']['username']}")
        else:
            print("No comments found in response")
        return True
    else:
        print(f"✗ FAILED: {data['errors']}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 FIX VERIFICATION PASSED!")
    else:
        print("\n❌ FIX VERIFICATION FAILED!")