#!/usr/bin/env python
"""
Debug script to trace nested tags processing in update_post mutation.
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Configure Django settings
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "test_app",
            "rail_django_graphql",
        ],
        SECRET_KEY="test-secret-key",
        USE_TZ=True,
    )

django.setup()

# Create database tables
from django.db import connection
from test_app.models import User, Post, Category, Tag

# Create tables manually
with connection.schema_editor() as schema_editor:
    schema_editor.create_model(User)
    schema_editor.create_model(Category)
    schema_editor.create_model(Tag)
    schema_editor.create_model(Post)

from django.db import transaction
from test_app.models import User, Post, Category, Tag
from rail_django_graphql.generators.nested_operations import NestedOperationHandler


def debug_nested_tags():
    """Debug the nested tags processing step by step."""

    print("=== Debug Nested Tags Processing ===")

    # Clean up existing data
    Tag.objects.all().delete()
    Post.objects.all().delete()
    User.objects.all().delete()
    Category.objects.all().delete()

    # Create test data
    user = User.objects.create(username="testuser", email="test@example.com")
    category = Category.objects.create(name="Test Category")
    post = Post.objects.create(
        title="Original Title", content="Original content", category=category
    )

    print(f"Created post: {post.id} - {post.title}")
    print(f"Initial tags count: {post.tags.count()}")

    # Create nested operation handler
    handler = NestedOperationHandler(None)

    # Test input data
    input_data = {"title": "Updated Post", "nested_tags": [{"name": "dsdsdsd"}]}

    print(f"\nInput data: {input_data}")

    # Check if nested operations are enabled for tags
    use_nested = handler._should_use_nested_operations(Post, "tags")
    print(f"Nested operations enabled for Post.tags: {use_nested}")

    # Manually trace the update process
    print("\n=== Tracing Update Process ===")

    # Separate fields like the handler does
    regular_fields = {}
    nested_fields = {}
    m2m_fields = {}
    reverse_fields = {}

    # Get reverse relationships for Post model
    reverse_relations = handler._get_reverse_relations(Post)
    print(f"Reverse relations: {list(reverse_relations.keys())}")

    for field_name, value in input_data.items():
        print(f"\nProcessing field: {field_name} = {value}")

        if field_name == "id":
            continue

        # Check if this is a reverse relationship field
        if field_name in reverse_relations:
            reverse_fields[field_name] = (reverse_relations[field_name], value)
            print(f"  -> Added to reverse_fields")
            continue

        if not hasattr(Post, field_name):
            print(f"  -> Post model doesn't have field '{field_name}'")
            continue

        try:
            field = Post._meta.get_field(field_name)
            print(f"  -> Found field: {field} (type: {type(field).__name__})")
        except:
            # Handle properties and methods
            regular_fields[field_name] = value
            print(f"  -> Added to regular_fields (property/method)")
            continue

        if isinstance(field, django.db.models.ForeignKey):
            nested_fields[field_name] = (field, value)
            print(f"  -> Added to nested_fields (ForeignKey)")
        elif isinstance(field, django.db.models.OneToOneField):
            nested_fields[field_name] = (field, value)
            print(f"  -> Added to nested_fields (OneToOneField)")
        elif isinstance(field, django.db.models.ManyToManyField):
            m2m_fields[field_name] = (field, value)
            print(f"  -> Added to m2m_fields (ManyToManyField)")
        else:
            regular_fields[field_name] = value
            print(f"  -> Added to regular_fields (other)")

    print(f"\nField categorization (before mapping):")
    print(f"  regular_fields: {regular_fields}")
    print(f"  nested_fields: {nested_fields}")
    print(f"  m2m_fields: {m2m_fields}")
    print(f"  reverse_fields: {reverse_fields}")

    # Check if 'nested_tags' is being processed as 'tags'
    print(f"\n=== Checking Field Name Mapping ===")
    print(f"Looking for 'tags' field in Post model...")
    try:
        tags_field = Post._meta.get_field("tags")
        print(f"Found tags field: {tags_field} (type: {type(tags_field).__name__})")
    except Exception as e:
        print(f"Error getting tags field: {e}")

    # Check if nested_tags should be mapped to tags
    print(f"\nChecking if 'nested_tags' should be mapped to 'tags'...")

    # Simulate the field name mapping from mutations.py
    mapped_data = {}
    for field_name, value in input_data.items():
        if field_name.startswith("nested_"):
            # Remove 'nested_' prefix to get actual field name
            actual_field_name = field_name[7:]  # Remove 'nested_' (7 characters)
            print(f"Mapping '{field_name}' -> '{actual_field_name}'")

            # Check if the actual field exists on the model
            if hasattr(Post, actual_field_name):
                try:
                    field = Post._meta.get_field(actual_field_name)
                    print(f"  -> Found field: {field} (type: {type(field).__name__})")
                    mapped_data[actual_field_name] = value
                except:
                    print(f"  -> Field '{actual_field_name}' not found in model")
            else:
                print(f"  -> Model doesn't have field '{actual_field_name}'")
        else:
            mapped_data[field_name] = value

    print(f"\nMapped data: {mapped_data}")

    # Re-categorize with mapped data
    regular_fields = {}
    nested_fields = {}
    m2m_fields = {}
    reverse_fields = {}

    for field_name, value in mapped_data.items():
        print(f"\nProcessing mapped field: {field_name} = {value}")

        if field_name == "id":
            continue

        # Check if this is a reverse relationship field
        if field_name in reverse_relations:
            reverse_fields[field_name] = (reverse_relations[field_name], value)
            print(f"  -> Added to reverse_fields")
            continue

        if not hasattr(Post, field_name):
            print(f"  -> Post model doesn't have field '{field_name}'")
            continue

        try:
            field = Post._meta.get_field(field_name)
            print(f"  -> Found field: {field} (type: {type(field).__name__})")
        except:
            # Handle properties and methods
            regular_fields[field_name] = value
            print(f"  -> Added to regular_fields (property/method)")
            continue

        if isinstance(field, django.db.models.ForeignKey):
            nested_fields[field_name] = (field, value)
            print(f"  -> Added to nested_fields (ForeignKey)")
        elif isinstance(field, django.db.models.OneToOneField):
            nested_fields[field_name] = (field, value)
            print(f"  -> Added to nested_fields (OneToOneField)")
        elif isinstance(field, django.db.models.ManyToManyField):
            m2m_fields[field_name] = (field, value)
            print(f"  -> Added to m2m_fields (ManyToManyField)")
        else:
            regular_fields[field_name] = value
            print(f"  -> Added to regular_fields (other)")

    print(f"\nField categorization after mapping:")
    print(f"  regular_fields: {regular_fields}")
    print(f"  nested_fields: {nested_fields}")
    print(f"  m2m_fields: {m2m_fields}")
    print(f"  reverse_fields: {reverse_fields}")

    # Simulate the actual update
    print(f"\n=== Simulating Update ===")

    try:
        with transaction.atomic():
            # Update regular fields
            for field_name, value in regular_fields.items():
                setattr(post, field_name, value)
                print(f"Set {field_name} = {value}")

            # Save the instance
            post.save()
            print(f"Saved post")

            # Handle many-to-many relationships
            for field_name, (field, value) in m2m_fields.items():
                print(f"\nProcessing M2M field: {field_name}")
                print(f"  Field: {field}")
                print(f"  Value: {value}")

                if value is None:
                    print(f"  -> Skipping (value is None)")
                    continue

                m2m_manager = getattr(post, field_name)
                print(f"  M2M manager: {m2m_manager}")

                # Check if nested operations should be used for this field
                use_nested = handler._should_use_nested_operations(Post, field_name)
                print(f"  Use nested operations: {use_nested}")

                if isinstance(value, list):
                    print(f"  Processing list of {len(value)} items")
                    related_objects = []
                    for i, item in enumerate(value):
                        print(f"    Item {i}: {item} (type: {type(item).__name__})")
                        if isinstance(item, dict) and use_nested:
                            if "id" in item:
                                # Reference existing object
                                related_obj = field.related_model.objects.get(
                                    pk=item["id"]
                                )
                                print(f"      -> Found existing object: {related_obj}")
                            else:
                                # Create new object only if nested operations are enabled
                                print(f"      -> Creating new object with data: {item}")
                                related_obj = handler.handle_nested_create(
                                    field.related_model, item
                                )
                                print(f"      -> Created: {related_obj}")
                            related_objects.append(related_obj)
                        elif isinstance(item, (str, int)):
                            # Direct ID reference - always allowed
                            related_obj = field.related_model.objects.get(pk=item)
                            related_objects.append(related_obj)
                            print(f"      -> Found by ID: {related_obj}")
                        elif isinstance(item, dict) and not use_nested:
                            print(
                                f"      -> ERROR: Nested operations disabled but dict provided"
                            )

                    print(f"  Setting M2M to: {related_objects}")
                    m2m_manager.set(related_objects)
                    print(f"  M2M set complete")

            print(f"\nFinal post tags count: {post.tags.count()}")
            for tag in post.tags.all():
                print(f"  Tag: {tag.name}")

            print(f"All tags in database:")
            for tag in Tag.objects.all():
                print(f"  DB Tag: {tag.name}")

    except Exception as e:
        print(f"Error during update: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_nested_tags()
