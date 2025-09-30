# -*- coding: utf-8 -*-
"""
Debug script to see what processed_item contains before handle_nested_create
"""

import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rail_django_graphql.settings")
django.setup()

from django.contrib.auth.models import User
from test_app.models import Post, Comment, Category
from rail_django_graphql.generators.nested_operations import NestedOperationHandler

# Monkey patch to add debug logging to the nested update where processed_item is created
original_handle_nested_update = NestedOperationHandler.handle_nested_update


def debug_handle_nested_update(self, model, input_data, instance):
    print(f"=== handle_nested_update called ===")
    print(f"Model: {model}")
    print(f"Instance: {instance}")
    print(f"Input data: {input_data}")

    # We need to manually trace through the nested update logic
    for field_name, value in input_data.items():
        if field_name.startswith("nested_"):
            print(f"\nProcessing nested field: {field_name}")
            related_field_name = field_name.replace("nested_", "")

            try:
                related_field = model._meta.get_field(related_field_name)
                print(f"Related field: {related_field}")

                if hasattr(related_field, "related_model"):
                    print(f"Related model: {related_field.related_model}")

                    if isinstance(value, list):
                        print(f"Processing list of {len(value)} items")
                        for i, item in enumerate(value):
                            print(f"\n  Item {i}: {item}")
                            if isinstance(item, dict) and "id" not in item:
                                print(f"    Creating new object with data: {item}")

                                # This is the logic that creates processed_item
                                item[related_field.field.name] = instance.pk
                                print(
                                    f"    Added foreign key: {related_field.field.name} = {instance.pk}"
                                )

                                # Handle foreign key fields in the new object data
                                processed_item = {}
                                for key, val in item.items():
                                    print(
                                        f"    Processing field: {key} = {val} (type: {type(val)})"
                                    )
                                    try:
                                        field = (
                                            related_field.related_model._meta.get_field(
                                                key
                                            )
                                        )
                                        print(
                                            f"      Field info: {field} (type: {type(field)})"
                                        )
                                        if isinstance(
                                            field, django.db.models.ForeignKey
                                        ):
                                            print(f"      Foreign key field detected")
                                            if val is None:
                                                processed_item[key] = None
                                                print(f"        Set to None")
                                            elif isinstance(val, (str, int)):
                                                print(
                                                    f"        Converting ID {val} to model instance"
                                                )
                                                # Convert ID to related object instance
                                                related_obj = (
                                                    field.related_model.objects.get(
                                                        pk=val
                                                    )
                                                )
                                                processed_item[key] = related_obj
                                                print(f"        Set to: {related_obj}")
                                            elif isinstance(val, dict):
                                                print(
                                                    f"        Dict value - nested operation"
                                                )
                                                # Handle nested object creation/update
                                                if "id" in val:
                                                    related_obj = (
                                                        field.related_model.objects.get(
                                                            pk=val["id"]
                                                        )
                                                    )
                                                    updated_related = (
                                                        self.handle_nested_update(
                                                            field.related_model,
                                                            val,
                                                            related_obj,
                                                        )
                                                    )
                                                    processed_item[key] = (
                                                        updated_related
                                                    )
                                                else:
                                                    new_related = (
                                                        self.handle_nested_create(
                                                            field.related_model, val
                                                        )
                                                    )
                                                    processed_item[key] = new_related
                                            elif hasattr(val, "pk"):
                                                print(
                                                    f"        Model instance - using directly"
                                                )
                                                # Already a model instance, use directly
                                                processed_item[key] = val
                                            else:
                                                print(
                                                    f"        Other type - direct assignment"
                                                )
                                                processed_item[key] = val
                                        else:
                                            print(f"      Non-foreign key field")
                                            processed_item[key] = val
                                    except Exception as e:
                                        print(f"      Exception processing field: {e}")
                                        # Fallback to direct assignment for non-model fields
                                        processed_item[key] = val

                                print(f"    Final processed_item: {processed_item}")
                                print(
                                    f"    Processed_item types: {[(k, type(v)) for k, v in processed_item.items()]}"
                                )

                                print(
                                    f"    Calling handle_nested_create with processed_item..."
                                )
                                try:
                                    new_obj = self.handle_nested_create(
                                        related_field.related_model, processed_item
                                    )
                                    print(f"    SUCCESS: Created {new_obj}")
                                except Exception as e:
                                    print(f"    ERROR in handle_nested_create: {e}")
                                    raise
            except Exception as e:
                print(f"Error processing nested field: {e}")

    try:
        result = original_handle_nested_update(self, model, input_data, instance)
        print(f"Update result: {result}")
        return result
    except Exception as e:
        print(f"ERROR in handle_nested_update: {e}")
        raise


NestedOperationHandler.handle_nested_update = debug_handle_nested_update

from rail_django_graphql.schema import schema


def test_debug():
    print("=== DEBUGGING PROCESSED ITEM FINAL ===")

    # Clean up
    Comment.objects.filter(content__contains="c2xx").delete()
    Post.objects.filter(title__contains="xxx").delete()
    User.objects.filter(username="test_final_user").delete()
    Category.objects.filter(name="Test Final Category").delete()

    # Create test data
    user = User.objects.create_user(
        username="test_final_user", email="test_final@test.com"
    )
    category = Category.objects.create(name="Test Final Category")
    post = Post.objects.create(
        title="Test Final Post", content="Test content", category=category
    )

    print(f"Created post {post.id}, user {user.id}")

    # Test the exact mutation that's failing
    mutation = f"""
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
    """

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
