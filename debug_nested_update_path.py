# -*- coding: utf-8 -*-
"""
Debug script to trace the exact path through nested update logic
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from django_graphql_auto.generators.nested_operations import NestedOperationHandler

# Monkey patch to add debug logging to the nested update
original_handle_nested_update = NestedOperationHandler.handle_nested_update

def debug_handle_nested_update(self, model, input_data, instance):
    print(f"=== handle_nested_update called ===")
    print(f"Model: {model}")
    print(f"Instance: {instance}")
    print(f"Input data: {input_data}")
    
    # Check for nested fields
    for field_name, value in input_data.items():
        if field_name.startswith('nested_'):
            print(f"Found nested field: {field_name} = {value}")
            
            # Get the related field
            related_field_name = field_name.replace('nested_', '')
            try:
                related_field = model._meta.get_field(related_field_name)
                print(f"Related field: {related_field} (type: {type(related_field)})")
                
                if hasattr(related_field, 'related_model'):
                    print(f"Related model: {related_field.related_model}")
                    
                    if isinstance(value, list):
                        print(f"Processing list of {len(value)} items")
                        for i, item in enumerate(value):
                            print(f"  Item {i}: {item} (type: {type(item)})")
                            if isinstance(item, dict):
                                if 'id' in item:
                                    print(f"    Has ID: {item['id']} - will update existing")
                                else:
                                    print(f"    No ID - will create new")
                                    print(f"    Item fields: {list(item.keys())}")
                                    for k, v in item.items():
                                        print(f"      {k}: {v} (type: {type(v)})")
            except Exception as e:
                print(f"Error getting related field: {e}")
    
    try:
        result = original_handle_nested_update(self, model, input_data, instance)
        print(f"Update result: {result}")
        return result
    except Exception as e:
        print(f"ERROR in handle_nested_update: {e}")
        raise

NestedOperationHandler.handle_nested_update = debug_handle_nested_update

from django_graphql_auto.schema import schema

def test_debug():
    print("=== DEBUGGING NESTED UPDATE PATH ===")
    
    # Clean up
    Comment.objects.filter(content__contains="c2xx").delete()
    Post.objects.filter(title__contains="xxx").delete()
    User.objects.filter(username="test_path_user").delete()
    Category.objects.filter(name="Test Path Category").delete()
    
    # Create test data
    user = User.objects.create_user(username='test_path_user', email='test_path@test.com')
    category = Category.objects.create(name='Test Path Category')
    post = Post.objects.create(title='Test Path Post', content='Test content', category=category)
    
    print(f"Created post {post.id}, user {user.id}")
    
    # Test the exact mutation that's failing
    mutation = f'''
    mutation {{
        update_post(id:"{post.id}",input:{{ 
            nested_comments:[ 
                {{content:"c2xx",author:"{user.id}"}}, 
            ], 
            title:"xxx", 
        }}){{ 
            ok 
            errors 
        }} 
    }}
    '''
    
    print("Executing mutation...")
    
    try:
        result = schema.execute(mutation)
        print(f"Result: {result.data}")
        if result.errors:
            print(f"Errors: {result.errors}")
    except Exception as e:
        print(f"Exception: {e}")
    
    print("=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    test_debug()