# -*- coding: utf-8 -*-
"""
Debug script to see what parameters are passed to model.objects.create
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_graphql_auto.settings')
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from django_graphql_auto.generators.nested_operations import NestedOperationHandler

# Monkey patch to add debug logging to the create call
original_handle_nested_create = NestedOperationHandler.handle_nested_create

def debug_handle_nested_create(self, model, input_data, parent_instance=None):
    print(f"=== handle_nested_create called ===")
    print(f"Model: {model}")
    print(f"Input data: {input_data}")
    
    # Let's manually trace through the logic
    regular_fields = {}
    nested_fields = {}
    m2m_fields = {}
    reverse_fields = {}

    # Get reverse relationships for this model
    reverse_relations = self._get_reverse_relations(model)

    for field_name, value in input_data.items():
        if not hasattr(model, field_name):
            continue
        
        # Check if this is a reverse relationship field
        if field_name in reverse_relations:
            reverse_fields[field_name] = (reverse_relations[field_name], value)
            continue
            
        try:
            field = model._meta.get_field(field_name)
        except:
            # Handle properties and methods
            regular_fields[field_name] = value
            continue

        if isinstance(field, django.db.models.ForeignKey):
            nested_fields[field_name] = (field, value)
        elif isinstance(field, django.db.models.OneToOneField):
            nested_fields[field_name] = (field, value)
        elif isinstance(field, django.db.models.ManyToManyField):
            m2m_fields[field_name] = (field, value)
        else:
            regular_fields[field_name] = value

    print(f"Regular fields: {regular_fields}")
    print(f"Nested fields: {nested_fields}")
    print(f"M2M fields: {m2m_fields}")
    print(f"Reverse fields: {reverse_fields}")

    # Handle foreign key relationships first
    for field_name, (field, value) in nested_fields.items():
        print(f"Processing nested field: {field_name} = {value} (type: {type(value)})")
        if value is None:
            continue
            
        if isinstance(value, dict):
            print(f"  Dict value - checking for 'id'")
            # Nested create
            if 'id' in value:
                print(f"  Update existing object with id {value['id']}")
                # Update existing object
                related_instance = field.related_model.objects.get(pk=value['id'])
                regular_fields[field_name] = self.handle_nested_update(
                    field.related_model, 
                    value, 
                    related_instance
                )
            else:
                print(f"  Create new object")
                # Create new object
                regular_fields[field_name] = self.handle_nested_create(
                    field.related_model, 
                    value
                )
        elif isinstance(value, (str, int)):
            print(f"  String/int value - getting existing object")
            # Reference to existing object - convert ID to model instance
            try:
                related_instance = field.related_model.objects.get(pk=value)
                regular_fields[field_name] = related_instance
                print(f"  Found related instance: {related_instance}")
            except field.related_model.DoesNotExist:
                print(f"  ERROR: Related instance not found")
                raise django.core.exceptions.ValidationError(
                    f"{field.related_model.__name__} with id '{value}' does not exist"
                )
        elif hasattr(value, 'pk'):
            print(f"  Model instance - using directly")
            regular_fields[field_name] = value

    print(f"Final regular_fields before create: {regular_fields}")
    print(f"Field types: {[(k, type(v)) for k, v in regular_fields.items()]}")
    
    # Create the main instance
    try:
        print(f"Calling {model}.objects.create(**{regular_fields})")
        instance = model.objects.create(**regular_fields)
        print(f"Successfully created: {instance}")
        return instance
    except Exception as e:
        print(f"ERROR in create: {e}")
        raise

NestedOperationHandler.handle_nested_create = debug_handle_nested_create

from django_graphql_auto.schema import schema

def test_debug():
    print("=== DEBUGGING CREATE CALL ===")
    
    # Clean up
    Comment.objects.filter(content__contains="c2xx").delete()
    Post.objects.filter(title__contains="xxx").delete()
    User.objects.filter(username="test_create_user").delete()
    Category.objects.filter(name="Test Create Category").delete()
    
    # Create test data
    user = User.objects.create_user(username='test_create_user', email='test_create@test.com')
    category = Category.objects.create(name='Test Create Category')
    post = Post.objects.create(title='Test Create Post', content='Test content', category=category)
    
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