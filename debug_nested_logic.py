# -*- coding: utf-8 -*-
"""
Debug script to trace nested update logic step by step
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from django_graphql_auto.generators.nested_operations import NestedOperationHandler

# Create a custom handler to trace the logic
class DebugNestedOperationHandler(NestedOperationHandler):
    
    def handle_nested_update(self, model, input_data, instance):
        print(f"\n=== DEBUG handle_nested_update ===")
        print(f"Model: {model}")
        print(f"Instance: {instance}")
        print(f"Input data: {input_data}")
        
        updated_object_ids = []
        
        for field_name, value in input_data.items():
            print(f"\nProcessing field: {field_name} = {value}")
            
            if field_name.startswith('nested_'):
                related_field_name = field_name.replace('nested_', '')
                print(f"Related field name: {related_field_name}")
                
                try:
                    related_field = model._meta.get_field(related_field_name)
                    print(f"Related field: {related_field}")
                    
                    if hasattr(related_field, 'related_model'):
                        print(f"Related model: {related_field.related_model}")
                        
                        if isinstance(value, list):
                            print(f"Processing list with {len(value)} items")
                            
                            for i, item in enumerate(value):
                                print(f"\n  Item {i}: {item} (type: {type(item)})")
                                
                                if isinstance(item, dict):
                                    if 'id' in item:
                                        print(f"    Updating existing object with id: {item['id']}")
                                    else:
                                        print(f"    Creating new object")
                                        
                                        # Add the foreign key reference
                                        item[related_field.field.name] = instance.pk
                                        print(f"    Added FK: {related_field.field.name} = {instance.pk}")
                                        
                                        # Process the item data
                                        processed_item = {}
                                        print(f"    Processing item fields:")
                                        
                                        for key, val in item.items():
                                            print(f"      {key}: {val} (type: {type(val)})")
                                            
                                            try:
                                                field = related_field.related_model._meta.get_field(key)
                                                print(f"        Field info: {field}")
                                                
                                                if hasattr(field, 'related_model'):  # ForeignKey
                                                    print(f"        ForeignKey to {field.related_model}")
                                                    
                                                    if val is None:
                                                        processed_item[key] = None
                                                        print(f"        -> None")
                                                    elif isinstance(val, (str, int)):
                                                        print(f"        Converting ID {val} to instance")
                                                        try:
                                                            related_obj = field.related_model.objects.get(pk=val)
                                                            processed_item[key] = related_obj
                                                            print(f"        -> {related_obj}")
                                                        except Exception as e:
                                                            print(f"        ERROR getting object: {e}")
                                                            processed_item[key] = val
                                                    elif hasattr(val, 'pk'):
                                                        processed_item[key] = val
                                                        print(f"        -> {val} (already instance)")
                                                    else:
                                                        processed_item[key] = val
                                                        print(f"        -> {val} (other)")
                                                else:
                                                    processed_item[key] = val
                                                    print(f"        -> {val} (non-FK)")
                                                    
                                            except Exception as e:
                                                print(f"        Exception: {e}")
                                                processed_item[key] = val
                                                print(f"        -> {val} (fallback)")
                                        
                                        print(f"    Final processed_item: {processed_item}")
                                        print(f"    Types: {[(k, type(v)) for k, v in processed_item.items()]}")
                                        
                                        # Call handle_nested_create
                                        print(f"    Calling handle_nested_create...")
                                        try:
                                            new_obj = self.handle_nested_create(related_field.related_model, processed_item)
                                            print(f"    SUCCESS: {new_obj}")
                                            if hasattr(new_obj, 'pk'):
                                                updated_object_ids.append(new_obj.pk)
                                        except Exception as e:
                                            print(f"    ERROR in handle_nested_create: {e}")
                                            raise
                                            
                except Exception as e:
                    print(f"Error processing field {field_name}: {e}")
                    raise
        
        print(f"\nReturning updated_object_ids: {updated_object_ids}")
        return updated_object_ids

# Replace the original handler
original_handler = NestedOperationHandler()
debug_handler = DebugNestedOperationHandler()

# Monkey patch the method
import django_graphql_auto.generators.mutation_generator as mutation_gen
mutation_gen.NestedOperationHandler = DebugNestedOperationHandler

from django_graphql_auto.schema import schema

def test_debug():
    print("=== DEBUGGING NESTED LOGIC ===")
    
    # Clean up
    Comment.objects.filter(content__contains="debug_test").delete()
    Post.objects.filter(title__contains="Debug Test").delete()
    User.objects.filter(username="debug_user").delete()
    Category.objects.filter(name="Debug Category").delete()
    
    # Create test data
    user = User.objects.create_user(username='debug_user', email='debug@test.com')
    category = Category.objects.create(name='Debug Category')
    post = Post.objects.create(title='Debug Test Post', content='Test content', category=category)
    
    print(f"Created post {post.id}, user {user.id}")
    
    # Test the mutation
    mutation = f'''
    mutation {{
        update_post(id:"{post.id}",input:{{ 
            nested_comments:[ 
                {{content:"debug_test",author:"{user.id}"}}, 
            ], 
            title:"Debug Test Updated", 
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
        import traceback
        traceback.print_exc()
    
    print("=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    test_debug()